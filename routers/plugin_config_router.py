"""
插件配置管理路由组件
提供插件配置的增强管理，包括 Schema 获取、配置读写、备份恢复等 API 接口
"""

import shutil
from datetime import datetime
from pathlib import Path
from typing import Optional

import toml
import tomlkit
from pydantic import BaseModel

from src.common.logger import get_logger
from src.common.security import VerifiedDep
from src.config.config import CONFIG_DIR
from src.plugin_system import BaseRouterComponent
from src.plugin_system.core.plugin_manager import plugin_manager

from ..utils.plugin_schema_service import (
    parse_plugin_schema,
    get_plugin_default_config,
)

logger = get_logger("WebUI.PluginConfigRouter")

# 配置文件根目录
CONFIG_ROOT = Path(CONFIG_DIR)


# ==================== 响应模型 ====================


class PluginConfigInfo(BaseModel):
    """插件配置文件信息"""
    plugin_name: str
    display_name: str
    config_path: str
    exists: bool
    has_schema: bool
    last_modified: Optional[str] = None


class PluginConfigListResponse(BaseModel):
    """插件配置列表响应"""
    success: bool
    configs: list[PluginConfigInfo]
    total: int
    error: Optional[str] = None


class PluginConfigContentResponse(BaseModel):
    """插件配置内容响应"""
    success: bool
    plugin_name: str
    content: Optional[str] = None  # 原始 TOML 内容
    parsed: Optional[dict] = None  # 解析后的配置
    last_modified: Optional[str] = None
    error: Optional[str] = None


class PluginSchemaResponse(BaseModel):
    """插件配置 Schema 响应"""
    success: bool
    plugin_name: str
    schema: Optional[dict] = None  # 按 section 组织的字段定义
    sections: Optional[list[dict]] = None  # section 元数据
    layout: Optional[dict] = None  # 布局配置
    error: Optional[str] = None


class PluginConfigSaveRequest(BaseModel):
    """保存配置请求"""
    content: str  # TOML 原始内容
    create_backup: bool = True


class PluginConfigUpdateRequest(BaseModel):
    """更新配置请求（可视化编辑）"""
    updates: dict  # 键值对更新，支持点号路径如 "section.key"
    create_backup: bool = True


class PluginConfigSaveResponse(BaseModel):
    """保存配置响应"""
    success: bool
    message: Optional[str] = None
    backup_path: Optional[str] = None
    error: Optional[str] = None


class PluginConfigBackupInfo(BaseModel):
    """备份信息"""
    name: str
    path: str
    created_at: str
    size: int


class PluginConfigBackupsResponse(BaseModel):
    """备份列表响应"""
    success: bool
    backups: list[PluginConfigBackupInfo]
    error: Optional[str] = None


# ==================== 工具函数 ====================


def get_plugin_config_path(plugin_name: str) -> Path:
    """获取插件配置文件路径"""
    return CONFIG_ROOT / "plugins" / plugin_name / "config.toml"


def get_plugin_display_name(plugin_name: str) -> str:
    """获取插件的显示名称"""
    from src.plugin_system.core.component_registry import component_registry
    
    try:
        plugin_info = component_registry.get_plugin_info(plugin_name)
        if plugin_info and plugin_info.display_name:
            return plugin_info.display_name
    except Exception:
        pass
    
    # 美化插件名称
    return plugin_name.replace("_plugin", "").replace("_", " ").title()


def _deep_merge_dict(target: dict, source: dict, path: str = "") -> None:
    """
    深度合并字典，保留 tomlkit 的注释结构
    只更新叶子节点的值，不替换整个 section
    """
    for key, value in source.items():
        current_path = f"{path}.{key}" if path else key
        
        if key in target:
            # 键已存在
            if isinstance(value, dict) and isinstance(target[key], dict):
                # 两边都是字典，递归合并
                _deep_merge_dict(target[key], value, current_path)
            elif isinstance(value, list) and isinstance(target[key], list):
                # 两边都是列表，逐个元素合并或替换
                target_list = target[key]
                for i, item in enumerate(value):
                    if i < len(target_list):
                        if isinstance(item, dict) and isinstance(target_list[i], dict):
                            _deep_merge_dict(target_list[i], item, f"{current_path}.{i}")
                        else:
                            target_list[i] = item
                    else:
                        target_list.append(item)
                # 如果源列表更短，需要截断目标列表
                while len(target_list) > len(value):
                    target_list.pop()
            else:
                # 叶子节点或类型不同，直接替换
                target[key] = value
        else:
            # 新键，直接添加
            target[key] = value


