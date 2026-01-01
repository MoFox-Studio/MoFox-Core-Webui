"""
Git 更新管理器
提供 Git 仓库检查更新、拉取更新、回滚等功能
"""

import subprocess
from pathlib import Path
from typing import Optional

from src.common.logger import get_logger

from .git_detector import GitDetector
from .venv_utils import VenvDetector, DependencyInstaller

logger = get_logger("WebUI.GitUpdater")


class GitUpdater:
    """Git 更新管理器"""

    def __init__(self, repo_path: Path, branch: str | None = None):
        self.repo_path = repo_path
        self.git_path = GitDetector.get_git_executable()

        if not self.git_path:
            raise RuntimeError("Git 未安装或未找到")
        
        # 如果没有指定分支,自动检测当前分支
        if branch is None:
            self.branch = self._get_current_branch()
        else:
            self.branch = branch

    def _get_current_branch(self) -> str:
        """获取当前 Git 分支"""
        try:
            result = subprocess.run(
                [str(self.git_path), "branch", "--show-current"],
                cwd=str(self.repo_path),
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="ignore",
                timeout=5,
            )
            if result.returncode == 0 and result.stdout.strip():
                branch = result.stdout.strip()
                logger.info(f"检测到当前分支: {branch}")
                return branch
            else:
                logger.warning("无法检测当前分支，使用默认分支 'main'")
                return "main"
        except Exception as e:
            logger.warning(f"检测当前分支失败: {e}，使用默认分支 'main'")
            return "main"

    def _run_git_command(self, *args, **kwargs) -> subprocess.CompletedProcess:
        """运行 Git 命令"""
        cmd = [str(self.git_path)] + [str(arg) for arg in args]
        return subprocess.run(
            cmd,
            cwd=str(self.repo_path),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="ignore",
            **kwargs,
        )

    async def check_updates(self) -> dict:
        """检查是否有更新"""
        try:
            # 获取远程更新
            logger.info("正在从远程仓库获取更新信息...")
            fetch_result = self._run_git_command("fetch", "origin", self.branch, timeout=30)

            if fetch_result.returncode != 0:
                return {"success": False, "error": f"无法连接远程仓库: {fetch_result.stderr}"}

            # 获取本地和远程的 commit hash
            local_result = self._run_git_command("rev-parse", "HEAD")
            remote_result = self._run_git_command("rev-parse", f"origin/{self.branch}")

            if local_result.returncode != 0 or remote_result.returncode != 0:
                return {"success": False, "error": "无法获取版本信息"}

            local_commit = local_result.stdout.strip()
            remote_commit = remote_result.stdout.strip()

            has_update = local_commit != remote_commit

            # 获取落后的提交数
            commits_behind = 0
            if has_update:
                count_result = self._run_git_command(
                    "rev-list", "--count", f"HEAD..origin/{self.branch}"
                )
                if count_result.returncode == 0:
                    commits_behind = int(count_result.stdout.strip())

            # 获取更新日志
            update_logs = []
            if has_update:
                log_result = self._run_git_command(
                    "log", "--oneline", f"HEAD..origin/{self.branch}", "--max-count=10"
                )
                if log_result.returncode == 0:
                    update_logs = [
                        line.strip()
                        for line in log_result.stdout.strip().split("\n")
                        if line.strip()
                    ]

            return {
                "success": True,
                "has_update": has_update,
                "current_commit": local_commit[:8],
                "remote_commit": remote_commit[:8],
                "commits_behind": commits_behind,
                "update_logs": update_logs,
            }

        except subprocess.TimeoutExpired:
            return {"success": False, "error": "检查更新超时"}
        except Exception as e:
            logger.error(f"检查更新失败: {e}")
            return {"success": False, "error": str(e)}

    async def pull_updates(self, force: bool = False, stash_local: bool = True) -> dict:
        """拉取更新"""
        try:
            updated_files = []

            # 检查本地是否有未提交的修改
            status_result = self._run_git_command("status", "--porcelain")
            has_local_changes = bool(status_result.stdout.strip())

            if has_local_changes:
                if not force:
                    return {
                        "success": False,
                        "error": "本地有未提交的修改，请先提交或使用强制更新",
                    }

                if stash_local:
                    logger.info("暂存本地修改...")
                    stash_result = self._run_git_command(
                        "stash", "push", "-m", "Auto stash before update"
                    )
                    if stash_result.returncode != 0:
                        return {
                            "success": False,
                            "error": f"暂存本地修改失败: {stash_result.stderr}",
                        }
                else:
                    logger.info("重置本地修改...")
                    reset_result = self._run_git_command("reset", "--hard", "HEAD")
                    if reset_result.returncode != 0:
                        return {
                            "success": False,
                            "error": f"重置本地修改失败: {reset_result.stderr}",
                        }

            # 拉取更新
            logger.info(f"正在拉取 {self.branch} 分支的最新代码...")
            pull_result = self._run_git_command("pull", "origin", self.branch, timeout=60)

            if pull_result.returncode != 0:
                return {"success": False, "error": f"拉取更新失败: {pull_result.stderr}"}

            # 解析更新的文件
            if "Already up to date" not in pull_result.stdout:
                # 获取更新的文件列表
                diff_result = self._run_git_command("diff", "--name-only", "HEAD@{1}", "HEAD")
                if diff_result.returncode == 0:
                    updated_files = [
                        line.strip()
                        for line in diff_result.stdout.strip().split("\n")
                        if line.strip()
                    ]

            result = {
                "success": True,
                "message": "更新成功" if updated_files else "已是最新版本",
                "updated_files": updated_files,
            }

            # 如果有文件更新，尝试安装依赖
            if updated_files:
                logger.info("检测到文件更新，准备安装依赖...")
                venv_type = VenvDetector.detect_venv_type(self.repo_path)

                if venv_type:
                    logger.info(f"检测到虚拟环境类型: {venv_type}，开始安装依赖...")
                    dep_result = await DependencyInstaller.install_dependencies(
                        self.repo_path, venv_type
                    )

                    result["dependencies_installed"] = dep_result["success"]
                    result["venv_type"] = venv_type

                    if dep_result["success"]:
                        result["dependencies_message"] = dep_result["message"]
                        logger.info("依赖安装成功")
                    else:
                        result["dependencies_message"] = f"依赖安装失败: {dep_result.get('error', '未知错误')}"
                        logger.warning(f"依赖安装失败: {dep_result.get('error')}")
                else:
                    result["dependencies_message"] = "未检测到虚拟环境，跳过依赖安装"
                    logger.warning("未检测到虚拟环境，跳过依赖安装")

            return result

        except subprocess.TimeoutExpired:
            return {"success": False, "error": "更新超时"}
        except Exception as e:
            logger.error(f"更新失败: {e}")
            return {"success": False, "error": str(e)}

    def get_current_commit(self) -> Optional[str]:
        """获取当前 commit hash"""
        result = self._run_git_command("rev-parse", "HEAD")
        if result.returncode == 0:
            return result.stdout.strip()
        return None

    async def rollback(self, commit_hash: str) -> dict:
        """回滚到指定版本"""
        try:
            logger.info(f"正在回滚到版本: {commit_hash}")

            # 重置到指定版本
            reset_result = self._run_git_command("reset", "--hard", commit_hash)

            if reset_result.returncode != 0:
                return {"success": False, "error": f"回滚失败: {reset_result.stderr}"}

            return {"success": True, "message": f"已回滚到版本 {commit_hash[:8]}"}

        except Exception as e:
            logger.error(f"回滚失败: {e}")
            return {"success": False, "error": str(e)}

    def get_branches(self) -> dict:
        """获取所有分支列表"""
        try:
            # 获取远程分支
            fetch_result = self._run_git_command("fetch", "origin", timeout=30)
            if fetch_result.returncode != 0:
                logger.warning(f"获取远程分支失败: {fetch_result.stderr}")

            # 获取本地和远程分支
            result = self._run_git_command("branch", "-a")
            if result.returncode != 0:
                return {"success": False, "error": "获取分支列表失败"}

            branches = []
            current_branch = None
            
            for line in result.stdout.strip().split("\n"):
                line = line.strip()
                if not line:
                    continue
                
                # 当前分支标记为 *
                is_current = line.startswith("*")
                if is_current:
                    line = line[1:].strip()
                    current_branch = line
                
                # 跳过远程HEAD指针
                if "HEAD ->" in line:
                    continue
                
                # 处理远程分支
                if line.startswith("remotes/origin/"):
                    branch_name = line.replace("remotes/origin/", "")
                    if branch_name not in branches:
                        branches.append(branch_name)
                elif line not in branches:
                    branches.append(line)

            return {
                "success": True,
                "branches": sorted(branches),
                "current_branch": current_branch
            }

        except Exception as e:
            logger.error(f"获取分支列表失败: {e}")
            return {"success": False, "error": str(e)}

    async def switch_branch(self, branch: str) -> dict:
        """切换到指定分支"""
        try:
            logger.info(f"正在切换到分支: {branch}")

            # 检查本地是否有未提交的修改
            status_result = self._run_git_command("status", "--porcelain")
            has_local_changes = bool(status_result.stdout.strip())

            if has_local_changes:
                logger.info("暂存本地修改...")
                stash_result = self._run_git_command(
                    "stash", "push", "-m", f"Auto stash before switching to {branch}"
                )
                if stash_result.returncode != 0:
                    return {
                        "success": False,
                        "error": f"暂存本地修改失败: {stash_result.stderr}"
                    }

            # 检查本地是否已有该分支
            branch_result = self._run_git_command("branch", "--list", branch)
            has_local_branch = bool(branch_result.stdout.strip())

            if has_local_branch:
                # 切换到本地分支
                checkout_result = self._run_git_command("checkout", branch)
            else:
                # 从远程创建并切换到分支
                checkout_result = self._run_git_command(
                    "checkout", "-b", branch, f"origin/{branch}"
                )

            if checkout_result.returncode != 0:
                return {
                    "success": False,
                    "error": f"切换分支失败: {checkout_result.stderr}"
                }

            # 拉取最新代码
            pull_result = self._run_git_command("pull", "origin", branch, timeout=60)

            result = {
                "success": True,
                "message": f"已切换到分支 {branch}",
                "current_branch": branch
            }

            # 尝试安装依赖
            venv_type = VenvDetector.detect_venv_type(self.repo_path)
            if venv_type:
                logger.info(f"检测到虚拟环境类型: {venv_type}，开始安装依赖...")
                dep_result = await DependencyInstaller.install_dependencies(
                    self.repo_path, venv_type
                )
                result["dependencies_installed"] = dep_result["success"]
                result["venv_type"] = venv_type
                if dep_result["success"]:
                    result["dependencies_message"] = dep_result["message"]
                else:
                    result["dependencies_message"] = f"依赖安装失败: {dep_result.get('error', '未知错误')}"

            return result

        except Exception as e:
            logger.error(f"切换分支失败: {e}")
            return {"success": False, "error": str(e)}
