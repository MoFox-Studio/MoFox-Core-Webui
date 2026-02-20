<!--
  @file LogViewerView.vue
  @description Material Design 3 风格的历史日志查看器
-->
<template>
  <div class="log-viewer-view">
    <!-- 页面标题 -->
    <div class="page-header">
      <div class="header-content">
        <div class="title-group">
          <span class="material-symbols-rounded title-icon">history</span>
          <h1 class="page-title">历史日志</h1>
        </div>
        <p class="page-description">查看和搜索历史日志文件</p>
      </div>
    </div>

    <!-- 主内容区 -->
    <div class="content-wrapper">
      <div class="main-grid">
        <!-- 左侧：文件列表 -->
        <div class="file-panel m3-card">
          <div class="panel-header">
            <div class="header-title">
              <span class="material-symbols-rounded">folder_open</span>
              <h3>日志文件</h3>
            </div>
            <button 
              class="m3-icon-button" 
              @click="loadLogFiles" 
              title="刷新列表"
              :disabled="loadingFiles"
            >
              <span class="material-symbols-rounded" :class="{ spinning: loadingFiles }">refresh</span>
            </button>
          </div>
          
          <div class="file-list" v-if="!loadingFiles && logFiles.length > 0">
            <div 
              v-for="file in logFiles" 
              :key="file.name"
              class="file-item"
              :class="{ active: selectedFile === file.name }"
              @click="selectFile(file.name)"
            >
              <span class="material-symbols-rounded file-icon">description</span>
              <div class="file-info">
                <div class="file-name">{{ file.name }}</div>
                <div class="file-meta">{{ file.size_human }} · {{ file.mtime_human }}</div>
              </div>
            </div>
          </div>
          
          <div v-else-if="loadingFiles" class="loading-state">
            <span class="material-symbols-rounded spinning">refresh</span>
            <p>正在加载文件列表...</p>
          </div>
          
          <div v-else class="empty-state">
            <span class="material-symbols-rounded">folder_off</span>
            <p>暂无日志文件</p>
          </div>
        </div>

        <!-- 右侧：日志内容 -->
        <div class="log-panel m3-card">
          <!-- 工具栏 -->
          <div class="toolbar" v-if="selectedFile">
            <div class="toolbar-left">
              <span class="material-symbols-rounded">{{ selectedFile.endsWith('.gz') ? 'folder_zip' : 'description' }}</span>
              <span class="file-title">{{ selectedFile }}</span>
              <span class="log-count" v-if="stats">{{ totalEntries }} 条记录</span>
            </div>
            
            <div class="toolbar-right">
              <div class="search-box">
                <span class="material-symbols-rounded search-icon">search</span>
                <input 
                  v-model="searchQuery" 
                  @keyup.enter="performSearch" 
                  placeholder="搜索日志内容..."
                  class="search-input"
                />
                <button 
                  v-if="searchQuery" 
                  class="m3-icon-button small"
                  @click="searchQuery = ''; performSearch()"
                >
                  <span class="material-symbols-rounded">close</span>
                </button>
              </div>
            </div>
          </div>

          <!-- 日志内容区域 -->
          <div class="log-content" ref="logContainer">
            <!-- 欢迎/空状态 -->
            <div v-if="!selectedFile" class="welcome-screen">
              <span class="material-symbols-rounded welcome-icon">inbox</span>
              <h3>请选择日志文件</h3>
              <p>从左侧列表中选择一个日志文件开始查看</p>
            </div>

            <!-- 加载状态 -->
            <div v-else-if="loadingLogs && logEntries.length === 0" class="loading-state">
              <span class="material-symbols-rounded spinning">refresh</span>
              <p>正在加载日志...</p>
            </div>

            <!-- 日志列表 -->
            <div v-else class="log-list">
              <div v-for="(entry, index) in logEntries" :key="index" class="log-entry">
                <span class="timestamp">{{ formatTime(entry.timestamp) }}</span>
                <span :class="['level-badge', `level-${entry.level.toLowerCase()}`]">
                  {{ entry.level }}
                </span>
                <span class="logger" :style="{ color: entry.logger_color || 'var(--md-sys-color-tertiary)' }">
                  {{ entry.logger_name || 'root' }}
                </span>
                <span class="message" v-html="highlightMessage(entry.event)"></span>
              </div>

              <!-- 空结果 -->
              <div v-if="logEntries.length === 0" class="empty-result">
                <span class="material-symbols-rounded">search_off</span>
                <p>没有找到匹配的日志记录</p>
              </div>

              <!-- 分页 -->
              <div class="pagination" v-if="totalPages > 1">
                <button 
                  class="m3-button text" 
                  :disabled="currentPage <= 1"
                  @click="goToPage(currentPage - 1)"
                >
                  <span class="material-symbols-rounded">chevron_left</span>
                  <span>上一页</span>
                </button>
                
                <span class="page-info">第 {{ currentPage }} / {{ totalPages }} 页</span>
                
                <button 
                  class="m3-button text" 
                  :disabled="currentPage >= totalPages"
                  @click="goToPage(currentPage + 1)"
                >
                  <span>下一页</span>
                  <span class="material-symbols-rounded">chevron_right</span>
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, nextTick, computed } from 'vue'
import {
  getLogFiles as apiGetLogFiles,
  searchLogs as apiSearchLogs,
  getLogStats as apiGetLogStats
} from '@/api/log_viewer'
import type { LogFile, LogEntry, LogStats } from '@/api/log_viewer'

