"""
Git 更新路由组件
提供 Git 环境检测、安装、更新等 API 接口
"""

import platform
import subprocess
from pathlib import Path
from typing import Optional

from pydantic import BaseModel

from src.common.logger import get_logger
from src.common.security import VerifiedDep
from src.config.config import PROJECT_ROOT
from src.plugin_system import BaseRouterComponent

logger = get_logger("WebUI.GitUpdateRouter")


# ==================== 请求/响应模型 ====================


class GitStatusResponse(BaseModel):
    """Git 状态响应"""

    git_available: bool
    git_version: Optional[str] = None
    git_path: Optional[str] = None
    is_portable: bool = False
    system_os: str
    is_git_repo: bool = False  # 是否为 Git 仓库
    update_mode: str = "unknown"  # git 或 release


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
    update_mode: str = "git"  # git 或 release
    current_version: Optional[str] = None  # Release 模式下的当前版本
    latest_version: Optional[str] = None  # Release 模式下的最新版本
    download_url: Optional[str] = None  # Release 下载地址


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


class GitRollbackRequest(BaseModel):
    """回滚请求"""

    commit_hash: str


class GitInstallResponse(BaseModel):
    """Git 安装响应"""

    success: bool
    message: str
    install_path: Optional[str] = None
    error: Optional[str] = None


# ==================== 核心工具类 ====================


class GitDetector:
    """Git 环境检测器"""

    @staticmethod
    def is_git_available() -> bool:
        """检查系统是否安装 Git"""
        # 先检查便携版
        portable_git = GitDetector.find_portable_git()
        if portable_git:
            try:
                subprocess.run(
                    [str(portable_git), "--version"],
                    capture_output=True,
                    check=True,
                    timeout=5,
                )
                return True
            except Exception:
                pass
        
        # 再检查系统 Git
        try:
            subprocess.run(
                ["git", "--version"],
                capture_output=True,
                check=True,
                timeout=5,
            )
            return True
        except (
            subprocess.CalledProcessError,
            FileNotFoundError,
            subprocess.TimeoutExpired,
        ):
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
        """获取 Git 可执行文件路径"""
        # 先查找便携版（优先使用后端目录下的）
        portable_git = GitDetector.find_portable_git()
        if portable_git:
            return str(portable_git)

        # 查找系统 Git
        import shutil

        git_path = shutil.which("git")
        return git_path

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


