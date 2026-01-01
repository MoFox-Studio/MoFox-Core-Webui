"""
UI 版本管理器
管理 WebUI 静态文件的版本检查、Git Pull 更新、备份恢复等功能
支持同时更新前端和后端代码
"""

import json
import shutil
import subprocess
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Optional, List

from src.common.logger import get_logger

logger = get_logger("WebUI.UIVersionManager")


# ==================== 默认配置（硬编码） ====================

GITHUB_OWNER = "MoFoxBot"
GITHUB_REPO = "MoFox-Core-Webui"
GITHUB_BRANCH = "webui-dist"
GITHUB_REPO_URL = f"https://github.com/{GITHUB_OWNER}/{GITHUB_REPO}.git"
MIRROR_URL = "https://ghproxy.com/"  # 可选镜像
AUTO_CHECK = True
CHECK_INTERVAL = 60  # 分钟
MAX_BACKUPS = 5


class UIVersionManager:
    """UI 版本管理器 - 使用 Git Pull 更新前端和后端"""

    def __init__(self, webui_dist_path: Optional[Path] = None):
        """
        初始化 UI 版本管理器
        
        Args:
            webui_dist_path: WebUI 静态文件目录，默认使用 mofox-webui/dist
        """
        # 获取项目根目录 (MoFox-Core-Webui)
        backend_dir = Path(__file__).parent.parent.parent
        self.project_root = backend_dir.parent
        
        # 获取 WebUI 静态文件目录
        if webui_dist_path:
            self.dist_path = webui_dist_path
        else:
            # 默认路径: MoFox-Core-Webui/mofox-webui/dist
            self.dist_path = self.project_root / "mofox-webui" / "dist"
        
        # 备份目录
        self.backup_dir = self.project_root / "backups"
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        
        # Git 可执行文件路径
        self._git_path: Optional[str] = None
        
        logger.info(f"UI 版本管理器初始化: project_root={self.project_root}, dist_path={self.dist_path}")

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

    def _init_git_repo(self, use_mirror: bool = False) -> tuple[bool, str]:
        """
        初始化 Git 仓库（如果不存在）
        
        Args:
            use_mirror: 是否使用镜像源
        """
        if self._is_git_repo():
            return True, "仓库已存在"
        
        logger.info("初始化 Git 仓库...")
        
        # 初始化仓库
        success, output = self._run_git_command(["init"])
        if not success:
            return False, f"初始化失败: {output}"
        
        # 添加远程仓库
        repo_url = f"{MIRROR_URL}{GITHUB_REPO_URL}" if use_mirror else GITHUB_REPO_URL
        success, output = self._run_git_command(["remote", "add", "origin", repo_url])
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
                # 尝试使用镜像
                self._run_git_command(["remote", "set-url", "origin", f"{MIRROR_URL}{GITHUB_REPO_URL}"])
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
                "error": str
            }
        """
        try:
            # 获取本地版本
            local_version = self.get_current_version()
            current_version = local_version.get("version", "unknown") if local_version else "未安装"
            current_commit = local_version.get("commit_short", "") if local_version else ""
            
            # 检查是否是 Git 仓库
            if not self._is_git_repo():
                return {
                    "success": True,
                    "has_update": True,
                    "current_version": "未安装",
                    "latest_version": "unknown",
                    "changelog": [],
                    "commits_behind": 0,
                    "need_init": True,  # 需要初始化仓库
                }
            
            # Fetch 远程更新
            success, output = self._run_git_command(["fetch", "origin", GITHUB_BRANCH])
            if not success:
                # 尝试使用镜像
                logger.info("尝试使用镜像源 fetch...")
                self._run_git_command(["remote", "set-url", "origin", f"{MIRROR_URL}{GITHUB_REPO_URL}"])
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
            
            # 获取待更新的提交日志
            changelog = []
            if has_update:
                success, log_output = self._run_git_command([
                    "log", "--oneline", f"HEAD..origin/{GITHUB_BRANCH}", "-10"
                ])
                if success and log_output:
                    changelog = log_output.split("\n")
            
            return {
                "success": True,
                "has_update": has_update,
                "current_version": current_version,
                "current_commit": current_commit,
                "latest_version": latest_version,
                "latest_commit": latest_commit,
                "changelog": changelog,
                "commits_behind": commits_count,
            }
        except Exception as e:
            logger.error(f"检查更新失败: {e}")
            return {
                "success": False,
                "has_update": False,
                "error": str(e)
            }

    def create_backup(self, backup_name: Optional[str] = None) -> Optional[str]:
        """
        备份当前项目（前端和后端）
        
        Args:
            backup_name: 备份名称，默认使用时间戳
            
        Returns:
            备份文件名或 None
        """
        try:
            # 获取当前版本
            current_version = self.get_current_version()
            version_str = current_version.get("version", "unknown") if current_version else "unknown"
            
            # 生成备份名称
            if not backup_name:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_name = f"backup_v{version_str}_{timestamp}.zip"
            
            backup_path = self.backup_dir / backup_name
            
            # 创建 ZIP 备份
            logger.info(f"正在创建备份: {backup_path}")
            with zipfile.ZipFile(backup_path, "w", zipfile.ZIP_DEFLATED) as zf:
                # 备份后端代码
                backend_dir = self.project_root / "backend"
                if backend_dir.exists():
                    for file in backend_dir.rglob("*"):
                        if file.is_file() and "__pycache__" not in str(file):
                            arcname = file.relative_to(self.project_root)
                            zf.write(file, arcname)
                
                # 备份前端静态文件
                if self.dist_path.exists():
                    for file in self.dist_path.rglob("*"):
                        if file.is_file():
                            arcname = Path("mofox-webui/dist") / file.relative_to(self.dist_path)
                            zf.write(file, arcname)
                
            # 清理旧备份（保留最近 MAX_BACKUPS 个）
            self._cleanup_old_backups()
            
            logger.info(f"备份完成: {backup_name}")
            return backup_name
            
        except Exception as e:
            logger.error(f"创建备份失败: {e}")
            return None

    def _cleanup_old_backups(self):
        """清理旧备份，只保留最近的 MAX_BACKUPS 个"""
        try:
            backups = sorted(
                self.backup_dir.glob("backup_*.zip"),
                key=lambda p: p.stat().st_mtime,
                reverse=True
            )
            
            for old_backup in backups[MAX_BACKUPS:]:
                logger.info(f"删除旧备份: {old_backup.name}")
                old_backup.unlink()
                
        except Exception as e:
            logger.warning(f"清理旧备份失败: {e}")

    async def download_and_apply(self, use_mirror: bool = False) -> dict:
        """
        使用 Git Pull 下载并应用更新
        
        Args:
            use_mirror: 是否使用镜像源
            
        Returns:
            dict: {"success": bool, "message": str, "version": str, "backup_name": str, "error": str}
        """
        try:
            # 1. 创建备份
            backup_name = self.create_backup()
            logger.info(f"已创建备份: {backup_name}")
            
            # 2. 检查/初始化 Git 仓库
            if not self._is_git_repo():
                success, msg = self._init_git_repo(use_mirror)
                if not success:
                    return {"success": False, "error": msg, "backup_name": backup_name}
            
            # 3. 设置远程 URL（根据是否使用镜像）
            repo_url = f"{MIRROR_URL}{GITHUB_REPO_URL}" if use_mirror else GITHUB_REPO_URL
            self._run_git_command(["remote", "set-url", "origin", repo_url])
            
            # 4. Fetch 远程更新
            success, output = self._run_git_command(["fetch", "origin", GITHUB_BRANCH])
            if not success:
                # 尝试使用镜像
                if not use_mirror:
                    logger.info("尝试使用镜像源...")
                    return await self.download_and_apply(use_mirror=True)
                return {"success": False, "error": f"获取远程更新失败: {output}", "backup_name": backup_name}
            
            # 5. 确保在正确的分支
            success, msg = self._ensure_correct_branch()
            if not success:
                return {"success": False, "error": msg, "backup_name": backup_name}
            
            # 6. 重置本地修改并拉取更新
            # 先暂存本地修改
            self._run_git_command(["stash", "push", "-m", "auto-stash-before-update"])
            
            # 强制重置到远程分支
            success, output = self._run_git_command(["reset", "--hard", f"origin/{GITHUB_BRANCH}"])
            if not success:
                return {"success": False, "error": f"重置失败: {output}", "backup_name": backup_name}
            
            # 7. 获取更新后的版本
            new_version = self.get_current_version()
            version = new_version.get("version", "unknown") if new_version else "unknown"
            
            logger.info(f"更新完成: v{version}")
            return {
                "success": True,
                "message": f"更新成功，已更新到 v{version}",
                "version": version,
                "backup_name": backup_name
            }
            
        except Exception as e:
            logger.error(f"更新失败: {e}")
            return {"success": False, "error": str(e)}

    def list_backups(self) -> List[dict]:
        """
        列出所有备份
        
        Returns:
            备份列表 [{"name": str, "version": str, "timestamp": str, "size": int}]
        """
        backups = []
        
        try:
            for backup_file in sorted(
                self.backup_dir.glob("backup_*.zip"),
                key=lambda p: p.stat().st_mtime,
                reverse=True
            ):
                # 解析备份信息
                name = backup_file.name
                size = backup_file.stat().st_size
                mtime = datetime.fromtimestamp(backup_file.stat().st_mtime)
                
                # 尝试从文件名提取版本
                version = None
                if "_v" in name:
                    try:
                        version = name.split("_v")[1].split("_")[0]
                    except Exception:
                        pass
                
                backups.append({
                    "name": name,
                    "version": version,
                    "timestamp": mtime.isoformat(),
                    "size": size
                })
        except Exception as e:
            logger.error(f"列出备份失败: {e}")
        
        return backups

    def rollback(self, backup_name: str) -> dict:
        """
        回滚到指定备份
        
        Args:
            backup_name: 备份文件名
            
        Returns:
            dict: {"success": bool, "message": str, "error": str}
        """
        backup_path = self.backup_dir / backup_name
        
        if not backup_path.exists():
            return {"success": False, "error": f"备份不存在: {backup_name}"}
        
        try:
            # 1. 先备份当前版本
            current_backup = self.create_backup(f"before_rollback_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip")
            
            # 2. 解压备份
            logger.info(f"正在恢复备份: {backup_name}")
            with zipfile.ZipFile(backup_path, "r") as zf:
                # 获取备份中的文件列表
                namelist = zf.namelist()
                
                # 恢复后端代码
                for name in namelist:
                    if name.startswith("backend/"):
                        target = self.project_root / name
                        target.parent.mkdir(parents=True, exist_ok=True)
                        with open(target, "wb") as f:
                            f.write(zf.read(name))
                
                # 恢复前端静态文件
                for name in namelist:
                    if name.startswith("mofox-webui/dist/"):
                        relative_path = name[len("mofox-webui/dist/"):]
                        if relative_path:
                            target = self.dist_path / relative_path
                            target.parent.mkdir(parents=True, exist_ok=True)
                            with open(target, "wb") as f:
                                f.write(zf.read(name))
            
            # 获取恢复后的版本
            restored_version = self.get_current_version()
            version_str = restored_version.get("version", "unknown") if restored_version else "unknown"
            
            logger.info(f"回滚完成: {backup_name} -> v{version_str}")
            return {
                "success": True,
                "message": f"已恢复到备份版本 v{version_str}",
                "version": version_str
            }
            
        except Exception as e:
            logger.error(f"回滚失败: {e}")
            return {"success": False, "error": str(e)}
    
    async def git_pull_update(self, use_mirror: bool = False) -> dict:
        """
        直接使用 Git Pull 更新（简化接口）
        
        Args:
            use_mirror: 是否使用镜像源
            
        Returns:
            dict: {"success": bool, "message": str, "version": str, "error": str}
        """
        return await self.download_and_apply(use_mirror)
