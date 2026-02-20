"""UI 更新路由组件

对应前端 @/api/ui_update.ts，完整实现以下端点：

    GET  /status              获取 UI 版本信息与更新检测（合并为一次请求）
    POST /update              执行 UI 更新（git pull --ff-only）
    GET  /backups             获取历史版本列表
    POST /rollback            回滚到指定 commit
    GET  /commit/{hash}       获取 commit 详情

注意：
- static/ 必须是以 webui-dist 为当前分支的独立 git 仓库
- 与 Neo-MoFox 主仓库（git_update）完全独立，互不干扰
"""

from __future__ import annotations

from pydantic import BaseModel

from src.kernel.logger import get_logger
from src.core.components.base.router import BaseRouter
from src.core.utils.security import VerifiedDep
from ..services.ui_update import (
    # 响应模型（Single Source of Truth 在 services/ui_update/models.py）
    UIStatusResult,
    UIUpdateResult,
    UIBackupsResponse,
    UICommitDetail,
    # 服务函数
    get_ui_status,
    update_ui,
    rollback_ui,
    get_ui_backups,
    get_ui_commit_detail,
)

logger = get_logger(name="UIUpdateRouter", color="#FAB387")


# ==================== 请求模型（仅路由层需要） ====================


class RollbackRequest(BaseModel):
    """回滚到指定 commit 的请求体。对应前端 rollbackUI(commitHash)"""
    commit_hash: str


# ==================== Router ====================


class UIUpdateRouter(BaseRouter):
    """UI 更新路由组件

    路径前缀: /webui/api/ui_update

    目标仓库: Webui_test_plugin/static/（独立 git 仓库，webui-dist 分支）
    """

    router_name = "UIUpdateRouter"
    router_description = "WebUI 静态文件更新、版本管理与回滚接口"

    custom_route_path = "/webui/api/ui_update"
    cors_origins = ["*"]

    def register_endpoints(self) -> None:
        """注册所有端点"""

        # -------- GET /status --------
        @self.app.get("/status", summary="获取 UI 状态", response_model=UIStatusResult)
        async def get_status(_=VerifiedDep) -> UIStatusResult:
            """一次性返回当前版本信息与远程更新检测结果。

            当 update_enabled=False 时说明 static/ 不是合法的可更新仓库，
            此时 has_update / latest_* / changelog 等字段无意义。
            """
            try:
                return await get_ui_status()
            except Exception as e:
                logger.error(f"获取 UI 状态失败: {e}")
                return UIStatusResult(success=False, error=str(e))

        # -------- POST /update --------
        @self.app.post("/update", summary="执行 UI 更新", response_model=UIUpdateResult)
        async def do_update(_=VerifiedDep) -> UIUpdateResult:
            """执行 git pull --ff-only 更新 UI 静态文件。

            仅当 static/ 处于 webui-dist 分支时允许操作。
            更新前自动记录当前 commit 作为回滚锚点（backup_commit 字段）。
            """
            try:
                return await update_ui()
            except Exception as e:
                logger.error(f"UI 更新失败: {e}")
                return UIUpdateResult(success=False, message=str(e), error=str(e))

        # -------- GET /backups --------
        @self.app.get("/backups", summary="获取历史版本列表", response_model=UIBackupsResponse)
        async def get_backups(_=VerifiedDep) -> UIBackupsResponse:
            """返回 static/ 仓库最近 20 条提交，每条附带版本 tag（若有）。"""
            try:
                return await get_ui_backups()
            except Exception as e:
                logger.error(f"获取 UI 历史版本失败: {e}")
                return UIBackupsResponse(success=False, error=str(e))

        # -------- POST /rollback --------
        @self.app.post("/rollback", summary="回滚 UI 版本", response_model=UIUpdateResult)
        async def do_rollback(body: RollbackRequest, _=VerifiedDep) -> UIUpdateResult:
            """将 static/ 仓库 reset --hard 到指定 commit 并清理未跟踪文件。"""
            try:
                return await rollback_ui(body.commit_hash)
            except Exception as e:
                logger.error(f"UI 回滚失败: {e}")
                return UIUpdateResult(success=False, message=str(e), error=str(e))

        # -------- GET /commit/{commit_hash} --------
        @self.app.get(
            "/commit/{commit_hash}",
            summary="获取 commit 详情",
            response_model=UICommitDetail,
        )
        async def get_commit_detail(commit_hash: str, _=VerifiedDep) -> UICommitDetail:
            """获取指定 commit 的完整信息，含变更文件列表与统计摘要。"""
            try:
                return await get_ui_commit_detail(commit_hash)
            except Exception as e:
                logger.error(f"获取 UI commit 详情失败: {e}")
                return UICommitDetail(success=False, error=str(e))

    async def startup(self) -> None:
        from ..services.ui_update.runner import PLUGIN_ROOT, is_ui_git_repo, ALLOWED_BRANCH
        is_repo = is_ui_git_repo()
        logger.info(
            f"UIUpdateRouter 已启动，路径: {self.custom_route_path}  "
            f"插件根目录: {PLUGIN_ROOT}  "
            f"是独立 git 仓库: {is_repo}  "
            f"允许分支: {ALLOWED_BRANCH}"
        )

    async def shutdown(self) -> None:
        logger.info("UIUpdateRouter 已关闭")