class ReleaseUpdater:
    """GitHub Release 更新管理器"""

    # 配置 GitHub 仓库信息
    GITHUB_REPO_OWNER = "ikun-11451"
    GITHUB_REPO_NAME = "MaiMai-Core"
    GITHUB_API_URL = f"https://api.github.com/repos/{GITHUB_REPO_OWNER}/{GITHUB_REPO_NAME}/releases/latest"
    
    def __init__(self, install_path: Path):
        self.install_path = install_path
        self.version_file = install_path / "VERSION"

    def get_current_version(self) -> Optional[str]:
        """获取当前安装的版本"""
        if self.version_file.exists():
            try:
                return self.version_file.read_text(encoding="utf-8").strip()
            except Exception as e:
                logger.warning(f"读取版本文件失败: {e}")
        return None

    async def check_updates(self) -> dict:
        """检查 GitHub Release 更新"""
        try:
            import httpx
            
            current_version = self.get_current_version()
            logger.info(f"当前版本: {current_version or '未知'}")
            
            # 请求 GitHub API
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    self.GITHUB_API_URL,
                    headers={"Accept": "application/vnd.github.v3+json"},
                    timeout=30,
                    follow_redirects=True
                )
                
                if response.status_code != 200:
                    return {
                        "success": False,
                        "error": f"无法获取 Release 信息: HTTP {response.status_code}"
                    }
                
                release_data = response.json()
                latest_version = release_data.get("tag_name", "").lstrip("v")
                
                # 检查是否有更新
                has_update = False
                if current_version is None:
                    has_update = True  # 首次安装
                elif current_version != latest_version:
                    has_update = True
                
                # 查找下载链接
                download_url = None
                assets = release_data.get("assets", [])
                for asset in assets:
                    name = asset.get("name", "").lower()
                    # 根据系统选择合适的资源
                    if platform.system() == "Windows" and name.endswith(".zip"):
                        download_url = asset.get("browser_download_url")
                        break
                    elif platform.system() == "Linux" and "linux" in name:
                        download_url = asset.get("browser_download_url")
                        break
                
                # 获取更新日志
                update_logs = []
                body = release_data.get("body", "")
                if body:
                    lines = body.split("\n")
                    update_logs = [line.strip() for line in lines[:10] if line.strip()]
                
                return {
                    "success": True,
                    "has_update": has_update,
                    "current_version": current_version or "未知",
                    "latest_version": latest_version,
                    "download_url": download_url,
                    "update_logs": update_logs,
                    "release_name": release_data.get("name", ""),
                    "published_at": release_data.get("published_at", "")
                }
                
        except Exception as e:
            logger.error(f"检查 Release 更新失败: {e}")
            return {"success": False, "error": str(e)}

    async def download_and_install(self, download_url: str, latest_version: str) -> dict:
        """下载并安装新版本"""
        try:
            import httpx
            import zipfile
            import shutil
            
            # 创建临时目录
            temp_dir = self.install_path / "temp_update"
            temp_dir.mkdir(parents=True, exist_ok=True)
            
            download_file = temp_dir / "update.zip"
            
            try:
                logger.info(f"正在下载更新: {download_url}")
                
                # 下载文件
                async with httpx.AsyncClient() as client:
                    async with client.stream("GET", download_url, timeout=300, follow_redirects=True) as response:
                        response.raise_for_status()
                        
                        total_size = int(response.headers.get("content-length", 0))
                        downloaded = 0
                        
                        with open(download_file, "wb") as f:
                            async for chunk in response.aiter_bytes(chunk_size=8192):
                                f.write(chunk)
                                downloaded += len(chunk)
                                if total_size > 0:
                                    progress = (downloaded / total_size) * 100
                                    if downloaded % (1024 * 1024) == 0:  # 每 1MB 记录一次
                                        logger.info(f"下载进度: {progress:.1f}%")
                
                logger.info("下载完成，正在解压...")
                
                # 解压文件
                extract_dir = temp_dir / "extracted"
                extract_dir.mkdir(parents=True, exist_ok=True)
                
                with zipfile.ZipFile(download_file, 'r') as zip_ref:
                    zip_ref.extractall(extract_dir)
                
                logger.info("解压完成，正在更新文件...")
                
                # 备份旧版本
                backup_dir = self.install_path / "backup"
                if backup_dir.exists():
                    shutil.rmtree(backup_dir)
                
                # 移动当前文件到备份
                important_dirs = ["mmc", "config", "data", "logs"]
                backup_dir.mkdir(parents=True, exist_ok=True)
                
                for item in self.install_path.iterdir():
                    if item.name not in ["temp_update", "backup", "VERSION"] and item.name in important_dirs:
                        continue  # 保留用户数据
                    if item != temp_dir and item != backup_dir:
                        try:
                            dest = backup_dir / item.name
                            if item.is_dir():
                                shutil.copytree(item, dest, dirs_exist_ok=True)
                            else:
                                shutil.copy2(item, dest)
                        except Exception as e:
                            logger.warning(f"备份 {item} 失败: {e}")
                
                # 复制新文件
                for item in extract_dir.iterdir():
                    dest = self.install_path / item.name
                    try:
                        if item.is_dir():
                            shutil.copytree(item, dest, dirs_exist_ok=True)
                        else:
                            shutil.copy2(item, dest)
                    except Exception as e:
                        logger.error(f"复制 {item} 失败: {e}")
                        raise
                
                # 写入新版本号
                self.version_file.write_text(latest_version, encoding="utf-8")
                
                logger.info("更新完成")
                
                return {
                    "success": True,
                    "message": f"成功更新到版本 {latest_version}",
                    "version": latest_version
                }
                
            finally:
                # 清理临时文件
                try:
                    shutil.rmtree(temp_dir)
                except Exception as e:
                    logger.warning(f"清理临时文件失败: {e}")
                    
        except Exception as e:
            logger.error(f"下载安装失败: {e}")
            return {"success": False, "error": str(e)}

    async def rollback(self) -> dict:
        """回滚到备份版本"""
        try:
            import shutil
            
            backup_dir = self.install_path / "backup"
            if not backup_dir.exists():
                return {"success": False, "error": "没有可用的备份"}
            
            logger.info("正在回滚到备份版本...")
            
            # 复制备份文件回去
            for item in backup_dir.iterdir():
                dest = self.install_path / item.name
                try:
                    if dest.exists():
                        if dest.is_dir():
                            shutil.rmtree(dest)
                        else:
                            dest.unlink()
                    
                    if item.is_dir():
                        shutil.copytree(item, dest)
                    else:
                        shutil.copy2(item, dest)
                except Exception as e:
                    logger.error(f"回滚 {item} 失败: {e}")
                    raise
            
            logger.info("回滚完成")
            
            return {
                "success": True,
                "message": "已回滚到备份版本"
            }
            
        except Exception as e:
            logger.error(f"回滚失败: {e}")
            return {"success": False, "error": str(e)}


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

            return {
                "success": True,
                "message": "更新成功" if updated_files else "已是最新版本",
                "updated_files": updated_files,
            }

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


# ==================== 路由组件 ====================


