"""UI 更新服务

目标是 Webui_test_plugin 插件根目录本身就是一个独立 git 仓库（webui-dist 分支），
与 Neo-MoFox 主仓库完全无关。

公开接口：
- models:   Pydantic 响应模型（Single Source of Truth）
- runner:   底层 git 命令封装（PLUGIN_ROOT、ALLOWED_BRANCH、run_ui_git 等）
- status:   获取 UI 版本与更新状态（get_ui_status）
- updater:  执行更新与回滚（update_ui、rollback_ui）
- history:  历史版本列表与 commit 详情（get_ui_backups、get_ui_commit_detail）
"""

from .models import (
    UIStatusResult,
    UIUpdateResult,
    UIBackupInfo,
    UIBackupsResponse,
    UICommitDetail,
    FileChange,
)
from .runner import (
    PLUGIN_ROOT,
    ALLOWED_BRANCH,
    is_ui_git_repo,
    run_ui_git,
    get_ui_branch,
    get_ui_version,
)
from .status import get_ui_status
from .updater import update_ui, rollback_ui
from .history import get_ui_backups, get_ui_commit_detail

__all__ = [
    # models
    "UIStatusResult",
    "UIUpdateResult",
    "UIBackupInfo",
    "UIBackupsResponse",
    "UICommitDetail",
    "FileChange",
    # runner
    "PLUGIN_ROOT",
    "ALLOWED_BRANCH",
    "is_ui_git_repo",
    "run_ui_git",
    "get_ui_branch",
    "get_ui_version",
    # status
    "get_ui_status",
    # updater
    "update_ui",
    "rollback_ui",
    # history
    "get_ui_backups",
    "get_ui_commit_detail",
]
