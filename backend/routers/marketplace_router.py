"""
插件市场路由组件
提供插件市场浏览、搜索、下载、安装等API接口
"""

import tempfile
import zipfile
from pathlib import Path
from typing import Optional

import httpx
from pydantic import BaseModel

from src.common.logger import get_logger
from src.common.security import VerifiedDep
from src.plugin_system import BaseRouterComponent
from src.plugin_system.apis import plugin_info_api, plugin_manage_api

logger = get_logger("WebUI.MarketplaceRouter")


# ==================== 常量配置 ====================

# 插件仓库数据 URL
PLUGIN_REPO_URL = "https://cdn.jsdelivr.net/gh/MoFox-Studio/MoFox-Plugin-Repo@main/plugin_details.json"

# 插件安装目录
PLUGINS_DIR = Path("plugins")


# ==================== 请求/响应模型 ====================


class InstallPluginRequest(BaseModel):
    """安装插件请求"""

    plugin_id: str
    repository_url: str
    auto_load: bool = True  # 默认自动加载


class MarketplaceListResponse(BaseModel):
    """插件市场列表响应"""

    success: bool
    data: Optional[dict] = None
    error: Optional[str] = None


class PluginDetailResponse(BaseModel):
    """插件详情响应"""

    success: bool
    data: Optional[dict] = None
    error: Optional[str] = None


class InstallPluginResponse(BaseModel):
    """安装插件响应"""

    success: bool
    message: str
    plugin_name: Optional[str] = None
    loaded: bool = False


class UpdatePluginResponse(BaseModel):
    """更新插件响应"""

    success: bool
    message: str


class CheckUpdatesResponse(BaseModel):
    """检查更新响应"""

    success: bool
    data: dict | None = None
    error: str | None = None


# ==================== 路由组件 ====================


