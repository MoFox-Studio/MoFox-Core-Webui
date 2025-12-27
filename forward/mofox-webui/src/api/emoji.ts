/**
 * 表情包管理 API
 */

import { api } from './index'

/**
 * 表情包列表项
 */
export interface EmojiItem {
  id: number
  hash: string
  description: string
  format: string
  is_registered: boolean
  is_banned: boolean
  usage_count: number
  query_count: number
  record_time: number
  thumbnail: string | null
}

/**
 * 表情包详情
 */
export interface EmojiDetail {
  id: number
  hash: string
  description: string
  format: string
  full_path: string
  is_registered: boolean
  is_banned: boolean
  usage_count: number
  query_count: number
  last_used_time: number | null
  record_time: number
  register_time: number | null
  full_image: string | null
}

/**
 * 表情包列表响应
 */
export interface EmojiListResponse {
  items: EmojiItem[]
  total: number
  page: number
  page_size: number
  total_pages: number
}

/**
 * 表情包更新请求
 */
export interface EmojiUpdateRequest {
  description?: string
  is_banned?: boolean
}

/**
 * 批量操作结果
 */
export interface BatchOperationResult {
  hash: string
  success: boolean
  error?: string
}

/**
 * 批量操作响应
 */
export interface BatchOperationResponse {
  processed: number
  succeeded: number
  failed: number
  results: BatchOperationResult[]
}

/**
 * 上传结果
 */
export interface UploadResult {
  filename: string
  success: boolean
  hash?: string
  message?: string
  error?: string
}

/**
 * 上传响应
 */
export interface UploadResponse {
  uploaded: number
  failed: number
  results: UploadResult[]
}

/**
 * 表情包统计响应
 */
export interface EmojiStatsResponse {
  total_count: number
  registered_count: number
  banned_count: number
  total_usage: number
  top_used: Array<{
    hash: string
    description: string
    usage_count: number
  }>
}

/**
 * 获取表情包列表参数
 */
export interface GetEmojiListParams {
  page?: number
  page_size?: number
  search?: string
  sort_by?: string
  sort_order?: 'asc' | 'desc'
  is_registered?: boolean
  is_banned?: boolean
}

/**
 * 获取表情包列表
 */
export async function getEmojiList(params: GetEmojiListParams = {}) {
  const response = await api.get<{ success: boolean; data: EmojiListResponse }>('/emoji/list', { params })
  return response.data
}

/**
 * 获取表情包详情
 */
export async function getEmojiDetail(hash: string) {
  const response = await api.get<{ success: boolean; data: EmojiDetail }>(`/emoji/${hash}`)
  return response.data
}

/**
 * 上传表情包
 */
export async function uploadEmojis(files: File[]) {
  const formData = new FormData()
  files.forEach(file => formData.append('files', file))
  
  // 不要手动设置 Content-Type，让浏览器自动设置（包含 boundary）
  const response = await api.post<{ success: boolean; data: UploadResponse }>('/emoji/upload', formData)
  
  if (!response.success) {
    const errorMsg = (response as any).error || '上传失败'
    throw new Error(errorMsg)
  }
  
  return response.data
}

/**
 * 删除表情包
 */
export async function deleteEmoji(hash: string) {
  const response = await api.delete<{ success: boolean; message: string }>(`/emoji/${hash}`)
  return response.data
}

/**
 * 更新表情包信息
 */
export async function updateEmoji(hash: string, data: EmojiUpdateRequest) {
  const response = await api.patch<{ success: boolean; data: EmojiDetail }>(`/emoji/${hash}`, data)
  return response.data
}

/**
 * 批量操作表情包
 */
export async function batchOperationEmojis(action: 'delete' | 'ban' | 'unban', hashes: string[]) {
  const response = await api.post<{ success: boolean; data: BatchOperationResponse }>('/emoji/batch', {
    action,
    emoji_hashes: hashes
  })
  return response.data
}

/**
 * 获取表情包统计信息
 */
export async function getEmojiStats() {
  const response = await api.get<{ success: boolean; data: EmojiStatsResponse }>('/emoji/stats')
  return response.data
}
