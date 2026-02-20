"""UI 更新服务层共享 Pydantic 模型

对应前端 @/api/ui_update.ts，是所有响应模型的唯一定义来源（Single Source of Truth）。
Router 层直接导入这些模型用作 response_model，避免重复定义。
"""

from __future__ import annotations

from pydantic import BaseModel


# ==================== 文件变更（复用） ====================

class FileChange(BaseModel):
    """单个文件变更记录"""
    status: str   # 新增 / 修改 / 删除 / 重命名
    path: str


# ==================== UI 状态（合并了版本信息和更新检查） ====================

class UIStatusResult(BaseModel):
    """UI 状态响应（对应前端 UIStatusResult）

    一次请求同时返回版本信息与更新检测结果。
    当 update_enabled=False 时，has_update / latest_* / changelog 等字段无意义。
    """
    success: bool
    # 是否有更新
    has_update: bool = False
    # 当前版本
    current_version: str | None = None
    current_commit: str | None = None
    # 远程版本
    latest_version: str | None = None
    latest_commit: str | None = None
    # 更新日志（每条 oneline commit 消息）
    changelog: list[str] = []
    commits_behind: int | None = None
    # 更新功能是否启用
    update_enabled: bool | None = None
    # 当前分支
    current_branch: str | None = None
    # 提示信息（禁用原因等）
    message: str | None = None
    # 错误信息
    error: str | None = None


# ==================== 更新 / 回滚结果 ====================

class UIUpdateResult(BaseModel):
    """更新或回滚操作的结果（对应前端 UIUpdateResult）"""
    success: bool
    message: str
    version: str | None = None
    backup_commit: str | None = None   # 更新前的提交 hash（用于回滚）
    commit: str | None = None          # 当前提交 hash
    commit_short: str | None = None    # 当前提交简短 hash
    error: str | None = None


# ==================== 历史版本 ====================

class UIBackupInfo(BaseModel):
    """历史版本条目（对应前端 UIBackupInfo）"""
    commit: str           # 完整 commit hash
    commit_short: str     # 简短 commit hash
    version: str | None = None   # 版本号（如 v1.2.3）
    message: str          # 提交消息
    timestamp: str        # 提交时间
    is_current: bool      # 是否是当前版本


class UIBackupsResponse(BaseModel):
    """历史版本列表响应"""
    success: bool
    data: list[UIBackupInfo] = []
    error: str | None = None


# ==================== Commit 详情 ====================

class UICommitDetail(BaseModel):
    """Commit 详情（对应前端 UICommitDetail）"""
    success: bool
    commit: str | None = None
    commit_short: str | None = None
    version: str | None = None
    message: str | None = None
    body: str | None = None
    author: str | None = None
    timestamp: str | None = None
    files_changed: list[FileChange] | None = None
    stats: str | None = None
    error: str | None = None
