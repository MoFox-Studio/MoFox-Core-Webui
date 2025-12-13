<template>
  <div class="dashboard-home">
    <!-- 连接错误弹窗 -->
    <ConnectionError 
      :visible="showConnectionError"
      :message="connectionErrorMsg"
      @close="showConnectionError = false"
      @retry="fetchAllData"
    />

    <!-- 统计卡片 -->
    <section class="stats-section">
      <div class="stats-grid">
        <div class="stat-card" v-for="stat in statsData" :key="stat.label">
          <div class="stat-icon" :style="{ background: stat.bgColor }">
            <Icon :icon="stat.icon" :style="{ color: stat.color }" />
          </div>
          <div class="stat-content">
            <span class="stat-value">{{ stat.value }}</span>
            <span class="stat-label">{{ stat.label }}</span>
          </div>
          <div v-if="stat.subValue" class="stat-sub">
            <span>{{ stat.subValue }}</span>
          </div>
        </div>
      </div>
    </section>

    <!-- 主要内容区 -->
    <section class="main-section">
      <div class="content-grid">
        <!-- 今日日程 -->
        <div class="card schedule-card">
          <div class="card-header">
            <h3 class="card-title">
              <Icon icon="lucide:calendar" />
              今日日程
            </h3>
            <span class="date-badge">{{ schedule?.date || '加载中...' }}</span>
          </div>
          <div class="card-body">
            <!-- 当前活动 -->
            <div v-if="schedule?.current_activity" class="current-activity">
              <div class="current-label">
                <Icon icon="lucide:play-circle" />
                当前活动
              </div>
              <div class="current-content">
                <span class="current-time">{{ schedule.current_activity.time_range }}</span>
                <span class="current-text">{{ schedule.current_activity.activity }}</span>
              </div>
            </div>
            
            <!-- 日程列表 -->
            <div v-if="schedule?.activities?.length" class="schedule-list">
              <div 
                class="schedule-item" 
                v-for="(item, index) in schedule.activities" 
                :key="index"
                :class="{ 'is-current': isCurrentActivity(item) }"
              >
                <div class="schedule-time">{{ item.time_range }}</div>
                <div class="schedule-activity">{{ item.activity }}</div>
              </div>
            </div>
            <div v-else class="empty-state small">
              <Icon icon="lucide:calendar-off" class="empty-icon" />
              <p>暂无日程安排</p>
            </div>
          </div>
        </div>

        <!-- 月度计划 -->
        <div class="card plans-card">
          <div class="card-header">
            <h3 class="card-title">
              <Icon icon="lucide:target" />
              月度计划
            </h3>
            <span class="total-badge" v-if="monthlyPlans">
              共 {{ monthlyPlans.total }} 项
            </span>
          </div>
          <div class="card-body plans-body">
            <div v-if="monthlyPlans?.plans?.length" class="plans-list">
              <div class="plan-item" v-for="(plan, index) in monthlyPlans.plans" :key="index">
                <Icon icon="lucide:check-square" class="plan-icon" />
                <span class="plan-text">{{ plan }}</span>
              </div>
            </div>
            <div v-else class="empty-state small">
              <Icon icon="lucide:clipboard-list" class="empty-icon" />
              <p>暂无月度计划</p>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- 插件和组件统计（合并为一行） -->
    <section class="combined-stats-section">
      <div class="combined-stats-grid">
        <!-- 插件统计卡片 -->
        <div class="mini-card" @click="showPluginDetail = true">
          <div class="mini-card-header">
            <Icon icon="lucide:puzzle" class="mini-card-icon" style="color: #3b82f6" />
            <span class="mini-card-title">插件统计</span>
          </div>
          <div class="mini-card-stats">
            <div class="mini-stat">
              <span class="mini-stat-value success">{{ overview?.plugins.enabled ?? 0 }}</span>
              <span class="mini-stat-label">启用</span>
            </div>
            <div class="mini-stat">
              <span class="mini-stat-value">{{ overview?.plugins.loaded ?? 0 }}</span>
              <span class="mini-stat-label">已加载</span>
            </div>
            <div class="mini-stat">
              <span class="mini-stat-value warning">{{ overview?.plugins.disabled ?? 0 }}</span>
              <span class="mini-stat-label">禁用</span>
            </div>
            <div class="mini-stat">
              <span class="mini-stat-value danger">{{ overview?.plugins.failed ?? 0 }}</span>
              <span class="mini-stat-label">失败</span>
            </div>
          </div>
        </div>

        <!-- 动作组件卡片 -->
        <div 
          class="mini-card component-card" 
          v-if="overview?.components.by_type?.['action']"
          @click="showComponentDetailModal('action')"
        >
          <div class="mini-card-header">
            <Icon icon="lucide:play" class="mini-card-icon" style="color: #10b981" />
            <span class="mini-card-title">动作</span>
          </div>
          <div class="mini-card-stats">
            <div class="mini-stat">
              <span class="mini-stat-value">{{ overview?.components.by_type?.['action']?.total ?? 0 }}</span>
              <span class="mini-stat-label">总数</span>
            </div>
            <div class="mini-stat">
              <span class="mini-stat-value success">{{ overview?.components.by_type?.['action']?.enabled ?? 0 }}</span>
              <span class="mini-stat-label">启用</span>
            </div>
            <div class="mini-stat">
              <span class="mini-stat-value warning">{{ overview?.components.by_type?.['action']?.disabled ?? 0 }}</span>
              <span class="mini-stat-label">禁用</span>
            </div>
          </div>
        </div>

        <!-- 扩展命令卡片 -->
        <div 
          class="mini-card component-card" 
          v-if="overview?.components.by_type?.['plus_command']"
          @click="showComponentDetailModal('plus_command')"
        >
          <div class="mini-card-header">
            <Icon icon="lucide:plus-square" class="mini-card-icon" style="color: #f59e0b" />
            <span class="mini-card-title">扩展命令</span>
          </div>
          <div class="mini-card-stats">
            <div class="mini-stat">
              <span class="mini-stat-value">{{ overview?.components.by_type?.['plus_command']?.total ?? 0 }}</span>
              <span class="mini-stat-label">总数</span>
            </div>
            <div class="mini-stat">
              <span class="mini-stat-value success">{{ overview?.components.by_type?.['plus_command']?.enabled ?? 0 }}</span>
              <span class="mini-stat-label">启用</span>
            </div>
            <div class="mini-stat">
              <span class="mini-stat-value warning">{{ overview?.components.by_type?.['plus_command']?.disabled ?? 0 }}</span>
              <span class="mini-stat-label">禁用</span>
            </div>
          </div>
        </div>

        <!-- 适配器卡片 -->
        <div 
          class="mini-card component-card" 
          v-if="overview?.components.by_type?.['adapter']"
          @click="showComponentDetailModal('adapter')"
        >
          <div class="mini-card-header">
            <Icon icon="lucide:plug" class="mini-card-icon" style="color: #8b5cf6" />
            <span class="mini-card-title">适配器</span>
          </div>
          <div class="mini-card-stats">
            <div class="mini-stat">
              <span class="mini-stat-value">{{ overview?.components.by_type?.['adapter']?.total ?? 0 }}</span>
              <span class="mini-stat-label">总数</span>
            </div>
            <div class="mini-stat">
              <span class="mini-stat-value success">{{ overview?.components.by_type?.['adapter']?.enabled ?? 0 }}</span>
              <span class="mini-stat-label">启用</span>
            </div>
            <div class="mini-stat">
              <span class="mini-stat-value warning">{{ overview?.components.by_type?.['adapter']?.disabled ?? 0 }}</span>
              <span class="mini-stat-label">禁用</span>
            </div>
          </div>
        </div>

        <!-- 工具卡片 -->
        <div 
          class="mini-card component-card" 
          v-if="overview?.components.by_type?.['tool']"
          @click="showComponentDetailModal('tool')"
        >
          <div class="mini-card-header">
            <Icon icon="lucide:wrench" class="mini-card-icon" style="color: #ec4899" />
            <span class="mini-card-title">工具</span>
          </div>
          <div class="mini-card-stats">
            <div class="mini-stat">
              <span class="mini-stat-value">{{ overview?.components.by_type?.['tool']?.total ?? 0 }}</span>
              <span class="mini-stat-label">总数</span>
            </div>
            <div class="mini-stat">
              <span class="mini-stat-value success">{{ overview?.components.by_type?.['tool']?.enabled ?? 0 }}</span>
              <span class="mini-stat-label">启用</span>
            </div>
            <div class="mini-stat">
              <span class="mini-stat-value warning">{{ overview?.components.by_type?.['tool']?.disabled ?? 0 }}</span>
              <span class="mini-stat-label">禁用</span>
            </div>
          </div>
        </div>

        <!-- 定时任务卡片 -->
        <div 
          class="mini-card component-card" 
          v-if="overview?.components.by_type?.['scheduled_task']"
          @click="showComponentDetailModal('scheduled_task')"
        >
          <div class="mini-card-header">
            <Icon icon="lucide:calendar-clock" class="mini-card-icon" style="color: #06b6d4" />
            <span class="mini-card-title">定时任务</span>
          </div>
          <div class="mini-card-stats">
            <div class="mini-stat">
              <span class="mini-stat-value">{{ overview?.components.by_type?.['scheduled_task']?.total ?? 0 }}</span>
              <span class="mini-stat-label">总数</span>
            </div>
            <div class="mini-stat">
              <span class="mini-stat-value success">{{ overview?.components.by_type?.['scheduled_task']?.enabled ?? 0 }}</span>
              <span class="mini-stat-label">启用</span>
            </div>
            <div class="mini-stat">
              <span class="mini-stat-value warning">{{ overview?.components.by_type?.['scheduled_task']?.disabled ?? 0 }}</span>
              <span class="mini-stat-label">禁用</span>
            </div>
          </div>
        </div>

        <!-- HTTP路由卡片 -->
        <div 
          class="mini-card component-card" 
          v-if="overview?.components.by_type?.['http_router']"
          @click="showComponentDetailModal('http_router')"
        >
          <div class="mini-card-header">
            <Icon icon="lucide:route" class="mini-card-icon" style="color: #14b8a6" />
            <span class="mini-card-title">HTTP路由</span>
          </div>
          <div class="mini-card-stats">
            <div class="mini-stat">
              <span class="mini-stat-value">{{ overview?.components.by_type?.['http_router']?.total ?? 0 }}</span>
              <span class="mini-stat-label">总数</span>
            </div>
            <div class="mini-stat">
              <span class="mini-stat-value success">{{ overview?.components.by_type?.['http_router']?.enabled ?? 0 }}</span>
              <span class="mini-stat-label">启用</span>
            </div>
            <div class="mini-stat">
              <span class="mini-stat-value warning">{{ overview?.components.by_type?.['http_router']?.disabled ?? 0 }}</span>
              <span class="mini-stat-label">禁用</span>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- 消息统计图表 -->
    <section class="chart-section">
      <div class="card">
        <div class="card-header">
          <h3 class="card-title">
            <Icon icon="lucide:bar-chart-2" />
            消息收发统计
          </h3>
          <div class="chart-controls">
            <select v-model="messageStatsPeriod" @change="fetchMessageStats" class="period-select">
              <option value="last_hour">最近1小时</option>
              <option value="last_24_hours">最近24小时</option>
              <option value="last_7_days">最近7天</option>
              <option value="last_30_days">最近30天</option>
            </select>
            <button class="refresh-btn" @click="fetchMessageStats" :disabled="chartLoading">
              <Icon :icon="chartLoading ? 'lucide:loader-2' : 'lucide:refresh-cw'" :class="{ spinning: chartLoading }" />
            </button>
          </div>
        </div>
        <div class="card-body chart-body">
          <div v-if="chartLoading" class="chart-loading">
            <Icon icon="lucide:loader-2" class="spinning" />
            <span>加载中...</span>
          </div>
          <div v-else-if="!messageStats?.data_points?.length" class="empty-state small">
            <Icon icon="lucide:line-chart" class="empty-icon" />
            <p>暂无消息数据</p>
          </div>
          <div v-else class="chart-container">
            <v-chart class="chart" :option="messageChartOption" autoresize />
          </div>
          <div class="chart-summary" v-if="messageStats">
            <div class="summary-item">
              <span class="summary-label">收到消息</span>
              <span class="summary-value received">{{ messageStats.total_received }}</span>
            </div>
            <div class="summary-item">
              <span class="summary-label">发送消息</span>
              <span class="summary-value sent">{{ messageStats.total_sent }}</span>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- 插件详情弹窗 -->
    <div v-if="showPluginDetail" class="modal-overlay" @click.self="showPluginDetail = false">
      <div class="modal-content modal-large">
        <div class="modal-header">
          <h3>插件详情</h3>
          <button class="close-btn" @click="showPluginDetail = false">
            <Icon icon="lucide:x" />
          </button>
        </div>
        <div class="modal-body">
          <div class="stats-detail-grid">
            <div class="stats-detail-item clickable" @click="showPluginListModal('loaded')">
              <div class="detail-icon" style="background: rgba(16, 185, 129, 0.1)">
                <Icon icon="lucide:check-circle" style="color: #10b981" />
              </div>
              <div class="detail-info">
                <span class="detail-value">{{ overview?.plugins.loaded ?? '-' }}</span>
                <span class="detail-label">已加载</span>
              </div>
              <Icon icon="lucide:chevron-right" class="detail-arrow" />
            </div>
            <div class="stats-detail-item clickable" @click="showPluginListModal('enabled')">
              <div class="detail-icon" style="background: rgba(59, 130, 246, 0.1)">
                <Icon icon="lucide:circle-dot" style="color: #3b82f6" />
              </div>
              <div class="detail-info">
                <span class="detail-value">{{ overview?.plugins.enabled ?? '-' }}</span>
                <span class="detail-label">已启用</span>
              </div>
              <Icon icon="lucide:chevron-right" class="detail-arrow" />
            </div>
            <div class="stats-detail-item clickable" @click="showPluginListModal('disabled')">
              <div class="detail-icon" style="background: rgba(245, 158, 11, 0.1)">
                <Icon icon="lucide:circle-pause" style="color: #f59e0b" />
              </div>
              <div class="detail-info">
                <span class="detail-value">{{ overview?.plugins.disabled ?? '-' }}</span>
                <span class="detail-label">已禁用</span>
              </div>
              <Icon icon="lucide:chevron-right" class="detail-arrow" />
            </div>
            <div class="stats-detail-item clickable" @click="showPluginListModal('failed')">
              <div class="detail-icon" style="background: rgba(239, 68, 68, 0.1)">
                <Icon icon="lucide:alert-circle" style="color: #ef4444" />
              </div>
              <div class="detail-info">
                <span class="detail-value">{{ overview?.plugins.failed ?? '-' }}</span>
                <span class="detail-label">加载失败</span>
              </div>
              <Icon icon="lucide:chevron-right" class="detail-arrow" />
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 插件列表弹窗 -->
    <div v-if="showPluginList" class="modal-overlay" @click.self="showPluginList = false">
      <div class="modal-content modal-large">
        <div class="modal-header">
          <h3>{{ pluginListTitle }}</h3>
          <button class="close-btn" @click="showPluginList = false">
            <Icon icon="lucide:x" />
          </button>
        </div>
        <div class="modal-body">
          <div v-if="pluginListLoading" class="loading-state">
            <Icon icon="lucide:loader-2" class="spinning" />
            <span>加载中...</span>
          </div>
          <div v-else-if="filteredPluginList.length === 0" class="empty-state small">
            <Icon icon="lucide:inbox" class="empty-icon" />
            <p>暂无插件</p>
          </div>
          <div v-else class="plugin-list">
            <div class="plugin-item" v-for="plugin in filteredPluginList" :key="plugin.name">
              <div class="plugin-item-header">
                <Icon 
                  :icon="plugin.enabled ? 'lucide:check-circle' : (plugin.error ? 'lucide:alert-circle' : 'lucide:circle-pause')" 
                  :style="{ color: plugin.enabled ? '#10b981' : (plugin.error ? '#ef4444' : '#f59e0b') }"
                />
                <span class="plugin-name">{{ plugin.display_name }}</span>
                <span class="plugin-version">v{{ plugin.version }}</span>
              </div>
              <div class="plugin-item-info">
                <span class="plugin-author">作者: {{ plugin.author }}</span>
                <span class="plugin-components">组件: {{ plugin.components_count }}</span>
              </div>
              <div v-if="plugin.error" class="plugin-error">
                <Icon icon="lucide:alert-triangle" />
                <span>{{ plugin.error }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 组件详情弹窗 -->
    <div v-if="showComponentDetail" class="modal-overlay" @click.self="showComponentDetail = false">
      <div class="modal-content modal-large">
        <div class="modal-header">
          <h3>
            <Icon :icon="getComponentTypeIcon(currentComponentType)" style="margin-right: 8px" />
            {{ formatComponentType(currentComponentType) }}组件列表
          </h3>
          <button class="close-btn" @click="showComponentDetail = false">
            <Icon icon="lucide:x" />
          </button>
        </div>
        <div class="modal-body">
          <div v-if="componentListLoading" class="loading-state">
            <Icon icon="lucide:loader-2" class="spinning" />
            <span>加载中...</span>
          </div>
          <div v-else-if="componentList.length === 0" class="empty-state small">
            <Icon icon="lucide:inbox" class="empty-icon" />
            <p>暂无组件</p>
          </div>
          <div v-else class="component-list">
            <div class="component-item" v-for="comp in componentList" :key="comp.name">
              <div class="component-item-header">
                <Icon 
                  :icon="comp.enabled ? 'lucide:check-circle' : 'lucide:circle-pause'" 
                  :style="{ color: comp.enabled ? '#10b981' : '#f59e0b' }"
                />
                <span class="component-name">{{ comp.name }}</span>
                <span :class="['component-status', comp.enabled ? 'enabled' : 'disabled']">
                  {{ comp.enabled ? '启用' : '禁用' }}
                </span>
              </div>
              <div class="component-item-desc" v-if="comp.description">
                {{ comp.description }}
              </div>
              <div class="component-item-plugin">
                <Icon icon="lucide:puzzle" />
                <span>来自插件: {{ comp.plugin_name }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { Icon } from '@iconify/vue'
import VChart from 'vue-echarts'
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { LineChart } from 'echarts/charts'
import { GridComponent, TooltipComponent, LegendComponent } from 'echarts/components'
import { 
  getDashboardOverview, 
  getTodaySchedule, 
  getMonthlyPlans,
  getLLMStats,
  getMessageStats,
  getPluginsByStatus,
  getComponentsByType,
  type DashboardOverview,
  type ScheduleResponse,
  type MonthlyPlanResponse,
  type ScheduleActivity,
  type LLMStatsResponse,
  type MessageStatsResponse,
  type PluginListItem,
  type ComponentItem
} from '@/api'
import ConnectionError from '@/components/ConnectionError.vue'

// 注册 ECharts 组件
use([CanvasRenderer, LineChart, GridComponent, TooltipComponent, LegendComponent])

const loading = ref(false)
const chartLoading = ref(false)
const overview = ref<DashboardOverview | null>(null)
const schedule = ref<ScheduleResponse | null>(null)
const monthlyPlans = ref<MonthlyPlanResponse | null>(null)
const llmStats = ref<LLMStatsResponse | null>(null)
const messageStats = ref<MessageStatsResponse | null>(null)
const messageStatsPeriod = ref<'last_hour' | 'last_24_hours' | 'last_7_days' | 'last_30_days'>('last_24_hours')

// 弹窗状态
const showPluginDetail = ref(false)
const showPluginList = ref(false)
const showComponentDetail = ref(false)

// 插件列表相关
const pluginListLoading = ref(false)
const pluginListType = ref<'loaded' | 'enabled' | 'disabled' | 'failed'>('loaded')
const pluginListData = ref<{ loaded: PluginListItem[], failed: PluginListItem[] }>({ loaded: [], failed: [] })

// 组件列表相关
const componentListLoading = ref(false)
const currentComponentType = ref('')
const componentList = ref<ComponentItem[]>([])

// 连接错误状态
const showConnectionError = ref(false)
const connectionErrorMsg = ref('')

// 获取所有数据
async function fetchAllData() {
  loading.value = true
  showConnectionError.value = false
  
  try {
    // 并行获取所有数据
    const [overviewRes, scheduleRes, plansRes, llmRes] = await Promise.all([
      getDashboardOverview(),
      getTodaySchedule(),
      getMonthlyPlans(),
      getLLMStats('last_24_hours')
    ])
    
    // 检查是否全部失败（连接问题）
    if (!overviewRes.success && overviewRes.status === 0) {
      connectionErrorMsg.value = overviewRes.error || '无法连接到后端服务'
      showConnectionError.value = true
      return
    }
    
    if (overviewRes.success && overviewRes.data) {
      overview.value = overviewRes.data
    }
    
    if (scheduleRes.success && scheduleRes.data) {
      schedule.value = scheduleRes.data
    }
    
    if (plansRes.success && plansRes.data) {
      monthlyPlans.value = plansRes.data
    }
    
    if (llmRes.success && llmRes.data) {
      llmStats.value = llmRes.data
    }
    
    // 获取消息统计
    await fetchMessageStats()
  } catch (error) {
    console.error('获取数据失败:', error)
    connectionErrorMsg.value = '请求发生错误，请检查网络连接'
    showConnectionError.value = true
  } finally {
    loading.value = false
  }
}

// 获取消息统计
async function fetchMessageStats() {
  chartLoading.value = true
  try {
    const res = await getMessageStats(messageStatsPeriod.value)
    if (res.success && res.data) {
      messageStats.value = res.data
    }
  } catch (error) {
    console.error('获取消息统计失败:', error)
  } finally {
    chartLoading.value = false
  }
}

// 判断是否为当前活动
function isCurrentActivity(item: ScheduleActivity): boolean {
  if (!schedule.value?.current_activity) return false
  return item.time_range === schedule.value.current_activity.time_range
}

// 格式化运行时间
function formatUptime(seconds: number): string {
  if (!seconds) return '-'
  const days = Math.floor(seconds / 86400)
  const hours = Math.floor((seconds % 86400) / 3600)
  const minutes = Math.floor((seconds % 3600) / 60)
  
  if (days > 0) return `${days}天${hours}时`
  if (hours > 0) return `${hours}时${minutes}分`
  return `${minutes}分钟`
}

// 格式化内存
function formatMemory(mb: number): string {
  if (!mb) return '-'
  if (mb >= 1024) return `${(mb / 1024).toFixed(1)}GB`
  return `${mb.toFixed(0)}MB`
}

// 格式化 Token 数量
function formatTokens(tokens: number): string {
  if (!tokens) return '0'
  if (tokens >= 1000000) return `${(tokens / 1000000).toFixed(1)}M`
  if (tokens >= 1000) return `${(tokens / 1000).toFixed(1)}K`
  return tokens.toString()
}

// 顶部统计卡片数据 - 将插件数量改为 LLM 用量
const statsData = computed(() => [
  { 
    label: 'LLM调用', 
    value: llmStats.value?.total_requests ?? '-', 
    subValue: `${formatTokens(llmStats.value?.total_tokens ?? 0)} tokens`,
    icon: 'lucide:brain', 
    color: '#3b82f6', 
    bgColor: 'rgba(59, 130, 246, 0.1)',
  },
  { 
    label: '聊天会话', 
    value: overview.value?.chats.total_streams ?? '-', 
    subValue: `群聊 ${overview.value?.chats.group_streams ?? 0} / 私聊 ${overview.value?.chats.private_streams ?? 0}`,
    icon: 'lucide:messages-square', 
    color: '#10b981', 
    bgColor: 'rgba(16, 185, 129, 0.1)',
  },
  { 
    label: '内存占用', 
    value: formatMemory(overview.value?.system.memory_usage_mb ?? 0), 
    subValue: `CPU ${overview.value?.system.cpu_percent?.toFixed(1) ?? 0}%`,
    icon: 'lucide:cpu', 
    color: '#f59e0b', 
    bgColor: 'rgba(245, 158, 11, 0.1)',
  },
  { 
    label: '运行时长', 
    value: formatUptime(overview.value?.system.uptime_seconds ?? 0), 
    icon: 'lucide:clock', 
    color: '#8b5cf6', 
    bgColor: 'rgba(139, 92, 246, 0.1)',
  },
])

// 插件列表标题
const pluginListTitle = computed(() => {
  const titles: Record<string, string> = {
    'loaded': '已加载的插件',
    'enabled': '已启用的插件',
    'disabled': '已禁用的插件',
    'failed': '加载失败的插件'
  }
  return titles[pluginListType.value] || '插件列表'
})

// 筛选后的插件列表
const filteredPluginList = computed(() => {
  const { loaded, failed } = pluginListData.value
  switch (pluginListType.value) {
    case 'loaded':
      return loaded
    case 'enabled':
      return loaded.filter(p => p.enabled)
    case 'disabled':
      return loaded.filter(p => !p.enabled)
    case 'failed':
      return failed
    default:
      return []
  }
})

// 显示插件列表弹窗
async function showPluginListModal(type: 'loaded' | 'enabled' | 'disabled' | 'failed') {
  pluginListType.value = type
  showPluginList.value = true
  pluginListLoading.value = true
  
  try {
    const res = await getPluginsByStatus()
    if (res.success && res.data) {
      pluginListData.value = res.data
    }
  } catch (error) {
    console.error('获取插件列表失败:', error)
  } finally {
    pluginListLoading.value = false
  }
}

// 显示组件详情弹窗
async function showComponentDetailModal(type: string) {
  currentComponentType.value = type
  showComponentDetail.value = true
  componentListLoading.value = true
  
  try {
    const res = await getComponentsByType(type, false)
    if (res.success && res.data) {
      componentList.value = res.data.components
    }
  } catch (error) {
    console.error('获取组件列表失败:', error)
  } finally {
    componentListLoading.value = false
  }
}

// 组件类型图标映射
function getComponentTypeIcon(type: string): string {
  const iconMap: Record<string, string> = {
    'handler': 'lucide:zap',
    'event_handler': 'lucide:zap',
    'tool': 'lucide:wrench',
    'generator': 'lucide:sparkles',
    'text_generator': 'lucide:sparkles',
    'chatter': 'lucide:message-circle',
    'router': 'lucide:route',
    'http_router': 'lucide:route',
    'scheduler': 'lucide:calendar-clock',
    'scheduled_task': 'lucide:calendar-clock',
    'middleware': 'lucide:layers',
    'willing_modifier': 'lucide:sliders-horizontal',
    'prompt_builder': 'lucide:file-text',
    'thought_chain': 'lucide:git-branch',
    'action': 'lucide:play',
    'command': 'lucide:terminal',
    'plus_command': 'lucide:plus-square',
    'interest_calculator': 'lucide:calculator',
    'prompt': 'lucide:message-square',
    'adapter': 'lucide:plug',
  }
  return iconMap[type.toLowerCase()] || 'lucide:box'
}

// 格式化组件类型名称 - 完整中文译名
function formatComponentType(type: string): string {
  const nameMap: Record<string, string> = {
    'handler': '事件处理器',
    'event_handler': '事件处理器',
    'tool': '工具',
    'generator': '生成器',
    'text_generator': '文本生成器',
    'chatter': '聊天器',
    'router': '路由',
    'http_router': 'HTTP路由',
    'scheduler': '定时任务',
    'scheduled_task': '定时任务',
    'middleware': '中间件',
    'willing_modifier': '意愿修改器',
    'prompt_builder': '提示词构建器',
    'thought_chain': '思维链',
    'action': '动作',
    'action_handler': '动作处理器',
    'message_processor': '消息处理器',
    'response_generator': '响应生成器',
    'context_provider': '上下文提供器',
    'memory_provider': '记忆提供器',
    'emotion_analyzer': '情感分析器',
    'interest_matcher': '兴趣匹配器',
    'relationship_tracker': '关系追踪器',
    'command': '命令',
    'plus_command': '扩展命令',
    'interest_calculator': '兴趣计算器',
    'prompt': '提示词',
    'adapter': '适配器',
  }
  return nameMap[type.toLowerCase()] || type
}

// 消息统计图表配置
const messageChartOption = computed(() => {
  const dataPoints = messageStats.value?.data_points || []
  
  return {
    tooltip: {
      trigger: 'axis',
      backgroundColor: 'rgba(30, 41, 59, 0.95)',
      borderColor: 'rgba(71, 85, 105, 0.5)',
      textStyle: {
        color: '#e2e8f0'
      }
    },
    legend: {
      data: ['收到消息', '发送消息'],
      textStyle: {
        color: '#94a3b8'
      },
      bottom: 0
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '15%',
      top: '10%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      boundaryGap: false,
      data: dataPoints.map(p => p.timestamp),
      axisLine: {
        lineStyle: {
          color: '#475569'
        }
      },
      axisLabel: {
        color: '#94a3b8',
        rotate: dataPoints.length > 12 ? 45 : 0
      }
    },
    yAxis: {
      type: 'value',
      axisLine: {
        lineStyle: {
          color: '#475569'
        }
      },
      axisLabel: {
        color: '#94a3b8'
      },
      splitLine: {
        lineStyle: {
          color: 'rgba(71, 85, 105, 0.3)'
        }
      }
    },
    series: [
      {
        name: '收到消息',
        type: 'line',
        smooth: true,
        data: dataPoints.map(p => p.received),
        itemStyle: {
          color: '#10b981'
        },
        areaStyle: {
          color: {
            type: 'linear',
            x: 0,
            y: 0,
            x2: 0,
            y2: 1,
            colorStops: [
              { offset: 0, color: 'rgba(16, 185, 129, 0.3)' },
              { offset: 1, color: 'rgba(16, 185, 129, 0.05)' }
            ]
          }
        }
      },
      {
        name: '发送消息',
        type: 'line',
        smooth: true,
        data: dataPoints.map(p => p.sent),
        itemStyle: {
          color: '#3b82f6'
        },
        areaStyle: {
          color: {
            type: 'linear',
            x: 0,
            y: 0,
            x2: 0,
            y2: 1,
            colorStops: [
              { offset: 0, color: 'rgba(59, 130, 246, 0.3)' },
              { offset: 1, color: 'rgba(59, 130, 246, 0.05)' }
            ]
          }
        }
      }
    ]
  }
})

onMounted(() => {
  fetchAllData()
})
</script>

<style scoped>
.dashboard-home {
  display: flex;
  flex-direction: column;
  gap: 24px;
  padding-bottom: 40px;
}

/* 统计卡片区域 */
.stats-section {
  margin-bottom: 8px;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
  gap: 20px;
}

.stat-card {
  background: var(--bg-primary);
  border-radius: var(--radius-lg);
  padding: 24px;
  display: flex;
  align-items: center;
  gap: 20px;
  box-shadow: var(--shadow-sm);
  transition: all var(--transition);
  border: 1px solid transparent;
}

.stat-card:hover {
  transform: translateY(-4px);
  box-shadow: var(--shadow-md);
  border-color: var(--border-light);
}

.stat-icon {
  width: 56px;
  height: 56px;
  border-radius: 18px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 26px;
  box-shadow: var(--shadow-sm);
}

.stat-content {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.stat-value {
  font-size: 28px;
  font-weight: 800;
  color: var(--text-primary);
  line-height: 1.2;
}

.stat-label {
  font-size: 14px;
  color: var(--text-secondary);
  font-weight: 600;
}

.stat-sub {
  margin-left: auto;
  font-size: 12px;
  padding: 4px 10px;
  background: var(--bg-secondary);
  border-radius: var(--radius-full);
  color: var(--text-tertiary);
  font-weight: 600;
}

/* 主要内容区 */
.main-section {
  margin-bottom: 8px;
}

.content-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
  gap: 24px;
}

/* 通用卡片样式 */
.card {
  background: var(--bg-primary);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-sm);
  display: flex;
  flex-direction: column;
  overflow: hidden;
  border: 1px solid transparent;
  transition: all var(--transition);
}

.card:hover {
  box-shadow: var(--shadow-md);
}

.card-header {
  padding: 20px 24px;
  border-bottom: 1px solid var(--border-light);
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.card-title {
  font-size: 18px;
  font-weight: 700;
  color: var(--text-primary);
  display: flex;
  align-items: center;
  gap: 10px;
  margin: 0;
}

.card-title svg {
  color: var(--primary);
}

.card-body {
  padding: 24px;
  flex: 1;
}

/* 插件和组件统计 */
.combined-stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 24px;
}

.mini-card {
  background: var(--bg-primary);
  border-radius: var(--radius-lg);
  padding: 24px;
  cursor: pointer;
  transition: all var(--transition);
  box-shadow: var(--shadow-sm);
  border: 1px solid transparent;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.mini-card:hover {
  transform: translateY(-2px);
  box-shadow: var(--shadow-md);
  border-color: var(--primary-light);
}

.mini-card-header {
  display: flex;
  align-items: center;
  gap: 12px;
}

.mini-card-icon {
  width: 40px;
  height: 40px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 20px;
}

.mini-card-title {
  font-size: 16px;
  font-weight: 700;
  color: var(--text-primary);
}

.mini-card-stats {
  display: flex;
  gap: 24px;
}

.mini-stat {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.mini-stat-value {
  font-size: 24px;
  font-weight: 800;
  color: var(--text-primary);
}

.mini-stat-label {
  font-size: 12px;
  color: var(--text-tertiary);
  font-weight: 600;
  text-transform: uppercase;
}

/* 图表区域 */
.chart-section {
  margin-top: 8px;
}

.chart-container {
  height: 300px;
  width: 100%;
  margin-top: 20px;
}

.chart-summary {
  display: flex;
  gap: 32px;
  margin-bottom: 20px;
}

.summary-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.summary-label {
  font-size: 12px;
  color: var(--text-tertiary);
  font-weight: 600;
  text-transform: uppercase;
}

.summary-value {
  font-size: 24px;
  font-weight: 800;
}

.summary-value.received {
  color: var(--success);
}

.summary-value.sent {
  color: var(--primary);
}

/* 插件统计详情 */
.stats-detail-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 16px;
}

.stats-detail-item {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 16px;
  background: var(--bg-secondary);
  border-radius: var(--radius);
  transition: all var(--transition-fast);
  border: 1px solid transparent;
}

.stats-detail-item:hover {
  background: var(--bg-primary);
  box-shadow: var(--shadow-sm);
  border-color: var(--border-light);
}

.detail-icon {
  width: 48px;
  height: 48px;
  border-radius: 14px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 22px;
}

.detail-info {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.detail-value {
  font-size: 20px;
  font-weight: 700;
  color: var(--text-primary);
}

.detail-label {
  font-size: 12px;
  color: var(--text-tertiary);
  font-weight: 600;
}

/* 弹窗样式 */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.4);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  backdrop-filter: blur(8px);
}

.modal-content {
  background: var(--bg-primary);
  border-radius: var(--radius-xl);
  width: 90%;
  max-width: 500px;
  max-height: 85vh;
  overflow: hidden;
  animation: modalIn 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  box-shadow: var(--shadow-lg);
}

@keyframes modalIn {
  from {
    opacity: 0;
    transform: scale(0.95) translateY(10px);
  }
  to {
    opacity: 1;
    transform: scale(1) translateY(0);
  }
}

.modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 20px 24px;
  border-bottom: 1px solid var(--border-light);
}

