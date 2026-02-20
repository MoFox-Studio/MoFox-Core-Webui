"""主程序仓库状态服务

提供：
- get_repo_status()     获取当前分支、所有可用分支
- refresh_branches()    fetch 远程后重新获取分支列表
"""

from __future__ import annotations

from src.kernel.logger import get_logger
from .runner import run_git, is_repo_available
from .models import RepoStatus

logger = get_logger(name="GitStatus", color="#89DCEB")


async def get_repo_status() -> RepoStatus:
    """获取主程序仓库状态。"""
    if not is_repo_available():
        return RepoStatus(is_git_repo=False, error="仓库目录不存在")

    try:
        # 检测是否是 git 仓库
        stdout, _, code = await run_git("rev-parse", "--is-inside-work-tree")
        if code != 0 or stdout != "true":
            return RepoStatus(is_git_repo=False, error="当前目录不是 Git 仓库")

        # 获取当前分支
        branch_out, _, _ = await run_git("rev-parse", "--abbrev-ref", "HEAD")
        current_branch = branch_out if branch_out else None

        # 获取所有本地分支 + 远程跟踪分支（去重）
        local_out, _, _ = await run_git("branch", "--format=%(refname:short)")
        remote_out, _, _ = await run_git(
            "branch", "-r", "--format=%(refname:short)"
        )

        local_branches = [b.strip() for b in local_out.splitlines() if b.strip()]

        # 远程分支去掉 origin/ 前缀，过滤 HEAD
        remote_branches: list[str] = []
        for b in remote_out.splitlines():
            b = b.strip()
            if not b or "HEAD" in b:
                continue
            # 去掉 origin/ 前缀
            if "/" in b:
                short = b.split("/", 1)[1]
            else:
                short = b
            remote_branches.append(short)

        # 合并去重，本地分支在前
        all_branches = local_branches.copy()
        for b in remote_branches:
            if b not in all_branches:
                all_branches.append(b)

        return RepoStatus(
            is_git_repo=True,
            current_branch=current_branch,
            available_branches=all_branches,
        )

    except RuntimeError as e:
        return RepoStatus(is_git_repo=False, error=str(e))
    except Exception as e:
        logger.error(f"获取仓库状态失败: {e}")
        return RepoStatus(is_git_repo=False, error=f"获取仓库状态失败: {e}")


async def refresh_branches() -> RepoStatus:
    """执行 git fetch 拉取远程信息，然后返回最新的仓库状态。

    fetch 失败时仍返回当前本地状态，并将警告附加到 error 字段。
    """
    fetch_error: str | None = None
    try:
        _, stderr, code = await run_git("fetch", "--prune", timeout=30.0)
        if code != 0:
            fetch_error = f"fetch 失败（{stderr}），分支列表可能不是最新"
            logger.warning(fetch_error)
    except RuntimeError as e:
        fetch_error = str(e)
        logger.warning(f"fetch 远程分支失败: {e}")

    status = await get_repo_status()
    # 仅在无其他错误时附加 fetch 警告
    if fetch_error and status.error is None:
        status = status.model_copy(update={"error": fetch_error})
    return status
