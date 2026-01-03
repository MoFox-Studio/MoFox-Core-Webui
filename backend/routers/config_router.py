"""
配置管理路由组件
提供配置文件的读取、修改、备份等API接口
"""

import re
import shutil
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Optional
from urllib.parse import unquote

import toml
import tomlkit
from pydantic import BaseModel

from src.common.logger import get_logger
from src.common.security import VerifiedDep
from src.config.config import CONFIG_DIR
from src.plugin_system import BaseRouterComponent
from src.plugin_system.core.plugin_manager import plugin_manager

logger = get_logger("WebUI.ConfigRouter")

# 配置文件根目录
CONFIG_ROOT = Path(CONFIG_DIR)


# ==================== 响应模型 ====================

class ConfigFileInfo(BaseModel):
    """配置文件信息"""
    name: str  # 文件名（不含路径）
    display_name: str  # 显示名称
    path: str  # 相对于配置根目录的路径
    type: str  # 类型：main（主配置）, model（模型配置）, plugin（插件配置）
    plugin_name: Optional[str] = None  # 如果是插件配置，关联的插件名
    description: Optional[str] = None  # 描述
    last_modified: Optional[str] = None  # 最后修改时间


class ConfigListResponse(BaseModel):
    """配置文件列表响应"""
    configs: list[ConfigFileInfo]
    total: int


class ConfigContentResponse(BaseModel):
    """配置文件内容响应"""
    success: bool
    path: str
    content: Optional[str] = None  # TOML 原始内容
    parsed: Optional[dict] = None  # 解析后的内容
    error: Optional[str] = None


class ConfigSchemaField(BaseModel):
    """配置字段模式"""
    key: str
    type: str  # string, number, boolean, array, object
    value: Any
    description: Optional[str] = None
    section: str  # 所属的 section


class ConfigSchemaResponse(BaseModel):
    """配置模式响应"""
    success: bool
    path: str
    sections: list[dict]  # 包含 section 名称和字段
    error: Optional[str] = None


class SaveConfigRequest(BaseModel):
    """保存配置请求"""
    content: str  # TOML 原始内容
    create_backup: bool = True  # 是否创建备份


class SaveConfigResponse(BaseModel):
    """保存配置响应"""
    success: bool
    message: Optional[str] = None
    backup_path: Optional[str] = None
    error: Optional[str] = None


class UpdateConfigRequest(BaseModel):
    """更新配置请求（可视化编辑用）"""
    updates: dict  # 键值对更新
    create_backup: bool = True


class ConfigBackupInfo(BaseModel):
    """配置备份信息"""
    name: str
    path: str
    created_at: str
    size: int


class ConfigBackupsResponse(BaseModel):
    """配置备份列表响应"""
    success: bool
    backups: list[ConfigBackupInfo]
    error: Optional[str] = None


# ==================== 工具函数 ====================

def get_plugin_display_name(plugin_folder: str) -> str:
    """
    获取插件的显示名称
    尝试从插件元数据获取，否则美化文件夹名
    """
    from src.plugin_system.core.component_registry import component_registry
    
    try:
        plugin_info = component_registry.get_plugin_info(plugin_folder)
        if plugin_info and plugin_info.display_name:
            return plugin_info.display_name
    except Exception:
        pass
    
    # 美化文件夹名称
    name = plugin_folder.replace("_plugin", "").replace("_", " ").title()
    return name


def parse_toml_comments(content: str) -> dict[str, str]:
    """
    解析 TOML 文件中的注释，提取字段描述
    返回字典：{section.key: description}
    """
    comments = {}
    current_section = ""
    lines = content.split("\n")
    pending_comment = []
    
    for line in lines:
        line_stripped = line.strip()
        
        # 匹配 section 头
        section_match = re.match(r'^\[+([^\]]+)\]+', line_stripped)
        if section_match:
            current_section = section_match.group(1).strip()
            pending_comment = []
            continue
        
        # 匹配注释行
        if line_stripped.startswith("#"):
            comment = line_stripped.lstrip("#").strip()
            pending_comment.append(comment)
            continue
        
        # 匹配键值对
        kv_match = re.match(r'^([a-zA-Z_][a-zA-Z0-9_]*)\s*=', line_stripped)
        if kv_match:
            key = kv_match.group(1)
            full_key = f"{current_section}.{key}" if current_section else key
            if pending_comment:
                comments[full_key] = " ".join(pending_comment)
            pending_comment = []
            continue
        
        # 空行重置注释
        if not line_stripped:
            pending_comment = []
    
    return comments


