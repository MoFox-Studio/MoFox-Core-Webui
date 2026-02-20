"""Git 环境检测服务

负责：
- 检测系统中 Git 可执行文件的路径
- 获取 Git 版本信息
- 判断 Git 来源（自定义 / 便携版 / 系统）
"""

from __future__ import annotations

import platform
import shutil
import subprocess
from pathlib import Path

from src.kernel.logger import get_logger

logger = get_logger(name="GitDetector", color="#A6E3A1")

# 便携版 Git 的默认安装目录（相对于插件工作目录）
PORTABLE_GIT_DIR = Path("git")
PORTABLE_GIT_EXE = PORTABLE_GIT_DIR / "bin" / "git.exe"

# Windows 常见系统安装路径
_WINDOWS_SYSTEM_CANDIDATES: list[str] = [
    r"C:\Program Files\Git\bin\git.exe",
    r"C:\Program Files (x86)\Git\bin\git.exe",
    r"C:\Git\bin\git.exe",
]


def get_system_os() -> str:
    """返回当前操作系统名称（Windows / Linux / Darwin）"""
    return platform.system()


def get_git_version(git_path: str) -> str | None:
    """运行 `git --version` 并返回版本字符串，失败返回 None"""
    try:
        result = subprocess.run(
            [git_path, "--version"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except Exception as e:
        logger.debug(f"获取 Git 版本失败 ({git_path}): {e}")
    return None


def detect_git_path() -> str | None:
    """自动检测系统中的 Git 可执行文件路径。

    检测顺序：
    1. PATH 中的 git
    2. Windows 便携版默认目录
    3. Windows 常见系统安装路径

    Returns:
        Git 可执行文件的绝对路径，未找到则返回 None
    """
    # 1. PATH 搜索
    path = shutil.which("git")
    if path:
        return path

    # 2. 便携版（相对路径，适用于 Windows）
    if get_system_os() == "Windows" and PORTABLE_GIT_EXE.exists():
        return str(PORTABLE_GIT_EXE.resolve())

    # 3. Windows 常见安装路径
    if get_system_os() == "Windows":
        for candidate in _WINDOWS_SYSTEM_CANDIDATES:
            if Path(candidate).exists():
                return candidate

    return None


def resolve_git_source(git_path: str) -> tuple[str, bool]:
    """判断 Git 的来源类型。

    Args:
        git_path: Git 可执行文件路径

    Returns:
        (source, is_portable)：
            source 取值 'custom' | 'portable' | 'system' | 'unknown'
            is_portable 是否为便携版
    """
    try:
        resolved = Path(git_path).resolve()
        portable_resolved = PORTABLE_GIT_EXE.resolve()
        if resolved == portable_resolved or str(resolved).startswith(
            str(PORTABLE_GIT_DIR.resolve())
        ):
            return "portable", True
    except Exception:
        pass
    return "system", False
