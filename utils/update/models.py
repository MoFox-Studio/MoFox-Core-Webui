"""
Pydantic 数据模型
集中管理所有更新相关的数据模型
"""

from typing import Optional, List
from pydantic import BaseModel


# ==================== Git 相关模型 ====================


class GitStatusResponse(BaseModel):
    """Git 环境状态响应"""

    git_available: bool
    git_version: Optional[str] = None
    git_path: Optional[str] = None
    git_source: str = "unknown"  # 'custom' | 'portable' | 'system' | 'unknown'
    is_portable: bool = False
    system_os: str


class GitCheckUpdateResponse(BaseModel):
    """检查更新响应"""

    success: bool
    has_update: bool = False
    current_commit: Optional[str] = None
    remote_commit: Optional[str] = None
    commits_behind: int = 0
    update_logs: List[str] = []
    branch: Optional[str] = None
    error: Optional[str] = None


class GitUpdateRequest(BaseModel):
    """更新请求"""

    force: bool = False
    stash_local: bool = True
    create_backup: bool = True


class GitUpdateResponse(BaseModel):
    """更新响应"""

    success: bool
    message: str
    updated_files: List[str] = []
    backup_commit: Optional[str] = None
    error: Optional[str] = None
    dependencies_installed: bool = False  # 是否已安装依赖
    dependencies_message: Optional[str] = None  # 依赖安装信息
    venv_type: Optional[str] = None  # 虚拟环境类型


class GitRollbackRequest(BaseModel):
    """回滚请求"""

    commit_hash: str


class GitSwitchBranchRequest(BaseModel):
    """切换分支请求"""

    branch: str


class GitSwitchBranchResponse(BaseModel):
    """切换分支响应"""

    success: bool
    message: str
    current_branch: Optional[str] = None
    error: Optional[str] = None
    dependencies_installed: bool = False  # 是否已安装依赖
    dependencies_message: Optional[str] = None  # 依赖安装信息
    venv_type: Optional[str] = None  # 虚拟环境类型


class GitInstallResponse(BaseModel):
    """Git 安装响应"""

    success: bool
    message: str
    install_path: Optional[str] = None
    error: Optional[str] = None


class GitSetPathRequest(BaseModel):
    """设置 Git 路径请求"""

    path: str


class GitSetPathResponse(BaseModel):
    """设置 Git 路径响应"""

    success: bool
    message: str
    git_path: Optional[str] = None
    git_version: Optional[str] = None
    error: Optional[str] = None


# ==================== UI 更新相关模型 ====================


class UIFileInfo(BaseModel):
    """UI 文件信息"""
    
    path: str
    hash: str
    size: int


class UIVersionInfo(BaseModel):
    """UI 版本信息"""

    version: str
    build_time: str
    commit: str
    branch: str
    files: List[UIFileInfo] = []
    changelog: List[str] = []


class UIStatsCheckResponse(BaseModel):
    """UI 版本状态响应"""

    success: bool
    has_update: bool = False
    current_version: Optional[str] = None
    current_commit: Optional[str] = None
    latest_version: Optional[str] = None
    latest_commit: Optional[str] = None
    changelog: List[str] = []
    commits_behind: int = 0
    download_size: Optional[int] = None
    error: Optional[str] = None
    # 更新功能是否启用
    update_enabled: bool = True
    # 当前分支
    current_branch: Optional[str] = None
    # 提示信息
    message: Optional[str] = None


class UIUpdateResponse(BaseModel):
    """UI 更新响应"""

    success: bool
    message: str
    version: Optional[str] = None
    backup_commit: Optional[str] = None  # 更新前的提交 hash（用于回滚）
    commit: Optional[str] = None  # 当前提交 hash
    commit_short: Optional[str] = None  # 当前提交简短 hash
    error: Optional[str] = None


class UIBackupInfo(BaseModel):
    """UI 备份信息（Git 提交记录）"""

    commit: str  # 完整 commit hash
    commit_short: str  # 简短 commit hash
    version: Optional[str] = None  # 版本号
    message: str  # 提交消息
    timestamp: str  # 提交时间
    is_current: bool = False  # 是否是当前版本


class UIRollbackRequest(BaseModel):
    """UI 回滚请求"""

    commit_hash: str  # 要回滚到的 commit hash
