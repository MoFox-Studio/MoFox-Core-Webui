<!--
  @file LiveChatView.vue
  @description 即时通讯页面 - 实时监控平台消息并支持手动发送
  
  功能说明：
  1. 实时展示来自所有平台的真实消息
  2. 支持手动发送消息到指定聊天流
  3. 支持图片/表情包展示
  4. 区分消息来源（用户/Bot/WebUI）
  5. 支持引用消息展示
  
  布局结构：
  - 左侧：聊天流列表（按平台分组）
  - 右侧：消息列表 + 输入框
  
  实现方式：
  - WebSocket 实时消息推送
  - 使用 send_api 发送消息（零侵入）
  - 使用 message_api 获取历史（零侵入）
-->
<template>
  <div class="live-chat-view">
    <!-- 左侧：聊天流列表 -->
    <aside class="stream-panel">
      <div class="panel-header">
        <div class="header-content">
          <span class="material-symbols-rounded">forum</span>
          <h2>聊天流</h2>
        </div>
        <button class="m3-button icon-only" @click="refreshStreams" title="刷新列表">
          <span class="material-symbols-rounded">refresh</span>
        </button>
      </div>
      
      <!-- 搜索框 -->
      <div class="search-box">
        <span class="material-symbols-rounded">search</span>
        <input 
          v-model="searchQuery" 
          type="text" 
          placeholder="搜索聊天流..."
        />
      </div>
      
      <!-- 平台筛选 -->
      <div class="platform-filter">
        <button 
          v-for="platform in availablePlatforms" 
          :key="platform"
          class="filter-chip"
          :class="{ active: selectedPlatform === platform }"
          @click="selectedPlatform = selectedPlatform === platform ? '' : platform"
        >
          {{ platform || '全部' }}
        </button>
      </div>
      
      <!-- 聊天流列表 -->
      <div class="stream-list">
        <div 
          v-for="stream in filteredStreams" 
          :key="stream.stream_id"
          class="stream-item"
          :class="{ active: selectedStream?.stream_id === stream.stream_id }"
          @click="selectStream(stream)"
        >
          <div class="stream-icon">
            <span class="material-symbols-rounded">
              {{ stream.group_id ? 'group' : 'person' }}
            </span>
          </div>
          <div class="stream-info">
            <div class="stream-header-row">
              <div class="stream-name">
                {{ stream.group_id || stream.user_id || '未知' }}
              </div>
              <span class="last-active" v-if="stream.last_message_time">
                {{ formatTime(stream.last_message_time) }}
              </span>
            </div>
            <div class="stream-meta">
              <span class="platform-badge">{{ stream.platform }}</span>
            </div>
          </div>
          <div class="unread-badge" v-if="unreadCounts[stream.stream_id]">
            {{ unreadCounts[stream.stream_id] }}
          </div>
        </div>
        
        <div v-if="filteredStreams.length === 0" class="empty-state">
          <span class="material-symbols-rounded">inbox</span>
          <p>暂无聊天流</p>
        </div>
      </div>
    </aside>

    <!-- 右侧：聊天区域 -->
    <main class="chat-panel">
      <!-- 顶部栏 -->
      <header class="chat-header">
        <div v-if="selectedStream" class="header-content">
          <div class="stream-icon large">
            <span class="material-symbols-rounded">
              {{ selectedStream.group_id ? 'group' : 'person' }}
            </span>
          </div>
          <div class="stream-info">
            <h2>{{ selectedStream.group_id || selectedStream.user_id || '未知' }}</h2>
            <p class="stream-id">{{ selectedStream.stream_id }}</p>
          </div>
        </div>
        <div v-else class="header-placeholder">
          <span class="material-symbols-rounded">chat</span>
          <span>即时通讯</span>
        </div>
        
        <div class="header-actions">
          <div class="connection-status" :class="{ connected: wsConnected }">
            <span class="material-symbols-rounded">
              {{ wsConnected ? 'wifi' : 'wifi_off' }}
            </span>
            <span>{{ wsConnected ? '已连接' : '未连接' }}</span>
          </div>
          <button 
            class="m3-button icon-only" 
            @click="loadHistoryMessages"
            title="加载历史消息"
          >
            <span class="material-symbols-rounded">history</span>
          </button>
        </div>
      </header>

      <!-- 消息列表 -->
      <div class="messages-container" ref="messagesContainer">
        <div v-if="!selectedStream" class="welcome-state">
          <span class="material-symbols-rounded">forum</span>
          <h3>即时通讯</h3>
          <p>选择一个聊天流查看实时消息</p>
        </div>

        <div v-else-if="loadingMessages" class="loading-state">
          <div class="spinner"></div>
          <p>加载消息中...</p>
        </div>

        <div v-else class="messages-list">
          <div 
            v-for="msg in currentMessages" 
            :key="msg.message_id"
            class="message"
            :class="{
              'is-incoming': !msg.is_sent,
              'is-outgoing': msg.is_sent,
              'is-bot': msg.is_bot,
              'is-webui': msg.is_webui,
            }"
          >
            <!-- 引用消息 -->
            <div 
              v-if="msg.reply_message_id" 
              class="reply-preview"
              @click="scrollToMessage(msg.reply_message_id)"
            >
              <span class="material-symbols-rounded">reply</span>
              <span class="reply-text">
                {{ getReplyPreview(msg.reply_message_id) }}
              </span>
            </div>
            
            <!-- 消息头部 -->
            <div class="message-header">
              <span class="user-name">{{ msg.sender_name || '未知用户' }}</span>
              <span v-if="msg.is_bot" class="sender-badge bot">🤖 Bot</span>
              <span v-if="msg.is_webui" class="sender-badge webui">📱 WebUI</span>
              <span class="message-time">{{ formatMessageTime(msg.time) }}</span>
            </div>
            
            <!-- 消息内容 -->
            <div class="message-content">
              <!-- 图片消息 -->
              <img 
                v-if="msg.images && msg.images.length > 0" 
                :src="getImageUrl(msg.images[0])"
                class="message-image"
                @click="previewImage(msg.images[0].hash || '')"
                loading="lazy"
              />
              <!-- 文本消息 -->
              <span v-else class="text-content">{{ msg.content }}</span>
            </div>
          </div>
          
          <div v-if="currentMessages.length === 0" class="empty-messages">
            <span class="material-symbols-rounded">chat_bubble_outline</span>
            <p>暂无消息</p>
          </div>
        </div>
      </div>

      <!-- 消息输入区域 -->
      <div v-if="selectedStream" class="input-area">
        <div class="input-toolbar">
          <button class="m3-icon-button" @click="showImageUpload = true" title="发送图片">
            <span class="material-symbols-rounded">image</span>
          </button>
          <button class="m3-icon-button" @click="showEmojiPicker = true" title="发送表情">
            <span class="material-symbols-rounded">mood</span>
          </button>
        </div>
        
        <div class="input-wrapper">
          <textarea 
            v-model="inputMessage"
            placeholder="输入消息..."
            @keydown.enter.exact="sendMessage"
            @keydown.enter.shift.exact.prevent="inputMessage += '\n'"
            rows="1"
            ref="inputTextarea"
          ></textarea>
        </div>
        
        <button 
          class="m3-button filled send-button" 
          @click="sendMessage"
          :disabled="!inputMessage.trim() || sending"
        >
          <span class="material-symbols-rounded">send</span>
        </button>
      </div>
    </main>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, watch, nextTick } from 'vue'
