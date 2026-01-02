"""
UI 版本管理器
管理 WebUI 静态文件的版本检查、Git Pull 更新、备份恢复等功能
支持同时更新前端和后端代码
"""

import subprocess
from datetime import datetime
from pathlib import Path
from typing import Optional, List

from src.common.logger import get_logger

logger = get_logger("WebUI.UIVersionManager")


# ==================== 默认配置（硬编码） ====================

GITHUB_OWNER = "MoFox-Studio"
GITHUB_REPO = "MoFox-Core-Webui"
GITHUB_BRANCH = "webui-dist"
GITHUB_REPO_URL = f"https://github.com/{GITHUB_OWNER}/{GITHUB_REPO}.git"
AUTO_CHECK = True
CHECK_INTERVAL = 60  # 分钟
MAX_HISTORY_COMMITS = 20  # 列出的历史提交数量


class UIVersionManager:
    """UI 版本管理器 - 使用 Git Pull 更新前端和后端"""

    def __init__(self):
        """初始化 UI 版本管理器"""
        # 项目根目录（插件目录，backend 内容直接在此）
        # utils/update/ui_version_manager.py -> 往上3层到根目录
        self.project_root = Path(__file__).parent.parent.parent
        
        # Git 可执行文件路径
        self._git_path: Optional[str] = None
        
        logger.debug(f"UI 版本管理器初始化: project_root={self.project_root}")

    def _get_git_path(self) -> Optional[str]:
        """获取 Git 可执行文件路径"""
        if self._git_path:
            return self._git_path
        
        # 尝试从 git_detector 获取
        try:
            from .git_detector import GitDetector
            detector = GitDetector()
            self._git_path = detector.get_git_executable()
        except Exception:
            self._git_path = "git"  # 使用系统默认
        
        return self._git_path

    def _run_git_command(self, args: List[str], cwd: Optional[Path] = None) -> tuple[bool, str]:
        """
        运行 Git 命令
        
        Args:
            args: Git 命令参数
            cwd: 工作目录，默认使用项目根目录
            
        Returns:
            (success, output)
        """
        git_path = self._get_git_path()
        if not git_path:
            return False, "Git 不可用"
        
        work_dir = cwd or self.project_root
        
        try:
            result = subprocess.run(
                [git_path] + args,
                cwd=str(work_dir),
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='replace',
                timeout=120
            )
            
            output = result.stdout + result.stderr
            success = result.returncode == 0
            
            if not success:
                logger.warning(f"Git 命令失败: {args}, 输出: {output}")
            
            return success, output.strip()
        except subprocess.TimeoutExpired:
            return False, "Git 命令超时"
        except Exception as e:
            return False, str(e)

    def _is_git_repo(self) -> bool:
        """检查项目是否是 Git 仓库"""
        git_dir = self.project_root / ".git"
        return git_dir.exists()

    def _get_current_branch(self) -> Optional[str]:
        """获取当前分支名称"""
        if not self._is_git_repo():
            return None
        success, branch = self._run_git_command(["rev-parse", "--abbrev-ref", "HEAD"])
        return branch.strip() if success else None

    def is_update_enabled(self) -> bool:
        """
        检查是否启用更新功能
        只有在 webui-dist 分支上才启用更新
        """
        current_branch = self._get_current_branch()
        return current_branch == GITHUB_BRANCH

    def _init_git_repo(self) -> tuple[bool, str]:
        """初始化 Git 仓库（如果不存在）"""
        if self._is_git_repo():
            return True, "仓库已存在"
        
        logger.info("初始化 Git 仓库...")
        
        # 初始化仓库
        success, output = self._run_git_command(["init"])
        if not success:
            return False, f"初始化失败: {output}"
        
        # 添加远程仓库
        success, output = self._run_git_command(["remote", "add", "origin", GITHUB_REPO_URL])
        if not success and "already exists" not in output:
            return False, f"添加远程仓库失败: {output}"
        
        return True, "仓库初始化成功"

    def _ensure_correct_branch(self) -> tuple[bool, str]:
        """确保当前在正确的分支上"""
        # 获取当前分支
        success, current_branch = self._run_git_command(["rev-parse", "--abbrev-ref", "HEAD"])
        
        if success and current_branch == GITHUB_BRANCH:
            return True, f"已在 {GITHUB_BRANCH} 分支"
        
        # 尝试切换到目标分支
        success, output = self._run_git_command(["checkout", GITHUB_BRANCH])
        if success:
            return True, f"已切换到 {GITHUB_BRANCH} 分支"
        
        # 如果分支不存在，尝试从远程获取
        success, output = self._run_git_command(["fetch", "origin", GITHUB_BRANCH])
        if not success:
            return False, f"获取分支失败: {output}"
        
        success, output = self._run_git_command(["checkout", "-b", GITHUB_BRANCH, f"origin/{GITHUB_BRANCH}"])
        if success:
            return True, f"已创建并切换到 {GITHUB_BRANCH} 分支"
        
        return False, f"切换分支失败: {output}"

    def get_current_version(self) -> Optional[dict]:
        """
        获取本地版本信息（通过 Git 提交信息）
        
        Returns:
            dict: {"version": str, "commit": str, "build_time": str, "branch": str}
        """
        if not self._is_git_repo():
            return None
        
        try:
            # 获取最新提交的简短哈希
            success, commit_short = self._run_git_command(["rev-parse", "--short", "HEAD"])
            if not success:
                return None
            
            # 获取完整哈希
            success, commit_full = self._run_git_command(["rev-parse", "HEAD"])
            
            # 获取提交时间
            success, commit_time = self._run_git_command(["log", "-1", "--format=%ci"])
            
            # 获取当前分支
            success, branch = self._run_git_command(["rev-parse", "--abbrev-ref", "HEAD"])
            
            # 从提交消息中提取版本号（格式: Build: vYYYY.MMDD.HHMM）
            success, commit_msg = self._run_git_command(["log", "-1", "--format=%s"])
            version = "unknown"
            if success and "Build: v" in commit_msg:
                try:
                    version = commit_msg.split("Build: v")[1].split()[0]
                except Exception:
                    pass
            
            # 如果没有从消息中获取到版本，使用提交时间生成
            if version == "unknown" and commit_time:
                try:
                    from datetime import datetime
                    dt = datetime.fromisoformat(commit_time.split()[0] + "T" + commit_time.split()[1])
                    version = dt.strftime("%Y.%m%d.%H%M")
                except Exception:
                    version = commit_short
            
            version_info = {
                "version": version,
                "commit": commit_full.strip() if commit_full else commit_short,
                "commit_short": commit_short.strip(),
                "build_time": commit_time.strip() if commit_time else "",
                "branch": branch.strip() if branch else GITHUB_BRANCH,
            }
            
            logger.debug(f"当前版本: {version_info}")
            return version_info
            
        except Exception as e:
            logger.error(f"获取版本信息失败: {e}")
            return None

    async def fetch_remote_version(self) -> Optional[dict]:
        """
        获取远程最新版本信息（通过 Git fetch）
        
        Returns:
            dict: {"version": str, "commit": str, "changelog": list}
        """
        try:
            # 先 fetch 远程分支
            success, _ = self._run_git_command(["fetch", "origin", GITHUB_BRANCH])
            if not success:
                return None
            
            # 获取远程分支的最新提交信息
            success, commit = self._run_git_command(["rev-parse", f"origin/{GITHUB_BRANCH}"])
            if not success:
                return None
            
            success, commit_short = self._run_git_command(["rev-parse", "--short", f"origin/{GITHUB_BRANCH}"])
            
            # 获取远程提交消息
            success, commit_msg = self._run_git_command(["log", f"origin/{GITHUB_BRANCH}", "-1", "--format=%s"])
            version = "unknown"
            if success and "Build: v" in commit_msg:
                try:
                    version = commit_msg.split("Build: v")[1].split()[0]
                except Exception:
                    pass
            
            # 获取远程提交时间
            success, commit_time = self._run_git_command(["log", f"origin/{GITHUB_BRANCH}", "-1", "--format=%ci"])
            
            # 如果没有从消息中获取到版本，使用提交时间生成
            if version == "unknown" and commit_time:
                try:
                    from datetime import datetime
                    dt = datetime.fromisoformat(commit_time.split()[0] + "T" + commit_time.split()[1])
                    version = dt.strftime("%Y.%m%d.%H%M")
                except Exception:
                    version = commit_short.strip() if commit_short else "unknown"
            
            # 获取 changelog（最近 10 条提交）
            success, log_output = self._run_git_command([
                "log", f"origin/{GITHUB_BRANCH}", "--oneline", "-10", "--format=%s"
            ])
            changelog = log_output.split("\n") if success and log_output else []
            
            version_info = {
                "version": version,
                "commit": commit.strip() if commit else "",
                "commit_short": commit_short.strip() if commit_short else "",
                "build_time": commit_time.strip() if commit_time else "",
                "changelog": changelog,
            }
            
            logger.info(f"远程版本: {version}")
            return version_info
            
        except Exception as e:
            logger.error(f"获取远程版本失败: {e}")
            return None

    async def check_update(self) -> dict:
        """
        检查是否有更新（通过 Git fetch）
        
        Returns:
            dict: {
                "success": bool,
                "has_update": bool,
                "current_version": str,
                "latest_version": str,
                "changelog": list,
                "commits_behind": int,
                "error": str,
                "update_enabled": bool
            }
        """
        try:
            # 获取本地版本
            local_version = self.get_current_version()
            current_version = local_version.get("version", "unknown") if local_version else "未安装"
            current_commit = local_version.get("commit_short", "") if local_version else ""
            current_branch = self._get_current_branch()
            
            # 检查是否启用更新（只有 webui-dist 分支才启用）
            update_enabled = self.is_update_enabled()
            if not update_enabled:
                return {
                    "success": True,
                    "has_update": False,
                    "current_version": current_version,
                    "current_branch": current_branch,
                    "update_enabled": False,
                    "message": f"当前分支为 {current_branch}，非 {GITHUB_BRANCH} 分支，更新功能已禁用"
                }
            
            # 检查是否是 Git 仓库
            if not self._is_git_repo():
                return {
                    "success": True,
                    "has_update": False,
                    "current_version": "未安装",
                    "update_enabled": False,
                    "message": "当前目录不是 Git 仓库，更新功能已禁用"
                }
            
            # Fetch 远程更新
            success, output = self._run_git_command(["fetch", "origin", GITHUB_BRANCH])
            if not success:
                return {
                    "success": False,
                    "has_update": False,
                    "current_version": current_version,
                    "error": f"获取远程更新失败: {output}"
                }
            
            # 检查是否有新提交
            success, commits_behind = self._run_git_command([
                "rev-list", "--count", f"HEAD..origin/{GITHUB_BRANCH}"
            ])
            
            commits_count = int(commits_behind) if success and commits_behind.isdigit() else 0
            has_update = commits_count > 0
            
            # 获取远程版本信息
            remote_version = await self.fetch_remote_version()
            latest_version = remote_version.get("version", "unknown") if remote_version else "unknown"
            latest_commit = remote_version.get("commit_short", "") if remote_version else ""
            
            # 获取待更新的提交日志（解析 Recent changes 部分）
            changelog = []
            if has_update:
                # 获取最新提交的完整消息体
                success, log_output = self._run_git_command([
                    "log", "--format=%B", f"HEAD..origin/{GITHUB_BRANCH}", "-1"
                ])
                if success and log_output:
                    # 查找 "Recent changes:" 部分并提取变更列表
                    lines = log_output.split("\n")
                    in_changes_section = False
                    for line in lines:
                        line = line.strip()
                        if "Recent changes:" in line or "recent changes:" in line.lower():
                            in_changes_section = True
                            continue
                        if in_changes_section and line.startswith("-"):
                            changelog.append(line)
            
            return {
                "success": True,
                "has_update": has_update,
                "current_version": current_version,
                "current_commit": current_commit,
                "latest_version": latest_version,
                "latest_commit": latest_commit,
                "changelog": changelog,
                "commits_behind": commits_count,
                "update_enabled": True,
            }
        except Exception as e:
            logger.error(f"检查更新失败: {e}")
            return {
                "success": False,
                "has_update": False,
                "error": str(e)
            }

    def create_backup(self, backup_message: Optional[str] = None) -> Optional[str]:
        """
        记录当前 Git 提交作为备份点
        
        Args:
            backup_message: 备份说明信息
            
        Returns:
            当前提交的 commit hash 或 None
        """
        try:
            if not self._is_git_repo():
                logger.warning("当前目录不是 Git 仓库，无法创建备份")
                return None
            
            # 获取当前提交 hash
            success, commit_hash = self._run_git_command(["rev-parse", "HEAD"])
            if not success:
                logger.error("获取当前提交失败")
                return None
            
            commit_hash = commit_hash.strip()
            
            # 获取简短 hash
            success, commit_short = self._run_git_command(["rev-parse", "--short", "HEAD"])
            commit_short = commit_short.strip() if success else commit_hash[:7]
            
            message = backup_message or "更新前自动备份"
            logger.info(f"已记录备份点: {commit_short} ({message})")
            
            return commit_hash
            
        except Exception as e:
            logger.error(f"创建备份失败: {e}")
            return None

    def get_backup_commit(self) -> Optional[str]:
        """
        获取更新前的备份提交（用于回滚）
        通过 reflog 查找上一个 HEAD 位置
        
        Returns:
            上一个提交的 hash 或 None
        """
        try:
            # 使用 reflog 获取上一个 HEAD 位置
            success, output = self._run_git_command(["rev-parse", "HEAD@{1}"])
            if success:
                return output.strip()
            return None
        except Exception:
            return None

    async def download_and_apply(self) -> dict:
        """
        使用 Git Pull 下载并应用更新
            
        Returns:
            dict: {"success": bool, "message": str, "version": str, "backup_name": str, "error": str}
        """
        try:
            # 0. 检查是否启用更新
            if not self.is_update_enabled():
                current_branch = self._get_current_branch()
                return {
                    "success": False, 
                    "error": f"当前分支为 {current_branch}，非 {GITHUB_BRANCH} 分支，更新功能已禁用"
                }
            
            # 1. 记录当前提交作为备份点
            backup_commit = self.create_backup("更新前自动备份")
            logger.info(f"已记录备份点: {backup_commit[:7] if backup_commit else 'None'}")
            
            # 2. 检查/初始化 Git 仓库
            if not self._is_git_repo():
                success, msg = self._init_git_repo()
                if not success:
                    return {"success": False, "error": msg, "backup_commit": backup_commit}
            
            # 3. 设置远程 URL
            self._run_git_command(["remote", "set-url", "origin", GITHUB_REPO_URL])
            
            # 4. Fetch 远程更新
            success, output = self._run_git_command(["fetch", "origin", GITHUB_BRANCH])
            if not success:
                return {"success": False, "error": f"获取远程更新失败: {output}", "backup_commit": backup_commit}
            
            # 5. 确保在正确的分支
            success, msg = self._ensure_correct_branch()
            if not success:
                return {"success": False, "error": msg, "backup_commit": backup_commit}
            
            # 6. 重置本地修改并拉取更新
            # 先暂存本地修改
            self._run_git_command(["stash", "push", "-m", "auto-stash-before-update"])
            
            # 强制重置到远程分支
            success, output = self._run_git_command(["reset", "--hard", f"origin/{GITHUB_BRANCH}"])
            if not success:
                return {"success": False, "error": f"重置失败: {output}", "backup_commit": backup_commit}
            
            # 7. 获取更新后的版本
            new_version = self.get_current_version()
            version = new_version.get("version", "unknown") if new_version else "unknown"
            
            logger.info(f"更新完成: v{version}")
            return {
                "success": True,
                "message": f"更新成功，已更新到 v{version}",
                "version": version,
                "backup_commit": backup_commit
            }
            
        except Exception as e:
            logger.error(f"更新失败: {e}")
            return {"success": False, "error": str(e)}

    def list_backups(self) -> List[dict]:
        """
        列出 Git 历史提交作为可回滚的备份点
        
        Returns:
            提交历史列表 [{"commit": str, "commit_short": str, "version": str, "message": str, "timestamp": str, "is_current": bool}]
        """
        backups = []
        
        try:
            if not self._is_git_repo():
                logger.warning("当前目录不是 Git 仓库")
                return backups
            
            # 获取当前 HEAD
            success, current_head = self._run_git_command(["rev-parse", "HEAD"])
            current_head = current_head.strip() if success else ""
            
            # 获取提交历史
            # 格式: commit_hash|short_hash|时间|提交消息
            success, log_output = self._run_git_command([
                "log", f"-{MAX_HISTORY_COMMITS}",
                "--format=%H|%h|%ci|%s"
            ])
            
            if not success or not log_output:
                return backups
            
            for line in log_output.strip().split("\n"):
                if not line:
                    continue
                
                parts = line.split("|", 3)
                if len(parts) < 4:
                    continue
                
                commit_hash, commit_short, timestamp, message = parts
                
                # 从提交消息中提取版本号
                version = None
                if "Build: v" in message:
                    try:
                        version = message.split("Build: v")[1].split()[0]
                    except Exception:
                        pass
                
                # 如果没有版本号，尝试从时间生成
                if not version:
                    try:
                        dt = datetime.fromisoformat(timestamp.split()[0] + "T" + timestamp.split()[1])
                        version = dt.strftime("%Y.%m%d.%H%M")
                    except Exception:
                        version = commit_short
                
                backups.append({
                    "commit": commit_hash,
                    "commit_short": commit_short,
                    "version": version,
                    "message": message,
                    "timestamp": timestamp,
                    "is_current": commit_hash == current_head
                })
                
        except Exception as e:
            logger.error(f"列出备份失败: {e}")
        
        return backups

    def rollback(self, commit_hash: str) -> dict:
        """
        回滚到指定的 Git 提交
        
        Args:
            commit_hash: 目标提交的 hash（完整或简短均可）
            
        Returns:
            dict: {"success": bool, "message": str, "version": str, "error": str}
        """
        try:
            if not self._is_git_repo():
                return {"success": False, "error": "当前目录不是 Git 仓库"}
            
            # 验证提交是否存在
            success, full_hash = self._run_git_command(["rev-parse", "--verify", commit_hash])
            if not success:
                return {"success": False, "error": f"提交不存在: {commit_hash}"}
            
            full_hash = full_hash.strip()
            
            # 获取当前提交用于日志
            current_version = self.get_current_version()
            current_commit = current_version.get("commit_short", "unknown") if current_version else "unknown"
            
            logger.info(f"正在回滚: {current_commit} -> {commit_hash[:7]}")
            
            # 使用 git reset --hard 回滚到指定提交
            success, output = self._run_git_command(["reset", "--hard", full_hash])
            if not success:
                return {"success": False, "error": f"回滚失败: {output}"}
            
            # 获取回滚后的版本信息
            restored_version = self.get_current_version()
            version_str = restored_version.get("version", "unknown") if restored_version else "unknown"
            commit_short = restored_version.get("commit_short", commit_hash[:7]) if restored_version else commit_hash[:7]
            
            logger.info(f"回滚完成: -> {commit_short} (v{version_str})")
            return {
                "success": True,
                "message": f"已回滚到 {commit_short} (v{version_str})",
                "version": version_str,
                "commit": full_hash,
                "commit_short": commit_short
            }
            
        except Exception as e:
            logger.error(f"回滚失败: {e}")
            return {"success": False, "error": str(e)}

    def get_commit_detail(self, commit_hash: str) -> dict:
        """
        获取指定提交的详细信息
        
        Args:
            commit_hash: 提交的 hash（完整或简短均可）
            
        Returns:
            dict: {
                "success": bool,
                "commit": str,
                "commit_short": str,
                "message": str,
                "body": str,
                "author": str,
                "timestamp": str,
                "files_changed": list,
                "stats": str,
                "error": str
            }
        """
        try:
            if not self._is_git_repo():
                return {"success": False, "error": "当前目录不是 Git 仓库"}
            
            # 验证提交是否存在
            success, full_hash = self._run_git_command(["rev-parse", "--verify", commit_hash])
            if not success:
                return {"success": False, "error": f"提交不存在: {commit_hash}"}
            
            full_hash = full_hash.strip()
            
            # 获取简短 hash
            success, commit_short = self._run_git_command(["rev-parse", "--short", full_hash])
            commit_short = commit_short.strip() if success else full_hash[:7]
            
            # 获取提交标题
            success, subject = self._run_git_command(["log", "-1", "--format=%s", full_hash])
            subject = subject.strip() if success else ""
            
            # 获取提交正文（包含更新内容）
            success, body = self._run_git_command(["log", "-1", "--format=%b", full_hash])
            body = body.strip() if success else ""
            
            # 获取作者
            success, author = self._run_git_command(["log", "-1", "--format=%an <%ae>", full_hash])
            author = author.strip() if success else ""
            
            # 获取提交时间
            success, timestamp = self._run_git_command(["log", "-1", "--format=%ci", full_hash])
            timestamp = timestamp.strip() if success else ""
            
            # 获取修改的文件列表
            success, files_output = self._run_git_command(["diff-tree", "--no-commit-id", "--name-status", "-r", full_hash])
            files_changed = []
            if success and files_output:
                for line in files_output.strip().split("\n"):
                    if line:
                        parts = line.split("\t", 1)
                        if len(parts) == 2:
                            status, filepath = parts
                            status_map = {"A": "新增", "M": "修改", "D": "删除", "R": "重命名"}
                            files_changed.append({
                                "status": status_map.get(status[0], status),
                                "path": filepath
                            })
            
            # 获取统计信息
            success, stats = self._run_git_command(["diff-tree", "--stat", "--no-commit-id", full_hash])
            stats = stats.strip() if success else ""
            
            # 提取版本号
            version = None
            if "Build: v" in subject:
                try:
                    version = subject.split("Build: v")[1].split()[0]
                except Exception:
                    pass
            
            return {
                "success": True,
                "commit": full_hash,
                "commit_short": commit_short,
                "version": version,
                "message": subject,
                "body": body,
                "author": author,
                "timestamp": timestamp,
                "files_changed": files_changed,
                "stats": stats
            }
            
        except Exception as e:
            logger.error(f"获取提交详情失败: {e}")
            return {"success": False, "error": str(e)}
    
    async def git_pull_update(self) -> dict:
        """
        直接使用 Git Pull 更新（简化接口）
            
        Returns:
            dict: {"success": bool, "message": str, "version": str, "error": str}
        """
        return await self.download_and_apply()
