/**
 * 模型配置管理 API
 *
 * 提供 model.toml 配置的 CRUD 管理接口
 * 后端由 ModelConfigRouter 提供支持，路径前缀为 /webui/api/model-config
 */

import { api } from './index'

// ==================== 类型定义 ====================

/** API 提供商数据 */
export interface APIProviderData {
  name: string
  base_url: string
  api_key: string | string[]
  client_type: 'openai' | 'gemini' | 'aiohttp_gemini' | 'bedrock'
  max_retry: number
  timeout: number
  retry_interval: number
}

/** 模型信息数据 */
export interface ModelInfoData {
  name: string
  model_identifier: string
  api_provider: string
  price_in: number
  price_out: number
  force_stream_mode: boolean
  max_context: number
  tool_call_compat: boolean
  extra_params: Record<string, unknown>
  anti_truncation: boolean
}

/** 任务配置数据 */
export interface TaskConfigData {
  model_list: string[]
  max_tokens: number
  temperature: number
  concurrency_count: number
  embedding_dimension: number | null
}

/** 模型任务配置（每个字段对应一个任务） */
export interface ModelTasksData {
  utils?: TaskConfigData
  utils_small?: TaskConfigData
  actor?: TaskConfigData
  sub_actor?: TaskConfigData
  vlm?: TaskConfigData
  voice?: TaskConfigData
  video?: TaskConfigData
  tool_use?: TaskConfigData
  embedding?: TaskConfigData
}

/** 完整模型配置 */
export interface ModelConfigData {
  api_providers: APIProviderData[]
  models: ModelInfoData[]
  model_tasks: ModelTasksData
}

/** 原始 TOML 响应 */
export interface ModelConfigRawResponse {
  success: boolean
  content: string
  path: string
}

/** 备份信息 */
export interface ModelConfigBackupInfo {
  name: string
  path: string
  created_at: string
  size: number
}

/** 备份列表响应 */
export interface ModelConfigBackupsResponse {
  success: boolean
  backups: ModelConfigBackupInfo[]
}

/** 更新响应 */
export interface ModelConfigUpdateResponse {
  success: boolean
  message: string
}

/** 模型测试响应 */
export interface ModelTestResponse {
  success: boolean
  connected: boolean
  model_name: string
  response_time?: number  // 响应时间（秒）
  response_text?: string
  error?: string
}

// ==================== API 端点 ====================

const BASE = 'model-config'

export const MODEL_CONFIG_ENDPOINTS = {
  /** 获取/更新结构化配置 */
  CONFIG: `${BASE}/config`,
  /** 获取/保存原始 TOML */
  CONFIG_RAW: `${BASE}/config/raw`,
  /** 获取备份列表 */
  BACKUPS: `${BASE}/config/backups`,
  /** 从备份恢复 */
  RESTORE: (backupName: string) => `${BASE}/config/restore/${encodeURIComponent(backupName)}`,
  /** 测试模型连通性 */
  TEST: `${BASE}/test`,
} as const

// ==================== API 函数 ====================

/**
 * 获取当前模型配置（结构化）
 */
export async function getModelConfig(): Promise<ModelConfigData> {
  const result = await api.get<ModelConfigData>(MODEL_CONFIG_ENDPOINTS.CONFIG)
  if (result.success && result.data) return result.data
  throw new Error(result.error || '获取模型配置失败')
}

/**
 * 保存完整模型配置（结构化）
 */
export async function saveModelConfig(data: ModelConfigData): Promise<ModelConfigUpdateResponse> {
  const result = await api.put<ModelConfigUpdateResponse>(MODEL_CONFIG_ENDPOINTS.CONFIG, data)
  if (result.success && result.data) return result.data
  throw new Error(result.error || '保存模型配置失败')
}

/**
 * 获取原始 TOML 文本
 */
export async function getModelConfigRaw(): Promise<ModelConfigRawResponse> {
  const result = await api.get<ModelConfigRawResponse>(MODEL_CONFIG_ENDPOINTS.CONFIG_RAW)
  if (result.success && result.data) return result.data
  throw new Error(result.error || '获取原始配置失败')
}

/**
 * 保存原始 TOML 文本
 */
export async function saveModelConfigRaw(content: string): Promise<{ success: boolean; message: string }> {
  const result = await api.post<{ success: boolean; message: string }>(
    MODEL_CONFIG_ENDPOINTS.CONFIG_RAW,
    { content }
  )
  if (result.success && result.data) return result.data
  throw new Error(result.error || '保存原始配置失败')
}

