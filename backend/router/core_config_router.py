"""Core 配置管理路由组件

提供 Core 配置的管理接口，包括配置描述生成、配置读取和更新
"""

from typing import Any, Literal
from pathlib import Path
import inspect
import shutil
import datetime

from fastapi import HTTPException
from pydantic import BaseModel
from pydantic_core import PydanticUndefined

from src.kernel.logger import get_logger
from src.core.components.base.router import BaseRouter
from src.core.utils.security import VerifiedDep
from src.core.config import get_core_config
from src.core.config.core_config import CoreConfig, CORE_VERSION

from .core_config_meta import (
    SECTION_ICONS,
    SECTION_NAMES_CN,
    FIELD_NAMES_CN,
    TEXTAREA_TALL_FIELDS,
    SELECT_FIELD_OPTIONS,
    SPECIAL_EDITOR_FIELDS,
)

logger = get_logger(name="CoreConfigRouter", color="blue")

CONFIG_PATH = Path("config/core.toml")
BACKUP_DIR = Path("config/backups")


# ==================== API Models ====================

class ConfigFieldSchema(BaseModel):
    """配置字段 Schema"""
    key: str                                # 字段完整路径，如 "bot.ui_level"
    name: str                               # 显示名称（从 description 提取或使用字段名）
    description: str                        # 详细描述
    type: Literal["string", "number", "boolean", "array", "object", "textarea", "textarea_tall", "select"]
    default: Any | None = None              # 默认值
    placeholder: str | None = None          # 占位符
    options: list[dict[str, Any]] | None = None    # 选项（用于 select 类型）
    min: float | None = None                # 最小值
    max: float | None = None                # 最大值
    step: float | None = None               # 步进值
    readonly: bool = False                  # 是否只读
    advanced: bool = False                  # 是否为高级选项
    specialEditor: str | None = None        # 特殊编辑器类型


class ConfigGroupSchema(BaseModel):
    """配置组 Schema"""
    key: str                                # 组键名
    name: str                               # 组名称
    icon: str                               # 图标
    description: str                        # 组描述
    fields: list[ConfigFieldSchema]         # 字段列表
    expert: bool = False                    # 是否为专家模式组
    hasSpecialEditor: bool = False          # 是否包含特殊编辑器


class ConfigSchemaResponse(BaseModel):
    """配置 Schema 响应"""
    version: str                            # 配置版本
    groups: list[ConfigGroupSchema]         # 配置组列表


class ConfigUpdateRequest(BaseModel):
    """配置更新请求"""
    updates: dict[str, Any]                 # 要更新的配置项，键为点分隔路径


class ConfigUpdateResponse(BaseModel):
    """配置更新响应"""
    success: bool
    message: str
    failed_keys: list[str] | None = None


class ConfigRawResponse(BaseModel):
    """原始配置文件内容响应"""
    success: bool
    content: str
    path: str


class ConfigSaveRawRequest(BaseModel):
    """原始配置文件保存请求"""
    content: str


class ConfigBackupInfo(BaseModel):
    """备份信息"""
    name: str
    path: str
    created_at: str
    size: int


class ConfigBackupsResponse(BaseModel):
    """备份列表响应"""
    success: bool
    backups: list[ConfigBackupInfo]


# ==================== Schema 生成逻辑 ====================

def _python_type_to_field_type(python_type: Any) -> str:
    """将 Python 类型转换为前端字段类型"""
    if python_type is str:
        return "string"
    elif python_type is int or python_type is float:
        return "number"
    elif python_type is bool:
        return "boolean"
    elif hasattr(python_type, "__origin__"):
        origin = python_type.__origin__
        if origin is list:
            return "array"
        elif origin is dict:
            return "object"
    return "string"


def _extract_field_info(section_key: str, field_name: str, field_info: Any) -> ConfigFieldSchema:
    """从 Pydantic Field 提取配置字段信息"""
    
    # 获取字段类型
    field_type = field_info.annotation
    type_str = _python_type_to_field_type(field_type)
    
    # 获取描述
    description = field_info.description or f"{field_name} 配置项"
    
    # 获取默认值
    default_value = None
    if field_info.default is not PydanticUndefined:
        default_value = field_info.default
    elif field_info.default_factory is not None:
        try:
            default_value = field_info.default_factory()
        except Exception:
            pass
    
    # 检测是否应该使用 select（优先级最高，覆盖其他类型推断）
    options = None
    if field_name in SELECT_FIELD_OPTIONS:
        type_str = "select"
        options = SELECT_FIELD_OPTIONS[field_name]

    # 检测是否应该使用 textarea（仅 string 类型，select 字段跳过）
    if type_str == "string":
        if field_name in TEXTAREA_TALL_FIELDS:
            type_str = "textarea_tall"
        elif isinstance(default_value, str) and (len(default_value) > 50 or "\n" in default_value):
            type_str = "textarea"

    # 检测特殊编辑器（SPECIAL_EDITOR_FIELDS 显式指定 > array 自动推断）
    special_editor: str | None = SPECIAL_EDITOR_FIELDS.get(field_name)
    if special_editor is None and type_str == "array":
        if hasattr(field_type, "__args__") and field_type.__args__ and field_type.__args__[0] == str:
            special_editor = "string_array"

    return ConfigFieldSchema(
        key=f"{section_key}.{field_name}",
        name=_field_name_to_display_name(field_name),
        description=description,
        type=type_str,
        default=default_value,
        placeholder=None,
        options=options,
        specialEditor=special_editor,
    )


