"""
HTTP路由组件模块
"""

from .auth_router import WebUIAuthRouter
from .stats_router import WebUIStatsRouter

__all__ = [
    "WebUIAuthRouter",
    "WebUIStatsRouter",
]
