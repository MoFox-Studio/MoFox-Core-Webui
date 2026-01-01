"""
WebUI认证插件
提供WebUI前端登录验证功能

功能:
1. 启动固定端口(12138)的发现服务器
2. 提供主程序IP和端口信息
3. 提供带有API Key验证的接口

流程:
前端 → 发现服务器(固定端口12138) → 返回主程序端口和IP
    → 通过主程序的端口和IP访问插件系统定义的API接口
"""

from typing import List, Tuple, Type

from src.common.logger import get_logger
from src.plugin_system import BasePlugin, ComponentInfo, register_plugin
from src.plugin_system.base.config_types import ConfigField

from .handlers import WebUIShutdownHandler, WebUIStartupHandler, LiveChatEventHandler
from .routers import (
    ChatroomRouterComponent,
    EmojiManagerRouterComponent,
    ExpressionRouterComponent,
    GitUpdateRouterComponent,
    GitEnvRouterComponent,
    UIUpdateRouterComponent,
    LiveChatRouterComponent,
    LogViewerRouterComponent,
    InitializationRouter,
    MarketplaceRouterComponent,
    RelationshipRouterComponent,
    WebUIAuthRouter,
    WebUIConfigRouter,
    WebUIModelRouter,
    WebUIModelStatsRouter,
    WebUIPluginRouter,
    WebUISettingRouter,
    WebUIStatsRouter,
)
from .adapters import UIChatroomAdapter

logger = get_logger("WebUIAuth.Plugin")


@register_plugin
class WebUIAuthPlugin(BasePlugin):
    """
    WebUI插件

    提供:
    1. 固定端口的发现服务器 (端口12138)
    2. HTTP接口
    """

    # 插件基本信息
    plugin_name: str = "webui_backend"
    plugin_version: str = "1.0.0"
    plugin_author: str = "MoFox Team"
    plugin_description: str = "WebUI前端认证插件，提供发现服务和验证接口"

    # 插件配置
    enable_plugin: bool = True
    dependencies: list[str] = []
    python_dependencies: list[str] = ["uvicorn", "fastapi", "psutil"]
    config_file_name: str = "config.toml"

    # 配置模式定义
    config_schema: dict = {
        "plugin": {
            "enable": ConfigField(type=bool, default=True, description="是否启用插件"),
        },
        "discovery": {
            "port": ConfigField(type=int, default=12138, description="发现服务器端口（固定端口，供前端发现主程序）"),
            "host": ConfigField(type=str, default="0.0.0.0", description="发现服务器绑定地址"),
        },
        "auth": {
            "api_keys": ConfigField(
                type=list, default=["mofox-default-key"], description="有效的API Key列表，用于验证前端请求"
            ),
            "session_timeout_minutes": ConfigField(
                type=int, default=1440, description="会话超时时间（分钟），默认24小时"
            ),
        },
        "main_server": {
            "host": ConfigField(type=str, default="127.0.0.1", description="主程序HTTP服务器地址"),
            "port": ConfigField(type=int, default=8000, description="主程序HTTP服务器端口"),
        },
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        logger.info("WebUI认证插件初始化")

    async def on_plugin_loaded(self):
        """插件加载完成后的回调"""
        logger.info("WebUI认证插件已加载")
        logger.info(
            f"发现服务器配置: {self.get_config('discovery.host', '0.0.0.0')}:{self.get_config('discovery.port', 12138)}"
        )
        logger.info(
            f"主程序配置: {self.get_config('main_server.host', '127.0.0.1')}:{self.get_config('main_server.port', 8000)}"
        )

    def get_plugin_components(self) -> List:
        """
        返回插件包含的组件列表

        包括:
        - WebUIStartupHandler: 启动时启动发现服务器
        - WebUIShutdownHandler: 关闭时停止发现服务器
        - WebUIAuthRouter: HTTP认证接口
        - WebUIStatsRouter: HTTP统计数据接口
        - ChatroomRouterComponent: 聊天室接口
        """
        return [
            # 事件处理器
            (WebUIStartupHandler.get_handler_info(), WebUIStartupHandler),
            (WebUIShutdownHandler.get_handler_info(), WebUIShutdownHandler),
            (LiveChatEventHandler.get_handler_info(), LiveChatEventHandler),
            # HTTP路由组件
            (WebUIAuthRouter.get_router_info(), WebUIAuthRouter),
            (WebUIConfigRouter.get_router_info(), WebUIConfigRouter),
            (WebUIPluginRouter.get_router_info(), WebUIPluginRouter),
            (WebUIStatsRouter.get_router_info(), WebUIStatsRouter),
            (WebUIModelStatsRouter.get_router_info(), WebUIModelStatsRouter),
            (MarketplaceRouterComponent.get_router_info(), MarketplaceRouterComponent),
            (GitUpdateRouterComponent.get_router_info(), GitUpdateRouterComponent),
            (LogViewerRouterComponent.get_router_info(), LogViewerRouterComponent),
            (ExpressionRouterComponent.get_router_info(), ExpressionRouterComponent),
            (RelationshipRouterComponent.get_router_info(), RelationshipRouterComponent),
            (EmojiManagerRouterComponent.get_router_info(), EmojiManagerRouterComponent),
            (ChatroomRouterComponent.get_router_info(), ChatroomRouterComponent),
            (LiveChatRouterComponent.get_router_info(), LiveChatRouterComponent),
             (InitializationRouter.get_router_info(),     InitializationRouter),
            (GitEnvRouterComponent.get_router_info(), GitEnvRouterComponent),
            (UIUpdateRouterComponent.get_router_info(), UIUpdateRouterComponent),
            (UIChatroomAdapter.get_adapter_info(), UIChatroomAdapter),
            (WebUIModelRouter.get_router_info(),WebUIModelRouter),
            (WebUISettingRouter.get_router_info(), WebUISettingRouter),
        ]
