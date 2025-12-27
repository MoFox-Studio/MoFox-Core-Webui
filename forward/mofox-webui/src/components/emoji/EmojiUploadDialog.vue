<template>
  <Teleport to="body">
    <Transition name="dialog">
      <div v-if="modelValue" class="dialog-overlay" @click="handleClose">
        <div class="dialog-container" @click.stop>
          <div class="dialog-header">
            <h2>上传表情包</h2>
            <button class="close-button" @click="handleClose">
              <span class="material-symbols-rounded">close</span>
            </button>
          </div>

          <div class="dialog-content">
            <!-- 拖拽上传区域 -->
            <div
              class="upload-area"
              :class="{ 'drag-over': isDragOver }"
              @drop.prevent="handleDrop"
              @dragover.prevent="isDragOver = true"
              @dragleave.prevent="isDragOver = false"
              @click="triggerFileInput"
            >
              <span class="material-symbols-rounded upload-icon">cloud_upload</span>
              <p class="upload-text">拖拽文件到此处或点击选择</p>
              <p class="upload-hint">支持 PNG, JPG, GIF, WEBP 格式</p>
              <input
                ref="fileInput"
                type="file"
                multiple
                accept="image/png,image/jpeg,image/gif,image/webp"
                style="display: none"
                @change="handleFileSelect"
              />
            </div>

            <!-- 文件预览列表 -->
            <div v-if="fileList.length > 0" class="file-list">
              <h3>待上传文件 ({{ fileList.length }})</h3>
              <div class="file-grid">
                <div
                  v-for="(file, index) in fileList"
                  :key="index"
                  class="file-item"
                  :class="{ 'upload-error': file.error, 'upload-success': file.success }"
                >
                  <div class="file-preview">
                    <img v-if="file.preview" :src="file.preview" :alt="file.name" />
                    <div v-else class="preview-placeholder">
                      <span class="material-symbols-rounded">image</span>
                    </div>
                  </div>
                  <div class="file-info">
                    <div class="file-name" :title="file.name">{{ file.name }}</div>
                    <div class="file-size">{{ formatFileSize(file.size) }}</div>
                    <div v-if="file.error" class="file-error">{{ file.error }}</div>
                    <div v-if="file.uploading" class="file-progress">
                      <div class="progress-bar">
                        <div class="progress-fill" :style="{ width: file.progress + '%' }"></div>
                      </div>
                      <div class="progress-text">{{ file.progress.toFixed(2) }}%</div>
                    </div>
                    <div v-if="file.success" class="file-success">
                      <span class="material-symbols-rounded">check_circle</span>
                      上传成功
                    </div>
                  </div>
                  <button
                    class="remove-button"
                    :disabled="file.uploading"
                    @click="removeFile(index)"
                  >
                    <span class="material-symbols-rounded">close</span>
                  </button>
                </div>
              </div>
            </div>

            <!-- 上传统计 -->
            <div v-if="uploadStats.total > 0" class="upload-stats">
              <div class="stat-item">
                <span class="material-symbols-rounded">folder</span>
                <span>总计: {{ uploadStats.total }}</span>
              </div>
              <div class="stat-item success">
                <span class="material-symbols-rounded">check_circle</span>
                <span>成功: {{ uploadStats.success }}</span>
              </div>
              <div class="stat-item error">
                <span class="material-symbols-rounded">error</span>
                <span>失败: {{ uploadStats.failed }}</span>
              </div>
            </div>
          </div>

          <div class="dialog-footer">
            <button class="secondary-button" @click="handleClose" :disabled="isUploading">
              取消
            </button>
            <button
              class="primary-button"
              @click="handleUpload"
              :disabled="fileList.length === 0 || isUploading"
            >
              <span v-if="isUploading">上传中...</span>
              <span v-else>开始上传 ({{ fileList.length }})</span>
            </button>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { useEmojiStore } from '@/stores/emojiStore'

interface FileItem {
  name: string
  size: number
  file: File
  preview: string | null
  uploading: boolean
  success: boolean
  error: string | null
  progress: number
}