.modal-header h3 {
  margin: 0;
  font-size: 18px;
  font-weight: 700;
  color: var(--text-primary);
}

.close-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  border: none;
  background: transparent;
  border-radius: var(--radius);
  color: var(--text-secondary);
  cursor: pointer;
  transition: all var(--transition-fast);
}

.close-btn:hover {
  background: var(--bg-secondary);
  color: var(--danger);
}

.modal-body {
  padding: 24px;
  overflow-y: auto;
}

/* 空状态 */
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 48px;
  color: var(--text-tertiary);
  gap: 16px;
}

.empty-state.small {
  padding: 32px;
}

.empty-state.small .empty-icon {
  font-size: 36px;
}

.empty-icon {
  font-size: 56px;
  opacity: 0.4;
  color: var(--text-tertiary);
}

/* 日程卡片 */
.date-badge {
  font-size: 13px;
  color: var(--primary);
  padding: 6px 14px;
  background: var(--primary-bg);
  border-radius: var(--radius-full);
  font-weight: 700;
}

.current-activity {
  background: linear-gradient(135deg, var(--primary-bg), rgba(249, 115, 22, 0.05));
  border: 1px solid rgba(249, 115, 22, 0.2);
  border-radius: var(--radius);
  padding: 20px;
  margin-bottom: 20px;
}

