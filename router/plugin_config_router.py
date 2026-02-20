"""插件配置管理路由组件

提供插件配置文件的管理接口，包括：
- 获取所有已加载插件的配置文件列表（含 Pydantic Schema）
- 获取指定插件的配置文件原始 TOML 内容（含 Pydantic Schema）
- 更新指定插件的配置文件内容
- 配置备份与恢复
"""

import inspect
import shutil
import datetime
import tomllib
from pathlib import Path
from typing import Any, Literal

from fastapi import HTTPException
from pydantic import BaseModel
from pydantic_core import PydanticUndefined

from src.kernel.logger import get_logger
from src.core.components.base.router import BaseRouter
from src.core.utils.security import VerifiedDep
from src.core.managers import get_plugin_manager
from src.core.managers.config_manager import get_config_manager

logger = get_logger(name="PluginConfigRouter", color="green")

# 配置根目录
PLUGIN_CONFIG_BASE = Path("config/plugins")
BACKUP_DIR = Path("config/backups/plugins")


# ==================== Schema Models ====================


class SchemaField(BaseModel):
    """单个配置字段的 Schema 描述"""
    key: str                                        # 完整路径，如 "section.field"
    name: str                                       # 显示名称
    description: str                                # 描述
    type: Literal["string", "number", "boolean", "array", "object", "textarea", "select"]
    default: Any | None = None
    options: list[dict[str, Any]] | None = None     # select 类型选项


class SchemaSection(BaseModel):
    """配置节 Schema"""
    key: str                                        # section 键名
    name: str                                       # 显示名称
    description: str                                # 描述
    fields: list[SchemaField]


# ==================== API Models ====================


class PluginConfigInfo(BaseModel):
    """插件配置文件信息"""
    plugin_name: str
    display_name: str
    config_path: str
    config_name: str
    size: int
    modified_at: str
    has_config: bool
    config_schema: list[SchemaSection] | None = None       # Pydantic 生成的 Schema（可选）


class PluginConfigListResponse(BaseModel):
    """插件配置列表响应"""
    success: bool
    plugins: list[PluginConfigInfo]
    total: int


class PluginConfigRawResponse(BaseModel):
    """原始配置文件内容响应"""
    success: bool
    content: str
    path: str
    plugin_name: str
    config_schema: list[SchemaSection] | None = None       # Pydantic 生成的 Schema（可选）


class PluginConfigSaveRequest(BaseModel):
    """保存配置请求"""
    content: str


class PluginConfigSaveResponse(BaseModel):
    """保存配置响应"""
    success: bool
    message: str
    backup_path: str | None = None


class PluginBackupInfo(BaseModel):
    """备份信息"""
    name: str
    path: str
    created_at: str
    size: int


class PluginBackupsResponse(BaseModel):
    """备份列表响应"""
    success: bool
    backups: list[PluginBackupInfo]


# ==================== Schema 生成逻辑 ====================


def _py_type_to_field_type(annotation: Any) -> str:
    """将 Python 类型注解转换为前端字段类型字符串"""
    if annotation is str:
        return "string"
    if annotation is int or annotation is float:
        return "number"
    if annotation is bool:
        return "boolean"
    if hasattr(annotation, "__origin__"):
        origin = annotation.__origin__
        if origin is list:
            return "array"
        if origin is dict:
            return "object"
    return "string"


def _extract_schema_field(section_key: str, field_name: str, field_info: Any) -> SchemaField:
    """从 Pydantic FieldInfo 中提取 SchemaField"""
    annotation = field_info.annotation
    type_str = _py_type_to_field_type(annotation)

    description = field_info.description or f"{field_name} 配置项"

    # 获取默认值
    default_value: Any = None
    if field_info.default is not PydanticUndefined:
        default_value = field_info.default
    elif field_info.default_factory is not None:
        try:
            default_value = field_info.default_factory()
        except Exception:
            pass

    # 对于 string 类型，多行或长默认值使用 textarea
    if type_str == "string":
        if isinstance(default_value, str) and (len(default_value) > 60 or "\n" in default_value):
            type_str = "textarea"

    return SchemaField(
        key=f"{section_key}.{field_name}",
        name=field_name.replace("_", " ").title(),
        description=description,
        type=type_str,
        default=default_value,
    )


