<template>
  <Transition name="pop">
    <div 
      v-if="uiStore.isDocOpen"
      class="floating-doc"
      :style="{ left: x + 'px', top: y + 'px', width: width + 'px', height: height + 'px' }"
      ref="windowRef"
    >
      <div class="doc-header" @mousedown="startDrag">
        <div class="drag-handle">
          <span class="material-symbols-rounded drag-icon">drag_indicator</span>
          <span class="title">官方文档</span>
        </div>
        <div class="actions">
          <button class="action-btn" @click="openInNewTab" title="在新窗口打开">
            <span class="material-symbols-rounded">open_in_new</span>
          </button>
          <button class="action-btn close-btn" @click="uiStore.closeDoc" title="关闭">
            <span class="material-symbols-rounded">close</span>
          </button>
        </div>
      </div>
      <div class="doc-content">
        <iframe src="https://docs.mofox-sama.com/" frameborder="0"></iframe>
        <!-- 遮罩层，防止拖拽时鼠标事件被 iframe 捕获 -->
        <div v-if="isDragging || isResizing" class="iframe-mask"></div>
      </div>
      <!-- 调整大小的手柄 -->
      <div class="resize-handle" @mousedown.stop="startResize">
        <span class="material-symbols-rounded">drag_handle</span>
      </div>
    </div>
  </Transition>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useUIStore } from '@/stores/ui'

const uiStore = useUIStore()
const windowRef = ref<HTMLElement | null>(null)

// 初始位置和大小
const x = ref(window.innerWidth - 450)
const y = ref(80)
const width = ref(400)
const height = ref(600)

const isDragging = ref(false)
const isResizing = ref(false)

// 拖拽相关变量
let startX = 0
let startY = 0
let initialLeft = 0
let initialTop = 0

// 调整大小相关变量
let initialWidth = 0
let initialHeight = 0

const startDrag = (e: MouseEvent) => {
  // 如果点击的是按钮，不触发拖拽
  if ((e.target as HTMLElement).closest('.action-btn')) return

  isDragging.value = true
  startX = e.clientX
  startY = e.clientY
  initialLeft = x.value
  initialTop = y.value
  
  document.addEventListener('mousemove', onDrag)
  document.addEventListener('mouseup', stopDrag)
}

const onDrag = (e: MouseEvent) => {
  if (!isDragging.value) return
  const dx = e.clientX - startX
  const dy = e.clientY - startY
  
  const newX = initialLeft + dx
  const newY = initialTop + dy
  
  // 限制在屏幕范围内
  const maxX = window.innerWidth - width.value
  const maxY = window.innerHeight - height.value
  
  x.value = Math.max(0, Math.min(newX, maxX))
  y.value = Math.max(0, Math.min(newY, maxY))
}

const stopDrag = () => {
  isDragging.value = false
  document.removeEventListener('mousemove', onDrag)
  document.removeEventListener('mouseup', stopDrag)
}

const startResize = (e: MouseEvent) => {
  isResizing.value = true
  startX = e.clientX
  startY = e.clientY
  initialWidth = width.value
  initialHeight = height.value
  
  document.addEventListener('mousemove', onResize)
  document.addEventListener('mouseup', stopResize)
}

const onResize = (e: MouseEvent) => {
  if (!isResizing.value) return
  const dx = e.clientX - startX
  const dy = e.clientY - startY
  
  width.value = Math.max(300, initialWidth + dx)
  height.value = Math.max(200, initialHeight + dy)
}

const stopResize = () => {
  isResizing.value = false
  document.removeEventListener('mousemove', onResize)
  document.removeEventListener('mouseup', stopResize)
}

const openInNewTab = () => {
  window.open('https://docs.mofox-sama.com/', '_blank')
  uiStore.closeDoc()
}

onMounted(() => {
  // 简单的响应式初始位置
  if (window.innerWidth < 800) {
    x.value = 20
    width.value = window.innerWidth - 40
  } else {
    x.value = window.innerWidth - 450
  }
})
</script>

<style scoped>
.floating-doc {
  position: fixed;
  will-change: width, height, left, top;
  background: var(--md-sys-color-surface);
  border: 1px solid var(--md-sys-color-outline-variant);
  border-radius: 16px;
  box-shadow: var(--md-sys-elevation-3);
  display: flex;
  flex-direction: column;
  z-index: 1000;
  overflow: hidden;
}

.doc-header {
  height: 48px;
  background: var(--md-sys-color-surface-container);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 8px 0 16px;
  cursor: move;
  user-select: none;
  border-bottom: 1px solid var(--md-sys-color-outline-variant);
}

.drag-handle {
  display: flex;
  align-items: center;
  gap: 8px;
  color: var(--md-sys-color-on-surface);
  font-weight: 500;
}

.drag-icon {
  font-size: 20px;
  color: var(--md-sys-color-on-surface-variant);
}

.actions {
  display: flex;
  gap: 4px;
}

.action-btn {
  width: 32px;
  height: 32px;
  border: none;
  background: transparent;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  color: var(--md-sys-color-on-surface-variant);
  transition: all 0.2s;
}

.action-btn:hover {
  background: var(--md-sys-color-surface-container-high);
  color: var(--md-sys-color-on-surface);
}

.action-btn.close-btn:hover {
  background: var(--md-sys-color-error-container);
  color: var(--md-sys-color-on-error-container);
}

.action-btn span {
  font-size: 20px;
}

.doc-content {
  flex: 1;
  position: relative;
  background: white;
  overflow: hidden;
}

iframe {
  width: 100%;
  height: 100%;
  border: none;
}

.iframe-mask {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  z-index: 1;
  background: transparent;
}

.resize-handle {
  position: absolute;
  bottom: 0;
  right: 0;
  width: 20px;
  height: 20px;
  cursor: nwse-resize;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--md-sys-color-outline);
  background: var(--md-sys-color-surface-container-low);
  border-top-left-radius: 8px;
  z-index: 2;
}

.resize-handle span {
  font-size: 14px;
  transform: rotate(45deg);
}

/* Transition */
.pop-enter-active,
.pop-leave-active {
  transition: all 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);
}

.pop-enter-from,
.pop-leave-to {
  opacity: 0;
  transform: scale(0.9) translateY(20px);
}
</style>
