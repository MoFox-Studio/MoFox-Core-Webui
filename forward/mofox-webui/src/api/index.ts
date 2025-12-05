/**
 * API 请求模块
 * 统一管理所有 API 请求
 */

// API 基础配置
const API_BASE_URL = `http://${window.location.hostname}:3001`
const PLUGIN_BASE_PATH = '/plugins/webui_backend'

/**
 * API 请求类
 */
class ApiClient {
  private baseUrl: string
  private token: string | null = null

  constructor(baseUrl: string = API_BASE_URL) {
    this.baseUrl = baseUrl
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
  private buildUrl(endpoint: string): string {
    // 移除开头的斜杠（如果有）
    const cleanEndpoint = endpoint.startsWith('/') ? endpoint.slice(1) : endpoint
    return `${this.baseUrl}${PLUGIN_BASE_PATH}/${cleanEndpoint}`
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
    const url = this.buildUrl(endpoint)
    
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
    PLUGIN_DETAIL: (name: string) => `stats/plugins/${name}`,
    SYSTEM: 'stats/system',
    SCHEDULE: 'stats/schedule',
    MONTHLY_PLANS: 'stats/monthly-plans',
    LLM_STATS: 'stats/llm-stats',
    MESSAGE_STATS: 'stats/message-stats'
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

// ==================== API 便捷方法 ====================

/**
 * 获取仪表盘总览数据
 */
export async function getDashboardOverview() {
  return api.get<DashboardOverview>(API_ENDPOINTS.STATS.OVERVIEW)
}

/**
 * 获取插件列表
 */
export async function getPluginList() {
  return api.get<PluginListResponse>(API_ENDPOINTS.STATS.PLUGINS)
}

/**
 * 获取插件详情
 */
export async function getPluginDetail(pluginName: string) {
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
