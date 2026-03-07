# 前端 Tag 映射系统使用文档

## 概述

本文档说明了 MoFox WebUI 前端的配置 Tag 映射系统的实现和使用方式。该系统允许后端通过预设的语义标签（tag）来指定配置项和配置节的图标显示，前端统一映射到 Material Symbols 图标。

## 架构说明

### 1. 类型定义（`src/api/pluginConfig.ts`）

```typescript
/** 配置字段 Schema */
export interface PluginSchemaField {
  key: string
  name: string
  description: string
  type: 'string' | 'number' | 'boolean' | 'array' | 'object' | 'textarea' | 'select'
  default?: unknown
  options?: { value: string; label: string }[]
  tag?: string  // 🆕 语义标签（用于前端映射到图标）
}

/** 配置节 Schema */
export interface PluginSchemaSection {
  key: string
  name: string
  description: string
  fields: PluginSchemaField[]
  tag?: string  // 🆕 语义标签（用于前端映射到图标）
}
```

### 2. Tag 映射工具（`src/utils/tagIconMapper.ts`）

#### 预设 Tag 值（16 个）

| Tag | 含义 | Material Symbol 图标 |
|-----|------|---------------------|
| `general` | 通用配置 | `settings` |
| `security` | 安全与权限 | `lock` |
| `network` | 网络与连接 | `lan` |
| `ai` | AI/LLM 相关 | `psychology` |
| `database` | 数据库配置 | `database` |
| `user` | 用户与身份 | `person` |
| `timer` | 定时与调度 | `schedule` |
| `performance` | 性能优化 | `speed` |
| `text` | 文本处理 | `subject` |
| `list` | 列表配置 | `view_list` |
| `advanced` | 高级选项 | `tune` |
| `debug` | 调试日志 | `bug_report` |
| `file` | 文件路径 | `folder_open` |
| `color` | 颜色外观 | `palette` |
| `notification` | 通知提醒 | `notifications` |
| `plugin` | 插件相关 | `extension` |

#### 核心函数

```typescript
// 根据 tag 获取图标（最基础的函数）
getIconByTag(tag: string | null | undefined, fallback?: string): string

// 获取 section 图标（优先使用 tag，然后推断）
getSectionIcon(section: { tag?: string | null; key: string }, fallback?: string): string

// 获取字段图标（field 级别，可选显示）
getFieldIcon(field: { tag?: string | null }, fallback?: string | null): string | null

// 从 key 推断图标（向后兼容旧数据）
inferIconFromKey(sectionKey: string): string
```

### 3. 组件集成

#### ConfigSection.vue（Section 级别图标）

```vue
<script setup lang="ts">
import { getSectionIcon } from '@/utils/tagIconMapper'

// section 图标（使用 tag 映射系统）
const sectionIcon = computed(() => {
  return getSectionIcon(props.section, 'folder')
})
</script>

<template>
  <div class="section-header">
    <span class="section-icon material-symbols-rounded">{{ sectionIcon }}</span>
    <h3>{{ section.name }}</h3>
  </div>
</template>
```

#### SchemaFieldEditor.vue（Field 级别图标）

```vue
<script setup lang="ts">
import { getFieldIcon } from '@/utils/tagIconMapper'

// 字段图标（基于 tag）
const fieldIcon = computed(() => {
  return getFieldIcon(props.field)
})
</script>

<template>
  <div class="field-header">
    <div class="header-left">
      <span v-if="fieldIcon" class="field-icon material-symbols-rounded">{{ fieldIcon }}</span>
      <span class="field-label">{{ field.name }}</span>
    </div>
  </div>
</template>
```

## 使用示例

### 后端 Python 代码示例

```python
from src.kernel.config import Field, section_meta, ConfigBase, SectionBase

class MyPluginConfig(ConfigBase):
    @section_meta(
        title="AI 配置",
        description="LLM 模型相关配置",
        tag="ai"  # 🆕 设置 section 图标
    )
    class AISection(SectionBase):
        model_name: str = Field(
            "gpt-4",
            label="模型名称",
            description="使用的 LLM 模型",
            tag="ai"  # 🆕 设置字段图标（可选）
        )
        
        api_key: str = Field(
            ...,
            label="API 密钥",
            description="OpenAI API 密钥",
            tag="security"  # 🆕 安全相关字段
        )
        
        temperature: float = Field(
            0.7,
            label="温度参数",
            ge=0.0,
            le=2.0,
            tag="advanced"  # 🆕 高级参数
        )
```

