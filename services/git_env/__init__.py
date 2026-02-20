"""Git 环境管理服务

公开接口：
- detector: Git 路径检测与版本查询
- installer: Git 安装（Windows 便携版 / 其他平台安装指南）
- manager:  高层协调接口（读写存储 + 检测）
"""

from .detector import detect_git_path, get_git_version, get_system_os, resolve_git_source
from .installer import install_git_windows, get_install_guide
from .manager import get_git_env_status, set_git_path, auto_detect_git

__all__ = [
    # detector
    "detect_git_path",
    "get_git_version",
    "get_system_os",
    "resolve_git_source",
    # installer
    "install_git_windows",
    "get_install_guide",
    # manager
    "get_git_env_status",
    "set_git_path",
    "auto_detect_git",
]
