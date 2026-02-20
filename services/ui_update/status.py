"""UI 更新状态服务

提供：
- get_ui_status()    获取 UI 状态（版本信息 + 更新检测，合二为一）
"""

from __future__ import annotations

from src.kernel.logger import get_logger
from .runner import (
    PLUGIN_ROOT,
    ALLOWED_BRANCH,
    is_ui_git_repo,
    run_ui_git,
    get_ui_branch,
    get_ui_version,
)
from .models import UIStatusResult

logger = get_logger(name="UIStatus", color="#89DCEB")


async def get_ui_status() -> UIStatusResult:
    """获取 UI 静态文件仓库的完整状态。

    流程：
    1. 检查 static/ 是否是独立 git 仓库 → 否则禁用更新
    2. 检查当前分支是否为 webui-dist → 不是则禁用更新
    3. 获取当前版本、当前 commit
    4. git fetch origin 拉取远程信息
    5. 计算落后提交数 + 获取 changelog
    6. 获取远程最新 commit 和版本号
    """

    # ---------- 1. 是否是独立 git 仓库 ----------
    if not is_ui_git_repo():
        return UIStatusResult(
            success=True,
            update_enabled=False,
            message=(
                f"插件根目录（{PLUGIN_ROOT}）不是独立的 git 仓库。"
                "若要启用 UI 自动更新，请将插件目录以"
                " git worktree 或单独 clone 的方式置于 webui-dist 分支。"
            ),
        )

    try:
        # ---------- 2. 检查分支 ----------
        current_branch = await get_ui_branch()
        if current_branch != ALLOWED_BRANCH:
            return UIStatusResult(
                success=True,
                update_enabled=False,
                current_branch=current_branch,
                message=(
                    f'当前分支为 "{current_branch}"，'
                    f'仅 {ALLOWED_BRANCH} 分支支持自动更新。'
                ),
            )

        # ---------- 3. 当前 commit 与版本 ----------
        head_out, _, _ = await run_ui_git("rev-parse", "HEAD")
        current_commit = head_out[:40] if head_out else None
        current_version = await get_ui_version()

        # ---------- 4. fetch ----------
        _, fetch_err, fetch_code = await run_ui_git("fetch", "origin", timeout=30.0)
        if fetch_code != 0:
            # fetch 失败但仍可展示本地信息
            logger.warning(f"UI fetch 失败: {fetch_err}")
            return UIStatusResult(
                success=True,
                update_enabled=True,
                current_branch=current_branch,
                current_commit=current_commit,
                current_version=current_version,
                error=f"无法连接到远程仓库: {fetch_err}",
            )

        # ---------- 5. 落后提交数 ----------
        behind_out, _, _ = await run_ui_git("rev-list", "--count", "HEAD..@{u}")
        try:
            commits_behind = int(behind_out)
        except (ValueError, TypeError):
            commits_behind = 0

        # ---------- 6. changelog ----------
        changelog: list[str] = []
        if commits_behind > 0:
            log_out, _, _ = await run_ui_git(
                "log", "--oneline", "--no-decorate", "HEAD..@{u}"
            )
            changelog = [l.strip() for l in log_out.splitlines() if l.strip()]

        # ---------- 7. 远程最新 commit 与版本 ----------
        remote_out, _, remote_code = await run_ui_git("rev-parse", "@{u}")
        latest_commit: str | None = None
        latest_version: str | None = None
        if remote_code == 0 and remote_out:
            latest_commit = remote_out[:40]
            latest_version = await get_ui_version(latest_commit)

        return UIStatusResult(
            success=True,
            update_enabled=True,
            has_update=commits_behind > 0,
            current_branch=current_branch,
            current_commit=current_commit,
            current_version=current_version,
            latest_commit=latest_commit,
            latest_version=latest_version,
            changelog=changelog,
            commits_behind=commits_behind,
        )

    except RuntimeError as e:
        return UIStatusResult(success=False, error=str(e))
    except Exception as e:
        logger.error(f"获取 UI 状态失败: {e}")
        return UIStatusResult(success=False, error=f"获取 UI 状态失败: {e}")
