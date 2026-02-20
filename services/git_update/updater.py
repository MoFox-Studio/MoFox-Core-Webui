"""主程序更新服务

提供：
- check_updates()                       检查是否有可用更新
- update_main_program(force, backup)    执行 pull 更新
- switch_branch(branch)                 切换分支
"""

from __future__ import annotations

from src.kernel.logger import get_logger
from .runner import run_git, is_repo_available
from .models import UpdateCheck, UpdateResult, SwitchBranchResult

logger = get_logger(name="GitUpdater", color="#A6E3A1")


async def check_updates() -> UpdateCheck:
    """检查主程序是否有可用更新。

    流程：
    1. git fetch origin 拉取最新远程信息（网络操作）
    2. 对比本地 HEAD 与 @{u}（upstream）的提交差距
    3. 获取每条提交的 oneline 日志作为更新内容
    """
    if not is_repo_available():
        return _fail("仓库目录不存在")

    try:
        # --- 1. fetch ---
        _, fetch_err, fetch_code = await run_git("fetch", "origin", timeout=30.0)
        if fetch_code != 0:
            return _fail(f"无法连接到远程仓库: {fetch_err}")

        # --- 2. 当前分支 ---
        branch_out, _, _ = await run_git("rev-parse", "--abbrev-ref", "HEAD")
        current_branch = branch_out or None

        # --- 3. 本地 HEAD commit ---
        local_out, _, _ = await run_git("rev-parse", "HEAD")
        current_commit = local_out[:40] if local_out else None

        # --- 4. 远程 commit ---
        remote_out, _, remote_code = await run_git("rev-parse", "@{u}")
        if remote_code != 0:
            # 当前分支没有上游跟踪
            return UpdateCheck(
                success=True,
                has_update=False,
                current_commit=current_commit,
                branch=current_branch,
                error="当前分支没有设置远程跟踪分支",
            )
        remote_commit = remote_out[:40] if remote_out else None

        # --- 5. 落后提交数 ---
        behind_out, _, _ = await run_git(
            "rev-list", "--count", "HEAD..@{u}"
        )
        try:
            commits_behind = int(behind_out)
        except ValueError:
            commits_behind = 0

        # --- 6. 更新日志 ---
        logs: list[str] = []
        if commits_behind > 0:
            log_out, _, _ = await run_git(
                "log", "--oneline", "HEAD..@{u}", "--no-decorate"
            )
            logs = [l.strip() for l in log_out.splitlines() if l.strip()]

        return UpdateCheck(
            success=True,
            has_update=commits_behind > 0,
            current_commit=current_commit,
            remote_commit=remote_commit,
            commits_behind=commits_behind,
            update_logs=logs,
            branch=current_branch,
        )

    except RuntimeError as e:
        return _fail(str(e))
    except Exception as e:
        logger.error(f"检查更新失败: {e}")
        return _fail(f"检查更新失败: {e}")


async def update_main_program(
    force: bool = False,
    create_backup: bool = True,
) -> UpdateResult:
    """执行主程序更新（git pull）。

    Args:
        force:         强制更新，会先 reset --hard 放弃本地修改
        create_backup: 是否在更新前记录当前 commit（用于回滚）
    """
    if not is_repo_available():
        return _update_fail("仓库目录不存在")

    try:
        backup_commit: str | None = None

        # --- 记录当前 commit 作为回滚点 ---
        if create_backup:
            head_out, _, _ = await run_git("rev-parse", "HEAD")
            backup_commit = head_out[:40] if head_out else None

        # --- 强制模式：丢弃本地修改 ---
        if force:
            _, _, reset_code = await run_git("reset", "--hard", "HEAD")
            if reset_code != 0:
                return _update_fail("reset --hard 失败，请手动处理")
            # 清理未跟踪文件
            await run_git("clean", "-fd")

        # --- 执行 pull ---
        pull_out, pull_err, pull_code = await run_git(
            "pull", "--ff-only", timeout=60.0
        )

        # ff-only 失败时自动回退到 merge
        if pull_code != 0 and "Not possible to fast-forward" in pull_err:
            pull_out, pull_err, pull_code = await run_git(
                "pull", timeout=60.0
            )

        if pull_code != 0:
            return _update_fail(pull_err or "pull 失败")

        # --- 解析变更文件列表 ---
        updated_files: list[str] | None = None
        if backup_commit:
            diff_out, _, _ = await run_git(
                "diff", "--name-only", backup_commit, "HEAD"
            )
            if diff_out:
                updated_files = [f.strip() for f in diff_out.splitlines() if f.strip()]

        # 判断是否已经是最新
        already_up_to_date = "Already up to date" in pull_out or "Already up-to-date" in pull_out

        message = "已是最新版本，无需更新" if already_up_to_date else "更新成功，请重启程序以应用更改"

        return UpdateResult(
            success=True,
            message=message,
            updated_files=updated_files,
            backup_commit=backup_commit,
        )

    except RuntimeError as e:
        return _update_fail(str(e))
    except Exception as e:
        logger.error(f"更新失败: {e}")
        return _update_fail(f"更新失败: {e}")


async def switch_branch(branch: str) -> SwitchBranchResult:
    """切换到指定分支。

    如果本地没有该分支但远程有，会自动创建本地跟踪分支。
    """
    if not is_repo_available():
        return SwitchBranchResult(success=False, message="仓库目录不存在", error="repo_not_found")

    if not branch:
        return SwitchBranchResult(success=False, message="分支名不能为空", error="empty_branch")

    try:
        # 先尝试 checkout 本地分支
        _, err_local, code_local = await run_git("checkout", branch)

        if code_local != 0:
            # 尝试 checkout 并跟踪远程分支
            _, err_remote, code_remote = await run_git(
                "checkout", "-b", branch, f"origin/{branch}"
            )
            if code_remote != 0:
                error_msg = err_remote or err_local or f"切换到分支 {branch!r} 失败"
                return SwitchBranchResult(success=False, message=error_msg, error=error_msg)

        # 获取切换后的分支名
        new_branch_out, _, _ = await run_git("rev-parse", "--abbrev-ref", "HEAD")
        return SwitchBranchResult(
            success=True,
            message=f"已切换到分支 {new_branch_out!r}，请重启程序以应用更改",
            current_branch=new_branch_out or branch,
        )

    except RuntimeError as e:
        return SwitchBranchResult(success=False, message=str(e), error=str(e))
    except Exception as e:
        logger.error(f"切换分支失败: {e}")
        return SwitchBranchResult(success=False, message=f"切换分支失败: {e}", error=str(e))


# ==================== 内部帮助函数 ====================

def _fail(error: str) -> UpdateCheck:
    """生成 UpdateCheck 失败实例"""
    return UpdateCheck(success=False, has_update=False, error=error)


def _update_fail(error: str) -> UpdateResult:
    """生成 UpdateResult 失败实例"""
    return UpdateResult(success=False, message=error, error=error)
