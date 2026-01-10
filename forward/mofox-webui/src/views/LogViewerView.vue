<!--
  @file LogViewerView.vue
  @description 历史日志查看器页面
  
  功能说明：
  1. 查看历史日志文件列表
  2. 搜索和筛选日志内容
  3. 按日志级别筛选
  4. 按模块（logger）筛选
  5. 高级筛选（时间范围等）
  
  布局结构：
  - 左侧：日志文件列表（名称、大小、修改时间）
  - 右侧：日志内容显示和工具栏
  
  工具栏功能：
  - 关键词搜索
  - 级别筛选（debug/info/warning/error/critical）
  - 模块筛选
  - 高级筛选（时间范围、行数限制）
-->
<template>
  <div class="log-viewer-view">
    <!-- 页面标题：图标、标题、说明 -->
    <header class="page-header">
      <div class="header-content">
        <div class="title-group">
          <div class="header-icon-container">
            <span class="material-symbols-rounded header-icon">description</span>
          </div>
          <div class="header-text">
            <h1 class="page-title">日志查看器</h1>
            <p class="page-description">查看、搜索和分析系统日志</p>
          </div>
        </div>
      </div>
    </header>

    <!-- 主内容区 -->
    <div class="content-wrapper">
      <div class="log-container">
        <!-- 左侧：日志文件列表 -->
        <div class="m3-card file-list-panel">
          <div class="panel-header">
            <h3 class="panel-title">日志文件</h3>
            <button class="m3-icon-button" @click="loadLogFiles" :disabled="loading" title="刷新列表">
              <span class="material-symbols-rounded" :class="{ spinning: loading }">refresh</span>
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
              <span class="material-symbols-rounded file-icon">
                {{ file.compressed ? 'folder_zip' : 'text_snippet' }}
              </span>
              <div class="file-details">
                <div class="file-name">{{ file.name }}</div>
                <div class="file-meta">
                  <span>{{ file.size_human }}</span>
                  <span>{{ file.mtime_human }}</span>
                </div>
              </div>
            </div>
            
            <div v-if="logFiles.length === 0 && !loading" class="empty-state small">
              <span class="material-symbols-rounded empty-icon">inbox</span>
              <p>暂无日志文件</p>
            </div>
          </div>
        </div>

        <!-- 右侧：日志内容 -->
        <div class="m3-card log-content-panel">
          <!-- 搜索和筛选工具栏 -->
          <div class="toolbar">
            <div class="search-group">
              <div class="search-input-wrapper">
                <span class="material-symbols-rounded search-icon">search</span>
                <input 
                  v-model="searchQuery"
                  type="text"
                  placeholder="搜索日志内容..."
                  class="m3-input search-input"
                  @keyup.enter="searchLogs"
                />
              </div>
              <button 
                class="m3-button filled"
                @click="searchLogs"
                :disabled="!selectedFile || loading"
              >
                搜索
              </button>
            </div>

            <div class="filter-group">
              <!-- Level Dropdown -->
              <div class="custom-select" :class="{ active: showLevelDropdown }">
                <div class="select-trigger" @click="showLevelDropdown = !showLevelDropdown; showLoggerDropdown = false">
                  <span>{{ filterLevel ? filterLevel.toUpperCase() : '所有级别' }}</span>
                  <span class="material-symbols-rounded select-arrow">arrow_drop_down</span>
                </div>
                <Transition name="scale-y">
                  <div v-if="showLevelDropdown" class="select-options m3-card">
                    <div 
                      class="select-option" 
                      :class="{ selected: filterLevel === '' }"
                      @click="filterLevel = ''; searchLogs(); showLevelDropdown = false"
                    >
                      所有级别
                    </div>
                    <div 
                      v-for="level in ['debug', 'info', 'warning', 'error', 'critical']"
                      :key="level"
                      class="select-option"
                      :class="{ selected: filterLevel === level }"
                      @click="filterLevel = level; searchLogs(); showLevelDropdown = false"
                    >
                      {{ level.toUpperCase() }}
                    </div>
                  </div>
                </Transition>
                <div v-if="showLevelDropdown" class="dropdown-overlay" @click="showLevelDropdown = false"></div>
              </div>

              <!-- Logger Dropdown -->
              <div class="custom-select" :class="{ active: showLoggerDropdown }">
                <div class="select-trigger" @click="showLoggerDropdown = !showLoggerDropdown; showLevelDropdown = false">
                  <span>{{ filterLogger ? (loggers.find(l => l.name === filterLogger)?.alias || filterLogger) : '所有模块' }}</span>
                  <span class="material-symbols-rounded select-arrow">arrow_drop_down</span>
                </div>
                <Transition name="scale-y">
                  <div v-if="showLoggerDropdown" class="select-options m3-card">
                    <div 
                      class="select-option" 
                      :class="{ selected: filterLogger === '' }"
                      @click="filterLogger = ''; searchLogs(); showLoggerDropdown = false"
                    >
                      所有模块
                    </div>
                    <div 
                      v-for="logger in loggers" 
                      :key="logger.name"
                      class="select-option"
                      :class="{ selected: filterLogger === logger.name }"
                      @click="filterLogger = logger.name; searchLogs(); showLoggerDropdown = false"
                    >
                      {{ logger.alias || logger.name }}
                    </div>
                  </div>
                </Transition>
                <div v-if="showLoggerDropdown" class="dropdown-overlay" @click="showLoggerDropdown = false"></div>
              </div>

              <button 
                class="m3-icon-button" 
                :class="{ active: showAdvancedFilter }"
                @click="showAdvancedFilter = !showAdvancedFilter" 
                title="高级筛选"
              >
                <span class="material-symbols-rounded">filter_list</span>
              </button>

              <button class="m3-icon-button" @click="clearFilters" title="清除筛选">
                <span class="material-symbols-rounded">close</span>
              </button>
            </div>
          </div>

          <!-- 高级筛选面板 -->
          <Transition name="slide-down">
            <div v-if="showAdvancedFilter" class="advanced-filter">
              <div class="filter-row">
                <label class="filter-label">开始时间</label>
                <input v-model="filterStartTime" type="datetime-local" class="m3-input filter-input" />
              </div>
              <div class="filter-row">
                <label class="filter-label">结束时间</label>
                <input v-model="filterEndTime" type="datetime-local" class="m3-input filter-input" />
              </div>
              <div class="filter-row checkbox-row">
                <label class="m3-checkbox-label">
                  <input v-model="useRegex" type="checkbox" class="m3-checkbox" />
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
              <span class="stat-value" :class="'level-' + level.toLowerCase()">{{ count }}</span>
            </div>
          </div>

          <!-- 日志条目列表 -->
          <div class="log-entries" ref="logEntriesContainer">
            <div v-if="loading" class="loading-state">
              <span class="material-symbols-rounded spinning loading-icon">progress_activity</span>
              <p>加载中...</p>
            </div>

            <!-- 文件日志模式 -->
            <div v-else-if="!selectedFile" class="empty-state">
              <span class="material-symbols-rounded empty-icon">find_in_page</span>
              <p>请选择一个日志文件或启用实时日志</p>
            </div>

            <div v-else-if="logEntries.length === 0" class="empty-state">
              <span class="material-symbols-rounded empty-icon">inbox</span>
              <p>没有找到日志条目</p>
            </div>

            <div v-else class="entries-list">
              <div 
                v-for="entry in logEntries" 
                :key="entry.file_name + '-' + entry.line_number"
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
              class="m3-icon-button small"
              :disabled="currentPage === 1"
              @click="goToPage(1)"
              title="第一页"
            >
              <span class="material-symbols-rounded">first_page</span>
            </button>
            <button 
              class="m3-icon-button small"
              :disabled="currentPage === 1"
              @click="goToPage(currentPage - 1)"
              title="上一页"
            >
              <span class="material-symbols-rounded">chevron_left</span>
            </button>
            
            <div class="pagination-info">
              <span>第 {{ currentPage }} / {{ totalPages }} 页</span>
              <span class="separator">|</span>
              <span>共 {{ totalEntries }} 条</span>
            </div>

            <button 
              class="m3-icon-button small"
              :disabled="currentPage === totalPages"
              @click="goToPage(currentPage + 1)"
              title="下一页"
            >
              <span class="material-symbols-rounded">chevron_right</span>
            </button>
            <button 
              class="m3-icon-button small"
              :disabled="currentPage === totalPages"
              @click="goToPage(totalPages)"
              title="最后一页"
            >
              <span class="material-symbols-rounded">last_page</span>
            </button>

            <div class="custom-select small" :class="{ active: showPageSizeDropdown }">
              <div class="select-trigger" @click="showPageSizeDropdown = !showPageSizeDropdown">
                <span>{{ pageSize }} 条/页</span>
                <span class="material-symbols-rounded select-arrow">arrow_drop_down</span>
              </div>
              <Transition name="scale-y">
                <div v-if="showPageSizeDropdown" class="select-options m3-card up">
                  <div 
                    v-for="size in [50, 100, 200, 500]"
                    :key="size"
                    class="select-option"
                    :class="{ selected: pageSize === size }"
                    @click="pageSize = size; changePageSize(); showPageSizeDropdown = false"
                  >
                    {{ size }} 条/页
                  </div>
                </div>
              </Transition>
              <div v-if="showPageSizeDropdown" class="dropdown-overlay" @click="showPageSizeDropdown = false"></div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
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
const showLevelDropdown = ref(false)
const showLoggerDropdown = ref(false)
const showPageSizeDropdown = ref(false)

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
.log-viewer-view {
  height: 100%;
  display: flex;
  flex-direction: column;
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
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.title-group {
  display: flex;
  align-items: center;
  gap: 16px;
}

.header-icon-container {
  width: 48px;
  height: 48px;
  border-radius: 16px;
  background: var(--md-sys-color-secondary-container);
  color: var(--md-sys-color-on-secondary-container);
  display: flex;
  align-items: center;
  justify-content: center;
}

.header-icon {
  font-size: 24px;
}

.page-title {
  font-size: 22px;
  font-weight: 400;
  color: var(--md-sys-color-on-surface);
  margin: 0 0 4px;
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
  display: flex;
  flex-direction: column;
}

.log-container {
  flex: 1;
  display: grid;
  grid-template-columns: 280px 1fr;
  gap: 16px;
  min-height: 0;
  overflow: hidden;
}

/* 文件列表面板 */
.file-list-panel {
  display: flex;
  flex-direction: column;
  overflow: hidden;
  height: 100%;
  padding: 0;
  background: var(--md-sys-color-surface-container);
  border-radius: 32px;
  border: none;
  box-shadow: none;
}

.panel-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px;
  border-bottom: 1px solid var(--md-sys-color-outline-variant);
}