def get_field_type(value: Any) -> str:
    """获取值的类型名"""
    if isinstance(value, bool):
        return "boolean"
    elif isinstance(value, int):
        return "integer"
    elif isinstance(value, float):
        return "number"
    elif isinstance(value, str):
        return "string"
    elif isinstance(value, list):
        return "array"
    elif isinstance(value, dict):
        return "object"
    return "unknown"


def toml_to_schema(parsed: dict, comments: dict, prefix: str = "") -> list[ConfigSchemaField]:
    """将解析后的 TOML 转换为字段模式列表"""
    fields = []
    
    for key, value in parsed.items():
        full_key = f"{prefix}.{key}" if prefix else key
        section = prefix if prefix else "root"
        
        if isinstance(value, dict) and not any(isinstance(v, dict) for v in value.values()):
            # 普通字典，展开为字段
            for sub_key, sub_value in value.items():
                sub_full_key = f"{full_key}.{sub_key}"
                fields.append(ConfigSchemaField(
                    key=sub_key,
                    type=get_field_type(sub_value),
                    value=sub_value,
                    description=comments.get(sub_full_key),
                    section=full_key
                ))
        elif isinstance(value, dict):
            # 嵌套字典，递归处理
            fields.extend(toml_to_schema(value, comments, full_key))
        else:
            fields.append(ConfigSchemaField(
                key=key,
                type=get_field_type(value),
                value=value,
                description=comments.get(full_key),
                section=section
            ))
    
    return fields


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
                # 两边都是列表，需要特殊处理
                # 对于数组，逐个元素合并或替换
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
    支持点号分隔的键路径，如 "database.host" 或 "api_providers.0.name"
    支持 tomlkit 文档对象以保留注释
    
    ⚠️ 重要：当 value 是 dict 时，使用深度合并而不是直接替换，以保留注释
    """
    result = original  # 不复制，直接修改以保留 tomlkit 结构
    
    for key_path, value in updates.items():
        keys = key_path.split(".")
        current = result
        
        # 遍历到倒数第二层
        for i, key in enumerate(keys[:-1]):
            # 检查是否是数组索引
            if key.isdigit():
                idx = int(key)
                if isinstance(current, list) and idx < len(current):
                    current = current[idx]
                else:
                    break
            else:
                if key not in current:
                    # 检查下一个键是否是数字，决定创建 dict 还是 list
                    # 使用 tomlkit 对象以保留注释格式
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


# ==================== HTTP路由组件 ====================

class WebUIConfigRouter(BaseRouterComponent):
    """
    WebUI配置管理路由组件
    
    提供以下API端点：
    - GET /list: 获取所有配置文件列表
    - GET /content/{path}: 获取配置文件内容
    - GET /schema/{path}: 获取配置文件的结构化模式
    - POST /save/{path}: 保存配置文件（原始TOML）
    - POST /update/{path}: 更新配置文件（可视化编辑）
    - GET /backups/{path}: 获取配置文件的备份列表
    - POST /restore/{path}: 从备份恢复配置
    """
    
    component_name = "config"
    component_description = "WebUI配置管理接口"
    
    def register_endpoints(self) -> None:
        """注册所有HTTP端点"""
        
        @self.router.get("/list", summary="获取配置文件列表", response_model=ConfigListResponse)
        def list_configs(_=VerifiedDep):
            """
            获取所有可管理的配置文件列表
            
            返回：
            - 主配置文件（bot_config.toml）
            - 模型配置文件（model_config.toml）
            - 所有插件配置文件
            """
            try:
                configs = []
                
                # 主配置文件
                bot_config_path = CONFIG_ROOT / "bot_config.toml"
                if bot_config_path.exists():
                    stat = bot_config_path.stat()
                    configs.append(ConfigFileInfo(
                        name="bot_config.toml",
                        display_name="机器人主配置",
                        path="bot_config.toml",
                        type="main",
                        description="MoFox-Bot 的核心配置文件，包含数据库、权限、人格等设置",
                        last_modified=datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S")
                    ))
                
                # 模型配置文件
                model_config_path = CONFIG_ROOT / "model_config.toml"
                if model_config_path.exists():
                    stat = model_config_path.stat()
                    configs.append(ConfigFileInfo(
                        name="model_config.toml",
                        display_name="模型配置",
                        path="model_config.toml",
                        type="model",
                        description="API服务商和模型配置，用于配置 LLM 调用",
                        last_modified=datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S")
                    ))
                
                # 插件配置文件
                plugins_dir = CONFIG_ROOT / "plugins"
                if plugins_dir.exists():
                    for plugin_folder in sorted(plugins_dir.iterdir()):
                        if plugin_folder.is_dir():
                            config_file = plugin_folder / "config.toml"
                            if config_file.exists():
                                plugin_name = plugin_folder.name
                                
                                # 只列出已成功注册的插件配置文件
                                if plugin_name not in plugin_manager.loaded_plugins:
                                    logger.debug(f"跳过未注册的插件配置: {plugin_name}")
                                    continue
                                
                                stat = config_file.stat()
                                display_name = get_plugin_display_name(plugin_name)
                                
                                configs.append(ConfigFileInfo(
                                    name="config.toml",
                                    display_name=f"{display_name} 配置",
                                    path=f"plugins/{plugin_name}/config.toml",
                                    type="plugin",
                                    plugin_name=plugin_name,
                                    description=f"{display_name} 插件的配置文件",
                                    last_modified=datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S")
                                ))
                
                return ConfigListResponse(configs=configs, total=len(configs))
            
            except Exception as e:
                logger.error(f"获取配置列表失败: {e}")
                return ConfigListResponse(configs=[], total=0)
        
        @self.router.get("/content/{path:path}", summary="获取配置文件内容")
        def get_config_content(path: str, _=VerifiedDep):
            """
            获取指定配置文件的内容
            
            Args:
                path: 配置文件相对路径
            
            返回：
            - 原始 TOML 内容
            - 解析后的字典
            """
            try:
                # URL解码路径
                path = unquote(path)
                
                # 安全检查：防止路径遍历
                config_path = CONFIG_ROOT / path
                config_path = config_path.resolve()
                
                if not str(config_path).startswith(str(CONFIG_ROOT.resolve())):
                    return ConfigContentResponse(
                        success=False,
                        path=path,
                        error="非法路径"
                    )
                
                if not config_path.exists():
                    return ConfigContentResponse(
                        success=False,
                        path=path,
                        error="配置文件不存在"
                    )
                
                content = config_path.read_text(encoding="utf-8")
                parsed = toml.loads(content)
                
                return ConfigContentResponse(
                    success=True,
                    path=path,
                    content=content,
                    parsed=parsed
                )
            
            except toml.TomlDecodeError as e:
                logger.error(f"TOML 解析失败: {e}")
                return ConfigContentResponse(
                    success=False,
                    path=path,
                    error=f"TOML 格式错误: {str(e)}"
                )
            except Exception as e:
                logger.error(f"读取配置失败: {e}")
                return ConfigContentResponse(
                    success=False,
                    path=path,
                    error=str(e)
                )
        
        @self.router.get("/schema/{path:path}", summary="获取配置文件结构")
        def get_config_schema(path: str, _=VerifiedDep):
            """
            获取配置文件的结构化模式，用于可视化编辑
            
            Args:
                path: 配置文件相对路径
            
            返回：
            - 按 section 分组的字段列表
            - 每个字段包含：键名、类型、当前值、描述
            """
            try:
                # URL解码路径
                path = unquote(path)
                
                # 安全检查
                config_path = CONFIG_ROOT / path
                config_path = config_path.resolve()
                
                if not str(config_path).startswith(str(CONFIG_ROOT.resolve())):
                    return ConfigSchemaResponse(
                        success=False,
                        path=path,
                        sections=[],
                        error="非法路径"
                    )
                
                if not config_path.exists():
                    return ConfigSchemaResponse(
                        success=False,
                        path=path,
                        sections=[],
                        error="配置文件不存在"
                    )
                
                content = config_path.read_text(encoding="utf-8")
                parsed = toml.loads(content)
                comments = parse_toml_comments(content)
                
                # 按 section 组织字段
                sections_dict: dict[str, list] = {}
                
                def process_dict(d: dict, prefix: str = ""):
                    for key, value in d.items():
                        full_key = f"{prefix}.{key}" if prefix else key
                        
                        if isinstance(value, dict):
                            # 检查是否是纯值字典（所有值都是基本类型）
                            is_leaf_dict = all(
                                not isinstance(v, dict) or (isinstance(v, dict) and not v)
                                for v in value.values()
                            )
                            
                            if is_leaf_dict and value:
                                # 作为一个 section 处理
                                section_name = full_key
                                if section_name not in sections_dict:
                                    sections_dict[section_name] = []
                                
                                for sub_key, sub_value in value.items():
                                    sub_full_key = f"{full_key}.{sub_key}"
                                    sections_dict[section_name].append({
                                        "key": sub_key,
                                        "full_key": sub_full_key,
                                        "type": get_field_type(sub_value),
                                        "value": sub_value,
                                        "description": comments.get(sub_full_key, "")
                                    })
                            else:
                                # 递归处理嵌套字典
                                process_dict(value, full_key)
                        elif isinstance(value, list) and value and isinstance(value[0], dict):
                            # 数组中包含字典（如 [[api_providers]]）
                            section_name = full_key
                            if section_name not in sections_dict:
                                sections_dict[section_name] = []
                            
                            sections_dict[section_name].append({
                                "key": key,
                                "full_key": full_key,
                                "type": "array_of_objects",
                                "value": value,
                                "description": comments.get(full_key, ""),
                                "items_count": len(value)
                            })
                        else:
                            # 根级别的字段
                            section_name = prefix if prefix else "root"
                            if section_name not in sections_dict:
                                sections_dict[section_name] = []
                            
                            sections_dict[section_name].append({
                                "key": key,
                                "full_key": full_key,
                                "type": get_field_type(value),
                                "value": value,
                                "description": comments.get(full_key, "")
                            })
                
                process_dict(parsed)
                
                # 转换为列表格式
                sections = [
                    {
                        "name": name,
                        "display_name": name.replace("_", " ").title(),
                        "fields": fields
                    }
                    for name, fields in sections_dict.items()
                ]
                
                return ConfigSchemaResponse(
                    success=True,
                    path=path,
                    sections=sections
                )
            
            except Exception as e:
                logger.error(f"获取配置结构失败: {e}")
                return ConfigSchemaResponse(
                    success=False,
                    path=path,
                    sections=[],
                    error=str(e)
                )
        
        @self.router.post("/save/{path:path}", summary="保存配置文件")
        def save_config(path: str, request: SaveConfigRequest, _=VerifiedDep):
            """
            保存配置文件（原始 TOML 内容）
            
            Args:
                path: 配置文件相对路径
                request: 包含 TOML 内容和备份选项
            """
            try:
                # URL解码路径
                path = unquote(path)
                                # URL解码路径
                path = unquote(path)
                                # 安全检查
                config_path = CONFIG_ROOT / path
                config_path = config_path.resolve()
                
                if not str(config_path).startswith(str(CONFIG_ROOT.resolve())):
                    return SaveConfigResponse(
                        success=False,
                        error="非法路径"
                    )
                
                # 验证 TOML 格式（使用 tomlkit 保留注释和格式）
                try:
                    tomlkit.parse(request.content)
                except Exception as e:
                    return SaveConfigResponse(
                        success=False,
                        error=f"TOML 格式错误: {str(e)}"
                    )
                
                backup_path = None
                
                # 创建备份
                if request.create_backup and config_path.exists():
                    backup_dir = config_path.parent / "backups_from_webui"
                    backup_dir.mkdir(exist_ok=True)
                    
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    backup_name = f"{config_path.stem}_{timestamp}{config_path.suffix}"
                    backup_file = backup_dir / backup_name
                    
                    shutil.copy2(config_path, backup_file)
                    backup_path = str(backup_file.relative_to(CONFIG_ROOT))
                    logger.info(f"配置备份已创建: {backup_path}")
                
                # 保存配置
                config_path.parent.mkdir(parents=True, exist_ok=True)
                config_path.write_text(request.content, encoding="utf-8")
                
                logger.info(f"配置文件已保存: {path}")
                
                return SaveConfigResponse(
                    success=True,
                    message="配置已保存",
                    backup_path=backup_path
                )
            
            except Exception as e:
                logger.error(f"保存配置失败: {e}")
                return SaveConfigResponse(
                    success=False,
                    error=str(e)
                )
        
        @self.router.post("/update/{path:path}", summary="更新配置（可视化编辑）")
        def update_config(path: str, request: UpdateConfigRequest, _=VerifiedDep):
            """
            更新配置文件的特定字段（用于可视化编辑）
            使用 tomlkit 保留原始文件的注释和格式
            
            Args:
                path: 配置文件相对路径
                request: 包含更新的键值对
            """
            try:
                # URL解码路径
                path = unquote(path)
                
                # 安全检查
                config_path = CONFIG_ROOT / path
                config_path = config_path.resolve()
                
                if not str(config_path).startswith(str(CONFIG_ROOT.resolve())):
                    return SaveConfigResponse(
                        success=False,
                        error="非法路径"
                    )
                
                if not config_path.exists():
                    return SaveConfigResponse(
                        success=False,
                        error="配置文件不存在"
                    )
                
                # 读取当前配置（使用 tomlkit 保留注释）
                content = config_path.read_text(encoding="utf-8")
                parsed = tomlkit.parse(content)
                
                # 应用更新（tomlkit 文档对象会保留注释）
                updated = apply_updates(parsed, request.updates)
                
                backup_path = None
                
                # 创建备份
                if request.create_backup:
                    backup_dir = config_path.parent / "backups_from_webui"
                    backup_dir.mkdir(exist_ok=True)
                    
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    backup_name = f"{config_path.stem}_{timestamp}{config_path.suffix}"
                    backup_file = backup_dir / backup_name
                    
                    shutil.copy2(config_path, backup_file)
                    backup_path = str(backup_file.relative_to(CONFIG_ROOT))
                
                # 保存更新后的配置（使用 tomlkit.dumps 保留注释）
                new_content = tomlkit.dumps(updated)
                config_path.write_text(new_content, encoding="utf-8")
                
                logger.info(f"配置文件已更新: {path}")
                
                return SaveConfigResponse(
                    success=True,
                    message="配置已更新",
                    backup_path=backup_path
                )
            
            except Exception as e:
                logger.error(f"更新配置失败: {e}")
                return SaveConfigResponse(
                    success=False,
                    error=str(e)
                )
        
        @self.router.get("/backups/{path:path}", summary="获取配置备份列表")
        def list_backups(path: str, _=VerifiedDep):
            """
            获取指定配置文件的备份列表
            
            Args:
                path: 配置文件相对路径
            """
            try:
                # URL解码路径
                path = unquote(path)
                
                # 安全检查
                config_path = CONFIG_ROOT / path
                config_path = config_path.resolve()
                
                if not str(config_path).startswith(str(CONFIG_ROOT.resolve())):
                    return ConfigBackupsResponse(
                        success=False,
                        backups=[],
                        error="非法路径"
                    )
                
                backup_dir = config_path.parent / "backups_from_webui"
                backups = []
                
                if backup_dir.exists():
                    config_stem = config_path.stem
                    for backup_file in sorted(backup_dir.iterdir(), reverse=True):
                        if backup_file.is_file() and backup_file.name.startswith(config_stem):
                            stat = backup_file.stat()
                            backups.append(ConfigBackupInfo(
                                name=backup_file.name,
                                path=str(backup_file.relative_to(CONFIG_ROOT)),
                                created_at=datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S"),
                                size=stat.st_size
                            ))
                
                return ConfigBackupsResponse(
                    success=True,
                    backups=backups
                )
            
            except Exception as e:
                logger.error(f"获取备份列表失败: {e}")
                return ConfigBackupsResponse(
                    success=False,
                    backups=[],
                    error=str(e)
                )
        
        @self.router.post("/restore/{path:path}", summary="从备份恢复配置")
        def restore_backup(path: str, backup_name: str, _=VerifiedDep):
            """
            从备份恢复配置文件
            
            Args:
                path: 配置文件相对路径
                backup_name: 备份文件名
            """
            try:
                # 安全检查
                config_path = CONFIG_ROOT / path
                config_path = config_path.resolve()
                
                if not str(config_path).startswith(str(CONFIG_ROOT.resolve())):
                    return SaveConfigResponse(
                        success=False,
                        error="非法路径"
                    )
                
                backup_dir = config_path.parent / "backups_from_webui"
                backup_file = backup_dir / backup_name
                
                if not backup_file.exists():
                    return SaveConfigResponse(
                        success=False,
                        error="备份文件不存在"
                    )
                
                # 先备份当前配置
                if config_path.exists():
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    pre_restore_name = f"{config_path.stem}_prerestore_{timestamp}{config_path.suffix}"
                    pre_restore_file = backup_dir / pre_restore_name
                    shutil.copy2(config_path, pre_restore_file)
                
                # 恢复备份
                shutil.copy2(backup_file, config_path)
                
                logger.info(f"配置已从备份恢复: {backup_name}")
                
                return SaveConfigResponse(
                    success=True,
                    message=f"配置已从备份 {backup_name} 恢复"
                )
            
            except Exception as e:
                logger.error(f"恢复备份失败: {e}")
                return SaveConfigResponse(
                    success=False,
                    error=str(e)
                )
        
        @self.router.post("/validate", summary="验证TOML内容")
        def validate_toml(content: str, _=VerifiedDep):
            """
            验证 TOML 内容是否有效
            
            Args:
                content: TOML 内容
            """
            try:
                toml.loads(content)
                return {"success": True, "valid": True, "message": "TOML 格式有效"}
            except toml.TomlDecodeError as e:
                return {
                    "success": True,
                    "valid": False,
                    "message": f"TOML 格式错误: {str(e)}",
                    "line": getattr(e, 'lineno', None),
                    "col": getattr(e, 'colno', None)
                }
            except Exception as e:
                return {"success": False, "error": str(e)}