import {
  type StreamInfo,
  type MessageInfo,
  getStreams,
  getMessages,
  sendMessage as apiSendMessage,
  createWebSocketUrl,
  maskWebSocketUrl
} from '@/api/liveChatApi'

// ==================== 响应式数据 ====================

// 聊天流相关
const streams = ref<StreamInfo[]>([])
const selectedStream = ref<StreamInfo | null>(null)
const searchQuery = ref('')
const selectedPlatform = ref('')
const loadingStreams = ref(false)

// 消息相关
const messages = ref<Map<string, MessageInfo[]>>(new Map())
const loadingMessages = ref(false)
const unreadCounts = ref<Record<string, number>>({})

// 输入相关
const inputMessage = ref('')
const sending = ref(false)
const showImageUpload = ref(false)
const showEmojiPicker = ref(false)

// WebSocket 相关
const wsConnected = ref(false)
let ws: WebSocket | null = null
let reconnectTimer: number | null = null
let reconnectAttempts = 0
const MAX_RECONNECT_ATTEMPTS = 10
let pendingStreamId: string | null = null  // 待订阅的流ID

// DOM 引用
const messagesContainer = ref<HTMLElement | null>(null)
const inputTextarea = ref<HTMLTextAreaElement | null>(null)

// 引用消息缓存
const replyCache = ref<Map<string, MessageInfo>>(new Map())