.current-label {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
  font-weight: 700;
  color: var(--primary);
  margin-bottom: 8px;
  text-transform: uppercase;
  letter-spacing: 1px;
}

.current-content {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.current-time {
  font-size: 14px;
  color: var(--text-secondary);
  font-weight: 600;
}

.current-text {
  font-size: 18px;
  font-weight: 700;
  color: var(--text-primary);
}

.schedule-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
  flex: 1;
  overflow-y: auto;
}

.schedule-item {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 14px 16px;
  background: var(--bg-secondary);
  border-radius: var(--radius);
  transition: all var(--transition-fast);
  border: 1px solid transparent;
}

.schedule-item:hover {
  background: var(--bg-primary);
  box-shadow: var(--shadow-sm);
  transform: translateX(4px);
}

.schedule-item.is-current {
  background: var(--primary-bg);
  border-left: 4px solid var(--primary);
}

.schedule-time {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-secondary);
  min-width: 110px;
}

.schedule-activity {
  font-size: 15px;
  color: var(--text-primary);
  flex: 1;
  font-weight: 500;
}

/* 月度计划卡片 */
.plans-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.plan-item {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 14px;
  background: var(--bg-secondary);
  border-radius: var(--radius);
  transition: all var(--transition-fast);
}

.plan-item:hover {
  background: var(--bg-primary);
  box-shadow: var(--shadow-sm);
}

