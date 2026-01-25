<template>
  <div class="today-schedule m3-card">
    <div class="card-header">
      <div class="header-title">
        <span class="material-symbols-rounded">{{ viewMode === 'schedule' ? 'calendar_today' : 'event_note' }}</span>
        <h3>{{ viewMode === 'schedule' ? '今日日程' : '月度计划' }}</h3>
      </div>
      <div class="header-actions">
        <span v-if="viewMode === 'schedule'" class="m3-badge secondary">{{ schedule?.date || '-' }}</span>
        <span v-else class="m3-badge secondary">{{ monthlyPlans?.month || '-' }}</span>
        <button 
          class="toggle-button"
          @click="toggleView"
          :title="viewMode === 'schedule' ? '切换到月度计划' : '切换到今日日程'"
        >
          <span class="material-symbols-rounded">swap_horiz</span>
        </button>
      </div>
    </div>
    <div class="card-body">
      <!-- 日程视图 -->
      <template v-if="viewMode === 'schedule'">
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
            v-for="(item, index) in schedule.activities"
            :key="index"
            class="schedule-item"
            :class="{ 'is-current': isCurrentActivity(item) }"
          >
            <div class="item-time">{{ item.time_range }}</div>
            <div class="item-content">{{ item.activity }}</div>
          </div>
        </div>

        <!-- 空状态 -->
        <div v-else class="empty-state">
          <span class="material-symbols-rounded empty-icon">event_busy</span>
          <p>暂无日程安排</p>
        </div>
      </template>

      <!-- 月度计划视图 -->
      <template v-else>
        <div v-if="monthlyPlans?.plans?.length" class="plans-list">
          <div
            v-for="(plan, index) in monthlyPlans.plans"
            :key="index"
            class="plan-item"
          >
            <span class="plan-index">{{ index + 1 }}</span>
            <span class="plan-text">{{ plan }}</span>
          </div>
        </div>

        <!-- 空状态 -->
        <div v-else class="empty-state">
          <span class="material-symbols-rounded empty-icon">note_add</span>
          <p>暂无月度计划</p>
        </div>

        <!-- 计划总数 -->
        <div v-if="monthlyPlans?.total" class="plans-footer">
          <span class="plans-count">共 {{ monthlyPlans.total }} 条计划</span>
        </div>
      </template>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import type { ScheduleResponse, ScheduleActivity, MonthlyPlanResponse } from '@/api/dashboard'

const props = defineProps<{
  schedule: ScheduleResponse | null
  monthlyPlans: MonthlyPlanResponse | null
}>()

const viewMode = ref<'schedule' | 'plans'>('schedule')

function toggleView() {
  viewMode.value = viewMode.value === 'schedule' ? 'plans' : 'schedule'
}

function isCurrentActivity(item: ScheduleActivity): boolean {
  if (!props.schedule?.current_activity) return false
  return item.time_range === props.schedule.current_activity.time_range
}
</script>

<style scoped>
.today-schedule {
  animation: slideIn 0.5s cubic-bezier(0.2, 0, 0, 1) 0.3s backwards;
  display: flex;
  flex-direction: column;
  height: 100%;
  min-height: 500px;
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

.header-actions {
  display: flex;
  align-items: center;
  gap: 12px;
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

.toggle-button {
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

.toggle-button:hover {
  background: var(--md-sys-color-primary-container);
  color: var(--md-sys-color-on-primary-container);
  transform: scale(1.05);
}

.toggle-button:active {
  transform: scale(0.95);
}

.card-body {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.current-activity {
  background: var(--md-sys-color-primary-container);
  color: var(--md-sys-color-on-primary-container);
  border-radius: 12px;
  padding: 16px;
  margin-bottom: 20px;
  animation: pulse 2s ease-in-out infinite;
}

@keyframes pulse {
  0%, 100% {
    box-shadow: 0 0 0 0 rgba(var(--md-sys-color-primary-rgb, 103, 80, 164), 0.4);
  }
  50% {
    box-shadow: 0 0 0 8px rgba(var(--md-sys-color-primary-rgb, 103, 80, 164), 0);
  }
}

.activity-label {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
  font-weight: 600;
  margin-bottom: 8px;
  opacity: 0.9;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.activity-label .material-symbols-rounded {
  font-size: 18px;
}

.activity-content {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.activity-time {
  font-size: 14px;
  opacity: 0.9;
  font-weight: 500;
}

.activity-text {
  font-size: 18px;
  font-weight: 600;
}

.schedule-list {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 12px;
  overflow-y: auto;
  padding-right: 8px;
  min-height: 0;
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
  transition: all 0.3s ease;
}

.schedule-item:hover {
  background: var(--md-sys-color-surface-container-high);
  transform: translateX(4px);
}

.schedule-item.is-current {
  background: var(--md-sys-color-surface-container-highest);
  border-left-color: var(--md-sys-color-primary);
  box-shadow: var(--md-sys-elevation-1);
}

.item-time {
  width: 100px;
  font-size: 13px;
  color: var(--md-sys-color-on-surface-variant);
  font-variant-numeric: tabular-nums;
  font-weight: 500;
}

.item-content {
  flex: 1;
  font-size: 14px;
  color: var(--md-sys-color-on-surface);
}

.empty-state {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 12px;
  opacity: 0.5;
}

.empty-icon {
  font-size: 48px;
  color: var(--md-sys-color-on-surface-variant);
}

.empty-state p {
  margin: 0;
  font-size: 14px;
  color: var(--md-sys-color-on-surface-variant);
}

.plans-list {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 12px;
  overflow-y: auto;
  padding-right: 8px;
  min-height: 0;
}

.plans-list::-webkit-scrollbar {
  width: 6px;
}

.plans-list::-webkit-scrollbar-track {
  background: transparent;
}

.plans-list::-webkit-scrollbar-thumb {
  background-color: var(--md-sys-color-outline-variant);
  border-radius: 3px;
}

.plan-item {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 12px;
  border-radius: 8px;
  background: var(--md-sys-color-surface-container-low);
  transition: all 0.3s ease;
}

.plan-item:hover {
  background: var(--md-sys-color-surface-container-high);
  transform: translateX(4px);
}

.plan-index {
  flex-shrink: 0;
  width: 24px;
  height: 24px;
  border-radius: 50%;
  background: var(--md-sys-color-primary-container);
  color: var(--md-sys-color-on-primary-container);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  font-weight: 600;
}

.plan-text {
  flex: 1;
  font-size: 14px;
  color: var(--md-sys-color-on-surface);
  line-height: 1.5;
}

.plans-footer {
  margin-top: 16px;
  padding-top: 16px;
  border-top: 1px solid var(--md-sys-color-outline-variant);
  text-align: center;
}

.plans-count {
  font-size: 13px;
  color: var(--md-sys-color-on-surface-variant);
  font-weight: 500;
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
