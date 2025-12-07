<template>
  <div class="log-viewer">
    <!-- 页面标题 -->
    <div class="page-header">
      <div class="header-content">
        <div class="title-group">
          <Icon icon="lucide:file-text" class="title-icon" />
          <h1 class="page-title">日志查看器</h1>
        </div>
        <p class="page-description">查看、搜索和分析系统日志</p>
      </div>
    </div>

    <!-- 主内容区 -->
    <div class="content-wrapper">
      <div class="log-container">
        <!-- 左侧：日志文件列表 -->
        <div class="file-list-panel">
          <div class="panel-header">
            <h3 class="panel-title">日志文件</h3>
            <button class="refresh-button" @click="loadLogFiles" :disabled="loading">
              <Icon icon="lucide:refresh-cw" :class="{ spinning: loading }" />
            </button>
          </div>
          
          <div class="file-list">
            <div 
              v-for="file in logFiles" 
              :key="file.name"
              class="file-item"
              :class="{ active: selectedFile === file.name }"
              @click="selectFile(file.name)"
            >
              <div class="file-info">
                <Icon 
                  :icon="file.compressed ? 'lucide:file-archive' : 'lucide:file-text'" 
                  class="file-icon"
                />
                <div class="file-details">
                  <div class="file-name">{{ file.name }}</div>
                  <div class="file-meta">
                    <span>{{ file.size_human }}</span>
                    <span>{{ file.mtime_human }}</span>
                  </div>
                </div>
              </div>
            </div>
            
            <div v-if="logFiles.length === 0 && !loading" class="empty-state">
              <Icon icon="lucide:inbox" class="empty-icon" />
              <p>暂无日志文件</p>
            </div>
          </div>
        </div>

        <!-- 右侧：日志内容 -->
        <div class="log-content-panel">
          <!-- 搜索和筛选工具栏 -->
          <div class="toolbar">
            <div class="search-group">
              <div class="search-input-wrapper">
                <Icon icon="lucide:search" class="search-icon" />
                <input 
                  v-model="searchQuery"
                  type="text"
                  placeholder="搜索日志内容..."
                  class="search-input"
                  @keyup.enter="searchLogs"
                />
              </div>
              <button 
                class="search-button"
                @click="searchLogs"
                :disabled="!selectedFile || loading"
              >
                搜索
              </button>
            </div>

            <div class="filter-group">
              <select v-model="filterLevel" class="filter-select" @change="searchLogs">
                <option value="">所有级别</option>
                <option value="debug">DEBUG</option>
                <option value="info">INFO</option>
                <option value="warning">WARNING</option>
                <option value="error">ERROR</option>
                <option value="critical">CRITICAL</option>
              </select>

              <select v-model="filterLogger" class="filter-select" @change="searchLogs">
                <option value="">所有模块</option>
                <option v-for="logger in loggers" :key="logger.name" :value="logger.name">
                  {{ logger.alias || logger.name }}
                </option>
              </select>

              <button class="icon-button" @click="showAdvancedFilter = !showAdvancedFilter" title="高级筛选">
                <Icon icon="lucide:filter" />
              </button>

              <button class="icon-button" @click="clearFilters" title="清除筛选">
                <Icon icon="lucide:x" />
              </button>
            </div>
          </div>

          <!-- 高级筛选面板 -->
          <Transition name="slide-down">
            <div v-if="showAdvancedFilter" class="advanced-filter">
              <div class="filter-row">
                <label class="filter-label">开始时间</label>
                <input v-model="filterStartTime" type="datetime-local" class="filter-input" />
              </div>
              <div class="filter-row">
                <label class="filter-label">结束时间</label>
                <input v-model="filterEndTime" type="datetime-local" class="filter-input" />
              </div>
              <div class="filter-row">
                <label class="filter-label">
                  <input v-model="useRegex" type="checkbox" />
                  使用正则表达式
                </label>
              </div>
            </div>
          </Transition>

          <!-- 统计信息 -->
          <div v-if="stats" class="stats-bar">
            <div class="stat-item">
              <span class="stat-label">总计:</span>
              <span class="stat-value">{{ stats.total }}</span>
            </div>
            <div class="stat-item" v-for="(count, level) in stats.by_level" :key="level">
              <span class="stat-label">{{ level.toUpperCase() }}:</span>
              <span class="stat-value" :class="`level-${level}`">{{ count }}</span>
            </div>
          </div>

          <!-- 日志条目列表 -->
          <div class="log-entries" ref="logEntriesContainer">
            <div v-if="loading" class="loading-state">
              <Icon icon="lucide:loader-2" class="loading-icon spinning" />
              <p>加载中...</p>
            </div>

            <div v-else-if="!selectedFile" class="empty-state">
              <Icon icon="lucide:file-search" class="empty-icon" />
              <p>请选择一个日志文件</p>
            </div>

            <div v-else-if="logEntries.length === 0" class="empty-state">
              <Icon icon="lucide:inbox" class="empty-icon" />
              <p>没有找到日志条目</p>
            </div>

            <div v-else class="entries-list">
              <div 
                v-for="entry in logEntries" 
                :key="`${entry.file_name}-${entry.line_number}`"
                class="log-entry"
                :class="`level-${entry.level.toLowerCase()}`"
              >
                <div class="entry-header">
                  <span class="entry-time">{{ formatTimestamp(entry.timestamp) }}</span>
                  <span class="entry-level" :class="`level-${entry.level.toLowerCase()}`">
                    {{ entry.level.toUpperCase() }}
                  </span>
                  <span class="entry-logger" :style="{ color: entry.color }">
                    {{ entry.alias || entry.logger_name }}
                  </span>
                  <span class="entry-line">Line {{ entry.line_number }}</span>
                </div>
                <div class="entry-message">{{ entry.event }}</div>
                <div v-if="entry.extra && Object.keys(entry.extra).length > 0" class="entry-extra">
                  <details>
                    <summary>额外信息</summary>
                    <pre>{{ JSON.stringify(entry.extra, null, 2) }}</pre>
                  </details>
                </div>
              </div>
            </div>
          </div>

          <!-- 分页控制 -->
          <div v-if="logEntries.length > 0" class="pagination">
            <button 
              class="pagination-button"
              :disabled="currentPage === 1"
              @click="goToPage(1)"
            >
              <Icon icon="lucide:chevrons-left" />
            </button>
            <button 
              class="pagination-button"
              :disabled="currentPage === 1"
              @click="goToPage(currentPage - 1)"
            >
              <Icon icon="lucide:chevron-left" />
            </button>
            
            <div class="pagination-info">
              <span>第 {{ currentPage }} / {{ totalPages }} 页</span>
              <span class="separator">|</span>
              <span>共 {{ totalEntries }} 条</span>
            </div>

            <button 
              class="pagination-button"
              :disabled="currentPage === totalPages"
              @click="goToPage(currentPage + 1)"
            >
              <Icon icon="lucide:chevron-right" />
            </button>
            <button 
              class="pagination-button"
              :disabled="currentPage === totalPages"
              @click="goToPage(totalPages)"
            >
              <Icon icon="lucide:chevrons-right" />
            </button>

            <select v-model="pageSize" class="page-size-select" @change="changePageSize">
              <option :value="50">50 条/页</option>
              <option :value="100">100 条/页</option>
              <option :value="200">200 条/页</option>
              <option :value="500">500 条/页</option>
            </select>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { Icon } from '@iconify/vue'
