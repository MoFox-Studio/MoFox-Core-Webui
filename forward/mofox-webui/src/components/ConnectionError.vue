<template>
  <Teleport to="body">
    <Transition name="modal">
      <div v-if="visible" class="modal-overlay" @click.self="handleClose">
        <div class="modal-container">
          <div class="modal-icon">
            <Icon icon="lucide:wifi-off" />
          </div>
          <h2 class="modal-title">连接失败</h2>
          <p class="modal-message">
            无法连接到后端服务器<br>
            <span class="modal-detail">{{ message || '请检查服务是否正常运行' }}</span>
          </p>
          <div class="modal-actions">
            <button class="btn-retry" @click="handleRetry">
              <Icon icon="lucide:refresh-cw" />
              重试连接
            </button>
            <button class="btn-close" @click="handleClose">
              关闭
            </button>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup lang="ts">
import { Icon } from '@iconify/vue'

interface Props {
  visible: boolean
  message?: string
}

interface Emits {
  (e: 'close'): void
  (e: 'retry'): void
}

defineProps<Props>()
const emit = defineEmits<Emits>()

function handleClose() {
  emit('close')
}

function handleRetry() {
  emit('retry')
}
</script>

<style scoped>
.modal-overlay {
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
}

.modal-container {
  background: var(--bg-primary);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-lg);
  padding: 32px;
  max-width: 400px;
  width: 90%;
  text-align: center;
  box-shadow: var(--shadow-lg);
}

.modal-icon {
  width: 64px;
  height: 64px;
  margin: 0 auto 20px;
  background: rgba(239, 68, 68, 0.1);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 32px;
  color: #ef4444;
}

.modal-title {
  font-size: 20px;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0 0 12px;
}

.modal-message {
  font-size: 14px;
  color: var(--text-secondary);
  margin: 0 0 24px;
  line-height: 1.6;
}

.modal-detail {
  font-size: 12px;
  color: var(--text-tertiary);
}

.modal-actions {
  display: flex;
  gap: 12px;
  justify-content: center;
}

.btn-retry {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 20px;
  background: var(--primary);
  color: white;
  border: none;
  border-radius: var(--radius);
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all var(--transition-fast);
}

.btn-retry:hover {
  background: var(--primary-hover);
  transform: translateY(-1px);
}

.btn-close {
  padding: 10px 20px;
  background: var(--bg-secondary);
  color: var(--text-secondary);
  border: 1px solid var(--border-color);
  border-radius: var(--radius);
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all var(--transition-fast);
}

.btn-close:hover {
  background: var(--bg-hover);
}

/* 过渡动画 */
.modal-enter-active,
.modal-leave-active {
  transition: all 0.3s ease;
}

.modal-enter-from,
.modal-leave-to {
  opacity: 0;
}

.modal-enter-from .modal-container,
.modal-leave-to .modal-container {
  transform: scale(0.9);
}
</style>
