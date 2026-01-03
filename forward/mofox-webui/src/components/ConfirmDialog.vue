<template>
  <teleport to="body">
    <transition name="dialog-fade">
      <div v-if="visible" class="dialog-overlay" @click="handleOverlayClick">
        <div class="dialog-container" @click.stop>
          <div class="dialog-header">
            <div class="dialog-icon" :class="iconClass">
              <Icon :icon="iconName" />
            </div>
            <h3 class="dialog-title">{{ title }}</h3>
          </div>
          
          <div class="dialog-content">
            <p v-for="(line, index) in messageLines" :key="index" class="dialog-message">
              {{ line }}
            </p>
          </div>
          
          <div class="dialog-footer">
            <button 
              v-if="showCancel" 
              class="dialog-button cancel-button" 
              @click="handleCancel"
            >
              {{ cancelText }}
            </button>
            <button 
              class="dialog-button confirm-button" 
              :class="confirmButtonClass"
              @click="handleConfirm"
            >
              {{ confirmText }}
            </button>
          </div>
        </div>
      </div>
    </transition>
  </teleport>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { Icon } from '@iconify/vue'

export interface ConfirmDialogProps {
  visible: boolean
  title?: string
  message: string
  type?: 'info' | 'success' | 'warning' | 'danger'
  showCancel?: boolean
  confirmText?: string
  cancelText?: string
}

const props = withDefaults(defineProps<ConfirmDialogProps>(), {
  title: '提示',
  type: 'info',
  showCancel: true,
  confirmText: '确定',
  cancelText: '取消'
})

const emit = defineEmits<{
  confirm: []
  cancel: []
  'update:visible': [value: boolean]
}>()

const messageLines = computed(() => {
  return props.message.split('\n').filter(line => line.trim())
})

const iconName = computed(() => {
  const icons = {
    info: 'lucide:info',
    success: 'lucide:check-circle',
    warning: 'lucide:alert-triangle',
    danger: 'lucide:alert-circle'
  }
  return icons[props.type]
})

const iconClass = computed(() => `icon-${props.type}`)

const confirmButtonClass = computed(() => {
  const classes = {
    info: 'primary',
    success: 'success',
    warning: 'warning',
    danger: 'danger'
  }
  return classes[props.type]
})

const handleConfirm = () => {
  emit('confirm')
  emit('update:visible', false)
}

const handleCancel = () => {
  emit('cancel')
  emit('update:visible', false)
}

const handleOverlayClick = () => {
  if (props.showCancel) {
    handleCancel()
  }
}
</script>

<style scoped>
.dialog-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  backdrop-filter: blur(4px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 9999;
  padding: 20px;
}

.dialog-container {
  background: var(--bg-primary);
  border-radius: 12px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
  max-width: 420px;
  width: 100%;
  overflow: visible;
  max-height: calc(100vh - 40px);
  display: flex;
  flex-direction: column;
  animation: dialog-bounce 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);
}

@keyframes dialog-bounce {
  0% {
    transform: scale(0.9);
    opacity: 0;
  }
  100% {
    transform: scale(1);
    opacity: 1;
  }
}

.dialog-header {
  padding: 24px 24px 16px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
}

.dialog-icon {
  width: 56px;
  height: 56px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 28px;
}

.icon-info {
  background: var(--md-sys-color-primary-container);
  color: var(--md-sys-color-on-primary-container);
}

.icon-success {
  background: var(--md-sys-color-tertiary-container);
  color: var(--md-sys-color-on-tertiary-container);
}

.icon-warning {
  background: var(--md-sys-color-secondary-container);
  color: var(--md-sys-color-on-secondary-container);
}

.icon-danger {
  background: var(--md-sys-color-error-container);
  color: var(--md-sys-color-on-error-container);
}

.dialog-title {
  font-size: 20px;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0;
  text-align: center;
}

.dialog-content {
  padding: 0 24px 24px;
  display: flex;
  flex-direction: column;
  gap: 8px;
  overflow-y: auto;
  flex-shrink: 1;
}

.dialog-message {
  font-size: 14px;
  color: var(--text-secondary);
  line-height: 1.6;
  margin: 0;
  text-align: center;
}

.dialog-footer {
  padding: 16px 24px 24px;
  display: flex;
  gap: 12px;
  justify-content: center;
  flex-shrink: 0;
}

.dialog-button {
  flex: 1;
  padding: 12px 24px;
  border: none;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
  min-width: 100px;
}

.cancel-button {
  background: var(--bg-tertiary);
  color: var(--text-secondary);
  border: 1px solid var(--border-color);
}

.cancel-button:hover {
  background: var(--bg-secondary);
  border-color: var(--text-tertiary);
}

.confirm-button {
  color: white;
}

.confirm-button.primary {
  background: var(--md-sys-color-primary);
}

.confirm-button.primary:hover {
  background: var(--md-sys-color-primary);
  filter: brightness(0.9);
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(103, 80, 164, 0.3);
}

.confirm-button.success {
  background: var(--md-sys-color-tertiary);
}

.confirm-button.success:hover {
  background: var(--md-sys-color-tertiary);
  filter: brightness(0.9);
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(125, 82, 96, 0.3);
}

.confirm-button.warning {
  background: var(--md-sys-color-secondary);
}

.confirm-button.warning:hover {
  background: var(--md-sys-color-secondary);
  filter: brightness(0.9);
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(98, 91, 113, 0.3);
}

.confirm-button.danger {
  background: var(--md-sys-color-error);
}

.confirm-button.danger:hover {
  background: var(--md-sys-color-error);
  filter: brightness(0.9);
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(179, 38, 30, 0.3);
}

/* 过渡动画 */
.dialog-fade-enter-active,
.dialog-fade-leave-active {
  transition: opacity 0.3s;
}

.dialog-fade-enter-from,
.dialog-fade-leave-to {
  opacity: 0;
}

.dialog-fade-enter-active .dialog-container {
  animation: dialog-bounce 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);
}

.dialog-fade-leave-active .dialog-container {
  animation: dialog-bounce 0.2s cubic-bezier(0.34, 1.56, 0.64, 1) reverse;
}

/* 响应式 */
@media (max-width: 768px) {
  .dialog-container {
    max-width: 90%;
  }
  
  .dialog-footer {
    flex-direction: column-reverse;
  }
  
  .dialog-button {
    width: 100%;
  }
}
</style>
