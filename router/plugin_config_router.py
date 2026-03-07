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
    """单个配置字段的 Schema 描述（完整版）"""

    # === 基础属性 ===
    key: str  # 完整路径，如 "section.field"
    name: str  # 字段名称（英文）
    description: str  # 字段描述

    # === Pydantic  验证约束 ===
    type: Literal[
        "string", "number", "boolean", "array", "object"
    ]  # 基础类型
    default: Any | None = None  # 默认值

    # 数字约束
    min: float | int | None = None  # 最小值（ge）
    max: float | int | None = None  # 最大值（le）
    gt: float | int | None = None  # 大于
    lt: float | int | None = None  # 小于

    # 字符串/列表长度约束
    min_length: int | None = None  # 最小长度
    max_length: int | None = None  # 最大长度

    # 字符串模式
    pattern: str | None = None  # 正则表达式

    # === WebUI 显示增强 ===
    label: str | None = None  # 显示标签
    tag: str | None = None  # 预设标签（前端映射到图标）
    placeholder: str | None = None  # 占位符
    hint: str | None = None  # 帮助提示
    order: int = 0  # 显示顺序
    hidden: bool = False  # 是否隐藏
    disabled: bool = False  # 是否禁用

    # === 输入控件类型 ===
    input_type: Literal[
        "text",
        "password",
        "textarea",
        "number",
        "slider",
        "switch",
        "select",
        "list",
        "json",
        "color",
        "file",
    ] | None = None  # 强制指定的控件类型

    # === 控件特定参数 ===
    rows: int | None = None  # textarea 行数
    step: float | int | None = None  # number/slider 步进
    choices: list[dict[str, Any]] | None = None  # select 选项列表（支持复杂对象）

    # === 列表配置 ===
    item_type: Literal["str", "number", "boolean", "object"] | None = None
    item_fields: dict[str, Any] | None = None  # object 类型的字段定义
    min_items: int | None = None
    max_items: int | None = None

    # === 条件显示 ===
    depends_on: str | None = None  # 依赖的字段名
    depends_value: Any = None  # 依赖字段的期望值


class SchemaSection(BaseModel):
    """配置节 Schema（完整版）"""

    key: str  # section 键名
    name: str  # 显示名称
    description: str  # 描述
    tag: str | None = None  # section 预设标签（前端映射到图标）
    order: int = 0  # 显示顺序
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
    """将 Python 类型注解转换为前端基础类型字符串"""
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


def _infer_input_type(
    base_type: str,
    constraints: dict[str, Any],
    ui_attrs: dict[str, Any],
) -> str:
    """根据类型和约束自动推断最佳输入控件类型。

    Args:
        base_type: 基础类型（string, number, boolean 等）
        constraints: Pydantic 验证约束（ge, le, min_length 等）
        ui_attrs: UI 属性字典（从 json_schema_extra 读取）

    Returns:
        推断的控件类型
    """
    logger.debug(f"[input_type推断] base_type={base_type}, ui_attrs={ui_attrs.keys()}, choices={ui_attrs.get('choices')}")
    
    # 1. 如果用户强制指定了 input_type，直接使用
    if ui_attrs.get("input_type"):
        result = ui_attrs["input_type"]
        logger.debug(f"[input_type推断] 用户强制指定: {result}")
        return result

    # 2. 布尔类型 -> switch
    if base_type == "boolean":
        logger.debug("[input_type推断] boolean -> switch")
        return "switch"

    # 3. 数字类型且有 min/max -> slider
    if base_type == "number":
        if constraints.get("min") is not None and constraints.get("max") is not None:
            logger.debug("[input_type推断] number with min/max -> slider")
            return "slider"
        logger.debug("[input_type推断] number -> number")
        return "number"

    # 4. 字符串类型
    if base_type == "string":
        # 有 choices -> select
        if ui_attrs.get("choices"):
            logger.debug(f"[input_type推断] string with choices={ui_attrs.get('choices')} -> select")
            return "select"
        # 多行或长默认值 -> textarea
        default = constraints.get("default")
        if isinstance(default, str) and (len(default) > 60 or "\n" in default):
            logger.debug("[input_type推断] string with long/multiline default -> textarea")
            return "textarea"
        # 密码字段（根据字段名推断）
        field_name = ui_attrs.get("name", "").lower()
        if any(
            kw in field_name
            for kw in ["password", "secret", "token", "key", "api"]
        ):
            logger.debug(f"[input_type推断] string with password-like name '{field_name}' -> password")
            return "password"
        logger.debug("[input_type推断] string -> text")
        return "text"

    # 5. 列表 -> list
    if base_type == "array":
        logger.debug("[input_type推断] array -> list")
        return "list"

    # 6. 对象 -> json
    if base_type == "object":
        logger.debug("[input_type推断] object -> json")
        return "json"

    # 默认 text
    logger.debug(f"[input_type推断] unknown type '{base_type}' -> text (fallback)")
    return "text"


