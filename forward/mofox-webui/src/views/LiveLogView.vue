<template>
  <div class="live-log-view">
    <!-- 页面标题 -->
    <div class="page-header">
      <div class="header-content">
        <div class="title-group">
          <Icon icon="lucide:radio" class="title-icon" />
          <h1 class="page-title">实时日志</h1>
          <div class="status-badge" :class="{ connected: realtimeEnabled }">
            <span class="status-dot"></span>
            <span class="status-text">{{ realtimeEnabled ? '已连接' : '未连接' }}</span>
          </div>
        </div>
        <p class="page-description">实时查看系统日志输出</p>
      </div>
    </div>

    <!-- 主内容区 -->
    <div class="content-wrapper">
      <div class="log-container">
        <!-- 工具栏 -->
        <div class="toolbar">
          <div class="toolbar-left">
            <button 
              class="action-button primary" 
              @click="toggleRealtime"
              :disabled="connecting"
            >
              <Icon :icon="realtimeEnabled ? 'lucide:pause' : 'lucide:play'" />
              <span>{{ realtimeEnabled ? '断开连接' : '开始监听' }}</span>
            </button>
            
            <button 
              class="action-button" 
              @click="clearRealtimeLogs"
              :disabled="!realtimeEnabled && realtimeLogs.length === 0"
            >
              <Icon icon="lucide:trash-2" />
              <span>清空日志</span>
            </button>
            
            <div class="separator-line"></div>
            
            <label class="checkbox-label">
              <input type="checkbox" v-model="autoScroll" />
              <span>自动滚动</span>
            </label>
          </div>
          
          <div class="toolbar-right">
            <div class="filter-group">
              <div class="level-filter-dropdown">
                <button class="filter-button" @click="toggleLevelFilter">
                  <Icon icon="lucide:filter" />
                  <span>日志级别 ({{ selectedLevels.length }})</span>
                  <Icon :icon="showLevelFilter ? 'lucide:chevron-up' : 'lucide:chevron-down'" />
                </button>
                <div v-if="showLevelFilter" class="filter-dropdown-menu">
                  <label v-for="level in logLevels" :key="level" class="filter-option">
                    <input 
                      type="checkbox" 
                      :value="level" 
                      v-model="selectedLevels"
                    />
                    <span :class="`level-badge level-${level.toLowerCase()}`">{{ level }}</span>
                  </label>
                </div>
              </div>
              
              <input 
                v-model="searchQuery" 
                type="text" 
                class="search-input"
                placeholder="搜索日志内容..."
              />
            </div>
          </div>
        </div>

        <!-- 统计信息 -->
        <div class="stats-bar">
          <div class="stat-item">
            <span class="stat-label">总数:</span>
            <span class="stat-value">{{ realtimeLogs.length }}</span>
          </div>
          <div class="stat-item" v-if="realtimeLogs.length !== filteredLogs.length">
            <span class="stat-label">已筛选:</span>
            <span class="stat-value">{{ filteredLogs.length }}</span>
          </div>
          <div class="stat-item" v-for="(count, level) in logLevelCounts" :key="level">
            <span class="stat-label">{{ level }}:</span>
            <span class="stat-value" :class="`level-${level.toLowerCase()}`">{{ count }}</span>
          </div>
        </div>

        <!-- 日志内容区域 -->
        <div class="log-content" ref="logContentContainer">
          <div v-if="connecting" class="loading-state">
            <Icon icon="lucide:loader-2" class="loading-icon spinning" />
            <p>正在连接...</p>
          </div>

          <div v-else-if="!realtimeEnabled && realtimeLogs.length === 0" class="empty-state">
            <Icon icon="lucide:radio" class="empty-icon" />
            <p>点击"开始监听"按钮开始接收实时日志</p>
          </div>

          <div v-else-if="filteredLogs.length === 0" class="empty-state">
            <Icon icon="lucide:filter-x" class="empty-icon" />
            <p>没有匹配的日志</p>
            <p style="font-size: 12px; margin-top: 8px;">尝试调整筛选条件或搜索关键词</p>
          </div>

          <div v-else class="log-entries terminal-style">
            <div 
              v-for="entry in filteredLogs" 
              :key="entry.line_number"
              class="log-entry terminal-line"
              :class="`level-${entry.level.toLowerCase()}`"
            >
              <span class="terminal-time">{{ formatTimestamp(entry.timestamp) }}</span>
              <span class="terminal-level" :class="`level-${entry.level.toLowerCase()}`">
                [{{ entry.level.padEnd(8, ' ') }}]
              </span>
              <span 
                class="terminal-logger" 
                v-if="entry.alias || entry.logger_name"
                :style="entry.color ? { color: entry.color } : {}"
                :title="entry.alias ? entry.logger_name : ''"
              >
                [{{ entry.alias || entry.logger_name }}]
              </span>
              <span class="terminal-message" v-html="formatLogMessage(entry.event)"></span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, nextTick, watch } from 'vue'
