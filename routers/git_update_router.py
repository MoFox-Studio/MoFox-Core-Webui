"""
Git 更新路由组件
提供 Git 环境检测、安装、更新等 API 接口
"""

import os
import platform
import subprocess
from pathlib import Path
from typing import Optional
import shutil
import sys

from pydantic import BaseModel

from src.common.logger import get_logger
from src.common.security import VerifiedDep
from src.config.config import PROJECT_ROOT
from src.plugin_system import BaseRouterComponent

from ..utils.backend_storage import BackendStorage

logger = get_logger("WebUI.GitUpdateRouter")


# ==================== 请求/响应模型 ====================


class RepoStatusResponse(BaseModel):
    """主程序仓库状态响应"""

    is_git_repo: bool = False  # 是否为 Git 仓库
    current_branch: Optional[str] = None  # 当前分支
    available_branches: list[str] = []  # 可用分支列表
    error: Optional[str] = None


class GitCheckUpdateResponse(BaseModel):
    """检查更新响应"""

    success: bool
    has_update: bool = False
    current_commit: Optional[str] = None
    remote_commit: Optional[str] = None
    commits_behind: int = 0
    update_logs: list = []
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
    updated_files: list = []
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


class GitBackupInfo(BaseModel):
    """Git 历史版本/备份信息"""
    
    commit: str  # 完整 commit hash
    commit_short: str  # 简短 commit hash
    message: str  # 提交消息
    timestamp: str  # 提交时间
    is_current: bool = False  # 是否是当前版本


class GitBackupsResponse(BaseModel):
    """获取历史版本响应"""
    
    success: bool
    data: list[GitBackupInfo] = []
    error: Optional[str] = None


class GitCommitDetailResponse(BaseModel):
    """提交详情响应"""
    
    success: bool
    commit: Optional[str] = None
    commit_short: Optional[str] = None
    message: Optional[str] = None
    body: Optional[str] = None
    author: Optional[str] = None
    timestamp: Optional[str] = None
    files_changed: list[dict] = []
    stats: Optional[str] = None
    error: Optional[str] = None


# ==================== 核心工具类 ====================


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
        backend_dir = Path(__file__).parent.parent
        
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


