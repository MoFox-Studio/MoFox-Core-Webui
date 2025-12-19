/**
 * API 请求模块
 * 统一管理所有 API 请求
 */

// 发现服务器配置（固定端口，用于获取主程序信息）
const DISCOVERY_SERVER_PORT = 12138
const DISCOVERY_SERVER_URL = `http://${window.location.hostname}:${DISCOVERY_SERVER_PORT}`

// 插件 API 路径
const PLUGIN_BASE_PATH = '/plugins/webui_backend'

// 缓存的服务器信息
let cachedServerInfo: { host: string; port: number } | null = null

/**
 * 服务器信息接口
 */
interface ServerInfo {
  host: string
  port: number
}

/**
 * 从发现服务器获取主程序信息
 */
export async function getServerInfo(): Promise<ServerInfo> {
  // 如果有缓存，直接返回
  if (cachedServerInfo) {
    return cachedServerInfo
  }

  try {
    const response = await fetch(`${DISCOVERY_SERVER_URL}/api/server-info`)
    if (!response.ok) {
      throw new Error(`发现服务器请求失败: ${response.status}`)
    }
    const data = await response.json()
    cachedServerInfo = { host: data.host, port: data.port }
    return cachedServerInfo
  } catch (error) {
    console.error('无法连接到发现服务器:', error)
    throw error
  }
}

/**
 * 清除服务器信息缓存（用于重新获取）
 */
export function clearServerInfoCache() {
  cachedServerInfo = null
}

/**
 * 获取 API 基础 URL（从发现服务器获取的主程序地址）
 */
export async function getApiBaseUrl(): Promise<string> {
  const serverInfo = await getServerInfo()
  return `http://${serverInfo.host}:${serverInfo.port}`
}

/**
 * API 请求类
 */
class ApiClient {
  private token: string | null = null

  constructor() {
    this.token = localStorage.getItem('mofox_token')
  }

  /**
   * 设置 API Token
   */
  setToken(token: string | null) {
    this.token = token
    if (token) {
      localStorage.setItem('mofox_token', token)
    } else {
      localStorage.removeItem('mofox_token')
    }
  }

  /**
   * 获取当前 Token
   */
  getToken(): string | null {
    return this.token
  }

  /**
   * 构建完整的 API URL
   * @param endpoint - API 端点，如 'auth/login'
   */
  private async buildUrl(endpoint: string): Promise<string> {
    const baseUrl = await getApiBaseUrl()
    // 移除开头的斜杠（如果有）
    const cleanEndpoint = endpoint.startsWith('/') ? endpoint.slice(1) : endpoint
    return `${baseUrl}${PLUGIN_BASE_PATH}/${cleanEndpoint}`
  }

  /**
   * 通用请求方法
   * @param endpoint - API 端点，如 'auth/login'
   * @param options - fetch 请求选项
   */
  async request<T = unknown>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<{ success: boolean; data?: T; error?: string; status: number }> {
    const url = await this.buildUrl(endpoint)
    
    const headers = new Headers(options.headers)
    
    // 添加认证头
    if (this.token) {
      headers.set('X-API-Key', this.token)
    }
    
    // 设置默认 Content-Type
    if (!headers.has('Content-Type') && options.body) {
      headers.set('Content-Type', 'application/json')
    }

    try {
      const response = await fetch(url, {
        ...options,
        headers
      })

      const status = response.status

      // 尝试解析 JSON 响应
      let data: T | undefined
      try {
        data = await response.json()
      } catch {
        // 响应不是 JSON 格式
      }

      if (response.ok) {
        return { success: true, data, status }
      } else {
        return { 
          success: false, 
          error: (data as Record<string, unknown>)?.error as string || `请求失败: ${status}`,
          status 
        }
      }
    } catch (error) {
      console.error('API 请求错误:', error)
      return { 
        success: false, 
        error: error instanceof Error ? error.message : '网络请求失败',
        status: 0 
      }
    }
  }

