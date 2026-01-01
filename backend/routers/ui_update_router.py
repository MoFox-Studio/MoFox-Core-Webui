"""
UI 更新路由组件
提供 WebUI 静态文件更新相关 API 接口
"""

from fastapi import APIRouter

from src.common.logger import get_logger
from src.common.security import VerifiedDep
from src.plugin_system import BaseRouterComponent

from ..utils.update import UIVersionManager
from ..utils.update.models import (
    UIUpdateCheckResponse,
    UIUpdateResponse,
    UIRollbackRequest,
)

logger = get_logger("WebUI.UIUpdateRouter")


class UIUpdateRouterComponent(BaseRouterComponent):
    """UI 更新路由组件"""

    # ==================== 路由注册信息 ====================

    @classmethod
    def get_router_info(cls):
        return {
            "name": "ui_update_router",
            "prefix": "/ui_update",
            "description": "WebUI 静态文件更新接口",
        }

    def register_routes(self, router: APIRouter):
        """注册路由"""

        @router.get("/version", summary="获取当前 UI 版本")
        async def get_ui_version(_=VerifiedDep):
            """获取当前 WebUI 静态文件版本"""
            try:
                manager = UIVersionManager()
                version_info = manager.get_current_version()

                if version_info:
                    return {"success": True, "data": version_info}
                else:
                    return {
                        "success": True,
                        "data": {
                            "version": "未安装",
                            "build_time": None,
                            "commit": None,
                            "branch": None,
                            "changelog": [],
                        },
                    }
            except Exception as e:
                logger.error(f"获取 UI 版本失败: {e}")
                return {"success": False, "error": str(e)}

        @router.get("/check", summary="检查 UI 更新")
        async def check_ui_update(_=VerifiedDep) -> UIUpdateCheckResponse:
            """检查 WebUI 是否有可用更新"""
            try:
                manager = UIVersionManager()
                result = await manager.check_update()
                return UIUpdateCheckResponse(**result)
            except Exception as e:
                logger.error(f"检查 UI 更新失败: {e}")
                return UIUpdateCheckResponse(
                    success=False, has_update=False, error=str(e)
                )

        @router.post("/update", summary="执行 UI 更新")
        async def update_ui(_=VerifiedDep) -> UIUpdateResponse:
            """下载并应用 WebUI 更新"""
            try:
                manager = UIVersionManager()
                result = await manager.download_and_apply()
                return UIUpdateResponse(**result)
            except Exception as e:
                logger.error(f"UI 更新失败: {e}")
                return UIUpdateResponse(success=False, message="更新失败", error=str(e))

        @router.get("/backups", summary="获取备份列表")
        async def list_backups(_=VerifiedDep):
            """获取 UI 备份列表"""
            try:
                manager = UIVersionManager()
                backups = manager.list_backups()
                return {"success": True, "data": backups}
            except Exception as e:
                logger.error(f"获取备份列表失败: {e}")
                return {"success": False, "error": str(e), "data": []}

        @router.post("/rollback", summary="回滚 UI 版本")
        async def rollback_ui(
            request: UIRollbackRequest, _=VerifiedDep
        ) -> UIUpdateResponse:
            """回滚到指定的备份版本"""
            try:
                manager = UIVersionManager()
                result = manager.rollback(request.backup_name)
                return UIUpdateResponse(**result)
            except Exception as e:
                logger.error(f"UI 回滚失败: {e}")
                return UIUpdateResponse(success=False, message="回滚失败", error=str(e))