const props = defineProps<{
  modelValue: boolean
}>()

const emit = defineEmits<{
  'update:modelValue': [value: boolean]
  uploaded: []
}>()

const emojiStore = useEmojiStore()
const fileInput = ref<HTMLInputElement | null>(null)
const fileList = ref<FileItem[]>([])
const isDragOver = ref(false)
const isUploading = ref(false)

const uploadStats = computed(() => ({
  total: fileList.value.length,
  success: fileList.value.filter(f => f.success).length,
  failed: fileList.value.filter(f => f.error).length,
}))

// 监听对话框关闭，重置状态
watch(() => props.modelValue, (isOpen) => {
  if (!isOpen) {
    fileList.value = []
    isUploading.value = false
  }
})

const triggerFileInput = () => {
  fileInput.value?.click()
}

const handleFileSelect = (event: Event) => {
  const target = event.target as HTMLInputElement
  if (target.files) {
    addFiles(Array.from(target.files))
  }
}

const handleDrop = (event: DragEvent) => {
  isDragOver.value = false
  if (event.dataTransfer?.files) {
    addFiles(Array.from(event.dataTransfer.files))
  }
}

const addFiles = (files: File[]) => {
  // 验证文件类型
  const validTypes = ['image/png', 'image/jpeg', 'image/gif', 'image/webp']
  const maxSize = 10 * 1024 * 1024 // 10MB

  for (const file of files) {
    // 检查文件类型
    if (!validTypes.includes(file.type)) {
      alert(`文件 ${file.name} 格式不支持`)
      continue
    }

    // 检查文件大小
    if (file.size > maxSize) {
      alert(`文件 ${file.name} 超过大小限制（10MB）`)
      continue
    }

    // 检查重复
    if (fileList.value.some(f => f.name === file.name && f.size === file.size)) {
      continue
    }

    // 创建预览
    const reader = new FileReader()
    const fileItem: FileItem = {
      name: file.name,
      size: file.size,
      file,
      preview: null,
      uploading: false,
      success: false,
      error: null,
      progress: 0,
    }

    reader.onload = (e) => {
      fileItem.preview = e.target?.result as string
    }
    reader.readAsDataURL(file)

    fileList.value.push(fileItem)
  }
}

const removeFile = (index: number) => {
  fileList.value.splice(index, 1)
}

const handleUpload = async () => {
  if (fileList.value.length === 0) return

  isUploading.value = true

  // 准备待上传的文件数组
  const filesToUpload: File[] = []
  for (const fileItem of fileList.value) {
    if (!fileItem.success && !fileItem.error) {
      filesToUpload.push(fileItem.file)
    }
  }

  try {
    // 标记所有待上传文件为上传中
    for (const fileItem of fileList.value) {
      if (!fileItem.success && !fileItem.error) {
        fileItem.uploading = true
        fileItem.progress = 0
      }
    }

    // 模拟进度更新（实际应用中应该使用 XMLHttpRequest 或 axios 的进度回调）
    const progressInterval = setInterval(() => {
      for (const fileItem of fileList.value) {
        if (fileItem.uploading && fileItem.progress < 90) {
          fileItem.progress = parseFloat((fileItem.progress + Math.random() * 10).toFixed(2))
        }
      }
    }, 200)

    // 执行上传
    const result = await emojiStore.uploadEmojis(filesToUpload)

    clearInterval(progressInterval)

    // 处理上传结果
    // 标记成功的文件
    for (const successItem of result.success || []) {
      const fileItem = fileList.value.find(f => f.name === successItem.filename)
      if (fileItem) {
        fileItem.uploading = false
        fileItem.success = true
        fileItem.progress = 100
      }
    }

    // 标记失败的文件
    for (const failedItem of result.failed || []) {
      const fileItem = fileList.value.find(f => f.name === failedItem.filename)
      if (fileItem) {
        fileItem.uploading = false
        fileItem.error = failedItem.error || '上传失败'
        fileItem.progress = 0
      }
    }

    // 如果全部成功，延迟后关闭对话框
    if (result.failed.length === 0) {
      setTimeout(() => {
        emit('uploaded')
        handleClose()
      }, 1500)
    }
  } catch (error) {
    console.error('上传失败:', error)
    // 标记所有上传中的文件为失败
    for (const fileItem of fileList.value) {
      if (fileItem.uploading) {
        fileItem.uploading = false
        fileItem.error = '上传失败，请重试'
      }
    }
  } finally {
    isUploading.value = false
  }
}

