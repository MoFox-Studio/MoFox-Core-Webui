<template>
  <Teleport to="body">
    <Transition name="modal">
      <div v-if="visible" class="modal-overlay" @click.self="handleClose">
        <div class="m3-dialog modal-container">
          <div class="modal-icon">
            <span class="material-symbols-rounded">wifi_off</span>
          </div>
          <h2 class="modal-title">连接失败</h2>
          <p class="modal-message">
            无法连接到后端服务器<br>
            <span class="modal-detail">{{ message || '请检查服务是否正常运行' }}</span>
          </p>
          <div class="modal-actions">
            <button class="m3-button filled" @click="handleRetry">
              <span class="material-symbols-rounded">refresh</span>
              重试连接
            </button>
            <button class="m3-button text" @click="handleClose">
              关闭
            </button>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup lang="ts">
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
  background: var(--md-sys-color-surface-container-high);
  border-radius: 28px;
  padding: 24px;
  max-width: 320px;
  width: 90%;
  text-align: center;
  box-shadow: var(--md-sys-elevation-3);
  display: flex;
  flex-direction: column;
  align-items: center;
}

.modal-icon {
  width: 48px;
  height: 48px;
  margin-bottom: 16px;
  color: var(--md-sys-color-error);
  font-size: 48px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.modal-icon .material-symbols-rounded {
  font-size: 48px;
}

.modal-title {
  font-size: 24px;
  font-weight: 400;
  color: var(--md-sys-color-on-surface);
  margin: 0 0 16px;
}

.modal-message {
  font-size: 14px;
  color: var(--md-sys-color-on-surface-variant);
  margin: 0 0 24px;
  line-height: 1.5;
}

.modal-detail {
  font-size: 12px;
  color: var(--md-sys-color-error);
  margin-top: 4px;
  display: block;
}

.modal-actions {
  display: flex;
  flex-direction: column;
  gap: 12px;
  width: 100%;
}

.m3-button {
  height: 40px;
  border-radius: 20px;
  padding: 0 24px;
  font-size: 14px;
  font-weight: 500;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  cursor: pointer;
  transition: all 0.2s;
  border: none;
  width: 100%;
}

.m3-button.filled {
  background: var(--md-sys-color-primary);
  color: var(--md-sys-color-on-primary);
}

.m3-button.filled:hover {
  box-shadow: var(--md-sys-elevation-1);
  background: linear-gradient(rgba(255, 255, 255, 0.08), rgba(255, 255, 255, 0.08)), var(--md-sys-color-primary);
}

.m3-button.text {
  background: transparent;
  color: var(--md-sys-color-primary);
}

.m3-button.text:hover {
  background: var(--md-sys-color-surface-container-highest);
}

/* 过渡动画 */
.modal-enter-active,
.modal-leave-active {
  transition: all 0.2s cubic-bezier(0.2, 0, 0, 1);
}

.modal-enter-from,
.modal-leave-to {
  opacity: 0;
}

.modal-enter-from .modal-container,
.modal-leave-to .modal-container {
  transform: scale(0.9);
  opacity: 0;
}
</style>
