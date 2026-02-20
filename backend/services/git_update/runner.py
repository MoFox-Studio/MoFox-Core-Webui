"""Git 命令执行器（底层封装）

负责：
- 解析当前 Git 可执行文件路径（委托给 git_env 服务）
- 确定主程序仓库根目录
- 提供统一的 `run_git()` 异步接口执行任意 git 命令
"""

from __future__ import annotations

import asyncio
import subprocess
from pathlib import Path
from typing import Any

from src.kernel.logger import get_logger
from ..git_env import get_git_env_status

logger = get_logger(name="GitRunner", color="#F38BA8")


def _find_repo_root() -> Path | None:
    """从插件文件向上查找包含 .git 目录的仓库根路径。

    优先查找 Neo-MoFox 的 .git（即插件所在项目的根目录）。
    """
    # 从当前文件开始往上查找
    current = Path(__file__).resolve()
    for parent in current.parents:
        if (parent / ".git").exists():
            return parent
    return None


# 仓库根目录（模块加载时确定一次）
REPO_ROOT: Path | None = _find_repo_root()


async def get_git_executable() -> str | None:
    """获取当前可用的 Git 可执行文件路径。

    直接复用 git_env 的状态检查，不重复实现检测逻辑。
    """
    try:
        status: dict[str, Any] = await get_git_env_status()
        if status.get("git_available") and status.get("git_path"):
            return status["git_path"]
    except Exception as e:
        logger.error(f"获取 Git 路径失败: {e}")
    return None


async def run_git(
    *args: str,
    cwd: Path | str | None = None,
    timeout: float = 60.0,
    check_repo: bool = True,
) -> tuple[str, str, int]:
    """异步执行 git 命令。

    Args:
        *args: git 子命令及参数，例如 "status", "--porcelain"
        cwd:   执行目录，默认为 REPO_ROOT
        timeout: 命令超时秒数
        check_repo: 是否要求 REPO_ROOT 存在（默认 True）

    Returns:
        (stdout, stderr, returncode)

    Raises:
        RuntimeError: Git 不可用或仓库路径不存在
    """
    git_exe = await get_git_executable()
    if not git_exe:
        raise RuntimeError("Git 不可用，请先在 Git 环境设置中配置")

    work_dir = Path(cwd) if cwd else REPO_ROOT
    if check_repo and (work_dir is None or not work_dir.exists()):
        raise RuntimeError(f"仓库目录不存在: {work_dir!r}")

    cmd = [git_exe, *args]
    logger.debug(f"执行: {' '.join(cmd)}  cwd={work_dir}")

    try:
        result = await asyncio.to_thread(
            lambda: subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=str(work_dir),
                timeout=timeout,
                encoding="utf-8",
                errors="replace",
            )
        )
        return result.stdout.strip(), result.stderr.strip(), result.returncode
    except subprocess.TimeoutExpired:
        raise RuntimeError(f"git 命令超时（{timeout}s）: {' '.join(args)}")
    except Exception as e:
        raise RuntimeError(f"执行 git 命令失败: {e}") from e


def is_repo_available() -> bool:
    """快速判断仓库目录是否存在（同步，无需 git）"""
    return REPO_ROOT is not None and REPO_ROOT.exists()
