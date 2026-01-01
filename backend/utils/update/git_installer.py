"""
Git 自动安装器
支持 Windows、Linux、macOS 平台自动安装 Git
"""

import platform
import subprocess
from pathlib import Path

from src.common.logger import get_logger

logger = get_logger("WebUI.GitInstaller")


class GitInstaller:
    """Git 自动安装器（支持全平台）"""

    # Windows 便携版 Git 下载地址
    PORTABLE_GIT_URL = "https://github.com/git-for-windows/git/releases/download/v2.43.0.windows.1/PortableGit-2.43.0-64-bit.7z.exe"
    PORTABLE_GIT_MIRROR_URL = "https://registry.npmmirror.com/-/binary/git-for-windows/v2.43.0.windows.1/PortableGit-2.43.0-64-bit.7z.exe"

    @staticmethod
    def get_backend_dir() -> Path:
        """获取后端目录"""
        return Path(__file__).parent.parent.parent

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
