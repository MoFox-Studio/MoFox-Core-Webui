<!--
  @file DashboardHome.vue
  @description 仪表盘首页视图 - 全新设计
  
  功能说明：
  1. 每日名言 - 励志名言展示
  2. 快捷功能入口 - 8个常用功能快捷访问
  3. 系统状态概览 - CPU、内存、运行时长等
  4. 今日日程 - 显示当日活动安排
  5. 消息统计图表 - 可视化消息收发趋势
-->
<template>
  <div class="dashboard-home-new">
    <!-- 连接错误弹窗 -->
    <ConnectionError 
      :visible="showConnectionError"
      :message="connectionErrorMsg"
      @close="showConnectionError = false"
      @retry="fetchAllData"
    />

    <!-- 每日名言 -->
    <DailyQuote />

    <!-- 快捷功能入口 -->
    <QuickActions />

    <!-- 系统状态 + 今日日程 -->
    <section class="main-content">
      <div class="content-grid">
        <!-- 左侧：系统状态 -->
        <SystemStatus 
          :overview="overview" 
          :is-refreshing="isRefreshingOverview"
          @refresh="handleRefreshOverview"
        />

        <!-- 右侧：今日日程 -->
        <TodaySchedule 
          :schedule="schedule" 
          :monthly-plans="monthlyPlans"
        />
      </div>
    </section>

    <!-- 消息统计图表 -->
    <section class="chart-section">
      <div class="m3-card chart-card">
        <div class="card-header">
          <div class="header-title">
            <span class="material-symbols-rounded">bar_chart</span>
            <h3>消息统计</h3>
          </div>
          <div class="header-actions">
            <M3Select 
              v-model="messageStatsPeriod" 
              :options="messageStatsOptions"
              @change="fetchMessageStats"
            />
          </div>
        </div>
        <div class="card-body chart-body">
          <div v-if="chartLoading" class="loading-overlay">
            <span class="material-symbols-rounded spinning">refresh</span>
          </div>
          <v-chart class="chart" :option="messageChartOption" autoresize />
        </div>
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, computed } from 'vue'
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { LineChart } from 'echarts/charts'
import { GridComponent, TooltipComponent, LegendComponent } from 'echarts/components'
import VChart from 'vue-echarts'
import { 
  getDashboardOverview, 
  getTodaySchedule, 
  getMessageStats,
  getMonthlyPlans,
  type DashboardOverview, 
  type ScheduleResponse, 
  type MessageStatsResponse,
  type MonthlyPlanResponse,
} from '@/api/dashboard'
import ConnectionError from '@/components/ConnectionError.vue'
import M3Select from '@/components/M3Select.vue'
import DailyQuote from '@/components/dashboard/DailyQuote.vue'
import QuickActions from '@/components/dashboard/QuickActions.vue'
import SystemStatus from '@/components/dashboard/SystemStatus.vue'
import TodaySchedule from '@/components/dashboard/TodaySchedule.vue'
import { useThemeStore } from '@/stores/theme'

// 注册 ECharts 组件
use([CanvasRenderer, LineChart, GridComponent, TooltipComponent, LegendComponent])

const themeStore = useThemeStore()

const loading = ref(false)
const chartLoading = ref(false)
const overview = ref<DashboardOverview | null>(null)
const schedule = ref<ScheduleResponse | null>(null)
const monthlyPlans = ref<MonthlyPlanResponse | null>(null)
const messageStats = ref<MessageStatsResponse | null>(null)
const messageStatsPeriod = ref<'last_hour' | 'last_24_hours' | 'last_7_days' | 'last_30_days'>('last_24_hours')
const isRefreshingOverview = ref(false)

// 自动刷新定时器
let autoRefreshTimer: number | null = null

const messageStatsOptions = [
  { label: '最近1小时', value: 'last_hour' },
  { label: '最近24小时', value: 'last_24_hours' },
  { label: '最近7天', value: 'last_7_days' },
  { label: '最近30天', value: 'last_30_days' }
]

// 连接错误状态
const showConnectionError = ref(false)
const connectionErrorMsg = ref('')

// 手动刷新overview
async function handleRefreshOverview() {
  isRefreshingOverview.value = true
  const startTime = Date.now()
  try {
    const overviewRes = await getDashboardOverview()
    if (overviewRes.success && overviewRes.data) {
      overview.value = overviewRes.data
    }
  } catch (error) {
    console.error('刷新系统状态失败:', error)
  } finally {
    // 确保至少显示 800ms 的加载动画
    const elapsed = Date.now() - startTime
    const minDelay = 800
    if (elapsed < minDelay) {
      await new Promise(resolve => setTimeout(resolve, minDelay - elapsed))
    }
    isRefreshingOverview.value = false
  }
}

