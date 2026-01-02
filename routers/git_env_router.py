"""
Git 环境管理路由组件
提供 Git 环境检测、安装、路径配置等 API 接口
"""

import platform
from pathlib import Path

from fastapi import APIRouter

from src.common.logger import get_logger
from src.common.security import VerifiedDep
from src.plugin_system import BaseRouterComponent

from ..utils.update import (
    GitDetector,
    GitInstaller,
    GitStatusResponse,
    GitInstallResponse,
    GitSetPathRequest,
    GitSetPathResponse,
)

from ..utils.backend_storage import BackendStorage

logger = get_logger("WebUI.GitEnvRouter")


class GitEnvRouterComponent(BaseRouterComponent):
    """Git 环境管理路由组件"""

    # ==================== 组件元数据 ====================

    component_name = "git_env"
    component_description = "Git 环境管理接口"

    def register_endpoints(self) -> None:
        """注册路由"""

        @self.router.get("/status", summary="获取 Git 环境状态")
        async def get_git_status(_ = VerifiedDep) -> GitStatusResponse:
            """获取当前 Git 环境状态"""
            try:
                git_available = GitDetector.is_git_available()
                git_version = GitDetector.get_git_version() if git_available else None
                git_path = GitDetector.get_git_executable()
                git_source = GitDetector.get_git_source()

                return GitStatusResponse(
                    git_available=git_available,
                    git_version=git_version,
                    git_path=git_path,
                    git_source=git_source,
                    is_portable=git_source == "portable",
                    system_os=platform.system(),
                )
            except Exception as e:
                logger.error(f"获取 Git 状态失败: {e}")
                return GitStatusResponse(
                    git_available=False,
                    system_os=platform.system(),
                )

        @self.router.post("/install", summary="安装 Git")
        async def install_git(_ = VerifiedDep) -> GitInstallResponse:
            """自动安装 Git"""
            try:
                result = await GitInstaller.install_git()
                return GitInstallResponse(**result)
            except Exception as e:
                logger.error(f"安装 Git 失败: {e}")
                return GitInstallResponse(
                    success=False,
                    message="安装失败",
                    error=str(e)
                )

        @self.router.post("/set-path", summary="设置自定义 Git 路径")
        async def set_git_path(request: GitSetPathRequest,_ = VerifiedDep) -> GitSetPathResponse:
            """设置自定义 Git 可执行文件路径"""
            try:
                git_path = Path(request.path)
                
                # 验证路径是否存在
                if not git_path.exists():
                    return GitSetPathResponse(
                        success=False,
                        message="路径不存在",
                        error=f"文件不存在: {request.path}"
                    )
                
                # 验证是否为有效的 Git 可执行文件
                import subprocess
                try:
                    result = subprocess.run(
                        [str(git_path), "--version"],
                        capture_output=True,
                        text=True,
                        timeout=5,
                    )
                    if result.returncode != 0:
                        return GitSetPathResponse(
                            success=False,
                            message="无效的 Git 可执行文件",
                            error="该文件不是有效的 Git 可执行文件"
                        )
                    
                    # 提取版本信息
                    version_line = result.stdout.strip()
                    git_version = version_line.split("git version")[-1].strip() if "git version" in version_line else version_line
                    
                except subprocess.TimeoutExpired:
                    return GitSetPathResponse(
                        success=False,
                        message="验证超时",
                        error="执行 Git 命令超时"
                    )
                
                # 保存路径
                BackendStorage.set_git_path(str(git_path))
                BackendStorage.set_git_source("custom")
                
                logger.info(f"已设置自定义 Git 路径: {git_path}")
                
                return GitSetPathResponse(
                    success=True,
                    message="Git 路径设置成功",
                    git_path=str(git_path),
                    git_version=git_version
                )
                
            except Exception as e:
                logger.error(f"设置 Git 路径失败: {e}")
                return GitSetPathResponse(
                    success=False,
                    message="设置失败",
                    error=str(e)
                )

        @self.router.post("/auto-detect", summary="自动检测 Git")
        async def auto_detect_git(_ = VerifiedDep) -> GitSetPathResponse:
            """清除当前配置并重新自动检测 Git"""
            try:
                BackendStorage.clear_git_path()
                BackendStorage.set_git_source("unknown")
                
                # 重新检测 Git
                git_path = GitDetector.get_git_executable()
                
                if git_path:
                    git_version = GitDetector.get_git_version()
                    git_source = BackendStorage.get_git_source()
                    
                    source_label = {
                        "portable": "便携版",
                        "system": "系统",
                        "custom": "自定义"
                    }.get(git_source, "")
                    
                    message = f"已检测到 Git ({source_label})" if source_label else "已检测到 Git"
                    logger.info(f"自动检测到 Git: {git_path} ({source_label})")
                    
                    return GitSetPathResponse(
                        success=True,
                        message=message,
                        git_path=git_path,
                        git_version=git_version
                    )
                else:
                    logger.info("自动检测未找到 Git")
                    return GitSetPathResponse(
                        success=False,
                        message="未检测到 Git",
                        error="系统中未找到 Git，请手动设置路径或下载便携版"
                    )
                    
            except Exception as e:
                logger.error(f"自动检测 Git 失败: {e}")
                return GitSetPathResponse(
                    success=False,
                    message="检测失败",
                    error=str(e)
                )

        @self.router.get("/install-guide", summary="获取安装指南")
        async def get_install_guide(_ = VerifiedDep):
            """获取当前系统的 Git 安装指南"""
            try:
                guide = GitInstaller.get_system_install_guide()
                return {
                    "success": True,
                    "data": guide
                }
            except Exception as e:
                logger.error(f"获取安装指南失败: {e}")
                return {
                    "success": False,
                    "error": str(e)
                }


