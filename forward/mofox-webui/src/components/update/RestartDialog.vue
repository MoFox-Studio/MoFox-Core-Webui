<!--
  @file RestartDialog.vue
  @description 重启提示弹窗组件
  
  功能说明：
  1. 更新完成后提示用户重启
  2. 显示更新日志
  3. 提供立即重启和稍后重启选项
-->
<template>
  <Teleport to="body">
    <Transition name="fade">
      <div v-if="modelValue" class="dialog-overlay" @click.self="handleLater">
        <Transition name="scale">
          <div v-if="modelValue" class="dialog-content m3-card">
            <!-- 头部 -->
            <div class="dialog-header">
              <div class="dialog-icon" :class="updateTypeClass">
                <span class="material-symbols-rounded">{{ updateTypeIcon }}</span>
              </div>
              <h2>{{ title }}</h2>
            </div>
            
            <!-- 内容 -->
            <div class="dialog-body">
              <p class="dialog-message">{{ message }}</p>
              
              <!-- 更新日志 -->
              <div v-if="changelog && changelog.length > 0" class="changelog-section">
                <h4>更新内容:</h4>
                <ul class="changelog-list">
                  <li v-for="(log, index) in changelog.slice(0, 5)" :key="index">
                    {{ log }}
                  </li>
                </ul>
              </div>
              
              <!-- 提示信息 -->
              <div class="tip-section">
                <span class="material-symbols-rounded">info</span>
                <span>{{ tipMessage }}</span>
              </div>
            </div>
            
            <!-- 底部按钮 -->
            <div class="dialog-footer">
              <button class="m3-button text" @click="handleLater">
                稍后重启
              </button>
              <button class="m3-button filled" @click="handleRestart">
                <span class="material-symbols-rounded">restart_alt</span>
                <span>立即重启</span>
              </button>
            </div>
          </div>
        </Transition>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup lang="ts">
import { computed } from 'vue'

// Props
const props = withDefaults(defineProps<{
  modelValue: boolean
  updateType: 'main' | 'ui' | 'both'
  changelog?: string[]
}>(), {
  updateType: 'main',
  changelog: () => []
})

// Emits
const emit = defineEmits<{
  (e: 'update:modelValue', value: boolean): void
  (e: 'restart'): void
  (e: 'later'): void
}>()

// 计算属性
const updateTypeClass = computed(() => {
  return {
    main: 'type-main',
    ui: 'type-ui',
    both: 'type-both'
  }[props.updateType]
})

const updateTypeIcon = computed(() => {
  return {
    main: 'smart_toy',
    ui: 'web',
    both: 'system_update'
  }[props.updateType]
})

const title = computed(() => {
  return {
    main: '主程序更新完成',
    ui: 'UI 更新完成',
    both: '全部更新完成'
  }[props.updateType]
})

const message = computed(() => {
  return {
    main: '主程序已更新成功，需要重启才能生效。',
    ui: 'WebUI 已更新成功，需要刷新页面才能生效。',
    both: '主程序和 WebUI 都已更新成功，需要重启才能生效。'
  }[props.updateType]
})

const tipMessage = computed(() => {
  if (props.updateType === 'ui') {
    return '刷新页面后将加载新版本的 WebUI'
  }
  return '重启后新功能将生效，当前的连接会暂时中断'
})

// 方法
function handleRestart() {
  emit('restart')
  emit('update:modelValue', false)
}

function handleLater() {
  emit('later')
  emit('update:modelValue', false)
}
</script>

<style scoped>
.dialog-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.6);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 2000;
  backdrop-filter: blur(4px);
}

.dialog-content {
  width: 90%;
  max-width: 420px;
  padding: 24px;
  background: var(--md-sys-color-surface-container-high);
  border-radius: 28px;
  box-shadow: var(--md-sys-elevation-3);
}

.dialog-header {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 16px;
  margin-bottom: 20px;
  text-align: center;
}

.dialog-icon {
  width: 64px;
  height: 64px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 20px;
}

.dialog-icon .material-symbols-rounded {
  font-size: 36px;
}

.dialog-icon.type-main {
  background: var(--md-sys-color-primary-container);
  color: var(--md-sys-color-on-primary-container);
}

.dialog-icon.type-ui {
  background: var(--md-sys-color-secondary-container);
  color: var(--md-sys-color-on-secondary-container);
}

.dialog-icon.type-both {
  background: var(--md-sys-color-tertiary-container);
  color: var(--md-sys-color-on-tertiary-container);
}

.dialog-header h2 {
  margin: 0;
  font-size: 20px;
  font-weight: 500;
  color: var(--md-sys-color-on-surface);
}

.dialog-body {
  margin-bottom: 24px;
}

.dialog-message {
  margin: 0 0 16px;
  color: var(--md-sys-color-on-surface-variant);
  text-align: center;
  line-height: 1.5;
}

.changelog-section {
  margin-bottom: 16px;
  padding: 12px;
  background: var(--md-sys-color-surface-container);
  border-radius: 12px;
}

.changelog-section h4 {
  margin: 0 0 8px;
  font-size: 14px;
  font-weight: 500;
  color: var(--md-sys-color-on-surface);
}

.changelog-list {
  margin: 0;
  padding-left: 20px;
}

.changelog-list li {
  font-size: 13px;
  color: var(--md-sys-color-on-surface-variant);
  margin-bottom: 4px;
}

.tip-section {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  padding: 12px;
  background: var(--md-sys-color-surface-container-low);
  border-radius: 8px;
  font-size: 13px;
  color: var(--md-sys-color-on-surface-variant);
}

.tip-section .material-symbols-rounded {
  font-size: 18px;
  color: var(--md-sys-color-primary);
  flex-shrink: 0;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
}

/* 按钮样式 */
.m3-button {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 10px 24px;
  border: none;
  border-radius: 20px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.m3-button.filled {
  background: var(--md-sys-color-primary);
  color: var(--md-sys-color-on-primary);
}

.m3-button.filled:hover {
  box-shadow: var(--md-sys-elevation-1);
}

.m3-button.text {
  background: transparent;
  color: var(--md-sys-color-primary);
}

.m3-button.text:hover {
  background: var(--md-sys-color-primary-container);
}

/* 动画 */
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

.scale-enter-active,
.scale-leave-active {
  transition: all 0.3s cubic-bezier(0.2, 0, 0, 1);
}

.scale-enter-from,
.scale-leave-to {
  opacity: 0;
  transform: scale(0.9);
}
</style>
