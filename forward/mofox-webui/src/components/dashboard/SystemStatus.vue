<template>
  <div class="system-status m3-card">
    <div class="card-header">
      <div class="header-title">
        <span class="material-symbols-rounded">monitoring</span>
        <h3>系统状态</h3>
      </div>
      <button 
        class="refresh-button" 
        :class="{ refreshing: isRefreshing }"
        @click="handleRefresh"
        title="刷新系统状态"
      >
        <span class="material-symbols-rounded">refresh</span>
      </button>
    </div>
    <div class="card-body">
      <div class="status-item">
        <div class="status-icon-container cpu">
          <span class="material-symbols-rounded">memory</span>
        </div>
        <div class="status-info">
          <div class="status-label">CPU使用率</div>
          <div class="status-value">{{ formatPercent(overview?.system.cpu_percent) }}</div>
          <div class="status-progress">
            <div class="progress-bar" :style="{ width: `${overview?.system.cpu_percent || 0}%`, backgroundColor: getCPUColor(overview?.system.cpu_percent || 0) }"></div>
          </div>
        </div>
      </div>

      <div class="status-item">
        <div class="status-icon-container memory">
          <span class="material-symbols-rounded">storage</span>
        </div>
        <div class="status-info">
          <div class="status-label">内存占用</div>
          <div class="status-value">{{ formatMemory(overview?.system.memory_usage_mb) }}</div>
          <div class="status-progress">
            <div class="progress-bar" :style="{ width: `${memoryPercent}%`, backgroundColor: getMemoryColor(memoryPercent) }"></div>
          </div>
        </div>
      </div>

      <div class="status-item">
        <div class="status-icon-container time">
          <span class="material-symbols-rounded">schedule</span>
        </div>
        <div class="status-info">
          <div class="status-label">运行时长</div>
          <div class="status-value">{{ formatUptime(overview?.system.uptime_seconds) }}</div>
        </div>
      </div>

      <div class="status-item">
        <div class="status-icon-container chat">
          <span class="material-symbols-rounded">chat</span>
        </div>
        <div class="status-info">
          <div class="status-label">聊天会话</div>
          <div class="status-value">{{ overview?.chats.total_streams || 0 }} 个</div>
          <div class="status-sub">群聊 {{ overview?.chats.group_streams || 0 }} / 私聊 {{ overview?.chats.private_streams || 0 }}</div>
        </div>
      </div>

      <div class="status-item">
        <div class="status-icon-container plugin">
          <span class="material-symbols-rounded">extension</span>
        </div>
        <div class="status-info">
          <div class="status-label">插件状态</div>
          <div class="status-value">{{ overview?.plugins.loaded || 0 }} 个</div>
          <div class="status-sub">启用 {{ overview?.plugins.enabled || 0 }} / 失败 {{ overview?.plugins.failed || 0 }}</div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, defineEmits } from 'vue'
import type { DashboardOverview } from '@/api/dashboard'

const props = defineProps<{
  overview: DashboardOverview | null
  isRefreshing?: boolean
}>()

const emit = defineEmits<{
  refresh: []
}>()

const memoryPercent = computed(() => {
  if (!props.overview || !props.overview.system.total_memory_mb) return 0
  const totalMemory = props.overview.system.total_memory_mb
  return Math.min(100, (props.overview.system.memory_usage_mb / totalMemory) * 100)
})

function handleRefresh() {
  emit('refresh')
}

function formatMemory(mb?: number): string {
  if (!mb) return '-'
  if (mb >= 1024) return `${(mb / 1024).toFixed(1)} GB`
  return `${mb.toFixed(0)} MB`
}

function formatUptime(seconds?: number): string {
  if (!seconds) return '-'
  const days = Math.floor(seconds / 86400)
  const hours = Math.floor((seconds % 86400) / 3600)
  const minutes = Math.floor((seconds % 3600) / 60)
  
  if (days > 0) return `${days}天${hours}时`
  if (hours > 0) return `${hours}时${minutes}分`
  return `${minutes}分钟`
}

function formatPercent(value?: number): string {
  if (value === undefined) return '-'
  return `${value.toFixed(1)}%`
}

function getCPUColor(percent: number): string {
  if (percent > 80) return 'var(--md-sys-color-error)'
  if (percent > 50) return 'var(--md-sys-color-tertiary)'
  return 'var(--md-sys-color-primary)'
}

function getMemoryColor(percent: number): string {
  if (percent > 85) return 'var(--md-sys-color-error)'
  if (percent > 70) return '#f59e0b'
  return 'var(--md-sys-color-secondary)'
}
</script>

<style scoped>
.system-status {
  animation: slideIn 0.5s cubic-bezier(0.2, 0, 0, 1) 0.2s backwards;
}

.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 20px;
  padding-bottom: 16px;
  border-bottom: 1px solid var(--md-sys-color-outline-variant);
}

.header-title {
  display: flex;
  align-items: center;
  gap: 12px;
}

.header-title h3 {
  font-size: 18px;
  font-weight: 600;
  color: var(--md-sys-color-on-surface);
  margin: 0;
}

.header-title .material-symbols-rounded {
  font-size: 24px;
  color: var(--md-sys-color-primary);
}

.refresh-button {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  border: none;
  background: var(--md-sys-color-surface-container-high);
  color: var(--md-sys-color-on-surface);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.2s ease;
}

.refresh-button:hover {
  background: var(--md-sys-color-surface-container-highest);
  transform: scale(1.05);
}

.refresh-button:active {
  transform: scale(0.95);
}

.refresh-button.refreshing .material-symbols-rounded {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}

.card-body {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.status-item {
  display: flex;
  align-items: flex-start;
  gap: 16px;
}

.status-icon-container {
  width: 48px;
  height: 48px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.status-icon-container.cpu {
  background: rgba(var(--md-sys-color-primary-rgb, 103, 80, 164), 0.15);
  color: var(--md-sys-color-primary);
}

.status-icon-container.memory {
  background: rgba(var(--md-sys-color-secondary-rgb, 3, 218, 197), 0.15);
  color: var(--md-sys-color-secondary);
}

.status-icon-container.time {
  background: rgba(var(--md-sys-color-tertiary-rgb, 127, 103, 190), 0.15);
  color: var(--md-sys-color-tertiary);
}

.status-icon-container.chat {
  background: rgba(16, 185, 129, 0.15);
  color: #10b981;
}

.status-icon-container.plugin {
  background: rgba(59, 130, 246, 0.15);
  color: #3b82f6;
}

.status-icon-container .material-symbols-rounded {
  font-size: 24px;
}

.status-info {
  flex: 1;
  min-width: 0;
}

.status-label {
  font-size: 13px;
  color: var(--md-sys-color-on-surface-variant);
  margin-bottom: 4px;
}

.status-value {
  font-size: 20px;
  font-weight: 700;
  color: var(--md-sys-color-on-surface);
  margin-bottom: 4px;
}

.status-sub {
  font-size: 12px;
  color: var(--md-sys-color-on-surface-variant);
  opacity: 0.7;
}

.status-progress {
  margin-top: 8px;
  height: 6px;
  background: var(--md-sys-color-surface-container-highest);
  border-radius: 3px;
  overflow: hidden;
}

.progress-bar {
  height: 100%;
  border-radius: 3px;
  transition: width 0.6s cubic-bezier(0.4, 0, 0.2, 1);
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
</style>