def _generate_plugin_schema(config_cls: type) -> list[SchemaSection]:
    """从插件配置 Pydantic 类生成 SchemaSection 列表"""
    sections: list[SchemaSection] = []

    for section_name, section_field in config_cls.model_fields.items():
        section_type = section_field.annotation

        # 跳过没有子字段的简单字段
        if not hasattr(section_type, "model_fields"):
            continue

        # section 键名（优先使用 __config_section_name__）
        section_key = getattr(section_type, "__config_section_name__", section_name)

        # section 描述
        doc = inspect.getdoc(section_type) or f"{section_name} 配置"
        section_description = doc.split("\n")[0]

        fields: list[SchemaField] = []
        for field_name, field_info in section_type.model_fields.items():
            try:
                fields.append(_extract_schema_field(section_key, field_name, field_info))
            except Exception as e:
                logger.warning(f"提取字段 {section_key}.{field_name} Schema 失败: {e}")

        sections.append(SchemaSection(
            key=section_key,
            name=section_key.replace("_", " ").title(),
            description=section_description,
            fields=fields,
        ))

    return sections


def _get_plugin_config_schema(plugin_name: str, config_name: str) -> list[SchemaSection] | None:
    """通过注册表获取插件指定 config_name 对应的配置类，生成 Schema。找不到时返回 None。"""
    try:
        from src.core.components.registry import get_global_registry
        from src.core.components.types import ComponentType, parse_signature

        registry = get_global_registry()
        config_classes = registry.get_by_type(ComponentType.CONFIG)
        if not config_classes:
            return None

        for signature, cls in config_classes.items():
            sig_info = parse_signature(signature)
            if sig_info.get("plugin_name") != plugin_name:
                continue
            # config_name 对应 cls.config_name 类属性
            cls_config_name = getattr(cls, "config_name", "config")
            if cls_config_name != config_name:
                continue
            return _generate_plugin_schema(cls)
    except Exception as e:
        logger.warning(f"生成插件 '{plugin_name}/{config_name}' Schema 失败: {e}")
    return None


# ==================== 内部工具函数 ====================


def _get_plugin_config_files(plugin_name: str) -> list[Path]:
    """获取插件的所有 TOML 配置文件"""
    plugin_dir = PLUGIN_CONFIG_BASE / plugin_name
    if not plugin_dir.exists() or not plugin_dir.is_dir():
        return []
    return list(plugin_dir.glob("*.toml"))


def _build_plugin_config_info(plugin_name: str) -> list[PluginConfigInfo]:
    """构建指定插件的配置文件信息列表（含 Schema）。

    若插件目录不存在或没有 .toml 文件，抛出 HTTPException(400)。
    """
    config_files = _get_plugin_config_files(plugin_name)

    if not config_files:
        raise HTTPException(
            status_code=400,
            detail=f"插件 '{plugin_name}' 没有配置文件",
        )

    result: list[PluginConfigInfo] = []
    for config_file in sorted(config_files):
        stat = config_file.stat()
        schema = _get_plugin_config_schema(plugin_name, config_file.stem)
        result.append(PluginConfigInfo(
            plugin_name=plugin_name,
            display_name=plugin_name,
            config_path=str(config_file),
            config_name=config_file.stem,
            size=stat.st_size,
            modified_at=datetime.datetime.fromtimestamp(stat.st_mtime).isoformat(),
            has_config=True,
            config_schema=schema,
        ))

    return result