class MarketplaceRouterComponent(BaseRouterComponent):
    """插件市场路由组件"""

    component_name = "marketplace"
    component_description = "插件市场接口"

    def register_endpoints(self) -> None:
        """注册所有HTTP端点"""

        @self.router.get("/list", response_model=MarketplaceListResponse)
        async def get_marketplace_plugins(_ = VerifiedDep):
            """获取插件市场列表"""
            try:
                # 从 GitHub 获取插件列表
                async with httpx.AsyncClient() as client:
                    response = await client.get(PLUGIN_REPO_URL, timeout=10.0)
                    response.raise_for_status()
                    plugins = response.json()

                # 获取已安装插件列表 (Mapping: repo_name -> real_plugin_name)
                installed_plugins = {}
                
                from src.plugin_system.core.plugin_manager import plugin_manager

                # 获取所有已加载插件的路径映射 {path: name}
                loaded_paths = {}
                try:
                    for name in plugin_manager.list_loaded_plugins():
                        path = plugin_manager.get_plugin_path(name)
                        if path:
                            try:
                                # Normalize path for comparison
                                loaded_paths[str(Path(path).resolve())] = name
                            except Exception:
                                pass
                except Exception as e:
                    logger.warning(f"获取已加载插件路径失败: {e}")

                # 检查本地插件目录
                if PLUGINS_DIR.exists():
                    for plugin_dir in PLUGINS_DIR.iterdir():
                        if plugin_dir.is_dir() and (plugin_dir / "__init__.py").exists():
                            repo_name = plugin_dir.name
                            real_name = None
                            
                            # Try to find if this dir is loaded
                            try:
                                dir_abs_path = str(plugin_dir.resolve())
                                if dir_abs_path in loaded_paths:
                                    real_name = loaded_paths[dir_abs_path]
                            except Exception:
                                pass
                                
                            installed_plugins[repo_name] = real_name
                            
                    logger.info(f"已安装的插件: {list(installed_plugins.keys())}")

                return MarketplaceListResponse(
                    success=True, data={"plugins": plugins, "installed_plugins": installed_plugins}
                )
            except Exception as e:
                logger.error(f"获取插件市场数据失败: {e}")
                return MarketplaceListResponse(success=False, error=f"获取插件市场数据失败: {str(e)}")

        @self.router.get("/detail/{plugin_id}", response_model=PluginDetailResponse)
        async def get_plugin_detail(plugin_id: str, _= VerifiedDep):
            """获取插件详情"""
            try:
                # 获取插件列表
                async with httpx.AsyncClient() as client:
                    response = await client.get(PLUGIN_REPO_URL, timeout=10.0)
                    response.raise_for_status()
                    plugins = response.json()

                # 查找指定插件
                plugin = next((p for p in plugins if p["id"] == plugin_id), None)
                if not plugin:
                    return PluginDetailResponse(success=False, error="插件不存在")

                # 获取仓库地址并提取仓库名作为插件目录名
                repo_url = plugin["manifest"]["repository_url"]
                plugin_name = repo_url.rstrip("/").split("/")[-1]

                # 检查是否已安装
                plugin_dir = PLUGINS_DIR / plugin_name
                is_installed = plugin_dir.exists()

                # 获取 README (从 GitHub 或本地)
                readme = None
                    # 从 GitHub 获取 README
                try:
                        async with httpx.AsyncClient() as client:
                            # 构建 README 的 raw URL
                            readme_url = f"{repo_url.replace('github.com', 'raw.githubusercontent.com')}/main/README.md"
                            response = await client.get(readme_url, timeout=5.0)
                            if response.status_code == 200:
                                readme = response.text
                except Exception as e:
                        logger.warning(f"无法获取 README: {e}")

                # 获取真实的插件名称（通过路径映射）
                real_plugin_name = None
                if is_installed:
                    from src.plugin_system.core.plugin_manager import plugin_manager
                    
                    try:
                        plugin_dir_abs = str(plugin_dir.resolve())
                        for name in plugin_manager.list_loaded_plugins():
                            path = plugin_manager.get_plugin_path(name)
                            if path:
                                try:
                                    if str(Path(path).resolve()) == plugin_dir_abs:
                                        real_plugin_name = name
                                        break
                                except Exception:
                                    continue
                    except Exception as e:
                        logger.warning(f"获取真实插件名失败: {e}")

                # 获取已安装版本
                installed_version = None
                if is_installed and real_plugin_name:
                    plugin_details = plugin_info_api.get_plugin_details(real_plugin_name)
                    if plugin_details:
                        installed_version = plugin_details.get("version", "unknown")

                return PluginDetailResponse(
                    success=True,
                    data={
                        "plugin": plugin,
                        "is_installed": is_installed,
                        "installed_version": installed_version,
                        "readme": readme,
                    },
                )
            except Exception as e:
                logger.error(f"获取插件详情失败: {e}")
                return PluginDetailResponse(success=False, error=f"获取插件详情失败: {str(e)}")

        @self.router.post("/install", response_model=InstallPluginResponse)
        async def install_plugin(request: InstallPluginRequest, _= VerifiedDep):
            """安装插件（下载 ZIP 并解压）"""
            try:
                # 从仓库 URL 提取仓库名作为插件文件夹名
                repo_url = request.repository_url
                repo_name = repo_url.rstrip("/").split("/")[-1]
                target_plugin_path = PLUGINS_DIR / repo_name

                # 检查是否已安装
                if target_plugin_path.exists():
                    return InstallPluginResponse(
                        success=False,
                        message=f"插件 {repo_name} 已安装",
                        plugin_name=repo_name
                    )

                # 确保插件目录存在
                PLUGINS_DIR.mkdir(parents=True, exist_ok=True)

                # 下载 ZIP 文件
                zip_url = f"{repo_url}/archive/refs/heads/main.zip"
                logger.info(f"正在下载插件: {zip_url}")

                async with httpx.AsyncClient() as client:
                    response = await client.get(zip_url, timeout=30.0, follow_redirects=True)
                    response.raise_for_status()

                    # 保存到临时文件
                    with tempfile.NamedTemporaryFile(suffix=".zip", delete=False) as temp_file:
                        temp_file.write(response.content)
                        temp_zip_path = temp_file.name

                try:
                    # 解压 ZIP 文件
                    with zipfile.ZipFile(temp_zip_path, "r") as zip_ref:
                        # 创建临时解压目录
                        with tempfile.TemporaryDirectory() as temp_dir:
                            zip_ref.extractall(temp_dir)

                            # GitHub ZIP 会创建一个带 -main 后缀的目录
                            extracted_dirs = list(Path(temp_dir).iterdir())
                            if not extracted_dirs:
                                return InstallPluginResponse(success=False, message="ZIP 文件为空")

                            source_dir = extracted_dirs[0]

                            # 递归查找包含 plugin.py 的目录（插件根目录）
                            def find_plugin_root(directory: Path) -> Path | None:
                                """查找包含 plugin.py 的目录"""
                                if (directory / "plugin.py").exists():
                                    return directory

                                for subdir in directory.iterdir():
                                    if subdir.is_dir():
                                        result = find_plugin_root(subdir)
                                        if result:
                                            return result
                                return None

                            plugin_root = find_plugin_root(source_dir)

                            if not plugin_root:
                                # 如果没有 plugin.py，尝试查找 __init__.py
                                if (source_dir / "__init__.py").exists():
                                    plugin_root = source_dir
                                else:
                                    # 查找子目录中的 __init__.py
                                    plugin_subdirs = [
                                        d for d in source_dir.iterdir()
                                        if d.is_dir() and (d / "__init__.py").exists()
                                    ]
                                    if plugin_subdirs:
                                        plugin_root = plugin_subdirs[0]

                            if not plugin_root:
                                return InstallPluginResponse(
                                    success=False,
                                    message="无效的插件结构：找不到 plugin.py 或 __init__.py"
                                )

                            # 找到插件根目录
                            logger.info(f"找到插件根目录: {plugin_root}")

                            # 将插件根目录的内容复制到目标位置（使用仓库名作为文件夹名）
                            import shutil
                            shutil.copytree(plugin_root, target_plugin_path)

                    # 验证安装
                    if not (target_plugin_path / "__init__.py").exists():
                        import shutil

                        shutil.rmtree(target_plugin_path)
                        return InstallPluginResponse(success=False, message="插件安装失败：缺少 __init__.py")

                    logger.info(f"插件 {repo_name} 安装成功到 {target_plugin_path}")

                    # 自动加载插件（如果启用）
                    loaded = False
                    load_error = None
                    real_plugin_name = None

                    if request.auto_load:
                        try:
                            # 重新扫描插件目录以注册新安装的插件
                            logger.info("重新扫描插件目录...")
                            success_count, fail_count = plugin_manage_api.rescan_and_register_plugins(
                                load_after_register=True
                            )
                            logger.info(f"扫描完成: 成功 {success_count}, 失败 {fail_count}")

                            # 检查插件是否已加载（使用路径比较）
                            from src.plugin_system.core.plugin_manager import plugin_manager
                            
                            target_abs_path = str(target_plugin_path.resolve())
                            
                            # 遍历所有已加载插件，比较路径
                            for name in plugin_manager.list_loaded_plugins():
                                path = plugin_manager.get_plugin_path(name)
                                if path:
                                    try:
                                        if str(Path(path).resolve()) == target_abs_path:
                                            loaded = True
                                            real_plugin_name = name
                                            logger.info(f"插件 {repo_name} 已自动加载为 {real_plugin_name}")
                                            break
                                    except Exception:
                                        continue

                            if not loaded:
                                # 降级检查：使用名称比较（不区分大小写）
                                loaded_plugins = [p.lower() for p in plugin_manager.list_loaded_plugins()]
                                if repo_name.lower() in loaded_plugins:
                                    loaded = True
                                    real_plugin_name = repo_name # 假设名称一致
                                    logger.info(f"插件 {repo_name} 已自动加载 (通过名称匹配)")
                                else:
                                    load_error = "插件扫描成功但未能加载"
                                    logger.warning(
                                        f"插件 {repo_name} 未在已加载列表中。"
                                        f"已加载插件: {plugin_manager.list_loaded_plugins()}"
                                    )
                        except Exception as e:
                            logger.warning(f"自动加载插件失败: {e}")
                            load_error = str(e)

                    message = f"插件 {repo_name} 安装成功"
                    if loaded:
                        message += f"并已加载 ({real_plugin_name})" if real_plugin_name else "并已加载"
                    elif request.auto_load:
                        message += f"，但加载失败：{load_error}"

                    return InstallPluginResponse(
                        success=True, 
                        message=message, 
                        plugin_name=real_plugin_name if real_plugin_name else repo_name, 
                        loaded=loaded
                    )

                finally:
                    # 清理临时文件
                    Path(temp_zip_path).unlink(missing_ok=True)

            except Exception as e:
                logger.error(f"安装插件失败: {e}")
                # 清理临时文件
                Path(temp_zip_path).unlink(missing_ok=True)
                return InstallPluginResponse(success=False, message=f"安装插件失败: {e!s}")

        @self.router.post("/update/{plugin_id}", response_model=UpdatePluginResponse)
        async def update_plugin(plugin_id: str, _= VerifiedDep):
            """更新插件（重新下载并覆盖）"""
            try:
                # 从插件列表获取仓库 URL
                async with httpx.AsyncClient() as client:
                    response = await client.get(PLUGIN_REPO_URL, timeout=10.0)
                    response.raise_for_status()
                    plugins = response.json()

                plugin = next((p for p in plugins if p["id"] == plugin_id), None)
                if not plugin:
                    return UpdatePluginResponse(success=False, message="插件不存在")

                # 从仓库 URL 提取仓库名作为插件目录名
                repo_url = plugin["manifest"]["repository_url"]
                plugin_name = repo_url.rstrip("/").split("/")[-1]
                plugin_path = PLUGINS_DIR / plugin_name

                if not plugin_path.exists():
                    return UpdatePluginResponse(success=False, message="插件未安装")

                # 备份当前插件
                import shutil

                backup_path = plugin_path.with_suffix(".backup")
                if backup_path.exists():
                    shutil.rmtree(backup_path)
                shutil.copytree(plugin_path, backup_path)

                try:
                    # 删除当前插件
                    shutil.rmtree(plugin_path)

                    # 重新安装
                    install_request = InstallPluginRequest(plugin_id=plugin_id, repository_url=repo_url)
                    result = await install_plugin(install_request, _)

                    if result.success:
                        # 删除备份
                        shutil.rmtree(backup_path)
                        return UpdatePluginResponse(success=True, message=f"插件 {plugin_name} 更新成功")
                    else:
                        # 恢复备份
                        if backup_path.exists():
                            if plugin_path.exists():
                                shutil.rmtree(plugin_path)
                            shutil.copytree(backup_path, plugin_path)
                            shutil.rmtree(backup_path)
                        return UpdatePluginResponse(success=False, message=f"更新失败: {result.message}")

                except Exception as e:
                    # 恢复备份
                    if backup_path.exists():
                        if plugin_path.exists():
                            shutil.rmtree(plugin_path)
                        shutil.copytree(backup_path, plugin_path)
                        shutil.rmtree(backup_path)
                    raise e

            except Exception as e:
                logger.error(f"更新插件失败: {e}")
                return UpdatePluginResponse(success=False, message=f"更新插件失败: {e!s}")

        @self.router.get("/check-updates", response_model=CheckUpdatesResponse)
        async def check_plugin_updates(_=VerifiedDep):
            """检查插件更新"""
            try:
                # 获取远程插件列表
                async with httpx.AsyncClient() as client:
                    response = await client.get(PLUGIN_REPO_URL, timeout=10.0)
                    response.raise_for_status()
                    remote_plugins = response.json()

                updates = []

                # 获取已加载插件的路径映射
                from src.plugin_system.core.plugin_manager import plugin_manager
                loaded_paths = {}
                try:
                    for name in plugin_manager.list_loaded_plugins():
                        path = plugin_manager.get_plugin_path(name)
                        if path:
                            try:
                                loaded_paths[str(Path(path).resolve())] = name
                            except Exception:
                                pass
                except Exception as e:
                    logger.warning(f"获取已加载插件路径失败: {e}")

                # 检查已安装的插件
                if PLUGINS_DIR.exists():
                    for plugin_dir in PLUGINS_DIR.iterdir():
                        if not plugin_dir.is_dir() or not (plugin_dir / "__init__.py").exists():
                            continue

                        # plugin_dir.name 是仓库名
                        repo_name = plugin_dir.name

                        # 找到真实的插件名称
                        real_plugin_name = None
                        try:
                            dir_abs_path = str(plugin_dir.resolve())
                            real_plugin_name = loaded_paths.get(dir_abs_path)
                        except Exception:
                            pass

                        if not real_plugin_name:
                            continue

                        # 获取本地版本
                        plugin_details = plugin_info_api.get_plugin_details(real_plugin_name)
                        if not plugin_details:
                            continue

                        current_version = plugin_details.get("version", "unknown")

                        # 查找远程版本（通过仓库名匹配）
                        remote_plugin = next(
                            (p for p in remote_plugins 
                             if p["manifest"]["repository_url"].rstrip("/").split("/")[-1] == repo_name), 
                            None
                        )

                        if remote_plugin:
                            latest_version = remote_plugin["manifest"].get("version", "unknown")

                            # 简单的版本比较（可以使用 packaging.version 做更精确的比较）
                            if current_version != latest_version:
                                updates.append(
                                    {
                                        "plugin_id": remote_plugin["id"],
                                        "plugin_name": repo_name,
                                        "current_version": current_version,
                                        "latest_version": latest_version,
                                    }
                                )

                return CheckUpdatesResponse(success=True, data={"updates": updates})
            except Exception as e:
                logger.error(f"检查更新失败: {e}")
                return CheckUpdatesResponse(success=False, error=f"检查更新失败: {e!s}")
