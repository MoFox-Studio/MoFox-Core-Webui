<!--
  @file LiveLogView.vue
  @description 实时日志查看页面
  
  功能说明：
  1. 实时接收和显示系统日志（SSE 连接）
  2. 日志级别筛选（DEBUG/INFO/WARNING/ERROR/CRITICAL）
  3. 关键词搜索
  4. 自动滚动到最新日志
  
  连接状态：
  - 显示当前连接状态（已连接/未连接）
  - 支持手动开始/停止监听
  
  工具栏功能：
  - 开始/断开连接
  - 清空日志
  - 自动滚动开关
  - 日志级别筛选
  - 内容搜索
  
  统计信息：
  - 日志总数、已筛选数量、各级别数量
-->
<template>
  <div class="live-log-view">
    <!-- 页面标题：标题和连接状态指示 -->
    <div class="page-header">
      <div class="header-content">
        <div class="title-group">
          <span class="material-symbols-rounded title-icon">sensors</span>
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
              class="m3-button filled" 
              @click="toggleRealtime"
              :disabled="connecting"
            >
              <span class="material-symbols-rounded">{{ realtimeEnabled ? 'pause' : 'play_arrow' }}</span>
              <span>{{ realtimeEnabled ? '断开连接' : '开始监听' }}</span>
            </button>
            
            <button 
              class="m3-button text error" 
              @click="clearRealtimeLogs"
              :disabled="!realtimeEnabled && realtimeLogs.length === 0"
            >
              <span class="material-symbols-rounded">delete</span>
              <span>清空日志</span>
            </button>
            
            <div class="separator-line"></div>
            
            <div class="m3-switch-container">
              <label class="m3-switch">
                <input type="checkbox" v-model="autoScroll" />
                <span class="slider"></span>
              </label>
              <span class="switch-label">自动滚动</span>
            </div>
          </div>
          
          <div class="toolbar-right">
            <div class="filter-group">
              <div class="level-filter-dropdown">
                <button class="m3-filter-chip" @click="toggleLevelFilter" :class="{ active: showLevelFilter }">
                  <span class="material-symbols-rounded">filter_list</span>
                  <span>日志级别 ({{ selectedLevels.length }})</span>
                  <span class="material-symbols-rounded">{{ showLevelFilter ? 'expand_less' : 'expand_more' }}</span>
                </button>
                <div v-if="showLevelFilter" class="filter-dropdown-menu m3-card">
                  <label v-for="level in logLevels" :key="level" class="filter-option">
                    <input 
                      type="checkbox" 
                      :value="level" 
                      v-model="selectedLevels"
                    />
                    <span :class="['level-badge', 'level-' + level.toLowerCase()]">{{ level }}</span>
                  </label>
                </div>
              </div>
              
              <div class="search-box">
                <span class="material-symbols-rounded search-icon">search</span>
                <input 
                  v-model="searchQuery" 
                  type="text" 
                  class="m3-input"
                  placeholder="搜索日志内容..."
                />
              </div>
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
            <span class="stat-value" :class="'level-' + level.toLowerCase()">{{ count }}</span>
          </div>
        </div>

        <!-- 日志内容区域 -->
        <div class="log-content" ref="logContentContainer">
          <div v-if="connecting" class="loading-state">
            <span class="material-symbols-rounded spinning loading-icon">progress_activity</span>
            <p>正在连接...</p>
          </div>

          <div v-else-if="!realtimeEnabled && realtimeLogs.length === 0" class="empty-state">
            <span class="material-symbols-rounded empty-icon">sensors</span>
            <p>点击"开始监听"按钮开始接收实时日志</p>
          </div>

          <div v-else-if="filteredLogs.length === 0" class="empty-state">
            <span class="material-symbols-rounded empty-icon">filter_list_off</span>
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

