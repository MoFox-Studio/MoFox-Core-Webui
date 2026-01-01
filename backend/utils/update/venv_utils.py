"""
虚拟环境工具
检测虚拟环境类型和安装依赖
"""

import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Optional

from src.common.logger import get_logger

logger = get_logger("WebUI.VenvUtils")


class VenvDetector:
    """虚拟环境检测器"""

    @staticmethod
    def detect_venv_type(project_root: Path) -> Optional[str]:
        """
        检测虚拟环境类型
        返回: 'uv' | 'venv' | 'conda' | None
        """
        # 检查是否在虚拟环境中
        in_venv = hasattr(sys, "real_prefix") or (
            hasattr(sys, "base_prefix") and sys.base_prefix != sys.prefix
        )

        if not in_venv:
            logger.warning("当前不在虚拟环境中")
            return None

        venv_path = Path(sys.prefix)

        # 1. 检测 uv (优先检查 pyvenv.cfg 文件)
        pyvenv_cfg = venv_path / "pyvenv.cfg"
        if pyvenv_cfg.exists():
            try:
                with open(pyvenv_cfg) as f:
                    content = f.read()
                    if "uv = " in content:
                        logger.info("检测到 uv 虚拟环境 (pyvenv.cfg)")
                        return "uv"
            except Exception as e:
                logger.warning(f"读取 pyvenv.cfg 失败: {e}")

        # 2. 检测 conda (检查环境变量和路径)
        if "CONDA_DEFAULT_ENV" in os.environ or "CONDA_PREFIX" in os.environ:
            logger.info("检测到 conda 虚拟环境")
            return "conda"

        # 通过路径特征检测 conda
        if "conda" in str(venv_path).lower() or "anaconda" in str(venv_path).lower():
            logger.info(f"检测到 conda 虚拟环境 (路径: {venv_path})")
            return "conda"

        # 3. 默认为 venv (标准 Python 虚拟环境)
        logger.info(f"检测到标准 venv 虚拟环境 (路径: {venv_path})")
        return "venv"

    @staticmethod
    def get_requirements_file(project_root: Path) -> Optional[Path]:
        """获取依赖文件路径"""
        req_file = project_root / "requirements.txt"

        if req_file.exists():
            logger.info(f"找到依赖文件: {req_file}")
            return req_file

        logger.warning("未找到依赖文件")
        return None


class DependencyInstaller:
    """依赖安装器"""

    @staticmethod
    async def install_dependencies(project_root: Path, venv_type: str) -> dict:
        """
        根据虚拟环境类型安装依赖
        """
        try:
            logger.info(f"开始安装依赖 (虚拟环境类型: {venv_type})")

            # 获取依赖文件
            req_file = VenvDetector.get_requirements_file(project_root)
            if not req_file:
                return {"success": False, "error": "未找到 requirements.txt 文件"}

            # 根据虚拟环境类型选择安装命令
            if venv_type == "uv":
                return await DependencyInstaller._install_with_uv(project_root, req_file)
            elif venv_type == "conda":
                return await DependencyInstaller._install_with_conda(project_root, req_file)
            elif venv_type == "venv":
                return await DependencyInstaller._install_with_pip(project_root, req_file)
            else:
                return {"success": False, "error": f"不支持的虚拟环境类型: {venv_type}"}

        except Exception as e:
            logger.error(f"安装依赖失败: {e}")
            return {"success": False, "error": str(e)}

    @staticmethod
    async def _install_with_uv(project_root: Path, req_file: Path) -> dict:
        """使用 uv 安装依赖"""
        try:
            logger.info("使用 uv 安装依赖...")

            # 检查 uv 是否可用
            uv_path = shutil.which("uv")
            if not uv_path:
                return {"success": False, "error": "uv 未安装或不在 PATH 中"}

            # 使用 uv pip install
            result = subprocess.run(
                [uv_path, "pip", "install", "-r", str(req_file)],
                cwd=str(project_root),
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="ignore",
                timeout=300,
            )

            if result.returncode == 0:
                logger.info("uv 依赖安装成功")
                return {
                    "success": True,
                    "message": "依赖安装成功 (uv)",
                    "output": result.stdout,
                }
            else:
                logger.error(f"uv 依赖安装失败: {result.stderr}")
                return {"success": False, "error": f"uv 安装失败: {result.stderr}"}

        except subprocess.TimeoutExpired:
            return {"success": False, "error": "安装依赖超时"}
        except Exception as e:
            logger.error(f"uv 安装依赖失败: {e}")
            return {"success": False, "error": str(e)}

    @staticmethod
    async def _install_with_conda(project_root: Path, req_file: Path) -> dict:
        """使用 conda 安装依赖"""
        try:
            logger.info("使用 conda 安装依赖...")

            # 获取当前 conda 环境名
            conda_env = os.environ.get("CONDA_DEFAULT_ENV")
            if not conda_env:
                return {"success": False, "error": "无法获取 conda 环境名"}

            # 使用 conda run 执行 pip install
            result = subprocess.run(
                ["conda", "run", "-n", conda_env, "pip", "install", "-r", str(req_file)],
                cwd=str(project_root),
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="ignore",
                timeout=300,
            )

            if result.returncode == 0:
                logger.info("conda 依赖安装成功")
                return {
                    "success": True,
                    "message": f"依赖安装成功 (conda环境: {conda_env})",
                    "output": result.stdout,
                }
            else:
                logger.error(f"conda 依赖安装失败: {result.stderr}")
                return {"success": False, "error": f"conda 安装失败: {result.stderr}"}

        except subprocess.TimeoutExpired:
            return {"success": False, "error": "安装依赖超时"}
        except Exception as e:
            logger.error(f"conda 安装依赖失败: {e}")
            return {"success": False, "error": str(e)}

    @staticmethod
    async def _install_with_pip(project_root: Path, req_file: Path) -> dict:
        """使用 pip 安装依赖"""
        try:
            logger.info("使用 pip 安装依赖...")

            # 使用当前 Python 环境的 pip
            result = subprocess.run(
                [sys.executable, "-m", "pip", "install", "-r", str(req_file)],
                cwd=str(project_root),
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="ignore",
                timeout=300,
            )

            if result.returncode == 0:
                logger.info("pip 依赖安装成功")
                return {
                    "success": True,
                    "message": "依赖安装成功 (pip)",
                    "output": result.stdout,
                }
            else:
                logger.error(f"pip 依赖安装失败: {result.stderr}")
                return {"success": False, "error": f"pip 安装失败: {result.stderr}"}

        except subprocess.TimeoutExpired:
            return {"success": False, "error": "安装依赖超时"}
        except Exception as e:
            logger.error(f"pip 安装依赖失败: {e}")
            return {"success": False, "error": str(e)}
