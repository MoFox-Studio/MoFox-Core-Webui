"""日志事件处理器

监听日志输出事件并通过 WebSocket 实时推送到前端。
"""

from typing import Any
import asyncio

from src.core.components.base.event_handler import BaseEventHandler
from src.kernel.event import EventDecision
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
        self, event_name: str, params: dict[str, Any]
    ) -> tuple["EventDecision", dict[str, Any]]:
        """处理日志输出事件。

        Args:
            event_name: 触发本处理器的事件名称
            params: 事件参数字典，包含日志数据
                   格式: {
                       'timestamp': '2026-02-19T17:13:32.223',
                       'level': 'DEBUG',
                       'logger_name': 'event_manager',
                       'display': 'event_manager',
                       'color': '#88C0D0',
                       'message': '...'
                   }

        Returns:
            tuple[EventDecision, dict]: 决策与参数
        """
        if params is None:
            return EventDecision.PASS, params

        # 打印日志信息（调试用）
        # print(f"{params}")

        # 广播到 WebSocket 客户端
        try:
            from ..router.realtime_log_router import RealtimeLogRouter
            # 在事件循环中创建任务，避免阻塞主流程
            asyncio.create_task(RealtimeLogRouter.broadcast_log(params))
        except Exception as e:
            logger.debug(f"广播日志到 WebSocket 失败: {e}")

        return EventDecision.SUCCESS, params
