"""主程序历史版本服务

提供：
- get_main_backups()              获取最近 N 条提交作为"历史版本"列表
- get_main_commit_detail(hash)    获取指定 commit 的详细信息
- rollback_version(hash)          将仓库 reset 到指定 commit
"""

from __future__ import annotations

import re

from src.kernel.logger import get_logger
from .runner import run_git, is_repo_available
from .models import MainBackupInfo, MainBackupsResponse, MainCommitDetail, FileChange, UpdateResult

logger = get_logger(name="GitHistory", color="#CBA6F7")

# 默认显示的历史版本数量
_BACKUP_LIMIT = 20

# git log 分隔符（不易在提交消息中出现的特殊标记）
_SEP = "||GIT_SEP||"
_RECORD_SEP = "||GIT_RECORD||"

# log format：hash|short|subject|author|date
_LOG_FORMAT = f"%H{_SEP}%h{_SEP}%s{_SEP}%an{_SEP}%aI{_RECORD_SEP}"


async def get_main_backups(limit: int = _BACKUP_LIMIT) -> MainBackupsResponse:
    """获取主程序最近 N 条提交列表，作为可回滚的历史版本。"""
    if not is_repo_available():
        return MainBackupsResponse(success=False, error="仓库目录不存在")

    try:
        # 获取当前 HEAD
        head_out, _, _ = await run_git("rev-parse", "HEAD")
        current_commit = head_out[:40] if head_out else ""

        # 获取最近 N 条提交
        log_out, _, code = await run_git(
            "log",
            f"--pretty=format:{_LOG_FORMAT}",
            f"-{limit}",
        )

        if code != 0:
            return MainBackupsResponse(success=False, error="获取提交历史失败")

        records: list[MainBackupInfo] = []
        for raw in log_out.split(_RECORD_SEP):
            raw = raw.strip()
            if not raw:
                continue
            parts = raw.split(_SEP)
            if len(parts) < 5:
                continue
            commit_hash, commit_short, message, author, timestamp = (
                parts[0].strip(),
                parts[1].strip(),
                parts[2].strip(),
                parts[3].strip(),
                parts[4].strip(),
            )
            records.append(MainBackupInfo(
                commit=commit_hash,
                commit_short=commit_short,
                message=message,
                author=author,
                timestamp=timestamp,
                is_current=commit_hash == current_commit,
            ))

        return MainBackupsResponse(success=True, data=records)

    except RuntimeError as e:
        return MainBackupsResponse(success=False, error=str(e))
    except Exception as e:
        logger.error(f"获取历史版本列表失败: {e}")
        return MainBackupsResponse(success=False, error=f"获取历史版本列表失败: {e}")


