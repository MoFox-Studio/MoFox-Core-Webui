/**
 * 插件配置管理 API（新版）
 *
 * 对应后端 PluginConfigRouter（/webui/api/plugin-config）
 *
 * 端点一览：
 * - GET  /list                                    获取所有已加载插件的配置列表
 * - GET  /list/{plugin_name}                      获取指定插件的配置列表
 * - GET  /raw/{plugin_name}/{config_name}         获取配置文件原始 TOML 内容
 * - POST /raw/{plugin_name}/{config_name}         保存配置文件原始 TOML 内容
 * - GET  /backups/{plugin_name}/{config_name}     获取备份列表
 * - POST /restore/{plugin_name}/{config_name}/{backup_name}  从备份恢复
 */

import { api } from './index'

// ==================== 路径常量 ====================

const BASE = 'plugin-config'

export const PLUGIN_CONFIG_ENDPOINTS = {
  /** 获取所有插件配置列表 */
  LIST_ALL: `${BASE}/list`,
  /** 获取指定插件的配置列表 */
  LIST: (pluginName: string) => `${BASE}/list/${encodeURIComponent(pluginName)}`,
  /** 获取原始 TOML 内容 */
  RAW: (pluginName: string, configName: string) =>
    `${BASE}/raw/${encodeURIComponent(pluginName)}/${encodeURIComponent(configName)}`,
  /** 获取备份列表 */
  BACKUPS: (pluginName: string, configName: string) =>
    `${BASE}/backups/${encodeURIComponent(pluginName)}/${encodeURIComponent(configName)}`,
  /** 从备份恢复 */
  RESTORE: (pluginName: string, configName: string, backupName: string) =>
    `${BASE}/restore/${encodeURIComponent(pluginName)}/${encodeURIComponent(configName)}/${encodeURIComponent(backupName)}`,
} as const

// ==================== 类型定义 ====================

/** 编辑器组件使用的字段类型（兼容旧格式） */
export interface SchemaField {
  key: string
  label?: string
  description?: string
  input_type?: string
  type?: string
  choices?: { value: unknown; label: string }[]
  default?: unknown
  placeholder?: string
  hint?: string
  disabled?: boolean
  required?: boolean
  min?: number
  max?: number
  step?: number
  min_items?: number
  max_items?: number
  item_type?: string
  item_fields?: SchemaField[]
  max_length?: number
  rows?: number
  icon?: string
}

/** 配置字段 Schema */
export interface PluginSchemaField {
  /** 完整路径，如 "section.field" */
  key: string
  /** 显示名称 */
  name: string
  /** 描述 */
  description: string
  /** 字段类型 */
  type: 'string' | 'number' | 'boolean' | 'array' | 'object' | 'textarea' | 'select'
  /** 默认值 */
  default?: unknown
  /** select 类型的选项 */
  options?: { value: string; label: string }[]
}

/** 配置节 Schema */
export interface PluginSchemaSection {
  /** section 键名 */
  key: string
  /** 显示名称 */
  name: string
  /** 描述 */
  description: string
  /** 字段列表 */
  fields: PluginSchemaField[]
}

/** 单个插件配置文件信息 */
export interface PluginConfigFileInfo {
  /** 插件名称 */
  plugin_name: string
  /** 显示名称 */
  display_name: string
  /** 配置文件路径（相对） */
  config_path: string
  /** 配置文件名（不含 .toml 扩展名） */
  config_name: string
  /** 文件大小（字节） */
  size: number
  /** 最后修改时间（ISO 格式） */
  modified_at: string
  /** 是否存在配置文件 */
  has_config: boolean
  /** Pydantic 生成的 Schema（可能为 null） */
  config_schema: PluginSchemaSection[] | null
}

/** 插件配置列表响应 */
export interface PluginConfigListResponse {
  success: boolean
  plugins: PluginConfigFileInfo[]
  total: number
  error?: string
}

/** 原始配置文件内容响应 */
export interface PluginConfigRawResponse {
  success: boolean
  content: string
  path: string
  plugin_name: string
  /** Pydantic 生成的 Schema（可能为 null） */
  config_schema: PluginSchemaSection[] | null
  error?: string
}

/** 保存配置请求 */
export interface PluginConfigSaveRequest {
  content: string
}

/** 保存配置响应 */
export interface PluginConfigSaveResponse {
  success: boolean
  message: string
  backup_path?: string
  error?: string
}

/** 备份信息 */
export interface PluginBackupInfo {
  name: string
  path: string
  created_at: string
  size: number
}

/** 备份列表响应 */
export interface PluginBackupsResponse {
  success: boolean
  backups: PluginBackupInfo[]
  error?: string
}

/** 恢复备份响应 */
export interface PluginRestoreResponse {
  success: boolean
  message: string
  error?: string
}

// ==================== API 函数 ====================

/**
 * 获取所有已加载插件的配置文件列表
 *
 * 只返回存在配置文件（has_config=true）的条目。
 */
export async function listAllPluginConfigs() {
  return api.get<PluginConfigListResponse>(PLUGIN_CONFIG_ENDPOINTS.LIST_ALL)
}

/**
 * 获取指定插件的配置文件列表
 *
 * @param pluginName 插件名称
 */
export async function listPluginConfigs(pluginName: string) {
  return api.get<PluginConfigListResponse>(PLUGIN_CONFIG_ENDPOINTS.LIST(pluginName))
}

/**
 * 获取指定插件配置文件的原始 TOML 内容
 *
 * @param pluginName  插件名称
 * @param configName  配置文件名（不含 .toml 扩展名，默认为 "config"）
 */
export async function getPluginConfigRaw(pluginName: string, configName = 'config') {
  return api.get<PluginConfigRawResponse>(PLUGIN_CONFIG_ENDPOINTS.RAW(pluginName, configName))
}

/**
 * 保存指定插件配置文件的原始 TOML 内容
 *
 * 保存前会自动备份旧文件（最多保留 20 份）。
 *
 * @param pluginName  插件名称
 * @param configName  配置文件名（不含 .toml 扩展名，默认为 "config"）
 * @param content     TOML 文本内容
 */
export async function savePluginConfigRaw(
  pluginName: string,
  configName: string = 'config',
  content: string,
) {
  return api.post<PluginConfigSaveResponse>(
    PLUGIN_CONFIG_ENDPOINTS.RAW(pluginName, configName),
    { content } satisfies PluginConfigSaveRequest,
  )
}

/**
 * 获取指定插件配置文件的备份列表
 *
 * @param pluginName  插件名称
 * @param configName  配置文件名（不含 .toml 扩展名，默认为 "config"）
 */
export async function getPluginConfigBackups(pluginName: string, configName = 'config') {
  return api.get<PluginBackupsResponse>(PLUGIN_CONFIG_ENDPOINTS.BACKUPS(pluginName, configName))
}

/**
 * 从备份恢复指定插件配置文件
 *
 * @param pluginName  插件名称
 * @param configName  配置文件名（不含 .toml 扩展名，默认为 "config"）
 * @param backupName  备份文件名（带 .toml 扩展名）
 */
export async function restorePluginConfigFromBackup(
  pluginName: string,
  configName: string = 'config',
  backupName: string,
) {
  return api.post<PluginRestoreResponse>(
    PLUGIN_CONFIG_ENDPOINTS.RESTORE(pluginName, configName, backupName),
  )
}