def apply_updates(original: dict, updates: dict) -> dict:
    """
    应用更新到原始配置
    支持点号分隔的键路径，如 "section.key"
    
    ⚠️ 重要：当 value 是 dict 时，使用深度合并而不是直接替换，以保留注释
    """
    result = original
    
    for key_path, value in updates.items():
        keys = key_path.split(".")
        current = result
        
        # 遍历到倒数第二层
        for i, key in enumerate(keys[:-1]):
            if key.isdigit():
                idx = int(key)
                if isinstance(current, list) and idx < len(current):
                    current = current[idx]
                else:
                    break
            else:
                if key not in current:
                    if i + 1 < len(keys) - 1 and keys[i + 1].isdigit():
                        current[key] = tomlkit.array()
                    else:
                        current[key] = tomlkit.table()
                current = current[key]
        
        # 设置最终值
        final_key = keys[-1]
        if final_key.isdigit():
            idx = int(final_key)
            if isinstance(current, list):
                if idx < len(current):
                    if isinstance(value, dict) and isinstance(current[idx], dict):
                        # 数组元素是字典，深度合并
                        _deep_merge_dict(current[idx], value, f"{key_path}")
                    else:
                        current[idx] = value
                else:
                    current.append(value)
        else:
            # 关键修复：如果 value 是 dict 且目标也是 dict，使用深度合并
            if isinstance(value, dict) and final_key in current and isinstance(current[final_key], dict):
                _deep_merge_dict(current[final_key], value, key_path)
            else:
                current[final_key] = value
    
    return result


# ==================== 路由组件 ====================