const formatFileSize = (bytes: number): string => {
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(2) + ' KB'
  return (bytes / (1024 * 1024)).toFixed(2) + ' MB'
}

const handleClose = () => {
  if (isUploading.value) {
    if (!confirm('上传正在进行中，确定要关闭吗？')) {
      return
    }
  }
  emit('update:modelValue', false)
}
</script>

<style scoped>
.dialog-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.6);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  padding: 20px;
}

.dialog-container {
  background: var(--md-sys-color-surface);
  border-radius: 28px;
  width: 100%;
  max-width: 900px;
  max-height: 90vh;
  display: flex;
  flex-direction: column;
  box-shadow: var(--md-sys-elevation-5);
}

.dialog-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 24px;
  border-bottom: 1px solid var(--md-sys-color-outline-variant);
}

.dialog-header h2 {
  font-size: 24px;
  font-weight: 500;
  color: var(--md-sys-color-on-surface);
  margin: 0;
}

.close-button {
  width: 40px;
  height: 40px;
  border: none;
  background: transparent;
  border-radius: 50%;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--md-sys-color-on-surface-variant);
  transition: all 0.2s;
}

.close-button:hover {
  background: var(--md-sys-color-surface-container-highest);
}

.dialog-content {
  flex: 1;
  overflow-y: auto;
  padding: 24px;
}

.upload-area {
  border: 2px dashed var(--md-sys-color-outline);
  border-radius: 16px;
  padding: 48px 24px;
  text-align: center;
  cursor: pointer;
  transition: all 0.3s;
  background: var(--md-sys-color-surface-container);
}

.upload-area:hover,
.upload-area.drag-over {
  border-color: var(--md-sys-color-primary);
  background: var(--md-sys-color-primary-container);
}

.upload-icon {
  font-size: 64px;
  color: var(--md-sys-color-primary);
  display: block;
  margin: 0 auto 16px;
}

.upload-text {
  font-size: 18px;
  font-weight: 500;
  color: var(--md-sys-color-on-surface);
  margin: 0 0 8px 0;
}

.upload-hint {
  font-size: 14px;
  color: var(--md-sys-color-on-surface-variant);
  margin: 0;
}

.file-list {
  margin-top: 24px;
}

.file-list h3 {
  font-size: 16px;
  font-weight: 500;
  color: var(--md-sys-color-on-surface);
  margin: 0 0 12px 0;
}

.file-grid {
  display: grid;
  gap: 12px;
}

.file-item {
  display: flex;
  gap: 12px;
  padding: 12px;
  background: var(--md-sys-color-surface-container);
  border-radius: 12px;
  border: 1px solid var(--md-sys-color-outline-variant);
  transition: all 0.2s;
}

.file-item.upload-success {
  border-color: var(--md-sys-color-tertiary);
  background: var(--md-sys-color-tertiary-container);
}

.file-item.upload-error {
  border-color: var(--md-sys-color-error);
  background: var(--md-sys-color-error-container);
}

.file-preview {
  width: 80px;
  height: 80px;
  flex-shrink: 0;
  border-radius: 8px;
  overflow: hidden;
  background: var(--md-sys-color-surface-container-highest);
  display: flex;
  align-items: center;
  justify-content: center;
}

.file-preview img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.preview-placeholder {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 100%;
  height: 100%;
}

.preview-placeholder .material-symbols-rounded {
  font-size: 32px;
  color: var(--md-sys-color-on-surface-variant);
}