def _create_plugin_backup(plugin_name: str, config_name: str) -> Path | None:
    """创建指定插件配置文件的备份，最多保留 20 份"""
    config_path = PLUGIN_CONFIG_BASE / plugin_name / f"{config_name}.toml"
    if not config_path.exists():
        return None

    backup_dir = BACKUP_DIR / plugin_name
    backup_dir.mkdir(parents=True, exist_ok=True)

    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = backup_dir / f"{config_name}_{ts}.toml"
    shutil.copy2(config_path, backup_file)

    all_backups = sorted(
        backup_dir.glob(f"{config_name}_*.toml"),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    for old in all_backups[20:]:
        try:
            old.unlink()
        except Exception:
            pass

    return backup_file


def _list_plugin_backups(plugin_name: str, config_name: str) -> list[PluginBackupInfo]:
    """列出指定插件配置文件的所有备份"""
    backup_dir = BACKUP_DIR / plugin_name
    if not backup_dir.exists():
        return []

    result: list[PluginBackupInfo] = []
    for f in sorted(
        backup_dir.glob(f"{config_name}_*.toml"),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    ):
        stat = f.stat()
        result.append(PluginBackupInfo(
            name=f.name,
            path=str(f),
            created_at=datetime.datetime.fromtimestamp(stat.st_mtime).isoformat(),
            size=stat.st_size,
        ))
    return result


# ==================== Router ====================


class PluginConfigRouter(BaseRouter):
    """插件配置管理路由组件

    提供以下 API 端点：
    - GET  /list                                    获取所有已加载插件的配置列表（含 Schema）
    - GET  /list/{plugin_name}                      获取指定插件的配置列表（含 Schema）
    - GET  /raw/{plugin_name}/{config_name}         获取配置文件原始 TOML 内容（含 Schema）
    - POST /raw/{plugin_name}/{config_name}         保存配置文件原始 TOML 内容
    - GET  /backups/{plugin_name}/{config_name}     获取备份列表
    - POST /restore/{plugin_name}/{config_name}/{backup_name}  从备份恢复
    """

    router_name = "PluginConfigRouter"
    router_description = "插件配置文件管理接口"

    custom_route_path = "/webui/api/plugin-config"
    cors_origins = ["*"]

    def register_endpoints(self) -> None:
        """注册所有 HTTP 端点"""

        @self.app.get("/list", summary="获取所有插件配置列表", response_model=PluginConfigListResponse)
        async def get_all_plugin_configs(_=VerifiedDep):
            """获取所有已加载插件的配置文件信息列表（含 Pydantic Schema）"""
            try:
                plugin_manager = get_plugin_manager()
                loaded_plugins = plugin_manager.list_loaded_plugins()

                all_configs: list[PluginConfigInfo] = []
                for pname in loaded_plugins:
                    try:
                        all_configs.extend(_build_plugin_config_info(pname))
                    except HTTPException:
                        pass  # 没有配置文件的插件直接跳过

                return PluginConfigListResponse(
                    success=True,
                    plugins=all_configs,
                    total=len(all_configs),
                )
            except Exception as e:
                logger.error(f"获取插件配置列表失败: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.get("/list/{plugin_name}", summary="获取指定插件的配置列表", response_model=PluginConfigListResponse)
        async def get_plugin_configs(plugin_name: str, _=VerifiedDep):
            """获取指定插件的配置文件信息列表（含 Pydantic Schema）"""
            try:
                plugin_manager = get_plugin_manager()
                if not plugin_manager.is_plugin_loaded(plugin_name):
                    raise HTTPException(status_code=404, detail=f"插件 '{plugin_name}' 未加载或不存在")

                infos = _build_plugin_config_info(plugin_name)
                return PluginConfigListResponse(success=True, plugins=infos, total=len(infos))
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"获取插件 '{plugin_name}' 配置列表失败: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.get(
            "/raw/{plugin_name}/{config_name}",
            summary="获取配置文件原始内容（含 Schema）",
            response_model=PluginConfigRawResponse,
        )
        async def get_plugin_config_raw(plugin_name: str, config_name: str, _=VerifiedDep):
            """获取指定插件配置文件的原始 TOML 内容，同时附带 Pydantic Schema"""
            try:
                plugin_manager = get_plugin_manager()
                if not plugin_manager.is_plugin_loaded(plugin_name):
                    raise HTTPException(status_code=404, detail=f"插件 '{plugin_name}' 未加载或不存在")

                config_path = PLUGIN_CONFIG_BASE / plugin_name / f"{config_name}.toml"
                if not config_path.exists():
                    raise HTTPException(status_code=404, detail=f"配置文件不存在: {config_path}")

                content = config_path.read_text(encoding="utf-8")
                schema = _get_plugin_config_schema(plugin_name, config_name)

                return PluginConfigRawResponse(
                    success=True,
                    content=content,
                    path=str(config_path),
                    plugin_name=plugin_name,
                    config_schema=schema,
                )
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"获取插件 '{plugin_name}/{config_name}' 配置内容失败: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.post(
            "/raw/{plugin_name}/{config_name}",
            summary="保存配置文件原始内容",
            response_model=PluginConfigSaveResponse,
        )
        async def save_plugin_config_raw(
            plugin_name: str,
            config_name: str,
            request: PluginConfigSaveRequest,
            _=VerifiedDep,
        ):
            """保存原始 TOML 内容到指定插件配置文件"""
            try:
                plugin_manager = get_plugin_manager()
                if not plugin_manager.is_plugin_loaded(plugin_name):
                    raise HTTPException(status_code=404, detail=f"插件 '{plugin_name}' 未加载或不存在")

                try:
                    tomllib.loads(request.content)
                except tomllib.TOMLDecodeError as e:
                    raise HTTPException(status_code=400, detail=f"TOML 语法错误: {e}")

                config_path = PLUGIN_CONFIG_BASE / plugin_name / f"{config_name}.toml"
                backup_path: Path | None = None
                if config_path.exists():
                    backup_path = _create_plugin_backup(plugin_name, config_name)

                config_path.parent.mkdir(parents=True, exist_ok=True)
                config_path.write_text(request.content, encoding="utf-8")

                logger.info(f"插件 '{plugin_name}' 配置文件 '{config_name}.toml' 已保存")
                return PluginConfigSaveResponse(
                    success=True,
                    message="配置已保存",
                    backup_path=str(backup_path) if backup_path else None,
                )
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"保存插件 '{plugin_name}/{config_name}' 配置失败: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.get(
            "/backups/{plugin_name}/{config_name}",
            summary="获取备份列表",
            response_model=PluginBackupsResponse,
        )
        async def get_plugin_backups(plugin_name: str, config_name: str, _=VerifiedDep):
            """获取指定插件配置文件的所有备份"""
            try:
                backups = _list_plugin_backups(plugin_name, config_name)
                return PluginBackupsResponse(success=True, backups=backups)
            except Exception as e:
                logger.error(f"获取插件 '{plugin_name}/{config_name}' 备份列表失败: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.post(
            "/restore/{plugin_name}/{config_name}/{backup_name}",
            summary="从备份恢复配置",
        )
        async def restore_plugin_backup(
            plugin_name: str,
            config_name: str,
            backup_name: str,
            _=VerifiedDep,
        ):
            """从指定备份恢复插件配置文件"""
            try:
                backup_file = BACKUP_DIR / plugin_name / backup_name
                if not backup_file.exists():
                    raise HTTPException(status_code=404, detail=f"备份文件不存在: {backup_name}")

                config_path = PLUGIN_CONFIG_BASE / plugin_name / f"{config_name}.toml"
                if config_path.exists():
                    _create_plugin_backup(plugin_name, config_name)

                config_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(backup_file, config_path)

                logger.info(f"插件 '{plugin_name}' 配置 '{config_name}' 已从备份 '{backup_name}' 恢复")
                return {"success": True, "message": f"已从备份 '{backup_name}' 恢复配置"}
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"恢复插件 '{plugin_name}/{config_name}' 配置失败: {e}")
                raise HTTPException(status_code=500, detail=str(e))

    async def startup(self) -> None:
        logger.info(f"Plugin Config 路由已启动，路径: {self.custom_route_path}")

    async def shutdown(self) -> None:
        logger.info("Plugin Config 路由已关闭")


