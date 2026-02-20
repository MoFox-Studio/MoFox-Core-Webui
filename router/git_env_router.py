"""Git 环境管理路由组件

对应前端 @/api/git_env.ts，完整实现以下端点：

    GET  /status         获取 Git 环境状态
    POST /install        安装 Git（Windows 下载便携版）
    POST /set-path       设置自定义 Git 路径
    POST /auto-detect    清除配置并重新自动检测
    GET  /install-guide  获取当前平台安装指南
"""

from __future__ import annotations

from pydantic import BaseModel

from src.kernel.logger import get_logger
from src.core.components.base.router import BaseRouter
from src.core.utils.security import VerifiedDep
from ..services.git_env import (
    get_git_env_status,
    set_git_path,
    auto_detect_git,
    install_git_windows,
    get_install_guide,
    get_system_os,
)

logger = get_logger(name="GitEnvRouter", color="#CBA6F7")


# ==================== Pydantic Models ====================

from typing import Literal


class GitEnvStatus(BaseModel):
    """Git 环境状态（对应前端 GitEnvStatus）"""
    git_available: bool
    git_version: str | None = None
    git_path: str | None = None
    git_source: Literal["custom", "portable", "system", "unknown"] = "unknown"
    is_portable: bool = False
    system_os: str


class GitInstallResult(BaseModel):
    """Git 安装结果（对应前端 GitInstallResult）"""
    success: bool
    message: str
    install_path: str | None = None
    error: str | None = None


class GitSetPathResult(BaseModel):
    """Git 路径设置/检测结果（对应前端 GitSetPathResult）"""
    success: bool
    message: str
    git_path: str | None = None
    git_version: str | None = None
    error: str | None = None


class GitInstallGuide(BaseModel):
    """Git 安装指南（对应前端 GitInstallGuide）"""
    platform: str
    method: str
    description: str
    manual_url: str | None = None
    manual_commands: dict[str, str] | None = None


class GitInstallGuideResponse(BaseModel):
    """安装指南响应（含 success 包装）"""
    success: bool
    data: GitInstallGuide | None = None
    error: str | None = None


class SetPathRequest(BaseModel):
    """设置 Git 路径请求"""
    path: str


# ==================== Router ====================


class GitEnvRouter(BaseRouter):
    """Git 环境管理路由组件

    路径前缀: /webui/api/git_env
    """

    router_name = "GitEnvRouter"
    router_description = "Git 环境检测与配置管理接口"

    custom_route_path = "/webui/api/git_env"
    cors_origins = ["*"]

    def register_endpoints(self) -> None:
        """注册所有端点"""

        # -------- GET /status --------
        @self.app.get("/status", summary="获取 Git 环境状态", response_model=GitEnvStatus)
        async def get_status(_=VerifiedDep) -> GitEnvStatus:
            """返回当前 Git 环境的完整状态信息"""
            try:
                data = await get_git_env_status()
                return GitEnvStatus(**data)
            except Exception as e:
                logger.error(f"获取 Git 状态失败: {e}")
                from fastapi import HTTPException
                raise HTTPException(status_code=500, detail=str(e))

        # -------- POST /install --------
        @self.app.post("/install", summary="安装 Git", response_model=GitInstallResult)
        async def install_git(_=VerifiedDep) -> GitInstallResult:
            """Windows：下载便携版 MinGit 并解压到 git/ 目录。其他平台返回不支持提示。"""
            try:
                if get_system_os() != "Windows":
                    return GitInstallResult(
                        success=False,
                        message="自动安装便携版 Git 仅支持 Windows，请参阅安装指南",
                        error="unsupported_platform",
                    )
                result = await install_git_windows()
                return GitInstallResult(**result)
            except Exception as e:
                logger.error(f"安装 Git 失败: {e}")
                return GitInstallResult(success=False, message="安装过程出现错误", error=str(e))

        # -------- POST /set-path --------
        @self.app.post("/set-path", summary="设置自定义 Git 路径", response_model=GitSetPathResult)
        async def set_path(body: SetPathRequest, _=VerifiedDep) -> GitSetPathResult:
            """验证指定路径是否为有效的 Git 可执行文件，验证通过后持久化保存。"""
            try:
                result = await set_git_path(body.path)
                return GitSetPathResult(**result)
            except Exception as e:
                logger.error(f"设置 Git 路径失败: {e}")
                return GitSetPathResult(success=False, message="设置失败", error=str(e))

        # -------- POST /auto-detect --------
        @self.app.post("/auto-detect", summary="自动检测 Git", response_model=GitSetPathResult)
        async def auto_detect(_=VerifiedDep) -> GitSetPathResult:
            """清除当前自定义 Git 路径配置，重新扫描系统自动检测。"""
            try:
                result = await auto_detect_git()
                return GitSetPathResult(**result)
            except Exception as e:
                logger.error(f"自动检测 Git 失败: {e}")
                return GitSetPathResult(success=False, message="检测失败", error=str(e))

        # -------- GET /install-guide --------
        @self.app.get("/install-guide", summary="获取 Git 安装指南", response_model=GitInstallGuideResponse)
        async def install_guide(_=VerifiedDep) -> GitInstallGuideResponse:
            """返回当前操作系统对应的 Git 安装方式与命令参考。"""
            try:
                guide = get_install_guide()
                return GitInstallGuideResponse(success=True, data=GitInstallGuide(**guide))
            except Exception as e:
                logger.error(f"获取安装指南失败: {e}")
                return GitInstallGuideResponse(success=False, error=str(e))

    async def startup(self) -> None:
        logger.info(f"GitEnvRouter 已启动，路径: {self.custom_route_path}")

    async def shutdown(self) -> None:
        logger.info("GitEnvRouter 已关闭")
