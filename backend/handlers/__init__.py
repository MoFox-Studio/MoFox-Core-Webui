"""
事件处理器模块
"""

from .startup_handler import WebUIStartupHandler
from .shutdown_handler import WebUIShutdownHandler

__all__ = [
    "WebUIStartupHandler",
    "WebUIShutdownHandler",
]
