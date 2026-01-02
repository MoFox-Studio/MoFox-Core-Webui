"""
UI 更新路由组件
提供 WebUI 静态文件更新相关 API 接口
"""

from src.common.logger import get_logger
from src.common.security import VerifiedDep
from src.plugin_system import BaseRouterComponent

from ..utils.update import UIVersionManager
from ..utils.update.models import (
    UIStatsCheckResponse,
    UIUpdateResponse,
    UIRollbackRequest,
)

logger = get_logger("WebUI.UIUpdateRouter")


class UIUpdateRouterComponent(BaseRouterComponent):
    """UI 更新路由组件"""

    # ==================== 组件元数据 ====================

    component_name = "ui_update"
    component_description = "WebUI 静态文件更新接口"

    def register_endpoints(self) -> None:
        """注册路由"""

        @self.router.get("/status", summary="获取 UI 状态和检查更新")
        async def get_ui_status(_=VerifiedDep) -> UIStatsCheckResponse:
            """
            获取 WebUI 当前版本信息并检查更新
            合并了版本信息和更新检查功能
            """
            try:
                manager = UIVersionManager()
                result = await manager.check_update()
                return UIStatsCheckResponse(**result)
            except Exception as e:
                logger.error(f"获取 UI 状态失败: {e}")
                return UIStatsCheckResponse(
                    success=False, has_update=False, error=str(e)
                )

        @self.router.post("/update", summary="执行 UI 更新")
        async def update_ui(_=VerifiedDep) -> UIUpdateResponse:
            """下载并应用 WebUI 更新"""
            try:
                manager = UIVersionManager()
                result = await manager.download_and_apply()
                return UIUpdateResponse(**result)
            except Exception as e:
                logger.error(f"UI 更新失败: {e}")
                return UIUpdateResponse(success=False, message="更新失败", error=str(e))

        @self.router.get("/backups", summary="获取备份列表")
        async def list_backups(_=VerifiedDep):
            """获取 UI 备份列表"""
            try:
                manager = UIVersionManager()
                backups = manager.list_backups()
                return {"success": True, "data": backups}
            except Exception as e:
                logger.error(f"获取备份列表失败: {e}")
                return {"success": False, "error": str(e), "data": []}

        @self.router.post("/rollback", summary="回滚 UI 版本")
        async def rollback_ui(
            request: UIRollbackRequest, _=VerifiedDep
        ) -> UIUpdateResponse:
            """回滚到指定的 Git 提交"""
            try:
                manager = UIVersionManager()
                result = manager.rollback(request.commit_hash)
                return UIUpdateResponse(**result)
            except Exception as e:
                logger.error(f"UI 回滚失败: {e}")
                return UIUpdateResponse(success=False, message="回滚失败", error=str(e))

        @self.router.get("/commit/{commit_hash}", summary="获取提交详情")
        async def get_commit_detail(commit_hash: str, _=VerifiedDep):
            """获取指定提交的详细信息"""
            try:
                manager = UIVersionManager()
                result = manager.get_commit_detail(commit_hash)
                return result
            except Exception as e:
                logger.error(f"获取提交详情失败: {e}")
                return {"success": False, "error": str(e)}
