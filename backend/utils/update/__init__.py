"""
更新工具模块
提供 Git 环境检测、安装、更新等功能
"""

from .models import (
    GitStatusResponse,
    GitCheckUpdateResponse,
    GitUpdateRequest,
    GitUpdateResponse,
    GitRollbackRequest,
    GitSwitchBranchRequest,
    GitSwitchBranchResponse,
    GitInstallResponse,
    GitSetPathRequest,
    GitSetPathResponse,
    UIVersionInfo,
    UIUpdateCheckResponse,
    UIUpdateResponse,
    UIBackupInfo,
)
from .git_detector import GitDetector
from .git_installer import GitInstaller
from .git_updater import GitUpdater
from .venv_utils import VenvDetector, DependencyInstaller
from .ui_version_manager import UIVersionManager

__all__ = [
    # Models
    "GitStatusResponse",
    "GitCheckUpdateResponse",
    "GitUpdateRequest",
    "GitUpdateResponse",
    "GitRollbackRequest",
    "GitSwitchBranchRequest",
    "GitSwitchBranchResponse",
    "GitInstallResponse",
    "GitSetPathRequest",
    "GitSetPathResponse",
    "UIVersionInfo",
    "UIUpdateCheckResponse",
    "UIUpdateResponse",
    "UIBackupInfo",
    # Utils
    "GitDetector",
    "GitInstaller",
    "GitUpdater",
    "VenvDetector",
    "DependencyInstaller",
    "UIVersionManager",
]