// Python 字典转 JSON 的状态机解析器
const pythonDictToJson = (pythonStr: string): string => {
  let inString = false
  let stringChar = ''
  let escaped = false
  let result = ''
  
  for (let i = 0; i < pythonStr.length; i++) {
    const char = pythonStr[i]
    
    if (!inString) {
      // 不在字符串内
      if ((char === "'" || char === '"') && !escaped) {
        // 开始字符串 - 统一转换为双引号
        inString = true
        stringChar = char
        result += '"'
      } else if (char === ':' && pythonStr.substring(i + 1).match(/^\s*(True|False|None)\b/)) {
        // 处理 Python 的 True/False/None
        const match = pythonStr.substring(i + 1).match(/^\s*(True|False|None)\b/)
        if (match) {
          if (match[1] === 'True') result += ': true'
          else if (match[1] === 'False') result += ': false'
          else if (match[1] === 'None') result += ': null'
          i += match[0].length
        }
      } else {
        result += char
      }
    } else {
      // 在字符串内
      if (escaped) {
        // 处理转义字符
        if (char === stringChar) {
          // 转义的引号：保留反斜杠和引号
          // 如果原字符串是单引号，转义后的单引号在 JSON 中不需要转义
          // 如果是双引号，需要转义
          if (stringChar === "'") {
            result += char  // JSON 中单引号不需要转义，直接输出
          } else {
            result += '\\' + char  // JSON 中双引号需要转义
          }
        } else if (char === '\\') {
          result += '\\\\'  // 反斜杠需要双重转义
        } else if (char === 'n') {
          result += '\\n'
        } else if (char === 'r') {
          result += '\\r'
        } else if (char === 't') {
          result += '\\t'
        } else if (char === '"') {
          // 字符串内的双引号需要转义
          result += '\\"'
        } else {
          // 其他转义字符保持原样
          result += '\\' + char
        }
        escaped = false
      } else if (char === '\\') {
        // 转义字符开始
        escaped = true
      } else if (char === stringChar) {
        // 字符串结束
        inString = false
        stringChar = ''
        result += '"'
      } else if (char === '"') {
        // 字符串内部的双引号需要转义
        result += '\\"'
      } else {
        // 普通字符
        result += char
      }
    }
  }
  
  return result
}