import { Icon } from '@iconify/vue'
import { getServerInfo } from '@/api/index'
import type { LogEntry } from '@/api/log_viewer'

// 状态
const realtimeEnabled = ref(false)
const connecting = ref(false)
const realtimeLogs = ref<LogEntry[]>([])
const autoScroll = ref(true)
const websocket = ref<WebSocket | null>(null)
const logContentContainer = ref<HTMLElement | null>(null)

// 筛选
const logLevels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
const selectedLevels = ref<string[]>(['INFO', 'WARNING', 'ERROR', 'CRITICAL']) // 默认排除 DEBUG
const showLevelFilter = ref(false)
const searchQuery = ref('')

// 切换级别筛选面板
const toggleLevelFilter = () => {
  showLevelFilter.value = !showLevelFilter.value
}

// 点击外部关闭筛选面板
const handleClickOutside = (event: MouseEvent) => {
  const target = event.target as HTMLElement
  if (!target.closest('.level-filter-dropdown')) {
    showLevelFilter.value = false
  }
}

// 过滤后的日志
const filteredLogs = computed(() => {
  let logs = realtimeLogs.value

  // 按级别筛选（多选）
  if (selectedLevels.value.length > 0 && selectedLevels.value.length < logLevels.length) {
    logs = logs.filter(log => selectedLevels.value.includes(log.level))
  }

  // 按关键词搜索
  if (searchQuery.value) {
    const query = searchQuery.value.toLowerCase()
    logs = logs.filter(log => 
      log.event.toLowerCase().includes(query) ||
      (log.logger_name && log.logger_name.toLowerCase().includes(query)) ||
      (log.alias && log.alias.toLowerCase().includes(query))
    )
  }

  return logs
})

// 统计各级别日志数量（基于所有日志，不是过滤后的）
const logLevelCounts = computed(() => {
  const counts: Record<string, number> = {
    DEBUG: 0,
    INFO: 0,
    WARNING: 0,
    ERROR: 0,
    CRITICAL: 0
  }

  realtimeLogs.value.forEach(log => {
    const level = log.level
    if (level && counts[level] !== undefined) {
      counts[level]++
    }
  })

  return counts
})

// 格式化时间戳
const formatTimestamp = (timestamp: string) => {
  if (!timestamp) return ''
  return timestamp.replace('T', ' ').substring(0, 19)
}

