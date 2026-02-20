"""Chatroom 适配器

为 WebUI 聊天室提供消息适配层，无 WebSocket 传输，
使用内存队列实现 Bot 回复的异步轮询。
"""

from __future__ import annotations

import asyncio
import time
import uuid
from typing import Any

from mofox_wire import CoreSink, MessageEnvelope

from src.kernel.logger import get_logger
from src.core.components.base.adapter import BaseAdapter

logger = get_logger(name="ChatroomAdapter", color="#A6E3A1")

PLATFORM = "webui"
_ADAPTER_INSTANCE: "ChatroomAdapter | None" = None


def get_chatroom_adapter() -> "ChatroomAdapter | None":
    """获取全局 ChatroomAdapter 单例"""
    return _ADAPTER_INSTANCE


def set_chatroom_adapter(adapter: "ChatroomAdapter") -> None:
    """设置全局 ChatroomAdapter 单例"""
    global _ADAPTER_INSTANCE
    _ADAPTER_INSTANCE = adapter


class ChatroomAdapter(BaseAdapter):
    """WebUI 聊天室适配器

    不使用 WebSocket，通过内存队列在 HTTP 轮询与 Bot 核心之间传递消息。
    """

    adapter_name = "chatroom_adapter"
    adapter_version = "1.0.0"
    adapter_author = "MoFox Team"
    adapter_description = "WebUI 聊天室适配器（HTTP 轮询模式）"
    platform = PLATFORM

    run_in_subprocess = False

    def __init__(self, core_sink: CoreSink, plugin: Any | None = None, **kwargs: Any) -> None:
        # transport=None：不需要 WebSocket 连接
        super().__init__(core_sink, plugin=plugin, transport=None, **kwargs)

        # Bot 回复缓冲队列（供前端轮询）
        self._pending_responses: asyncio.Queue[dict[str, Any]] = asyncio.Queue()

        # 消息内容缓存（用于 reply 引用查询），FIFO、上限 1000 条
        self._message_cache: dict[str, dict[str, Any]] = {}
        self._cache_max_size = 1000

        set_chatroom_adapter(self)
        logger.info("ChatroomAdapter 初始化完成")

    # ------------------------------------------------------------------ #
    #  生命周期                                                           #
    # ------------------------------------------------------------------ #

    async def on_adapter_loaded(self) -> None:
        logger.info("ChatroomAdapter 已加载，等待 WebUI 接入")

    async def on_adapter_unloaded(self) -> None:
        logger.info("ChatroomAdapter 正在关闭...")
        # 清空两个队列
        for q in (self._pending_responses,):
            while not q.empty():
                try:
                    q.get_nowait()
                except asyncio.QueueEmpty:
                    break
        self._message_cache.clear()
        logger.info("ChatroomAdapter 已关闭")

    # ------------------------------------------------------------------ #
    #  消息入方向：WebUI → Core                                          #
    # ------------------------------------------------------------------ #

    async def send_message(self, raw_message: dict[str, Any]) -> None:
        """将前端原始消息推送到 CoreSink

        Args:
            raw_message: 前端发来的原始消息字典
        """
        envelope = await self.from_platform_message(raw_message)
        if envelope is None:
            logger.warning(f"from_platform_message 返回 None，忽略消息: {raw_message}")
            return
        await self.core_sink.send(envelope)
        logger.debug(f"消息已推送到 CoreSink: {raw_message.get('message_id', '?')}")

    async def from_platform_message(  # type: ignore[override]
        self, raw: dict[str, Any]
    ) -> MessageEnvelope | None:
        """将 WebUI 原始消息转换为 MessageEnvelope

        Args:
            raw: 原始消息字典，格式::

                {
                    "message_id": "xxx",          # 前端生成
                    "user_id": "12345",
                    "nickname": "测试用户",
                    "content": "你好",
                    "timestamp": 1234567890.0,
                    "message_type": "text",        # text | image
                    "reply_to": "msg_id"           # 可选，引用消息 ID
                }

        Returns:
            MessageEnvelope | None
        """
        try:
            message_id = raw.get("message_id") or str(uuid.uuid4())
            user_id = raw.get("user_id", "unknown")
            nickname = raw.get("nickname", "Unknown")
            content = raw.get("content", "")
            timestamp = raw.get("timestamp", time.time())
            message_type = raw.get("message_type", "text")
            reply_to = raw.get("reply_to")

            # 先缓存当前消息（供后续引用查询）
            self._cache_message({
                "message_id": message_id,
                "user_id": user_id,
                "nickname": nickname,
                "content": content,
                "timestamp": timestamp,
                "message_type": message_type,
            })

            # 构建消息段列表
            message_segment: list[dict[str, Any]] = []

            # 引用段（优先放在最前面）
            if reply_to:
                message_segment.append({"type": "reply", "data": reply_to})

            # 内容段
            if message_type in ("text", "image"):
                message_segment.append({"type": message_type, "data": content})
            else:
                message_segment.append({"type": message_type, "data": content})

            # 构建元数据
            metadata: dict[str, Any] = {"raw": raw}
            if reply_to:
                metadata["reply_to"] = reply_to
                quoted = self._message_cache.get(reply_to)
                if quoted:
                    metadata["quoted_message"] = quoted

            envelope: MessageEnvelope = {  # type: ignore[typeddict-item]
                "direction": "incoming",
                "message_info": {
                    "platform": PLATFORM,
                    "message_id": message_id,
                    "user_info": {
                        "user_id": user_id,
                        "platform": PLATFORM,
                        "user_nickname": nickname,
                    },
                    "time": timestamp,
                },
                "message_segment": message_segment,  # type: ignore[typeddict-item]
                "metadata": metadata,
            }

            logger.debug(f"消息已转换: {message_id} from {nickname}: {content[:50]}")
            return envelope

        except Exception as e:
            logger.error(f"from_platform_message 失败: {e}", exc_info=True)
            return None

    # ------------------------------------------------------------------ #
    #  消息出方向：Core → WebUI                                          #
    # ------------------------------------------------------------------ #

    async def _send_platform_message(  # type: ignore[override]
        self, envelope: MessageEnvelope
    ) -> None:
        """将 Bot 回复加入 _pending_responses 队列供前端轮询"""
        try:
            message_info = envelope.get("message_info", {})
            message_segment = envelope.get("message_segment", [])
            metadata = envelope.get("metadata", {})

            if isinstance(message_segment, dict):
                message_segment = [message_segment]

            # 提取内容
            text_content = ""
            image_urls: list[str] = []
            emoji_list: list[str] = []

            for seg in message_segment:
                seg_type = seg.get("type")
                seg_data = seg.get("data", "")
                if seg_type == "text" and isinstance(seg_data, str):
                    text_content += seg_data
                elif seg_type == "image" and isinstance(seg_data, str):
                    image_urls.append(seg_data)
                elif seg_type == "emoji" and isinstance(seg_data, str):
                    emoji_list.append(seg_data)

            # 确定消息类型
            if emoji_list:
                msg_type = "emoji"
            elif image_urls:
                msg_type = "image"
            else:
                msg_type = "text"

            # 以原始消息 message_id 作为 Bot 回复的 reply_to
            raw = metadata.get("raw", {})
            reply_to = raw.get("message_id") if raw else None

            response_msg: dict[str, Any] = {
                "message_id": message_info.get("message_id") or str(uuid.uuid4()),
                "user_id": "mofox_bot",
                "nickname": "MoFox Bot",
                "content": text_content,
                "images": image_urls,
                "emojis": emoji_list,
                "timestamp": time.time(),
                "message_type": msg_type,
                "reply_to": reply_to,
            }

            # 缓存 Bot 回复
            self._cache_message({
                "message_id": response_msg["message_id"],
                "user_id": response_msg["user_id"],
                "nickname": response_msg["nickname"],
                "content": text_content,
                "timestamp": response_msg["timestamp"],
                "message_type": msg_type,
                "emojis": emoji_list,
            })

            await self._pending_responses.put(response_msg)
            logger.debug(f"Bot 回复已入队: {text_content[:50]}")

        except Exception as e:
            logger.error(f"_send_platform_message 失败: {e}", exc_info=True)

    # ------------------------------------------------------------------ #
    #  前端轮询接口                                                       #
    # ------------------------------------------------------------------ #

    async def get_pending_responses(self, user_id: str | None = None) -> list[dict[str, Any]]:
        """排空 _pending_responses 队列并返回所有待取消息

        Args:
            user_id: 若提供，只返回该用户相关的消息（通过 reply_to 对应的原始请求 user_id 过滤）

        Returns:
            待发送消息列表
        """
        responses: list[dict[str, Any]] = []
        while not self._pending_responses.empty():
            try:
                msg = self._pending_responses.get_nowait()
                if user_id is not None:
                    # 通过 reply_to 找到原始消息，判断是否属于该 user_id
                    reply_to = msg.get("reply_to")
                    if reply_to:
                        original = self._message_cache.get(reply_to)
                        if original and original.get("user_id") != user_id:
                            # 放回队列（其他用户的消息）
                            await self._pending_responses.put(msg)
                            continue
                responses.append(msg)
            except asyncio.QueueEmpty:
                break
        return responses

    def get_cached_message(self, message_id: str) -> dict[str, Any] | None:
        """根据 message_id 从缓存查询消息内容"""
        return self._message_cache.get(message_id)

    # ------------------------------------------------------------------ #
    #  内部工具                                                           #
    # ------------------------------------------------------------------ #

    def _cache_message(self, message: dict[str, Any]) -> None:
        """缓存消息，超出上限时淘汰最旧条目（FIFO）"""
        message_id = message.get("message_id")
        if not message_id:
            return
        self._message_cache[message_id] = message
        if len(self._message_cache) > self._cache_max_size:
            oldest_key = next(iter(self._message_cache))
            del self._message_cache[oldest_key]
