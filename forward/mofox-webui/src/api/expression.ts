/**
 * 表达方式管理 API
 */

import { api } from './index'

/**
 * 表达方式类型
 */
export type ExpressionType = 'style' | 'grammar'

/**
 * 排序字段
 */
export type SortByField = 'count' | 'last_active_time' | 'create_date'

/**
 * 搜索范围
 */
export type SearchField = 'situation' | 'style' | 'both'

/**
 * 合并策略
 */
export type MergeStrategy = 'skip' | 'replace' | 'merge'

/**
 * 表达方式信息
 */
export interface Expression {
  id: number
  situation: string
  style: string
  count: number
  last_active_time: number
  chat_id: string  // 哈希值，用于后端操作
  chat_id_display?: string  // 格式化显示：platform:raw_id:type（可选，兼容旧数据）
  chat_platform?: string  // 平台（如：QQ、OneBot）（可选）
  chat_raw_id?: string  // 原始ID（群号或用户ID）（可选）
  chat_type?: string  // 类型（group/private）（可选）
  chat_name: string
  type: ExpressionType
  create_date: number
}

/**
 * 表达方式详情
 */
export interface ExpressionDetail extends Expression {
  usage_stats: {
    days_since_create: number
    days_since_last_use: number
    usage_frequency: number
  }
}

/**
 * 表达方式列表响应
 */
export interface ExpressionListResponse {
  expressions: Expression[]
  total: number
  page: number
  page_size: number
  total_pages: number
}

/**
 * 搜索结果响应
 */
export interface SearchExpressionsResponse {
  results: Expression[]
  total: number
}

/**
 * 统计信息响应
 */
export interface ExpressionStatistics {
  total_count: number
  style_count: number
  grammar_count: number
  top_used: Array<{
    id: number
    situation: string
    style: string
    count: number
    chat_name: string
    type: ExpressionType
  }>
  recent_added: Array<{
    id: number
    situation: string
    style: string
    count: number
    chat_name: string
    type: ExpressionType
    create_date: number
  }>
  chat_distribution: Record<
    string,
    {
      count: number
      chat_id: string
    }
  >
}

/**
 * 共享组信息
 */
export interface SharingGroup {
  group_name: string
  chat_streams: Array<{
    chat_id: string
    chat_name: string
    stream_config: string
    learn_expression: boolean
    use_expression: boolean
  }>
  expression_count: number
}

/**
 * 共享组列表响应
 */
export interface SharingGroupsResponse {
  groups: SharingGroup[]
  total: number
}

/**
 * 关联聊天流响应
 */
export interface RelatedChatsResponse {
  chat_ids: Array<{
    chat_id: string
    chat_name: string
  }>
  total: number
}

/**
 * 创建表达方式请求
 */
export interface CreateExpressionRequest {
  situation: string
  style: string
  chat_id: string
  type?: ExpressionType
  count?: number
}

/**
 * 更新表达方式请求
 */
export interface UpdateExpressionRequest {
  situation?: string
  style?: string
  count?: number
  type?: ExpressionType
}

/**
 * 导入表达方式请求
 */
export interface ImportExpressionsRequest {
  data: string
  format?: 'json' | 'csv'
  chat_id?: string
  merge_strategy?: MergeStrategy
}

/**
 * 导入结果响应
 */
export interface ImportResult {
  imported: number
  skipped: number
  replaced: number
  errors: string[]
}

/**
 * 导出结果响应
 */
export interface ExportResult {
  data: string
  format: 'json' | 'csv'
}

// ==================== 查询接口 ====================

/**
 * 获取表达方式列表
 */
export async function getExpressionList(
  page: number = 1,
  pageSize: number = 20,
  chatId?: string,
  type?: ExpressionType,
  sortBy: SortByField = 'last_active_time',
  sortOrder: 'asc' | 'desc' = 'desc'
) {
  const params = new URLSearchParams()
  params.append('page', page.toString())
  params.append('page_size', pageSize.toString())
  if (chatId) params.append('chat_id', chatId)
  if (type) params.append('type', type)
  params.append('sort_by', sortBy)
  params.append('sort_order', sortOrder)

  return await api.get<ExpressionListResponse>(`expression/list?${params.toString()}`)
}

/**
 * 获取表达方式详情
 */
export async function getExpressionDetail(expressionId: number) {
  return await api.get<ExpressionDetail>(`expression/${expressionId}`)
}

/**
 * 搜索表达方式
 */
export async function searchExpressions(
  keyword: string,
  searchField: SearchField = 'both',
  chatId?: string,
  type?: ExpressionType,
  limit: number = 50
) {
  const params = new URLSearchParams()
  params.append('keyword', keyword)
  params.append('search_field', searchField)
  if (chatId) params.append('chat_id', chatId)
  if (type) params.append('type', type)
  params.append('limit', limit.toString())

  return await api.get<SearchExpressionsResponse>(`expression/search/query?${params.toString()}`)
}

/**
 * 获取统计信息
 */
export async function getStatistics(chatId?: string) {
  const params = chatId ? `?chat_id=${chatId}` : ''
  return await api.get<ExpressionStatistics>(`expression/statistics/overview${params}`)
}

// ==================== 管理接口 ====================

/**
 * 创建表达方式
 */
export async function createExpression(data: CreateExpressionRequest) {
  return await api.post<ExpressionDetail>('expression/', data)
}

/**
 * 更新表达方式
 */
export async function updateExpression(expressionId: number, data: UpdateExpressionRequest) {
  return await api.put<{ success: boolean }>(`expression/${expressionId}`, data)
}

/**
 * 删除表达方式
 */
export async function deleteExpression(expressionId: number) {
  return await api.delete<{ success: boolean }>(`expression/${expressionId}`)
}

/**
 * 批量删除表达方式
 */
export async function batchDeleteExpressions(expressionIds: number[]) {
  return await api.post<{ deleted: number }>('expression/batch-delete', {
    expression_ids: expressionIds
  })
}

/**
 * 激活表达方式（增加权重）
 */
export async function activateExpression(expressionId: number, increment: number = 0.1) {
  return await api.post<{ success: boolean }>(`expression/${expressionId}/activate?increment=${increment}`)
}

/**
 * 清理过期表达方式
 */
export async function cleanupExpired(chatId?: string, expirationDays?: number) {
  const params = new URLSearchParams()
  if (chatId) params.append('chat_id', chatId)
  if (expirationDays) params.append('expiration_days', expirationDays.toString())

  const queryStr = params.toString()
  return await api.post<{ deleted: number }>(`expression/cleanup${queryStr ? '?' + queryStr : ''}`)
}

// ==================== 共享组接口 ====================

/**
 * 获取共享组列表
 */
export async function getSharingGroups() {
  return await api.get<SharingGroupsResponse>('expression/sharing-groups/list')
}

/**
 * 获取关联聊天流
 */
export async function getRelatedChats(chatId: string) {
  return await api.get<RelatedChatsResponse>(`expression/related-chats/${chatId}`)
}

// ==================== 导入导出接口 ====================

/**
 * 导出表达方式
 */
export async function exportExpressions(
  chatId?: string,
  type?: ExpressionType,
  format: 'json' | 'csv' = 'json'
) {
  const params = new URLSearchParams()
  if (chatId) params.append('chat_id', chatId)
  if (type) params.append('type', type)
  params.append('format', format)

  return await api.get<ExportResult>(`expression/export/data?${params.toString()}`)
}

/**
 * 导入表达方式
 */
export async function importExpressions(data: ImportExpressionsRequest) {
  return await api.post<ImportResult>('expression/import/data', data)
}
