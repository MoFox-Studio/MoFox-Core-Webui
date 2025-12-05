<template>
  <div class="dashboard-home">
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
          <div class="stat-trend" :class="stat.trend > 0 ? 'positive' : 'negative'">
            <Icon :icon="stat.trend > 0 ? 'lucide:trending-up' : 'lucide:trending-down'" />
            <span>{{ Math.abs(stat.trend) }}%</span>
          </div>
        </div>
      </div>
    </section>

    <!-- 主要内容区 -->
    <section class="main-section">
      <div class="content-grid">
        <!-- 活动图表 -->
        <div class="card chart-card">
          <div class="card-header">
            <h3 class="card-title">
              <Icon icon="lucide:activity" />
              活动概览
            </h3>
            <div class="card-actions">
              <button 
                v-for="period in ['日', '周', '月']" 
                :key="period"
                class="period-btn"
                :class="{ active: activePeriod === period }"
                @click="activePeriod = period"
              >
                {{ period }}
              </button>
            </div>
          </div>
          <div class="card-body">
            <div class="chart-placeholder">
              <Icon icon="lucide:bar-chart-3" class="chart-icon" />
              <p>图表数据加载中...</p>
            </div>
          </div>
        </div>

        <!-- 快捷操作 -->
        <div class="card quick-actions-card">
          <div class="card-header">
            <h3 class="card-title">
              <Icon icon="lucide:zap" />
              快捷操作
            </h3>
          </div>
          <div class="card-body">
            <div class="quick-actions">
              <button class="action-btn" v-for="action in quickActions" :key="action.label">
                <div class="action-icon" :style="{ background: action.bgColor }">
                  <Icon :icon="action.icon" :style="{ color: action.color }" />
                </div>
                <span class="action-label">{{ action.label }}</span>
              </button>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- 最近活动 -->
    <section class="activity-section">
      <div class="card">
        <div class="card-header">
          <h3 class="card-title">
            <Icon icon="lucide:clock" />
            最近活动
          </h3>
          <a href="#" class="view-all">查看全部</a>
        </div>
        <div class="card-body">
          <div class="activity-list">
            <div class="activity-item" v-for="activity in recentActivities" :key="activity.id">
              <div class="activity-icon" :style="{ background: activity.bgColor }">
                <Icon :icon="activity.icon" :style="{ color: activity.color }" />
              </div>
              <div class="activity-content">
                <p class="activity-text">{{ activity.text }}</p>
                <span class="activity-time">{{ activity.time }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { Icon } from '@iconify/vue'

const activePeriod = ref('日')

const statsData = [
  { 
    label: '今日消息', 
    value: '1,234', 
    icon: 'lucide:message-circle', 
    color: '#3b82f6', 
    bgColor: 'rgba(59, 130, 246, 0.1)',
    trend: 12
  },
  { 
    label: '活跃用户', 
    value: '256', 
    icon: 'lucide:users', 
    color: '#10b981', 
    bgColor: 'rgba(16, 185, 129, 0.1)',
    trend: 8
  },
  { 
    label: '响应时间', 
    value: '23ms', 
    icon: 'lucide:timer', 
    color: '#f59e0b', 
    bgColor: 'rgba(245, 158, 11, 0.1)',
    trend: -5
  },
  { 
    label: '运行时长', 
    value: '72h', 
    icon: 'lucide:clock', 
    color: '#8b5cf6', 
    bgColor: 'rgba(139, 92, 246, 0.1)',
    trend: 0
  },
]

const quickActions = [
  { label: '重启服务', icon: 'lucide:refresh-cw', color: '#3b82f6', bgColor: 'rgba(59, 130, 246, 0.1)' },
  { label: '查看日志', icon: 'lucide:file-text', color: '#10b981', bgColor: 'rgba(16, 185, 129, 0.1)' },
  { label: '配置管理', icon: 'lucide:settings', color: '#f59e0b', bgColor: 'rgba(245, 158, 11, 0.1)' },
  { label: '数据备份', icon: 'lucide:database', color: '#8b5cf6', bgColor: 'rgba(139, 92, 246, 0.1)' },
]

const recentActivities = [
  { id: 1, text: '用户 Alice 发送了一条消息', time: '2分钟前', icon: 'lucide:message-circle', color: '#3b82f6', bgColor: 'rgba(59, 130, 246, 0.1)' },
  { id: 2, text: '系统配置已更新', time: '15分钟前', icon: 'lucide:settings', color: '#10b981', bgColor: 'rgba(16, 185, 129, 0.1)' },
  { id: 3, text: '新用户 Bob 加入了群组', time: '1小时前', icon: 'lucide:user-plus', color: '#f59e0b', bgColor: 'rgba(245, 158, 11, 0.1)' },
  { id: 4, text: '插件 weather 已启用', time: '3小时前', icon: 'lucide:puzzle', color: '#8b5cf6', bgColor: 'rgba(139, 92, 246, 0.1)' },
]
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

.stat-trend {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 13px;
  font-weight: 500;
  padding: 4px 8px;
  border-radius: var(--radius-full);
}

.stat-trend.positive {
  color: var(--success);
  background: var(--success-bg);
}

.stat-trend.negative {
  color: var(--danger);
  background: var(--danger-bg);
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

.card-actions {
  display: flex;
  gap: 4px;
}

.period-btn {
  padding: 6px 12px;
  border-radius: var(--radius-sm);
  background: transparent;
  border: none;
  color: var(--text-tertiary);
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: all var(--transition-fast);
}

.period-btn:hover {
  background: var(--bg-hover);
  color: var(--text-secondary);
}

.period-btn.active {
  background: var(--primary-bg);
  color: var(--primary);
}

.card-body {
  padding: 20px;
}

.view-all {
  font-size: 14px;
  color: var(--primary);
  font-weight: 500;
}

.view-all:hover {
  text-decoration: underline;
}

/* 主内容区网格 */
.content-grid {
  display: grid;
  grid-template-columns: 2fr 1fr;
  gap: 20px;
}

/* 图表区占位 */
.chart-placeholder {
  height: 300px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: var(--text-tertiary);
  gap: 12px;
}

.chart-icon {
  font-size: 48px;
  opacity: 0.5;
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

/* 活动列表 */
.activity-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.activity-item {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 12px;
  border-radius: var(--radius);
  transition: background var(--transition-fast);
}

.activity-item:hover {
  background: var(--bg-secondary);
}

.activity-icon {
  width: 40px;
  height: 40px;
  min-width: 40px;
  border-radius: var(--radius);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 18px;
}

.activity-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.activity-text {
  font-size: 14px;
  color: var(--text-primary);
  margin: 0;
}

.activity-time {
  font-size: 12px;
  color: var(--text-tertiary);
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
}
</style>
