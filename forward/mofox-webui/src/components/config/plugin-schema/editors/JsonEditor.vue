<!--
  @file JsonEditor.vue
  @description JSON 编辑器组�?- Material Design 3 风格
-->
<template>
  <div class="json-editor" :class="{ 'is-focused': isFocused, 'has-error': !!error }">
    <div class="editor-header">
      <div class="header-left">
        <span class="material-symbols-rounded header-icon">data_object</span>
        <span class="header-label">JSON 编辑器</span>
      </div>
      <div class="header-actions">
        <button 
          type="button" 
          class="action-button" 
          @click="formatJson"
          title="格式化"
        >
          <span class="material-symbols-rounded">format_align_left</span>
        </button>
        <button 
          type="button" 
          class="action-button" 
          @click="minifyJson"
          title="压缩"
        >
          <span class="material-symbols-rounded">compress</span>
        </button>
        <button 
          type="button" 
          class="action-button" 
          @click="copyJson"
          title="复制"
        >
          <span class="material-symbols-rounded">{{ copied ? 'check' : 'content_copy' }}</span>
        </button>
      </div>
    </div>
    
    <div class="editor-body">
      <div class="line-numbers">
        <div v-for="n in lineCount" :key="n" class="line-number">{{ n }}</div>
      </div>
      <textarea 
        class="json-textarea"
        :value="jsonString"
        :placeholder="field.placeholder || '{\n  \n}'"
        :disabled="field.disabled"
        spellcheck="false"
        @input="handleInput"
        @focus="isFocused = true"
        @blur="handleBlur"
        @keydown.tab.prevent="handleTab"
      ></textarea>
    </div>
    
    <div class="editor-footer">
      <div v-if="error" class="error-message">
        <span class="material-symbols-rounded">error</span>
        {{ error }}
      </div>
      <div v-else class="status-info">
        <span class="material-symbols-rounded">check_circle</span>
        JSON 格式正确
      </div>
      <span class="size-info">{{ jsonString.length }} 字符</span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import type { SchemaField } from '@/api/pluginConfigApi'

const props = defineProps<{
  field: SchemaField
  modelValue: unknown
}>()

const emit = defineEmits<{
  (e: 'update:modelValue', value: unknown): void
}>()

const error = ref('')
const internalValue = ref('')
const isFocused = ref(false)
const copied = ref(false)

// Initialize internal value
watch(() => props.modelValue, (val) => {
  if (typeof val === 'object' && val !== null) {
    internalValue.value = JSON.stringify(val, null, 2)
  } else if (val === undefined || val === null) {
    internalValue.value = '{}'
  }
}, { immediate: true })

const jsonString = computed(() => internalValue.value)
const lineCount = computed(() => Math.max(jsonString.value.split('\n').length, 5))

function handleInput(event: Event) {
  const target = event.target as HTMLTextAreaElement
  internalValue.value = target.value
  error.value = ''
  
  try {
    const parsed = JSON.parse(target.value)
    emit('update:modelValue', parsed)
    error.value = ''
  } catch (e) {
    error.value = '无效�?JSON 格式'
  }
}

function handleBlur() {
  isFocused.value = false
  formatJson()
}

function formatJson() {
  try {
    const parsed = JSON.parse(internalValue.value)
    internalValue.value = JSON.stringify(parsed, null, 2)
    error.value = ''
  } catch (e) {
    // Keep error state
  }
}

function minifyJson() {
  try {
    const parsed = JSON.parse(internalValue.value)
    internalValue.value = JSON.stringify(parsed)
    error.value = ''
  } catch (e) {
    // Keep error state
  }
}

function copyJson() {
  navigator.clipboard.writeText(internalValue.value)
  copied.value = true
  setTimeout(() => { copied.value = false }, 2000)
}

function handleTab(event: KeyboardEvent) {
  const target = event.target as HTMLTextAreaElement
  const start = target.selectionStart
  const end = target.selectionEnd
  const value = target.value
  
  target.value = value.substring(0, start) + '  ' + value.substring(end)
  target.selectionStart = target.selectionEnd = start + 2
  internalValue.value = target.value
}
</script>

<style scoped>
.json-editor {
  display: flex;
  flex-direction: column;
  border-radius: 16px;
  background: var(--md-sys-color-surface-container);
  border: 1px solid var(--md-sys-color-outline-variant);
  overflow: hidden;
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
}

.json-editor:hover {
  border-color: var(--md-sys-color-outline);
}

.json-editor.is-focused {
  border-color: var(--md-sys-color-primary);
  box-shadow: 0 0 0 1px var(--md-sys-color-primary);
}

.json-editor.has-error {
  border-color: var(--md-sys-color-error);
}

.json-editor.has-error.is-focused {
  box-shadow: 0 0 0 1px var(--md-sys-color-error);
}

/* 头部 */
.editor-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 12px;
  background: var(--md-sys-color-surface-container-high);
  border-bottom: 1px solid var(--md-sys-color-outline-variant);
}

.header-left {
  display: flex;
  align-items: center;
  gap: 8px;
}

.header-icon {
  font-size: 20px;
  color: var(--md-sys-color-primary);
}

.header-label {
  font-size: 13px;
  font-weight: 500;
  color: var(--md-sys-color-on-surface-variant);
}

.header-actions {
  display: flex;
  gap: 4px;
}

.action-button {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  border: none;
  background: transparent;
  border-radius: 8px;
  color: var(--md-sys-color-on-surface-variant);
  cursor: pointer;
  transition: all 0.2s;
}

.action-button:hover {
  background: var(--md-sys-color-surface-container-highest);
  color: var(--md-sys-color-on-surface);
}

.action-button .material-symbols-rounded {
  font-size: 18px;
}

/* 编辑器主�?*/
.editor-body {
  display: flex;
  min-height: 160px;
  max-height: 320px;
}

.line-numbers {
  display: flex;
  flex-direction: column;
  padding: 12px 8px;
  background: var(--md-sys-color-surface-container-high);
  border-right: 1px solid var(--md-sys-color-outline-variant);
  user-select: none;
}

.line-number {
  font-family: 'JetBrains Mono', 'Fira Code', monospace;
  font-size: 12px;
  line-height: 1.6;
  color: var(--md-sys-color-on-surface-variant);
  opacity: 0.6;
  text-align: right;
  min-width: 24px;
}

.json-textarea {
  flex: 1;
  padding: 12px 16px;
  font-family: 'JetBrains Mono', 'Fira Code', monospace;
  font-size: 13px;
  line-height: 1.6;
  color: var(--md-sys-color-on-surface);
  background: transparent;
  border: none;
  resize: none;
  overflow-y: auto;
}

.json-textarea:focus {
  outline: none;
}

.json-textarea::placeholder {
  color: var(--md-sys-color-on-surface-variant);
  opacity: 0.5;
}

/* 底部 */
.editor-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 12px;
  background: var(--md-sys-color-surface-container-high);
  border-top: 1px solid var(--md-sys-color-outline-variant);
}

.error-message {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: var(--md-sys-color-error);
}

.error-message .material-symbols-rounded {
  font-size: 16px;
}

.status-info {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: #10b981;
}

.status-info .material-symbols-rounded {
  font-size: 16px;
}

.size-info {
  font-size: 11px;
  color: var(--md-sys-color-on-surface-variant);
}
</style>