// 格式化日志消息（处理 ANSI 转义序列和 JSON）
const formatLogMessage = (message: string) => {
  if (!message) return ''
  
  // 尝试解析 JSON 格式的日志（包括 Python 字典格式）
  try {
    // 先尝试直接解析 JSON
    let parsed = null
    try {
      parsed = JSON.parse(message)
    } catch {
      // 如果失败，尝试将 Python 字典格式转换为 JSON
      const jsonMessage = message
        .replace(/'/g, '"')  // 单引号转双引号
        .replace(/True/g, 'true')  // Python True -> JSON true
        .replace(/False/g, 'false')  // Python False -> JSON false
        .replace(/None/g, 'null')  // Python None -> JSON null
      parsed = JSON.parse(jsonMessage)
    }
    
    if (parsed && typeof parsed === 'object') {
      // 只返回 event 内容
      if (parsed.event) {
        return escapeHtml(parsed.event)
      }
    }
  } catch (e) {
    // 不是 JSON，继续处理
  }
  
  // 处理 ANSI 转义序列
  const ansiRegex = /\x1b\[(\d+)m/g
  const colorMap: Record<string, string> = {
    '30': '#000000', '31': '#e74c3c', '32': '#2ecc71', '33': '#f39c12',
    '34': '#3498db', '35': '#9b59b6', '36': '#1abc9c', '37': '#ecf0f1',
    '90': '#7f8c8d', '91': '#e74c3c', '92': '#2ecc71', '93': '#f39c12',
    '94': '#3498db', '95': '#9b59b6', '96': '#1abc9c', '97': '#ffffff'
  }
  
  let result = ''
  let lastIndex = 0
  let currentColor = ''
  let match: RegExpExecArray | null
  
  while ((match = ansiRegex.exec(message)) !== null) {
    const text = message.substring(lastIndex, match.index)
    if (text) {
      if (currentColor) {
        result += `<span style="color: ${currentColor};">${escapeHtml(text)}</span>`
      } else {
        result += escapeHtml(text)
      }
    }
    
    const code = match[1]
    if (code === '0') {
      currentColor = ''
    } else if (code && colorMap[code]) {
      currentColor = colorMap[code]
    }
    
    lastIndex = ansiRegex.lastIndex
  }
  
  const remainingText = message.substring(lastIndex)
  if (remainingText) {
    if (currentColor) {
      result += `<span style="color: ${currentColor};">${escapeHtml(remainingText)}</span>`
    } else {
      result += escapeHtml(remainingText)
    }
  }
  
  return result || escapeHtml(message)
}

// HTML 转义
const escapeHtml = (text: string) => {
  const div = document.createElement('div')
  div.textContent = text
  return div.innerHTML
}

// 切换实时日志
const toggleRealtime = () => {
  if (realtimeEnabled.value) {
    disconnectWebSocket()
  } else {
    connectWebSocket()
  }
}

// 连接 WebSocket
const connectWebSocket = async () => {
  if (connecting.value || realtimeEnabled.value) return

  connecting.value = true
  try {
    // 动态获取服务器信息
    const serverInfo = await getServerInfo()
    const wsUrl = `ws://${serverInfo.host}:${serverInfo.port}/plugins/webui_backend/log_viewer/realtime`
    
    console.log('正在连接WebSocket:', wsUrl)
    websocket.value = new WebSocket(wsUrl)
    
    websocket.value.onopen = () => {
      console.log('WebSocket已连接')
      realtimeEnabled.value = true
      connecting.value = false
    }
    
    websocket.value.onmessage = (event) => {
      try {
        let logEntry: LogEntry | any = JSON.parse(event.data)
        
        // 检查是否是嵌套的 JSON 字符串（后端可能发送的是字符串化的 JSON）
        if (typeof logEntry === 'string') {
          try {
            logEntry = JSON.parse(logEntry)
          } catch {
            // 如果不是 JSON 字符串，创建一个简单的日志对象
            logEntry = {
              timestamp: new Date().toISOString(),
              level: 'INFO',
              logger_name: 'unknown',
              event: String(logEntry),
              line_number: 0,
              file_name: 'realtime'
            }
          }
        }
        
        
        // 添加行号(用于key)
        logEntry.line_number = realtimeLogs.value.length + 1
        logEntry.file_name = 'realtime'
        
        realtimeLogs.value.push(logEntry as LogEntry)
        
        // 限制缓冲区大小
        if (realtimeLogs.value.length > 1000) {
          realtimeLogs.value.shift()
          // 重新编号
          realtimeLogs.value.forEach((log, index) => {
            log.line_number = index + 1
          })
        }
        
        // 自动滚动到底部
        if (autoScroll.value) {
          nextTick(() => {
            scrollToBottom()
          })
        }
      } catch (error) {
        console.error('解析日志消息失败:', error, event.data)
      }
    }
    
    websocket.value.onerror = (error) => {
      console.error('WebSocket错误:', error)
      connecting.value = false
    }
    
    websocket.value.onclose = () => {
      console.log('WebSocket已断开')
      realtimeEnabled.value = false
      connecting.value = false
    }
  } catch (error) {
    console.error('连接WebSocket失败:', error)
    connecting.value = false
  }
}

// 断开 WebSocket
const disconnectWebSocket = () => {
  if (websocket.value) {
    websocket.value.close()
    websocket.value = null
  }
  realtimeEnabled.value = false
  connecting.value = false
}

// 清空日志
const clearRealtimeLogs = () => {
  realtimeLogs.value = []
}

// 滚动到底部
const scrollToBottom = () => {
  if (logContentContainer.value) {
    logContentContainer.value.scrollTop = logContentContainer.value.scrollHeight
  }
}

// 监听自动滚动变化
watch(autoScroll, (newValue) => {
  if (newValue) {
    nextTick(() => {
      scrollToBottom()
    })
  }
})

// 初始化
onMounted(() => {
  // 可以选择自动连接
  // connectWebSocket()
  
  // 添加点击外部关闭筛选面板的监听器
  document.addEventListener('click', handleClickOutside)
})

// 清理
onUnmounted(() => {
  disconnectWebSocket()
  document.removeEventListener('click', handleClickOutside)
})
</script>

<style scoped>
.live-log-view {
  height: 100%;
  display: flex;
  flex-direction: column;
  background: var(--bg-secondary);
  animation: fadeIn 0.4s ease-out;
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}

/* 页面标题 */
.page-header {
  background: rgba(255, 255, 255, 0.8);
  backdrop-filter: blur(12px);
  border-bottom: 1px solid rgba(0, 0, 0, 0.05);
  padding: 24px 32px;
  position: sticky;
  top: 0;
  z-index: 10;
}

.header-content {
  max-width: 1400px;
  margin: 0 auto;
}

.title-group {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 8px;
}

.title-icon {
  font-size: 32px;
  color: var(--primary);
  background: rgba(249, 115, 22, 0.1);
  padding: 8px;
  border-radius: 12px;
}

.page-title {
  font-size: 24px;
  font-weight: 700;
  color: var(--text-primary);
  margin: 0;
  letter-spacing: -0.5px;
}

.status-badge {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 12px;
  border-radius: 20px;
  background: #f3f4f6;
  border: 1px solid transparent;
  font-size: 12px;
  font-weight: 600;
  color: var(--text-secondary);
  transition: all 0.3s ease;
}

.status-badge.connected {
  background: #ecfdf5;
  border-color: rgba(16, 185, 129, 0.2);
  color: #059669;
}

.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #9ca3af;
  transition: all 0.3s ease;
}

.status-badge.connected .status-dot {
  background: #10b981;
  box-shadow: 0 0 0 2px rgba(16, 185, 129, 0.2);
  animation: pulse 2s infinite;
}

@keyframes pulse {
  0% { box-shadow: 0 0 0 0 rgba(16, 185, 129, 0.4); }
  70% { box-shadow: 0 0 0 6px rgba(16, 185, 129, 0); }
  100% { box-shadow: 0 0 0 0 rgba(16, 185, 129, 0); }
}

.page-description {
  font-size: 14px;
  color: var(--text-secondary);
  margin: 0;
  padding-left: 56px;
}

/* 主内容区 */
.content-wrapper {
  flex: 1;
  overflow: hidden;
  padding: 24px 32px;
  display: flex;
  flex-direction: column;
  min-height: 0;
}

.log-container {
  max-width: 1400px;
  margin: 0 auto;
  width: 100%;
  height: 100%;
  max-height: calc(100vh - 220px);
  display: flex;
  flex-direction: column;
  background: #1e1e1e; /* Darker background for better contrast */
  border-radius: 16px;
  border: 1px solid rgba(0,0,0,0.1);
  overflow: hidden;
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.2);
}