// ==================== 计算属性 ====================

const availablePlatforms = computed(() => {
  const platforms = new Set<string>([''])
  streams.value.forEach(s => {
    if (s.platform) platforms.add(s.platform)
  })
  return Array.from(platforms)
})

const filteredStreams = computed(() => {
  return streams.value.filter(stream => {
    // 平台筛选
    if (selectedPlatform.value && stream.platform !== selectedPlatform.value) {
      return false
    }
    // 搜索筛选
    if (searchQuery.value) {
      const query = searchQuery.value.toLowerCase()
      const name = (stream.group_name || stream.user_nickname || '').toLowerCase()
      const id = stream.stream_id.toLowerCase()
      if (!name.includes(query) && !id.includes(query)) {
        return false
      }
    }
    return true
  })
})

const currentMessages = computed(() => {
  if (!selectedStream.value) return []
  return messages.value.get(selectedStream.value.stream_id) || []
})

// ==================== 方法 ====================

// 刷新聊天流列表
async function refreshStreams() {
  loadingStreams.value = true
  try {
    streams.value = await getStreams(100)
  } catch (error) {
    console.error('获取聊天流失败:', error)
  } finally {
    loadingStreams.value = false
  }
}

// 选择聊天流
function selectStream(stream: StreamInfo) {
  selectedStream.value = stream
  // 清除未读计数
  unreadCounts.value[stream.stream_id] = 0
  // 加载历史消息
  loadHistoryMessages()
  // 重新订阅 WebSocket
  subscribeToStream(stream.stream_id)
}

// 加载历史消息
async function loadHistoryMessages() {
  if (!selectedStream.value) return
  
  loadingMessages.value = true
  try {
    const streamId = selectedStream.value.stream_id
    const messageList = await getMessages(streamId, 200)
    console.log(`加载聊天流 ${streamId} 的历史消息，共 ${messageList.length} 条`)
    messages.value.set(streamId, messageList)
    await nextTick()
    scrollToBottom()
  } catch (error) {
    console.error('获取历史消息失败:', error)
  } finally {
    loadingMessages.value = false
  }
}

// 发送消息
async function sendMessage() {
  if (!inputMessage.value.trim() || !selectedStream.value || sending.value) return
  
  sending.value = true
  try {
    const result = await apiSendMessage({
      stream_id: selectedStream.value.stream_id,
      content: inputMessage.value.trim(),
      message_type: 'text'
    })
    
    if (result.success) {
      inputMessage.value = ''
      // 消息会通过 WebSocket 返回，无需手动添加
      nextTick(adjustTextareaHeight)
    } else {
      console.error('发送失败:', result.error)
    }
  } catch (error) {
    console.error('发送消息失败:', error)
  } finally {
    sending.value = false
  }
}