// 状态
const loadingFiles = ref(false)
const loadingLogs = ref(false)
const logFiles = ref<LogFile[]>([])
const selectedFile = ref<string>('')
const logEntries = ref<LogEntry[]>([])
const stats = ref<LogStats | null>(null)
const logContainer = ref<HTMLElement | null>(null)

// 搜索和分页
const searchQuery = ref('')
const currentPage = ref(1)
const pageSize = ref(100)
const totalEntries = ref(0)
const totalPages = computed(() => Math.ceil(totalEntries.value / pageSize.value))

// API 调用
const loadLogFiles = async () => {
  loadingFiles.value = true
  try {
    const res = await apiGetLogFiles()
    // 修复：安全检查 res.files 是否存在
    if (res && res.success && Array.isArray(res.data?.files)) {
      logFiles.value = res.data.files.sort((a, b) => b.mtime - a.mtime)
    } else {
      logFiles.value = []
      console.warn('Invalid response from getLogFiles API', res)
    }
  } catch (error) {
    console.error('Failed to load file list', error)
    logFiles.value = []
  } finally {
    loadingFiles.value = false
  }
}

const selectFile = async (filename: string) => {
  if (selectedFile.value === filename) return
  selectedFile.value = filename
  currentPage.value = 1
  searchQuery.value = ''
  logEntries.value = []
  
  await loadStats()
  await performSearch()
}

const loadStats = async () => {
  if (!selectedFile.value) return
  try {
    const res = await apiGetLogStats(selectedFile.value)
    stats.value = res
  } catch (error) {
    console.error('Failed to load stats', error)
    stats.value = null
  }
}

const performSearch = async () => {
  if (!selectedFile.value) return
  
  loadingLogs.value = true
  try {
    const res = await apiSearchLogs({
      filename: selectedFile.value,
      query: searchQuery.value,
      limit: pageSize.value,
      offset: (currentPage.value - 1) * pageSize.value
    })
    
    if (res && res.success) {
      logEntries.value = res.data?.entries || []
      totalEntries.value = res.data?.total || 0
      
      // 滚动到顶部
      nextTick(() => {
        if (logContainer.value) {
          logContainer.value.scrollTop = 0
        }
      })
    }
  } catch (error) {
    console.error('Search failed', error)
    logEntries.value = []
    totalEntries.value = 0
  } finally {
    loadingLogs.value = false
  }
}

const goToPage = (page: number) => {
  if (page < 1 || page > totalPages.value) return
  currentPage.value = page
  performSearch()
}

// 工具函数
const formatTime = (isoString: string) => {
  if (!isoString) return '--:--:--'
  try {
    const date = new Date(isoString)
    // 检查日期是否有效
    if (isNaN(date.getTime())) {
      // 尝试简单解析 ISO 格式的时间部分 (YYYY-MM-DDTHH:mm:ss.xxx)
      const match = isoString.match(/T?(\d{2}):(\d{2}):(\d{2})/)
      if (match) {
        return `${match[1]}:${match[2]}:${match[3]}`
      }
      return '--:--:--'
    }
    return date.toLocaleTimeString('zh-CN', { 
      hour: '2-digit', 
      minute: '2-digit', 
      second: '2-digit',
      hour12: false
    })
  } catch {
    return '--:--:--'
  }
}

