"""插件管理路由组件

提供插件管理接口，完全匹配前端 API 期望格式。

API 路径前缀：/webui/api/plugin_manager

前端对应文件：
- forward/mofox-webui/src/api/index.ts (API定义)
- forward/mofox-webui/src/stores/plugin.ts (状态管理)
- forward/mofox-webui/src/views/PluginManageView.vue (页面)
"""

import shutil
from pathlib import Path
from typing import Any

from fastapi import HTTPException
from pydantic import BaseModel, Field

from src.kernel.logger import get_logger
from src.core.components.base.router import BaseRouter
from src.core.utils.security import VerifiedDep
from src.core.managers import get_plugin_manager
from src.core.components.state_manager import get_global_state_manager
from src.core.components.types import ComponentState, ComponentType, build_signature
from src.core.components.loader import get_plugin_loader

logger = get_logger(name="PluginManageRouter", color="cyan")

PLUGINS_DIR = Path("plugins")


# ==================== API Models ====================

class PluginItem(BaseModel):
    """插件项 - 匹配前端 PluginItem 接口"""
    name: str
    display_name: str
    version: str
    author: str
    description: str = ""
    enabled: bool
    loaded: bool
    components_count: int
    last_updated: str | None = None
    config_path: str | None = None
    error: str | None = None
    plugin_type: str | None = None  # "system" 表示系统插件


class PluginManageListResponse(BaseModel):
    """插件管理列表响应 - 匹配前端 PluginManageListResponse 接口"""
    success: bool
    plugins: list[PluginItem]
    failed_plugins: list[PluginItem]
    total: int
    loaded: int
    enabled: int
    failed: int
    error: str | None = None


class PluginComponent(BaseModel):
    """组件项 - 匹配前端 PluginComponent 接口"""
    name: str
    type: str
    description: str = ""
    enabled: bool
    plugin_name: str
    details: dict[str, Any] | None = None


class PluginDetailInfo(BaseModel):
    """插件详细信息 - 匹配前端 PluginDetailInfo 接口"""
    name: str
    display_name: str
    version: str
    author: str
    description: str = ""
    enabled: bool
    loaded: bool
    components: list[PluginComponent]
    components_count: int
    config: dict[str, Any]
    metadata: dict[str, Any] | None = None


class PluginDetailResponse(BaseModel):
    """插件详情响应 - 匹配前端 PluginDetailResponse 接口"""
    success: bool
    plugin: PluginDetailInfo | None = None
    error: str | None = None


class OperationResponse(BaseModel):
    """操作响应 - 匹配前端 OperationResponse 接口"""
    success: bool
    message: str | None = None
    error: str | None = None


class ScanResultResponse(BaseModel):
    """扫描结果响应 - 匹配前端 ScanResultResponse 接口"""
    success: bool
    registered: int = 0
    loaded: int = 0
    failed: int = 0
    new_plugins: list[str] = Field(default_factory=list)
    error: str | None = None


# ==================== Helper Functions ====================

def _convert_to_plugin_item(plugin_name: str, plugin_path: str | None = None) -> PluginItem | None:
    """将插件信息转换为 PluginItem 格式
    
    Args:
        plugin_name: 插件名称
        plugin_path: 插件路径（可选）
        
    Returns:
        PluginItem 对象，如果插件不存在则返回 None
    """
    plugin_manager = get_plugin_manager()
    state_manager = get_global_state_manager()
    
    # 获取 manifest
    manifest = plugin_manager.get_manifest(plugin_name)
    if not manifest:
        return None
    
    # 获取插件状态
    plugin_sig = build_signature(plugin_name, ComponentType.PLUGIN, plugin_name)
    state = state_manager.get_state(plugin_sig)
    
    loaded = plugin_manager.is_plugin_loaded(plugin_name)
    enabled = state == ComponentState.ACTIVE
    
    # 获取插件路径
    if plugin_path is None:
        plugin_path = plugin_manager._plugin_paths.get(plugin_name, "")
    
    # 统计组件数量
    components_count = len(manifest.include) if manifest.include else 0
    
    # 获取配置路径
    config_path = str(Path(f"config/plugins/{plugin_name}/config.toml"))
    
    return PluginItem(
        name=plugin_name,
        display_name=manifest.name,
        version=manifest.version,
        description=manifest.description or "",
        author=manifest.author,
        loaded=loaded,
        enabled=enabled,
        components_count=components_count,
        config_path=config_path,
        plugin_type=None,  # TODO: 从 manifest 或其他地方获取
    )