  /**
   * GET 请求
   */
  async get<T = unknown>(endpoint: string, options: RequestInit = {}) {
    return this.request<T>(endpoint, { ...options, method: 'GET' })
  }

  /**
   * POST 请求
   */
  async post<T = unknown>(endpoint: string, body?: unknown, options: RequestInit = {}) {
    return this.request<T>(endpoint, {
      ...options,
      method: 'POST',
      body: body ? JSON.stringify(body) : undefined
    })
  }

  /**
   * PUT 请求
   */
  async put<T = unknown>(endpoint: string, body?: unknown, options: RequestInit = {}) {
    return this.request<T>(endpoint, {
      ...options,
      method: 'PUT',
      body: body ? JSON.stringify(body) : undefined
    })
  }

  /**
   * DELETE 请求
   */
  async delete<T = unknown>(endpoint: string, options: RequestInit = {}) {
    return this.request<T>(endpoint, { ...options, method: 'DELETE' })
  }
}

// 导出单例实例
export const api = new ApiClient()

// 导出类以便需要时创建新实例
export { ApiClient }

// 常用 API 端点
export const API_ENDPOINTS = {
  AUTH: {
    LOGIN: 'auth/login',
    LOGOUT: 'auth/logout',
    VERIFY: 'auth/verify',
    HEALTH: 'auth/health'
  },
  STATS: {
    OVERVIEW: 'stats/overview',
    PLUGINS: 'stats/plugins',
    PLUGINS_BY_STATUS: 'stats/plugins-by-status',
    PLUGIN_DETAIL: (name: string) => `stats/plugins/${name}`,
    COMPONENTS_BY_TYPE: (type: string) => `stats/components-by-type/${type}`,
    SYSTEM: 'stats/system',
    SYSTEM_RESTART: 'stats/system/restart',
    SYSTEM_SHUTDOWN: 'stats/system/shutdown',
    SCHEDULE: 'stats/schedule',
    MONTHLY_PLANS: 'stats/monthly-plans',
    LLM_STATS: 'stats/llm-stats',
    MESSAGE_STATS: 'stats/message-stats'
  },
  CONFIG: {
    LIST: 'config/list',
    CONTENT: (path: string) => `config/content/${path}`,
    SCHEMA: (path: string) => `config/schema/${path}`,
    SAVE: (path: string) => `config/save/${path}`,
    UPDATE: (path: string) => `config/update/${path}`,
    BACKUPS: (path: string) => `config/backups/${path}`,
    RESTORE: (path: string) => `config/restore/${path}`,
    VALIDATE: 'config/validate'
  },
  PLUGIN: {
    LIST: 'plugin_manager/plugins',
    DETAIL: (name: string) => `plugin_manager/plugins/${name}`,
    STATUS: (name: string) => `plugin_manager/plugins/${name}/status`,
    ENABLE: (name: string) => `plugin_manager/plugins/${name}/enable`,
    DISABLE: (name: string) => `plugin_manager/plugins/${name}/disable`,
    RELOAD: (name: string) => `plugin_manager/plugins/${name}/reload`,
    UNLOAD: (name: string) => `plugin_manager/plugins/${name}/unload`,
    DELETE: (name: string) => `plugin_manager/plugins/${name}/delete`,
    LOAD: (name: string) => `plugin_manager/plugins/${name}/load`,
    COMPONENTS: (name: string) => `plugin_manager/plugins/${name}/components`,
    COMPONENT_ENABLE: (pluginName: string, componentName: string, type: string) => 
      `plugin_manager/plugins/${pluginName}/components/${componentName}/enable?component_type=${type}`,
    COMPONENT_DISABLE: (pluginName: string, componentName: string, type: string) => 
      `plugin_manager/plugins/${pluginName}/components/${componentName}/disable?component_type=${type}`,
    SCAN: 'plugin_manager/plugins/scan',
    RELOAD_ALL: 'plugin_manager/plugins/reload-all',
    BATCH_ENABLE: 'plugin_manager/plugins/batch/enable',
    BATCH_DISABLE: 'plugin_manager/plugins/batch/disable',
    BATCH_RELOAD: 'plugin_manager/plugins/batch/reload'
  }
} as const