import {
  getLogFiles as apiGetLogFiles,
  searchLogs as apiSearchLogs,
  getLoggers as apiGetLoggers,
  getLogStats as apiGetLogStats
} from '@/api/log_viewer'
import type { LogFile, LogEntry, LoggerInfo, LogStats } from '@/api/log_viewer'

// 状态
const loading = ref(false)
const logFiles = ref<LogFile[]>([])
const selectedFile = ref<string>('')
const logEntries = ref<LogEntry[]>([])
const loggers = ref<LoggerInfo[]>([])
const stats = ref<LogStats | null>(null)

// 搜索和筛选
const searchQuery = ref('')
const filterLevel = ref('')
const filterLogger = ref('')
const filterStartTime = ref('')
const filterEndTime = ref('')
const useRegex = ref(false)
const showAdvancedFilter = ref(false)

// 分页
const currentPage = ref(1)
const pageSize = ref(100)
const totalEntries = ref(0)

const totalPages = computed(() => Math.ceil(totalEntries.value / pageSize.value))

// 加载日志文件列表
const loadLogFiles = async () => {
  loading.value = true
  try {
    const response = await apiGetLogFiles()
    if (response.success && response.data) {
      logFiles.value = response.data.files
    } else {
      console.error('获取日志文件列表失败')
    }
  } catch (error) {
    console.error('加载日志文件失败:', error)
  } finally {
    loading.value = false
  }
}

// 选择日志文件
const selectFile = async (filename: string) => {
  selectedFile.value = filename
  currentPage.value = 1
  
  // 加载该文件的 logger 列表
  await loadLoggers()
  
  // 加载统计信息
  await loadStats()
  
  // 搜索日志
  await performSearch()
}

