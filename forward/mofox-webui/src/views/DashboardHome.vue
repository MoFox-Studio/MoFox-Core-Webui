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
          <div class="card-body">
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

    <!-- 插件统计 -->
    <section class="plugins-section">
      <div class="card">
        <div class="card-header">
          <h3 class="card-title">
            <Icon icon="lucide:puzzle" />
            插件统计
          </h3>
          <button class="refresh-btn" @click="fetchAllData" :disabled="loading">
            <Icon :icon="loading ? 'lucide:loader-2' : 'lucide:refresh-cw'" :class="{ spinning: loading }" />
          </button>
        </div>
        <div class="card-body">
          <div class="stats-detail-grid">
            <div class="stats-detail-item">
              <div class="detail-icon" style="background: rgba(16, 185, 129, 0.1)">
                <Icon icon="lucide:check-circle" style="color: #10b981" />
              </div>
              <div class="detail-info">
                <span class="detail-value">{{ overview?.plugins.loaded ?? '-' }}</span>
                <span class="detail-label">已加载</span>
              </div>
            </div>
            <div class="stats-detail-item">
              <div class="detail-icon" style="background: rgba(59, 130, 246, 0.1)">
                <Icon icon="lucide:circle-dot" style="color: #3b82f6" />
              </div>
              <div class="detail-info">
                <span class="detail-value">{{ overview?.plugins.enabled ?? '-' }}</span>
                <span class="detail-label">已启用</span>
              </div>
            </div>
            <div class="stats-detail-item">
              <div class="detail-icon" style="background: rgba(245, 158, 11, 0.1)">
                <Icon icon="lucide:circle-pause" style="color: #f59e0b" />
              </div>
              <div class="detail-info">
                <span class="detail-value">{{ overview?.plugins.disabled ?? '-' }}</span>
                <span class="detail-label">已禁用</span>
              </div>
            </div>
            <div class="stats-detail-item">
              <div class="detail-icon" style="background: rgba(239, 68, 68, 0.1)">
                <Icon icon="lucide:alert-circle" style="color: #ef4444" />
              </div>
              <div class="detail-info">
                <span class="detail-value">{{ overview?.plugins.failed ?? '-' }}</span>
                <span class="detail-label">加载失败</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- 组件统计 -->
    <section class="activity-section">
      <div class="card">
        <div class="card-header">
          <h3 class="card-title">
            <Icon icon="lucide:boxes" />
            组件统计
          </h3>
          <span class="total-badge">
            共 {{ overview?.components.total ?? 0 }} 个组件
          </span>
        </div>
        <div class="card-body">
          <div class="component-stats-grid" v-if="overview?.components.by_type && Object.keys(overview.components.by_type).length">
            <div 
              class="component-type-card" 
              v-for="(stats, type) in overview.components.by_type" 
              :key="type"
            >
              <div class="type-header">
                <Icon :icon="getComponentTypeIcon(type)" class="type-icon" />
                <span class="type-name">{{ formatComponentType(type) }}</span>
              </div>
              <div class="type-stats">
                <div class="type-stat">
                  <span class="type-stat-value">{{ stats.total }}</span>
                  <span class="type-stat-label">总数</span>
                </div>
                <div class="type-stat enabled">
                  <span class="type-stat-value">{{ stats.enabled }}</span>
                  <span class="type-stat-label">启用</span>
                </div>
                <div class="type-stat disabled">
                  <span class="type-stat-value">{{ stats.disabled }}</span>
                  <span class="type-stat-label">禁用</span>
                </div>
              </div>
            </div>
          </div>
          <div v-else class="empty-state">
            <Icon icon="lucide:inbox" class="empty-icon" />
            <p>暂无组件数据</p>
          </div>
        </div>
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { Icon } from '@iconify/vue'
import { 
  getDashboardOverview, 
  getTodaySchedule, 
  getMonthlyPlans,
  type DashboardOverview,
  type ScheduleResponse,
  type MonthlyPlanResponse,
  type ScheduleActivity
} from '@/api'
import ConnectionError from '@/components/ConnectionError.vue'

