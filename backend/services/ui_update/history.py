"""UI 历史版本服务

提供：
- get_ui_backups(limit)          获取最近 N 条提交作为历史版本列表
- get_ui_commit_detail(hash)     获取指定 commit 的完整详情
"""

from __future__ import annotations

from src.kernel.logger import get_logger
from .runner import is_ui_git_repo, run_ui_git, get_ui_version
from .models import UIBackupInfo, UIBackupsResponse, UICommitDetail, FileChange

logger = get_logger(name="UIHistory", color="#CBA6F7")

# 默认显示的历史版本数
_BACKUP_LIMIT = 20

# git log 分隔符（低冲突特殊标记）
_SEP = "||UI_SEP||"
_RECORD_SEP = "||UI_RECORD||"

# log format：完整hash | 短hash | subject | author | ISO 时间
_LOG_FORMAT = f"%H{_SEP}%h{_SEP}%s{_SEP}%an{_SEP}%aI{_RECORD_SEP}"

# git 状态字母到中文的映射
_STATUS_MAP: dict[str, str] = {
    "A": "新增",
    "M": "修改",
    "D": "删除",
    "R": "重命名",
    "C": "复制",
    "T": "类型变更",
    "U": "未合并",
}


def _map_status(letter: str) -> str:
    """将 git diff-tree 状态字母映射为中文，未知字母原样返回。"""
    return _STATUS_MAP.get(letter[0].upper(), letter)


async def _get_tag_for_commit(commit_hash: str) -> str | None:
    """获取指定 commit 上直接打的 tag，无则返回 None。"""
    try:
        out, _, code = await run_ui_git("tag", "--points-at", commit_hash)
        if code == 0 and out:
            # 取第一行（可能存在多个 tag）
            return out.splitlines()[0].strip() or None
    except RuntimeError:
        pass
    return None


async def get_ui_backups(limit: int = _BACKUP_LIMIT) -> UIBackupsResponse:
    """获取 static/ 仓库最近 N 条提交，作为可回滚的历史版本列表。"""
    if not is_ui_git_repo():
        return UIBackupsResponse(success=False, error="插件根目录不是独立的 git 仓库")

    try:
        # 当前 HEAD
        head_out, _, _ = await run_ui_git("rev-parse", "HEAD")
        current_commit = head_out[:40] if head_out else ""

        # 获取最近 N 条提交
        log_out, _, code = await run_ui_git(
            "log",
            f"--pretty=format:{_LOG_FORMAT}",
            f"-{limit}",
        )
        if code != 0:
            return UIBackupsResponse(success=False, error="获取提交历史失败")

        records: list[UIBackupInfo] = []
        for raw in log_out.split(_RECORD_SEP):
            raw = raw.strip()
            if not raw:
                continue
            parts = raw.split(_SEP)
            if len(parts) < 5:
                continue

            commit_hash   = parts[0].strip()
            commit_short  = parts[1].strip()
            message       = parts[2].strip()
            # author      = parts[3]  # 暂不展示
            timestamp     = parts[4].strip()

            # 尝试解析该 commit 上的 tag 作为版本
            version = await _get_tag_for_commit(commit_hash)

            records.append(UIBackupInfo(
                commit=commit_hash,
                commit_short=commit_short,
                version=version,
                message=message,
                timestamp=timestamp,
                is_current=(commit_hash == current_commit),
            ))

        return UIBackupsResponse(success=True, data=records)

    except RuntimeError as e:
        return UIBackupsResponse(success=False, error=str(e))
    except Exception as e:
        logger.error(f"获取 UI 历史版本列表失败: {e}")
        return UIBackupsResponse(success=False, error=f"获取 UI 历史版本列表失败: {e}")


async def get_ui_commit_detail(commit_hash: str) -> UICommitDetail:
    """获取指定 commit 的完整详情，含变更文件列表与统计。"""
    if not is_ui_git_repo():
        return UICommitDetail(success=False, error="插件根目录不是独立的 git 仓库")

    try:
        # ---------- 基础信息 ----------
        # format: hash | short | subject | body | author | ISO_date
        _DETAIL_SEP = "||D_SEP||"
        info_out, _, info_code = await run_ui_git(
            "show",
            "-s",
            f"--pretty=format:%H{_DETAIL_SEP}%h{_DETAIL_SEP}%s{_DETAIL_SEP}%b{_DETAIL_SEP}%an{_DETAIL_SEP}%aI",
            commit_hash,
        )
        if info_code != 0:
            return UICommitDetail(success=False, error=f"commit 不存在: {commit_hash}")

        parts = info_out.split(_DETAIL_SEP)
        if len(parts) < 6:
            return UICommitDetail(success=False, error="无法解析 commit 信息")

        full_hash    = parts[0].strip()
        short_hash   = parts[1].strip()
        subject      = parts[2].strip()
        body         = parts[3].strip() or None
        author       = parts[4].strip()
        timestamp    = parts[5].strip()

        # 版本号（该 commit 上的 tag）
        version = await _get_tag_for_commit(full_hash)

        # ---------- 变更文件列表 ----------
        diff_out, _, _ = await run_ui_git(
            "diff-tree", "--no-commit-id", "-r", "--name-status", commit_hash
        )
        files_changed: list[FileChange] = []
        for line in diff_out.splitlines():
            line = line.strip()
            if not line:
                continue
            tokens = line.split("\t", maxsplit=2)
            if len(tokens) < 2:
                continue
            status_letter = tokens[0]
            # 重命名/复制：tokens = [R100, old_path, new_path]
            if len(tokens) == 3:
                path = f"{tokens[1]} → {tokens[2]}"
            else:
                path = tokens[1]
            files_changed.append(FileChange(
                status=_map_status(status_letter),
                path=path,
            ))

        # ---------- 变更统计 ----------
        stat_out, _, _ = await run_ui_git(
            "show", "--stat", "--no-patch", commit_hash
        )
        # stat 最后一行类似 "3 files changed, 42 insertions(+), 5 deletions(-)"
        stat_lines = [l for l in stat_out.splitlines() if l.strip()]
        stats = stat_lines[-1].strip() if stat_lines else None

        return UICommitDetail(
            success=True,
            commit=full_hash,
            commit_short=short_hash,
            version=version,
            message=subject,
            body=body,
            author=author,
            timestamp=timestamp,
            files_changed=files_changed if files_changed else None,
            stats=stats,
        )

    except RuntimeError as e:
        return UICommitDetail(success=False, error=str(e))
    except Exception as e:
        logger.error(f"获取 UI commit 详情失败: {e}")
        return UICommitDetail(success=False, error=f"获取 UI commit 详情失败: {e}")