/* 终端配色变量 */
:root {
  --terminal-bg: #1e1e1e;
  --terminal-bar-bg: #252526;
  --terminal-border: #333333;
  --terminal-text: #d4d4d4;
  --terminal-text-dim: #858585;
  --terminal-text-darker: #6e6e6e;
  --terminal-hover: rgba(255, 255, 255, 0.05);
  --terminal-scrollbar-track: #1e1e1e;
  --terminal-scrollbar-thumb: #424242;
  --terminal-scrollbar-thumb-hover: #4f4f4f;
}

/* 工具栏 */
.toolbar {
  padding: 16px 24px;
  border-bottom: 1px solid var(--terminal-border);
  background: var(--terminal-bar-bg);
  display: flex;
  justify-content: space-between;
  gap: 16px;
  flex-wrap: wrap;
  flex-shrink: 0;
}

.toolbar-left,
.toolbar-right {
  display: flex;
  gap: 12px;
  align-items: center;
}

.action-button {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 16px;
  border: 1px solid var(--terminal-border);
  border-radius: 8px;
  background: #2d2d2d;
  color: #e0e0e0;
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
}

.action-button:hover:not(:disabled) {
  background: #383838;
  border-color: var(--primary);
  color: var(--primary);
}

.action-button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.action-button.primary {
  background: var(--primary);
  color: white;
  border-color: var(--primary);
}

