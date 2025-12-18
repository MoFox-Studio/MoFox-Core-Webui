<template>
  <router-view />
  
  <!-- 全局 Toast 提示 -->
  <Transition name="toast">
    <div v-if="toast.show" :class="['m3-snackbar', toast.type]">
      <span class="material-symbols-rounded icon">
        {{ toast.type === 'success' ? 'check_circle' : 'error' }}
      </span>
      <span class="message">{{ toast.message }}</span>
    </div>
  </Transition>
</template>

<script setup lang="ts">
import { onMounted, onUnmounted, ref } from 'vue'
import { useThemeStore } from '@/stores/theme'
import { startUpdateChecker, stopUpdateChecker, setToastCallback } from '@/utils/updateChecker'

// 初始化主题
useThemeStore()

// Toast 状态
const toast = ref({ show: false, message: '', type: 'success' as 'success' | 'error' })

// Toast 显示函数
function showToast(message: string, type: 'success' | 'error') {
  toast.value = { show: true, message, type }
  setTimeout(() => {
    toast.value.show = false
  }, 3000)
}

// 启动时设置 Toast 回调并启动更新检查器
onMounted(() => {
  setToastCallback(showToast)
  startUpdateChecker()
})

// 卸载时停止更新检查器
onUnmounted(() => {
  stopUpdateChecker()
})
</script>

<style scoped>
/* 全局 Toast (M3 Snackbar 风格) */
.m3-snackbar {
  position: fixed;
  bottom: 24px;
  right: 24px;
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 14px 16px;
  background: var(--md-sys-color-inverse-surface);
  color: var(--md-sys-color-inverse-on-surface);
  border-radius: 4px;
  box-shadow: var(--md-sys-elevation-3);
  font-size: 14px;
  line-height: 20px;
  z-index: 9999;
  min-width: 288px;
  max-width: 600px;
}

.m3-snackbar.success .icon {
  color: #a5d6a7; /* Light green for success on dark inverse surface */
}

.m3-snackbar.error .icon {
  color: #ef9a9a; /* Light red for error on dark inverse surface */
}

.icon {
  font-size: 20px;
}

.message {
  flex: 1;
}

/* 动画 */
.toast-enter-active,
.toast-leave-active {
  transition: all 0.3s cubic-bezier(0.2, 0, 0, 1);
}

.toast-enter-from,
.toast-leave-to {
  opacity: 0;
  transform: translateY(20px);
}

@media (max-width: 768px) {
  .m3-snackbar {
    bottom: 12px;
    right: 12px;
    left: 12px;
    min-width: auto;
  }
}
</style>