.panel-title {
  font-size: 16px;
  font-weight: 500;
  color: var(--md-sys-color-on-surface);
  margin: 0;
}

.file-list {
  flex: 1;
  overflow-y: auto;
  padding: 8px;
}

.file-item {
  padding: 12px;
  border-radius: 12px;
  cursor: pointer;
  transition: all 0.2s;
  margin-bottom: 4px;
  display: flex;
  align-items: flex-start;
  gap: 12px;
}

.file-item:hover {
  background: var(--md-sys-color-surface-container-highest);
}

.file-item.active {
  background: var(--md-sys-color-secondary-container);
  color: var(--md-sys-color-on-secondary-container);
}

.file-icon {
  font-size: 20px;
  color: var(--md-sys-color-on-surface-variant);
}

.file-item.active .file-icon {
  color: var(--md-sys-color-on-secondary-container);
}

.file-details {
  flex: 1;
  min-width: 0;
}

.file-name {
  font-size: 14px;
  font-weight: 500;
  margin-bottom: 4px;
  word-break: break-all;
}

.file-meta {
  font-size: 11px;
  opacity: 0.7;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

/* 日志内容面板 */
.log-content-panel {
  display: flex;
  flex-direction: column;
  overflow: hidden;
  height: 100%;
  padding: 0;
  background: var(--md-sys-color-surface-container);
  border-radius: 32px;
  border: none;
  box-shadow: none;
}

/* 工具栏 */
.toolbar {
  padding: 16px;
  border-bottom: 1px solid var(--md-sys-color-outline-variant);
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
  background: var(--md-sys-color-surface-container-low);
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
  height: 40px;
  background: var(--md-sys-color-surface-container-high);
  border-radius: 20px;
  display: flex;
  align-items: center;
  transition: all 0.2s;
}

.search-input-wrapper:hover {
  background: var(--md-sys-color-surface-container-highest);
}

.search-input-wrapper:focus-within {
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

.search-input {
  width: 100%;
  height: 100%;
  background: transparent;
  border: none;
  padding: 0 16px 0 44px;
  font-size: 14px;
  color: var(--md-sys-color-on-surface);
  outline: none;
  border-radius: 20px;
  font-family: inherit;
}

.search-input::placeholder {
  color: var(--md-sys-color-on-surface-variant);
}

.filter-group {
  display: flex;
  gap: 8px;
  align-items: center;
}

/* Custom Dropdown */
.custom-select {
  position: relative;
  height: 40px;
  min-width: 120px;
}

.select-trigger {
  height: 100%;
  background: var(--md-sys-color-surface-container-high);
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 12px;
  cursor: pointer;
  transition: all 0.2s;
  user-select: none;
  gap: 8px;
}

.select-trigger:hover {
  background: var(--md-sys-color-surface-container-highest);
}

.custom-select.active .select-trigger {
  background: var(--md-sys-color-secondary-container);
  color: var(--md-sys-color-on-secondary-container);
}

.select-trigger span:first-child {
  font-size: 14px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.select-arrow {
  font-size: 20px;
  color: var(--md-sys-color-on-surface-variant);
  transition: transform 0.2s;
}

.custom-select.active .select-arrow {
  transform: rotate(180deg);
  color: var(--md-sys-color-on-secondary-container);
}

.select-options {
  position: absolute;
  top: calc(100% + 4px);
  left: 0;
  min-width: 100%;
  max-height: 300px;
  overflow-y: auto;
  background: var(--md-sys-color-surface-container-high);
  border-radius: 8px;
  padding: 4px;
  z-index: 1000;
  box-shadow: var(--md-sys-elevation-2);
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.select-option {
  padding: 8px 12px;
  font-size: 14px;
  color: var(--md-sys-color-on-surface);
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.2s;
  white-space: nowrap;
}

.select-option:hover {
  background: var(--md-sys-color-surface-container-highest);
}

.select-option.selected {
  background: var(--md-sys-color-secondary-container);
  color: var(--md-sys-color-on-secondary-container);
  font-weight: 500;
}

.dropdown-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  z-index: 999;
  background: transparent;
}

/* Transitions */
.scale-y-enter-active,
.scale-y-leave-active {
  transition: all 0.2s cubic-bezier(0.2, 0, 0, 1);
  transform-origin: top;
}

.scale-y-enter-from,
.scale-y-leave-to {
  opacity: 0;
  transform: scaleY(0.8);
}

.custom-select.small {
  height: 32px;
  min-width: 110px;
}

.custom-select.small .select-trigger {
  font-size: 12px;
  padding: 0 8px;
}

.custom-select.small .select-arrow {
  font-size: 18px;
}

.select-options.up {
  top: auto;
  bottom: calc(100% + 4px);
  transform-origin: bottom;
}

/* 高级筛选 */
.advanced-filter {
  padding: 16px;
  border-bottom: 1px solid var(--md-sys-color-outline-variant);
  background: var(--md-sys-color-surface-container);
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
  color: var(--md-sys-color-on-surface-variant);
  white-space: nowrap;
}

.filter-input {
  padding: 8px 12px;
  font-size: 13px;
}

.checkbox-row {
  margin-left: auto;
}

.m3-checkbox-label {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  color: var(--md-sys-color-on-surface);
  cursor: pointer;
}

.m3-checkbox {
  width: 18px;
  height: 18px;
  accent-color: var(--md-sys-color-primary);
}

/* 统计栏 */
.stats-bar {
  padding: 12px 16px;
  border-bottom: 1px solid var(--md-sys-color-outline-variant);
  background: var(--md-sys-color-surface-container-low);
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
  color: var(--md-sys-color-on-surface-variant);
}

.stat-value {
  font-weight: 600;
  color: var(--md-sys-color-on-surface);
}

/* 日志条目列表 */
.log-entries {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
  background: var(--md-sys-color-surface);
}

.entries-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.log-entry {
  padding: 12px;
  border-radius: 8px;
  border-left: 4px solid var(--md-sys-color-outline);
  background: var(--md-sys-color-surface-container-lowest);
  transition: all 0.2s;
  font-family: 'JetBrains Mono', 'Fira Code', Consolas, monospace;
}

.log-entry:hover {
  background: var(--md-sys-color-surface-container-low);
}

/* 日志级别颜色 */
.log-entry.level-debug { border-left-color: #909090; }
.log-entry.level-info { border-left-color: #2196F3; }
.log-entry.level-warning { border-left-color: #FFC107; }
.log-entry.level-error { border-left-color: #F44336; }
.log-entry.level-critical { border-left-color: #D32F2F; }

.entry-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 8px;
  font-size: 12px;
  flex-wrap: wrap;
}

.entry-time {
  color: var(--md-sys-color-on-surface-variant);
}

.entry-level {
  padding: 2px 8px;
  border-radius: 4px;
  font-weight: 600;
  font-size: 11px;
  color: white;
}

.entry-level.level-debug { background: #909090; }
.entry-level.level-info { background: #2196F3; }
.entry-level.level-warning { background: #FFC107; color: black; }
.entry-level.level-error { background: #F44336; }
.entry-level.level-critical { background: #D32F2F; }

.entry-logger {
  font-weight: 600;
  font-family: 'Roboto Mono', monospace;

}

.entry-line {
  color: var(--md-sys-color-on-surface-variant);
  margin-left: auto;
}

.entry-message {
  color: var(--md-sys-color-on-surface);
  font-size: 13px;
  line-height: 1.6;
  word-break: break-word;
  white-space: pre-wrap;
  font-family: 'Roboto Mono', monospace;
}

.entry-extra {
  margin-top: 8px;
  font-size: 12px;
}

.entry-extra summary {
  color: var(--md-sys-color-primary);
  cursor: pointer;
  user-select: none;
}

.entry-extra pre {
  margin-top: 8px;
  padding: 12px;
  background: var(--md-sys-color-surface-container-high);
  border-radius: 8px;
  overflow-x: auto;
  color: var(--md-sys-color-on-surface-variant);
}

/* 分页 */
.pagination {
  padding: 12px 16px;
  border-top: 1px solid var(--md-sys-color-outline-variant);
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  background: var(--md-sys-color-surface-container-low);
}

.pagination-info {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 0 16px;
  font-size: 13px;
  color: var(--md-sys-color-on-surface-variant);
}

.separator {
  color: var(--md-sys-color-outline);
}

.select-wrapper.small .filter-select {
  padding: 6px 28px 6px 12px;
  font-size: 12px;
}

/* 空状态 */
.empty-state,
.loading-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px 20px;
  color: var(--md-sys-color-on-surface-variant);
  height: 100%;
}

.empty-state.small {
  padding: 32px 16px;
}

.empty-icon,
.loading-icon {
  font-size: 48px;
  margin-bottom: 12px;
  opacity: 0.5;
}

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
}

@media (max-width: 768px) {
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
  
  .select-wrapper {
    flex: 1;
  }
  
  .filter-select {
    width: 100%;
  }
}
</style>
