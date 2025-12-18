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
        <div class="m3-card stat-card" v-for="stat in statsData" :key="stat.label">
          <div class="stat-icon-container" :style="{ backgroundColor: stat.bgColor, color: stat.color }">
            <span class="material-symbols-rounded stat-icon">{{ stat.icon }}</span>
          </div>
          <div class="stat-content">
            <div class="stat-value-row">
              <span class="stat-value">{{ stat.value }}</span>
            </div>
            <span class="stat-label">{{ stat.label }}</span>
          </div>
          <div v-if="stat.subValue" class="stat-sub">
            <span class="material-symbols-rounded sub-icon">info</span>
            <span>{{ stat.subValue }}</span>
          </div>
        </div>
      </div>
    </section>

    <!-- 主要内容区 -->
    <section class="main-section">
      <div class="content-grid">
        <!-- 左侧列 -->
        <div class="grid-column">
          <!-- 今日日程 -->
          <div class="m3-card schedule-card">
            <div class="card-header">
              <div class="header-title">
                <span class="material-symbols-rounded">calendar_today</span>
                <h3>今日日程</h3>
              </div>
              <span class="m3-badge secondary">{{ schedule?.date || '加载中...' }}</span>
            </div>
            <div class="card-body">
              <!-- 当前活动 -->
              <div v-if="schedule?.current_activity" class="current-activity">
                <div class="activity-label">
                  <span class="material-symbols-rounded">play_circle</span>
                  当前活动
                </div>
                <div class="activity-content">
                  <span class="activity-time">{{ schedule.current_activity.time_range }}</span>
                  <span class="activity-text">{{ schedule.current_activity.activity }}</span>
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
                  <div class="item-time">{{ item.time_range }}</div>
                  <div class="item-content">{{ item.activity }}</div>
                </div>
              </div>
              <div v-else class="empty-state">
                <span class="material-symbols-rounded empty-icon">event_busy</span>
                <p>暂无日程安排</p>
              </div>
            </div>
          </div>

          <!-- 消息统计图表 -->
          <div class="m3-card chart-card">
            <div class="card-header">
              <div class="header-title">
                <span class="material-symbols-rounded">bar_chart</span>
                <h3>消息统计</h3>
              </div>
              <div class="header-actions">
                <select v-model="messageStatsPeriod" @change="fetchMessageStats" class="m3-select">
                  <option value="last_hour">最近1小时</option>
                  <option value="last_24_hours">最近24小时</option>
                  <option value="last_7_days">最近7天</option>
                  <option value="last_30_days">最近30天</option>
                </select>
              </div>
            </div>
            <div class="card-body chart-body">
              <div v-if="chartLoading" class="loading-overlay">
                <span class="material-symbols-rounded spinning">refresh</span>
              </div>
              <v-chart class="chart" :option="messageChartOption" autoresize />
            </div>
          </div>
        </div>

        <!-- 右侧列 -->
        <div class="grid-column">
          <!-- 月度计划 -->
          <div class="m3-card plans-card">
            <div class="card-header">
              <div class="header-title">
                <span class="material-symbols-rounded">track_changes</span>
                <h3>月度计划</h3>
              </div>
              <span class="m3-badge tertiary" v-if="monthlyPlans">
                {{ monthlyPlans.total }} 项
              </span>
            </div>
            <div class="card-body">
              <div v-if="monthlyPlans?.plans?.length" class="plans-list">
                <div class="plan-item" v-for="(plan, index) in monthlyPlans.plans" :key="index">
                  <span class="material-symbols-rounded plan-check">check_box</span>
                  <span class="plan-text">{{ plan }}</span>
                </div>
              </div>
              <div v-else class="empty-state">
                <span class="material-symbols-rounded empty-icon">assignment</span>
                <p>暂无月度计划</p>
              </div>
            </div>
          </div>

          <!-- 概览小卡片 -->
          <div class="mini-cards-grid">
            <!-- 插件概览 -->
            <div class="m3-card mini-card clickable" @click="showPluginListModal('loaded')">
              <div class="mini-card-header">
                <span class="mini-card-title">插件系统</span>
                <span class="material-symbols-rounded arrow-icon">chevron_right</span>
              </div>
              <div class="mini-card-stats">
                <div class="mini-stat">
                  <span class="mini-value">{{ overview?.plugins.loaded_count ?? '-' }}</span>
                  <span class="mini-label">已加载</span>
                </div>
                <div class="mini-stat">
                  <span class="mini-value error">{{ overview?.plugins.failed_count ?? '-' }}</span>
                  <span class="mini-label">失败</span>
                </div>
              </div>
            </div>

            <!-- 组件概览 -->
            <div class="m3-card mini-card clickable" @click="showComponentDetailModal('all')">
              <div class="mini-card-header">
                <span class="mini-card-title">组件系统</span>
                <span class="material-symbols-rounded arrow-icon">chevron_right</span>
              </div>
              <div class="mini-card-stats">
                <div class="mini-stat">
                  <span class="mini-value">{{ overview?.components.total_count ?? '-' }}</span>
                  <span class="mini-label">总数</span>
                </div>
                <div class="mini-stat">
                  <span class="mini-value success">{{ overview?.components.enabled_count ?? '-' }}</span>
                  <span class="mini-label">启用</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- 插件列表弹窗 -->
    <div class="m3-dialog-overlay" v-if="showPluginList" @click="showPluginList = false">
      <div class="m3-dialog" @click.stop>
        <div class="dialog-header">
          <h3>{{ pluginListTitle }}</h3>
          <button class="m3-icon-button" @click="showPluginList = false">
            <span class="material-symbols-rounded">close</span>
          </button>
        </div>
        <div class="dialog-content">
          <div v-if="pluginListLoading" class="loading-state">
            <span class="material-symbols-rounded spinning">refresh</span>
            加载中...
          </div>
          <div v-else-if="filteredPluginList.length" class="plugin-list">
            <div class="plugin-item" v-for="plugin in filteredPluginList" :key="plugin.id">
              <div class="plugin-item-header">
                <span class="plugin-name">{{ plugin.name }}</span>
                <span class="plugin-version">v{{ plugin.version }}</span>
              </div>
              <div class="plugin-item-info">
                <span>{{ plugin.author }}</span>
                <span>{{ plugin.description }}</span>
              </div>
              <div v-if="plugin.error" class="plugin-error">
                <span class="material-symbols-rounded">error</span>
                <span>{{ plugin.error }}</span>
              </div>
            </div>
          </div>
          <div v-else class="empty-state">
            <p>暂无数据</p>
          </div>
        </div>
      </div>
    </div>

    <!-- 组件列表弹窗 -->
    <div class="m3-dialog-overlay" v-if="showComponentDetail" @click="showComponentDetail = false">
      <div class="m3-dialog" @click.stop>
        <div class="dialog-header">
          <h3>组件列表</h3>
          <button class="m3-icon-button" @click="showComponentDetail = false">
            <span class="material-symbols-rounded">close</span>
          </button>
        </div>
        <div class="dialog-content">
          <div v-if="componentListLoading" class="loading-state">
            <span class="material-symbols-rounded spinning">refresh</span>
            加载中...
          </div>
          <div v-else-if="componentList.length" class="component-list">
            <div class="component-item" v-for="comp in componentList" :key="comp.id">
              <div class="component-item-header">
                <span class="material-symbols-rounded component-icon">{{ getComponentTypeIcon(comp.type) }}</span>
                <span class="component-name">{{ comp.name }}</span>
                <span class="component-status" :class="comp.enabled ? 'enabled' : 'disabled'">
                  {{ comp.enabled ? '已启用' : '已禁用' }}
                </span>
              </div>
              <div class="component-item-desc">{{ comp.description }}</div>
              <div class="component-item-plugin">
                <span class="material-symbols-rounded">extension</span>
                {{ comp.plugin_id }}
              </div>
            </div>
          </div>
          <div v-else class="empty-state">
            <p>暂无数据</p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { LineChart } from 'echarts/charts'
