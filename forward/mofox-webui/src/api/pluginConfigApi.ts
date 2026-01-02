/**
 * 插件配置 API 模块
 * 提供插件配置管理相关的 API 请求封装
 * 支持增强 Schema 获取、配置读写、备份恢复等功能
 */

import { api, API_ENDPOINTS } from './index'

// ==================== 类型定义 ====================

/** 插件配置文件信息 */
export interface PluginConfigInfo {
  plugin_name: string
  display_name: string
  config_path: string
  exists: boolean
  has_schema: boolean
  last_modified?: string
}

/** 插件配置列表响应 */
export interface PluginConfigListResponse {
  success: boolean
  configs: PluginConfigInfo[]
  total: number
  error?: string
}

/** 插件配置内容响应 */
export interface PluginConfigContentResponse {
  success: boolean
  plugin_name: string
  content?: string  // 原始 TOML 内容
  parsed?: Record<string, unknown>  // 解析后的配置
  last_modified?: string
  error?: string
}

/** Schema 字段定义 */
export interface SchemaField {
  // 基础属性
  key: string
  section: string
  type: string
  default: unknown
  description: string
  required: boolean
  choices?: unknown[]
  example?: string
  
  // 推断的输入类型
  input_type: 'text' | 'password' | 'number' | 'slider' | 'switch' | 'select' | 'textarea' | 'list' | 'json' | 'color' | 'file'
  
  // UI 属性
  label?: string
  placeholder?: string
  hint?: string
  icon?: string
  hidden?: boolean
  disabled?: boolean
  order?: number
  rows?: number
  
  // 验证属性
  min?: number
  max?: number
  step?: number
  pattern?: string
  max_length?: number
  min_length?: number
  
  // 条件显示
  group?: string
  depends_on?: string
  depends_value?: unknown
  
  // 列表专用
  item_type?: 'string' | 'number' | 'object'
  item_fields?: Record<string, {
    type?: 'string' | 'number' | 'boolean'
    label?: string
    placeholder?: string
    default?: unknown
  }>
  min_items?: number
  max_items?: number
}

/** Section 元数据 */
export interface SectionMeta {
  name: string
  title: string
  description?: string
  icon?: string
  collapsed?: boolean
  order?: number
}

/** Tab 配置 */
export interface TabConfig {
  id: string
  title: string
  sections: string[]
  icon?: string
  order?: number
  badge?: string
}

/** 布局配置 */
export interface LayoutConfig {
  type: 'tabs' | 'sections' | 'flat'
  tabs?: TabConfig[]
}

/** 插件 Schema 响应 */
export interface PluginSchemaResponse {
  success: boolean
  plugin_name: string
  schema?: Record<string, SchemaField[]>  // 按 section 组织的字段
  sections?: SectionMeta[]
  layout?: LayoutConfig
  error?: string
}

/** 插件配置保存响应 */
export interface PluginConfigSaveResponse {
  success: boolean
  message?: string
  backup_path?: string
  error?: string
}

/** 插件配置备份信息 */
export interface PluginConfigBackupInfo {
  name: string
  path: string
  created_at: string
  size: number
}

/** 备份列表响应 */
export interface PluginConfigBackupsResponse {
  success: boolean
  backups: PluginConfigBackupInfo[]
  error?: string
}

/** 验证响应 */
export interface PluginConfigValidateResponse {
  success: boolean
  valid?: boolean
  message?: string
  line?: number
  col?: number
  error?: string
}

// ==================== API 函数 ====================

/**
 * 获取所有插件配置列表
 */
export async function getPluginConfigList() {
  return api.get<PluginConfigListResponse>(API_ENDPOINTS.PLUGIN_CONFIG.LIST)
}

/**
 * 获取插件配置 Schema（增强版）
 * @param pluginName 插件名称
 */
export async function getPluginSchema(pluginName: string) {
  return api.get<PluginSchemaResponse>(API_ENDPOINTS.PLUGIN_CONFIG.SCHEMA(pluginName))
}