const highlightMessage = (msg: string) => {
  if (!msg) return ''
  if (!searchQuery.value) return msg
  
  // 简单的高亮，转义特殊字符
  const escaped = searchQuery.value.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
  const reg = new RegExp(`(${escaped})`, 'gi')
  return msg.replace(reg, '<mark class="highlight">$1</mark>')
}

onMounted(() => {
  loadLogFiles()
})
</script>

<style scoped>
/* ==================== 基础布局 ==================== */
.log-viewer-view {
  display: flex;
  flex-direction: column;
  height: 100%;
  padding: 16px;
  gap: 16px;
  padding: 0;
  overflow: hidden;
}

/* ==================== 页面标题 ==================== */
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

.page-description {
  font-size: 14px;
  color: var(--md-sys-color-on-surface-variant);
  margin: 0;
}

/* ==================== 主内容区 ==================== */
.content-wrapper {
  flex: 1;
  overflow: hidden;
  padding: 0;
  display: flex;
  flex-direction: column;
  min-height: 0;
}

.main-grid {
  display: grid;
  grid-template-columns: 320px 1fr;
  gap: 24px;
  height: 100%;
  padding: 16px;
}

/* ==================== 文件面板 ==================== */
.file-panel {
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.panel-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16px;
  padding-bottom: 12px;
  border-bottom: 1px solid var(--md-sys-color-outline-variant);
}

.header-title {
  display: flex;
  align-items: center;
  gap: 8px;
}

.header-title .material-symbols-rounded {
  font-size: 20px;
  color: var(--md-sys-color-primary);
}

.header-title h3 {
  font: var(--md-sys-typescale-title-medium);
  color: var(--md-sys-color-on-surface);
  margin: 0;
}

.file-list {
  flex: 1;
  overflow-y: auto;
  margin: -8px;
  padding: 8px;
}

.file-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  border-radius: 12px;
  cursor: pointer;
  transition: all var(--transition-fast);
  margin-bottom: 4px;
}

.file-item:hover {
  background: var(--md-sys-color-surface-container-high);
}

.file-item.active {
  background: var(--md-sys-color-primary-container);
}

.file-icon {
  font-size: 20px;
  color: var(--md-sys-color-on-surface-variant);
  flex-shrink: 0;
}

.file-item.active .file-icon {
  color: var(--md-sys-color-primary);
}

.file-info {
  flex: 1;
  min-width: 0;
}