class GitUpdateRouterComponent(BaseRouterComponent):
    """Git 更新路由组件"""

    component_name = "git_update"
    component_description = "Git 更新管理接口"

    def register_endpoints(self) -> None:
        """注册所有 HTTP 端点"""

        @self.router.get("/status", response_model=GitStatusResponse)
        async def get_git_status(_=VerifiedDep):
            """获取 Git 环境状态"""
            detector = GitDetector()
            git_available = detector.is_git_available()
            
            # 检查主程序是否为 Git 仓库
            repo_path = Path(PROJECT_ROOT)
            is_git_repo = detector.is_git_repo(repo_path)
            
            # 确定更新模式
            update_mode = "unknown"
            if is_git_repo and git_available:
                update_mode = "git"
            elif not is_git_repo:
                update_mode = "release"

            return GitStatusResponse(
                git_available=git_available,
                git_version=detector.get_git_version() if git_available else None,
                git_path=detector.get_git_executable() if git_available else None,
                is_portable=detector.find_portable_git() is not None,
                system_os=platform.system(),
                is_git_repo=is_git_repo,
                update_mode=update_mode,
            )

        @self.router.post("/install", response_model=GitInstallResponse)
        async def install_git(_=VerifiedDep):
            """自动安装 Git（支持全平台）"""
            logger.info(f"开始安装 Git，当前系统: {platform.system()}")
            
            result = await GitInstaller.install_git()
            
            return GitInstallResponse(
                success=result["success"],
                message=result["message"],
                install_path=result.get("install_path"),
                error=result.get("error"),
            )

        @self.router.get("/check", response_model=GitCheckUpdateResponse)
        async def check_updates(_=VerifiedDep):
            """检查主程序更新"""
            try:
                repo_path = Path(PROJECT_ROOT)
                detector = GitDetector()
                is_git_repo = detector.is_git_repo(repo_path)
                
                # 根据是否为 Git 仓库选择不同的更新方式
                if is_git_repo:
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
                            update_mode="git",
                        )
                    else:
                        return GitCheckUpdateResponse(success=False, error=result["error"], update_mode="git")
                else:
                    # Release 模式
                    release_updater = ReleaseUpdater(repo_path)
                    result = await release_updater.check_updates()
                    
                    if result["success"]:
                        return GitCheckUpdateResponse(
                            success=True,
                            has_update=result["has_update"],
                            current_version=result["current_version"],
                            latest_version=result["latest_version"],
                            download_url=result.get("download_url"),
                            update_logs=result.get("update_logs", []),
                            update_mode="release",
                        )
                    else:
                        return GitCheckUpdateResponse(success=False, error=result["error"], update_mode="release")

            except Exception as e:
                logger.error(f"检查更新失败: {e}")
                return GitCheckUpdateResponse(success=False, error=str(e))

        @self.router.post("/update", response_model=GitUpdateResponse)
        async def update_main_program(request: GitUpdateRequest, _=VerifiedDep):
            """更新主程序"""
            try:
                repo_path = Path(PROJECT_ROOT)
                detector = GitDetector()
                is_git_repo = detector.is_git_repo(repo_path)
                
                if is_git_repo:
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
                else:
                    # Release 模式更新
                    release_updater = ReleaseUpdater(repo_path)
                    
                    # 先检查更新获取下载链接
                    check_result = await release_updater.check_updates()
                    if not check_result["success"]:
                        return GitUpdateResponse(
                            success=False, 
                            message="检查更新失败", 
                            error=check_result.get("error")
                        )
                    
                    if not check_result["has_update"]:
                        return GitUpdateResponse(
                            success=True,
                            message="当前已是最新版本"
                        )
                    
                    download_url = check_result.get("download_url")
                    if not download_url:
                        return GitUpdateResponse(
                            success=False,
                            message="未找到适合当前系统的更新包"
                        )
                    
                    # 执行下载和安装
                    result = await release_updater.download_and_install(
                        download_url, 
                        check_result["latest_version"]
                    )
                    
                    if result["success"]:
                        return GitUpdateResponse(
                            success=True,
                            message=result["message"]
                        )
                    else:
                        return GitUpdateResponse(
                            success=False,
                            message="更新失败",
                            error=result.get("error")
                        )

            except Exception as e:
                logger.error(f"更新失败: {e}")
                return GitUpdateResponse(success=False, message="更新失败", error=str(e))

        @self.router.post("/rollback", response_model=GitUpdateResponse)
        async def rollback_version(request: GitRollbackRequest, _=VerifiedDep):
            """回滚到指定版本"""
            try:
                repo_path = Path(PROJECT_ROOT)
                detector = GitDetector()
                is_git_repo = detector.is_git_repo(repo_path)
                
                if is_git_repo:
                    # Git 模式回滚
                    updater = GitUpdater(repo_path)
                    result = await updater.rollback(request.commit_hash)

                    if result["success"]:
                        return GitUpdateResponse(success=True, message=result["message"])
                    else:
                        return GitUpdateResponse(success=False, message="回滚失败", error=result["error"])
                else:
                    # Release 模式回滚
                    release_updater = ReleaseUpdater(repo_path)
                    result = await release_updater.rollback()
                    
                    if result["success"]:
                        return GitUpdateResponse(success=True, message=result["message"])
                    else:
                        return GitUpdateResponse(success=False, message="回滚失败", error=result["error"])

            except Exception as e:
                logger.error(f"回滚失败: {e}")
                return GitUpdateResponse(success=False, message="回滚失败", error=str(e))