def _field_name_to_display_name(field_name: str) -> str:
    """将字段名转换为显示名称，优先使用中文映射"""
    return FIELD_NAMES_CN.get(field_name, field_name.replace("_", " ").title())


def _get_section_icon(section_key: str) -> str:
    """根据 section 键名返回合适的图标"""
    return SECTION_ICONS.get(section_key, "lucide:folder")


def _generate_config_schema(config_model: type[CoreConfig]) -> ConfigSchemaResponse:    
    """生成配置 Schema"""
    
    groups: list[ConfigGroupSchema] = []
    
    # 遍历所有配置节
    for section_name, section_field in config_model.model_fields.items():
        # 获取 section 类型
        section_type = section_field.annotation
        
        # 跳过非 SectionBase 的字段
        if not hasattr(section_type, "model_fields"):
            continue
        
        # 获取 section 的配置节名称
        section_key = getattr(section_type, "__config_section_name__", section_name)
        
        # 获取 section 的 docstring 作为描述
        section_doc = inspect.getdoc(section_type) or f"{section_name} 配置"
        section_description = section_doc.split("\n")[0]  # 取第一行作为描述
        
        # 提取所有字段
        fields: list[ConfigFieldSchema] = []
        for field_name, field_info in section_type.model_fields.items():
            field_schema = _extract_field_info(section_key, field_name, field_info)
            fields.append(field_schema)
        
        # 创建配置组
        group = ConfigGroupSchema(
            key=section_key,
            name=SECTION_NAMES_CN.get(section_key, _field_name_to_display_name(section_key)),
            icon=_get_section_icon(section_key),
            description=section_description,
            fields=fields,
        )
        groups.append(group)
    
    return ConfigSchemaResponse(
        version=CORE_VERSION,
        groups=groups,
    )


def _create_backup() -> Path | None:
    """创建当前配置的备份，最多保留 20 份"""
    if not CONFIG_PATH.exists():
        return None
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = BACKUP_DIR / f"core_{ts}.toml"
    shutil.copy2(CONFIG_PATH, backup_file)
    
    # 只保留最新的 20 个备份
    all_backups = sorted(BACKUP_DIR.glob("core_*.toml"), key=lambda p: p.stat().st_mtime, reverse=True)
    for old in all_backups[20:]:
        try:
            old.unlink()
        except Exception:
            pass
    return backup_file


def _list_backups() -> list[ConfigBackupInfo]:
    """列出所有备份文件"""
    if not BACKUP_DIR.exists():
        return []
    result = []
    for f in sorted(BACKUP_DIR.glob("core_*.toml"), key=lambda p: p.stat().st_mtime, reverse=True):
        stat = f.stat()
        result.append(ConfigBackupInfo(
            name=f.name,
            path=str(f),
            created_at=datetime.datetime.fromtimestamp(stat.st_mtime).isoformat(),
            size=stat.st_size,
        ))
    return result


# ==================== Router ====================