class GitInstaller:
    """Git 自动安装器（支持全平台）"""

    # Windows 便携版 Git 下载地址
    PORTABLE_GIT_URL = "https://github.com/git-for-windows/git/releases/download/v2.43.0.windows.1/PortableGit-2.43.0-64-bit.7z.exe"
    PORTABLE_GIT_MIRROR_URL = "https://registry.npmmirror.com/-/binary/git-for-windows/v2.43.0.windows.1/PortableGit-2.43.0-64-bit.7z.exe"

    @staticmethod
    def get_backend_dir() -> Path:
        """获取后端目录"""
        return Path(__file__).parent.parent

    @staticmethod
    async def install_git() -> dict:
        """自动安装 Git（全平台支持）"""
        system = platform.system()
        
        if system == "Windows":
            return await GitInstaller._install_windows()
        elif system == "Linux":
            return await GitInstaller._install_linux()
        elif system == "Darwin":
            return await GitInstaller._install_macos()
        else:
            return {
                "success": False,
                "message": "不支持的操作系统",
                "error": f"当前系统 {system} 不支持自动安装",
            }

    @staticmethod
    async def _install_windows() -> dict:
        """Windows 自动安装（下载便携版到后端目录）"""
        import httpx

        backend_dir = GitInstaller.get_backend_dir()
        install_dir = backend_dir / "PortableGit"
        install_dir.mkdir(parents=True, exist_ok=True)
        
        installer_path = install_dir / "git_installer.exe"

        try:
            logger.info("正在从镜像源下载 Git...")
            
            # 优先使用镜像源，失败则尝试官方源
            urls = [
                GitInstaller.PORTABLE_GIT_MIRROR_URL,
                GitInstaller.PORTABLE_GIT_URL,
            ]
            
            download_success = False
            for url in urls:
                try:
                    async with httpx.AsyncClient() as client:
                        async with client.stream("GET", url, timeout=300, follow_redirects=True) as response:
                            response.raise_for_status()
                            with open(installer_path, "wb") as f:
                                async for chunk in response.aiter_bytes(chunk_size=8192):
                                    f.write(chunk)
                    download_success = True
                    logger.info(f"从 {url} 下载成功")
                    break
                except Exception as e:
                    logger.warning(f"从 {url} 下载失败: {e}")
                    continue
            
            if not download_success:
                return {
                    "success": False,
                    "message": "Git 下载失败",
                    "error": "所有下载源均失败，请检查网络连接",
                }

            logger.info("Git 下载完成，正在解压...")

            # 执行自解压
            result = subprocess.run(
                [str(installer_path), "-y", "-gm2", f"-o{install_dir}"],
                capture_output=True,
                text=True,
                timeout=120,
            )

            if result.returncode == 0:
                logger.info(f"Git 安装成功，路径: {install_dir}")
                # 删除安装包
                try:
                    installer_path.unlink()
                except Exception:
                    pass
                    
                return {
                    "success": True,
                    "message": "Git 安装成功",
                    "install_path": str(install_dir / "bin/git.exe"),
                }
            else:
                logger.error(f"Git 安装失败: {result.stderr}")
                return {
                    "success": False,
                    "message": "Git 安装失败",
                    "error": f"解压失败: {result.stderr}",
                }

        except Exception as e:
            logger.error(f"Git 安装失败: {e}")
            return {
                "success": False,
                "message": "Git 安装失败",
                "error": str(e),
            }

    @staticmethod
    async def _install_linux() -> dict:
        """Linux 自动安装"""
        try:
            # 检测 Linux 发行版
            distro_info = GitInstaller._detect_linux_distro()
            distro = distro_info["distro"]
            
            logger.info(f"检测到 Linux 发行版: {distro}")
            
            # 根据发行版选择安装命令
            install_commands = {
                "debian": ["sudo", "apt-get", "update", "&&", "sudo", "apt-get", "install", "-y", "git"],
                "ubuntu": ["sudo", "apt-get", "update", "&&", "sudo", "apt-get", "install", "-y", "git"],
                "centos": ["sudo", "dnf", "install", "-y", "git"],
                "rhel": ["sudo", "dnf", "install", "-y", "git"],
                "fedora": ["sudo", "dnf", "install", "-y", "git"],
                "arch": ["sudo", "pacman", "-Sy", "--noconfirm", "git"],
                "opensuse": ["sudo", "zypper", "install", "-y", "git"],
            }
            
            cmd = install_commands.get(distro)
            if not cmd:
                return {
                    "success": False,
                    "message": f"不支持的 Linux 发行版: {distro}",
                    "error": "请手动安装 Git",
                }
            
            logger.info(f"正在执行安装命令: {' '.join(cmd)}")
            
            # 执行安装（使用 shell=True 来支持 && 连接符）
            result = subprocess.run(
                " ".join(cmd),
                shell=True,
                capture_output=True,
                text=True,
                timeout=300,
            )
            
            if result.returncode == 0:
                logger.info("Git 安装成功")
                return {
                    "success": True,
                    "message": "Git 安装成功",
                    "install_path": subprocess.run(["which", "git"], capture_output=True, text=True).stdout.strip(),
                }
            else:
                logger.error(f"Git 安装失败: {result.stderr}")
                return {
                    "success": False,
                    "message": "Git 安装失败",
                    "error": result.stderr,
                }
                
        except Exception as e:
            logger.error(f"Git 安装失败: {e}")
            return {
                "success": False,
                "message": "Git 安装失败",
                "error": str(e),
            }

    @staticmethod
    async def _install_macos() -> dict:
        """macOS 自动安装"""
        try:
            # 检查是否安装了 Homebrew
            has_brew = subprocess.run(
                ["which", "brew"],
                capture_output=True,
                timeout=5,
            ).returncode == 0
            
            if has_brew:
                logger.info("检测到 Homebrew，使用 brew 安装 Git")
                result = subprocess.run(
                    ["brew", "install", "git"],
                    capture_output=True,
                    text=True,
                    timeout=300,
                )
                
                if result.returncode == 0:
                    return {
                        "success": True,
                        "message": "Git 安装成功（通过 Homebrew）",
                        "install_path": subprocess.run(["which", "git"], capture_output=True, text=True).stdout.strip(),
                    }
                else:
                    logger.error(f"Homebrew 安装 Git 失败: {result.stderr}")
            
            # 尝试使用 Xcode Command Line Tools
            logger.info("尝试安装 Xcode Command Line Tools...")
            result = subprocess.run(
                ["xcode-select", "--install"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            
            # xcode-select --install 会弹出 GUI，所以我们只是触发安装
            return {
                "success": True,
                "message": "已触发 Xcode Command Line Tools 安装，请在弹出的窗口中完成安装",
                "install_path": None,
            }
                
        except Exception as e:
            logger.error(f"Git 安装失败: {e}")
            return {
                "success": False,
                "message": "Git 安装失败",
                "error": str(e),
            }

    @staticmethod
    def _detect_linux_distro() -> dict:
        """检测 Linux 发行版"""
        try:
            # 尝试读取 /etc/os-release
            if Path("/etc/os-release").exists():
                with open("/etc/os-release", "r") as f:
                    content = f.read().lower()
                    
                    if "ubuntu" in content:
                        return {"distro": "ubuntu", "name": "Ubuntu"}
                    elif "debian" in content:
                        return {"distro": "debian", "name": "Debian"}
                    elif "centos" in content:
                        return {"distro": "centos", "name": "CentOS"}
                    elif "rhel" in content or "red hat" in content:
                        return {"distro": "rhel", "name": "Red Hat"}
                    elif "fedora" in content:
                        return {"distro": "fedora", "name": "Fedora"}
                    elif "arch" in content:
                        return {"distro": "arch", "name": "Arch Linux"}
                    elif "opensuse" in content:
                        return {"distro": "opensuse", "name": "openSUSE"}
            
            # 尝试其他方法
            if Path("/etc/debian_version").exists():
                return {"distro": "debian", "name": "Debian"}
            elif Path("/etc/redhat-release").exists():
                return {"distro": "rhel", "name": "Red Hat"}
                
        except Exception as e:
            logger.warning(f"检测 Linux 发行版失败: {e}")
        
        return {"distro": "unknown", "name": "Unknown"}

    @staticmethod
    def get_system_install_guide() -> dict:
        """获取系统安装指南"""
        system = platform.system()

        if system == "Windows":
            return {
                "platform": "Windows",
                "method": "automatic",
                "description": "系统将自动下载便携版 Git 到后端目录",
                "manual_url": "https://git-scm.com/download/win",
            }
        elif system == "Linux":
            return {
                "platform": "Linux",
                "method": "automatic",
                "description": "系统将自动使用包管理器安装 Git",
                "manual_commands": {
                    "Debian/Ubuntu": "sudo apt install git",
                    "CentOS/RHEL": "sudo dnf install git",
                    "Arch": "sudo pacman -S git",
                },
            }
        elif system == "Darwin":
            return {
                "platform": "macOS",
                "method": "automatic",
                "description": "系统将自动使用 Homebrew 或 Xcode Command Line Tools 安装 Git",
                "manual_commands": {
                    "Homebrew": "brew install git",
                    "Xcode": "xcode-select --install",
                },
            }
        else:
            return {
                "platform": "Unknown",
                "method": "manual",
                "description": "请访问 Git 官网下载安装",
                "manual_url": "https://git-scm.com/downloads",
            }


class GitUpdater:
    """Git 更新管理器"""

    def __init__(self, repo_path: Path, branch: str | None = None):
        self.repo_path = repo_path
        self.git_path = GitDetector.get_git_executable()

        if not self.git_path:
            raise RuntimeError("Git 未安装或未找到")
        
        # 如果没有指定分支,自动检测当前分支
        if branch is None:
            self.branch = self._get_current_branch()
        else:
            self.branch = branch

    def _get_current_branch(self) -> str:
        """获取当前 Git 分支"""
        try:
            result = subprocess.run(
                [str(self.git_path), "branch", "--show-current"],
                cwd=str(self.repo_path),
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="ignore",
                timeout=5,
            )
            if result.returncode == 0 and result.stdout.strip():
                branch = result.stdout.strip()
                logger.info(f"检测到当前分支: {branch}")
                return branch
            else:
                logger.warning("无法检测当前分支，使用默认分支 'main'")
                return "main"
        except Exception as e:
            logger.warning(f"检测当前分支失败: {e}，使用默认分支 'main'")
            return "main"

    def _run_git_command(self, *args, **kwargs) -> subprocess.CompletedProcess:
        """运行 Git 命令"""
        cmd = [str(self.git_path)] + [str(arg) for arg in args]
        return subprocess.run(
            cmd,
            cwd=str(self.repo_path),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="ignore",
            **kwargs,
        )

    async def check_updates(self) -> dict:
        """检查是否有更新"""
        try:
            # 获取远程更新
            logger.info("正在从远程仓库获取更新信息...")
            fetch_result = self._run_git_command("fetch", "origin", self.branch, timeout=30)

            if fetch_result.returncode != 0:
                return {"success": False, "error": f"无法连接远程仓库: {fetch_result.stderr}"}

            # 获取本地和远程的 commit hash
            local_result = self._run_git_command("rev-parse", "HEAD")
            remote_result = self._run_git_command("rev-parse", f"origin/{self.branch}")

            if local_result.returncode != 0 or remote_result.returncode != 0:
                return {"success": False, "error": "无法获取版本信息"}

            local_commit = local_result.stdout.strip()
            remote_commit = remote_result.stdout.strip()

            has_update = local_commit != remote_commit

            # 获取落后的提交数
            commits_behind = 0
            if has_update:
                count_result = self._run_git_command(
                    "rev-list", "--count", f"HEAD..origin/{self.branch}"
                )
                if count_result.returncode == 0:
                    commits_behind = int(count_result.stdout.strip())

            # 获取更新日志
            update_logs = []
            if has_update:
                log_result = self._run_git_command(
                    "log", "--oneline", f"HEAD..origin/{self.branch}", "--max-count=10"
                )
                if log_result.returncode == 0:
                    update_logs = [
                        line.strip()
                        for line in log_result.stdout.strip().split("\n")
                        if line.strip()
                    ]

            return {
                "success": True,
                "has_update": has_update,
                "current_commit": local_commit[:8],
                "remote_commit": remote_commit[:8],
                "commits_behind": commits_behind,
                "update_logs": update_logs,
            }

        except subprocess.TimeoutExpired:
            return {"success": False, "error": "检查更新超时"}
        except Exception as e:
            logger.error(f"检查更新失败: {e}")
            return {"success": False, "error": str(e)}

    async def pull_updates(self, force: bool = False, stash_local: bool = True) -> dict:
        """拉取更新"""
        try:
            updated_files = []

            # 检查本地是否有未提交的修改
            status_result = self._run_git_command("status", "--porcelain")
            has_local_changes = bool(status_result.stdout.strip())

            if has_local_changes:
                if not force:
                    return {
                        "success": False,
                        "error": "本地有未提交的修改，请先提交或使用强制更新",
                    }

                if stash_local:
                    logger.info("暂存本地修改...")
                    stash_result = self._run_git_command(
                        "stash", "push", "-m", "Auto stash before update"
                    )
                    if stash_result.returncode != 0:
                        return {
                            "success": False,
                            "error": f"暂存本地修改失败: {stash_result.stderr}",
                        }
                else:
                    logger.info("重置本地修改...")
                    reset_result = self._run_git_command("reset", "--hard", "HEAD")
                    if reset_result.returncode != 0:
                        return {
                            "success": False,
                            "error": f"重置本地修改失败: {reset_result.stderr}",
                        }

            # 拉取更新
            logger.info(f"正在拉取 {self.branch} 分支的最新代码...")
            pull_result = self._run_git_command("pull", "origin", self.branch, timeout=60)

            if pull_result.returncode != 0:
                return {"success": False, "error": f"拉取更新失败: {pull_result.stderr}"}

            # 解析更新的文件
            if "Already up to date" not in pull_result.stdout:
                # 获取更新的文件列表
                diff_result = self._run_git_command("diff", "--name-only", "HEAD@{1}", "HEAD")
                if diff_result.returncode == 0:
                    updated_files = [
                        line.strip()
                        for line in diff_result.stdout.strip().split("\n")
                        if line.strip()
                    ]

            result = {
                "success": True,
                "message": "更新成功" if updated_files else "已是最新版本",
                "updated_files": updated_files,
            }

            # 如果有文件更新，尝试安装依赖
            if updated_files:
                logger.info("检测到文件更新，准备安装依赖...")
                venv_type = VenvDetector.detect_venv_type(self.repo_path)

                if venv_type:
                    logger.info(f"检测到虚拟环境类型: {venv_type}，开始安装依赖...")
                    dep_result = await DependencyInstaller.install_dependencies(
                        self.repo_path, venv_type
                    )

                    result["dependencies_installed"] = dep_result["success"]
                    result["venv_type"] = venv_type

                    if dep_result["success"]:
                        result["dependencies_message"] = dep_result["message"]
                        logger.info("依赖安装成功")
                    else:
                        result["dependencies_message"] = f"依赖安装失败: {dep_result.get('error', '未知错误')}"
                        logger.warning(f"依赖安装失败: {dep_result.get('error')}")
                else:
                    result["dependencies_message"] = "未检测到虚拟环境，跳过依赖安装"
                    logger.warning("未检测到虚拟环境，跳过依赖安装")

            return result

        except subprocess.TimeoutExpired:
            return {"success": False, "error": "更新超时"}
        except Exception as e:
            logger.error(f"更新失败: {e}")
            return {"success": False, "error": str(e)}

    def get_current_commit(self) -> Optional[str]:
        """获取当前 commit hash"""
        result = self._run_git_command("rev-parse", "HEAD")
        if result.returncode == 0:
            return result.stdout.strip()
        return None

    async def rollback(self, commit_hash: str) -> dict:
        """回滚到指定版本"""
        try:
            logger.info(f"正在回滚到版本: {commit_hash}")

            # 重置到指定版本
            reset_result = self._run_git_command("reset", "--hard", commit_hash)

            if reset_result.returncode != 0:
                return {"success": False, "error": f"回滚失败: {reset_result.stderr}"}

            return {"success": True, "message": f"已回滚到版本 {commit_hash[:8]}"}

        except Exception as e:
            logger.error(f"回滚失败: {e}")
            return {"success": False, "error": str(e)}

    def get_branches(self) -> dict:
        """获取所有分支列表"""
        try:
            # 获取远程分支
            fetch_result = self._run_git_command("fetch", "origin", timeout=30)
            if fetch_result.returncode != 0:
                logger.warning(f"获取远程分支失败: {fetch_result.stderr}")

            # 获取本地和远程分支
            result = self._run_git_command("branch", "-a")
            if result.returncode != 0:
                return {"success": False, "error": "获取分支列表失败"}

            branches = []
            current_branch = None
            
            for line in result.stdout.strip().split("\n"):
                line = line.strip()
                if not line:
                    continue
                
                # 当前分支标记为 *
                is_current = line.startswith("*")
                if is_current:
                    line = line[1:].strip()
                    current_branch = line
                
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

            return {
                "success": True,
                "branches": sorted(branches),
                "current_branch": current_branch
            }

        except Exception as e:
            logger.error(f"获取分支列表失败: {e}")
            return {"success": False, "error": str(e)}

    async def switch_branch(self, branch: str) -> dict:
        """切换到指定分支"""
        try:
            logger.info(f"正在切换到分支: {branch}")

            # 检查本地是否有未提交的修改
            status_result = self._run_git_command("status", "--porcelain")
            has_local_changes = bool(status_result.stdout.strip())

            if has_local_changes:
                logger.info("暂存本地修改...")
                stash_result = self._run_git_command(
                    "stash", "push", "-m", f"Auto stash before switching to {branch}"
                )
                if stash_result.returncode != 0:
                    return {
                        "success": False,
                        "error": f"暂存本地修改失败: {stash_result.stderr}"
                    }

            # 检查本地是否已有该分支
            branch_result = self._run_git_command("branch", "--list", branch)
            has_local_branch = bool(branch_result.stdout.strip())

            if has_local_branch:
                # 切换到本地分支
                checkout_result = self._run_git_command("checkout", branch)
            else:
                # 从远程创建并切换
                checkout_result = self._run_git_command(
                    "checkout", "-b", branch, f"origin/{branch}"
                )

            if checkout_result.returncode != 0:
                return {"success": False, "error": f"切换分支失败: {checkout_result.stderr}"}

            # 更新分支引用
            self.branch = branch

            # 拉取最新代码
            pull_result = self._run_git_command("pull", "origin", branch, timeout=60)
            if pull_result.returncode != 0:
                logger.warning(f"拉取最新代码失败: {pull_result.stderr}")

            result = {
                "success": True,
                "message": f"已切换到分支 {branch}",
                "current_branch": branch
            }

            # 切换分支后安装依赖
            logger.info("切换分支完成，准备安装依赖...")
            venv_type = VenvDetector.detect_venv_type(self.repo_path)

            if venv_type:
                logger.info(f"检测到虚拟环境类型: {venv_type}，开始安装依赖...")
                dep_result = await DependencyInstaller.install_dependencies(
                    self.repo_path, venv_type
                )

                result["dependencies_installed"] = dep_result["success"]
                result["venv_type"] = venv_type

                if dep_result["success"]:
                    result["dependencies_message"] = dep_result["message"]
                    logger.info("依赖安装成功")
                else:
                    result["dependencies_message"] = f"依赖安装失败: {dep_result.get('error', '未知错误')}"
                    logger.warning(f"依赖安装失败: {dep_result.get('error')}")
            else:
                result["dependencies_message"] = "未检测到虚拟环境，跳过依赖安装"
                logger.warning("未检测到虚拟环境，跳过依赖安装")

            return result

        except subprocess.TimeoutExpired:
            return {"success": False, "error": "切换分支超时"}
        except Exception as e:
            logger.error(f"切换分支失败: {e}")
            return {"success": False, "error": str(e)}

    def get_commit_history(self, max_count: int = 20) -> list[dict]:
        """
        获取提交历史列表（用于版本回退选择）
        
        Args:
            max_count: 最大提交数量
            
        Returns:
            提交历史列表
        """
        try:
            # 获取当前 HEAD
            head_result = self._run_git_command("rev-parse", "HEAD")
            current_head = head_result.stdout.strip() if head_result.returncode == 0 else ""
            
            # 获取提交历史（排除合并提交）
            # 格式: commit_hash|short_hash|时间|提交消息
            log_result = self._run_git_command(
                "log", f"-{max_count}", "--no-merges", "--format=%H|%h|%ci|%s"
            )
            
            if log_result.returncode != 0:
                return []
            
            commits = []
            for line in log_result.stdout.strip().split("\n"):
                if not line:
                    continue
                
                parts = line.split("|", 3)
                if len(parts) < 4:
                    continue
                
                commit_hash, commit_short, timestamp, message = parts
                
                commits.append({
                    "commit": commit_hash,
                    "commit_short": commit_short,
                    "message": message,
                    "timestamp": timestamp,
                    "is_current": commit_hash == current_head
                })
            
            return commits
            
        except Exception as e:
            logger.error(f"获取提交历史失败: {e}")
            return []

    def get_commit_detail(self, commit_hash: str) -> dict:
        """
        获取指定提交的详细信息
        
        Args:
            commit_hash: 提交的 hash（完整或简短均可）
            
        Returns:
            提交详情字典
        """
        try:
            # 验证提交是否存在
            verify_result = self._run_git_command("rev-parse", "--verify", commit_hash)
            if verify_result.returncode != 0:
                return {"success": False, "error": f"提交不存在: {commit_hash}"}
            
            full_hash = verify_result.stdout.strip()
            
            # 获取简短 hash
            short_result = self._run_git_command("rev-parse", "--short", full_hash)
            commit_short = short_result.stdout.strip() if short_result.returncode == 0 else full_hash[:7]
            
            # 获取提交标题
            subject_result = self._run_git_command("log", "-1", "--format=%s", full_hash)
            subject = subject_result.stdout.strip() if subject_result.returncode == 0 else ""
            
            # 获取提交正文
            body_result = self._run_git_command("log", "-1", "--format=%b", full_hash)
            body = body_result.stdout.strip() if body_result.returncode == 0 else ""
            
            # 获取作者
            author_result = self._run_git_command("log", "-1", "--format=%an <%ae>", full_hash)
            author = author_result.stdout.strip() if author_result.returncode == 0 else ""
            
            # 获取提交时间
            time_result = self._run_git_command("log", "-1", "--format=%ci", full_hash)
            timestamp = time_result.stdout.strip() if time_result.returncode == 0 else ""
            
            # 获取修改的文件列表
            files_result = self._run_git_command("diff-tree", "--no-commit-id", "--name-status", "-r", full_hash)
            files_changed = []
            if files_result.returncode == 0 and files_result.stdout:
                for line in files_result.stdout.strip().split("\n"):
                    if line:
                        parts = line.split("\t", 1)
                        if len(parts) == 2:
                            status, filepath = parts
                            status_map = {"A": "新增", "M": "修改", "D": "删除", "R": "重命名"}
                            files_changed.append({
                                "status": status_map.get(status[0], status),
                                "path": filepath
                            })
            
            # 获取统计信息
            stats_result = self._run_git_command("diff-tree", "--stat", "--no-commit-id", full_hash)
            stats = stats_result.stdout.strip() if stats_result.returncode == 0 else ""
            
            return {
                "success": True,
                "commit": full_hash,
                "commit_short": commit_short,
                "message": subject,
                "body": body,
                "author": author,
                "timestamp": timestamp,
                "files_changed": files_changed,
                "stats": stats
            }
            
        except Exception as e:
            logger.error(f"获取提交详情失败: {e}")
            return {"success": False, "error": str(e)}


# ==================== 路由组件 ====================


class GitUpdateRouterComponent(BaseRouterComponent):
    """Git 更新路由组件"""

    component_name = "git_update"
    component_description = "Git 更新管理接口"

    def register_endpoints(self) -> None:
        """注册所有 HTTP 端点"""

        @self.router.get("/status", response_model=RepoStatusResponse)
        async def get_repo_status(_=VerifiedDep):
            """获取主程序仓库状态"""
            try:
                detector = GitDetector()
                git_available = detector.is_git_available()
                
                # 检查主程序是否为 Git 仓库
                repo_path = Path(PROJECT_ROOT)
                is_git_repo = detector.is_git_repo(repo_path)
                
                if not is_git_repo:
                    return RepoStatusResponse(
                        is_git_repo=False,
                        error="主程序不是 Git 仓库"
                    )
                
                if not git_available:
                    return RepoStatusResponse(
                        is_git_repo=True,
                        error="Git 不可用"
                    )
                
                # 获取分支信息
                current_branch = None
                available_branches = []
                try:
                    updater = GitUpdater(repo_path)
                    branch_info = updater.get_branches()
                    if branch_info["success"]:
                        current_branch = branch_info["current_branch"]
                        available_branches = branch_info["branches"]
                except Exception as e:
                    logger.warning(f"获取分支信息失败: {e}")

                return RepoStatusResponse(
                    is_git_repo=is_git_repo,
                    current_branch=current_branch,
                    available_branches=available_branches,
                )
            except Exception as e:
                logger.error(f"获取仓库状态失败: {e}")
                return RepoStatusResponse(
                    is_git_repo=False,
                    error=str(e)
                )

        @self.router.get("/check", response_model=GitCheckUpdateResponse)
        async def check_updates(_=VerifiedDep):
            """检查主程序更新（仅支持 Git 仓库）"""
            try:
                repo_path = Path(PROJECT_ROOT)
                detector = GitDetector()
                is_git_repo = detector.is_git_repo(repo_path)
                
                if not is_git_repo:
                    return GitCheckUpdateResponse(
                        success=False,
                        error="主程序不是 Git 仓库，无法检查更新"
                    )
                
                # Git 模式
                updater = GitUpdater(repo_path)
                result = await updater.check_updates()

                if result["success"]:
                    return GitCheckUpdateResponse(
                        success=True,
                        has_update=result["has_update"],
                        current_commit=result["current_commit"],
                        remote_commit=result["remote_commit"],
                        commits_behind=result["commits_behind"],
                        update_logs=result["update_logs"],
                        branch=updater.branch,
                    )
                else:
                    return GitCheckUpdateResponse(success=False, error=result["error"])

            except Exception as e:
                logger.error(f"检查更新失败: {e}")
                return GitCheckUpdateResponse(success=False, error=str(e))

        @self.router.post("/update", response_model=GitUpdateResponse)
        async def update_main_program(request: GitUpdateRequest, _=VerifiedDep):
            """更新主程序（仅支持 Git 仓库）"""
            try:
                repo_path = Path(PROJECT_ROOT)
                detector = GitDetector()
                is_git_repo = detector.is_git_repo(repo_path)
                
                if not is_git_repo:
                    return GitUpdateResponse(
                        success=False,
                        message="主程序不是 Git 仓库，无法执行更新",
                        error="主程序不是 Git 仓库"
                    )
                
                # Git 模式更新
                updater = GitUpdater(repo_path)

                # 创建备份点
                backup_commit = None
                if request.create_backup:
                    backup_commit = updater.get_current_commit()

                # 执行更新
                result = await updater.pull_updates(
                    force=request.force, stash_local=request.stash_local
                )

                if result["success"]:
                    return GitUpdateResponse(
                        success=True,
                        message=result["message"],
                        updated_files=result.get("updated_files", []),
                        backup_commit=backup_commit,
                    )
                else:
                    return GitUpdateResponse(
                        success=False, message="更新失败", error=result["error"]
                    )

            except Exception as e:
                logger.error(f"更新失败: {e}")
                return GitUpdateResponse(success=False, message="更新失败", error=str(e))

        @self.router.post("/rollback", response_model=GitUpdateResponse)
        async def rollback_version(request: GitRollbackRequest, _=VerifiedDep):
            """回滚到指定版本（仅支持 Git 仓库）"""
            try:
                repo_path = Path(PROJECT_ROOT)
                detector = GitDetector()
                is_git_repo = detector.is_git_repo(repo_path)
                
                if not is_git_repo:
                    return GitUpdateResponse(
                        success=False,
                        message="主程序不是 Git 仓库，无法执行回滚",
                        error="主程序不是 Git 仓库"
                    )
                
                # Git 模式回滚
                updater = GitUpdater(repo_path)
                result = await updater.rollback(request.commit_hash)

                if result["success"]:
                    return GitUpdateResponse(success=True, message=result["message"])
                else:
                    return GitUpdateResponse(success=False, message="回滚失败", error=result["error"])

            except Exception as e:
                logger.error(f"回滚失败: {e}")
                return GitUpdateResponse(success=False, message="回滚失败", error=str(e))

        @self.router.post("/switch-branch", response_model=GitSwitchBranchResponse)
        async def switch_branch(request: GitSwitchBranchRequest, _=VerifiedDep):
            """切换主程序分支"""
            try:
                repo_path = Path(PROJECT_ROOT)
                detector = GitDetector()
                is_git_repo = detector.is_git_repo(repo_path)
                
                if not is_git_repo:
                    return GitSwitchBranchResponse(
                        success=False,
                        message="主程序不是 Git 仓库，无法切换分支",
                        error="主程序不是 Git 仓库"
                    )
                
                # 切换分支
                updater = GitUpdater(repo_path)
                result = await updater.switch_branch(request.branch)

                if result["success"]:
                    return GitSwitchBranchResponse(
                        success=True,
                        message=result["message"],
                        current_branch=result.get("current_branch")
                    )
                else:
                    return GitSwitchBranchResponse(
                        success=False,
                        message="切换分支失败",
                        error=result["error"]
                    )

            except Exception as e:
                logger.error(f"切换分支失败: {e}")
                return GitSwitchBranchResponse(
                    success=False,
                    message="切换分支失败",
                    error=str(e)
                )

        @self.router.get("/backups", response_model=GitBackupsResponse)
        async def get_backups(_=VerifiedDep):
            """获取主程序历史版本列表（用于回退）"""
            try:
                repo_path = Path(PROJECT_ROOT)
                detector = GitDetector()
                
                if not detector.is_git_repo(repo_path):
                    return GitBackupsResponse(
                        success=False,
                        error="主程序不是 Git 仓库"
                    )
                
                updater = GitUpdater(repo_path)
                commits = updater.get_commit_history(max_count=20)
                
                backups = [GitBackupInfo(**c) for c in commits]
                
                return GitBackupsResponse(
                    success=True,
                    data=backups
                )
                
            except Exception as e:
                logger.error(f"获取历史版本列表失败: {e}")
                return GitBackupsResponse(
                    success=False,
                    error=str(e)
                )

        @self.router.get("/commits/{commit_hash}", response_model=GitCommitDetailResponse)
        async def get_commit_detail(commit_hash: str, _=VerifiedDep):
            """获取指定提交的详细信息"""
            try:
                repo_path = Path(PROJECT_ROOT)
                detector = GitDetector()
                
                if not detector.is_git_repo(repo_path):
                    return GitCommitDetailResponse(
                        success=False,
                        error="主程序不是 Git 仓库"
                    )
                
                updater = GitUpdater(repo_path)
                result = updater.get_commit_detail(commit_hash)
                
                return GitCommitDetailResponse(**result)
                
            except Exception as e:
                logger.error(f"获取提交详情失败: {e}")
                return GitCommitDetailResponse(
                    success=False,
                    error=str(e)
                )
