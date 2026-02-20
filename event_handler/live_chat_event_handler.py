"""实时消息事件处理器

监听消息发送和接收事件，并通过 WebSocket 实时推送到前端。
"""

from typing import Any
import time

from src.core.components.base.event_handler import BaseEventHandler
from src.core.components.types import EventType
from src.kernel.logger import get_logger

logger = get_logger("live_chat_event_handler", display="实时消息处理器")


class LiveChatEventHandler(BaseEventHandler):
    """实时消息事件处理器。

    订阅消息接收和发送事件，在接收到消息时：
    1. 构建消息数据结构
    2. 通过 WebSocket 广播到前端
    """

    handler_name = "live_chat_event_handler"
    handler_description = "监听消息事件并实时推送到 WebUI"
    weight = 0
    intercept_message = False
    init_subscribe = [EventType.ON_MESSAGE_RECEIVED, EventType.ON_MESSAGE_SENT]

    async def execute(
        self, kwargs: dict[str, Any] | None
    ) -> tuple[bool, bool, str | None]:
        """处理消息事件。

        Args:
            kwargs: 事件参数字典，包含 message 对象
                   ON_MESSAGE_RECEIVED: {
                       'message': Message,
                       'envelope': MessageEnvelope,
                       'adapter_signature': str
                   }
                   ON_MESSAGE_SENT: {
                       'message': Message,
                       'envelope': MessageEnvelope,
                       'adapter_signature': str
                   }

        Returns:
            tuple[bool, bool, str | None]: (是否成功, 是否拦截, 消息)
        """
        if kwargs is None:
            return False, False, "无事件参数"

        try:
            message = kwargs.get("message")
            if not message:
                return False, False, "缺少消息对象"

            # 获取事件类型（从订阅中判断）
            event_type = kwargs.get("event_type")
            is_sent = event_type == EventType.ON_MESSAGE_SENT

            # 构建消息数据
            message_data = await self._build_message_data(message, is_sent)

            # 广播到 WebSocket 客户端
            await self._broadcast_message(message_data)

            logger.debug(
                f"{'[发送]' if is_sent else '[接收]'} "
                f"消息已推送: {message.message_id}"
            )

            return True, False, None

        except Exception as e:
            logger.error(f"处理消息事件失败: {e}", exc_info=True)
            return False, False, str(e)

    async def _build_message_data(
        self, message: Any, is_sent: bool
    ) -> dict[str, Any]:
        """构建前端所需的消息数据结构。

        Args:
            message: Message 对象
            is_sent: 是否为发送的消息

        Returns:
            dict: 消息数据字典
        """
        # 基础消息信息
        data = {
            "message_id": message.message_id,
            "stream_id": message.stream_id,
            "platform": message.platform,
            "chat_type": message.chat_type,
            "time": message.time or time.time(),
            "content": message.processed_plain_text or message.content or "",
            "sender_id": message.sender_id,
            "sender_name": message.sender_cardname or message.sender_name,
            "is_sent": is_sent,
            "is_bot": False,  # 将在下面更新
            "is_webui": False,
        }

        # 判断是否为 Bot 消息
        if is_sent:
            data["is_bot"] = True
        else:
            # 检查发送者是否为 Bot
            try:
                from src.core.managers.adapter_manager import get_adapter_manager
                adapter_manager = get_adapter_manager()
                
                # 查找匹配平台的适配器
                from src.core.components.registry import get_global_registry
                from src.core.components.types import ComponentType
                
                registry = get_global_registry()
                adapters = registry.get_by_type(ComponentType.ADAPTER)
                
                for sig, adapter_cls in adapters.items():
                    if hasattr(adapter_cls, "platform") and adapter_cls.platform == message.platform:
                        adapter = adapter_manager.get_adapter(sig)
                        if adapter:
                            bot_info = await adapter.get_bot_info()
                            bot_id = str(bot_info.get("bot_id", ""))
                            if bot_id and message.sender_id == bot_id:
                                data["is_bot"] = True
                            break
            except Exception as e:
                logger.warning(f"检查 Bot 消息失败: {e}")

        # 处理图片消息
        images = []
        if hasattr(message, "message_chain") and message.message_chain:
            for segment in message.message_chain:
                if segment.type == "image" and segment.data.get("hash"):
                    images.append({
                        "hash": segment.data.get("hash"),
                        "url": segment.data.get("url"),
                    })
        data["images"] = images

        # 处理引用消息
        reply_message_id = None
        if hasattr(message, "extra") and message.extra:
            reply_message_id = message.extra.get("reply_message_id")
        data["reply_message_id"] = reply_message_id

        # 额外元数据
        data["metadata"] = {
            "message_type": str(message.message_type) if hasattr(message, "message_type") else "",
        }

        return data

    async def _broadcast_message(self, message_data: dict[str, Any]) -> None:
        """广播消息到所有订阅了相应 stream 的 WebSocket 客户端。

        Args:
            message_data: 消息数据字典
        """
        try:
            # 导入 LiveChatRouter 并调用其广播方法
            from ..router.live_chat_router import LiveChatRouter
            await LiveChatRouter.broadcast_message(message_data)
        except Exception as e:
            logger.warning(f"广播消息失败: {e}")
