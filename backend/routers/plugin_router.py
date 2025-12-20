"""
插件管理路由组件
提供插件生命周期管理、状态控制、组件管理等API接口
"""

from typing import Optional

from fastapi import Query
from pathlib import Path
from pydantic import BaseModel

from src.common.logger import get_logger
from src.common.security import VerifiedDep
from src.plugin_system import BaseRouterComponent
from src.plugin_system.apis import component_state_api, plugin_info_api, plugin_manage_api
from src.plugin_system.base.component_types import ComponentType
from src.plugin_system.core.component_registry import component_registry
from src.plugin_system.core.plugin_manager import plugin_manager
from src.config.config import CONFIG_DIR


logger = get_logger("WebUI.PluginRouter")


# ==================== 响应模型 ====================


class PluginItemResponse(BaseModel):
    """插件列表项"""

    name: str
    display_name: str
    version: str
    author: str
    description: Optional[str] = None
    enabled: bool
    loaded: bool
    components_count: int
    last_updated: Optional[str] = None
    config_path: Optional[str] = None
    error: Optional[str] = None


class PluginListResponse(BaseModel):
    """插件列表响应"""

    success: bool
    plugins: list[PluginItemResponse]  # 正常加载的插件列表（已加载和已注册）
    failed_plugins: list[PluginItemResponse] = []  # 加载失败的插件列表
    total: int
    loaded: int
    enabled: int
    failed: int
    error: Optional[str] = None


class ComponentItemResponse(BaseModel):
    """组件项"""

    name: str
    type: str
    description: Optional[str] = None
    enabled: bool
    plugin_name: str
    details: Optional[dict] = None


class ComponentsResponse(BaseModel):
    """组件列表响应"""

    success: bool
    plugin_name: str
    components: list[ComponentItemResponse]
    total: int
    enabled: int
    disabled: int
    error: Optional[str] = None


class PluginDetailResponse(BaseModel):
    """插件详情响应"""

    success: bool
    plugin: Optional[dict] = None
    error: Optional[str] = None


class OperationResponse(BaseModel):
    """操作响应"""

    success: bool
    message: Optional[str] = None
    error: Optional[str] = None


class ScanResultResponse(BaseModel):
    """扫描结果响应"""

    success: bool
    registered: int
    loaded: int
    failed: int
    new_plugins: list[str]
    error: Optional[str] = None


class BatchOperationResponse(BaseModel):
    """批量操作响应"""

    success: bool
    results: dict[str, dict]
    total: int
    succeeded: int
    failed: int


# ==================== 请求模型 ====================


class ScanRequest(BaseModel):
    """扫描请求"""

    load_after_register: bool = True


class BatchOperationRequest(BaseModel):
    """批量操作请求"""

    plugin_names: list[str]


# ==================== 工具函数 ====================


def _get_plugin_item_response(plugin_name: str, error_msg: Optional[str] = None) -> PluginItemResponse:
    """
    构建插件列表项响应

    Args:
        plugin_name: 插件名称
        error_msg: 错误信息（如果插件加载失败）

    Returns:
        PluginItemResponse: 插件列表项
    """
    plugin_info = component_registry.get_plugin_info(plugin_name)
    plugin_instance = plugin_manager.get_plugin_instance(plugin_name)

    return PluginItemResponse(
        name=plugin_name,
        display_name=plugin_info.display_name if plugin_info else plugin_name,
        version=plugin_info.version if plugin_info else "unknown",
        author=plugin_info.author if plugin_info else "unknown",
        description=plugin_info.description if plugin_info else None,
        enabled=plugin_instance.enable_plugin if plugin_instance else False,
        loaded=plugin_instance is not None,
        components_count=len(plugin_info.components) if plugin_info else 0,
        config_path=f"config/plugins/{plugin_name}.toml" if plugin_instance else None,
        error=error_msg,
    )


def _get_component_type_name(component_type: ComponentType) -> str:
    """获取组件类型的友好名称"""
    type_names = {
        ComponentType.COMMAND: "Command",
        ComponentType.ACTION: "Action",
        ComponentType.EVENT_HANDLER: "EventHandler",
        ComponentType.ROUTER: "Router",
        ComponentType.TOOL: "Tool",
        ComponentType.PROMPT: "Prompt",
    }
    return type_names.get(component_type, str(component_type))


# ==================== HTTP路由组件 ====================