// ==================== 类型定义 ====================

/** 插件统计 */
export interface PluginStats {
  loaded: number
  registered: number
  failed: number
  enabled: number
  disabled: number
}

/** 组件统计 */
export interface ComponentStats {
  total: number
  enabled: number
  disabled: number
  by_type: Record<string, { total: number; enabled: number; disabled: number }>
}

/** 聊天流统计 */
export interface ChatStats {
  total_streams: number
  group_streams: number
  private_streams: number
  qq_streams: number
}

/** 系统统计 */
export interface SystemStats {
  uptime_seconds: number
  memory_usage_mb: number
  cpu_percent: number
}

/** 仪表盘总览数据 */
export interface DashboardOverview {
  plugins: PluginStats
  components: ComponentStats
  chats: ChatStats
  system: SystemStats
}

/** 插件详情 */
export interface PluginDetail {
  name: string
  display_name: string
  version: string
  author: string
  enabled: boolean
  components_count: number
}

/** 插件列表响应 */
export interface PluginListResponse {
  plugins: PluginDetail[]
  total: number
}

/** 系统状态响应 */
export interface SystemStatusResponse {
  uptime_seconds: number
  uptime_formatted: string
  memory_usage_mb: number
  memory_usage_formatted: string
  cpu_percent: number
  threads: number
}

/** 日程活动 */
export interface ScheduleActivity {
  time_range: string
  activity: string
}

/** 日程响应 */
export interface ScheduleResponse {
  date: string
  activities: ScheduleActivity[]
  current_activity: ScheduleActivity | null
}

/** 月度计划响应 */
export interface MonthlyPlanResponse {
  plans: string[]
  total: number
  month: string
}

/** LLM 统计响应 */
export interface LLMStatsResponse {
  total_requests: number
  total_cost: number
  total_tokens: number
  input_tokens: number
  output_tokens: number
}

/** 消息统计数据点 */
export interface MessageStatsDataPoint {
  timestamp: string
  received: number
  sent: number
}

/** 消息统计响应 */
export interface MessageStatsResponse {
  data_points: MessageStatsDataPoint[]
  total_received: number
  total_sent: number
  period: string
}

/** 插件列表项（带错误信息） */
export interface PluginListItem {
  name: string
  display_name: string
  version: string
  author: string
  enabled: boolean
  components_count: number
  error?: string
}

/** 按状态分组的插件列表 */
export interface PluginsByStatusResponse {
  loaded: PluginListItem[]
  failed: PluginListItem[]
}

/** 组件项 */
export interface ComponentItem {
  name: string
  plugin_name: string
  description: string
  enabled: boolean
}

/** 按类型分组的组件列表 */
export interface ComponentsByTypeResponse {
  component_type: string
  components: ComponentItem[]
  total: number
  enabled: number
  disabled: number
}

// ==================== API 便捷方法 ====================

/**
 * 获取仪表盘总览数据
 */
export async function getDashboardOverview() {
  return api.get<DashboardOverview>(API_ENDPOINTS.STATS.OVERVIEW)
}

/**
 * 获取插件列表（按状态分组，用于仪表盘）
 */
export async function getPluginsByStatus() {
  return api.get<PluginsByStatusResponse>(API_ENDPOINTS.STATS.PLUGINS_BY_STATUS)
}

/**
 * 获取插件详情（Stats API，用于仪表盘）
 */
export async function getPluginDetailForStats(pluginName: string) {
  return api.get<{ success: boolean; plugin?: Record<string, unknown>; error?: string }>(
    API_ENDPOINTS.STATS.PLUGIN_DETAIL(pluginName)
  )
}

/**
 * 获取系统状态
 */
export async function getSystemStatus() {
  return api.get<SystemStatusResponse>(API_ENDPOINTS.STATS.SYSTEM)
}