// WebSocket 连接
async function connectWebSocket() {
  if (ws?.readyState === WebSocket.OPEN) return
  
  try {
    const wsUrl = await createWebSocketUrl()
    
    console.log('连接 WebSocket:', maskWebSocketUrl(wsUrl))
    ws = new WebSocket(wsUrl)
  
  ws.onopen = () => {
    console.log('WebSocket 已连接')
    wsConnected.value = true
    reconnectAttempts = 0
    
    // 优先订阅待订阅的流，否则订阅已选择的流
    const streamToSubscribe = pendingStreamId || selectedStream.value?.stream_id
    if (streamToSubscribe) {
      // 直接发送订阅消息，不通过 subscribeToStream 避免循环
      ws!.send(JSON.stringify({
        type: 'subscribe',
        stream_id: streamToSubscribe
      }))
      pendingStreamId = null
    }
  }
  
  ws.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data)
      handleWebSocketMessage(data)
    } catch (e) {
      // 可能是 pong 响应
      if (event.data !== 'pong') {
        console.error('解析 WebSocket 消息失败:', e)
      }
    }
  }
  
  ws.onclose = () => {
    console.log('WebSocket 已断开')
    wsConnected.value = false
    scheduleReconnect()
  }
  
  ws.onerror = (error) => {
    console.error('WebSocket 错误:', error)
  }
  } catch (error) {
    console.error('连接 WebSocket 失败:', error)
  }
}

// 处理 WebSocket 消息
function handleWebSocketMessage(data: any) {
  if (data.type === 'message') {
    const msg = data.data as MessageInfo
    const streamId = msg.stream_id
    
    if (!streamId) return
    
    // 添加到消息列表
    if (!messages.value.has(streamId)) {
      messages.value.set(streamId, [])
    }
    const streamMessages = messages.value.get(streamId)!
    
    // 检查是否已存在（避免重复）
    if (!streamMessages.some(m => m.message_id === msg.message_id)) {
      streamMessages.push(msg)
      
      // 如果是当前查看的聊天流，滚动到底部
      if (selectedStream.value?.stream_id === streamId) {
        nextTick(() => scrollToBottom())
      } else {
        // 增加未读计数
        unreadCounts.value[streamId] = (unreadCounts.value[streamId] || 0) + 1
      }
    }
  } else if (data.type === 'subscribed') {
    console.log('已订阅聊天流:', data.stream_id)
  } else if (data.type === 'pong') {
    // 心跳响应
    console.debug('收到心跳响应')
  }
}

// 订阅聊天流
function subscribeToStream(streamId: string) {
  if (ws?.readyState === WebSocket.OPEN) {
    ws.send(JSON.stringify({
      type: 'subscribe',
      stream_id: streamId
    }))
    pendingStreamId = null  // 订阅成功，清除待订阅
  } else {
    // WS 未连接，保存待订阅ID，连接成功后自动订阅
    pendingStreamId = streamId
    console.log('待订阅聊天流:', streamId)
  }
}

// 重连调度
function scheduleReconnect() {
  if (reconnectAttempts >= MAX_RECONNECT_ATTEMPTS) {
    console.error('WebSocket 重连次数超过限制')
    return
  }
  
  const delay = Math.min(1000 * Math.pow(2, reconnectAttempts), 30000)
  reconnectAttempts++
  
  console.log(`将在 ${delay}ms 后重连 (尝试 ${reconnectAttempts}/${MAX_RECONNECT_ATTEMPTS})`)
  
  reconnectTimer = window.setTimeout(() => {
    connectWebSocket()
  }, delay)
}

// 心跳检测
function startHeartbeat() {
  setInterval(() => {
    if (ws?.readyState === WebSocket.OPEN) {
      ws.send('ping')
    }
  }, 30000)
}

// 滚动到底部
function scrollToBottom() {
  if (messagesContainer.value) {
    messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
  }
}