async def get_main_commit_detail(commit_hash: str) -> MainCommitDetail:
    """获取指定 commit 的详细信息，包含所有变更文件。"""
    if not is_repo_available():
        return MainCommitDetail(success=False, error="仓库目录不存在")

    if not commit_hash or not re.fullmatch(r"[0-9a-fA-F]{4,40}", commit_hash):
        return MainCommitDetail(success=False, error="无效的 commit hash")

    try:
        # 获取提交元数据（完整 commit 消息 + 摘要行分开）
        meta_out, _, meta_code = await run_git(
            "show",
            "--no-patch",
            "--format=%H%n%h%n%s%n%b%n---AUTHOR---%n%an%n---DATE---%n%aI",
            commit_hash,
        )
        if meta_code != 0:
            return MainCommitDetail(success=False, error=f"找不到 commit: {commit_hash!r}")

        lines = meta_out.splitlines()
        # 解析各字段
        full_hash = lines[0] if len(lines) > 0 else ""
        short_hash = lines[1] if len(lines) > 1 else ""

        # subject 是第 3 行
        subject = lines[2] if len(lines) > 2 else ""

        # body：从第 4 行到 ---AUTHOR--- 标记之前
        body_lines: list[str] = []
        author = ""
        date = ""
        section = "body"
        for line in lines[3:]:
            if line == "---AUTHOR---":
                section = "author"
            elif line == "---DATE---":
                section = "date"
            elif section == "body":
                body_lines.append(line)
            elif section == "author":
                author = line
            elif section == "date":
                date = line

        body = "\n".join(body_lines).strip()

        # 获取变更文件列表
        files_out, _, files_code = await run_git(
            "show",
            "--name-status",
            "--format=",
            commit_hash,
        )

        files_changed: list[FileChange] = []
        if files_code == 0 and files_out:
            for fline in files_out.splitlines():
                fline = fline.strip()
                if not fline:
                    continue
                parts = fline.split("\t", 1)
                if len(parts) == 2:
                    raw_status, file_path = parts
                    # 处理重命名（如 R100\told_name\tnew_name）
                    if raw_status.startswith("R"):
                        file_path_parts = fline.split("\t")
                        file_path = f"{file_path_parts[1]} → {file_path_parts[2]}" if len(file_path_parts) >= 3 else file_path
                        status_name = "重命名"
                    elif raw_status == "A":
                        status_name = "新增"
                    elif raw_status == "M":
                        status_name = "修改"
                    elif raw_status == "D":
                        status_name = "删除"
                    else:
                        status_name = raw_status
                    files_changed.append(FileChange(status=status_name, path=file_path))

        # 获取 diffstat 统计
        stats_out, _, _ = await run_git(
            "show",
            "--stat",
            "--format=",
            commit_hash,
        )
        stats = stats_out.splitlines()[-1].strip() if stats_out else None

        return MainCommitDetail(
            success=True,
            commit=full_hash,
            commit_short=short_hash,
            message=subject,
            body=body or None,
            author=author,
            timestamp=date,
            files_changed=files_changed,
            stats=stats,
        )

    except RuntimeError as e:
        return MainCommitDetail(success=False, error=str(e))
    except Exception as e:
        logger.error(f"获取 commit 详情失败: {e}")
        return MainCommitDetail(success=False, error=f"获取 commit 详情失败: {e}")


async def rollback_version(commit_hash: str) -> UpdateResult:
    """将仓库 hard reset 到指定 commit。

    Args:
        commit_hash: 目标 commit 的完整或简短 hash
    """
    if not is_repo_available():
        return UpdateResult(success=False, message="仓库目录不存在", error="repo_not_found")

    if not commit_hash or not re.fullmatch(r"[0-9a-fA-F]{4,40}", commit_hash):
        return UpdateResult(success=False, message="无效的 commit hash", error="invalid_hash")

    try:
        # 记录当前 HEAD 作为"撤销回滚"的凭据
        head_out, _, _ = await run_git("rev-parse", "HEAD")
        old_commit = head_out[:40] if head_out else None

        # 验证目标 commit 存在
        verify_out, _, verify_code = await run_git(
            "cat-file", "-t", commit_hash
        )
        if verify_code != 0 or verify_out.strip() not in ("commit", "tag"):
            return UpdateResult(
                success=False,
                message=f"找不到 commit {commit_hash!r}",
                backup_commit=old_commit,
                error="commit_not_found",
            )

        # 执行 reset
        _, err, reset_code = await run_git("reset", "--hard", commit_hash)
        if reset_code != 0:
            return UpdateResult(
                success=False,
                message=err or f"reset 到 {commit_hash!r} 失败",
                backup_commit=old_commit,
                error=err,
            )

        # 清理未跟踪文件
        await run_git("clean", "-fd")

        # 获取变更文件列表
        diff_out, _, _ = await run_git(
            "diff", "--name-only", commit_hash, old_commit or "HEAD"
        )
        updated_files = [f.strip() for f in diff_out.splitlines() if f.strip()] if diff_out else None

        short = commit_hash[:7]
        return UpdateResult(
            success=True,
            message=f"已回滚到版本 {short!r}，请重启程序以应用更改",
            updated_files=updated_files,
            backup_commit=old_commit,
        )

    except RuntimeError as e:
        return UpdateResult(success=False, message=str(e), error=str(e))
    except Exception as e:
        logger.error(f"回滚失败: {e}")
        return UpdateResult(success=False, message=f"回滚失败: {e}", error=str(e))
