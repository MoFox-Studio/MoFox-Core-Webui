"""主程序更新路由组件

对应前端 @/api/git_update.ts，完整实现以下端点：

    GET  /status             获取仓库状态（当前分支、可用分支）
    POST /refresh-branches   fetch 远程并刷新分支列表
    GET  /check              检查是否有可用更新
    POST /update             执行主程序更新（git pull）
    POST /rollback           回滚到指定 commit
    POST /switch-branch      切换分支
    GET  /backups            获取历史版本列表
    GET  /commits/{hash}     获取 commit 详情
"""

from __future__ import annotations

from pydantic import BaseModel

from src.kernel.logger import get_logger
from src.core.components.base.router import BaseRouter
from src.core.utils.security import VerifiedDep
from ..services.git_update import (
    # 响应模型（Single Source of Truth 在 services/git_update/models.py）
    RepoStatus,
    UpdateCheck,
    UpdateResult,
    SwitchBranchResult,
    MainBackupInfo,
    MainBackupsResponse,
    MainCommitDetail,
    # 服务函数
    get_repo_status,
    refresh_branches,
    check_updates,
    update_main_program,
    switch_branch,
    get_main_backups,
    get_main_commit_detail,
    rollback_version,
)

logger = get_logger(name="GitUpdateRouter", color="#A6E3A1")


# ==================== 请求模型（仅路由层需要） ====================


class UpdateRequest(BaseModel):
    """执行更新请求"""
    force: bool = False
    create_backup: bool = True


class RollbackRequest(BaseModel):
    """回滚请求"""
    commit_hash: str


class SwitchBranchRequest(BaseModel):
    """切换分支请求"""
    branch: str


# ==================== Router ====================


class GitUpdateRouter(BaseRouter):
    """主程序更新路由组件

    路径前缀: /webui/api/git_update
    """

    router_name = "GitUpdateRouter"
    router_description = "主程序 Git 更新、回滚与分支管理接口"

    custom_route_path = "/webui/api/git_update"
    cors_origins = ["*"]

    def register_endpoints(self) -> None:
        """注册所有端点"""

        # -------- GET /status --------
        @self.app.get("/status", summary="获取仓库状态", response_model=RepoStatus)
        async def get_status(_=VerifiedDep) -> RepoStatus:
            """返回当前分支和全部可用分支列表"""
            try:
                return await get_repo_status()
            except Exception as e:
                logger.error(f"获取仓库状态失败: {e}")
                return RepoStatus(is_git_repo=False, error=str(e))

        # -------- POST /refresh-branches --------
        @self.app.post("/refresh-branches", summary="刷新远程分支", response_model=RepoStatus)
        async def do_refresh_branches(_=VerifiedDep) -> RepoStatus:
            """fetch 远程仓库并返回最新分支列表（需要网络，可能较慢）"""
            try:
                return await refresh_branches()
            except Exception as e:
                logger.error(f"刷新分支列表失败: {e}")
                return RepoStatus(is_git_repo=False, error=str(e))

        # -------- GET /check --------
        @self.app.get("/check", summary="检查更新", response_model=UpdateCheck)
        async def do_check_updates(_=VerifiedDep) -> UpdateCheck:
            """fetch 远程并对比提交差距，返回是否有可用更新及变更日志"""
            try:
                return await check_updates()
            except Exception as e:
                logger.error(f"检查更新失败: {e}")
                return UpdateCheck(success=False, has_update=False, error=str(e))

        # -------- POST /update --------
        @self.app.post("/update", summary="执行更新", response_model=UpdateResult)
        async def do_update(body: UpdateRequest, _=VerifiedDep) -> UpdateResult:
            """执行 git pull 更新主程序，支持强制更新（丢弃本地修改）"""
            try:
                return await update_main_program(
                    force=body.force,
                    create_backup=body.create_backup,
                )
            except Exception as e:
                logger.error(f"执行更新失败: {e}")
                return UpdateResult(success=False, message=str(e), error=str(e))

        # -------- POST /rollback --------
        @self.app.post("/rollback", summary="回滚版本", response_model=UpdateResult)
        async def do_rollback(body: RollbackRequest, _=VerifiedDep) -> UpdateResult:
            """将仓库 hard reset 到指定 commit，同时清理未跟踪文件"""
            try:
                return await rollback_version(body.commit_hash)
            except Exception as e:
                logger.error(f"回滚失败: {e}")
                return UpdateResult(success=False, message=str(e), error=str(e))

        # -------- POST /switch-branch --------
        @self.app.post("/switch-branch", summary="切换分支", response_model=SwitchBranchResult)
        async def do_switch_branch(body: SwitchBranchRequest, _=VerifiedDep) -> SwitchBranchResult:
            """切换到指定分支，本地不存在时自动跟踪远程分支"""
            try:
                return await switch_branch(body.branch)
            except Exception as e:
                logger.error(f"切换分支失败: {e}")
                return SwitchBranchResult(success=False, message=str(e), error=str(e))

        # -------- GET /backups --------
        @self.app.get("/backups", summary="获取历史版本列表", response_model=MainBackupsResponse)
        async def get_backups(_=VerifiedDep) -> MainBackupsResponse:
            """返回最近 20 条提交记录，每条可作为回滚"锚点"""
            try:
                return await get_main_backups()
            except Exception as e:
                logger.error(f"获取历史版本列表失败: {e}")
                return MainBackupsResponse(success=False, error=str(e))

        # -------- GET /commits/{commit_hash} --------
        @self.app.get("/commits/{commit_hash}", summary="获取 commit 详情", response_model=MainCommitDetail)
        async def get_commit_detail(commit_hash: str, _=VerifiedDep) -> MainCommitDetail:
            """获取指定 commit 的完整信息，包含变更文件列表"""
            try:
                return await get_main_commit_detail(commit_hash)
            except Exception as e:
                logger.error(f"获取 commit 详情失败: {e}")
                return MainCommitDetail(success=False, error=str(e))

    async def startup(self) -> None:
        from ..services.git_update.runner import REPO_ROOT
        logger.info(
            f"GitUpdateRouter 已启动，路径: {self.custom_route_path}  "
            f"仓库根目录: {REPO_ROOT}"
        )

    async def shutdown(self) -> None:
        logger.info("GitUpdateRouter 已关闭")