/**
 * 重启 Bot
 */
export async function restartBot() {
  return api.post<{ success: boolean; message?: string; error?: string }>(
    API_ENDPOINTS.STATS.SYSTEM_RESTART
  )
}

/**
 * 关闭 Bot
 */
export async function shutdownBot() {
  return api.post<{ success: boolean; message?: string; error?: string }>(
    API_ENDPOINTS.STATS.SYSTEM_SHUTDOWN
  )
}

/**
 * 获取今日日程
 */
export async function getTodaySchedule(date?: string) {
  const endpoint = date 
    ? `${API_ENDPOINTS.STATS.SCHEDULE}?date=${date}` 
    : API_ENDPOINTS.STATS.SCHEDULE
  return api.get<ScheduleResponse>(endpoint)
}

/**
 * 获取月度计划
 */
export async function getMonthlyPlans(month?: string, limit: number = 10) {
  let endpoint = API_ENDPOINTS.STATS.MONTHLY_PLANS
  const params = new URLSearchParams()
  if (month) params.append('month', month)
  if (limit) params.append('limit', limit.toString())
  const queryString = params.toString()
  if (queryString) endpoint += `?${queryString}`
  return api.get<MonthlyPlanResponse>(endpoint)
}

/**
 * 获取 LLM 使用统计
 */
export async function getLLMStats(period: 'last_hour' | 'last_24_hours' | 'last_7_days' | 'last_30_days' = 'last_24_hours') {
  const endpoint = `${API_ENDPOINTS.STATS.LLM_STATS}?period=${period}`
  return api.get<LLMStatsResponse>(endpoint)
}

/**
 * 获取消息收发统计
 */
export async function getMessageStats(period: 'last_hour' | 'last_24_hours' | 'last_7_days' | 'last_30_days' = 'last_24_hours') {
  const endpoint = `${API_ENDPOINTS.STATS.MESSAGE_STATS}?period=${period}`
  return api.get<MessageStatsResponse>(endpoint)
}

/**
 * 获取按类型分组的组件列表
 */
export async function getComponentsByType(componentType: string, enabledOnly: boolean = false) {
  const endpoint = `${API_ENDPOINTS.STATS.COMPONENTS_BY_TYPE(componentType)}?enabled_only=${enabledOnly}`
  return api.get<ComponentsByTypeResponse>(endpoint)
}

// ==================== 配置管理相关类型 ====================

/** 配置文件信息 */
export interface ConfigFileInfo {
  name: string
  display_name: string
  path: string
  type: 'main' | 'model' | 'plugin'
  plugin_name?: string
  description?: string
  last_modified?: string
}

/** 配置文件列表响应 */
export interface ConfigListResponse {
  configs: ConfigFileInfo[]
  total: number
}

/** 配置文件内容响应 */
export interface ConfigContentResponse {
  success: boolean
  path: string
  content?: string
  parsed?: Record<string, unknown>
  error?: string
}

/** 配置字段 */
export interface ConfigSchemaField {
  key: string
  full_key: string
  type: string
  value: unknown
  description?: string
  items_count?: number
  readonly?: boolean
}

/** 配置 Section */
export interface ConfigSection {
  name: string
  display_name: string
  fields: ConfigSchemaField[]
}

/** 配置模式响应 */
export interface ConfigSchemaResponse {
  success: boolean
  path: string
  sections: ConfigSection[]
  error?: string
}

/** 保存配置响应 */
export interface SaveConfigResponse {
  success: boolean
  message?: string
  backup_path?: string
  error?: string
}

/** 配置备份信息 */
export interface ConfigBackupInfo {
  name: string
  path: string
  created_at: string
  size: number
}

/** 配置备份列表响应 */
export interface ConfigBackupsResponse {
  success: boolean
  backups: ConfigBackupInfo[]
  error?: string
}

/** 验证 TOML 响应 */
export interface ValidateTomlResponse {
  success: boolean
  valid?: boolean
  message?: string
  line?: number
  col?: number
  error?: string
}

