/**
 * 仪表盘 API 模块
 * 包含所有仪表盘相关的类型定义和 API 方法
 */

import { api, API_ENDPOINTS } from './index'

// ==================== 仪表盘相关类型定义 ====================

/**
 * 插件统计信息
 * 用于仪表盘展示插件的各种状态数量
 */
export interface PluginStats {
  loaded: number
  registered: number
  failed: number
  enabled: number
  disabled: number
}

/**
 * 组件统计信息
 * 统计系统中各类组件的数量和状态
 */
export interface ComponentStats {
  /** 组件总数 */
  total: number
  /** 已启用的组件数 */
  enabled: number
  /** 已禁用的组件数 */
  disabled: number
  /** 按类型分组的组件统计（如：handler、decorator、scheduler 等） */
  by_type: Record<string, { total: number; enabled: number; disabled: number }>
}

/**
 * 聊天流统计信息
 * 统计各种聊天流的数量
 */
export interface ChatStats {
  /** 总聊天流数 */
  total_streams: number
  /** 群组聊天流数 */
  group_streams: number
  /** 私聊流数 */
  private_streams: number
  /** QQ 聊天流数 */
  qq_streams: number
}

/**
 * 系统统计信息
 * 系统运行状态的关键指标
 */
export interface SystemStats {
  /** 系统运行时间（秒） */
  uptime_seconds: number
  /** 内存使用量（MB） */
  memory_usage_mb: number
  /** 系统总内存（MB） */
  total_memory_mb: number
  /** CPU 使用率（百分比） */
  cpu_percent: number
}

/**
 * 仪表盘总览数据
 * 汇总所有关键统计信息
 */
export interface DashboardOverview {
  /** 插件统计 */
  plugins: PluginStats
  /** 组件统计 */
  components: ComponentStats
  /** 聊天流统计 */
  chats: ChatStats
  /** 系统统计 */
  system: SystemStats
}

/**
 * 插件详情信息
 * 单个插件的基本信息
 */
export interface PluginDetail {
  /** 插件名称（内部标识） */
  name: string
  /** 插件显示名称 */
  display_name: string
  /** 插件版本号 */
  version: string
  /** 插件作者 */
  author: string
  /** 是否已启用 */
  enabled: boolean
  /** 组件数量 */
  components_count: number
}

/**
 * 插件列表响应
 * 返回插件列表及总数
 */
export interface PluginListResponse {
  /** 插件列表 */
  plugins: PluginDetail[]
  /** 插件总数 */
  total: number
}

/**
 * 系统状态响应
 * 系统运行状态的详细信息
 */
export interface SystemStatusResponse {
  /** 运行时间（秒） */
  uptime_seconds: number
  /** 格式化的运行时间（如 "2天 3小时"） */
  uptime_formatted: string
  /** 内存使用量（MB） */
  memory_usage_mb: number
  /** 格式化的内存使用量（如 "128.5 MB"） */
  memory_usage_formatted: string
  /** CPU 使用率（百分比） */
  cpu_percent: number
  /** 线程数 */
  threads: number
}

/**
 * 日程活动项
 * 单个时间段的活动安排
 */
export interface ScheduleActivity {
  /** 时间范围（如 "09:00-10:00"） */
  time_range: string
  /** 活动内容描述 */
  activity: string
}

/**
 * 日程响应
 * 某一天的完整日程安排
 */
export interface ScheduleResponse {
  /** 日期（YYYY-MM-DD） */
  date: string
  /** 活动列表 */
  activities: ScheduleActivity[]
  /** 当前正在进行的活动 */
  current_activity: ScheduleActivity | null
}

/**
 * 月度计划响应
 * 某个月的计划列表
 */
export interface MonthlyPlanResponse {
  /** 计划列表 */
  plans: string[]
  /** 计划总数 */
  total: number
  /** 月份（YYYY-MM） */
  month: string
}

/**
 * LLM 使用统计响应
 * 大语言模型的使用情况统计
 */
export interface LLMStatsResponse {
  /** 总请求次数 */
  total_requests: number
  /** 总花费（单位：元或美元） */
  total_cost: number
  /** 总令牌数 */
  total_tokens: number
  /** 输入令牌数 */
  input_tokens: number
  /** 输出令牌数 */
  output_tokens: number
}

/**
 * 消息统计数据点
 * 时间序列数据中的单个点
 */
export interface MessageStatsDataPoint {
  /** 时间戳（ISO 格式） */
  timestamp: string
  /** 收到的消息数 */
  received: number
  /** 发送的消息数 */
  sent: number
}

/**
 * 消息统计响应
 * 消息收发的时间序列统计
 */
export interface MessageStatsResponse {
  /** 数据点列表（时间序列） */
  data_points: MessageStatsDataPoint[]
  /** 总接收消息数 */
  total_received: number
  /** 总发送消息数 */
  total_sent: number
  /** 统计周期（如 "last_24_hours"） */
  period: string
}

/**
 * 每日名言响应
 * 显示励志名言和作者信息
 */
export interface DailyQuoteResponse {
  /** 名言内容 */
  quote: string
  /** 作者 */
  author: string
  /** 分类（励志/哲学/科技等） */
  category: string
  /** 日期 YYYY-MM-DD */
  date: string
}

/**
 * 插件列表项（带错误信息）
 * 用于按状态分组的插件列表，包含加载失败信息
 */
export interface PluginListItem {
  /** 插件名称 */
  name: string
  /** 显示名称 */
  display_name: string
  /** 版本号 */
  version: string
  /** 作者 */
  author: string
  /** 是否启用 */
  enabled: boolean
  /** 组件数量 */
  components_count: number
  /** 错误信息（加载失败时） */
  error?: string
}

/**
 * 按状态分组的插件列表
 * 将插件分为已加载和加载失败两组
 */
export interface PluginsByStatusResponse {
  /** 成功加载的插件 */
  loaded: PluginListItem[]
  /** 加载失败的插件 */
  failed: PluginListItem[]
}

/**
 * 组件项
 * 单个组件的详细信息
 */
export interface ComponentItem {
  /** 组件名称 */
  name: string
  /** 所属插件名称 */
  plugin_name: string
  /** 组件描述 */
  description: string
  /** 是否启用 */
  enabled: boolean
}

/**
 * 按类型分组的组件列表
 * 返回特定类型的所有组件
 */
export interface ComponentsByTypeResponse {
  /** 组件类型（如 "handler"、"decorator" 等） */
  component_type: string
  /** 组件列表 */
  components: ComponentItem[]
  /** 总数 */
  total: number
  /** 已启用数 */
  enabled: number
  /** 已禁用数 */
  disabled: number
}

// ==================== 仪表盘 API 方法 ====================

/**
 * 获取仪表盘总览数据
 * 
 * 包含：插件统计、组件统计、聊天流统计、系统统计
 * 
 * @returns Promise 包含总览数据的响应对象
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

/**
 * 获取每日名言
 */
export async function getDailyQuote() {
  return api.get<DailyQuoteResponse>(API_ENDPOINTS.STATS.DAILY_QUOTE)
}