/**
 * 获取备份列表
 */
export async function getModelConfigBackups(): Promise<ModelConfigBackupsResponse> {
  const result = await api.get<ModelConfigBackupsResponse>(MODEL_CONFIG_ENDPOINTS.BACKUPS)
  if (result.success && result.data) return result.data
  throw new Error(result.error || '获取备份列表失败')
}

/**
 * 从备份恢复模型配置
 */
export async function restoreModelConfigBackup(backupName: string): Promise<{ success: boolean; message: string }> {
  const result = await api.post<{ success: boolean; message: string }>(
    MODEL_CONFIG_ENDPOINTS.RESTORE(backupName)
  )
  if (result.success && result.data) return result.data
  throw new Error(result.error || '恢复备份失败')
}

/**
 * 测试模型连通性
 * 
 * 发送简单请求测试指定模型是否可用
 * @param modelName - 模型名称
 * @returns 测试结果，包括连接状态、响应时间等
 */
export async function testModelConnection(modelName: string): Promise<{ success: boolean; data?: ModelTestResponse; error?: string }> {
  const result = await api.post<ModelTestResponse>(MODEL_CONFIG_ENDPOINTS.TEST, { model_name: modelName })
  return result
}

// ==================== 工具函数 ====================

/** 默认任务配置工厂 */
export function createDefaultTaskConfig(): TaskConfigData {
  return {
    model_list: [],
    max_tokens: 800,
    temperature: 0.7,
    concurrency_count: 1,
    embedding_dimension: null,
  }
}

/** 默认 API 提供商工厂 */
export function createDefaultProvider(): APIProviderData {
  return {
    name: '',
    base_url: 'https://api.openai.com/v1',
    api_key: [],
    client_type: 'openai',
    max_retry: 3,
    timeout: 30,
    retry_interval: 10,
  }
}

/** 默认模型信息工厂 */
export function createDefaultModel(): ModelInfoData {
  return {
    name: '',
    model_identifier: '',
    api_provider: '',
    price_in: 0,
    price_out: 0,
    force_stream_mode: false,
    max_context: 32768,
    tool_call_compat: false,
    extra_params: {},
    anti_truncation: false,
  }
}

/** 所有预定义任务名称列表（有序） */
export const TASK_NAMES: (keyof ModelTasksData)[] = [
  'utils',
  'utils_small',
  'actor',
  'sub_actor',
  'vlm',
  'voice',
  'video',
  'tool_use',
  'embedding',
]

/** 任务中文名称映射 */
export const TASK_DISPLAY_NAMES: Record<keyof ModelTasksData, string> = {
  utils: '工具模型',
  utils_small: '小型工具模型',
  actor: '动作器',
  sub_actor: '副动作器',
  vlm: '视觉语言模型',
  voice: '语音识别',
  video: '视频分析',
  tool_use: '工具调用',
  embedding: '嵌入模型',
}

/** 任务描述映射 */
export const TASK_DESCRIPTIONS: Record<keyof ModelTasksData, string> = {
  utils: '在 MoFox 的一些组件中使用的模型，如表情包模块、取名模块、关系模块',
  utils_small: 'MoFox 中消耗量较大的小模型，建议使用速度较快的小模型',
  actor: '动作器模型，负责主要的对话生成',
  sub_actor: '副动作器模型，用于辅助任务',
  vlm: '图像识别模型，处理视觉输入',
  voice: '语音识别模型，将语音转为文本',
  video: '视频分析模型，处理视频内容',
  tool_use: '工具调用模型，需要支持 Function Call 的模型',
  embedding: '嵌入模型，用于语义向量化',
}

// ==================== 任务 Schema（后端驱动） ====================

/** 单个任务的 Schema 描述（由后端提供中文名称） */
export interface TaskSchemaItem {
  key: string
  name: string
  description: string
  category: 'core' | 'media' | 'memory' | 'other'
}

/** 任务 Schema 列表响应 */
export interface TasksSchemaResponse {
  tasks: TaskSchemaItem[]
}

/**
 * 获取所有任务的 Schema（中文名称、描述和分类）
 */
export async function getModelTasksSchema(): Promise<TaskSchemaItem[]> {
  const result = await api.get<TasksSchemaResponse>(`${BASE}/tasks-schema`)
  if (result.success && result.data) return result.data.tasks
  throw new Error(result.error || '获取任务 Schema 失败')
}