// 格式化日志消息（处理 ANSI 转义序列和 JSON）
const formatLogMessage = (message: string) => {
  if (!message) return ''
  
  // 检查是否是 Python 字典格式的字符串
  const trimmedMessage = message.trim()
  if (trimmedMessage.startsWith('{') && trimmedMessage.endsWith('}')) {
    try {
      // 使用改进的 Python 字典解析逻辑
      // 1. 先尝试直接解析（可能已经是标准 JSON）
      let parsed = null
      try {
        parsed = JSON.parse(trimmedMessage)
      } catch {
        // 2. 如果直接解析失败，使用状态机解析器
        const jsonStr = pythonDictToJson(trimmedMessage)
        parsed = JSON.parse(jsonStr)
      }
      
      // 如果成功解析且包含 event 字段，提取并返回
      if (parsed && typeof parsed === 'object' && parsed.event) {
        return escapeHtml(parsed.event)
      }
    } catch (e) {
      console.warn('解析 Python 字典格式失败，将作为普通文本处理:', e)
      // 解析失败，继续作为普通文本处理
    }
  }
  
  // 处理 ANSI 转义序列 - 改进版本，支持更多格式
  // 匹配 ANSI 颜色代码: \x1b[<codes>m 或 \033[<codes>m
  const ansiRegex = /[\x1b\x9b]\[([0-9;]+)m/g
  
  // 完整的 ANSI 颜色映射表
  const colorMap: Record<string, string> = {
    // 标准前景色 (30-37)
    '30': '#000000', '31': '#e74c3c', '32': '#2ecc71', '33': '#f39c12',
    '34': '#3498db', '35': '#9b59b6', '36': '#1abc9c', '37': '#ecf0f1',
    // 亮色前景色 (90-97)
    '90': '#7f8c8d', '91': '#ff6b6b', '92': '#51cf66', '93': '#ffd43b',
    '94': '#74c0fc', '95': '#da77f2', '96': '#3bc9db', '97': '#ffffff',
    // 标准背景色 (40-47)
    '40': '#000000', '41': '#e74c3c', '42': '#2ecc71', '43': '#f39c12',
    '44': '#3498db', '45': '#9b59b6', '46': '#1abc9c', '47': '#ecf0f1',
    // 亮色背景色 (100-107)
    '100': '#7f8c8d', '101': '#ff6b6b', '102': '#51cf66', '103': '#ffd43b',
    '104': '#74c0fc', '105': '#da77f2', '106': '#3bc9db', '107': '#ffffff'
  }
  
  let result = ''
  let lastIndex = 0
  let currentColor = ''
  let currentBgColor = ''
  let isBold = false
  let match: RegExpExecArray | null
  
  while ((match = ansiRegex.exec(message)) !== null) {
    // 提取两个转义序列之间的文本
    const text = message.substring(lastIndex, match.index)
    if (text) {
      // 应用当前样式
      let style = ''
      if (currentColor) style += `color: ${currentColor};`
      if (currentBgColor) style += ` background-color: ${currentBgColor};`
      if (isBold) style += ' font-weight: bold;'
      
      if (style) {
        result += `<span style="${style}">${escapeHtml(text)}</span>`
      } else {
        result += escapeHtml(text)
      }
    }
    
    // 解析 ANSI 代码 (可能是多个代码用分号分隔，如 "1;31")
    const codes = match[1]?.split(';') || []
    for (const code of codes) {
      if (code === '0' || code === '') {
        // 重置所有样式
        currentColor = ''
        currentBgColor = ''
        isBold = false
      } else if (code === '1') {
        // 粗体
        isBold = true
      } else if (code === '22') {
        // 取消粗体
        isBold = false
      } else if (colorMap[code]) {
        // 前景色或背景色
        const codeNum = parseInt(code)
        if ((codeNum >= 30 && codeNum <= 37) || (codeNum >= 90 && codeNum <= 97)) {
          currentColor = colorMap[code]
        } else if ((codeNum >= 40 && codeNum <= 47) || (codeNum >= 100 && codeNum <= 107)) {
          currentBgColor = colorMap[code]
        }
      }
    }
    
    lastIndex = ansiRegex.lastIndex
  }
  
  // 处理剩余文本
  const remainingText = message.substring(lastIndex)
  if (remainingText) {
    let style = ''
    if (currentColor) style += `color: ${currentColor};`
    if (currentBgColor) style += ` background-color: ${currentBgColor};`
    if (isBold) style += ' font-weight: bold;'
    
    if (style) {
      result += `<span style="${style}">${escapeHtml(remainingText)}</span>`
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
    // 使用相对路径，自动通过代理服务器转发（开发环境走Vite代理，生产环境走发现服务器代理）
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    const wsUrl = `${protocol}//${window.location.host}/ws/plugins/webui_backend/log_viewer/realtime`
    
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
  display: flex;
  flex-direction: column;
  height: 100%;
  padding: 16px;
  gap: 16px;
  animation: fadeIn 0.4s cubic-bezier(0.2, 0, 0, 1);
  background: var(--md-sys-color-surface);
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}

/* 页面标题 */
.page-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 24px;
  background: var(--md-sys-color-surface-container);
  border-radius: 32px;
  flex-shrink: 0;
}

.header-content {
  width: 100%;
  margin: 0;
}

.title-group {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 8px;
}

.title-icon {
  font-size: 28px;
  color: var(--md-sys-color-primary);
}

.page-title {
  font-size: 24px;
  font-weight: 400;
  color: var(--md-sys-color-on-surface);
  margin: 0;
}

.status-badge {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 4px 12px;
  border-radius: 16px;
  background: var(--md-sys-color-surface-container-highest);
  border: 1px solid var(--md-sys-color-outline);
  font-size: 12px;
  font-weight: 500;
  color: var(--md-sys-color-on-surface-variant);
}

.status-badge.connected {
  background: var(--md-sys-color-tertiary-container);
  border-color: transparent;
  color: var(--md-sys-color-on-tertiary-container);
}

.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--md-sys-color-outline);
}

.status-badge.connected .status-dot {
  background: var(--md-sys-color-on-tertiary-container);
  animation: pulse 2s infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}