const loading = ref(false)
const overview = ref<DashboardOverview | null>(null)
const schedule = ref<ScheduleResponse | null>(null)
const monthlyPlans = ref<MonthlyPlanResponse | null>(null)

// 连接错误状态
const showConnectionError = ref(false)
const connectionErrorMsg = ref('')

// 获取所有数据
async function fetchAllData() {
  loading.value = true
  showConnectionError.value = false
  
  try {
    // 并行获取所有数据
    const [overviewRes, scheduleRes, plansRes] = await Promise.all([
      getDashboardOverview(),
      getTodaySchedule(),
      getMonthlyPlans()
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
  } catch (error) {
    console.error('获取数据失败:', error)
    connectionErrorMsg.value = '请求发生错误，请检查网络连接'
    showConnectionError.value = true
  } finally {
    loading.value = false
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

// 顶部统计卡片数据
const statsData = computed(() => [
  { 
    label: '活跃插件', 
    value: overview.value?.plugins.enabled ?? '-', 
    subValue: `共 ${overview.value?.plugins.loaded ?? 0} 个`,
    icon: 'lucide:puzzle', 
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
  }
  return nameMap[type.toLowerCase()] || type
}

onMounted(() => {
  fetchAllData()
})
</script>

<style scoped>
.dashboard-home {
  display: flex;
  flex-direction: column;
  gap: 24px;
  animation: fadeIn 0.5s ease;
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
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
  gap: 20px;
}

.stat-card {
  background: var(--bg-primary);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-lg);
  padding: 20px;
  display: flex;
  align-items: center;
  gap: 16px;
  transition: all var(--transition);
}

.stat-card:hover {
  transform: translateY(-2px);
  box-shadow: var(--shadow-md);
}

.stat-icon {
  width: 48px;
  height: 48px;
  border-radius: var(--radius);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24px;
}

.stat-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.stat-value {
  font-size: 24px;
  font-weight: 700;
  color: var(--text-primary);
  letter-spacing: -0.5px;
}

.stat-label {
  font-size: 13px;
  color: var(--text-tertiary);
}

.stat-sub {
  font-size: 12px;
  color: var(--text-tertiary);
  padding: 4px 8px;
  background: var(--bg-secondary);
  border-radius: var(--radius-sm);
}

/* 卡片通用样式 */
.card {
  background: var(--bg-primary);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-lg);
  overflow: hidden;
}

.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 20px;
  border-bottom: 1px solid var(--border-color);
}

.card-title {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0;
}

.card-title svg {
  font-size: 20px;
  color: var(--primary);
}

.card-body {
  padding: 20px;
}

.refresh-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  border: none;
  background: var(--bg-secondary);
  border-radius: var(--radius);
  color: var(--text-secondary);
  cursor: pointer;
  transition: all var(--transition-fast);
}

.refresh-btn:hover:not(:disabled) {
  background: var(--bg-hover);
  color: var(--primary);
}

.refresh-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.total-badge {
  font-size: 13px;
  color: var(--text-tertiary);
  padding: 4px 12px;
  background: var(--bg-secondary);
  border-radius: var(--radius-full);
}

/* 主内容区网格 */
.content-grid {
  display: grid;
  grid-template-columns: 2fr 1fr;
  gap: 20px;
}

/* 插件统计详情 */
.stats-detail-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 16px;
}

.stats-detail-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 16px;
  background: var(--bg-secondary);
  border-radius: var(--radius);
  transition: all var(--transition-fast);
}

.stats-detail-item:hover {
  background: var(--bg-hover);
}

.detail-icon {
  width: 40px;
  height: 40px;
  border-radius: var(--radius);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 18px;
}