.action-button.primary:hover:not(:disabled) {
  background: #ea580c; /* Darker orange */
  box-shadow: 0 0 12px rgba(249, 115, 22, 0.3);
}

.separator-line {
  width: 1px;
  height: 24px;
  background: var(--terminal-border);
  margin: 0 8px;
}

.checkbox-label {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  color: #a0a0a0;
  cursor: pointer;
  user-select: none;
  padding: 4px 8px;
  border-radius: 6px;
  transition: background 0.2s;
}

.checkbox-label:hover {
  background: rgba(255,255,255,0.05);
  color: #e0e0e0;
}

.checkbox-label input[type="checkbox"] {
  width: 16px;
  height: 16px;
  cursor: pointer;
  accent-color: var(--primary);
}

.filter-group {
  display: flex;
  gap: 12px;
  align-items: center;
}

.level-filter-dropdown {
  position: relative;
}

.filter-button {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 16px;
  border: 1px solid var(--terminal-border);
  border-radius: 8px;
  background: #2d2d2d;
  color: #e0e0e0;
  font-size: 13px;
  cursor: pointer;
  transition: all 0.2s ease;
  white-space: nowrap;
}

.filter-button:hover {
  background: #383838;
  border-color: var(--primary);
}

.filter-dropdown-menu {
  position: absolute;
  top: calc(100% + 8px);
  right: 0;
  z-index: 1000;
  min-width: 220px;
  padding: 8px;
  background: #252526;
  border: 1px solid var(--terminal-border);
  border-radius: 12px;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.5);
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.filter-option {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 12px;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
  user-select: none;
  color: #d4d4d4;
  font-size: 13px;
}

.filter-option:hover {
  background: rgba(255,255,255,0.05);
}

.filter-option input[type="checkbox"] {
  width: 16px;
  height: 16px;
  cursor: pointer;
  accent-color: var(--primary);
}

.level-badge {
  padding: 2px 8px;
  border-radius: 4px;
  font-weight: 600;
  font-size: 11px;
  flex: 1;
  text-align: center;
}

