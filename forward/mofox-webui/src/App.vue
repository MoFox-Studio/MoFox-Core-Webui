<template>
  <router-view />
  
  <!-- 全局 Toast 提示 -->
  <div v-if="toast.show" :class="['global-toast', toast.type]">
    <Icon :icon="toast.type === 'success' ? 'lucide:check-circle' : 'lucide:alert-circle'" />
    {{ toast.message }}
  </div>
</template>

<script setup lang="ts">
import { onMounted, onUnmounted, ref } from 'vue'
import { Icon } from '@iconify/vue'
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
/* 全局 Toast */
.global-toast {
  position: fixed;
  bottom: 24px;
  right: 24px;
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 16px 24px;
  background: var(--bg-primary);
  border-radius: var(--radius);
  box-shadow: var(--shadow-lg);
  font-size: 15px;
  font-weight: 600;
  z-index: 9999;
  animation: slideIn 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  border: 1px solid var(--border-color);
}

.global-toast.success {
  border-left: 4px solid var(--success);
  color: var(--success);
}

.global-toast.error {
  border-left: 4px solid var(--danger);
  color: var(--danger);
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

@media (max-width: 768px) {
  .global-toast {
    bottom: 20px;
    right: 20px;
    left: 20px;
    justify-content: center;
  }
}
</style>