// 自动刷新overview（仅更新overview数据，不刷新其他）
async function autoRefreshOverview() {
  try {
    const overviewRes = await getDashboardOverview()
    if (overviewRes.success && overviewRes.data) {
      overview.value = overviewRes.data
    }
  } catch (error) {
    // 静默失败，不影响用户体验
    console.debug('自动刷新失败:', error)
  }
}

// 启动自动刷新
function startAutoRefresh() {
  if (autoRefreshTimer) return
  autoRefreshTimer = window.setInterval(() => {
    autoRefreshOverview()
  }, 5000) // 每5秒刷新一次
}

// 停止自动刷新
function stopAutoRefresh() {
  if (autoRefreshTimer) {
    clearInterval(autoRefreshTimer)
    autoRefreshTimer = null
  }
}

// 获取所有数据
async function fetchAllData() {
  loading.value = true
  showConnectionError.value = false
  
  try {
    // 并行获取所有数据
    const [overviewRes, scheduleRes, plansRes] = await Promise.all([
      getDashboardOverview(),
      getTodaySchedule(),
      getMonthlyPlans(),
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

// 消息统计图表配置
const messageChartOption = computed(() => {
  const dataPoints = messageStats.value?.data_points || []
  
  // 获取 CSS 变量值的辅助函数
  const getColor = (name: string) => {
    const val = getComputedStyle(document.documentElement).getPropertyValue(name).trim()
    return val || (themeStore.isDark ? '#ffffff' : '#000000')
  }

  return {
    backgroundColor: 'transparent',
    tooltip: {
      trigger: 'axis',
      backgroundColor: getColor('--md-sys-color-surface-container-high'),
      borderColor: getColor('--md-sys-color-outline-variant'),
      textStyle: {
        color: getColor('--md-sys-color-on-surface')
      },
      padding: [8, 12],
      borderRadius: 8
    },
    legend: {
      data: ['收到消息', '发送消息'],
      textStyle: {
        color: getColor('--md-sys-color-on-surface-variant')
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
          color: getColor('--md-sys-color-outline-variant')
        }
      },
      axisLabel: {
        color: getColor('--md-sys-color-on-surface-variant'),
        rotate: dataPoints.length > 12 ? 45 : 0
      }
    },
    yAxis: {
      type: 'value',
      axisLine: {
        lineStyle: {
          color: getColor('--md-sys-color-outline-variant')
        }
      },
      axisLabel: {
        color: getColor('--md-sys-color-on-surface-variant')
      },
      splitLine: {
        lineStyle: {
          color: getColor('--md-sys-color-outline-variant'),
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
  startAutoRefresh()
})

onUnmounted(() => {
  stopAutoRefresh()
})
</script>

<style scoped>
.dashboard-home-new {
  display: flex;
  flex-direction: column;
  gap: 0;
  padding-bottom: 40px;
  max-width: 1600px;
  margin: 0 auto;
  width: 100%;
}

.main-content {
  margin-bottom: 24px;
}

.content-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 24px;
  align-items: start;
}

.chart-section {
  animation: slideIn 0.5s cubic-bezier(0.2, 0, 0, 1) 0.4s backwards;
}

.m3-card {
  background: var(--md-sys-color-surface-container);
  border-radius: 24px;
  padding: 24px;
  transition: all 0.3s cubic-bezier(0.2, 0, 0, 1);
  border: 1px solid rgba(255, 255, 255, 0.05);
}

.chart-card {
  min-height: 400px;
  display: flex;
  flex-direction: column;
}

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

.chart-body {
  flex: 1;
  position: relative;
  min-height: 300px;
}

.chart {
  width: 100%;
  height: 100%;
  min-height: 300px;
}

.loading-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--md-sys-color-surface-container);
  z-index: 10;
}

.spinning {
  animation: spin 1s linear infinite;
  font-size: 36px;
  color: var(--md-sys-color-primary);
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

@keyframes slideIn {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* 响应式 */
@media (max-width: 1024px) {
  .content-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 768px) {
  .m3-card {
    padding: 16px;
    border-radius: 16px;
  }

  .chart-body,
  .chart {
    min-height: 250px;
  }
}
</style>
