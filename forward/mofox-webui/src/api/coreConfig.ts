/**
 * Core 配置管理 API
 * 
 * 提供 Neo-MoFox Core 层配置的管理接口
 * 后端由 CoreConfigRouter 提供支持
 */

import { api } from './index'

// ==================== 类型定义 ====================

/** 配置字段类型 */
export type ConfigFieldType = 'string' | 'number' | 'boolean' | 'array' | 'object' | 'textarea' | 'textarea_tall' | 'select' | 'password'

/** 特殊编辑器类型 */
export type SpecialEditorType = 'string_array' | 'key_value' | 'owner_list' | 'master_users' | 'expression_rules' | 'reaction_rules' | 'model_extra_params' | 'web_search_engines' | 'chat_list'

/** 配置字段 Schema */
export interface ConfigFieldSchema {
  key: string                                 // 字段完整路径，如 "bot.ui_level"
  name: string                                // 显示名称
  description: string                         // 详细描述
  type: ConfigFieldType                       // 字段类型
  default?: unknown                           // 默认值
  placeholder?: string                        // 占位符
  options?: { value: string; label: string }[] // 选项（用于 select 类型）
  min?: number                                // 最小值
  max?: number                                // 最大值
  step?: number                               // 步进值
  readonly?: boolean                          // 是否只读
  advanced?: boolean                          // 是否为高级选项
  expert?: boolean                            // 是否为专家选项
  specialEditor?: SpecialEditorType           // 特殊编辑器类型
  hidden?: boolean                            // 是否隐藏
}

/** 配置组 Schema */
export interface ConfigGroupSchema {
  key: string                                 // 组键名
  name: string                                // 组名称
  icon: string                                // 图标
  description: string                         // 组描述
  fields: ConfigFieldSchema[]                 // 字段列表
  expert?: boolean                            // 是否为专家模式组
  hasSpecialEditor?: boolean                  // 是否包含特殊编辑器
  hidden?: boolean                            // 是否隐藏
}

/** 配置 Schema 响应 */
export interface ConfigSchemaResponse {
  version: string                             // 配置版本
  groups: ConfigGroupSchema[]                 // 配置组列表
}

/** 配置内容响应 */
export interface ConfigContentResponse {
  version: string                             // 配置版本
  config: Record<string, Record<string, unknown>> // 配置内容
}

/** 原始 TOML 文件响应 */
export interface ConfigRawResponse {
  success: boolean
  content: string
  path: string
}

/** 备份信息 */
export interface ConfigBackupInfo {
  name: string
  path: string
  created_at: string
  size: number
}

/** 备份列表响应 */
export interface ConfigBackupsResponse {
  success: boolean
  backups: ConfigBackupInfo[]
}

/** 配置更新请求 */
export interface ConfigUpdateRequest {
  updates: Record<string, unknown>            // 要更新的配置项，键为点分隔路径
}

/** 配置更新响应 */
export interface ConfigUpdateResponse {
  success: boolean                            // 是否成功
  message: string                             // 消息
  failed_keys?: string[]                      // 失败的键（如果有）
}

// ==================== API 端点 ====================

const CORE_CONFIG_BASE = 'core-config'

export const CORE_CONFIG_ENDPOINTS = {
  /** 获取配置 Schema */
  SCHEMA: `${CORE_CONFIG_BASE}/schema`,
  /** 获取配置内容（键值对） */
  CONFIG: `${CORE_CONFIG_BASE}/config`,
  /** 获取/保存原始 TOML */
  CONFIG_RAW: `${CORE_CONFIG_BASE}/config/raw`,
  /** 获取备份列表 */
  BACKUPS: `${CORE_CONFIG_BASE}/config/backups`,
  /** 从备份恢复 */
  RESTORE: (backupName: string) => `${CORE_CONFIG_BASE}/config/restore/${encodeURIComponent(backupName)}`,
} as const

// ==================== API 函数 ====================

/**
 * 获取 Core 配置的 Schema
 * 
 * 返回配置的结构定义，包括所有配置组和字段的元数据
 * 用于前端动态生成配置表单
 * 
 * @returns Promise<ConfigSchemaResponse> 配置 Schema
 */
export async function getCoreConfigSchema() {
  const result = await api.get<ConfigSchemaResponse>(CORE_CONFIG_ENDPOINTS.SCHEMA)
  
  if (result.success && result.data) {
    return result.data
  }
  
  throw new Error(result.error || '获取配置 Schema 失败')
}

/**
 * 获取当前的 Core 配置值
 * 
 * @returns Promise<ConfigContentResponse> 当前配置内容
 */
