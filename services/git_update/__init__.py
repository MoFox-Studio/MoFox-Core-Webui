"""主程序 Git 更新服务

公开接口：
- models:   共享 Pydantic 响应模型（Single Source of Truth）
- runner:   底层 git 命令执行（get_git_executable, run_git, is_repo_available, REPO_ROOT）
- status:   仓库状态与分支管理（get_repo_status, refresh_branches）
- updater:  检查与执行更新、切换分支（check_updates, update_main_program, switch_branch）
- history:  历史版本列表、详情与回滚（get_main_backups, get_main_commit_detail, rollback_version）
"""

from .models import (
    RepoStatus,
    UpdateCheck,
    UpdateResult,
    SwitchBranchResult,
    FileChange,
    MainBackupInfo,
    MainBackupsResponse,
    MainCommitDetail,
)
from .runner import run_git, get_git_executable, is_repo_available, REPO_ROOT
from .status import get_repo_status, refresh_branches
from .updater import check_updates, update_main_program, switch_branch
from .history import get_main_backups, get_main_commit_detail, rollback_version

__all__ = [
    # models
    "RepoStatus",
    "UpdateCheck",
    "UpdateResult",
    "SwitchBranchResult",
    "FileChange",
    "MainBackupInfo",
    "MainBackupsResponse",
    "MainCommitDetail",
    # runner
    "run_git",
    "get_git_executable",
    "is_repo_available",
    "REPO_ROOT",
    # status
    "get_repo_status",
    "refresh_branches",
    # updater
    "check_updates",
    "update_main_program",
    "switch_branch",
    # history
    "get_main_backups",
    "get_main_commit_detail",
    "rollback_version",
]
