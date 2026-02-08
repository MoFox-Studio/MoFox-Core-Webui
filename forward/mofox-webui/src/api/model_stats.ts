/**
 * 模型统计 API 模块
 * 提供模型使用统计、提供商统计、模块统计等相关API
 */

import { api } from './index'

// ==================== API 端点 ====================

const MODEL_STATS_ENDPOINTS = {
  MODEL_USAGE: 'model_stats/model_usage',
  MODEL_OVERVIEW: 'model_stats/model_overview',
  MODEL_DETAIL: (modelName: string) => `model_stats/model_detail/${modelName}`,
  PROVIDER_STATS: 'model_stats/provider_stats',
  MODULE_STATS: 'model_stats/module_stats',
  CHART_DATA: 'model_stats/chart_data'
} as const

// ==================== 类型定义 ====================

/** 模型使用统计响应 */
export interface ModelUsageStatsResponse {
  stats: Record<string, {
    total_calls: number
    prompt_tokens: number
    completion_tokens: number
    total_tokens: number
  }>
}

/** 模型统计总览响应 */
export interface ModelOverviewResponse {
  total_models: number
  total_calls: number
  total_tokens: number
  total_cost: number
  most_used_model: string | null
  most_expensive_model: string | null
}

/** 模型详细统计响应 */
export interface ModelDetailResponse {
  model_name: string
  total_calls: number
  prompt_tokens: number
  completion_tokens: number
  total_tokens: number
  total_cost: number
  avg_tokens_per_call: number
  avg_time_per_call: number
  tps: number
  cost_per_ktok: number
}

/** 提供商统计项 */
export interface ProviderStatsItem {
  total_calls: number
  total_tokens: number
  total_cost: number
  avg_time: number
  tps: number
}

/** 提供商统计响应 */
export interface ProviderStatsResponse {
  stats: Record<string, ProviderStatsItem>
}

/** 模块统计项 */
export interface ModuleStatsItem {
  total_calls: number
  total_tokens: number
  total_cost: number
  avg_time: number
}

/** 模块统计响应 */
export interface ModuleStatsResponse {
  stats: Record<string, ModuleStatsItem>
}

/** 图表数据响应 */
export interface ChartDataResponse {
  chart_data: {
    pie_chart_cost_by_provider?: {
      labels: string[]
      data: number[]
    }
    pie_chart_req_by_provider?: {
      labels: string[]
      data: number[]
    }
    pie_chart_cost_by_module?: {
      labels: string[]
      data: number[]
    }
    bar_chart_cost_by_model?: {
      labels: string[]
      data: number[]
    }
    bar_chart_req_by_model?: {
      labels: string[]
      data: number[]
    }
    bar_chart_token_comparison?: {
      labels: string[]
      data: number[]
    }
    bar_chart_avg_response_time?: {
      labels: string[]
      data: number[]
    }
    [key: string]: any
  }
}

// ==================== API 方法 ====================

/**
 * 获取模型使用统计
 * @param timeRange - 时间范围：'1h' | '24h' | '7d' | '30d'| 'all'
 * @returns 模型使用统计数据
 */
export async function getModelUsageStats(timeRange: '1h' | '24h' | '7d' | '30d' | 'all' = '24h') {
  return api.get<ModelUsageStatsResponse>(`${MODEL_STATS_ENDPOINTS.MODEL_USAGE}?time_range=${timeRange}`)
}

/**
 * 获取模型统计总览
 * @param timeRange - 时间范围：'1h' | '24h' | '7d' | '30d'| 'all'
 * @returns 模型统计总览数据
 */
export async function getModelOverview(timeRange: '1h' | '24h' | '7d' | '30d' | 'all' = '24h') {
  return api.get<ModelOverviewResponse>(`${MODEL_STATS_ENDPOINTS.MODEL_OVERVIEW}?time_range=${timeRange}`)
}

/**
 * 获取模型详细统计
 * @param modelName - 模型名称
 * @param timeRange - 时间范围：'1h' | '24h' | '7d' | '30d'| 'all'
 * @returns 指定模型的详细统计数据
 */
export async function getModelDetail(modelName: string, timeRange: '1h' | '24h' | '7d' | '30d' | 'all' = '24h') {
  return api.get<ModelDetailResponse>(`${MODEL_STATS_ENDPOINTS.MODEL_DETAIL(modelName)}?time_range=${timeRange}`)
}

/**
 * 获取提供商统计
 * @param timeRange - 时间范围：'1h' | '24h' | '7d' | '30d' | 'all'
 * @returns 提供商统计数据
 */
export async function getProviderStats(timeRange: '1h' | '24h' | '7d' | '30d' | 'all' = '24h') {
  return api.get<ProviderStatsResponse>(`${MODEL_STATS_ENDPOINTS.PROVIDER_STATS}?time_range=${timeRange}`)
}

/**
 * 获取模块统计
 * @param timeRange - 时间范围：'1h' | '24h' | '7d' | '30d'| 'all'
 * @returns 模块统计数据
 */
export async function getModuleStats(timeRange: '1h' | '24h' | '7d' | '30d' | 'all' = '24h') {
  return api.get<ModuleStatsResponse>(`${MODEL_STATS_ENDPOINTS.MODULE_STATS}?time_range=${timeRange}`)
}

/**
 * 获取图表数据
 * @param timeRange - 时间范围：'1h' | '24h' | '7d' | '30d'| 'all'
 * @returns 用于前端图表展示的数据
 */
export async function getChartData(timeRange: '1h' | '24h' | '7d' | '30d' | 'all' = '24h') {
  return api.get<ChartDataResponse>(`${MODEL_STATS_ENDPOINTS.CHART_DATA}?time_range=${timeRange}`)
}
