"""
启动事件处理器
在系统启动时启动发现服务器和UI Chatroom适配器
"""

import asyncio
import sys
import webbrowser
from pathlib import Path
from typing import Set

from src.common.logger import get_logger
from src.plugin_system import BaseEventHandler, EventType
from src.plugin_system.base.base_event import HandlerResult
from src.common.server import get_global_server

from ..discovery_server import start_discovery_server, DISCOVERY_PORT

# 导入后端存储管理
sys.path.insert(0, str(Path(__file__).parent.parent))
from utils.backend_storage import BackendStorage

logger = get_logger("WebUIAuth.StartupHandler")

# 初始化状态的存储键名
INIT_STATUS_KEY = "is_initialized"

# 用于存储后台任务的集合
_background_tasks: Set[asyncio.Task] = set()


def check_initialization_status() -> bool:
    """
    检查系统是否已初始化

    Returns:
        bool: 是否已初始化
    """
    try:
        is_initialized = BackendStorage.get(INIT_STATUS_KEY, False)
        return is_initialized
    except Exception as e:
        logger.warning(f"检查初始化状态失败: {e}，假定未初始化")
        return False


def open_initialization_page(host: str, port: int) -> None:
    """
    打开浏览器到初始化页面

    Args:
        host: WebUI 主机地址
        port: WebUI 端口
    """
    # 如果 host 是 0.0.0.0，使用 localhost 来打开浏览器
    browser_host = "localhost" if host == "0.0.0.0" else host
    init_url = f"http://{browser_host}:{port}/initialization"

    try:
        logger.info(f"正在打开浏览器: {init_url}")
        webbrowser.open(init_url)
    except Exception as e:
        logger.warning(f"自动打开浏览器失败: {e}")
        logger.info(f"请手动打开浏览器访问: {init_url}")

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

            logger.info("准备启动发现服务器...")
            logger.info(f"主程序配置: {main_host}:{main_port}")
            logger.info(f"发现服务器端口: {DISCOVERY_PORT}") 

            # 创建后台任务启动发现服务器
            task = asyncio.create_task(
                start_discovery_server(
                    main_host=main_host, main_port=main_port, discovery_host="0.0.0.0"
                )
            )

            # 添加到后台任务集合并设置回调
            _background_tasks.add(task)
            task.add_done_callback(_background_tasks.discard)

            logger.info("发现服务器后台任务已创建")

            # 检查初始化状态
            is_initialized = check_initialization_status()

            if not is_initialized:
                # 未初始化，显示提示并打开浏览器
                logger.warning("=" * 60)
                logger.warning("⚠️  系统尚未完成初始化配置！")
                logger.warning("=" * 60)
                logger.warning("首次使用需要完成以下配置：")
                logger.warning("  1. 机器人基本信息（QQ号、昵称、人格设定等）")
                logger.warning("  2. AI模型配置（API密钥、模型提供商等）")
                logger.warning("  3. Git配置（可选，用于更新功能）")
                logger.warning("-" * 60)
                logger.warning("正在自动打开浏览器进入初始化向导...")
                logger.warning("=" * 60)

                # 延迟一小段时间后打开浏览器，确保服务器已启动
                await asyncio.sleep(2)
                open_initialization_page(main_host, DISCOVERY_PORT)
            else:
                logger.info("✓ 系统已完成初始化配置")

            return HandlerResult(
                success=True,
                continue_process=True,
                message=f"WebUI发现服务器已启动在端口 {DISCOVERY_PORT}",
                handler_name=self.handler_name,
            )

        except Exception as e:
            logger.error(f"启动发现服务器失败: {e}")
            return HandlerResult(
                success=False,
                continue_process=True,  # 即使失败也不阻断其他处理
                message=f"启动发现服务器失败: {str(e)}",
                handler_name=self.handler_name,
            )