### 前端效果

- **Section 头部**：显示 `psychology` 图标（AI 大脑图标）
- **model_name 字段**：显示 `psychology` 图标
- **api_key 字段**：显示 `lock` 图标（安全锁）
- **temperature 字段**：显示 `tune` 图标（调试旋钮）

### 兼容性处理

如果后端没有提供 `tag`，前端会自动根据 `key` 进行智能推断：

```typescript
// 后端返回：{ key: "database_config", tag: null }
// 前端推断：包含 "database" → 显示 "database" 图标

// 后端返回：{ key: "api_settings", tag: null }
// 前端推断：包含 "api" → 显示 "lan" 图标（网络）

// 后端返回：{ key: "unknown_section", tag: null }
// 前端推断：无匹配 → 显示 "folder" 图标（默认）
```

## 优势

### 1. 语义化设计
- 使用 `tag="security"` 而不是 `icon="lock"`
- 前端可以统一修改图标风格，无需修改后端代码
- 支持主题切换（未来可以根据主题使用不同图标集）

### 2. 智能推断
- 旧数据（无 tag）自动通过 key 关键词推断图标
- 减少迁移成本，平滑升级

### 3. 类型安全
- TypeScript 定义了完整的 `ConfigTag` 类型
- IDE 提供自动补全和类型检查
- 降低拼写错误风险

### 4. 统一管理
- 所有图标映射逻辑集中在 `tagIconMapper.ts`
- 便于维护和扩展新的 tag
- 前后端解耦

## 扩展指南

### 添加新的 Tag

1. **更新后端类型定义**（`src/kernel/config/core.py`）：

```python
TagLiteral = Literal[
    "general", "security", "network", "ai", "database",
    "user", "timer", "performance", "text", "list",
    "advanced", "debug", "file", "color", "notification",
    "plugin",
    "new_tag"  # 🆕 添加新的 tag
]
```

2. **更新前端类型和映射**（`src/utils/tagIconMapper.ts`）：

```typescript
export type ConfigTag =
  | 'general'
  | 'security'
  // ... 其他 tag
  | 'new_tag'  // 🆕 添加类型

export const TAG_TO_ICON: Record<ConfigTag, string> = {
  general: 'settings',
  security: 'lock',
  // ... 其他映射
  new_tag: 'new_icon_name',  // 🆕 添加映射
}
```

3. **更新文档**（`docs/config-tag-mapping.md`）

### 修改图标映射

只需修改 `TAG_TO_ICON` 常量即可，无需修改后端代码或组件代码：

```typescript
export const TAG_TO_ICON: Record<ConfigTag, string> = {
  ai: 'smart_toy',  // 改用机器人图标而不是大脑
  security: 'shield',  // 改用盾牌而不是锁
  // ...
}
```

## 注意事项

1. **Tag 是可选的**：后端可以不提供 `tag`，前端会自动推断
2. **Field 图标显示是可选的**：`getFieldIcon` 默认返回 `null`，只有设置了 `tag` 才显示
3. **Section 图标总是显示**：使用 `getSectionIcon`，会优先使用 tag → 推断 → fallback
4. **保持一致性**：同类型的配置应该使用相同的 tag（如所有安全相关都用 `security`）
5. **不要过度使用 Field 图标**：字段级别的图标是可选的，只在需要强调时使用

## 相关文件

- **后端文档**: `docs/config-tag-mapping.md`
- **类型定义**: `src/api/pluginConfig.ts`
- **映射工具**: `src/utils/tagIconMapper.ts`
- **Section 组件**: `src/components/config/plugin-schema/ConfigSection.vue`
- **Field 组件**: `src/components/config/plugin-schema/SchemaFieldEditor.vue`
- **后端配置系统**: `Neo-MoFox/src/kernel/config/core.py`

## 更新日志

- **2025-03-07**: 初始实现，支持 16 个预设 tag，包含智能推断和向后兼容