// ==================== 配置管理 API 方法 ====================

/**
 * 获取配置文件列表
 */
export async function getConfigList() {
  return api.get<ConfigListResponse>(API_ENDPOINTS.CONFIG.LIST)
}

/**
 * 获取配置文件内容
 */
export async function getConfigContent(path: string) {
  return api.get<ConfigContentResponse>(API_ENDPOINTS.CONFIG.CONTENT(path))
}

/**
 * 获取配置文件结构（用于可视化编辑）
 */
export async function getConfigSchema(path: string) {
  return api.get<ConfigSchemaResponse>(API_ENDPOINTS.CONFIG.SCHEMA(path))
}

/**
 * 保存配置文件（原始 TOML）
 */
export async function saveConfig(path: string, content: string, createBackup: boolean = true) {
  return api.post<SaveConfigResponse>(API_ENDPOINTS.CONFIG.SAVE(path), {
    content,
    create_backup: createBackup
  })
}

/**
 * 更新配置文件（可视化编辑）
 */
export async function updateConfig(path: string, updates: Record<string, unknown>, createBackup: boolean = true) {
  return api.post<SaveConfigResponse>(API_ENDPOINTS.CONFIG.UPDATE(path), {
    updates,
    create_backup: createBackup
  })
}

// ==================== 插件管理类型定义 ====================

/** 插件项 */
export interface PluginItem {
  name: string
  display_name: string
  version: string
  author: string
  description?: string
  enabled: boolean
  loaded: boolean
  components_count: number
  last_updated?: string
  config_path?: string
  error?: string
  plugin_type?: string  // 插件类型: "system" 表示系统插件
}

/** 插件管理列表响应 */
export interface PluginManageListResponse {
  success: boolean
  plugins: PluginItem[]
  failed_plugins: PluginItem[]  // 加载失败的插件列表
  total: number
  loaded: number
  enabled: number
  failed: number
  error?: string
}

/** 组件项 */
export interface PluginComponent {
  name: string
  type: string
  description?: string
  enabled: boolean
  plugin_name: string
  details?: Record<string, unknown>
}

/** 组件列表响应 */
export interface ComponentsResponse {
  success: boolean
  plugin_name: string
  components: PluginComponent[]
  total: number
  enabled: number
  disabled: number
  error?: string
}

/** 插件详细信息 */
export interface PluginDetailInfo {
  name: string
  display_name: string
  version: string
  author: string
  description?: string
  enabled: boolean
  loaded: boolean
  components: PluginComponent[]
  components_count: number
  config: {
    path: string
    exists: boolean
  }
  metadata?: Record<string, unknown>
}

/** 插件详情响应 */
export interface PluginDetailResponse {
  success: boolean
  plugin?: PluginDetailInfo
  error?: string
}

/** 操作响应 */
export interface OperationResponse {
  success: boolean
  message?: string
  error?: string
}

/** 扫描结果响应 */
export interface ScanResultResponse {
  success: boolean
  registered: number
  loaded: number
  failed: number
  new_plugins: string[]
  error?: string
}

/** 批量操作响应 */
export interface BatchOperationResponse {
  success: boolean
  results: Record<string, { success: boolean; message?: string; error?: string }>
  total: number
  succeeded: number
  failed: number
}

// ==================== 插件管理 API 方法 ====================

/**
 * 获取所有插件列表
 */
export async function getPluginList() {
  return api.get<PluginManageListResponse>(API_ENDPOINTS.PLUGIN.LIST)
}

/**
 * 获取插件详情
 */
export async function getPluginDetail(pluginName: string) {
  return api.get<PluginDetailResponse>(API_ENDPOINTS.PLUGIN.DETAIL(pluginName))
}

/**
 * 获取插件状态
 */
export async function getPluginStatus(pluginName: string) {
  return api.get<{ success: boolean; plugin_name: string; loaded: boolean; enabled: boolean }>(
    API_ENDPOINTS.PLUGIN.STATUS(pluginName)
  )
}

