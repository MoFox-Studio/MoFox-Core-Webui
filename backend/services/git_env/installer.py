"""Git 安装服务

负责：
- Windows：下载并解压便携版 Git（PortableGit）
- Linux / macOS：提供包管理器安装指引
- 所有平台：返回安装指南
"""

from __future__ import annotations

import asyncio
import zipfile
from pathlib import Path
from typing import Any

import httpx

from src.kernel.logger import get_logger
from .detector import PORTABLE_GIT_DIR, PORTABLE_GIT_EXE, get_system_os

logger = get_logger(name="GitInstaller", color="#F9E2AF")

# PortableGit 下载 URL（GitHub Release MinGit）
# 如需更换版本，只需修改此处
_PORTABLE_GIT_DOWNLOAD_URL = (
    "https://github.com/git-for-windows/git/releases/download/"
    "v2.47.1.windows.1/MinGit-2.47.1-64-bit.zip"
)

# Linux / macOS 安装指南数据
_INSTALL_GUIDES: dict[str, dict[str, Any]] = {
    "Linux": {
        "platform": "Linux",
        "method": "package_manager",
        "description": "使用系统包管理器安装 Git",
        "manual_commands": {
            "Ubuntu / Debian": "sudo apt-get install git",
            "Fedora / RHEL": "sudo dnf install git",
            "Arch Linux": "sudo pacman -S git",
            "Alpine": "apk add git",
        },
        "manual_url": "https://git-scm.com/download/linux",
    },
    "Darwin": {
        "platform": "macOS",
        "method": "homebrew",
        "description": "推荐使用 Homebrew 安装 Git，也可通过 Xcode Command Line Tools",
        "manual_commands": {
            "Homebrew": "brew install git",
            "Xcode CLT": "xcode-select --install",
        },
        "manual_url": "https://git-scm.com/download/mac",
    },
    "Windows": {
        "platform": "Windows",
        "method": "portable",
        "description": "可使用内置下载功能获取便携版 Git，或手动安装官方版本",
        "manual_url": "https://git-scm.com/download/win",
    },
}


def get_install_guide() -> dict[str, Any]:
    """返回当前平台的 Git 安装指南"""
    os_name = get_system_os()
    return _INSTALL_GUIDES.get(os_name, {
        "platform": os_name,
        "method": "manual",
        "description": "请访问 git-scm.com 手动下载并安装 Git",
        "manual_url": "https://git-scm.com/downloads",
    })


async def install_git_windows() -> dict[str, Any]:
    """下载并解压 MinGit 便携版到 PORTABLE_GIT_DIR。

    仅适用于 Windows，非 Windows 系统直接返回失败。

    Returns:
        {"success": bool, "message": str, "install_path": str | None, "error": str | None}
    """
    if get_system_os() != "Windows":
        return {
            "success": False,
            "message": "自动安装便携版 Git 仅支持 Windows",
            "error": "unsupported_platform",
        }

    if PORTABLE_GIT_EXE.exists():
        return {
            "success": True,
            "message": "便携版 Git 已存在，无需重复安装",
            "install_path": str(PORTABLE_GIT_EXE.resolve()),
        }

    zip_path = PORTABLE_GIT_DIR / "_download.zip"
    try:
        PORTABLE_GIT_DIR.mkdir(parents=True, exist_ok=True)
        logger.info(f"开始下载便携版 Git: {_PORTABLE_GIT_DOWNLOAD_URL}")

        async with httpx.AsyncClient(
            follow_redirects=True,
            timeout=120.0,
        ) as client:
            async with client.stream("GET", _PORTABLE_GIT_DOWNLOAD_URL) as resp:
                resp.raise_for_status()
                with open(zip_path, "wb") as f:
                    async for chunk in resp.aiter_bytes(chunk_size=65536):
                        f.write(chunk)

        logger.info("下载完成，开始解压...")

        # 解压在线程池中执行，避免阻塞事件循环
        await asyncio.to_thread(_extract_zip, zip_path, PORTABLE_GIT_DIR)
        zip_path.unlink(missing_ok=True)

        if not PORTABLE_GIT_EXE.exists():
            raise FileNotFoundError(f"解压后未找到 {PORTABLE_GIT_EXE}")

        install_path = str(PORTABLE_GIT_EXE.resolve())
        logger.info(f"便携版 Git 安装成功: {install_path}")
        return {
            "success": True,
            "message": "便携版 Git 安装成功",
            "install_path": install_path,
        }

    except httpx.HTTPStatusError as e:
        logger.error(f"下载失败 HTTP {e.response.status_code}: {e}")
        return {"success": False, "message": "下载失败", "error": str(e)}
    except Exception as e:
        logger.error(f"安装 Git 失败: {e}")
        # 清理残留
        zip_path.unlink(missing_ok=True)
        return {"success": False, "message": "安装失败", "error": str(e)}


def _extract_zip(zip_path: Path, dest_dir: Path) -> None:
    """同步解压 ZIP 文件（在线程池中调用）"""
    with zipfile.ZipFile(zip_path, "r") as zf:
        zf.extractall(dest_dir)