import { GridComponent, TooltipComponent, LegendComponent } from 'echarts/components'
import VChart from 'vue-echarts'
import { 
  getDashboardOverview, 
  getTodaySchedule, 
  getMonthlyPlans,
  getLLMStats,
  getMessageStats,
  getPluginsByStatus,
  getComponentsByType
} from '@/api'
import type { 
  DashboardOverview, 
  ScheduleResponse, 
  ScheduleActivity,
  MonthlyPlanResponse,
  LLMStatsResponse,
  MessageStatsResponse,
  PluginListItem,
  ComponentItem
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

// 顶部统计卡片数据
const statsData = computed(() => [
  { 
    label: 'LLM调用', 
    value: llmStats.value?.total_requests ?? '-', 
    subValue: `${formatTokens(llmStats.value?.total_tokens ?? 0)} tokens`,
    icon: 'psychology', 
    color: 'var(--md-sys-color-primary)', 
    bgColor: 'var(--md-sys-color-primary-container)',
  },
  { 
    label: '聊天会话', 
    value: overview.value?.chats.total_streams ?? '-', 
    subValue: `群聊 ${overview.value?.chats.group_streams ?? 0} / 私聊 ${overview.value?.chats.private_streams ?? 0}`,
    icon: 'chat', 
    color: 'var(--md-sys-color-tertiary)', 
    bgColor: 'var(--md-sys-color-tertiary-container)',
  },
  { 
    label: '内存占用', 
    value: formatMemory(overview.value?.system.memory_usage_mb ?? 0), 
    subValue: `CPU ${overview.value?.system.cpu_percent ?? 0}%`,
    icon: 'memory', 
    color: 'var(--md-sys-color-error)', 
    bgColor: 'var(--md-sys-color-error-container)',
  },
  { 
    label: '运行时长', 
    value: formatUptime(overview.value?.system.uptime_seconds ?? 0), 
    icon: 'schedule', 
    color: 'var(--md-sys-color-secondary)', 
    bgColor: 'var(--md-sys-color-secondary-container)',
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
    'handler': 'bolt',
    'event_handler': 'bolt',
    'tool': 'build',
    'generator': 'auto_awesome',
    'text_generator': 'auto_awesome',
    'chatter': 'chat_bubble',
    'router': 'alt_route',
    'http_router': 'alt_route',
    'scheduler': 'update',
    'scheduled_task': 'update',
    'middleware': 'layers',
    'willing_modifier': 'tune',
    'prompt_builder': 'description',
    'thought_chain': 'account_tree',
    'action': 'play_arrow',
    'command': 'terminal',
    'plus_command': 'add_box',
    'interest_calculator': 'calculate',
    'prompt': 'chat',
    'adapter': 'power',
  }
  return iconMap[type.toLowerCase()] || 'extension'
}

// 消息统计图表配置
const messageChartOption = computed(() => {
  const dataPoints = messageStats.value?.data_points || []
  const isDark = true // 假设暗色模式，实际应从主题 store 获取

  return {
    backgroundColor: 'transparent',
    tooltip: {
      trigger: 'axis',
      backgroundColor: 'var(--md-sys-color-surface-container-high)',
      borderColor: 'var(--md-sys-color-outline-variant)',
      textStyle: {
        color: 'var(--md-sys-color-on-surface)'
      },
      padding: [8, 12],
      borderRadius: 8
    },
    legend: {
      data: ['收到消息', '发送消息'],
      textStyle: {
        color: 'var(--md-sys-color-on-surface-variant)'
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
          color: 'var(--md-sys-color-outline-variant)'
        }
      },
      axisLabel: {
        color: 'var(--md-sys-color-on-surface-variant)',
        rotate: dataPoints.length > 12 ? 45 : 0
      }
    },
    yAxis: {
      type: 'value',
      axisLine: {
        lineStyle: {
          color: 'var(--md-sys-color-outline-variant)'
        }
      },
      axisLabel: {
        color: 'var(--md-sys-color-on-surface-variant)'
      },
      splitLine: {
        lineStyle: {
          color: 'var(--md-sys-color-outline-variant)',
          opacity: 0.3
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
          color: '#10b981' // 保持原有颜色或使用主题色
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
  animation: fadeIn 0.4s cubic-bezier(0.2, 0, 0, 1);
  padding-bottom: 40px;
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.spinning {
  animation: spin 1s linear infinite;
}

/* 统计卡片区 */
.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
  gap: 16px;
}

.m3-card {
  background: var(--md-sys-color-surface-container);
  border-radius: 16px;
  padding: 20px;
  transition: all 0.2s cubic-bezier(0.2, 0, 0, 1);
}

.stat-card {
  display: flex;
  align-items: flex-start;
  gap: 16px;
  position: relative;
  overflow: hidden;
}

.stat-card:hover {
  background: var(--md-sys-color-surface-container-high);
  transform: translateY(-2px);
  box-shadow: var(--md-sys-elevation-2);
}

.stat-icon-container {
  width: 48px;
  height: 48px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.stat-icon {
  font-size: 24px;
}

.stat-content {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.stat-value {
  font-size: 28px;
  font-weight: 600;
  color: var(--md-sys-color-on-surface);
  line-height: 1.2;
}

.stat-label {
  font-size: 14px;
  color: var(--md-sys-color-on-surface-variant);
  margin-top: 4px;
}

.stat-sub {
  position: absolute;
  top: 16px;
  right: 16px;
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
  color: var(--md-sys-color-on-surface-variant);
  background: var(--md-sys-color-surface-container-highest);
  padding: 4px 8px;
  border-radius: 8px;
}

.sub-icon {
  font-size: 14px;
}

/* 主内容网格 */
.content-grid {
  display: grid;
  grid-template-columns: 1.5fr 1fr;
  gap: 24px;
}

.grid-column {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

/* 卡片通用 */
.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 20px;
}

.header-title {
  display: flex;
  align-items: center;
  gap: 12px;
  color: var(--md-sys-color-on-surface);
}

.header-title h3 {
  font-size: 18px;
  font-weight: 500;
  margin: 0;
}

.header-title .material-symbols-rounded {
  color: var(--md-sys-color-primary);
}

.m3-badge {
  font-size: 12px;
  padding: 4px 12px;
  border-radius: 100px;
  font-weight: 500;
}

.m3-badge.secondary {
  background: var(--md-sys-color-secondary-container);
  color: var(--md-sys-color-on-secondary-container);
}

.m3-badge.tertiary {
  background: var(--md-sys-color-tertiary-container);
  color: var(--md-sys-color-on-tertiary-container);
}

/* 日程卡片 */
.current-activity {
  background: var(--md-sys-color-primary-container);
  color: var(--md-sys-color-on-primary-container);
  border-radius: 12px;
  padding: 16px;
  margin-bottom: 20px;
}

.activity-label {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
  font-weight: 500;
  margin-bottom: 8px;
  opacity: 0.8;
}

.activity-content {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.activity-time {
  font-size: 14px;
  opacity: 0.9;
}

.activity-text {
  font-size: 18px;
  font-weight: 600;
}

.schedule-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
  max-height: 300px;
  overflow-y: auto;
  padding-right: 8px;
}

.schedule-list::-webkit-scrollbar {
  width: 6px;
}

.schedule-list::-webkit-scrollbar-track {
  background: transparent;
}

.schedule-list::-webkit-scrollbar-thumb {
  background-color: var(--md-sys-color-outline-variant);
  border-radius: 3px;
}

.schedule-item {
  display: flex;
  align-items: center;
  padding: 12px;
  border-radius: 8px;
  background: var(--md-sys-color-surface-container-low);
  border-left: 3px solid transparent;
}

.schedule-item.is-current {
  background: var(--md-sys-color-surface-container-highest);
  border-left-color: var(--md-sys-color-primary);
}

.item-time {
  width: 100px;
  font-size: 13px;
  color: var(--md-sys-color-on-surface-variant);
  font-variant-numeric: tabular-nums;
}

.item-content {
  flex: 1;
  font-size: 14px;
  color: var(--md-sys-color-on-surface);
}

/* 计划列表 */
.plans-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.plan-item {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 12px;
  background: var(--md-sys-color-surface-container-low);
  border-radius: 8px;
}

.plan-check {
  color: var(--md-sys-color-primary);
  font-size: 20px;
}

.plan-text {
  flex: 1;
  font-size: 14px;
  color: var(--md-sys-color-on-surface);
  line-height: 1.5;
}

/* 迷你卡片 */
.mini-cards-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
}

.mini-card {
  padding: 16px;
  cursor: pointer;
}

.mini-card:hover {
  background: var(--md-sys-color-surface-container-high);
}

.mini-card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
}

.mini-card-title {
  font-size: 14px;
  font-weight: 500;
  color: var(--md-sys-color-on-surface);
}

.arrow-icon {
  font-size: 20px;
  color: var(--md-sys-color-on-surface-variant);
}

.mini-card-stats {
  display: flex;
  gap: 16px;
}

.mini-stat {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.mini-value {
  font-size: 20px;
  font-weight: 600;
  color: var(--md-sys-color-on-surface);
}

.mini-value.error { color: var(--md-sys-color-error); }
.mini-value.success { color: var(--md-sys-color-primary); }

.mini-label {
  font-size: 11px;
  color: var(--md-sys-color-on-surface-variant);
}

/* 图表卡片 */
.chart-card {
  min-height: 300px;
  display: flex;
  flex-direction: column;
}

.chart-body {
  flex: 1;
  position: relative;
  min-height: 240px;
}

.chart {
  width: 100%;
  height: 100%;
}

.m3-select {
  background: var(--md-sys-color-surface-container-highest);
  color: var(--md-sys-color-on-surface);
  border: none;
  padding: 6px 12px;
  border-radius: 8px;
  font-size: 13px;
  outline: none;
  cursor: pointer;
}

/* 弹窗样式 */
.m3-dialog-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  backdrop-filter: blur(4px);
}

.m3-dialog {
  background: var(--md-sys-color-surface-container);
  width: 90%;
  max-width: 500px;
  max-height: 80vh;
  border-radius: 28px;
  display: flex;
  flex-direction: column;
  box-shadow: var(--md-sys-elevation-3);
  animation: dialogIn 0.3s cubic-bezier(0.2, 0, 0, 1);
}

@keyframes dialogIn {
  from { opacity: 0; transform: scale(0.9); }
  to { opacity: 1; transform: scale(1); }
}

.dialog-header {
  padding: 24px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  border-bottom: 1px solid var(--md-sys-color-outline-variant);
}

.dialog-header h3 {
  margin: 0;
  font-size: 22px;
  color: var(--md-sys-color-on-surface);
}

.m3-icon-button {
  background: transparent;
  border: none;
  color: var(--md-sys-color-on-surface-variant);
  cursor: pointer;
  width: 40px;
  height: 40px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: background 0.2s;
}

.m3-icon-button:hover {
  background: var(--md-sys-color-surface-container-highest);
}

.dialog-content {
  padding: 24px;
  overflow-y: auto;
}

/* 列表项样式 */
.plugin-list, .component-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.plugin-item, .component-item {
  background: var(--md-sys-color-surface-container-low);
  padding: 16px;
  border-radius: 12px;
}

.plugin-item-header, .component-item-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 8px;
}

.plugin-name, .component-name {
  font-weight: 600;
  color: var(--md-sys-color-on-surface);
  flex: 1;
}

.plugin-version {
  font-size: 12px;
  background: var(--md-sys-color-surface-container-highest);
  padding: 2px 8px;
  border-radius: 4px;
}

.plugin-item-info {
  font-size: 13px;
  color: var(--md-sys-color-on-surface-variant);
  display: flex;
  gap: 12px;
}

.component-status {
  font-size: 12px;
  padding: 2px 8px;
  border-radius: 4px;
}

.component-status.enabled {
  background: rgba(16, 185, 129, 0.1);
  color: #10b981;
}

.component-status.disabled {
  background: rgba(245, 158, 11, 0.1);
  color: #f59e0b;
}

.component-item-desc {
  font-size: 13px;
  color: var(--md-sys-color-on-surface-variant);
  margin-bottom: 8px;
}

.component-item-plugin {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: var(--md-sys-color-on-surface-variant);
  opacity: 0.8;
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 40px;
  color: var(--md-sys-color-on-surface-variant);
  gap: 12px;
}

.empty-icon {
  font-size: 48px;
  opacity: 0.5;
}

/* 响应式 */
@media (max-width: 1024px) {
  .content-grid {
    grid-template-columns: 1fr;
  }
  
  .mini-cards-grid {
    grid-template-columns: 1fr;
  }
}
</style>