/**
 * 启用插件
 */
export async function enablePlugin(pluginName: string) {
  return api.post<OperationResponse>(API_ENDPOINTS.PLUGIN.ENABLE(pluginName))
}

/**
 * 禁用插件
 */
export async function disablePlugin(pluginName: string) {
  return api.post<OperationResponse>(API_ENDPOINTS.PLUGIN.DISABLE(pluginName))
}

/**
 * 重载插件
 */
export async function reloadPlugin(pluginName: string) {
  return api.post<OperationResponse>(API_ENDPOINTS.PLUGIN.RELOAD(pluginName))
}

/**
 * 卸载插件
 */
export async function unloadPlugin(pluginName: string) {
  return api.post<OperationResponse>(API_ENDPOINTS.PLUGIN.UNLOAD(pluginName))
}

/**
 * 删除插件（删除文件夹）
 */
export async function deletePlugin(pluginName: string) {
  return api.delete<OperationResponse>(API_ENDPOINTS.PLUGIN.DELETE(pluginName))
}

/**
 * 加载插件
 */
export async function loadPlugin(pluginName: string) {
  return api.post<OperationResponse>(API_ENDPOINTS.PLUGIN.LOAD(pluginName))
}

/**
 * 获取插件的所有组件
 */
export async function getPluginComponents(pluginName: string) {
  return api.get<ComponentsResponse>(API_ENDPOINTS.PLUGIN.COMPONENTS(pluginName))
}

/**
 * 启用组件
 */
export async function enableComponent(pluginName: string, componentName: string, componentType: string) {
  return api.post<OperationResponse>(
    API_ENDPOINTS.PLUGIN.COMPONENT_ENABLE(pluginName, componentName, componentType)
  )
}

/**
 * 禁用组件
 */
export async function disableComponent(pluginName: string, componentName: string, componentType: string) {
  return api.post<OperationResponse>(
    API_ENDPOINTS.PLUGIN.COMPONENT_DISABLE(pluginName, componentName, componentType)
  )
}

/**
 * 扫描新插件
 */
export async function scanPlugins(loadAfterRegister: boolean = true) {
  return api.post<ScanResultResponse>(API_ENDPOINTS.PLUGIN.SCAN, {
    load_after_register: loadAfterRegister
  })
}

/**
 * 重载所有插件
 */
export async function reloadAllPlugins() {
  return api.post<OperationResponse>(API_ENDPOINTS.PLUGIN.RELOAD_ALL)
}

/**
 * 批量启用插件
 */
export async function batchEnablePlugins(pluginNames: string[]) {
  return api.post<BatchOperationResponse>(API_ENDPOINTS.PLUGIN.BATCH_ENABLE, {
    plugin_names: pluginNames
  })
}

/**
 * 批量禁用插件
 */
export async function batchDisablePlugins(pluginNames: string[]) {
  return api.post<BatchOperationResponse>(API_ENDPOINTS.PLUGIN.BATCH_DISABLE, {
    plugin_names: pluginNames
  })
}

/**
 * 批量重载插件
 */
export async function batchReloadPlugins(pluginNames: string[]) {
  return api.post<BatchOperationResponse>(API_ENDPOINTS.PLUGIN.BATCH_RELOAD, {
    plugin_names: pluginNames
  })
}

/**
 * 获取配置备份列表
 */
export async function getConfigBackups(path: string) {
  return api.get<ConfigBackupsResponse>(API_ENDPOINTS.CONFIG.BACKUPS(path))
}

/**
 * 从备份恢复配置
 */
export async function restoreConfigBackup(path: string, backupName: string) {
  return api.post<SaveConfigResponse>(`${API_ENDPOINTS.CONFIG.RESTORE(path)}?backup_name=${encodeURIComponent(backupName)}`)
}

/**
 * 验证 TOML 内容
 */
export async function validateToml(content: string) {
  return api.post<ValidateTomlResponse>(API_ENDPOINTS.CONFIG.VALIDATE, content)
}