// 滚动到指定消息
function scrollToMessage(messageId: string) {
  // TODO: 实现滚动到指定消息
  console.log('滚动到消息:', messageId)
}

// 获取引用消息预览
function getReplyPreview(messageId: string): string {
  const cached = replyCache.value.get(messageId)
  if (cached) {
    return `${cached.user_nickname}: ${cached.content?.slice(0, 30)}...`
  }
  // 尝试从当前消息中查找
  const msg = currentMessages.value.find(m => m.message_id === messageId)
  if (msg) {
    return `${msg.user_nickname}: ${msg.content?.slice(0, 30)}...`
  }
  return '查看原消息'
}

// 转换图片URL（支持base64）
function getImageUrl(imageData: any): string {
  if (!imageData) return ''
  
  // 如果已经是完整的URL或data URL，直接返回
  if (imageData.url) {
    const url = imageData.url
    if (url.startsWith('http') || url.startsWith('data:')) {
      return url
    }
    // 如果是base64文本，添加data URL前缀
    if (url.match(/^[A-Za-z0-9+/=]+$/)) {
      return `data:image/png;base64,${url}`
    }
    return url
  }
  
  // 如果直接就是base64字符串
  if (typeof imageData === 'string') {
    if (imageData.startsWith('data:')) {
      return imageData
    }
    // 检查是否为base64格式
    if (imageData.match(/^[A-Za-z0-9+/=]+$/)) {
      return `data:image/png;base64,${imageData}`
    }
    return imageData
  }
  
  return ''
}

// 预览图片
function previewImage(hash: string) {
  // TODO: 实现图片预览
  console.log('预览图片:', hash)
}

// 格式化时间
function formatTime(timestamp: number | null): string {
  if (!timestamp) return ''
  const date = new Date(timestamp * 1000)
  const now = new Date()
  
  if (date.toDateString() === now.toDateString()) {
    return date.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
  }
  return date.toLocaleDateString('zh-CN', { month: 'short', day: 'numeric' })
}

// 格式化消息时间
function formatMessageTime(timestamp: number | null): string {
  if (!timestamp) return ''
  const date = new Date(timestamp * 1000)
  return date.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit', second: '2-digit' })
}

// 自动调整输入框高度
function adjustTextareaHeight() {
  const textarea = inputTextarea.value
  if (!textarea) return
  
  textarea.style.height = 'auto'
  const newHeight = textarea.scrollHeight
  textarea.style.height = newHeight + 'px'
  
  if (newHeight > 150) {
     textarea.style.overflowY = 'auto'
  } else {
     textarea.style.overflowY = 'hidden'
  }
}

// 监听输入内容变化，自动调整高度
watch(inputMessage, () => {
  nextTick(adjustTextareaHeight)
})

// ==================== 生命周期 ====================

onMounted(() => {
  refreshStreams()
  connectWebSocket()
  startHeartbeat()
})

onUnmounted(() => {
  if (ws) {
    ws.close()
    ws = null
  }
  if (reconnectTimer) {
    clearTimeout(reconnectTimer)
  }
})

// 监听选中的聊天流变化
watch(selectedStream, (newStream) => {
  if (newStream) {
    loadHistoryMessages()
  }
})
</script>

<style scoped>
/* Global Scrollbar */
::-webkit-scrollbar {
  width: 6px;
  height: 6px;
}
::-webkit-scrollbar-track {
  background: transparent;
}
::-webkit-scrollbar-thumb {
  background: var(--md-sys-color-outline-variant);
  border-radius: 3px;
}
::-webkit-scrollbar-thumb:hover {
  background: var(--md-sys-color-outline);
}

.live-chat-view {
  display: flex;
  height: 100%;
  width: 100%;
  background-color: transparent; /* Changed from surface to transparent to show wallpaper if any */
  box-sizing: border-box;
  overflow: hidden;
  border-radius: 0;
  gap: 16px; /* Restore gap */
  padding: 0; /* Remove padding if we want it to fit in the layout container, see Dashboard.vue padding */
}

