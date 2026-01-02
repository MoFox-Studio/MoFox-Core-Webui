<!--
  @file FileEditor.vue
  @description 文件路径编辑器组�?- Material Design 3 风格
-->
<template>
  <div class="file-editor" :class="{ 'is-focused': isFocused, 'has-value': hasValue }">
    <div class="field-wrapper">
      <span class="leading-icon material-symbols-rounded">folder</span>
      <input 
        type="text"
        class="file-input"
        :value="modelValue"
        :placeholder="field.placeholder || '输入文件路径...'"
        :disabled="field.disabled"
        @input="handleInput"
        @focus="isFocused = true"
        @blur="isFocused = false"
      >
      <button 
        type="button" 
        class="browse-button"
        @click="openFilePicker"
        :disabled="field.disabled"
        title="浏览"
      >
        <span class="material-symbols-rounded">folder_open</span>
        <span class="button-text">浏览</span>
      </button>
      <div class="field-decoration">
        <div class="field-border"></div>
        <div class="field-focus-indicator"></div>
      </div>
    </div>
    
    <!-- 文件信息 -->
    <div v-if="hasValue" class="file-info">
      <span class="material-symbols-rounded file-type-icon">{{ getFileIcon() }}</span>
      <span class="file-name">{{ getFileName() }}</span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import type { SchemaField } from '@/api/pluginConfigApi'

const props = defineProps<{
  field: SchemaField
  modelValue: unknown
}>()

const emit = defineEmits<{
  (e: 'update:modelValue', value: unknown): void
}>()

const isFocused = ref(false)

const hasValue = computed(() => {
  return props.modelValue !== undefined && props.modelValue !== null && props.modelValue !== ''
})

function handleInput(event: Event) {
  const target = event.target as HTMLInputElement
  emit('update:modelValue', target.value)
}

function openFilePicker() {
  // TODO: Implement file picker dialog
  console.log('Open file picker')
}

function getFileName() {
  const path = String(props.modelValue || '')
  return path.split(/[\\/]/).pop() || path
}

function getFileIcon() {
  const path = String(props.modelValue || '').toLowerCase()
  if (path.endsWith('.json') || path.endsWith('.toml') || path.endsWith('.yaml')) return 'settings'
  if (path.endsWith('.py')) return 'code'
  if (path.endsWith('.txt') || path.endsWith('.md')) return 'description'
  if (path.endsWith('.png') || path.endsWith('.jpg') || path.endsWith('.gif')) return 'image'
  if (/[\\/]$/.test(path) || !path.includes('.')) return 'folder'
  return 'insert_drive_file'
}
</script>

<style scoped>
.file-editor {
  position: relative;
  width: 100%;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.field-wrapper {
  position: relative;
  display: flex;
  align-items: center;
  background: var(--md-sys-color-surface-container-highest);
  border-radius: 16px 16px 0 0;
  overflow: hidden;
}

.leading-icon {
  position: absolute;
  left: 12px;
  font-size: 20px;
  color: var(--md-sys-color-on-surface-variant);
  transition: color 0.2s;
}

.is-focused .leading-icon {
  color: var(--md-sys-color-primary);
}

.file-input {
  width: 100%;
  height: 56px;
  padding: 0 120px 0 44px;
  font-size: 0.9rem;
  line-height: 24px;
  color: var(--md-sys-color-on-surface);
  background: transparent;
  border: none;
  font-family: 'JetBrains Mono', monospace;
  transition: background 0.2s cubic-bezier(0.4, 0, 0.2, 1);
  caret-color: var(--md-sys-color-primary);
}

.file-input:hover:not(:disabled) {
  background: color-mix(in srgb, var(--md-sys-color-on-surface) 4%, transparent);
}

.file-input:focus {
  outline: none;
}

.file-input:disabled {
  color: var(--md-sys-color-on-surface);
  opacity: 0.38;
  cursor: not-allowed;
}

.file-input::placeholder {
  color: var(--md-sys-color-on-surface-variant);
  font-family: inherit;
}

/* 浏览按钮 */
.browse-button {
  position: absolute;
  right: 8px;
  display: flex;
  align-items: center;
  gap: 6px;
  height: 40px;
  padding: 0 16px;
  background: var(--md-sys-color-primary-container);
  color: var(--md-sys-color-on-primary-container);
  border: none;
  border-radius: 20px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
}

.browse-button:hover:not(:disabled) {
  background: var(--md-sys-color-primary);
  color: var(--md-sys-color-on-primary);
}

.browse-button:disabled {
  opacity: 0.38;
  cursor: not-allowed;
}

.browse-button .material-symbols-rounded {
  font-size: 18px;
}

.button-text {
  display: inline;
}

@media (max-width: 480px) {
  .button-text {
    display: none;
  }
  .browse-button {
    padding: 0 12px;
  }
  .file-input {
    padding-right: 56px;
  }
}

/* 底部边框装饰 */
.field-decoration {
  position: absolute;
  left: 0;
  right: 0;
  bottom: 0;
  height: 2px;
  pointer-events: none;
}

.field-border {
  position: absolute;
  left: 0;
  right: 0;
  bottom: 0;
  height: 1px;
  background: var(--md-sys-color-on-surface-variant);
  transition: opacity 0.2s;
}

.field-focus-indicator {
  position: absolute;
  left: 50%;
  right: 50%;
  bottom: 0;
  height: 2px;
  background: var(--md-sys-color-primary);
  transition: left 0.3s cubic-bezier(0.4, 0, 0.2, 1), right 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.is-focused .field-border {
  opacity: 0;
}

.is-focused .field-focus-indicator {
  left: 0;
  right: 0;
}

/* 文件信息 */
.file-info {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  background: var(--md-sys-color-surface-container);
  border-radius: 12px;
}

.file-type-icon {
  font-size: 20px;
  color: var(--md-sys-color-primary);
}

.file-name {
  font-size: 13px;
  color: var(--md-sys-color-on-surface-variant);
  font-family: 'JetBrains Mono', monospace;
}
</style>
