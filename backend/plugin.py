"""测试路由插件

一个简单的测试插件，演示如何创建和注册Router组件。
"""

from src.kernel.logger import get_logger
from src.core.components.base.plugin import BasePlugin
from .router import FrontendRouter, CoreConfigRouter, ApiRouter, StatsRouter, SettingRouter, ModelConfigRouter, PluginConfigRouter, LogViewerRouter, RealtimeLogRouter, LiveChatRouter, ChatroomRouter, InitializationRouter, GitEnvRouter, GitUpdateRouter, UIUpdateRouter
from .adapter import ChatroomAdapter
from .event_handler import LogEventHandler, LiveChatEventHandler
from src.core.components.loader import register_plugin

logger = get_logger("webui_plugin")


@register_plugin
class MoFoxCoreWebui(BasePlugin):
    """Webui插件主类。

    注册和管理路由,并在初始化的时候帮路由准备好上下文。
    """

    plugin_name = "MoFox-Core-Webui"
    plugin_description = "MoFox-Team官方的WebUI插件"
    plugin_version = "1.0.0"

    dependent_components: list[str] = []

    def __init__(self, config=None):
        """初始化插件。"""
        super().__init__(config)
        logger.info(f"插件 {self.plugin_name} 初始化完成")

    def get_components(self) -> list[type]:
        """返回插件包含的所有组件。

        Returns:
            包含Routers和EventHandlers的组件列表
        """
        return [
            FrontendRouter, 
            ApiRouter, 
            StatsRouter, 
            SettingRouter,
            CoreConfigRouter, 
            ModelConfigRouter, 
            PluginConfigRouter,
            LogViewerRouter,
            RealtimeLogRouter,
            LiveChatRouter,
            ChatroomRouter,
            InitializationRouter,
            GitEnvRouter,
            GitUpdateRouter,
            UIUpdateRouter,
            ChatroomAdapter,
            LogEventHandler,
            LiveChatEventHandler
            ]

    async def on_plugin_loaded(self) -> None:
        """插件加载时的钩子。"""

    async def on_plugin_unloaded(self) -> None:
        """插件卸载时的钩子。"""