.file-info {
  flex: 1;
  display: flex;
  flex-direction: column;
  justify-content: center;
  gap: 4px;
}

.file-name {
  font-size: 14px;
  font-weight: 500;
  color: var(--md-sys-color-on-surface);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.file-size {
  font-size: 12px;
  color: var(--md-sys-color-on-surface-variant);
}

.file-error {
  font-size: 12px;
  color: var(--md-sys-color-error);
}

.file-success {
  font-size: 12px;
  color: var(--md-sys-color-tertiary);
  display: flex;
  align-items: center;
  gap: 4px;
}

.file-success .material-symbols-rounded {
  font-size: 16px;
}

.file-progress {
  display: flex;
  align-items: center;
  gap: 8px;
}

.progress-bar {
  flex: 1;
  height: 4px;
  background: var(--md-sys-color-surface-container-highest);
  border-radius: 2px;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  background: var(--md-sys-color-primary);
  transition: width 0.3s;
}

.progress-text {
  font-size: 12px;
  color: var(--md-sys-color-on-surface-variant);
  min-width: 40px;
}

.remove-button {
  width: 32px;
  height: 32px;
  border: none;
  background: transparent;
  border-radius: 50%;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--md-sys-color-on-surface-variant);
  transition: all 0.2s;
}

.remove-button:hover:not(:disabled) {
  background: var(--md-sys-color-error-container);
  color: var(--md-sys-color-error);
}

.remove-button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.upload-settings {
  margin-top: 24px;
}

.upload-settings h3 {
  font-size: 16px;
  font-weight: 500;
  color: var(--md-sys-color-on-surface);
  margin: 0 0 12px 0;
}

.setting-item {
  margin-bottom: 16px;
}

.setting-item label {
  display: block;
  font-size: 14px;
  color: var(--md-sys-color-on-surface-variant);
  margin-bottom: 8px;
}

.setting-item input {
  width: 100%;
  padding: 12px;
  border: 1px solid var(--md-sys-color-outline);
  border-radius: 8px;
  background: var(--md-sys-color-surface-container);
  color: var(--md-sys-color-on-surface);
  font-size: 14px;
}

.upload-stats {
  display: flex;
  gap: 16px;
  margin-top: 24px;
  padding: 16px;
  background: var(--md-sys-color-surface-container);
  border-radius: 12px;
}

.stat-item {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  color: var(--md-sys-color-on-surface);
}

.stat-item.success {
  color: var(--md-sys-color-tertiary);
}

.stat-item.error {
  color: var(--md-sys-color-error);
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  padding: 24px;
  border-top: 1px solid var(--md-sys-color-outline-variant);
}

.secondary-button,
.primary-button {
  padding: 10px 24px;
  border: none;
  border-radius: 20px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.secondary-button {
  background: transparent;
  color: var(--md-sys-color-primary);
}

.secondary-button:hover:not(:disabled) {
  background: var(--md-sys-color-surface-container-highest);
}

.primary-button {
  background: var(--md-sys-color-primary);
  color: var(--md-sys-color-on-primary);
}

.primary-button:hover:not(:disabled) {
  background: var(--md-sys-color-primary-container);
  color: var(--md-sys-color-on-primary-container);
}

.secondary-button:disabled,
.primary-button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* 对话框动画 */
.dialog-enter-active,
.dialog-leave-active {
  transition: opacity 0.3s;
}

.dialog-enter-active .dialog-container,
.dialog-leave-active .dialog-container {
  transition: transform 0.3s, opacity 0.3s;
}

.dialog-enter-from,
.dialog-leave-to {
  opacity: 0;
}

.dialog-enter-from .dialog-container,
.dialog-leave-to .dialog-container {
  transform: scale(0.9);
  opacity: 0;
}

@media (max-width: 768px) {
  .dialog-container {
    max-height: 95vh;
  }

  .file-preview {
    width: 60px;
    height: 60px;
  }

  .upload-stats {
    flex-direction: column;
  }
}
</style>
