# MoFox WebUI 插件配置 Schema 增强系统

> **实现方式**：扩展主程序 `ConfigField`，添加 UI 相关属性，向后兼容现有插件

## 📁 文档结构

| 文件 | 说明 |
|------|------|
| [01-架构设计.md](./01-架构设计.md) | 整体架构和设计思路 |
| [02-主程序修改.md](./02-主程序修改.md) | ConfigField 扩展和辅助类型 |
| [03-后端实现.md](./03-后端实现.md) | WebUI 后端路由拆分与 Schema 解析服务 |
| [04-前端组件.md](./04-前端组件.md) | 前端配置编辑器组件 |
| [05-插件开发指南.md](./05-插件开发指南.md) | 给插件开发者的使用文档 |

## 🎯 核心思路

**问题**：主程序的 `ConfigField` 只有基础属性，无法支持丰富的 UI 控件。

**解决**：扩展主程序的 `ConfigField`，添加可选的 UI 属性。主程序只使用基础属性，WebUI 读取全部属性。

```
扩展后的 ConfigField
┌─────────────────────────────────────┐
│ 基础属性（主程序使用）               │
│ - type, default, description        │
│ - example, required, choices        │
├─────────────────────────────────────┤
│ UI 属性（WebUI 使用，可选）          │
│ - input_type, placeholder, hint     │
│ - min, max, step, depends_on...     │
└─────────────────────────────────────┘
```

## ✅ 优势

1. **向后兼容**：现有插件无需修改，新属性都有默认值
2. **统一导入**：所有插件使用同一个 `from src.plugin_system.base.config_types import ConfigField`
3. **类型安全**：dataclass 提供完整的类型提示
4. **渐进增强**：插件开发者可按需使用新属性

## 🚀 快速开始

### 现有插件（无需修改）

```python
from src.plugin_system.base.config_types import ConfigField

config_schema = {
    "api": {
        "key": ConfigField(type=str, default="", description="API 密钥"),
    }
}
# WebUI 自动推断为文本输入框
```

### 新插件（使用增强属性）

```python
from src.plugin_system.base.config_types import ConfigField

config_schema = {
    "api": {
        "key": ConfigField(
            type=str,
            default="",
            description="API 密钥",
            input_type="password",      # 🌟 新属性
            placeholder="sk-xxxxxxxx",  # 🌟 新属性
            hint="从控制台获取",         # 🌟 新属性
            required=True
        ),
    }
}
```

详见 [05-插件开发指南.md](./05-插件开发指南.md)
