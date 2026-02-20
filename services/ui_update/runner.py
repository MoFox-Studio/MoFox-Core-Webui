"""UI 更新 Git 命令执行器（底层封装）

Webui_test_plugin 插件根目录本身就是一个独立的 git 仓库
（例如以 webui-dist 为当前分支单独 clone），与 Neo-MoFox 主仓库完全无关。
所有 git 操作都在插件根目录（PLUGIN_ROOT）中执行。

提供：
- PLUGIN_ROOT           插件根目录（绝对路径）
- ALLOWED_BRANCH        允许自动更新的分支名
- is_ui_git_repo()      判断 PLUGIN_ROOT 是否是独立 git 仓库根目录
- run_ui_git(*args)     在 PLUGIN_ROOT 中执行任意 git 命令
- get_ui_branch()       获取当前分支名
- get_ui_version()      获取当前版本号（git tag 解析）
"""

from __future__ import annotations

import asyncio
import subprocess
from pathlib import Path
from typing import Any

from src.kernel.logger import get_logger
from ..git_env import get_git_env_status

logger = get_logger(name="UIRunner", color="#89DCEB")

# ==================== 目录常量 ====================

# Webui_test_plugin/  —— 插件根目录，本身就是独立 git 仓库
PLUGIN_ROOT: Path = Path(__file__).resolve().parent.parent.parent

# 仅允许此分支执行自动更新，其他分支认为是开发模式，禁用
ALLOWED_BRANCH: str = "webui-dist"

# ==================== 工具函数 ====================


def is_ui_git_repo() -> bool:
    """判断插件根目录（PLUGIN_ROOT）本身是否是一个 git 仓库根目录。

    只检查 PLUGIN_ROOT/.git 是否存在（文件或目录均可，用于 worktree 兼容）。
    不向上遍历查找父目录的 .git，这样可以与 Neo-MoFox 主仓库区分开来。
    """
    if not PLUGIN_ROOT.exists():
        return False
    git_entry = PLUGIN_ROOT / ".git"
    return git_entry.exists()


async def _get_git_exe() -> str:
    """从 git_env 服务获取可用的 git 可执行文件路径。"""
    try:
        status: dict[str, Any] = await get_git_env_status()
        if status.get("git_available") and status.get("git_path"):
            return status["git_path"]
    except Exception as e:
        logger.error(f"获取 Git 路径失败: {e}")
    raise RuntimeError("Git 不可用，请先在 Git 环境设置中配置")


async def run_ui_git(
    *args: str,
    timeout: float = 60.0,
) -> tuple[str, str, int]:
    """在 PLUGIN_ROOT 中异步执行 git 命令。

    Args:
        *args:   git 子命令及参数，例如 "fetch", "origin"
        timeout: 超时秒数

    Returns:
        (stdout, stderr, returncode)

    Raises:
        RuntimeError: git 不可用 / 插件根目录不存在
    """
    if not PLUGIN_ROOT.exists():
        raise RuntimeError(f"插件根目录不存在: {PLUGIN_ROOT}")

    git_exe = await _get_git_exe()
    cmd = [git_exe, *args]
    logger.debug(f"执行(UI): {' '.join(cmd)}  cwd={PLUGIN_ROOT}")

    try:
        result = await asyncio.to_thread(
            lambda: subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=str(PLUGIN_ROOT),
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


async def get_ui_branch() -> str | None:
    """获取 static/ 仓库当前分支名，失败返回 None。"""
    try:
        out, _, code = await run_ui_git("rev-parse", "--abbrev-ref", "HEAD")
        return out if code == 0 and out else None
    except RuntimeError:
        return None


async def get_ui_version(commit: str | None = None) -> str | None:
    """尝试从 git tag 解析版本号。

    优先使用 ``git describe --tags --exact-match`` 精确匹配当前 commit 对应的 tag，
    其次使用 ``git describe --tags --abbrev=0`` 获取最近的 tag，
    均失败则返回 None。

    Args:
        commit: 可选，指定 commit hash；None 时使用 HEAD
    """
    ref = commit if commit else "HEAD"
    try:
        # 精确匹配
        out, _, code = await run_ui_git(
            "describe", "--tags", "--exact-match", ref
        )
        if code == 0 and out:
            return out

        # 最近 tag（不完全匹配时带有 -g<hash> 后缀，截取主版本号部分）
        out, _, code = await run_ui_git(
            "describe", "--tags", "--abbrev=0", ref
        )
        if code == 0 and out:
            return out
    except RuntimeError:
        pass
    return None
