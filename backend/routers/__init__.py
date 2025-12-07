"""
HTTP路由组件模块
"""

from .auth_router import WebUIAuthRouter
from .config_router import WebUIConfigRouter
from .git_update_router import GitUpdateRouterComponent
from .marketplace_router import MarketplaceRouterComponent
from .plugin_router import WebUIPluginRouter
from .stats_router import WebUIStatsRouter

__all__ = [
    "GitUpdateRouterComponent",
    "MarketplaceRouterComponent",
    "WebUIAuthRouter",
    "WebUIConfigRouter",
    "WebUIPluginRouter",
    "WebUIStatsRouter",
]