class PluginConfigRouterComponent(BaseRouterComponent):
    """
    插件配置管理路由组件
    
    功能:
    1. 获取所有插件配置列表
    2. 获取插件配置 Schema（增强版，包含 UI 信息）
    3. 读取/保存/更新插件配置
    4. 备份管理和恢复
    5. 重置为默认配置
    """

    component_name = "plugin_config"
    component_description = "WebUI 插件配置管理接口"
    component_version = "1.0.0"

    def register_endpoints(self) -> None:
        """注册所有 HTTP 端点"""

        # ==================== 列表接口 ====================

        @self.router.get("/list", response_model=PluginConfigListResponse)
        async def list_plugin_configs(_=VerifiedDep):
            """获取所有插件配置列表"""
            try:
                configs: list[PluginConfigInfo] = []
                
                # 遍历已加载的插件
                for plugin_name in plugin_manager.loaded_plugins:
                    config_path = get_plugin_config_path(plugin_name)
                    config_exists = config_path.exists()
                    
                    # 检查是否有 schema
                    plugin_instance = plugin_manager.get_plugin_instance(plugin_name)
                    has_schema = bool(
                        plugin_instance and 
                        getattr(plugin_instance, 'config_schema', None)
                    )
                    
                    # 获取最后修改时间
                    last_modified = None
                    if config_exists:
                        stat = config_path.stat()
                        last_modified = datetime.fromtimestamp(
                            stat.st_mtime
                        ).strftime("%Y-%m-%d %H:%M:%S")
                    
                    configs.append(PluginConfigInfo(
                        plugin_name=plugin_name,
                        display_name=get_plugin_display_name(plugin_name),
                        config_path=str(config_path.relative_to(CONFIG_ROOT)),
                        exists=config_exists,
                        has_schema=has_schema,
                        last_modified=last_modified,
                    ))
                
                # 按显示名称排序
                configs.sort(key=lambda x: x.display_name)
                
                return PluginConfigListResponse(
                    success=True,
                    configs=configs,
                    total=len(configs),
                )
                
            except Exception as e:
                logger.error(f"获取插件配置列表失败: {e}", exc_info=True)
                return PluginConfigListResponse(
                    success=False,
                    configs=[],
                    total=0,
                    error=str(e),
                )

        # ==================== Schema 接口 ====================

        @self.router.get("/{plugin_name}/schema", response_model=PluginSchemaResponse)
        async def get_plugin_schema(plugin_name: str, _=VerifiedDep):
            """
            获取插件配置 Schema
            
            返回增强的 Schema 信息，包括：
            - schema: 按 section 组织的字段定义
            - sections: section 元数据（标题、图标等）
            - layout: 布局配置（Tab 页等）
            
            控件类型自动推断：
            - bool → switch
            - int/float + min/max → slider
            - int/float → number
            - 有 choices → select
            - list → list
            - dict → json
            - str → text
            """
            try:
                result = parse_plugin_schema(plugin_name)
                
                if result is None:
                    return PluginSchemaResponse(
                        success=False,
                        plugin_name=plugin_name,
                        error="插件未加载",
                    )
                
                return PluginSchemaResponse(
                    success=True,
                    plugin_name=plugin_name,
                    schema=result["schema"],
                    sections=result["sections"],
                    layout=result["layout"],
                )
                
            except Exception as e:
                logger.error(f"获取插件 Schema 失败: {e}", exc_info=True)
                return PluginSchemaResponse(
                    success=False,
                    plugin_name=plugin_name,
                    error=str(e),
                )

        # ==================== 内容接口 ====================

        @self.router.get("/{plugin_name}/content", response_model=PluginConfigContentResponse)
        async def get_plugin_config_content(plugin_name: str, _=VerifiedDep):
            """获取插件配置内容"""
            try:
                config_path = get_plugin_config_path(plugin_name)
                
                if not config_path.exists():
                    return PluginConfigContentResponse(
                        success=False,
                        plugin_name=plugin_name,
                        error="配置文件不存在",
                    )
                
                content = config_path.read_text(encoding="utf-8")
                parsed = toml.loads(content)
                
                stat = config_path.stat()
                last_modified = datetime.fromtimestamp(
                    stat.st_mtime
                ).strftime("%Y-%m-%d %H:%M:%S")
                
                return PluginConfigContentResponse(
                    success=True,
                    plugin_name=plugin_name,
                    content=content,
                    parsed=parsed,
                    last_modified=last_modified,
                )
                
            except toml.TomlDecodeError as e:
                logger.error(f"TOML 解析失败: {e}")
                return PluginConfigContentResponse(
                    success=False,
                    plugin_name=plugin_name,
                    error=f"TOML 格式错误: {str(e)}",
                )
            except Exception as e:
                logger.error(f"读取配置失败: {e}", exc_info=True)
                return PluginConfigContentResponse(
                    success=False,
                    plugin_name=plugin_name,
                    error=str(e),
                )

        # ==================== 保存接口 ====================

        @self.router.post("/{plugin_name}/save", response_model=PluginConfigSaveResponse)
        async def save_plugin_config(
            plugin_name: str,
            request: PluginConfigSaveRequest,
            _=VerifiedDep,
        ):
            """保存插件配置（原始 TOML 内容）"""
            try:
                config_path = get_plugin_config_path(plugin_name)
                
                # 验证 TOML 格式
                try:
                    tomlkit.parse(request.content)
                except Exception as e:
                    return PluginConfigSaveResponse(
                        success=False,
                        error=f"TOML 格式错误: {str(e)}",
                    )
                
                backup_path = None
                
                # 创建备份
                if request.create_backup and config_path.exists():
                    backup_dir = config_path.parent / "backups_from_webui"
                    backup_dir.mkdir(exist_ok=True)
                    
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    backup_name = f"config_{timestamp}.toml"
                    backup_file = backup_dir / backup_name
                    
                    shutil.copy2(config_path, backup_file)
                    backup_path = str(backup_file.relative_to(CONFIG_ROOT))
                    logger.info(f"配置备份已创建: {backup_path}")
                
                # 确保目录存在
                config_path.parent.mkdir(parents=True, exist_ok=True)
                
                # 保存配置
                config_path.write_text(request.content, encoding="utf-8")
                logger.info(f"插件配置已保存: {plugin_name}")
                
                return PluginConfigSaveResponse(
                    success=True,
                    message="配置已保存",
                    backup_path=backup_path,
                )
                
            except Exception as e:
                logger.error(f"保存配置失败: {e}", exc_info=True)
                return PluginConfigSaveResponse(
                    success=False,
                    error=str(e),
                )

        @self.router.post("/{plugin_name}/update", response_model=PluginConfigSaveResponse)
        async def update_plugin_config(
            plugin_name: str,
            request: PluginConfigUpdateRequest,
            _=VerifiedDep,
        ):
            """更新插件配置（可视化编辑，使用 tomlkit 保留注释）"""
            try:
                config_path = get_plugin_config_path(plugin_name)
                
                if not config_path.exists():
                    return PluginConfigSaveResponse(
                        success=False,
                        error="配置文件不存在",
                    )
                
                # 读取当前配置（使用 tomlkit 保留注释）
                content = config_path.read_text(encoding="utf-8")
                parsed = tomlkit.parse(content)
                
                # 应用更新
                updated = apply_updates(parsed, request.updates)
                
                backup_path = None
                
                # 创建备份
                if request.create_backup:
                    backup_dir = config_path.parent / "backups_from_webui"
                    backup_dir.mkdir(exist_ok=True)
                    
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    backup_name = f"config_{timestamp}.toml"
                    backup_file = backup_dir / backup_name
                    
                    shutil.copy2(config_path, backup_file)
                    backup_path = str(backup_file.relative_to(CONFIG_ROOT))
                
                # 保存更新后的配置
                new_content = tomlkit.dumps(updated)
                config_path.write_text(new_content, encoding="utf-8")
                
                logger.info(f"插件配置已更新: {plugin_name}")
                
                return PluginConfigSaveResponse(
                    success=True,
                    message="配置已更新",
                    backup_path=backup_path,
                )
                
            except Exception as e:
                logger.error(f"更新配置失败: {e}", exc_info=True)
                return PluginConfigSaveResponse(
                    success=False,
                    error=str(e),
                )

        # ==================== 重置接口 ====================

        @self.router.post("/{plugin_name}/reset", response_model=PluginConfigSaveResponse)
        async def reset_plugin_config(plugin_name: str, _=VerifiedDep):
            """重置插件配置为默认值"""
            try:
                config_path = get_plugin_config_path(plugin_name)
                
                # 获取默认配置
                defaults = get_plugin_default_config(plugin_name)
                if defaults is None:
                    return PluginConfigSaveResponse(
                        success=False,
                        error="插件未加载或无 Schema 定义",
                    )
                
                backup_path = None
                
                # 备份当前配置
                if config_path.exists():
                    backup_dir = config_path.parent / "backups_from_webui"
                    backup_dir.mkdir(exist_ok=True)
                    
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    backup_name = f"config_prereset_{timestamp}.toml"
                    backup_file = backup_dir / backup_name
                    
                    shutil.copy2(config_path, backup_file)
                    backup_path = str(backup_file.relative_to(CONFIG_ROOT))
                
                # 调用插件的配置生成方法（如果有）
                plugin_instance = plugin_manager.get_plugin_instance(plugin_name)
                if plugin_instance and hasattr(plugin_instance, '_generate_and_save_default_config'):
                    plugin_instance._generate_and_save_default_config(str(config_path))
                else:
                    # 手动生成简单的默认配置
                    config_path.parent.mkdir(parents=True, exist_ok=True)
                    content = toml.dumps(defaults)
                    config_path.write_text(content, encoding="utf-8")
                
                logger.info(f"插件配置已重置: {plugin_name}")
                
                return PluginConfigSaveResponse(
                    success=True,
                    message="配置已重置为默认值",
                    backup_path=backup_path,
                )
                
            except Exception as e:
                logger.error(f"重置配置失败: {e}", exc_info=True)
                return PluginConfigSaveResponse(
                    success=False,
                    error=str(e),
                )

        # ==================== 备份接口 ====================

        @self.router.get("/{plugin_name}/backups", response_model=PluginConfigBackupsResponse)
        async def list_plugin_config_backups(plugin_name: str, _=VerifiedDep):
            """获取插件配置备份列表"""
            try:
                config_path = get_plugin_config_path(plugin_name)
                backup_dir = config_path.parent / "backups_from_webui"
                
                backups: list[PluginConfigBackupInfo] = []
                
                if backup_dir.exists():
                    for backup_file in sorted(backup_dir.iterdir(), reverse=True):
                        if backup_file.is_file() and backup_file.suffix == ".toml":
                            stat = backup_file.stat()
                            backups.append(PluginConfigBackupInfo(
                                name=backup_file.name,
                                path=str(backup_file.relative_to(CONFIG_ROOT)),
                                created_at=datetime.fromtimestamp(
                                    stat.st_mtime
                                ).strftime("%Y-%m-%d %H:%M:%S"),
                                size=stat.st_size,
                            ))
                
                return PluginConfigBackupsResponse(
                    success=True,
                    backups=backups,
                )
                
            except Exception as e:
                logger.error(f"获取备份列表失败: {e}", exc_info=True)
                return PluginConfigBackupsResponse(
                    success=False,
                    backups=[],
                    error=str(e),
                )

        @self.router.post("/{plugin_name}/restore/{backup_name}", response_model=PluginConfigSaveResponse)
        async def restore_plugin_config(
            plugin_name: str,
            backup_name: str,
            _=VerifiedDep,
        ):
            """从备份恢复插件配置"""
            try:
                config_path = get_plugin_config_path(plugin_name)
                backup_dir = config_path.parent / "backups_from_webui"
                backup_file = backup_dir / backup_name
                
                if not backup_file.exists():
                    return PluginConfigSaveResponse(
                        success=False,
                        error="备份文件不存在",
                    )
                
                # 先备份当前配置
                pre_restore_backup = None
                if config_path.exists():
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    pre_restore_name = f"config_prerestore_{timestamp}.toml"
                    pre_restore_file = backup_dir / pre_restore_name
                    shutil.copy2(config_path, pre_restore_file)
                    pre_restore_backup = str(pre_restore_file.relative_to(CONFIG_ROOT))
                
                # 恢复备份
                shutil.copy2(backup_file, config_path)
                
                logger.info(f"插件配置已从备份恢复: {plugin_name} <- {backup_name}")
                
                return PluginConfigSaveResponse(
                    success=True,
                    message=f"配置已从备份 {backup_name} 恢复",
                    backup_path=pre_restore_backup,
                )
                
            except Exception as e:
                logger.error(f"恢复备份失败: {e}", exc_info=True)
                return PluginConfigSaveResponse(
                    success=False,
                    error=str(e),
                )

        # ==================== 验证接口 ====================

        @self.router.post("/{plugin_name}/validate")
        async def validate_plugin_config(
            plugin_name: str,
            content: str,
            _=VerifiedDep,
        ):
            """验证插件配置 TOML 格式"""
            try:
                toml.loads(content)
                return {
                    "success": True,
                    "valid": True,
                    "message": "TOML 格式有效",
                }
            except toml.TomlDecodeError as e:
                return {
                    "success": True,
                    "valid": False,
                    "message": f"TOML 格式错误: {str(e)}",
                    "line": getattr(e, 'lineno', None),
                    "col": getattr(e, 'colno', None),
                }
            except Exception as e:
                return {
                    "success": False,
                    "error": str(e),
                }