.page-description {
  font-size: 14px;
  color: var(--md-sys-color-on-surface-variant);
  margin: 0;
}

/* 主内容区 */
.content-wrapper {
  flex: 1;
  overflow: hidden;
  padding: 0;
  display: flex;
  flex-direction: column;
  min-height: 0;
}

.log-container {
  width: 100%;
  height: 100%;
  max-height: none;
  display: flex;
  flex-direction: column;
  background: var(--md-sys-color-surface-container);
  border-radius: 32px;
  border: none;
  overflow: hidden;
  box-shadow: none;
}

/* 工具栏 */
.toolbar {
  padding: 16px;
  border-bottom: 1px solid var(--md-sys-color-outline-variant);
  background: var(--md-sys-color-surface-container);
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

.separator-line {
  width: 1px;
  height: 24px;
  background: var(--md-sys-color-outline-variant);
  margin: 0 4px;
}

.m3-switch-container {
  display: flex;
  align-items: center;
  gap: 12px;
}

.switch-label {
  font-size: 14px;
  color: var(--md-sys-color-on-surface);
}

.m3-button.error {
  color: var(--md-sys-color-error);
}

.filter-group {
  display: flex;
  gap: 8px;
  align-items: center;
}

.m3-filter-chip {
  height: 32px;
  padding: 0 12px;
  border-radius: 8px;
  border: 1px solid var(--md-sys-color-outline);
  background: transparent;
  color: var(--md-sys-color-on-surface-variant);
  font-size: 13px;
  font-weight: 500;
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  transition: all 0.2s;
}

.m3-filter-chip:hover {
  background: var(--md-sys-color-surface-container-highest);
}

.m3-filter-chip.active {
  background: var(--md-sys-color-secondary-container);
  color: var(--md-sys-color-on-secondary-container);
  border-color: transparent;
}

.m3-filter-chip .material-symbols-rounded {
  font-size: 18px;
}

.level-filter-dropdown {
  position: relative;
}

.filter-dropdown-menu {
  position: absolute;
  top: calc(100% + 4px);
  left: 0;
  z-index: 1000;
  min-width: 200px;
  padding: 8px;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.filter-option {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
  user-select: none;
}

.filter-option:hover {
  background: var(--md-sys-color-surface-container-highest);
}

.filter-option input[type="checkbox"] {
  width: 16px;
  height: 16px;
  cursor: pointer;
}

.level-badge {
  padding: 2px 8px;
  border-radius: 4px;
  font-weight: 500;
  font-size: 11px;
  flex: 1;
}

.level-badge.level-debug { background: #E0E0E0; color: #424242; }
.level-badge.level-info { background: #E3F2FD; color: #1565C0; }
.level-badge.level-warning { background: #FFF3E0; color: #EF6C00; }
.level-badge.level-error { background: #FFEBEE; color: #C62828; }
.level-badge.level-critical { background: #D32F2F; color: #FFFFFF; }

.search-box {
  position: relative;
  width: 240px;
  height: 40px;
  background: var(--md-sys-color-surface-container-high);
  border-radius: 20px;
  display: flex;
  align-items: center;
  transition: all 0.2s;
}

.search-box:hover {
  background: var(--md-sys-color-surface-container-highest);
}

.search-box:focus-within {
  background: var(--md-sys-color-surface-container-highest);
  box-shadow: 0 0 0 2px var(--md-sys-color-primary);
}

.search-icon {
  position: absolute;
  left: 12px;
  font-size: 20px;
  color: var(--md-sys-color-on-surface-variant);
  pointer-events: none;
}

.search-box .m3-input {
  width: 100%;
  height: 100%;
  background: transparent;
  border: none;
  padding: 0 16px 0 40px;
  font-size: 13px;
  color: var(--md-sys-color-on-surface);
  outline: none;
  border-radius: 20px;
  font-family: inherit;
}

.search-box .m3-input::placeholder {
  color: var(--md-sys-color-on-surface-variant);
}

/* 统计栏 */
.stats-bar {
  padding: 12px 16px;
  border-bottom: 1px solid var(--md-sys-color-outline-variant);
  background: var(--md-sys-color-surface-container-low);
  display: flex;
  gap: 24px;
  flex-wrap: wrap;
  flex-shrink: 0;
}

.stat-item {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  font-family: 'Roboto Mono', 'Noto Sans SC', 'JetBrains Mono', monospace;
}

.stat-label {
  color: var(--md-sys-color-on-surface-variant);
}

.stat-value {
  font-weight: 600;
  color: var(--md-sys-color-on-surface);
}

.stat-value.level-debug { color: #757575; }
.stat-value.level-info { color: #1565C0; }
.stat-value.level-warning { color: #EF6C00; }
.stat-value.level-error { color: #C62828; }
.stat-value.level-critical { color: #D32F2F; }

/* 日志内容区 - 命令行样式 */
.log-content {
  flex: 1;
  overflow-y: auto;
  overflow-x: auto;
  padding: 12px;
  min-height: 0;
  background: #1e1e1e; /* 纯黑背景，确保浅色模式下也能看清 */
  border-radius: 12px; /* 圆角 */
  color: #d4d4d4; /* 浅色文字 */
  font-family: 'Roboto Mono', 'Noto Sans SC', 'JetBrains Mono', monospace;
}

.log-content::-webkit-scrollbar {
  width: 10px;
  height: 10px;
}

.log-content::-webkit-scrollbar-track {
  background: #1e1e1e;
}

.log-content::-webkit-scrollbar-thumb {
  background: #424242;
  border-radius: 5px;
}

.log-content::-webkit-scrollbar-thumb:hover {
  background: #5a5a5a;
}

/* 命令行样式的日志条目 */
.log-entries.terminal-style {
  display: flex;
  flex-direction: column;
  gap: 0;
}

.log-entry.terminal-line {
  padding: 2px 4px;
  border: none;
  background: transparent;
  transition: background 0.1s ease;
  animation: terminalFadeIn 0.15s ease-out;
  font-family: 'Roboto Mono', 'Noto Sans SC', 'JetBrains Mono', monospace;
  font-size: 13px;
  line-height: 1.5;
  white-space: pre-wrap;
  word-break: break-word;
  display: flex;
  gap: 8px;
}

@keyframes terminalFadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

.log-entry.terminal-line:hover {
  background: #2d2d2d;
}

/* 时间戳 */
.terminal-time {
  color: #808080;
  flex-shrink: 0;
  font-weight: normal;
}

/* 日志级别 */
.terminal-level {
  font-weight: bold;
  flex-shrink: 0;
  min-width: 90px;
}

.terminal-level.level-debug { color: #808080; }
.terminal-level.level-info { color: #569cd6; }
.terminal-level.level-warning { color: #ce9178; }
.terminal-level.level-error { color: #f44747; }
.terminal-level.level-critical { 
  color: #ffffff;
  background: #f44747;
  padding: 0 4px;
  border-radius: 4px;
}

/* Logger名称 */
.terminal-logger {
  color: #4ec9b0;
  flex-shrink: 0;
  font-weight: normal;
}

/* 消息内容 */
.terminal-message {
  color: inherit;
  flex: 1;
  word-break: break-word;
  font-family: 'Roboto Mono', 'Noto Sans SC', 'JetBrains Mono', monospace;
}

/* 错误级别的消息 */
.log-entry.terminal-line.level-error {
  background: rgba(244, 71, 71, 0.1);
}

.log-entry.terminal-line.level-critical {
  background: rgba(244, 71, 71, 0.2);
}

/* 警告级别的消息 */
.log-entry.terminal-line.level-warning {
  background: rgba(206, 145, 120, 0.1);
}

/* 空状态 */
.empty-state,
.loading-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px 20px;
  color: #d4d4d4;
  height: 100%;
  font-family: 'Roboto Mono', 'Noto Sans SC', 'JetBrains Mono', monospace;
}

.empty-icon,
.loading-icon {
  font-size: 48px;
  margin-bottom: 12px;
  opacity: 0.5;
  color: #808080;
}

.empty-state p,
.loading-state p {
  font-size: 14px;
  margin: 0;
  color: #d4d4d4;
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