// 加载 logger 列表
const loadLoggers = async () => {
  if (!selectedFile.value) return
  
  try {
    const response = await apiGetLoggers(selectedFile.value)
    if (response.success && response.data) {
      loggers.value = response.data.loggers
    }
  } catch (error) {
    console.error('加载 logger 列表失败:', error)
  }
}

// 加载统计信息
const loadStats = async () => {
  if (!selectedFile.value) return
  
  try {
    const response = await apiGetLogStats(selectedFile.value)
    if (response.success && response.data) {
      stats.value = response.data
    }
  } catch (error) {
    console.error('加载统计信息失败:', error)
  }
}

// 搜索日志
const performSearch = async () => {
  if (!selectedFile.value) return
  
  loading.value = true
  try {
    const offset = (currentPage.value - 1) * pageSize.value
    
    const response = await apiSearchLogs({
      filename: selectedFile.value,
      query: searchQuery.value,
      level: filterLevel.value,
      logger_name: filterLogger.value,
      start_time: filterStartTime.value,
      end_time: filterEndTime.value,
      limit: pageSize.value,
      offset: offset,
      regex: useRegex.value
    })
    
    if (response.success && response.data) {
      logEntries.value = response.data.entries
      totalEntries.value = response.data.total
    } else {
      console.error('搜索日志失败')
    }
  } catch (error) {
    console.error('搜索日志失败:', error)
  } finally {
    loading.value = false
  }
}

// 触发搜索
const searchLogs = () => {
  currentPage.value = 1
  performSearch()
}

// 清除筛选
const clearFilters = () => {
  searchQuery.value = ''
  filterLevel.value = ''
  filterLogger.value = ''
  filterStartTime.value = ''
  filterEndTime.value = ''
  useRegex.value = false
  currentPage.value = 1
  performSearch()
}

// 分页控制
const goToPage = (page: number) => {
  if (page < 1 || page > totalPages.value) return
  currentPage.value = page
  performSearch()
}

const changePageSize = () => {
  currentPage.value = 1
  performSearch()
}

// 格式化时间戳
const formatTimestamp = (timestamp: string) => {
  if (!timestamp) return ''
  return timestamp.replace('T', ' ').substring(0, 19)
}

// 初始化
onMounted(() => {
  loadLogFiles()
})
</script>

<style scoped>
.log-viewer {
  height: 100%;
  display: flex;
  flex-direction: column;
  background: var(--bg-secondary);
}

/* 页面标题 */
.page-header {
  background: transparent;
  border-bottom: none;
  padding: 24px 32px;
}

.header-content {
  max-width: 1400px;
  margin: 0 auto;
}

.title-group {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 8px;
}

.title-icon {
  font-size: 28px;
  color: var(--primary);
}

.page-title {
  font-size: 24px;
  font-weight: 700;
  color: var(--text-primary);
  margin: 0;
}

.page-description {
  font-size: 14px;
  color: var(--text-secondary);
  margin: 0;
}

/* 主内容区 */
.content-wrapper {
  flex: 1;
  overflow: hidden;
  padding: 24px 32px;
  display: flex;
  flex-direction: column;
}

.log-container {
  max-width: 1400px;
  margin: 0 auto;
  flex: 1;
  display: grid;
  grid-template-columns: 280px 1fr;
  gap: 24px;
  min-height: 0;
  overflow: hidden;
}

/* 文件列表面板 */
.file-list-panel {
  background: var(--bg-primary);
  border-radius: var(--radius-lg);
  border: 1px solid var(--border-color);
  display: flex;
  flex-direction: column;
  overflow: hidden;
  height: 100%;
  max-height: calc(100vh - 180px);
}

.panel-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px;
  border-bottom: 1px solid var(--border-color);
}

.panel-title {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0;
}

.refresh-button {
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: transparent;
  border: 1px solid var(--border-color);
  border-radius: var(--radius);
  color: var(--text-secondary);
  cursor: pointer;
  transition: all var(--transition);
}

.refresh-button:hover:not(:disabled) {
  background: var(--bg-hover);
  color: var(--primary);
  border-color: var(--primary);
}

.refresh-button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.file-list {
  flex: 1;
  overflow-y: auto;
  overflow-x: hidden;
  padding: 8px;
  min-height: 0;
}

.file-list::-webkit-scrollbar {
  width: 6px;
}

.file-list::-webkit-scrollbar-track {
  background: transparent;
}

.file-list::-webkit-scrollbar-thumb {
  background: var(--border-color);
  border-radius: 3px;
}

.file-list::-webkit-scrollbar-thumb:hover {
  background: var(--text-tertiary);
}

