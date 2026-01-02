<!--
  @file TextareaEditor.vue
  @description 多行文本编辑器组件 - Material Design 3 风格
-->
<template>
  <div class="textarea-editor" :class="{ 'is-focused': isFocused }">
    <div class="field-wrapper">
      <textarea 
        class="textarea-input"
        :value="modelValue as string"
        :placeholder="field.placeholder || '输入内容...'"
        :disabled="field.disabled"
        :rows="field.rows || 4"
        :maxlength="field.max_length"
        @input="handleInput"
        @focus="isFocused = true"
        @blur="isFocused = false"
      ></textarea>
      <div class="field-decoration">
        <div class="field-border"></div>
        <div class="field-focus-indicator"></div>
      </div>
    </div>
    
    <!-- 底部信息 -->
    <div class="textarea-footer">
      <span v-if="lineCount > 1" class="line-count">
        <span class="material-symbols-rounded">format_list_numbered</span>
        {{ lineCount }} �?
      </span>
      <span class="char-counter" v-if="field.max_length">
        {{ charCount }} / {{ field.max_length }}
      </span>
      <span class="char-counter" v-else>
        {{ charCount }} 字符
      </span>
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

const charCount = computed(() => String(props.modelValue || '').length)
const lineCount = computed(() => String(props.modelValue || '').split('\n').length)

function handleInput(event: Event) {
  const target = event.target as HTMLTextAreaElement
  emit('update:modelValue', target.value)
}
</script>

<style scoped>
.textarea-editor {
  position: relative;
  width: 100%;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.field-wrapper {
  position: relative;
  display: flex;
  flex-direction: column;
  background: var(--md-sys-color-surface-container-highest);
  border-radius: 16px 16px 0 0;
  overflow: hidden;
}

.textarea-input {
  width: 100%;
  min-height: 120px;
  padding: 16px;
  font-size: 1rem;
  line-height: 1.5;
  color: var(--md-sys-color-on-surface);
  background: transparent;
  border: none;
  font-family: inherit;
  resize: vertical;
  transition: background 0.2s cubic-bezier(0.4, 0, 0.2, 1);
  caret-color: var(--md-sys-color-primary);
}

.textarea-input:hover:not(:disabled) {
  background: color-mix(in srgb, var(--md-sys-color-on-surface) 4%, transparent);
}

.textarea-input:focus {
  outline: none;
}

.textarea-input:disabled {
  color: var(--md-sys-color-on-surface);
  opacity: 0.38;
  cursor: not-allowed;
  resize: none;
}

.textarea-input::placeholder {
  color: var(--md-sys-color-on-surface-variant);
  opacity: 1;
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

/* 底部信息 */
.textarea-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 4px;
  font-size: 12px;
  color: var(--md-sys-color-on-surface-variant);
}

.line-count {
  display: flex;
  align-items: center;
  gap: 4px;
}

.line-count .material-symbols-rounded {
  font-size: 16px;
}

.char-counter {
  transition: color 0.2s;
}

.is-focused .char-counter {
  color: var(--md-sys-color-primary);
}
</style>