.plan-icon {
  font-size: 18px;
  color: var(--success);
  flex-shrink: 0;
  margin-top: 2px;
}

.plan-text {
  font-size: 15px;
  color: var(--text-primary);
  line-height: 1.5;
  font-weight: 500;
}

/* 加大弹窗 */
.modal-large {
  max-width: 700px;
}

/* 可点击的详情项 */
.stats-detail-item.clickable {
  cursor: pointer;
}

.stats-detail-item.clickable:hover {
  background: var(--bg-primary);
  transform: translateY(-2px);
  box-shadow: var(--shadow-sm);
}

.detail-arrow {
  color: var(--text-tertiary);
  font-size: 18px;
  margin-left: auto;
}

/* 加载状态 */
.loading-state {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  padding: 48px;
  color: var(--text-tertiary);
  font-weight: 500;
}

/* 插件列表 */
.plugin-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
  max-height: 400px;
  overflow-y: auto;
}

.plugin-item {
  background: var(--bg-secondary);
  border-radius: var(--radius);
  padding: 16px;
  transition: all var(--transition-fast);
  border: 1px solid transparent;
}

.plugin-item:hover {
  background: var(--bg-primary);
  box-shadow: var(--shadow-sm);
  border-color: var(--border-light);
}

.plugin-item-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 8px;
}

