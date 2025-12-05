"""
启动事件处理器
在系统启动时启动发现服务器
"""

import asyncio
import os
from typing import Set

from src.common.logger import get_logger
from src.plugin_system import BaseEventHandler, EventType
from src.plugin_system.base.base_event import HandlerResult
from src.common.server import get_global_server

from ..discovery_server import start_discovery_server, DISCOVERY_PORT

logger = get_logger("WebUIAuth.StartupHandler")

# 用于存储后台任务的集合
_background_tasks: Set[asyncio.Task] = set()


class WebUIStartupHandler(BaseEventHandler):
    """
    WebUI启动事件处理器
    在系统启动时启动固定端口的发现服务器
    """
    
    handler_name = "webui_startup_handler"
    handler_description = "在系统启动时启动WebUI发现服务器"
    weight = 10  # 权重，确保在其他处理器之前执行
    intercept_message = False  # 不拦截消息
    init_subscribe = [EventType.ON_START]  # 订阅启动事件
    
    async def execute(self, params: dict) -> HandlerResult:
        """
        处理启动事件，启动发现服务器
        
        Args:
            params: 事件参数
            
        Returns:
            HandlerResult: 处理结果
        """
        try:
            # 从环境变量或配置获取主程序的地址
            # 这些值应该与主程序的配置一致
            server = get_global_server()
            main_host = server.host
            main_port = server.port
            
            logger.info(f"准备启动发现服务器...")
            logger.info(f"主程序配置: {main_host}:{main_port}")
            logger.info(f"发现服务器端口: {DISCOVERY_PORT}")
            logger.info(f"登录接口: http://{main_host}:{main_port}/plugin-api/webui_auth/auth/login")
            
            # 创建后台任务启动发现服务器
            task = asyncio.create_task(
                start_discovery_server(
                    main_host=main_host,
                    main_port=main_port,
                    discovery_host="0.0.0.0"
                )
            )
            
            # 添加到后台任务集合并设置回调
            _background_tasks.add(task)
            task.add_done_callback(_background_tasks.discard)
            
            logger.info("发现服务器后台任务已创建")
            
            return HandlerResult(
                success=True,
                continue_process=True,
                message=f"WebUI发现服务器已启动在端口 {DISCOVERY_PORT}",
                handler_name=self.handler_name
            )
            
        except Exception as e:
            logger.error(f"启动发现服务器失败: {e}")
            return HandlerResult(
                success=False,
                continue_process=True,  # 即使失败也不阻断其他处理
                message=f"启动发现服务器失败: {str(e)}",
                handler_name=self.handler_name
            )
