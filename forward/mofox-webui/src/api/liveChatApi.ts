/**
 * 实时聊天 API 模块
 * 提供实时消息相关的 API 请求封装
 */

import { api, getServerInfo } from './index'

// ==================== 类型定义 ====================

/** 聊天流信息 */
export interface StreamInfo {
  stream_id: string
  platform: string | null
  user_id: string | null
  user_nickname: string | null
  group_id: string | null
  group_name: string | null
  last_active_time: number | null
}

/** 消息信息 */
export interface MessageInfo {
  message_id: string
  stream_id: string
  user_id: string | null
  user_nickname: string | null
  content: string | null
  display_message?: string | null
  timestamp: number | null
  is_emoji: boolean
  is_picid: boolean
  reply_to_id: string | null
  direction: 'incoming' | 'outgoing'
  sender_type: 'user' | 'bot' | 'webui'
  image_data?: string | null  // base64 图片数据 (data:image/...)
  emoji_data?: string | null  // base64 表情包数据 (data:image/...)
}

/** 聊天流列表响应 */
interface StreamsResponse {
  success: boolean
  streams: StreamInfo[]
  count: number
}

/** 消息列表响应 */
interface MessagesResponse {
  success: boolean
  messages: MessageInfo[]
  count: number
}

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
  message_id?: string
  error?: string
}

// ==================== API 函数 ====================

/**
 * 获取聊天流列表
 * @param limit 返回数量限制
 * @returns 聊天流列表
 */
export async function getStreams(limit: number = 100): Promise<StreamInfo[]> {
  try {
    const response = await api.get<StreamsResponse>(`live_chat/streams?limit=${limit}`)
    if (response.success && response.data) {
      const data = response.data as unknown as StreamsResponse
      if (data.success && data.streams) {
        return data.streams
      }
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
  hours: number = 24,
  limit: number = 200
): Promise<MessageInfo[]> {
  try {
    const response = await api.get<MessagesResponse>(
      `live_chat/messages/${streamId}?hours=${hours}&limit=${limit}`
    )
    if (response.success && response.data) {
      const data = response.data as unknown as MessagesResponse
      if (data.success && data.messages) {
        return data.messages
      }
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
      message_type: request.message_type || 'text',
      reply_to_id: request.reply_to_id
    })
    
    if (response.success && response.data) {
      const data = response.data as unknown as SendMessageResponse
      if (data.success) {
        return { success: true, messageId: data.message_id }
      } else {
        return { success: false, error: data.error || '发送失败' }
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
  // 使用相对路径，自动通过代理服务器转发（开发环境走Vite代理，生产环境走发现服务器代理）
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
  const token = localStorage.getItem('mofox_token') || ''
  return `${protocol}//${window.location.host}/plugins/webui_backend/live_chat/realtime?token=${encodeURIComponent(token)}`
}

/**
 * 获取 WebSocket URL（隐藏 token 用于日志）
 * @param wsUrl 原始 URL
 * @returns 隐藏 token 后的 URL
 */
export function maskWebSocketUrl(wsUrl: string): string {
  return wsUrl.replace(/token=[^&]+/, 'token=***')
}