export async function getCoreConfig() {
  const result = await api.get<ConfigContentResponse>(CORE_CONFIG_ENDPOINTS.CONFIG)
  
  if (result.success && result.data) {
    return result.data
  }
  
  throw new Error(result.error || '获取配置失败')
}

/**
 * 更新 Core 配置
 * 
 * @param updates - 要更新的配置项，键为点分隔路径（如 "bot.ui_level"）
 * @returns Promise<ConfigUpdateResponse> 更新结果
 */
export async function updateCoreConfig(updates: Record<string, unknown>) {
  const result = await api.put<ConfigUpdateResponse>(
    CORE_CONFIG_ENDPOINTS.CONFIG,
    { updates } as ConfigUpdateRequest
  )
  
  if (result.success && result.data) {
    return result.data
  }
  
  throw new Error(result.error || '更新配置失败')
}

/**
 * 批量更新多个配置项
 * 
 * 这是 updateCoreConfig 的别名，提供更清晰的语义
 * 
 * @param updates - 配置更新对象
 * @returns Promise<ConfigUpdateResponse> 更新结果
 */
export async function batchUpdateCoreConfig(updates: Record<string, unknown>) {
  return updateCoreConfig(updates)
}

/**
 * 获取原始 TOML 文件内容
 */
export async function getCoreConfigRaw(): Promise<ConfigRawResponse> {
  const result = await api.get<ConfigRawResponse>(CORE_CONFIG_ENDPOINTS.CONFIG_RAW)
  if (result.success && result.data) return result.data
  throw new Error(result.error || '获取原始配置失败')
}

/**
 * 保存原始 TOML 文件内容
 */
export async function saveCoreConfigRaw(content: string): Promise<{ success: boolean; message: string }> {
  const result = await api.post<{ success: boolean; message: string }>(
    CORE_CONFIG_ENDPOINTS.CONFIG_RAW,
    { content }
  )
  if (result.success && result.data) return result.data
  throw new Error(result.error || '保存原始配置失败')
}

/**
 * 获取备份列表
 */
export async function getCoreConfigBackups(): Promise<ConfigBackupsResponse> {
  const result = await api.get<ConfigBackupsResponse>(CORE_CONFIG_ENDPOINTS.BACKUPS)
  if (result.success && result.data) return result.data
  throw new Error(result.error || '获取备份列表失败')
}

/**
 * 从备份恢复配置
 */
export async function restoreCoreConfigBackup(backupName: string): Promise<{ success: boolean; message: string }> {
  const result = await api.post<{ success: boolean; message: string }>(
    CORE_CONFIG_ENDPOINTS.RESTORE(backupName)
  )
  if (result.success && result.data) return result.data
  throw new Error(result.error || '恢复备份失败')
}

// ==================== 工具函数 ====================

/**
 * 将嵌套的配置对象展平为点分隔的路径
 * 
 * 例如：
 * { bot: { ui_level: 'verbose' } } 
 * => { 'bot.ui_level': 'verbose' }
 * 
 * @param config - 嵌套的配置对象
 * @param prefix - 路径前缀（内部使用）
 * @returns 展平后的配置对象
 */
export function flattenConfig(
  config: Record<string, unknown>,
  prefix = ''
): Record<string, unknown> {
  const result: Record<string, unknown> = {}
  
  for (const [key, value] of Object.entries(config)) {
    const fullKey = prefix ? `${prefix}.${key}` : key
    
    if (value && typeof value === 'object' && !Array.isArray(value)) {
      // 递归展平嵌套对象
      Object.assign(result, flattenConfig(value as Record<string, unknown>, fullKey))
    } else {
      result[fullKey] = value
    }
  }
  
  return result
}

/**
 * 从展平的配置恢复为嵌套对象
 * 
 * 例如：
 * { 'bot.ui_level': 'verbose' }
 * => { bot: { ui_level: 'verbose' } }
 * 
 * @param flatConfig - 展平的配置对象
 * @returns 嵌套的配置对象
 */
export function unflattenConfig(
  flatConfig: Record<string, unknown>
): Record<string, Record<string, unknown>> {
  const result: Record<string, Record<string, unknown>> = {}
  
  for (const [key, value] of Object.entries(flatConfig)) {
    const parts = key.split('.')
    
    if (parts.length === 2) {
      const section = parts[0]!
      const field = parts[1]!
      
      if (!result[section]) {
        result[section] = {}
      }
      
      result[section][field] = value
    }
  }
  
  return result
}