/**
 * 获取插件配置内容
 * @param pluginName 插件名称
 */
export async function getPluginConfigContent(pluginName: string) {
  return api.get<PluginConfigContentResponse>(API_ENDPOINTS.PLUGIN_CONFIG.CONTENT(pluginName))
}

/**
 * 保存插件配置（原始 TOML）
 * @param pluginName 插件名称
 * @param content TOML 内容
 * @param createBackup 是否创建备份
 */
export async function savePluginConfig(
  pluginName: string,
  content: string,
  createBackup: boolean = true
) {
  return api.post<PluginConfigSaveResponse>(
    API_ENDPOINTS.PLUGIN_CONFIG.SAVE(pluginName),
    { content, create_backup: createBackup }
  )
}

/**
 * 更新插件配置（可视化编辑）
 * @param pluginName 插件名称
 * @param updates 键值对更新，支持点号路径如 "section.key"
 * @param createBackup 是否创建备份
 */
export async function updatePluginConfig(
  pluginName: string,
  updates: Record<string, unknown>,
  createBackup: boolean = true
) {
  return api.post<PluginConfigSaveResponse>(
    API_ENDPOINTS.PLUGIN_CONFIG.UPDATE(pluginName),
    { updates, create_backup: createBackup }
  )
}

/**
 * 重置插件配置为默认值
 * @param pluginName 插件名称
 */
export async function resetPluginConfig(pluginName: string) {
  return api.post<PluginConfigSaveResponse>(
    API_ENDPOINTS.PLUGIN_CONFIG.RESET(pluginName),
    {}
  )
}

/**
 * 获取插件配置备份列表
 * @param pluginName 插件名称
 */
export async function getPluginConfigBackups(pluginName: string) {
  return api.get<PluginConfigBackupsResponse>(
    API_ENDPOINTS.PLUGIN_CONFIG.BACKUPS(pluginName)
  )
}

/**
 * 从备份恢复插件配置
 * @param pluginName 插件名称
 * @param backupName 备份文件名
 */
export async function restorePluginConfig(pluginName: string, backupName: string) {
  return api.post<PluginConfigSaveResponse>(
    API_ENDPOINTS.PLUGIN_CONFIG.RESTORE(pluginName, backupName),
    {}
  )
}

/**
 * 验证插件配置 TOML 格式
 * @param pluginName 插件名称
 * @param content TOML 内容
 */
export async function validatePluginConfig(pluginName: string, content: string) {
  return api.post<PluginConfigValidateResponse>(
    API_ENDPOINTS.PLUGIN_CONFIG.VALIDATE(pluginName),
    content
  )
}

// ==================== 工具函数 ====================

/**
 * 根据 Schema 字段推断默认的输入组件
 * @param field Schema 字段
 */
export function getInputComponent(field: SchemaField): string {
  // 如果已指定 input_type，直接使用
  if (field.input_type) {
    return field.input_type
  }
  
  // 按类型推断
  switch (field.type) {
    case 'bool':
      return 'switch'
    case 'int':
    case 'float':
      if (field.min !== undefined && field.max !== undefined) {
        return 'slider'
      }
      return 'number'
    case 'list':
      return 'list'
    case 'dict':
      return 'json'
    default:
      if (field.choices && field.choices.length > 0) {
        return 'select'
      }
      return 'text'
  }
}

/**
 * 检查字段是否应该显示（基于 depends_on）
 * @param field 字段
 * @param values 当前配置值
 */
export function shouldShowField(
  field: SchemaField,
  values: Record<string, unknown>
): boolean {
  if (!field.depends_on) {
    return !field.hidden
  }
  
  const dependValue = values[field.depends_on]
  
  if (field.depends_value !== undefined) {
    return dependValue === field.depends_value
  }
  
  // 如果没有指定 depends_value，则检查依赖字段是否为 truthy
  return Boolean(dependValue)
}