def _extract_schema_field(
    section_key: str, field_name: str, field_info: Any
) -> SchemaField:
    """从 Pydantic FieldInfo 中提取完整的 SchemaField。

    读取：
    1. Pydantic 原生约束（ge, le, min_length, max_length, pattern 等）
    2. json_schema_extra 中的自定义 UI 属性
    3. 自动推断最佳控件类型
    """
    annotation = field_info.annotation
    base_type = _py_type_to_field_type(annotation)

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

    # 读取 Pydantic 原生约束
    constraints = field_info.metadata[0].__dict__ if field_info.metadata else {}
    pydantic_constraints = {
        "min": constraints.get("ge"),
        "max": constraints.get("le"),
        "gt": constraints.get("gt"),
        "lt": constraints.get("lt"),
        "min_length": constraints.get("min_length"),
        "max_length": constraints.get("max_length"),
        "pattern": constraints.get("pattern"),
        "default": default_value,
    }

    # 读取自定义 UI 属性（从 json_schema_extra）
    ui_attrs = field_info.json_schema_extra or {}
    
    logger.debug(f"[提取字段Schema] {section_key}.{field_name}: base_type={base_type}, ui_attrs={ui_attrs}")

    # 推断控件类型
    input_type = _infer_input_type(base_type, pydantic_constraints, ui_attrs)
    logger.debug(f"[提取字段Schema] {section_key}.{field_name}: 推断得到 input_type={input_type}")

    # 处理 choices（如果有）
    choices = ui_attrs.get("choices")
    logger.debug(f"[提取字段Schema] {section_key}.{field_name}: 原始 choices={choices}")
    
    if choices and len(choices) > 0 and not isinstance(choices[0], dict):
        # 简单值列表转换为 {label, value} 格式
        choices = [{"label": str(c), "value": c} for c in choices]
        logger.debug(f"[提取字段Schema] {section_key}.{field_name}: 转换后 choices={choices}")

    result = SchemaField(
        # 基础
        key=f"{section_key}.{field_name}",
        name=field_name,
        description=description,
        type=base_type,
        default=default_value,
        # Pydantic 约束
        min=pydantic_constraints.get("min"),
        max=pydantic_constraints.get("max"),
        gt=pydantic_constraints.get("gt"),
        lt=pydantic_constraints.get("lt"),
        min_length=pydantic_constraints.get("min_length"),
        max_length=pydantic_constraints.get("max_length"),
        pattern=pydantic_constraints.get("pattern"),
        # UI 显示
        label=ui_attrs.get("label"),
        tag=ui_attrs.get("tag"),
        placeholder=ui_attrs.get("placeholder"),
        hint=ui_attrs.get("hint"),
        order=ui_attrs.get("order", 0),
        hidden=ui_attrs.get("hidden", False),
        disabled=ui_attrs.get("disabled", False),
        # 控件
        input_type=input_type,
        rows=ui_attrs.get("rows"),
        step=ui_attrs.get("step"),
        choices=choices,
        # 列表
        item_type=ui_attrs.get("item_type"),
        item_fields=ui_attrs.get("item_fields"),
        min_items=ui_attrs.get("min_items"),
        max_items=ui_attrs.get("max_items"),
        # 条件显示
        depends_on=ui_attrs.get("depends_on"),
        depends_value=ui_attrs.get("depends_value"),
    )
    logger.debug(f"[提取字段Schema] {section_key}.{field_name}: 最终生成 SchemaField(type={result.type}, input_type={result.input_type}, choices={result.choices})")
    return result


def _generate_plugin_schema(config_cls: type) -> list[SchemaSection]:
    """从插件配置 Pydantic 类生成 SchemaSection 列表。

    读取：
    1. config_section 装饰器设置的 section 元数据（title, description, tag, order）
    2. 每个 section 下的字段定义（通过 _extract_schema_field）
    """
    sections: list[SchemaSection] = []

    for section_name, section_field in config_cls.model_fields.items():
        section_type = section_field.annotation

        # 跳过没有子字段的简单字段
        if not hasattr(section_type, "model_fields"):
            continue

        # section 键名（从装饰器读取）
        section_key = getattr(section_type, "__config_section_name__", section_name)

        # 从装饰器读取 section 元数据
        section_title_from_decorator = getattr(section_type, "__config_section_title__", None)
        section_description_from_decorator = getattr(section_type, "__config_section_description__", None)
        section_tag = getattr(section_type, "__config_section_tag__", None)
        section_order = getattr(section_type, "__config_section_order__", 0)

        # section title（优先级：装饰器 title > section_key 美化）
        section_title = section_title_from_decorator or section_key.replace("_", " ").title()

        # section 描述（优先级：装饰器 description > docstring 首行 > 默认文本）
        if section_description_from_decorator:
            section_description = section_description_from_decorator
        else:
            doc = inspect.getdoc(section_type) or ""
            section_description = doc.split("\n")[0] if doc else f"{section_key} 配置"

        # 提取字段
        fields: list[SchemaField] = []
        for field_name, field_info in section_type.model_fields.items():
            try:
                fields.append(_extract_schema_field(section_key, field_name, field_info))
            except Exception as e:
                logger.warning(f"提取字段 {section_key}.{field_name} Schema 失败: {e}")

        # 按 order 排序字段
        fields.sort(key=lambda f: f.order)

        sections.append(
            SchemaSection(
                key=section_key,
                name=section_title,
                description=section_description,
                tag=section_tag,
                order=section_order,
                fields=fields,
            )
        )

    # 按 order 排序 sections
    sections.sort(key=lambda s: s.order)

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