.level-badge.level-debug { background: #4b5563; color: white; }
.level-badge.level-info { background: #2563eb; color: white; }
.level-badge.level-warning { background: #d97706; color: white; }
.level-badge.level-error { background: #dc2626; color: white; }
.level-badge.level-critical { background: #991b1b; color: white; }

.search-input {
  padding: 8px 12px;
  border: 1px solid var(--terminal-border);
  border-radius: 8px;
  background: #1e1e1e;
  color: #e0e0e0;
  font-size: 13px;
  min-width: 240px;
  transition: all 0.2s;
}

.search-input:focus {
  outline: none;
  border-color: var(--primary);
  box-shadow: 0 0 0 2px rgba(249, 115, 22, 0.2);
}

/* 统计栏 */
.stats-bar {
  padding: 10px 24px;
  border-bottom: 1px solid var(--terminal-border);
  background: #1e1e1e;
  display: flex;
  gap: 24px;
  flex-wrap: wrap;
  flex-shrink: 0;
  font-size: 12px;
}

.stat-item {
  display: flex;
  align-items: center;
  gap: 8px;
  font-family: 'JetBrains Mono', 'Consolas', monospace;
}

.stat-label {
  color: #858585;
}

.stat-value {
  font-weight: 600;
  color: #d4d4d4;
  background: rgba(255,255,255,0.05);
  padding: 2px 6px;
  border-radius: 4px;
}

.stat-value.level-debug { color: #9ca3af; }
.stat-value.level-info { color: #60a5fa; }
.stat-value.level-warning { color: #fbbf24; }
.stat-value.level-error { color: #f87171; }
.stat-value.level-critical { color: #ef4444; }

/* 日志内容区 - 命令行样式 */
.log-content {
  flex: 1;
  overflow-y: auto;
  overflow-x: auto;
  padding: 16px;
  min-height: 0;
  background: #1e1e1e;
  font-family: 'JetBrains Mono', 'Consolas', 'Monaco', monospace;
}

.log-content::-webkit-scrollbar {
  width: 12px;
  height: 12px;
}

.log-content::-webkit-scrollbar-track {
  background: #1e1e1e;
}

.log-content::-webkit-scrollbar-thumb {
  background: #424242;
  border-radius: 6px;
  border: 3px solid #1e1e1e;
}

.log-content::-webkit-scrollbar-thumb:hover {
  background: #4f4f4f;
}

/* 命令行样式的日志条目 */
.log-entries.terminal-style {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.log-entry.terminal-line {
  padding: 4px 8px;
  border-radius: 4px;
  background: transparent;
  transition: background 0.1s ease;
  animation: terminalFadeIn 0.15s ease-out;
  font-family: 'JetBrains Mono', 'Consolas', monospace;
  font-size: 13px;
  line-height: 1.6;
  white-space: pre-wrap;
  word-break: break-word;
  display: flex;
  gap: 12px;
}

@keyframes terminalFadeIn {
  from { opacity: 0; transform: translateX(-5px); }
  to { opacity: 1; transform: translateX(0); }
}

.log-entry.terminal-line:hover {
  background: rgba(255, 255, 255, 0.05);
}

/* 时间戳 - 橙黄色 */
.terminal-time {
  color: #737373;
  flex-shrink: 0;
  font-weight: normal;
  font-size: 12px;
  opacity: 0.8;
}

/* 日志级别 - 根据级别显示不同颜色 */
.terminal-level {
  font-weight: bold;
  flex-shrink: 0;
  min-width: 80px;
  text-align: center;
  border-radius: 4px;
  font-size: 11px;
  padding: 0 4px;
  height: fit-content;
  align-self: flex-start;
  margin-top: 2px;
}

.terminal-level.level-debug { color: #9ca3af; background: rgba(156, 163, 175, 0.1); }
.terminal-level.level-info { color: #60a5fa; background: rgba(96, 165, 250, 0.1); }
.terminal-level.level-warning { color: #fbbf24; background: rgba(251, 191, 36, 0.1); }
.terminal-level.level-error { color: #f87171; background: rgba(248, 113, 113, 0.1); }
.terminal-level.level-critical { color: #ef4444; background: rgba(239, 68, 68, 0.15); border: 1px solid rgba(239, 68, 68, 0.3); }

/* Logger名称 */
.terminal-logger {
  color: #a3a3a3;
  flex-shrink: 0;
  font-weight: normal;
  opacity: 0.9;
}

/* 消息内容 */
.terminal-message {
  color: #e5e5e5;
  flex: 1;
  word-break: break-word;
}

/* 错误级别的消息使用红色背景 */
.log-entry.terminal-line.level-error {
  background: rgba(239, 68, 68, 0.05);
  border-left: 2px solid #ef4444;
}

.log-entry.terminal-line.level-critical {
  background: rgba(220, 38, 38, 0.1);
  border-left: 2px solid #dc2626;
}

/* 警告级别的消息使用橙色背景 */
.log-entry.terminal-line.level-warning {
  background: rgba(245, 158, 11, 0.05);
  border-left: 2px solid #f59e0b;
}

.entry-extra {
  margin-top: 8px;
  font-size: 12px;
}

.entry-extra details {
  cursor: pointer;
}

.entry-extra summary {
  color: var(--primary);
  user-select: none;
}

.entry-extra pre {
  margin-top: 8px;
  padding: 12px;
  background: #121212;
  border-radius: 8px;
  overflow-x: auto;
  font-family: 'JetBrains Mono', 'Consolas', monospace;
  font-size: 12px;
  color: #d4d4d4;
  border: 1px solid #333;
}

/* 空状态 */
.empty-state,
.loading-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 80px 20px;
  color: #6e6e6e;
  height: 100%;
  font-family: 'JetBrains Mono', 'Consolas', monospace;
}

.empty-icon,
.loading-icon {
  font-size: 48px;
  margin-bottom: 16px;
  opacity: 0.5;
  color: #525252;
}

.empty-state p,
.loading-state p {
  font-size: 14px;
  margin: 0;
  color: #858585;
}

.spinning {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

/* 响应式 */
@media (max-width: 768px) {
  .content-wrapper {
    padding: 16px;
  }
  
  .toolbar {
    flex-direction: column;
    align-items: stretch;
  }
  
  .toolbar-left,
  .toolbar-right {
    width: 100%;
    flex-wrap: wrap;
  }
  
  .filter-group {
    width: 100%;
    flex-wrap: wrap;
  }
  
  .search-input {
    flex: 1;
    min-width: auto;
  }
}
</style>