.detail-info {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.detail-value {
  font-size: 20px;
  font-weight: 600;
  color: var(--text-primary);
}

.detail-label {
  font-size: 12px;
  color: var(--text-tertiary);
}

/* 快捷操作 */
.quick-actions {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 12px;
}

.action-btn {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 10px;
  padding: 20px 16px;
  background: var(--bg-secondary);
  border: 1px solid var(--border-color);
  border-radius: var(--radius);
  cursor: pointer;
  transition: all var(--transition);
}

.action-btn:hover {
  background: var(--bg-hover);
  transform: translateY(-2px);
}

.action-icon {
  width: 40px;
  height: 40px;
  border-radius: var(--radius);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 20px;
}

.action-label {
  font-size: 13px;
  font-weight: 500;
  color: var(--text-secondary);
}

/* 组件统计 */
.component-stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 16px;
}

.component-type-card {
  background: var(--bg-secondary);
  border-radius: var(--radius);
  padding: 16px;
  transition: all var(--transition-fast);
}

.component-type-card:hover {
  background: var(--bg-hover);
}

.type-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 12px;
}

.type-icon {
  font-size: 18px;
  color: var(--primary);
}

.type-name {
  font-size: 14px;
  font-weight: 500;
  color: var(--text-primary);
}

.type-stats {
  display: flex;
  gap: 16px;
}

.type-stat {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 2px;
}

.type-stat-value {
  font-size: 18px;
  font-weight: 600;
  color: var(--text-primary);
}

.type-stat-label {
  font-size: 11px;
  color: var(--text-tertiary);
}

.type-stat.enabled .type-stat-value {
  color: var(--success);
}

.type-stat.disabled .type-stat-value {
  color: var(--text-tertiary);
}

/* 空状态 */
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 40px;
  color: var(--text-tertiary);
  gap: 12px;
}

.empty-state.small {
  padding: 24px;
}

.empty-state.small .empty-icon {
  font-size: 32px;
}

.empty-icon {
  font-size: 48px;
  opacity: 0.5;
}

/* 日程卡片 */
.date-badge {
  font-size: 13px;
  color: var(--primary);
  padding: 4px 12px;
  background: var(--primary-bg);
  border-radius: var(--radius-full);
  font-weight: 500;
}

.current-activity {
  background: linear-gradient(135deg, var(--primary-bg), rgba(59, 130, 246, 0.05));
  border: 1px solid var(--primary);
  border-radius: var(--radius);
  padding: 16px;
  margin-bottom: 16px;
}

.current-label {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  font-weight: 600;
  color: var(--primary);
  margin-bottom: 8px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.current-content {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.current-time {
  font-size: 13px;
  color: var(--text-tertiary);
  font-weight: 500;
}

.current-text {
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary);
}

.schedule-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
  max-height: 300px;
  overflow-y: auto;
}

.schedule-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  background: var(--bg-secondary);
  border-radius: var(--radius);
  transition: all var(--transition-fast);
}

.schedule-item:hover {
  background: var(--bg-hover);
}

.schedule-item.is-current {
  background: var(--primary-bg);
  border-left: 3px solid var(--primary);
}

.schedule-time {
  font-size: 13px;
  font-weight: 500;
  color: var(--text-tertiary);
  min-width: 100px;
}

.schedule-activity {
  font-size: 14px;
  color: var(--text-primary);
  flex: 1;
}

/* 月度计划卡片 */
.plans-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
  max-height: 300px;
  overflow-y: auto;
}

.plan-item {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  padding: 12px;
  background: var(--bg-secondary);
  border-radius: var(--radius);
  transition: all var(--transition-fast);
}

.plan-item:hover {
  background: var(--bg-hover);
}

.plan-icon {
  font-size: 16px;
  color: var(--success);
  flex-shrink: 0;
  margin-top: 2px;
}

.plan-text {
  font-size: 14px;
  color: var(--text-primary);
  line-height: 1.5;
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
  
  .quick-actions {
    grid-template-columns: 1fr;
  }
  
  .stats-detail-grid {
    grid-template-columns: 1fr;
  }
  
  .component-stats-grid {
    grid-template-columns: 1fr;
  }
}
</style>