.file-item {
  padding: 12px;
  border-radius: var(--radius);
  cursor: pointer;
  transition: all var(--transition);
  margin-bottom: 4px;
}

.file-item:hover {
  background: var(--bg-hover);
}

.file-item.active {
  background: var(--primary-bg);
  border-left: 3px solid var(--primary);
}

.file-info {
  display: flex;
  align-items: flex-start;
  gap: 12px;
}

.file-icon {
  font-size: 20px;
  color: var(--text-secondary);
  flex-shrink: 0;
}

.file-item.active .file-icon {
  color: var(--primary);
}

.file-details {
  flex: 1;
  min-width: 0;
}

.file-name {
  font-size: 13px;
  font-weight: 500;
  color: var(--text-primary);
  word-break: break-all;
  margin-bottom: 4px;
}

.file-meta {
  font-size: 11px;
  color: var(--text-tertiary);
  display: flex;
  flex-direction: column;
  gap: 2px;
}

/* 日志内容面板 */
.log-content-panel {
  background: var(--bg-primary);
  border-radius: var(--radius-lg);
  border: 1px solid var(--border-color);
  display: flex;
  flex-direction: column;
  overflow: hidden;
  height: 100%;
  max-height: calc(100vh - 180px);
}

/* 工具栏 */
.toolbar {
  padding: 16px;
  border-bottom: 1px solid var(--border-color);
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
}

.search-group {
  display: flex;
  gap: 8px;
  flex: 1;
  min-width: 300px;
}

.search-input-wrapper {
  flex: 1;
  position: relative;
}

.search-icon {
  position: absolute;
  left: 12px;
  top: 50%;
  transform: translateY(-50%);
  font-size: 18px;
  color: var(--text-tertiary);
  pointer-events: none;
}

.search-input {
  width: 100%;
  padding: 10px 12px 10px 40px;
  border: 1px solid var(--border-color);
  border-radius: var(--radius);
  background: var(--bg-secondary);
  color: var(--text-primary);
  font-size: 14px;
  transition: all var(--transition);
}

.search-input:focus {
  outline: none;
  border-color: var(--primary);
  background: var(--bg-primary);
}

.search-button {
  padding: 10px 24px;
  background: var(--primary);
  color: white;
  border: none;
  border-radius: var(--radius);
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all var(--transition);
}

.search-button:hover:not(:disabled) {
  background: var(--primary-dark);
}

.search-button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.filter-group {
  display: flex;
  gap: 8px;
  align-items: center;
}

.filter-select {
  padding: 10px 12px;
  border: 1px solid var(--border-color);
  border-radius: var(--radius);
  background: var(--bg-secondary);
  color: var(--text-primary);
  font-size: 14px;
  cursor: pointer;
  transition: all var(--transition);
}

.filter-select:focus {
  outline: none;
  border-color: var(--primary);
}

.icon-button {
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--bg-secondary);
  border: 1px solid var(--border-color);
  border-radius: var(--radius);
  color: var(--text-secondary);
  cursor: pointer;
  transition: all var(--transition);
}

.icon-button:hover {
  background: var(--bg-hover);
  color: var(--primary);
  border-color: var(--primary);
}

/* 高级筛选 */
.advanced-filter {
  padding: 16px;
  border-bottom: 1px solid var(--border-color);
  background: var(--bg-secondary);
  display: flex;
  gap: 16px;
  flex-wrap: wrap;
}

.filter-row {
  display: flex;
  align-items: center;
  gap: 8px;
}

.filter-label {
  font-size: 13px;
  color: var(--text-secondary);
  white-space: nowrap;
}

.filter-input {
  padding: 8px 12px;
  border: 1px solid var(--border-color);
  border-radius: var(--radius);
  background: var(--bg-primary);
  color: var(--text-primary);
  font-size: 13px;
}

/* 统计栏 */
.stats-bar {
  padding: 12px 16px;
  border-bottom: 1px solid var(--border-color);
  background: var(--bg-secondary);
  display: flex;
  gap: 24px;
  flex-wrap: wrap;
}

.stat-item {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
}

.stat-label {
  color: var(--text-secondary);
}

.stat-value {
  font-weight: 600;
  color: var(--text-primary);
}

