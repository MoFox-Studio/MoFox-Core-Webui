"""
关闭事件处理器
在系统关闭时停止发现服务器
"""

from src.common.logger import get_logger
from src.plugin_system import BaseEventHandler, EventType
from src.plugin_system.base.base_event import HandlerResult

from ..discovery_server import stop_discovery_server

logger = get_logger("WebUIAuth.ShutdownHandler")


class WebUIShutdownHandler(BaseEventHandler):
    """
    WebUI关闭事件处理器
    在系统关闭时停止发现服务器
    """
    
    handler_name = "webui_shutdown_handler"
    handler_description = "在系统关闭时停止WebUI发现服务器"
    weight = 10
    intercept_message = False
    init_subscribe = [EventType.ON_STOP]  # 订阅停止事件
    
    async def execute(self, params: dict) -> HandlerResult:
        """
        处理关闭事件，停止发现服务器
        
        Args:
            params: 事件参数
            
        Returns:
            HandlerResult: 处理结果
        """
        try:
            logger.info("正在停止WebUI发现服务器...")
            await stop_discovery_server()
            
            return HandlerResult(
                success=True,
                continue_process=True,
                message="WebUI发现服务器已停止",
                handler_name=self.handler_name
            )
            
        except Exception as e:
            logger.error(f"停止发现服务器失败: {e}")
            return HandlerResult(
                success=False,
                continue_process=True,
                message=f"停止发现服务器失败: {str(e)}",
                handler_name=self.handler_name
            )