/* 左侧面板 */
.stream-panel {
  width: 320px;
  min-width: 280px;
  display: flex;
  flex-direction: column;
  background: var(--md-sys-color-surface-container); 
  border-radius: 32px; /* Card style */
  box-shadow: none; /* Flat style as per dashboard */
  border: none;
  overflow: hidden;
}

.panel-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 24px;
}

.header-content {
  display: flex;
  align-items: center;
  gap: 12px;
}

.header-content h2 {
  margin: 0;
  font-size: 20px;
  font-weight: 600;
  color: var(--md-sys-color-on-surface);
}

.search-box {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 16px;
  background: var(--md-sys-color-surface-container-high);
  margin: 0 16px 16px;
  border-radius: 24px;
  transition: all 0.2s;
}

.search-box:focus-within {
  background: var(--md-sys-color-surface-container-highest);
  box-shadow: none; /* Removed glow, using background change */
}

.search-box input {
  flex: 1;
  border: none;
  background: none;
  outline: none;
  font-size: 14px;
  color: var(--md-sys-color-on-surface-variant);
}

.platform-filter {
  display: flex;
  gap: 8px;
  padding: 0 16px 12px;
  flex-wrap: wrap;
}

.filter-chip {
  padding: 6px 12px;
  border: 1px solid var(--md-sys-color-outline-variant);
  border-radius: 8px;
  background: transparent;
  cursor: pointer;
  font-size: 13px;
  font-weight: 500;
  color: var(--md-sys-color-on-surface-variant);
  transition: all 0.2s;
}

.filter-chip:hover {
  background: var(--md-sys-color-surface-container-high);
}

.filter-chip.active {
  background: var(--md-sys-color-primary-container);
  color: var(--md-sys-color-on-primary-container);
  border-color: transparent;
}

.stream-list {
  flex: 1;
  overflow-y: auto;
  padding: 8px; /* Reduced padding */
}

.stream-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 12px;
  border-radius: 12px;
  cursor: pointer;
  transition: background-color 0.2s;
  margin-bottom: 2px;
}

.stream-item:hover {
  background-color: var(--md-sys-color-surface-container-high);
}

.stream-item.active {
  background-color: var(--md-sys-color-primary-container);
  color: var(--md-sys-color-on-primary-container);
}

.stream-icon {
  width: 42px;
  height: 42px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--md-sys-color-surface-container-highest);
  color: var(--md-sys-color-primary);
  border-radius: 50%;
  font-size: 20px;
  flex-shrink: 0;
}

.stream-item.active .stream-icon {
    background: var(--md-sys-color-primary);
    color: var(--md-sys-color-on-primary);
}

.stream-icon.large {
  width: 48px;
  height: 48px;
  font-size: 24px;
}

.stream-info {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.stream-header-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
}

.stream-name {
  font-size: 15px;
  font-weight: 500;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  color: var(--md-sys-color-on-surface);
}

.last-active {
  font-size: 11px;
  color: var(--md-sys-color-on-surface-variant);
  white-space: nowrap;
  flex-shrink: 0;
}

.stream-meta {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
  color: var(--md-sys-color-on-surface-variant);
}

.platform-badge {
  padding: 2px 6px;
  background: var(--md-sys-color-surface-container-highest);
  color: var(--md-sys-color-on-surface-variant);
  border-radius: 4px;
  font-size: 10px;
  font-weight: 600;
  text-transform: uppercase;
  white-space: nowrap;
  max-width: 100%;
}

.unread-badge {
  min-width: 20px;
  height: 20px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--md-sys-color-error);
  color: var(--md-sys-color-on-error);
  border-radius: 10px;
  font-size: 11px;
  font-weight: 600;
  padding: 0 5px;
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 200px;
  color: var(--md-sys-color-on-surface-variant);
  opacity: 0.7;
}

