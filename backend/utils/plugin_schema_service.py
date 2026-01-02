"""
插件配置 Schema 解析服务
用于从插件实例解析 config_schema，转换为前端可用的增强 Schema
"""

from typing import Any

from src.common.logger import get_logger
from src.plugin_system.base.config_types import ConfigField
from src.plugin_system.core.plugin_manager import plugin_manager

logger = get_logger("WebUI.PluginSchemaService")


def infer_input_type(field_obj: ConfigField) -> str:
    """
    根据 ConfigField 属性推断输入控件类型
    
    推断规则（按优先级）：
    1. 如果指定了 input_type，直接使用
    2. bool 类型 → switch
    3. int/float + min/max → slider
    4. int/float → number  
    5. 有 choices → select
    6. list 类型 → list
    7. dict 类型 → json
    8. 默认 → text
    """
    # 1. 显式指定（未来扩展 ConfigField 后支持）
    input_type = getattr(field_obj, 'input_type', None)
    if input_type:
        return input_type
    
    # 2. 布尔类型
    if field_obj.type is bool:
        return "switch"
    
    # 3/4. 数字类型
    if field_obj.type in (int, float):
        # 检查是否有 min/max（未来扩展后支持）
        field_min = getattr(field_obj, 'min', None)
        field_max = getattr(field_obj, 'max', None)
        if field_min is not None and field_max is not None:
            return "slider"
        return "number"
    
    # 5. 有选项列表
    if field_obj.choices and len(field_obj.choices) > 0:
        return "select"
    
    # 6. 列表类型
    if field_obj.type is list:
        return "list"
    
    # 7. 字典类型
    if field_obj.type is dict:
        return "json"
    
    # 8. 默认文本
    return "text"


def get_type_name(field_type: Any) -> str:
    """获取类型的字符串名称"""
    if hasattr(field_type, '__name__'):
        return field_type.__name__
    return str(field_type)


def extract_field_schema(field_name: str, field_obj: ConfigField, section: str) -> dict[str, Any]:
    """
    从 ConfigField 提取完整的 Schema 信息
    
    Args:
        field_name: 字段名
        field_obj: ConfigField 实例
        section: 所属 section 名称
    
    Returns:
        包含字段所有信息的字典
    """
    schema: dict[str, Any] = {
        # 基础属性
        "key": field_name,
        "section": section,
        "type": get_type_name(field_obj.type),
        "default": field_obj.default,
        "description": field_obj.description,
        "required": field_obj.required,
        "example": field_obj.example,
        
        # 推断的输入类型
        "input_type": infer_input_type(field_obj),
    }
    
    # choices 处理
    if field_obj.choices:
        schema["choices"] = list(field_obj.choices)
    
    # 未来扩展属性（当 ConfigField 添加新属性后自动支持）
    optional_attrs = [
        # UI 属性
        'label', 'placeholder', 'hint', 'icon', 'hidden', 'disabled', 'order', 'rows',
        # 验证属性
        'min', 'max', 'step', 'pattern', 'max_length', 'min_length',
        # 条件显示
        'group', 'depends_on', 'depends_value',
        # 列表专用
        'item_type', 'item_fields', 'min_items', 'max_items',
    ]
    
    for attr in optional_attrs:
        if hasattr(field_obj, attr):
            value = getattr(field_obj, attr)
            if value is not None:
                schema[attr] = value
    
    return schema


def parse_plugin_schema(plugin_name: str) -> dict[str, Any] | None:
    """
    解析指定插件的完整配置 Schema
    
    Args:
        plugin_name: 插件名称
    
    Returns:
        {
            "schema": { section_name: [field_schemas...] },
            "sections": [ section_meta... ],
            "layout": layout_config or None
        }
        如果插件不存在或无 schema，返回 None
    """
    # 获取插件实例
    plugin_instance = plugin_manager.get_plugin_instance(plugin_name)
    if not plugin_instance:
        logger.warning(f"插件未加载: {plugin_name}")
        return None
    
    logger.info(f"正在解析插件 Schema: {plugin_name}")
    
    # 获取 config_schema
    config_schema = getattr(plugin_instance, 'config_schema', {})
    if not config_schema:
        logger.debug(f"插件 {plugin_name} 没有定义 config_schema")
        return {
            "schema": {},
            "sections": [],
            "layout": None
        }
    
    logger.info(f"插件 {plugin_name} 的 config_schema 包含 {len(config_schema)} 个 section: {list(config_schema.keys())}")
    
    # 获取 section 描述
    section_descriptions = getattr(plugin_instance, 'config_section_descriptions', {})
    
    # 获取布局配置（未来扩展）
    config_layout = getattr(plugin_instance, 'config_layout', None)
    
    # 解析 schema
    schema: dict[str, list[dict[str, Any]]] = {}
    
    for section_name, fields in config_schema.items():
        if not isinstance(fields, dict):
            logger.warning(f"section {section_name} 不是字典类型，跳过")
            continue
            
        schema[section_name] = []
        
        for field_name, field_obj in fields.items():
            if isinstance(field_obj, ConfigField):
                field_schema = extract_field_schema(field_name, field_obj, section_name)
                schema[section_name].append(field_schema)
                # 打印增强属性
                enhanced_attrs = [k for k in ['label', 'icon', 'input_type', 'depends_on', 'min', 'max'] 
                                  if field_schema.get(k)]
                if enhanced_attrs:
                    logger.info(f"  字段 {section_name}.{field_name} 增强属性: {enhanced_attrs}")
            else:
                logger.warning(f"字段 {section_name}.{field_name} 不是 ConfigField 类型: {type(field_obj)}")
        
        # 按 order 排序（如果有）
        schema[section_name].sort(key=lambda x: x.get('order', 0))
        logger.info(f"section {section_name} 解析完成，共 {len(schema[section_name])} 个字段")
    
    # 解析 section 元数据
    sections: list[dict[str, Any]] = []
    
    for section_name in schema.keys():
        section_meta: dict[str, Any] = {
            "name": section_name,
            "title": section_name.replace('_', ' ').title(),
            "order": 0
        }
        
        # 从 section_descriptions 获取额外信息
        if section_name in section_descriptions:
            desc = section_descriptions[section_name]
            if isinstance(desc, str):
                section_meta["title"] = desc
            elif isinstance(desc, dict):
                section_meta.update(desc)
        
        sections.append(section_meta)
    
    # 按 order 排序
    sections.sort(key=lambda x: x.get('order', 0))
    
    # 解析布局（未来扩展）
    layout = None
    if config_layout:
        if isinstance(config_layout, dict):
            layout = config_layout
        elif hasattr(config_layout, '__dict__'):
            layout = vars(config_layout)
    
    return {
        "schema": schema,
        "sections": sections,
        "layout": layout
    }


def get_plugin_default_config(plugin_name: str) -> dict[str, Any] | None:
    """
    获取插件的默认配置值
    
    Args:
        plugin_name: 插件名称
    
    Returns:
        按 section 组织的默认配置字典
    """
    plugin_instance = plugin_manager.get_plugin_instance(plugin_name)
    if not plugin_instance:
        return None
    
    config_schema = getattr(plugin_instance, 'config_schema', {})
    if not config_schema:
        return {}
    
    defaults: dict[str, dict[str, Any]] = {}
    
    for section_name, fields in config_schema.items():
        if not isinstance(fields, dict):
            continue
        
        defaults[section_name] = {}
        
        for field_name, field_obj in fields.items():
            if isinstance(field_obj, ConfigField):
                defaults[section_name][field_name] = field_obj.default
    
    return defaults
