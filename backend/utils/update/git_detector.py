"""
Git 环境检测器
检测系统 Git 环境、路径和版本信息
"""

import shutil
import subprocess
from pathlib import Path
from typing import Optional

from src.common.logger import get_logger

# 导入后端存储
import sys
backend_utils_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_utils_path))
from backend_storage import BackendStorage

logger = get_logger("WebUI.GitDetector")


class GitDetector:
    """Git 环境检测器"""

    @staticmethod
    def is_git_available() -> bool:
        """检查系统是否安装 Git"""
        git_path = GitDetector.get_git_executable()
        if not git_path:
            return False
            
        try:
            subprocess.run(
                [git_path, "--version"],
                capture_output=True,
                check=True,
                timeout=5,
            )
            return True
        except Exception:
            return False

    @staticmethod
    def is_git_repo(path: Path) -> bool:
        """检查指定路径是否为 Git 仓库"""
        git_dir = path / ".git"
        return git_dir.exists() and git_dir.is_dir()

    @staticmethod
    def get_git_version() -> Optional[str]:
        """获取 Git 版本"""
        git_path = GitDetector.get_git_executable()
        if not git_path:
            return None
            
        try:
            result = subprocess.run(
                [git_path, "--version"],
                capture_output=True,
                text=True,
                check=True,
                timeout=5,
            )
            # 输出格式: git version 2.41.0.windows.1
            version_line = result.stdout.strip()
            if "git version" in version_line:
                return version_line.split("git version")[-1].strip()
            return version_line
        except Exception:
            return None

    @staticmethod
    def get_git_executable() -> Optional[str]:
        """
        获取 Git 可执行文件路径
        优先级: 1. 自定义路径 2. 便携版 3. 系统 Git
        """
        # 1. 先检查是否有自定义路径
        custom_path = BackendStorage.get_git_path()
        if custom_path:
            custom_path_obj = Path(custom_path)
            if custom_path_obj.exists():
                logger.debug(f"使用自定义 Git 路径: {custom_path}")
                return str(custom_path)
            else:
                logger.warning(f"自定义 Git 路径无效: {custom_path}，将清除并尝试其他方式")
                BackendStorage.clear_git_path()
        
        # 2. 查找便携版（优先使用后端目录下的）
        portable_git = GitDetector.find_portable_git()
        if portable_git:
            logger.debug(f"找到便携版 Git: {portable_git}")
            # 保存便携版路径到存储
            BackendStorage.set_git_path(str(portable_git))
            BackendStorage.set_git_source("portable")
            return str(portable_git)

        # 3. 查找系统 Git
        git_path = shutil.which("git")
        if git_path:
            logger.debug(f"找到系统 Git: {git_path}")
            # 保存系统 Git 路径到存储
            BackendStorage.set_git_path(git_path)
            BackendStorage.set_git_source("system")
            return git_path
        
        return None

    @staticmethod
    def find_portable_git() -> Optional[Path]:
        """查找便携版 Git"""
        # 获取后端目录
        backend_dir = Path(__file__).parent.parent.parent
        
        # 检查标准位置（优先使用后端目录）
        possible_paths = [
            backend_dir / "PortableGit/bin/git.exe",  # Windows 后端目录
            backend_dir / "PortableGit/bin/git",      # Linux/macOS 后端目录
            Path("PortableGit/bin/git.exe"),
            Path("PortableGit/bin/git"),
            Path("../PortableGit/bin/git.exe"),
            Path("../PortableGit/bin/git"),
        ]

        for path in possible_paths:
            if path.exists():
                return path.resolve()

        return None

    @staticmethod
    def get_git_source() -> str:
        """获取 Git 来源类型"""
        source = BackendStorage.get_git_source()
        return source if source else "unknown"

    @staticmethod
    def get_current_branch(repo_path: Path) -> Optional[str]:
        """获取当前 Git 分支"""
        git_path = GitDetector.get_git_executable()
        if not git_path:
            return None
            
        try:
            result = subprocess.run(
                [git_path, "branch", "--show-current"],
                cwd=str(repo_path),
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="ignore",
                timeout=5,
            )
            if result.returncode == 0 and result.stdout.strip():
                return result.stdout.strip()
            return None
        except Exception as e:
            logger.warning(f"获取当前分支失败: {e}")
            return None

    @staticmethod
    def get_available_branches(repo_path: Path) -> list[str]:
        """获取可用分支列表"""
        git_path = GitDetector.get_git_executable()
        if not git_path:
            return []
            
        try:
            # 先获取远程分支
            subprocess.run(
                [git_path, "fetch", "origin"],
                cwd=str(repo_path),
                capture_output=True,
                timeout=30,
            )
            
            # 获取所有分支
            result = subprocess.run(
                [git_path, "branch", "-a"],
                cwd=str(repo_path),
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="ignore",
                timeout=10,
            )
            
            if result.returncode != 0:
                return []

            branches = []
            for line in result.stdout.strip().split("\n"):
                line = line.strip()
                if not line:
                    continue
                
                # 当前分支标记为 *
                if line.startswith("*"):
                    line = line[1:].strip()
                
                # 跳过远程HEAD指针
                if "HEAD ->" in line:
                    continue
                
                # 处理远程分支
                if line.startswith("remotes/origin/"):
                    branch_name = line.replace("remotes/origin/", "")
                    if branch_name not in branches:
                        branches.append(branch_name)
                elif line not in branches:
                    branches.append(line)

            return sorted(branches)
        except Exception as e:
            logger.warning(f"获取分支列表失败: {e}")
            return []