.empty-state .material-symbols-rounded {
   font-size: 48px;
   margin-bottom: 8px;
   opacity: 0.5;
}


/* 右侧聊天面板 */
.chat-panel {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-width: 0;
  background: var(--md-sys-color-surface-container); /* Match card background */
  border-radius: 32px; /* Card style */
  overflow: hidden;
}

.chat-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 24px;
  background: transparent;
  border-bottom: 1px solid var(--md-sys-color-outline-variant);
  border-radius: 0;
  box-shadow: none;
  height: 80px; /* Slightly taller header */
  box-sizing: border-box;
}

.chat-header .stream-id {
  font-size: 12px;
  color: var(--md-sys-color-on-surface-variant);
  margin: 0;
}

.header-placeholder {
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: 18px;
  font-weight: 600;
  color: var(--md-sys-color-on-surface);
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 12px;
}

.connection-status {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 4px 10px;
  border-radius: 100px;
  font-size: 12px;
  font-weight: 500;
  background: var(--md-sys-color-error-container);
  color: var(--md-sys-color-on-error-container);
}

.connection-status.connected {
  background: var(--md-sys-color-primary-container);
  color: var(--md-sys-color-on-primary-container);
}

/* 消息列表 */
.messages-container {
  flex: 1;
  overflow-y: auto;
  background: transparent;
  padding: 24px 48px; /* More padding */
  border: none;
  border-radius: 0;
  box-shadow: none;
}

.welcome-state,
.loading-state,
.empty-messages {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  gap: 24px;
  color: var(--md-sys-color-on-surface-variant);
}

.welcome-state .material-symbols-rounded,
.empty-messages .material-symbols-rounded {
  font-size: 64px;
  opacity: 0.1; /* More subtle */
  color: var(--md-sys-color-on-surface);
}

.welcome-state h3 {
    margin: 0;
    font-size: 24px;
    font-weight: 500;
    color: var(--md-sys-color-on-surface);
}

.messages-list {
  display: flex;
  flex-direction: column;
  gap: 20px; /* Increased gap for better reading */
  padding-bottom: 20px;
}

.message {
  max-width: 70%;
  padding: 12px 18px;
  border-radius: 20px;
  position: relative;
  animation: fadeIn 0.3s ease-out;
  box-shadow: 0 1px 2px rgba(0,0,0,0.05); /* Subtle shadow */
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}

.message.is-incoming {
  align-self: flex-start;
  background: var(--md-sys-color-surface-container-low); /* Distinct from background */
  color: var(--md-sys-color-on-surface);
  border-bottom-left-radius: 4px;
}

.message.is-outgoing {
  align-self: flex-end;
  background: var(--md-sys-color-primary);
  color: var(--md-sys-color-on-primary);
  border-bottom-right-radius: 4px;
}

.message.is-bot {
  background: var(--md-sys-color-secondary-container);
  color: var(--md-sys-color-on-secondary-container);
}

.message.is-webui {
  background: var(--md-sys-color-tertiary-container);
  color: var(--md-sys-color-on-tertiary-container);
}

.message-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 6px;
  font-size: 12px;
  opacity: 0.8;
}

.user-name {
  font-weight: 600;
}

.sender-badge {
  padding: 2px 6px;
  border-radius: 4px;
  font-size: 10px;
  font-weight: bold;
}

.sender-badge.bot {
  background: var(--md-sys-color-secondary);
  color: var(--md-sys-color-on-secondary);
}

.sender-badge.webui {
  background: var(--md-sys-color-tertiary);
  color: var(--md-sys-color-on-tertiary);
}

.message-time {
  margin-left: auto;
  font-size: 11px;
}

.message-content {
  word-break: break-word;
  line-height: 1.5;
  font-size: 15px;
}

