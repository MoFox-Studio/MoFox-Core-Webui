"""git_update 服务层共享 Pydantic 模型

这里是所有响应模型的唯一定义来源（Single Source of Truth）。
Router 层直接导入这些模型用作 response_model，避免重复定义。
"""

from __future__ import annotations

from pydantic import BaseModel


# ==================== 仓库状态 ====================

class RepoStatus(BaseModel):
    """仓库状态（对应前端 RepoStatus）"""
    is_git_repo: bool
    current_branch: str | None = None
    available_branches: list[str] = []
    error: str | None = None


# ==================== 更新检查 ====================

class UpdateCheck(BaseModel):
    """更新检查结果（对应前端 UpdateCheck）"""
    success: bool
    has_update: bool
    current_commit: str | None = None
    remote_commit: str | None = None
    commits_behind: int = 0
    update_logs: list[str] = []
    branch: str | None = None
    error: str | None = None


# ==================== 更新 / 回滚结果 ====================

class UpdateResult(BaseModel):
    """更新或回滚操作的结果（对应前端 UpdateResult）"""
    success: bool
    message: str
    updated_files: list[str] | None = None
    backup_commit: str | None = None
    error: str | None = None


# ==================== 切换分支 ====================

class SwitchBranchResult(BaseModel):
    """切换分支结果"""
    success: bool
    message: str
    current_branch: str | None = None
    error: str | None = None


# ==================== 历史版本 ====================

class FileChange(BaseModel):
    """单个文件变更记录"""
    status: str   # 新增 / 修改 / 删除 / 重命名
    path: str


class MainBackupInfo(BaseModel):
    """历史版本条目（对应前端 MainBackupInfo）"""
    commit: str
    commit_short: str
    message: str
    author: str = ""
    timestamp: str
    is_current: bool


class MainBackupsResponse(BaseModel):
    """历史版本列表响应"""
    success: bool
    data: list[MainBackupInfo] = []
    error: str | None = None


class MainCommitDetail(BaseModel):
    """Commit 详情（对应前端 MainCommitDetail）"""
    success: bool
    commit: str | None = None
    commit_short: str | None = None
    message: str | None = None
    body: str | None = None
    author: str | None = None
    timestamp: str | None = None
    files_changed: list[FileChange] | None = None
    stats: str | None = None
    error: str | None = None