.file-name {
  font-size: 14px;
  font-weight: 500;
  color: var(--md-sys-color-on-surface);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.file-item.active .file-name {
  color: var(--md-sys-color-on-primary-container);
}

.file-meta {
  font-size: 12px;
  color: var(--md-sys-color-on-surface-variant);
  margin-top: 2px;
}

.file-item.active .file-meta {
  color: var(--md-sys-color-on-primary-container);
  opacity: 0.8;
}

/* ==================== 日志面板 ==================== */
.log-panel {
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 16px;
  padding-bottom: 12px;
  border-bottom: 1px solid var(--md-sys-color-outline-variant);
  flex-wrap: wrap;
}

.toolbar-left {
  display: flex;
  align-items: center;
  gap: 12px;
  flex: 1;
  min-width: 0;
}

.toolbar-left .material-symbols-rounded {
  font-size: 20px;
  color: var(--md-sys-color-primary);
  flex-shrink: 0;
}

.file-title {
  font-size: 14px;
  font-weight: 500;
  color: var(--md-sys-color-on-surface);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.log-count {
  font-size: 12px;
  color: var(--md-sys-color-on-surface-variant);
  padding: 4px 12px;
  background: var(--md-sys-color-surface-container-high);
  border-radius: 12px;
  flex-shrink: 0;
}

.toolbar-right {
  display: flex;
  align-items: center;
  gap: 8px;
}

.search-box {
  display: flex;
  align-items: center;
  gap: 8px;
  background: var(--md-sys-color-surface-container-high);
  border: 1px solid var(--md-sys-color-outline-variant);
  border-radius: 20px;
  padding: 6px 16px;
  min-width: 280px;
  transition: all var(--transition-fast);
}

.search-box:focus-within {
  border-color: var(--md-sys-color-primary);
  background: var(--md-sys-color-surface);
}

.search-icon {
  font-size: 20px;
  color: var(--md-sys-color-on-surface-variant);
}

.search-input {
  flex: 1;
  border: none;
  background: transparent;
  font-size: 14px;
  color: var(--md-sys-color-on-surface);
  outline: none;
}

.search-input::placeholder {
  color: var(--md-sys-color-on-surface-variant);
  opacity: 0.6;
}

/* ==================== 日志内容 ==================== */
.log-content {
  flex: 1;
  overflow-y: auto;
  margin: -8px;
  padding: 8px;
  font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
}

.log-list {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.log-entry {
  display: flex;
  align-items: baseline;
  gap: 12px;
  padding: 6px 12px;
  border-radius: 8px;
  font-size: 13px;
  line-height: 1.6;
  transition: background var(--transition-fast);
}

.log-entry:hover {
  background: var(--md-sys-color-surface-container-high);
}

.timestamp {
  color: var(--md-sys-color-on-surface-variant);
  font-size: 12px;
  flex-shrink: 0;
  font-weight: 500;
}

.level-badge {
  font-size: 11px;
  font-weight: 600;
  padding: 2px 8px;
  border-radius: 4px;
  flex-shrink: 0;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.level-debug {
  background: rgba(128, 128, 128, 0.1);
  color: #808080;
}

.level-info {
  background: rgba(33, 150, 243, 0.1);
  color: #2196F3;
}

.level-warning {
  background: rgba(255, 152, 0, 0.1);
  color: #FF9800;
}

.level-error {
  background: rgba(244, 67, 54, 0.1);
  color: #F44336;
}

.level-critical {
  background: #B00020;
  color: #FFFFFF;
}

.logger {
  font-size: 12px;
  font-weight: 500;
  flex-shrink: 0;
  max-width: 150px;
  overflow: hidden;
  text-overflow: ellipsis;
}

.message {
  color: var(--md-sys-color-on-surface);
  word-break: break-word;
  flex: 1;
}

.message :deep(mark.highlight) {
  background: var(--md-sys-color-tertiary-container);
  color: var(--md-sys-color-on-tertiary-container);
  padding: 2px 4px;
  border-radius: 3px;
  font-weight: 600;
}

/* ==================== 状态页面 ==================== */
.welcome-screen,
.loading-state,
.empty-state,
.empty-result {
  height: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 16px;
  color: var(--md-sys-color-on-surface-variant);
  text-align: center;
}

.welcome-icon,
.loading-state .material-symbols-rounded,
.empty-state .material-symbols-rounded,
.empty-result .material-symbols-rounded {
  font-size: 64px;
  opacity: 0.3;
}

.welcome-screen h3,
.loading-state p,
.empty-state p,
.empty-result p {
  margin: 0;
  font-size: 16px;
}

.welcome-screen p {
  font-size: 14px;
  opacity: 0.7;
}

/* ==================== 分页 ==================== */
.pagination {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 16px;
  margin-top: 24px;
  padding-top: 16px;
  border-top: 1px solid var(--md-sys-color-outline-variant);
}

.page-info {
  font-size: 14px;
  color: var(--md-sys-color-on-surface-variant);
  min-width: 120px;
  text-align: center;
}

/* ==================== 动画 ==================== */
@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.spinning {
  animation: spin 1s linear infinite;
}

/* ==================== 滚动条美化 ==================== */
.file-list::-webkit-scrollbar,
.log-content::-webkit-scrollbar {
  width: 8px;
}

.file-list::-webkit-scrollbar-track,
.log-content::-webkit-scrollbar-track {
  background: transparent;
}

.file-list::-webkit-scrollbar-thumb,
.log-content::-webkit-scrollbar-thumb {
  background: var(--md-sys-color-outline-variant);
  border-radius: 4px;
}

.file-list::-webkit-scrollbar-thumb:hover,
.log-content::-webkit-scrollbar-thumb:hover {
  background: var(--md-sys-color-outline);
}

/* ==================== 响应式 ==================== */
@media (max-width: 1024px) {
  .main-grid {
    grid-template-columns: 1fr;
  }
  
  .file-panel {
    max-height: 300px;
  }
}
</style>