.message-image,
.message-emoji {
  max-width: 100%;
  border-radius: 12px;
  cursor: pointer;
  margin-top: 4px;
}

.message-emoji {
  width: 64px;
  height: 64px;
}

.reply-preview {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  margin-bottom: 8px;
  background: rgba(0, 0, 0, 0.05);
  border-radius: 8px;
  font-size: 13px;
  cursor: pointer;
  border-left: 3px solid currentColor;
}

.reply-preview:hover {
  background: rgba(0, 0, 0, 0.1);
}

/* 输入区域 */
.input-area {
  display: flex;
  align-items: flex-end;
  gap: 12px;
  padding: 24px;
  background: transparent;
  border-top: 1px solid var(--md-sys-color-outline-variant);
  border-radius: 0;
  box-shadow: none;
  /* Ensure it stays at bottom and full width */
  margin-top: auto; 
}

.input-wrapper {
  flex: 1;
  background: var(--md-sys-color-surface-container-high);
  border-radius: 28px;
  padding: 4px;
  display: flex;
  align-items: center;
}

.input-wrapper textarea {
  width: 100%;
  border: none;
  background: transparent;
  border-radius: 20px;
  padding: 12px 16px;
  resize: none;
  outline: none;
  font-size: 15px;
  font-family: inherit;
  color: var(--md-sys-color-on-surface);
  max-height: 150px;
  overflow-y: hidden;
}

.input-wrapper textarea:focus {
  background: transparent;
}

.send-button {
  border-radius: 28px;
  width: 48px;
  height: 48px;
  padding: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--md-sys-color-primary);
  color: var(--md-sys-color-on-primary);
  box-shadow: none;
  transition: transform 0.1s, background-color 0.2s;
  border: none;
  cursor: pointer;
}

.send-button:hover {
  background: var(--md-sys-color-primary-container); /* Check if this is darker or lighter, usually lighter/different */
  color: var(--md-sys-color-on-primary-container);
  box-shadow: 0 2px 6px rgba(0,0,0,0.1);
}

.send-button:active {
  transform: scale(0.95);
}

.send-button:disabled {
  background: var(--md-sys-color-surface-variant);
  color: var(--md-sys-color-on-surface-variant);
  cursor: not-allowed;
  box-shadow: none;
}

/* 加载动画 */
.spinner {
  width: 48px;
  height: 48px;
  border: 4px solid var(--md-sys-color-surface-container-high);
  border-top-color: var(--md-sys-color-primary);
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

/* Material 3 按钮样式 */
.m3-button {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 8px 16px;
  border: none;
  border-radius: 20px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
  height: 36px;
}

.m3-button.filled {
  background: var(--md-sys-color-primary);
  color: var(--md-sys-color-on-primary);
}

.m3-button.filled:hover {
  box-shadow: 0 1px 2px rgba(0,0,0,0.1);
}

.m3-button.filled:disabled {
  background: var(--md-sys-color-on-surface);
  opacity: 0.12;
  color: var(--md-sys-color-surface);
  box-shadow: none;
  cursor: not-allowed;
}

.m3-button.icon-only {
  padding: 0;
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background: transparent;
  color: var(--md-sys-color-on-surface-variant);
}

.m3-button.icon-only:hover {
  background: var(--md-sys-color-surface-container-high);
  color: var(--md-sys-color-on-surface);
}

.m3-icon-button {
  padding: 8px;
  width: 40px;
  height: 40px;
  border: none;
  border-radius: 50%;
  background: transparent;
  cursor: pointer;
  transition: background 0.2s;
  color: var(--md-sys-color-on-surface-variant);
  display: flex;
  align-items: center;
  justify-content: center;
}

.m3-icon-button:hover {
  background: var(--md-sys-color-surface-container-high);
  color: var(--md-sys-color-on-surface);
}

.m3-card {
  /* Base card style, kept for compatibility if used elsewhere */
}
</style>