def _get_all_plugin_paths() -> dict[str, str]:
    """获取所有插件路径（包括未加载的）
    
    Returns:
        插件名称到路径的映射
    """
    result: dict[str, str] = {}
    
    if not PLUGINS_DIR.exists():
        return result
    
    for item in PLUGINS_DIR.iterdir():
        # 跳过隐藏文件和 __pycache__
        if item.name.startswith('.') or item.name == '__pycache__':
            continue
        
        # 文件夹插件
        if item.is_dir():
            manifest_path = item / "manifest.json"
            if manifest_path.exists():
                result[item.name] = str(item)
        # ZIP/MFP 插件
        elif item.suffix in ['.zip', '.mfp']:
            plugin_name = item.stem
            result[plugin_name] = str(item)
    
    return result


# ==================== Router ====================

class PluginManageRouter(BaseRouter):
    """插件管理路由组件
    
    提供与前端完全匹配的 API 端点，支持插件的完整生命周期管理。
    
    API 端点列表：
    
    **插件查询接口**
    - GET  /plugins
      获取所有插件列表（包括已加载和失败的插件）
      返回：插件列表、失败列表、统计信息（总数、已加载、已启用、失败数）
      前端对应：getPluginList() in api/index.ts
    
    - GET  /plugins/{plugin_name}
      获取指定插件的详细信息
      返回：插件基本信息、组件列表、配置信息
      前端对应：getPluginDetail() in api/index.ts
    
    **插件生命周期管理**
    - POST /plugins/{plugin_name}/load
      加载指定插件（从文件系统导入并初始化）
      使用场景：首次加载插件或重新加载已卸载的插件
      前端对应：loadPlugin() in api/index.ts
    
    - POST /plugins/{plugin_name}/unload
      卸载指定插件（从内存中移除，但保留文件）
      使用场景：临时停用插件但不删除
      前端对应：unloadPlugin() in api/index.ts
    
    - POST /plugins/{plugin_name}/reload
      重载指定插件（卸载后重新加载）
      使用场景：代码更新后刷新插件
      前端对应：reloadPlugin() in api/index.ts
    
    **插件状态控制**
    - POST /plugins/{plugin_name}/enable
      启用插件（设置为 ACTIVE 状态，允许执行）
      注意：插件必须已加载才能启用
      前端对应：enablePlugin() in api/index.ts
    
    - POST /plugins/{plugin_name}/disable
      禁用插件（设置为 INACTIVE 状态，阻止执行）
      注意：不会卸载插件，只是停止其功能
      前端对应：disablePlugin() in api/index.ts
    
    **插件文件管理**
    - DELETE /plugins/{plugin_name}/delete
      删除插件（物理删除文件/目录）
      警告：此操作不可撤销，会删除插件的所有文件
      如果插件已加载，会先自动卸载
      前端对应：deletePlugin() in api/index.ts
    
    **批量操作**
    - POST /plugins/scan
      扫描插件目录，发现并加载新插件
      返回：注册数量、成功加载数量、失败数量、新插件列表
      使用场景：添加新插件后刷新列表
      前端对应：scanPlugins() in api/index.ts
    
    - POST /plugins/reload-all
      重载所有已加载的插件
      返回：成功数量、失败数量
      使用场景：批量更新插件或系统维护
      前端对应：reloadAllPlugins() in api/index.ts
    
    **配置说明**
    - 配置文件路径格式：plugins/{plugin_name}/config.toml
    - 所有端点都需要通过 VerifiedDep 进行身份验证
    - 响应格式统一使用 Pydantic 模型，保证类型安全
    - 需要在请求头中携带有效的 X-API-Key
    
    错误处理：
    - 成功：success=True, message 包含操作结果
    - 失败：success=False, error 包含错误详情
    
    Examples:
        >>> # 获取插件列表
        >>> GET /webui/api/plugin_manager/plugins
        >>> 
        >>> # 启用插件
        >>> POST /webui/api/plugin_manager/plugins/my_plugin/enable
        >>> 
        >>> # 扫描新插件
        >>> POST /webui/api/plugin_manager/plugins/scan
    """
    
    router_name = "PluginManageRouter"
    router_description = "插件管理接口"
    
    custom_route_path = "/webui/api/plugin_manager"
    cors_origins = ["*"]
    
    def register_endpoints(self) -> None:
        """注册所有 HTTP 端点"""
        
        @self.app.get("/plugins", summary="获取所有插件列表", response_model=PluginManageListResponse)
        async def get_plugin_list(_=VerifiedDep):
            """获取所有插件列表
            
            返回系统中所有插件的状态信息，包括：
            - 已成功加载的插件（含启用/禁用状态）
            - 加载失败的插件（含失败原因）
            - 统计信息：总数、已加载、已启用、失败数量
            
            响应格式：
            ```json
            {
                "success": true,
                "plugins": [...],
                "failed_plugins": [...],
                "total": 10,
                "loaded": 8,
                "enabled": 6,
                "failed": 2
            }
            ```
            
            前端对应：
            - getPluginList() in api/index.ts
            - fetchPlugins() in stores/plugin.ts
            """
            try:
                plugin_manager = get_plugin_manager()
                
                plugins: list[PluginItem] = []
                failed_plugins: list[PluginItem] = []
                
                # 获取所有已加载插件
                loaded_plugin_names = plugin_manager.list_loaded_plugins()
                for plugin_name in loaded_plugin_names:
                    item = _convert_to_plugin_item(plugin_name)
                    if item:
                        plugins.append(item)
                
                # 获取失败插件（来自 manager）
                failed_from_manager = plugin_manager._failed_plugins
                for plugin_name, error in failed_from_manager.items():
                    plugin_path = plugin_manager._plugin_paths.get(plugin_name, "")
                    
                    # 尝试获取基本信息
                    item = _convert_to_plugin_item(plugin_name, plugin_path)
                    if item:
                        item.error = error
                        failed_plugins.append(item)
                    else:
                        # 无法获取manifest，创建最小信息
                        failed_plugins.append(PluginItem(
                            name=plugin_name,
                            display_name=plugin_name,
                            version="unknown",
                            description="",
                            author="unknown",
                            loaded=False,
                            enabled=False,
                            components_count=0,
                            error=error,
                        ))
                
                # 统计信息
                total_count = len(plugins) + len(failed_plugins)
                loaded_count = len([p for p in plugins if p.loaded])
                enabled_count = len([p for p in plugins if p.enabled])
                failed_count = len(failed_plugins)
                
                return PluginManageListResponse(
                    success=True,
                    plugins=plugins,
                    failed_plugins=failed_plugins,
                    total=total_count,
                    loaded=loaded_count,
                    enabled=enabled_count,
                    failed=failed_count,
                )
                
            except Exception as e:
                logger.error(f"获取插件列表失败: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/plugins/{plugin_name}", summary="获取插件详情", response_model=PluginDetailResponse)
        async def get_plugin_detail(plugin_name: str, _=VerifiedDep):
            """获取指定插件的详细信息
            
            Args:
                plugin_name: 插件名称
            
            返回内容：
            - 插件基本信息（名称、版本、作者、描述等）
            - 组件列表（包含组件类型、名称、状态）
            - 配置信息（配置路径、是否存在）
            
            注意：
            - 插件必须已加载才能获取详情
            - 未加载的插件返回 success=False
            
            前端对应：
            - getPluginDetail() in api/index.ts
            - fetchPluginDetail() in stores/plugin.ts
            """
            try:
                plugin_manager = get_plugin_manager()
                
                # 检查插件是否已加载
                if not plugin_manager.is_plugin_loaded(plugin_name):
                    return PluginDetailResponse(
                        success=False,
                        error=f"插件 '{plugin_name}' 未加载"
                    )
                
                # 获取基本信息
                base_item = _convert_to_plugin_item(plugin_name)
                if not base_item:
                    return PluginDetailResponse(
                        success=False,
                        error=f"无法获取插件 '{plugin_name}' 的信息"
                    )
                
                # 获取组件信息
                components: list[PluginComponent] = []
                manifest = plugin_manager.get_manifest(plugin_name)
                state_manager = get_global_state_manager()
                
                if manifest and manifest.include:
                    for comp_include in manifest.include:
                        comp_sig = build_signature(
                            plugin_name,
                            ComponentType(comp_include.component_type),
                            comp_include.component_name
                        )
                        
                        comp_state = state_manager.get_state(comp_sig)
                        
                        components.append(PluginComponent(
                            name=comp_include.component_name,
                            type=comp_include.component_type,
                            description="",
                            enabled=comp_state == ComponentState.ACTIVE,
                            plugin_name=plugin_name,
                        ))
                
                # 构建详情信息
                detail_info = PluginDetailInfo(
                    name=base_item.name,
                    display_name=base_item.display_name,
                    version=base_item.version,
                    author=base_item.author,
                    description=base_item.description,
                    enabled=base_item.enabled,
                    loaded=base_item.loaded,
                    components=components,
                    components_count=len(components),
                    config={
                        "path": base_item.config_path or "",
                        "exists": Path(base_item.config_path or "").exists() if base_item.config_path else False,
                    },
                )
                
                return PluginDetailResponse(
                    success=True,
                    plugin=detail_info,
                )
                
            except Exception as e:
                logger.error(f"获取插件详情失败: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.post("/plugins/{plugin_name}/enable", summary="启用插件", response_model=OperationResponse)
        async def enable_plugin(plugin_name: str, _=VerifiedDep):
            """启用指定插件
            
            Args:
                plugin_name: 插件名称
            
            功能说明：
            - 将插件状态设置为 ACTIVE（激活）
            - 同时启用插件包含的所有组件
            - 启用后插件可以正常执行功能
            
            前置条件：
            - 插件必须已经加载（loaded=True）
            - 未加载的插件无法启用
            
            使用场景：
            - 重新激活被禁用的插件
            - 首次加载后启用插件
            
            前端对应：
            - enablePlugin() in api/index.ts
            - enablePluginAction() in stores/plugin.ts
            """
            try:
                plugin_manager = get_plugin_manager()
                state_manager = get_global_state_manager()
                
                # 检查是否已加载
                if not plugin_manager.is_plugin_loaded(plugin_name):
                    return OperationResponse(
                        success=False,
                        error=f"插件 '{plugin_name}' 未加载，无法启用"
                    )
                
                # 更新状态为 ACTIVE
                plugin_sig = build_signature(plugin_name, ComponentType.PLUGIN, plugin_name)
                await state_manager.set_state_async(plugin_sig, ComponentState.ACTIVE)
                
                # 同时启用插件的所有组件
                manifest = plugin_manager.get_manifest(plugin_name)
                if manifest and manifest.include:
                    for comp_include in manifest.include:
                        comp_sig = build_signature(
                            plugin_name,
                            ComponentType(comp_include.component_type),
                            comp_include.component_name
                        )
                        await state_manager.set_state_async(comp_sig, ComponentState.ACTIVE)
                
                return OperationResponse(
                    success=True,
                    message=f"插件 '{plugin_name}' 已启用"
                )
                
            except Exception as e:
                logger.error(f"启用插件失败: {e}")
                return OperationResponse(
                    success=False,
                    error=str(e)
                )
        
        @self.app.post("/plugins/{plugin_name}/disable", summary="禁用插件", response_model=OperationResponse)
        async def disable_plugin(plugin_name: str, _=VerifiedDep):
            """禁用指定插件
            
            Args:
                plugin_name: 插件名称
            
            功能说明：
            - 将插件状态设置为 INACTIVE（非激活）
            - 同时禁用插件包含的所有组件
            - 禁用后插件不会执行功能，但仍保留在内存中
            
            注意事项：
            - 禁用不等于卸载，不会释放内存
            - 禁用后可以随时重新启用
            - 适合临时停用插件而不删除
            
            使用场景：
            - 临时停用某个功能
            - 调试时排除特定插件影响
            - 避免插件冲突
            
            前端对应：
            - disablePlugin() in api/index.ts
            - disablePluginAction() in stores/plugin.ts
            """
            try:
                plugin_manager = get_plugin_manager()
                state_manager = get_global_state_manager()
                
                # 检查是否已加载
                if not plugin_manager.is_plugin_loaded(plugin_name):
                    return OperationResponse(
                        success=False,
                        error=f"插件 '{plugin_name}' 未加载"
                    )
                
                # 更新状态为 INACTIVE
                plugin_sig = build_signature(plugin_name, ComponentType.PLUGIN, plugin_name)
                await state_manager.set_state_async(plugin_sig, ComponentState.INACTIVE)
                
                # 同时禁用插件的所有组件
                manifest = plugin_manager.get_manifest(plugin_name)
                if manifest and manifest.include:
                    for comp_include in manifest.include:
                        comp_sig = build_signature(
                            plugin_name,
                            ComponentType(comp_include.component_type),
                            comp_include.component_name
                        )
                        await state_manager.set_state_async(comp_sig, ComponentState.INACTIVE)
                
                return OperationResponse(
                    success=True,
                    message=f"插件 '{plugin_name}' 已禁用"
                )
                
            except Exception as e:
                logger.error(f"禁用插件失败: {e}")
                return OperationResponse(
                    success=False,
                    error=str(e)
                )
        
        @self.app.post("/plugins/{plugin_name}/reload", summary="重载插件", response_model=OperationResponse)
        async def reload_plugin(plugin_name: str, _=VerifiedDep):
            """重载指定插件
            
            Args:
                plugin_name: 插件名称
            
            功能说明：
            - 卸载插件（清理内存和资源）
            - 重新加载插件（重新导入代码）
            - 恢复原有的启用/禁用状态
            
            前置条件：
            - 插件必须已经加载
            - 未加载的插件无法重载
            
            使用场景：
            - 插件代码更新后刷新
            - 修复插件运行时错误
            - 重置插件状态
            
            注意事项：
            - 重载会中断插件正在执行的任务
            - 插件配置会重新读取
            - 可能导致短暂的服务中断
            
            前端对应：
            - reloadPlugin() in api/index.ts
            - reloadPluginAction() in stores/plugin.ts
            """
            try:
                plugin_manager = get_plugin_manager()
                
                # 检查是否已加载
                if not plugin_manager.is_plugin_loaded(plugin_name):
                    return OperationResponse(
                        success=False,
                        error=f"插件 '{plugin_name}' 未加载，无法重载"
                    )
                
                # 重载插件
                success = await plugin_manager.reload_plugin(plugin_name)
                
                if success:
                    return OperationResponse(
                        success=True,
                        message=f"插件 '{plugin_name}' 重载成功"
                    )
                else:
                    error = plugin_manager._failed_plugins.get(plugin_name, "未知错误")
                    return OperationResponse(
                        success=False,
                        error=error
                    )
                    
            except Exception as e:
                logger.error(f"重载插件失败: {e}")
                return OperationResponse(
                    success=False,
                    error=str(e)
                )
        
        @self.app.post("/plugins/{plugin_name}/unload", summary="卸载插件", response_model=OperationResponse)
        async def unload_plugin(plugin_name: str, _=VerifiedDep):
            """卸载指定插件
            
            Args:
                plugin_name: 插件名称
            
            功能说明：
            - 从内存中完全移除插件
            - 清理插件使用的所有资源
            - 注销插件的所有组件
            - 清理 sys.modules 中的模块引用
            
            注意事项：
            - 不会删除插件文件（保留在 plugins 目录）
            - 卸载后可以重新加载
            - 会调用插件的 on_plugin_unloaded 钩子
            
            使用场景：
            - 释放不常用插件的内存
            - 准备删除插件前先卸载
            - 解决插件加载错误
            
            前端对应：
            - unloadPlugin() in api/index.ts
            - unloadPluginAction() in stores/plugin.ts
            """
            try:
                plugin_manager = get_plugin_manager()
                
                # 检查是否已加载
                if not plugin_manager.is_plugin_loaded(plugin_name):
                    return OperationResponse(
                        success=False,
                        error=f"插件 '{plugin_name}' 未加载"
                    )
                
                # 卸载插件
                success = await plugin_manager.unload_plugin(plugin_name)
                
                if success:
                    return OperationResponse(
                        success=True,
                        message=f"插件 '{plugin_name}' 卸载成功"
                    )
                else:
                    return OperationResponse(
                        success=False,
                        error=f"插件 '{plugin_name}' 卸载失败"
                    )
                    
            except Exception as e:
                logger.error(f"卸载插件失败: {e}")
                return OperationResponse(
                    success=False,
                    error=str(e)
                )
        
        @self.app.delete("/plugins/{plugin_name}/delete", summary="删除插件", response_model=OperationResponse)
        async def delete_plugin(plugin_name: str, _=VerifiedDep):
            """删除指定插件（物理删除文件）
            
            Args:
                plugin_name: 插件名称
            
            功能说明：
            - 物理删除插件文件/目录
            - 如果插件已加载，会先自动卸载
            - 支持删除文件夹插件和压缩包插件（.zip/.mfp）
            
            ⚠️ 警告：
            - 此操作不可撤销！
            - 会永久删除插件的所有文件
            - 删除前请确认备份重要数据
            - 不会自动删除插件配置文件
            
            执行流程：
            1. 检查插件是否已加载，如果是则先卸载
            2. 查找插件文件路径
            3. 删除整个插件目录或压缩包文件
            
            使用场景：
            - 彻底移除不需要的插件
            - 清理失败的插件
            - 准备重新安装插件
            
            前端对应：
            - deletePlugin() in api/index.ts
            - deletePluginAction() in stores/plugin.ts
            """
            try:
                plugin_manager = get_plugin_manager()
                
                # 如果插件已加载，先卸载
                if plugin_manager.is_plugin_loaded(plugin_name):
                    await plugin_manager.unload_plugin(plugin_name)
                
                # 查找插件路径
                all_paths = _get_all_plugin_paths()
                plugin_path = all_paths.get(plugin_name)
                
                if not plugin_path:
                    return OperationResponse(
                        success=False,
                        error=f"找不到插件 '{plugin_name}' 的文件"
                    )
                
                path_obj = Path(plugin_path)
                
                # 删除插件文件/目录
                try:
                    if path_obj.is_dir():
                        shutil.rmtree(path_obj)
                    elif path_obj.is_file():
                        path_obj.unlink()
                    else:
                        return OperationResponse(
                            success=False,
                            error=f"插件路径 '{plugin_path}' 无效"
                        )
                except Exception as e:
                    return OperationResponse(
                        success=False,
                        error=f"删除插件文件失败: {e}"
                    )
                
                return OperationResponse(
                    success=True,
                    message=f"插件 '{plugin_name}' 已删除"
                )
                
            except Exception as e:
                logger.error(f"删除插件失败: {e}")
                return OperationResponse(
                    success=False,
                    error=str(e)
                )
        
        @self.app.post("/plugins/{plugin_name}/load", summary="加载插件", response_model=OperationResponse)
        async def load_plugin(plugin_name: str, _=VerifiedDep):
            """加载指定插件
            
            Args:
                plugin_name: 插件名称
            
            功能说明：
            - 从文件系统导入插件模块
            - 读取并验证 manifest.json
            - 实例化插件类
            - 注册插件的所有组件
            - 调用 on_plugin_loaded 生命周期钩子
            
            执行流程：
            1. 在 plugins 目录中查找插件
            2. 读取 manifest.json 获取元信息
            3. 导入插件入口文件（plugin.py）
            4. 实例化插件类并注册组件
            5. 设置插件状态为 ACTIVE
            
            前置条件：
            - 插件文件存在于 plugins 目录
            - manifest.json 格式正确
            - 插件未被加载（避免重复加载）
            
            使用场景：
            - 首次加载新安装的插件
            - 重新加载已卸载的插件
            
            前端对应：
            - loadPlugin() in api/index.ts
            - loadPluginAction() in stores/plugin.ts
            """
            try:
                plugin_manager = get_plugin_manager()
                
                # 检查是否已加载
                if plugin_manager.is_plugin_loaded(plugin_name):
                    return OperationResponse(
                        success=False,
                        error=f"插件 '{plugin_name}' 已经加载"
                    )
                
                # 查找插件路径
                all_paths = _get_all_plugin_paths()
                plugin_path = all_paths.get(plugin_name)
                
                if not plugin_path:
                    return OperationResponse(
                        success=False,
                        error=f"找不到插件 '{plugin_name}'"
                    )
                
                # 加载插件
                success = await plugin_manager.load_plugin(plugin_path)
                
                if success:
                    return OperationResponse(
                        success=True,
                        message=f"插件 '{plugin_name}' 加载成功"
                    )
                else:
                    error = plugin_manager._failed_plugins.get(plugin_name, "未知错误")
                    return OperationResponse(
                        success=False,
                        error=error
                    )
                    
            except Exception as e:
                logger.error(f"加载插件失败: {e}")
                return OperationResponse(
                    success=False,
                    error=str(e)
                )
        
        @self.app.post("/plugins/scan", summary="扫描新插件", response_model=ScanResultResponse)
        async def scan_plugins(_=VerifiedDep):
            """扫描插件目录，发现并加载新插件
            
            功能说明：
            - 遍历 plugins 目录查找所有插件
            - 识别新增的插件（未被系统加载的）
            - 自动加载新发现的插件
            - 返回扫描结果统计
            
            扫描范围：
            - 文件夹格式插件（包含 manifest.json 的目录）
            - 压缩包格式插件（.zip 和 .mfp 文件）
            
            返回信息：
            ```json
            {
                "success": true,
                "registered": 5,    // 发现的新插件数量
                "loaded": 4,        // 成功加载的数量
                "failed": 1,        // 加载失败的数量
                "new_plugins": ["plugin_a", "plugin_b", ...]  // 新插件名称列表
            }
            ```
            
            使用场景：
            - 添加新插件后刷新系统
            - 定期检查插件目录
            - 批量导入插件
            
            注意事项：
            - 只会加载新插件，不会重载已存在的
            - 失败的插件会记录错误信息
            - 扫描可能需要一些时间
            
            前端对应：
            - scanPlugins() in api/index.ts
            - scanForNewPlugins() in stores/plugin.ts
            """
            try:
                plugin_loader = get_plugin_loader()
                plugin_manager = get_plugin_manager()
                
                # 获取当前已加载的插件
                loaded_before = set(plugin_manager.list_loaded_plugins())
                
                # 发现所有插件
                discovered = await plugin_loader.discover_plugins(str(PLUGINS_DIR))
                
                # 加载新发现的插件
                new_plugins: list[str] = []
                registered_count = 0
                loaded_count = 0
                failed_count = 0
                
                for plugin_path in discovered:
                    # 读取 manifest
                    from src.core.components.loader import load_manifest
                    manifest = await load_manifest(plugin_path)
                    
                    if not manifest:
                        failed_count += 1
                        continue
                    
                    plugin_name = manifest.name
                    
                    # 跳过已加载的插件
                    if plugin_name in loaded_before:
                        continue
                    
                    registered_count += 1
                    new_plugins.append(plugin_name)
                    
                    # 尝试加载
                    success = await plugin_manager.load_plugin(plugin_path)
                    
                    if success:
                        loaded_count += 1
                    else:
                        failed_count += 1
                
                return ScanResultResponse(
                    success=True,
                    registered=registered_count,
                    loaded=loaded_count,
                    failed=failed_count,
                    new_plugins=new_plugins,
                )
                
            except Exception as e:
                logger.error(f"扫描插件失败: {e}")
                return ScanResultResponse(
                    success=False,
                    error=str(e),
                )
        
        @self.app.post("/plugins/reload-all", summary="重载所有插件", response_model=OperationResponse)
        async def reload_all_plugins(_=VerifiedDep):
            """重载所有已加载的插件
            
            功能说明：
            - 批量重载系统中所有已加载的插件
            - 逐个执行：卸载 → 重新加载
            - 统计成功和失败的数量
            
            执行过程：
            1. 获取所有已加载插件列表
            2. 依次重载每个插件
            3. 记录成功和失败的数量
            4. 返回统计结果
            
            返回信息：
            - 全部成功：success=True, message 包含成功数量
            - 部分失败：success=False, error 包含成功/失败统计
            
            使用场景：
            - 批量更新插件后统一刷新
            - 系统维护或重置
            - 插件出现问题时批量重载
            
            ⚠️ 注意事项：
            - 操作时间可能较长（取决于插件数量）
            - 会中断所有插件的运行
            - 建议在系统空闲时执行
            - 可能导致短暂的服务中断
            
            前端对应：
            - reloadAllPlugins() in api/index.ts
            - reloadAll() in stores/plugin.ts
            """
            try:
                plugin_manager = get_plugin_manager()
                
                loaded_plugins = plugin_manager.list_loaded_plugins()
                
                if not loaded_plugins:
                    return OperationResponse(
                        success=True,
                        message="没有已加载的插件"
                    )
                
                succeeded_count = 0
                failed_count = 0
                
                for plugin_name in loaded_plugins:
                    try:
                        success = await plugin_manager.reload_plugin(plugin_name)
                        
                        if success:
                            succeeded_count += 1
                        else:
                            failed_count += 1
                            
                    except Exception:
                        failed_count += 1
                
                if failed_count == 0:
                    return OperationResponse(
                        success=True,
                        message=f"成功重载 {succeeded_count} 个插件"
                    )
                else:
                    return OperationResponse(
                        success=False,
                        error=f"重载完成，成功 {succeeded_count} 个，失败 {failed_count} 个"
                    )
                
            except Exception as e:
                logger.error(f"重载所有插件失败: {e}")
                return OperationResponse(
                    success=False,
                    error=str(e)
                )
    
    async def startup(self) -> None:
        """路由启动钩子"""
        logger.info(f"插件管理路由已启动，路径: {self.custom_route_path}")
    
    async def shutdown(self) -> None:
        """路由关闭钩子"""
        logger.info("插件管理路由已关闭")