.stat-value.level-debug { color: #8b8b8b; }
.stat-value.level-info { color: #3b82f6; }
.stat-value.level-warning { color: #f59e0b; }
.stat-value.level-error { color: #ef4444; }
.stat-value.level-critical { color: #dc2626; }

/* 日志条目列表 */
.log-entries {
  flex: 1;
  overflow-y: auto;
  overflow-x: hidden;
  padding: 16px;
  min-height: 0;
}

.log-entries::-webkit-scrollbar {
  width: 8px;
}

.log-entries::-webkit-scrollbar-track {
  background: var(--bg-secondary);
  border-radius: 4px;
}

.log-entries::-webkit-scrollbar-thumb {
  background: var(--border-color);
  border-radius: 4px;
}

.log-entries::-webkit-scrollbar-thumb:hover {
  background: var(--text-tertiary);
}

.entries-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.log-entry {
  padding: 12px;
  border-radius: var(--radius);
  border-left: 3px solid var(--border-color);
  background: var(--bg-secondary);
  transition: all var(--transition);
}

.log-entry:hover {
  background: var(--bg-hover);
}

.log-entry.level-debug { border-left-color: #8b8b8b; }
.log-entry.level-info { border-left-color: #3b82f6; }
.log-entry.level-warning { border-left-color: #f59e0b; }
.log-entry.level-error { border-left-color: #ef4444; }
.log-entry.level-critical { border-left-color: #dc2626; }

.entry-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 8px;
  font-size: 12px;
  flex-wrap: wrap;
}

.entry-time {
  color: var(--text-tertiary);
  font-family: 'Consolas', 'Monaco', monospace;
}

.entry-level {
  padding: 2px 8px;
  border-radius: var(--radius-sm);
  font-weight: 600;
  font-size: 11px;
}

.entry-level.level-debug { background: #8b8b8b; color: white; }
.entry-level.level-info { background: #3b82f6; color: white; }
.entry-level.level-warning { background: #f59e0b; color: white; }
.entry-level.level-error { background: #ef4444; color: white; }
.entry-level.level-critical { background: #dc2626; color: white; }

.entry-logger {
  font-weight: 600;
}

.entry-line {
  color: var(--text-tertiary);
  margin-left: auto;
}

.entry-message {
  color: var(--text-primary);
  font-size: 14px;
  line-height: 1.6;
  word-break: break-word;
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
  padding: 8px;
  background: var(--bg-primary);
  border-radius: var(--radius-sm);
  overflow-x: auto;
  font-family: 'Consolas', 'Monaco', monospace;
  font-size: 11px;
  color: var(--text-secondary);
}

/* 分页 */
.pagination {
  padding: 16px;
  border-top: 1px solid var(--border-color);
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
}

.pagination-button {
  width: 36px;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--bg-secondary);
  border: 1px solid var(--border-color);
  border-radius: var(--radius);
  color: var(--text-secondary);
  cursor: pointer;
  transition: all var(--transition);
}

.pagination-button:hover:not(:disabled) {
  background: var(--bg-hover);
  color: var(--primary);
  border-color: var(--primary);
}

.pagination-button:disabled {
  opacity: 0.3;
  cursor: not-allowed;
}

.pagination-info {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 0 16px;
  font-size: 14px;
  color: var(--text-secondary);
}

.separator {
  color: var(--border-color);
}

.page-size-select {
  padding: 8px 12px;
  border: 1px solid var(--border-color);
  border-radius: var(--radius);
  background: var(--bg-secondary);
  color: var(--text-primary);
  font-size: 13px;
  cursor: pointer;
}

/* 空状态 */
.empty-state,
.loading-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px 20px;
  color: var(--text-tertiary);
}

.empty-icon,
.loading-icon {
  font-size: 48px;
  margin-bottom: 12px;
  opacity: 0.5;
}

.empty-state p,
.loading-state p {
  font-size: 14px;
  margin: 0;
}

/* 动画 */
.spinning {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.slide-down-enter-active,
.slide-down-leave-active {
  transition: all 0.3s ease;
  overflow: hidden;
}

.slide-down-enter-from,
.slide-down-leave-to {
  max-height: 0;
  opacity: 0;
}

.slide-down-enter-to,
.slide-down-leave-from {
  max-height: 200px;
  opacity: 1;
}

/* 响应式 */
@media (max-width: 1024px) {
  .log-container {
    grid-template-columns: 1fr;
    grid-template-rows: 300px 1fr;
  }

  .file-list-panel {
    max-height: 300px;
    height: 300px;
  }
  
  .log-content-panel {
    max-height: calc(100vh - 540px);
  }
}

@media (max-width: 768px) {
  .content-wrapper {
    padding: 16px;
  }
  
  .log-container {
    gap: 16px;
  }
  
  .toolbar {
    flex-direction: column;
  }
  
  .search-group {
    width: 100%;
    min-width: auto;
  }
  
  .filter-group {
    width: 100%;
    flex-wrap: wrap;
  }
}
</style>
