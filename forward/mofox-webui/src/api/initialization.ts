import { api } from './index'

// ==================== 初始化系统 API ====================

/**
 * 初始化状态响应
 */
export interface InitStatusResponse {
  is_initialized: boolean
}

/**
 * 机器人配置请求
 */
export interface BotConfigRequest {
  nickname: string
  alias_names: string[]
  personality_core: string
  identity: string
  reply_style: string
  owner_list: string[]   // Bot所有者列表，格式：["qq:123456", "telegram:789"]
}

/**
 * 模型配置请求
 */
export interface ModelConfigRequest {
  api_key: string
  provider_name?: string
  base_url?: string
}

/**
 * Git配置请求
 */
export interface GitConfigRequest {
  git_path: string
}

/**
 * 验证响应
 */
export interface ValidationResponse {
  valid: boolean
  message?: string
}

/**
 * Git检测响应
 */
export interface GitDetectResponse {
  found: boolean
  path?: string
}

/**
 * 操作响应
 */
export interface OperationResponse {
  success: boolean
  message?: string
  error?: string
}

/**
 * 获取初始化状态
 */
export async function getInitStatus() {
  return api.get<InitStatusResponse>('initialization/status')
}

/**
 * 获取机器人配置
 */
export async function getBotConfig() {
  return api.get<BotConfigRequest>('initialization/bot-config')
}

/**
 * 保存机器人配置
 */
export async function saveBotConfig(config: BotConfigRequest) {
  return api.post<OperationResponse>('initialization/bot-config', config)
}

/**
 * 获取模型配置
 */
export async function getModelConfig() {
  return api.get<ModelConfigRequest>('initialization/model-config')
}

/**
 * 保存模型配置
 */
export async function saveModelConfig(config: ModelConfigRequest) {
  return api.post<OperationResponse>('initialization/model-config', config)
}

/**
 * 获取Git配置
 */
export async function getGitConfig() {
  return api.get<GitConfigRequest>('initialization/git-config')
}

/**
 * 保存Git配置
 */
export async function saveGitConfig(config: GitConfigRequest) {
  return api.post<OperationResponse>('initialization/git-config', config)
}

/**
 * 完成初始化
 */
export async function completeInitialization() {
  return api.post<OperationResponse>('initialization/complete')
}

/**
 * 验证API密钥
 */
export async function validateApiKey(apiKey: string) {
  return api.post<ValidationResponse>('initialization/validate-api-key', { api_key: apiKey })
}

/**
 * 自动检测Git路径
 */
export async function detectGitPath() {
  return api.get<GitDetectResponse>('initialization/detect-git')
}