.plugin-name {
  font-size: 16px;
  font-weight: 700;
  color: var(--text-primary);
  flex: 1;
}

.plugin-version {
  font-size: 12px;
  color: var(--text-secondary);
  padding: 2px 8px;
  background: var(--bg-tertiary);
  border-radius: var(--radius-sm);
  font-weight: 600;
}

.plugin-item-info {
  display: flex;
  gap: 16px;
  font-size: 13px;
  color: var(--text-secondary);
  margin-bottom: 8px;
}

.plugin-error {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  font-size: 13px;
  color: var(--danger);
  background: var(--danger-bg);
  padding: 10px 14px;
  border-radius: var(--radius);
  margin-top: 10px;
  font-weight: 500;
}

.plugin-error span {
  word-break: break-all;
}

/* 组件列表 */
.component-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
  max-height: 400px;
  overflow-y: auto;
}

.component-item {
  background: var(--bg-secondary);
  border-radius: var(--radius);
  padding: 16px;
  transition: all var(--transition-fast);
  border: 1px solid transparent;
}

.component-item:hover {
  background: var(--bg-primary);
  box-shadow: var(--shadow-sm);
  border-color: var(--border-light);
}

.component-item-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 8px;
}

.component-name {
  font-size: 16px;
  font-weight: 700;
  color: var(--text-primary);
  flex: 1;
}

.component-status {
  font-size: 12px;
  font-weight: 600;
  padding: 4px 10px;
  border-radius: var(--radius-full);
}

.component-status.enabled {
  color: var(--success);
  background: var(--success-bg);
}

.component-status.disabled {
  color: var(--warning);
  background: var(--warning-bg);
}

.component-item-desc {
  font-size: 14px;
  color: var(--text-secondary);
  line-height: 1.5;
  margin-bottom: 10px;
}

.component-item-plugin {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: var(--text-tertiary);
  font-weight: 500;
}

.component-item-plugin svg {
  font-size: 14px;
}

/* 响应式 */
@media (max-width: 1024px) {
  .content-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 640px) {
  .stats-grid {
    grid-template-columns: 1fr;
  }
  
  .combined-stats-grid {
    grid-template-columns: 1fr;
  }
  
  .stats-detail-grid {
    grid-template-columns: 1fr;
  }
  
  .chart-summary {
    flex-direction: column;
    gap: 16px;
  }
}
</style>
