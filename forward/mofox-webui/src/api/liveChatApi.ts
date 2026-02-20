/**
 * 实时聊天 API 模块
 * 提供实时消息相关的 API 请求封装
 */

import { api, getServerInfo } from './index'

// ==================== 类型定义 ====================

/** 聊天流信息 */
export interface StreamInfo {
  stream_id: string
  platform: string
  user_id: string
  group_id: string
  chat_type: string
  last_message_time: number | null
  last_message_content: string
  unread_count: number
}

/** 消息信息 */
export interface MessageInfo {
  message_id: string
  stream_id: string
  platform: string
  chat_type: string
  time: number
  content: string
  sender_id: string
  sender_name: string
  is_sent: boolean
  is_bot: boolean
  is_webui: boolean
  images: Array<{ hash?: string; url?: string }>
  reply_message_id: string | null
  metadata: Record<string, any>
}

// 后端直接返回数组，无需响应包装类型

/** 发送消息请求 */
export interface SendMessageRequest {
  stream_id: string
  content: string
  message_type?: 'text' | 'image' | 'emoji'
  reply_to_id?: string
}

/** 发送消息响应 */
interface SendMessageResponse {
  success: boolean
  message: string
  message_id: string | null
}

// ==================== API 函数 ====================

/**
 * 获取聊天流列表
 * @param limit 返回数量限制
 * @returns 聊天流列表
 */
export async function getStreams(limit: number = 100): Promise<StreamInfo[]> {
  try {
    // 使用系统 api 对象，它会自动添加 X-API-Key header
    const response = await api.get<StreamInfo[]>(`live_chat/streams?limit=${limit}`)
    if (response.success && response.data) {
      return response.data as StreamInfo[]
    }
    return []
  } catch (error) {
    console.error('获取聊天流失败:', error)
    return []
  }
}

/**
 * 获取历史消息
 * @param streamId 聊天流ID
 * @param hours 查询时间范围（小时）
 * @param limit 返回数量限制
 * @returns 消息列表
 */
export async function getMessages(
  streamId: string,
  limit: number = 100,
  beforeTime?: number
): Promise<MessageInfo[]> {
  try {
    let url = `live_chat/messages/${streamId}?limit=${limit}`
    if (beforeTime !== undefined) {
      url += `&before_time=${beforeTime}`
    }
    // 使用系统 api 对象，它会自动添加 X-API-Key header
    const response = await api.get<MessageInfo[]>(url)
    if (response.success && response.data) {
      return response.data as MessageInfo[]
    }
    return []
  } catch (error) {
    console.error('获取历史消息失败:', error)
    return []
  }
}

/**
 * 发送消息
 * @param request 发送消息请求
 * @returns 发送结果
 */
export async function sendMessage(request: SendMessageRequest): Promise<{
  success: boolean
  messageId?: string
  error?: string
}> {
  try {
    const response = await api.post<SendMessageResponse>('live_chat/send', {
      stream_id: request.stream_id,
      content: request.content,
      message_type: request.message_type || 'text'
    })
    
    if (response.success && response.data) {
      const data = response.data
      if (data.success) {
        return { success: true, messageId: data.message_id || undefined }
      } else {
        return { success: false, error: data.message || '发送失败' }
      }
    }
    return { success: false, error: response.error || '请求失败' }
  } catch (error) {
    console.error('发送消息失败:', error)
    return { success: false, error: String(error) }
  }
}

/**
 * 获取图片 URL
 * @param hash 图片哈希
 * @returns 图片 URL
 */
export function getImageUrl(hash: string | null): string {
  if (!hash) return ''
  return `/plugins/webui_backend/live_chat/image/${hash}`
}

/**
 * 获取表情 URL
 * @param hash 表情哈希
 * @returns 表情 URL
 */
export function getEmojiUrl(hash: string | null): string {
  if (!hash) return ''
  return `/plugins/webui_backend/live_chat/emoji/${hash}`
}

/**
 * 创建 WebSocket 连接 URL
 * @returns WebSocket URL
 */
export async function createWebSocketUrl(): Promise<string> {
  // 使用 Neo-MoFox 的统一路径：/webui/api/live_chat/ws
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
  const apiKey = localStorage.getItem('mofox_token') || ''
  return `${protocol}//${window.location.host}/webui/api/live_chat/ws?api_key=${encodeURIComponent(apiKey)}`
}

/**
 * 获取 WebSocket URL（隐藏 api_key 用于日志）
 * @param wsUrl 原始 URL
 * @returns 隐藏 api_key 后的 URL
 */
export function maskWebSocketUrl(wsUrl: string): string {
  return wsUrl.replace(/api_key=[^&]+/, 'api_key=***')
}
