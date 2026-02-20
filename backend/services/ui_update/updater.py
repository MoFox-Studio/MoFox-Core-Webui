"""UI 更新与回滚服务

提供：
- update_ui()           执行 git pull --ff-only 更新 UI 静态文件
- rollback_ui(hash)     将 static/ 仓库 reset --hard 到指定 commit
"""

from __future__ import annotations

from src.kernel.logger import get_logger
from .runner import (
    ALLOWED_BRANCH,
    is_ui_git_repo,
    run_ui_git,
    get_ui_branch,
    get_ui_version,
)
from .models import UIUpdateResult

logger = get_logger(name="UIUpdater", color="#A6E3A1")


def _fail(msg: str, error: str | None = None) -> UIUpdateResult:
    return UIUpdateResult(success=False, message=msg, error=error or msg)


async def _assert_ready() -> UIUpdateResult | None:
    """公共前置检查：仓库存在且在允许的分支上。

    返回 None 表示检查通过，返回 UIUpdateResult 表示检查失败（直接返回给调用方）。
    """
    if not is_ui_git_repo():
        return _fail("static/ 目录不是独立的 git 仓库，更新功能不可用")

    branch = await get_ui_branch()
    if branch != ALLOWED_BRANCH:
        return _fail(
            f'当前分支为 "{branch}"，仅 {ALLOWED_BRANCH} 分支支持自动更新',
        )
    return None


async def update_ui() -> UIUpdateResult:
    """执行 UI 更新（git pull --ff-only）。

    流程：
    1. 前置检查（是否是 git 仓库 & 正确分支）
    2. 记录当前 commit 作为回滚点
    3. git fetch origin
    4. git pull --ff-only（只允许 fast-forward，不自动合并）
    5. 返回更新后的 commit 与版本号
    """
    err = await _assert_ready()
    if err:
        return err

    try:
        # --- 记录当前 commit 作为回滚锚点 ---
        head_out, _, _ = await run_ui_git("rev-parse", "HEAD")
        backup_commit = head_out[:40] if head_out else None

        # --- fetch ---
        _, fetch_err, fetch_code = await run_ui_git("fetch", "origin", timeout=30.0)
        if fetch_code != 0:
            return _fail(f"无法连接到远程仓库: {fetch_err}")

        # --- pull --ff-only ---
        pull_out, pull_err, pull_code = await run_ui_git(
            "pull", "--ff-only", "origin", ALLOWED_BRANCH, timeout=120.0
        )
        if pull_code != 0:
            # 常见原因：已经是最新 / 存在分叉（不允许合并）
            if "Already up to date" in pull_out or "Already up to date" in pull_err:
                new_out, _, _ = await run_ui_git("rev-parse", "HEAD")
                new_commit = new_out[:40] if new_out else None
                version = await get_ui_version()
                return UIUpdateResult(
                    success=True,
                    message="已经是最新版本，无需更新",
                    version=version,
                    backup_commit=backup_commit,
                    commit=new_commit,
                    commit_short=new_commit[:7] if new_commit else None,
                )
            return _fail(f"pull 失败: {pull_err or pull_out}")

        # --- 获取更新后信息 ---
        new_out, _, _ = await run_ui_git("rev-parse", "HEAD")
        new_commit = new_out[:40] if new_out else None
        version = await get_ui_version()

        logger.info(f"UI 更新成功: {backup_commit[:7] if backup_commit else '?'} → {new_commit[:7] if new_commit else '?'}")

        return UIUpdateResult(
            success=True,
            message=f"UI 更新成功，已更新到 {version or new_commit[:7] if new_commit else '最新版本'}",
            version=version,
            backup_commit=backup_commit,
            commit=new_commit,
            commit_short=new_commit[:7] if new_commit else None,
        )

    except RuntimeError as e:
        return _fail(str(e))
    except Exception as e:
        logger.error(f"UI 更新失败: {e}")
        return _fail(f"UI 更新失败: {e}")


async def rollback_ui(commit_hash: str) -> UIUpdateResult:
    """将 static/ 仓库回滚到指定 commit（git reset --hard）。

    Args:
        commit_hash: 目标 commit 的完整或简短 hash（至少 7 位）
    """
    if not is_ui_git_repo():
        return _fail("插件根目录不是独立的 git 仓库，回滚功能不可用")

    # 回滚不强制要求特定分支（允许在任何 git 状态下回滚）
    try:
        # --- 记录当前 commit 作为回滚前快照 ---
        head_out, _, _ = await run_ui_git("rev-parse", "HEAD")
        before_commit = head_out[:40] if head_out else None

        # --- 验证目标 commit 是否存在 ---
        verify_out, verify_err, verify_code = await run_ui_git(
            "cat-file", "-t", commit_hash
        )
        if verify_code != 0 or verify_out.strip() != "commit":
            return _fail(
                f"目标 commit 不存在或无效: {commit_hash}",
                error=verify_err or f"cat-file 返回: {verify_out!r}",
            )

        # --- 执行 reset --hard ---
        _, reset_err, reset_code = await run_ui_git("reset", "--hard", commit_hash)
        if reset_code != 0:
            return _fail(f"reset --hard 失败: {reset_err}")

        # 清理未跟踪文件（保持 worktree 干净）
        await run_ui_git("clean", "-fd")

        # --- 获取回滚后信息 ---
        new_out, _, _ = await run_ui_git("rev-parse", "HEAD")
        new_commit = new_out[:40] if new_out else None
        version = await get_ui_version()

        logger.info(f"UI 回滚成功: {before_commit[:7] if before_commit else '?'} → {new_commit[:7] if new_commit else '?'}")

        return UIUpdateResult(
            success=True,
            message=f"UI 已回滚到 {new_commit[:7] if new_commit else commit_hash[:7]}",
            version=version,
            backup_commit=before_commit,
            commit=new_commit,
            commit_short=new_commit[:7] if new_commit else None,
        )

    except RuntimeError as e:
        return _fail(str(e))
    except Exception as e:
        logger.error(f"UI 回滚失败: {e}")
        return _fail(f"UI 回滚失败: {e}")