class CoreConfigRouter(BaseRouter):
    """Core 配置管理路由组件
    
    提供以下 API 端点：
    - GET  /schema:          获取配置 Schema
    - GET  /config:          获取当前配置（解析后的键值对）
    - PUT  /config:          更新配置（键值对方式）
    - GET  /config/raw:      获取原始 TOML 文件内容
    - POST /config/raw:      保存原始 TOML 文件内容
    - GET  /config/backups:  获取备份列表
    - POST /config/restore:  从备份恢复
    """
    
    router_name = "CoreConfigRouter"
    router_description = "Core 配置管理接口"
    
    custom_route_path = "/webui/api/core-config"
    cors_origins = ["*"]
    
    def register_endpoints(self) -> None:
        """注册所有 HTTP 端点"""
        
        @self.app.get("/schema", summary="获取配置结构描述", response_model=ConfigSchemaResponse)
        async def get_schema(_=VerifiedDep):
            """获取 Core 配置的 Schema 描述"""
            try:
                return _generate_config_schema(CoreConfig)
            except Exception as e:
                logger.error(f"生成配置 Schema 失败: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/config", summary="获取当前配置（键值对）")
        async def get_config(_=VerifiedDep):
            """获取当前的 Core 配置值（解析后的结构）"""
            try:
                config = get_core_config()
                config_dict = {}
                for section_name, section_field in CoreConfig.model_fields.items():
                    section_type = section_field.annotation
                    if not hasattr(section_type, "model_fields"):
                        continue
                    section_key = getattr(section_type, "__config_section_name__", section_name)
                    section_value = getattr(config, section_name)
                    config_dict[section_key] = section_value.model_dump()
                return {"version": CORE_VERSION, "config": config_dict}
            except Exception as e:
                logger.error(f"获取配置失败: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.put("/config", summary="更新配置", response_model=ConfigUpdateResponse)
        async def update_config(request: ConfigUpdateRequest, _=VerifiedDep):
            """更新 Core 配置（键为点分隔路径，如 "bot.ui_level"）"""
            try:
                config = get_core_config()
                failed_keys = []
                
                if not CONFIG_PATH.exists():
                    raise HTTPException(status_code=500, detail="配置文件不存在")
                
                for key, value in request.updates.items():
                    try:
                        parts = key.split(".", 1)
                        if len(parts) != 2:
                            failed_keys.append(key)
                            continue
                        section_key, field_name = parts
                        
                        section_name = None
                        for sn, sf in CoreConfig.model_fields.items():
                            st = sf.annotation
                            if hasattr(st, "__config_section_name__") and getattr(st, "__config_section_name__") == section_key:
                                section_name = sn
                                break
                        
                        if section_name is None or not hasattr(getattr(config, section_name), field_name):
                            failed_keys.append(key)
                            continue
                        
                        setattr(getattr(config, section_name), field_name, value)
                    except Exception as e:
                        logger.error(f"更新配置项 {key} 失败: {e}")
                        failed_keys.append(key)
                
                try:
                    from src.kernel.config.core import _render_toml_with_signature
                    config_dict = {}
                    for section_name, section_field in CoreConfig.model_fields.items():
                        section_type = section_field.annotation
                        if not hasattr(section_type, "model_fields"):
                            continue
                        section_key = getattr(section_type, "__config_section_name__", section_name)
                        config_dict[section_key] = getattr(config, section_name).model_dump()
                    
                    _create_backup()
                    CONFIG_PATH.write_text(_render_toml_with_signature(CoreConfig, config_dict), encoding="utf-8")
                    
                    return ConfigUpdateResponse(
                        success=len(failed_keys) == 0,
                        message="配置更新成功" if not failed_keys else f"部分配置更新失败: {', '.join(failed_keys)}",
                        failed_keys=failed_keys if failed_keys else None,
                    )
                except Exception as e:
                    logger.error(f"保存配置文件失败: {e}")
                    raise HTTPException(status_code=500, detail=f"保存配置失败: {e}")
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"更新配置失败: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/config/raw", summary="获取原始 TOML 内容", response_model=ConfigRawResponse)
        async def get_config_raw(_=VerifiedDep):
            """获取 config/core.toml 的原始文本内容"""
            try:
                if not CONFIG_PATH.exists():
                    raise HTTPException(status_code=404, detail="配置文件不存在")
                content = CONFIG_PATH.read_text(encoding="utf-8")
                return ConfigRawResponse(success=True, content=content, path=str(CONFIG_PATH))
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"读取原始配置失败: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.post("/config/raw", summary="保存原始 TOML 内容")
        async def save_config_raw(request: ConfigSaveRawRequest, _=VerifiedDep):
            """直接保存原始 TOML 文本到 config/core.toml"""
            try:
                # 先验证 TOML 语法
                import tomllib
                try:
                    tomllib.loads(request.content)
                except tomllib.TOMLDecodeError as e:
                    raise HTTPException(status_code=400, detail=f"TOML 语法错误: {e}")
                
                _create_backup()
                CONFIG_PATH.write_text(request.content, encoding="utf-8")
                return {"success": True, "message": "配置已保存"}
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"保存原始配置失败: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/config/backups", summary="获取备份列表", response_model=ConfigBackupsResponse)
        async def get_backups(_=VerifiedDep):
            """获取 Core 配置的所有备份文件列表"""
            try:
                backups = _list_backups()
                return ConfigBackupsResponse(success=True, backups=backups)
            except Exception as e:
                logger.error(f"获取备份列表失败: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.post("/config/restore/{backup_name}", summary="从备份恢复")
        async def restore_backup(backup_name: str, _=VerifiedDep):
            """从指定备份文件恢复 Core 配置"""
            try:
                backup_file = BACKUP_DIR / backup_name
                if not backup_file.exists():
                    raise HTTPException(status_code=404, detail=f"备份文件不存在: {backup_name}")
                
                # 先备份当前配置
                _create_backup()
                
                shutil.copy2(backup_file, CONFIG_PATH)
                return {"success": True, "message": f"已从 {backup_name} 恢复配置"}
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"恢复备份失败: {e}")
                raise HTTPException(status_code=500, detail=str(e))
    async def startup(self) -> None:
        """路由启动钩子"""
        logger.info(f"Core Config 路由已启动，路径: {self.custom_route_path}")
    
    async def shutdown(self) -> None:
        """路由关闭钩子"""
        logger.info("Core Config 路由已关闭")