class WebUIPluginRouter(BaseRouterComponent):
    """
    插件管理路由组件
    提供插件生命周期管理、状态控制、组件管理等API接口
    """

    component_name = "plugin_manager"
    component_description = "提供插件管理API接口"
    component_version = "1.0.0"

    def register_endpoints(self) -> None:
        """注册所有HTTP端点"""

        # ==================== 插件列表与查询 ====================

        @self.router.get("/plugins", summary="获取所有插件列表")
        def get_all_plugins(_=VerifiedDep) -> PluginListResponse:
            """
            获取所有插件列表，包括已加载、已注册和加载失败的插件
            """
            try:
                plugins = []  # 正常插件列表（已加载和已注册）
                failed_plugin_list = []  # 失败插件列表

                # 获取已加载的插件
                loaded_plugins = plugin_manage_api.list_loaded_plugins()
                for name in loaded_plugins:
                    plugins.append(_get_plugin_item_response(name))

                # 获取已注册但未加载的插件（这些插件可以被加载）
                registered_plugins = plugin_manage_api.list_registered_plugins()
                for name in registered_plugins:
                    if name not in loaded_plugins:
                        plugins.append(_get_plugin_item_response(name))

                # 获取加载失败的插件（单独列表）
                failed_plugins = plugin_manage_api.list_failed_plugins()
                for name, error in failed_plugins.items():
                    failed_plugin_list.append(
                        _get_plugin_item_response(name, error_msg=str(error) if error else "加载失败")
                    )

                # 统计
                total = len(plugins) + len(failed_plugin_list)
                loaded = len(loaded_plugins)
                enabled = sum(1 for p in plugins if p.enabled)
                failed = len(failed_plugin_list)

                return PluginListResponse(
                    success=True,
                    plugins=plugins,
                    failed_plugins=failed_plugin_list,  # 返回失败插件列表
                    total=total,
                    loaded=loaded,
                    enabled=enabled,
                    failed=failed,
                )
            except Exception as e:
                logger.error(f"获取插件列表失败: {e}", exc_info=True)
                return PluginListResponse(
                    success=False,
                    plugins=[],
                    failed_plugins=[],
                    total=0,
                    loaded=0,
                    enabled=0,
                    failed=0,
                    error=str(e),
                )

        @self.router.get("/plugins/{plugin_name}", summary="获取插件详情")
        def get_plugin_detail(plugin_name: str, _=VerifiedDep) -> PluginDetailResponse:
            """
            获取指定插件的详细信息，包括组件列表、配置路径等
            注意：只有已加载的插件才能获取详情
            """
            try:
                # 检查插件是否已加载（未加载的插件不能查看详情）
                if not plugin_manage_api.is_plugin_loaded(plugin_name):
                    logger.warning(f"插件未加载，无法获取详情: {plugin_name}")
                    return PluginDetailResponse(success=False, error=f"插件 '{plugin_name}' 未加载，无法查看详情")

                # 获取插件信息
                plugin_info = plugin_info_api.get_plugin_details(plugin_name)
                if not plugin_info:
                    logger.error(f"无法获取插件信息: {plugin_name}")
                    return PluginDetailResponse(success=False, error=f"无法获取插件 '{plugin_name}' 的信息")

                # 获取插件实例
                plugin_instance = plugin_manage_api.get_plugin_instance(plugin_name)

                # 构建组件列表
                # plugin_info_api.get_plugin_details() 返回的 components 是 list[dict]
                components_data = plugin_info.get("components", [])

                components = []
                for comp_info in components_data:
                    comp_name = comp_info.get("name", "unknown")
                    # API 返回的字段是 component_type
                    comp_type_str = comp_info.get("component_type", "Unknown")

                    # 直接使用 API 返回的 enabled 状态
                    is_enabled = comp_info.get("enabled", False)

                    components.append(
                        {
                            "name": comp_name,
                            "type": comp_type_str,
                            "description": comp_info.get("description", ""),
                            "enabled": is_enabled,
                        }
                    )

                # 构建详情响应
                config_path = Path(f"{CONFIG_DIR}/plugins/{plugin_name}/config.toml")
                config_file_exists = config_path.exists()

                plugin_enabled = plugin_instance.enable_plugin if plugin_instance else False

                plugin_detail = {
                    "name": plugin_name,
                    "display_name": plugin_info.get("display_name", plugin_name),
                    "version": plugin_info.get("version", "unknown"),
                    "author": plugin_info.get("author", "unknown"),
                    "description": plugin_info.get("description"),
                    "enabled": plugin_enabled,
                    "loaded": True,
                    "components": components,
                    "components_count": len(components),
                    "config": {
                        "path": config_path,
                        "exists": config_file_exists,  
                    },
                    "metadata": plugin_info.get("metadata", {}),
                }

                return PluginDetailResponse(
                    success=True,
                    plugin=plugin_detail,
                )
            except Exception as e:
                logger.error(f"获取插件详情失败: {e}", exc_info=True)
                return PluginDetailResponse(
                    success=False,
                    error=str(e),
                )

        # ==================== 插件状态管理 ====================

        @self.router.post("/plugins/{plugin_name}/enable", summary="启用插件")
        async def enable_plugin(plugin_name: str, _=VerifiedDep) -> OperationResponse:
            """启用指定的插件"""
            try:
                success = await plugin_manage_api.enable_plugin(plugin_name)
                if success:
                    return OperationResponse(success=True, message=f"插件 '{plugin_name}' 已启用")
                else:
                    return OperationResponse(success=False, error=f"启用插件 '{plugin_name}' 失败")
            except ValueError as e:
                return OperationResponse(success=False, error=str(e))
            except Exception as e:
                logger.error(f"启用插件失败: {e}", exc_info=True)
                return OperationResponse(success=False, error=f"内部错误: {str(e)}")

        @self.router.post("/plugins/{plugin_name}/disable", summary="禁用插件")
        async def disable_plugin(plugin_name: str, _=VerifiedDep) -> OperationResponse:
            """禁用指定的插件"""
            try:
                success = await plugin_manage_api.disable_plugin(plugin_name)
                if success:
                    return OperationResponse(success=True, message=f"插件 '{plugin_name}' 已禁用")
                else:
                    return OperationResponse(success=False, error=f"禁用插件 '{plugin_name}' 失败")
            except Exception as e:
                logger.error(f"禁用插件失败: {e}", exc_info=True)
                return OperationResponse(success=False, error=f"内部错误: {str(e)}")

        @self.router.post("/plugins/{plugin_name}/reload", summary="重载插件")
        async def reload_plugin(plugin_name: str, _=VerifiedDep) -> OperationResponse:
            """重新加载指定的插件"""
            try:
                success = await plugin_manage_api.reload_plugin(plugin_name)
                if success:
                    return OperationResponse(success=True, message=f"插件 '{plugin_name}' 重载成功")
                else:
                    return OperationResponse(success=False, error=f"重载插件 '{plugin_name}' 失败")
            except ValueError as e:
                return OperationResponse(success=False, error=str(e))
            except Exception as e:
                logger.error(f"重载插件失败: {e}", exc_info=True)
                return OperationResponse(success=False, error=f"内部错误: {str(e)}")

        @self.router.post("/plugins/{plugin_name}/unload", summary="卸载插件")
        async def unload_plugin(plugin_name: str, _=VerifiedDep) -> OperationResponse:
            """完全卸载指定的插件"""
            try:
                success = await plugin_manage_api.unload_plugin(plugin_name)
                if success:
                    return OperationResponse(success=True, message=f"插件 '{plugin_name}' 已卸载")
                else:
                    return OperationResponse(success=False, error=f"卸载插件 '{plugin_name}' 失败")
            except Exception as e:
                logger.error(f"卸载插件失败: {e}", exc_info=True)
                return OperationResponse(success=False, error=f"内部错误: {str(e)}")

        @self.router.delete("/plugins/{plugin_name}/delete", summary="删除插件")
        async def delete_plugin(plugin_name: str, _=VerifiedDep) -> OperationResponse:
            """删除指定的插件（删除文件夹）"""
            try:
                import shutil
                from pathlib import Path
                
                # 先卸载插件（如果已加载）
                if plugin_manage_api.is_plugin_loaded(plugin_name):
                    logger.info(f"插件 '{plugin_name}' 已加载，先进行卸载")
                    await plugin_manage_api.unload_plugin(plugin_name)
                
                # 获取插件路径
                plugin_path = plugin_manager.get_plugin_path(plugin_name)
                if not plugin_path:
                    logger.error(f"无法获取插件 '{plugin_name}' 的路径")
                    return OperationResponse(success=False, error=f"无法找到插件 '{plugin_name}' 的文件夹")
                
                # 获取插件文件夹路径（去除 plugin.py 或 __init__.py 部分）
                plugin_folder = Path(plugin_path)
                
                # 安全检查：确保路径包含 "plugins" 目录
                if "plugins" not in str(plugin_folder).lower():
                    logger.error(f"安全检查失败：插件路径不在 plugins 目录中: {plugin_folder}")
                    return OperationResponse(success=False, error="安全检查失败：插件路径不合法")
                
                # 检查文件夹是否存在
                if not plugin_folder.exists():
                    logger.warning(f"插件文件夹不存在: {plugin_folder}")
                    return OperationResponse(success=False, error=f"插件文件夹不存在: {plugin_folder}")
                
                # 删除文件夹
                logger.info(f"正在删除插件文件夹: {plugin_folder}")
                shutil.rmtree(plugin_folder)
                logger.info(f"插件 '{plugin_name}' 文件夹已删除: {plugin_folder}")
                
                # 从注册表中移除插件信息
                if plugin_name in plugin_manager.plugin_classes:
                    del plugin_manager.plugin_classes[plugin_name]
                if plugin_name in plugin_manager.plugin_paths:
                    del plugin_manager.plugin_paths[plugin_name]
                
                return OperationResponse(success=True, message=f"插件 '{plugin_name}' 已成功删除")
                
            except PermissionError as e:
                logger.error(f"删除插件失败（权限不足）: {e}", exc_info=True)
                return OperationResponse(success=False, error="权限不足，无法删除插件文件夹")
            except Exception as e:
                logger.error(f"删除插件失败: {e}", exc_info=True)
                return OperationResponse(success=False, error=f"内部错误: {str(e)}")

        @self.router.post("/plugins/{plugin_name}/load", summary="加载插件")
        async def load_plugin(plugin_name: str, _=VerifiedDep) -> OperationResponse:
            """加载指定的插件"""
            try:
                success = await plugin_manage_api.load_plugin(plugin_name)
                if success:
                    return OperationResponse(success=True, message=f"插件 '{plugin_name}' 加载成功")
                else:
                    return OperationResponse(success=False, error=f"加载插件 '{plugin_name}' 失败")
            except ValueError as e:
                return OperationResponse(success=False, error=str(e))
            except Exception as e:
                logger.error(f"加载插件失败: {e}", exc_info=True)
                return OperationResponse(success=False, error=f"内部错误: {str(e)}")

        @self.router.get("/plugins/{plugin_name}/status", summary="获取插件状态")
        def get_plugin_status(plugin_name: str, _=VerifiedDep) -> dict:
            """获取插件的当前状态"""
            try:
                return {
                    "success": True,
                    "plugin_name": plugin_name,
                    "loaded": plugin_manage_api.is_plugin_loaded(plugin_name),
                    "enabled": plugin_manage_api.is_plugin_enabled(plugin_name),
                }
            except Exception as e:
                logger.error(f"获取插件状态失败: {e}", exc_info=True)
                return {
                    "success": False,
                    "error": str(e),
                }

        # ==================== 组件管理 ====================

        @self.router.get("/plugins/{plugin_name}/components", summary="获取插件的所有组件")
        def get_plugin_components(plugin_name: str, _=VerifiedDep) -> ComponentsResponse:
            """获取指定插件的所有组件"""
            try:
                # 检查插件是否存在
                if not plugin_manage_api.is_plugin_loaded(plugin_name):
                    return ComponentsResponse(
                        success=False,
                        plugin_name=plugin_name,
                        components=[],
                        total=0,
                        enabled=0,
                        disabled=0,
                        error=f"插件 '{plugin_name}' 未加载",
                    )

                # 获取插件信息
                plugin_info = plugin_info_api.get_plugin_details(plugin_name)
                if not plugin_info:
                    return ComponentsResponse(
                        success=False,
                        plugin_name=plugin_name,
                        components=[],
                        total=0,
                        enabled=0,
                        disabled=0,
                        error=f"无法获取插件 '{plugin_name}' 的信息",
                    )

                # 构建组件列表
                components = []
                enabled_count = 0
                components_data = plugin_info.get("components", {})

                # 处理组件数据（可能是字典或列表）
                if isinstance(components_data, dict):
                    for comp_name, comp_info in components_data.items():
                        comp_type_str = comp_info.get("type", "Unknown")

                        # 尝试获取组件类型枚举
                        try:
                            comp_type = ComponentType[comp_type_str.upper()]
                        except (KeyError, AttributeError):
                            comp_type = ComponentType.COMMAND  # 默认类型

                        is_enabled = component_state_api.is_component_enabled(comp_name, comp_type)
                        if is_enabled:
                            enabled_count += 1

                        components.append(
                            ComponentItemResponse(
                                name=comp_name,
                                type=_get_component_type_name(comp_type),
                                description=comp_info.get("description"),
                                enabled=is_enabled,
                                plugin_name=plugin_name,
                                details=comp_info.get("details"),
                            )
                        )
                elif isinstance(components_data, list):
                    for comp_info in components_data:
                        if isinstance(comp_info, dict):
                            comp_name = comp_info.get("name", "unknown")
                            comp_type_str = comp_info.get("type", "Unknown")

                            # 尝试获取组件类型枚举
                            try:
                                comp_type = ComponentType[comp_type_str.upper()]
                            except (KeyError, AttributeError):
                                comp_type = ComponentType.COMMAND  # 默认类型

                            is_enabled = component_state_api.is_component_enabled(comp_name, comp_type)
                            if is_enabled:
                                enabled_count += 1

                            components.append(
                                ComponentItemResponse(
                                    name=comp_name,
                                    type=_get_component_type_name(comp_type),
                                    description=comp_info.get("description"),
                                    enabled=is_enabled,
                                    plugin_name=plugin_name,
                                    details=comp_info.get("details"),
                                )
                            )

                total = len(components)
                disabled_count = total - enabled_count

                return ComponentsResponse(
                    success=True,
                    plugin_name=plugin_name,
                    components=components,
                    total=total,
                    enabled=enabled_count,
                    disabled=disabled_count,
                )
            except Exception as e:
                logger.error(f"获取插件组件失败: {e}", exc_info=True)
                return ComponentsResponse(
                    success=False,
                    plugin_name=plugin_name,
                    components=[],
                    total=0,
                    enabled=0,
                    disabled=0,
                    error=str(e),
                )

        @self.router.post("/plugins/{plugin_name}/components/{component_name}/enable", summary="启用组件")
        async def enable_component(
            plugin_name: str,
            component_name: str,
            component_type: str = Query(..., description="组件类型"),
            _=VerifiedDep,
        ) -> OperationResponse:
            """启用指定的组件"""
            try:
                # 转换组件类型
                try:
                    comp_type = ComponentType[component_type.upper()]
                except KeyError:
                    available_types = [t.name for t in ComponentType]
                    logger.error(f"无效的组件类型: {component_type}, 可用类型: {available_types}")
                    return OperationResponse(
                        success=False, error=f"无效的组件类型: {component_type}，可用类型: {', '.join(available_types)}"
                    )

                success = await component_state_api.set_component_enabled(component_name, comp_type, True)

                if success:
                    return OperationResponse(success=True, message=f"组件 '{component_name}' 已启用")
                else:
                    return OperationResponse(success=False, error=f"启用组件 '{component_name}' 失败")
            except Exception as e:
                logger.error(f"启用组件失败: {e}", exc_info=True)
                return OperationResponse(success=False, error=f"内部错误: {str(e)}")

        @self.router.post("/plugins/{plugin_name}/components/{component_name}/disable", summary="禁用组件")
        async def disable_component(
            plugin_name: str,
            component_name: str,
            component_type: str = Query(..., description="组件类型"),
            _=VerifiedDep,
        ) -> OperationResponse:
            """禁用指定的组件"""
            try:
                # 转换组件类型
                try:
                    comp_type = ComponentType[component_type.upper()]
                except KeyError:
                    available_types = [t.name for t in ComponentType]
                    logger.error(f"无效的组件类型: {component_type}, 可用类型: {available_types}")
                    return OperationResponse(
                        success=False, error=f"无效的组件类型: {component_type}，可用类型: {', '.join(available_types)}"
                    )

                success = await component_state_api.set_component_enabled(component_name, comp_type, False)

                if success:
                    return OperationResponse(success=True, message=f"组件 '{component_name}' 已禁用")
                else:
                    return OperationResponse(success=False, error=f"禁用组件 '{component_name}' 失败")
            except Exception as e:
                logger.error(f"禁用组件失败: {e}", exc_info=True)
                return OperationResponse(success=False, error=f"内部错误: {str(e)}")

        # ==================== 批量操作和扫描 ====================

        @self.router.post("/plugins/scan", summary="扫描新插件")
        def scan_plugins(request: ScanRequest, _=VerifiedDep) -> ScanResultResponse:
            """扫描插件目录，发现并注册新插件"""
            try:
                # 记录扫描前的插件列表
                registered_before = set(plugin_manage_api.list_registered_plugins())

                # 执行扫描
                success_count, fail_count = plugin_manage_api.rescan_and_register_plugins(
                    load_after_register=request.load_after_register
                )

                # 找出新注册的插件
                registered_after = set(plugin_manage_api.list_registered_plugins())
                new_plugins = list(registered_after - registered_before)

                return ScanResultResponse(
                    success=True,
                    registered=success_count,
                    loaded=success_count if request.load_after_register else 0,
                    failed=fail_count,
                    new_plugins=new_plugins,
                )
            except Exception as e:
                logger.error(f"扫描插件失败: {e}", exc_info=True)
                return ScanResultResponse(
                    success=False,
                    registered=0,
                    loaded=0,
                    failed=0,
                    new_plugins=[],
                    error=str(e),
                )

        @self.router.post("/plugins/reload-all", summary="重载所有插件")
        async def reload_all_plugins(_=VerifiedDep) -> OperationResponse:
            """重新加载所有已加载的插件"""
            try:
                success = await plugin_manage_api.reload_all_plugins()
                if success:
                    return OperationResponse(success=True, message="所有插件重载成功")
                else:
                    return OperationResponse(success=False, error="部分插件重载失败，请查看日志")
            except Exception as e:
                logger.error(f"重载所有插件失败: {e}", exc_info=True)
                return OperationResponse(success=False, error=f"内部错误: {str(e)}")

        @self.router.post("/plugins/batch/enable", summary="批量启用插件")
        async def batch_enable_plugins(request: BatchOperationRequest, _=VerifiedDep) -> BatchOperationResponse:
            """批量启用多个插件"""
            results = {}
            succeeded = 0
            failed = 0

            for plugin_name in request.plugin_names:
                try:
                    success = await plugin_manage_api.enable_plugin(plugin_name)
                    if success:
                        results[plugin_name] = {"success": True, "message": "已启用"}
                        succeeded += 1
                    else:
                        results[plugin_name] = {"success": False, "error": "启用失败"}
                        failed += 1
                except Exception as e:
                    results[plugin_name] = {"success": False, "error": str(e)}
                    failed += 1

            return BatchOperationResponse(
                success=failed == 0,
                results=results,
                total=len(request.plugin_names),
                succeeded=succeeded,
                failed=failed,
            )

        @self.router.post("/plugins/batch/disable", summary="批量禁用插件")
        async def batch_disable_plugins(request: BatchOperationRequest, _=VerifiedDep) -> BatchOperationResponse:
            """批量禁用多个插件"""
            results = {}
            succeeded = 0
            failed = 0

            for plugin_name in request.plugin_names:
                try:
                    success = await plugin_manage_api.disable_plugin(plugin_name)
                    if success:
                        results[plugin_name] = {"success": True, "message": "已禁用"}
                        succeeded += 1
                    else:
                        results[plugin_name] = {"success": False, "error": "禁用失败"}
                        failed += 1
                except Exception as e:
                    results[plugin_name] = {"success": False, "error": str(e)}
                    failed += 1

            return BatchOperationResponse(
                success=failed == 0,
                results=results,
                total=len(request.plugin_names),
                succeeded=succeeded,
                failed=failed,
            )

        @self.router.post("/plugins/batch/reload", summary="批量重载插件")
        async def batch_reload_plugins(request: BatchOperationRequest, _=VerifiedDep) -> BatchOperationResponse:
            """批量重载多个插件"""
            results = {}
            succeeded = 0
            failed = 0

            for plugin_name in request.plugin_names:
                try:
                    success = await plugin_manage_api.reload_plugin(plugin_name)
                    if success:
                        results[plugin_name] = {"success": True, "message": "重载成功"}
                        succeeded += 1
                    else:
                        results[plugin_name] = {"success": False, "error": "重载失败"}
                        failed += 1
                except Exception as e:
                    results[plugin_name] = {"success": False, "error": str(e)}
                    failed += 1

            return BatchOperationResponse(
                success=failed == 0,
                results=results,
                total=len(request.plugin_names),
                succeeded=succeeded,
                failed=failed,
            )
