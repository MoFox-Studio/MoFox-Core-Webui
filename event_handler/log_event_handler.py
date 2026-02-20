"""日志事件处理器

监听日志输出事件并通过 WebSocket 实时推送到前端。
"""

from typing import Any
import asyncio

from src.core.components.base.event_handler import BaseEventHandler
from src.kernel.logger import get_logger, LOG_OUTPUT_EVENT

logger = get_logger("log_event_handler", display="日志事件处理器")


class LogEventHandler(BaseEventHandler):
    """日志事件处理器。

    订阅日志输出事件，在接收到日志时：
    1. 打印日志内容（调试用）
    2. 通过 WebSocket 广播到前端
    """

    handler_name = "log_event_handler"
    handler_description = "监听系统日志事件并实时推送到 WebUI"
    weight = 0
    intercept_message = False
    init_subscribe = [LOG_OUTPUT_EVENT]

    async def execute(
        self, kwargs: dict[str, Any] | None
    ) -> tuple[bool, bool, str | None]:
        """处理日志输出事件。

        Args:
            kwargs: 事件参数字典，包含日志数据
                   格式: {
                       'timestamp': '2026-02-19T17:13:32.223',
                       'level': 'DEBUG',
                       'logger_name': 'event_manager',
                       'display': 'event_manager',
                       'color': '#88C0D0',
                       'message': '...'
                   }

        Returns:
            tuple[bool, bool, str | None]: (是否成功, 是否拦截, 消息)
        """
        if kwargs is None:
            return False, False, "无事件参数"

        # 打印日志信息（调试用）
        # print(f"{kwargs}")

        # 广播到 WebSocket 客户端
        try:
            from ..router.realtime_log_router import RealtimeLogRouter
            
            # 在事件循环中创建任务，避免阻塞
            asyncio.create_task(RealtimeLogRouter.broadcast_log(kwargs))
        except Exception as e:
            # 不阻塞主流程，只记录错误
            logger.debug(f"广播日志到 WebSocket 失败: {e}")

        return True, False, None
