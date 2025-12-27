"""
UI Chatroom 适配器

用于WebUI聊天室的消息适配器，不使用WebSocket，而是通过内存队列直接通信

基于 MoFox-Bus 架构重写，参考 Napcat 适配器的设计模式
"""

from __future__ import annotations

import asyncio
import time
import uuid
from typing import Any

from mofox_wire import CoreSink, MessageEnvelope

from src.common.logger import get_logger
from src.plugin_system.base import BaseAdapter
from src.config.config import global_config

logger = get_logger("ui_chatroom_adapter")


class UIChatroomAdapter(BaseAdapter):
    """UI Chatroom 适配器 - 用于WebUI聊天室（基于 MoFox-Bus 架构）"""

    adapter_name = "ui_chatroom_adapter"
    adapter_version = "2.0.0"
    adapter_author = "MoFox Team"
    adapter_description = "WebUI 聊天室适配器（基于 MoFox-Bus 重写）"
    platform = "web_ui_chatroom"

    run_in_subprocess = False

    def __init__(self, core_sink: CoreSink, plugin: Any | None = None, **kwargs):
        """初始化 UI Chatroom 适配器"""
        # UI适配器不需要WebSocket，transport=None
        super().__init__(core_sink, plugin=plugin, transport=None, **kwargs)

        # 消息队列：用于后端向核心发送消息
        self._incoming_queue: asyncio.Queue = asyncio.Queue()
        
        # 消息存储：用于存储 AI 的异步回复
        self._pending_responses: asyncio.Queue[dict[str, Any]] = asyncio.Queue()
        
        # 引用消息缓存：用于前端查询引用的消息内容
        self._message_cache: dict[str, dict[str, Any]] = {}
        self._cache_max_size = 1000

        # 设置全局适配器实例
        set_ui_chatroom_adapter(self)

        logger.info("UI Chatroom 适配器初始化完成")

    async def on_adapter_loaded(self) -> None:
        """适配器加载时的初始化"""
        logger.info("UI Chatroom 适配器正在启动...")
        logger.info("UI Chatroom 适配器已加载，等待 WebUI 连接")

    async def on_adapter_unloaded(self) -> None:
        """适配器卸载时的清理"""
        logger.info("UI Chatroom 适配器正在关闭...")

        # 清空消息队列
        while not self._incoming_queue.empty():
            try:
                self._incoming_queue.get_nowait()
            except asyncio.QueueEmpty:
                break

        # 清空响应队列
        while not self._pending_responses.empty():
            try:
                self._pending_responses.get_nowait()
            except asyncio.QueueEmpty:
                break

        # 清空消息缓存
        self._message_cache.clear()

        logger.info("UI Chatroom 适配器已关闭")

    async def from_platform_message(self, raw: dict[str, Any]) -> MessageEnvelope | None:  # type: ignore[override]
        """
        将UI平台原始消息转换为 MessageEnvelope

        Args:
            raw: 原始消息数据
                {
                    "message_id": "xxx",
                    "user_id": "virtual_user_123",
                    "nickname": "测试用户",
                    "content": "你好",
                    "timestamp": 1234567890.0,
                    "message_type": "text",  # text, image, etc.
                    "reply_to": "msg_id" (optional)
                }

        Returns:
            MessageEnvelope | None: 转换后的消息信封，如果转换失败则返回 None
        """
        try:
            message_id = raw.get("message_id", str(uuid.uuid4()))
            user_id = raw.get("user_id", "unknown")
            nickname = raw.get("nickname", "Unknown User")
            content = raw.get("content", "")
            timestamp = raw.get("timestamp", time.time())
            message_type = raw.get("message_type", "text")
            reply_to = raw.get("reply_to")

            # 缓存消息用于引用查询
            self._cache_message({
                "message_id": message_id,
                "user_id": user_id,
                "nickname": nickname,
                "content": content,
                "timestamp": timestamp,
                "message_type": message_type,
            })

            # 构建消息段
            message_segment = []
            
            if message_type == "text":
                message_segment.append({
                    "type": "text",
                    "data": content  # str 类型
                })
            elif message_type == "image":
                # 对于image类型，data是URL字符串
                message_segment.append({
                    "type": "image",
                    "data": content  # str 类型的URL
                })
            else:
                # 其他类型的消息
                message_segment.append({
                    "type": message_type,
                    "data": content
                })

            # 构建元数据，包含引用信息
            metadata: dict[str, Any] = {
                "raw": raw,
            }
            
            # 如果有引用消息，添加到元数据
            if reply_to:
                metadata["reply_to"] = reply_to
                # 尝试从缓存获取被引用的消息
                quoted_msg = self._message_cache.get(reply_to)
                if quoted_msg:
                    metadata["quoted_message"] = quoted_msg

            # 构建 MessageEnvelope
            envelope: MessageEnvelope = {
                "direction": "incoming",
                "message_info": {
                    "platform": self.platform,
                    "message_id": message_id,
                    "user_info": {
                        "user_id": user_id,
                        "platform": self.platform,
                        "user_nickname": nickname,
                    },
                    "time": timestamp,
                },
                "message_segment": message_segment,
                "metadata": metadata
            }

            logger.debug(f"转换消息: {message_id} from {nickname}: {content[:50]}...")
            return envelope

        except Exception as e:
            logger.error(f"转换消息失败: {e}", exc_info=True)
            return None

    async def _send_platform_message(self, envelope: MessageEnvelope) -> None:  # type: ignore[override]
        """
        将 MessageEnvelope 转换并发送到UI平台
        
        将消息放入待处理队列，供前端轮询获取

        Args:
            envelope: 要发送的消息信封
        """
        try:
            message_info = envelope.get("message_info", {})
            message_segment = envelope.get("message_segment", [])
            metadata = envelope.get("metadata", {})
            
            # 确保 message_segment 是列表
            if isinstance(message_segment, dict):
                message_segment = [message_segment]
            
            # 提取文本内容、图片和表情包
            text_content = ""
            image_urls = []
            emoji_base64_list = []  # 存储表情包的 base64 数据
            
            for segment in message_segment:
                seg_type = segment.get("type")
                seg_data = segment.get("data", "")
                
                if seg_type == "text":
                    # data 是 str
                    if isinstance(seg_data, str):
                        text_content += seg_data
                elif seg_type == "image":
                    # data 是 str (URL)
                    if isinstance(seg_data, str):
                        image_urls.append(seg_data)
                elif seg_type == "emoji":
                    # emoji 的 data 是 base64 编码的图片
                    if isinstance(seg_data, str):
                        emoji_base64_list.append(seg_data)
                        logger.debug(f"提取到表情包，长度: {len(seg_data)}")

            # 获取原始消息的 message_id 作为 reply_to
            reply_to = None
            raw = metadata.get("raw", {})
            if raw:
                reply_to = raw.get("message_id")

            # 确定消息类型
            if emoji_base64_list:
                msg_type = "emoji"
            elif image_urls:
                msg_type = "image"
            elif text_content:
                msg_type = "text"
            else:
                msg_type = "text"

            # 构建响应消息
            response_message = {
                "message_id": message_info.get("message_id", str(uuid.uuid4())),
                "user_id": "mofox_bot",  # 机器人的ID
                "nickname": global_config.bot.nickname,
                "content": text_content,
                "images": image_urls,
                "emojis": emoji_base64_list,  # 添加表情包列表
                "timestamp": time.time(),
                "message_type": msg_type,
                "reply_to": reply_to,  # 引用原消息
            }

            # 缓存机器人的回复消息
            self._cache_message({
                "message_id": response_message["message_id"],
                "user_id": response_message["user_id"],
                "nickname": response_message["nickname"],
                "content": text_content,
                "timestamp": response_message["timestamp"],
                "message_type": response_message["message_type"],
                "emojis": emoji_base64_list,  # 缓存表情包数据
            })

            # 将响应消息放入队列
            await self._pending_responses.put(response_message)
            logger.debug(f"AI 回复已加入队列: {text_content[:50]}...")

        except Exception as e:
            logger.error(f"发送消息失败: {e}", exc_info=True)

    def _cache_message(self, message: dict[str, Any]) -> None:
        """缓存消息用于引用查询"""
        message_id = message.get("message_id")
        if message_id:
            self._message_cache[message_id] = message
            
            # 限制缓存大小
            if len(self._message_cache) > self._cache_max_size:
                # 删除最旧的消息（简单的FIFO策略）
                oldest_key = next(iter(self._message_cache))
                del self._message_cache[oldest_key]

    async def send_message(self, raw_message: dict[str, Any]) -> None:
        """
        从后端接收消息并处理（供 WebUI API 调用）
        
        此方法会：
        1. 转换为 MessageEnvelope 并推送到核心
        2. 立即返回，不等待响应（异步模式）
        
        注意：使用 on_platform_message() 方法，该方法内部会调用 core_sink.send()
        
        Args:
            raw_message: 原始消息数据
        """
        try:
            # 使用 BaseAdapter 的 on_platform_message 方法处理消息
            # 该方法会自动调用 from_platform_message 并发送到核心
            await self.on_platform_message(raw_message)
            logger.debug(f"消息已发送到核心: {raw_message.get('message_id')}")

        except ValueError as ve:
            logger.error(f"消息验证失败: {ve}")
            # 发送系统错误消息
            await self._pending_responses.put({
                "message_id": str(uuid.uuid4()),
                "user_id": "system",
                "nickname": "系统",
                "content": f"消息格式错误: {str(ve)}",
                "images": [],
                "timestamp": time.time(),
                "message_type": "text",
            })
        except Exception as e:
            logger.error(f"发送消息异常: {e}", exc_info=True)
            # 发送系统错误消息
            await self._pending_responses.put({
                "message_id": str(uuid.uuid4()),
                "user_id": "system",
                "nickname": "系统",
                "content": f"发送失败: {str(e)}",
                "images": [],
                "timestamp": time.time(),
                "message_type": "text",
            })

    async def get_pending_responses(self, timeout: float = 0.1) -> list[dict[str, Any]]:
        """
        获取待处理的响应消息（用于前端轮询）
        
        Args:
            timeout: 等待超时时间（秒），默认 0.1 秒
            
        Returns:
            响应消息列表
        """
        responses = []
        try:
            # 尝试获取所有可用的响应（非阻塞）
            while True:
                try:
                    response = await asyncio.wait_for(
                        self._pending_responses.get(),
                        timeout=timeout if not responses else 0.01
                    )
                    responses.append(response)
                except asyncio.TimeoutError:
                    break
        except Exception as e:
            logger.error(f"获取待处理响应失败: {e}")
        
        return responses

    def get_cached_message(self, message_id: str) -> dict[str, Any] | None:
        """
        获取缓存的消息（用于前端查询引用的消息）
        
        Args:
            message_id: 消息 ID
            
        Returns:
            消息数据，如果不存在则返回 None
        """
        return self._message_cache.get(message_id)


# 全局适配器实例
_adapter_instance: UIChatroomAdapter | None = None


def get_ui_chatroom_adapter() -> UIChatroomAdapter | None:
    """获取全局UI Chatroom适配器实例"""
    global _adapter_instance
    return _adapter_instance


def set_ui_chatroom_adapter(adapter: UIChatroomAdapter | None) -> None:
    """设置全局UI Chatroom适配器实例"""
    global _adapter_instance
    _adapter_instance = adapter
