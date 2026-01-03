<!--
  @file TextEditor.vue
  @description 文本编辑器组件 - Material Design 3 风格
-->
<template>
  <div class="m3-text-field-container" :class="{ 'is-focused': isFocused, 'has-value': hasValue }">
    <div class="field-wrapper">
      <input 
        type="text"
        class="m3-text-field"
        :value="modelValue"
        :placeholder="field.placeholder"
        :disabled="field.disabled"
        :maxlength="field.max_length"
        @input="handleInput"
        @focus="isFocused = true"
        @blur="isFocused = false"
      >
      <div class="field-decoration">
        <div class="field-border"></div>
        <div class="field-focus-indicator"></div>
      </div>
      <!-- 清除按钮 -->
      <button 
        v-if="hasValue && !field.disabled"
        type="button"
        class="clear-button"
        @click="clearValue"
        tabindex="-1"
      >
        <span class="material-symbols-rounded">close</span>
      </button>
    </div>
    <!-- 字符计数 -->
    <div v-if="field.max_length" class="char-counter">
      {{ String(modelValue || '').length }} / {{ field.max_length }}
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

function clearValue() {
  emit('update:modelValue', '')
}
</script>

<style scoped>
.m3-text-field-container {
  position: relative;
  width: 100%;
}

.field-wrapper {
  position: relative;
  display: flex;
  align-items: center;
}

.m3-text-field {
  width: 100%;
  height: 56px;
  padding: 0 48px 0 16px;
  font-size: 1rem;
  line-height: 24px;
  color: var(--md-sys-color-on-surface);
  background: var(--md-sys-color-surface-container-highest);
  border: none;
  border-radius: 16px;
  transition: background 0.2s cubic-bezier(0.4, 0, 0.2, 1);
  caret-color: var(--md-sys-color-primary);
}

.m3-text-field:hover:not(:disabled) {
  background: color-mix(in srgb, var(--md-sys-color-on-surface) 8%, var(--md-sys-color-surface-container-highest));
}

.m3-text-field:focus {
  outline: 2px solid var(--md-sys-color-primary);
  outline-offset: -2px;
  background: var(--md-sys-color-surface-container-highest);
}

.m3-text-field:disabled {
  color: var(--md-sys-color-on-surface);
  opacity: 0.38;
  cursor: not-allowed;
}

.m3-text-field::placeholder {
  color: var(--md-sys-color-on-surface-variant);
  opacity: 1;
}

/* 底部边框装饰 */
.field-decoration {
  display: none;
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

/* 清除按钮 */
.clear-button {
  position: absolute;
  right: 8px;
  top: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  border: none;
  background: transparent;
  border-radius: 50%;
  color: var(--md-sys-color-on-surface-variant);
  cursor: pointer;
  opacity: 0;
  transform: scale(0.8);
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
}

.clear-button .material-symbols-rounded {
  font-size: 20px;
}

.clear-button:hover {
  background: var(--md-sys-color-surface-container);
  color: var(--md-sys-color-on-surface);
}

.m3-text-field-container:hover .clear-button,
.is-focused .clear-button {
  opacity: 1;
  transform: scale(1);
}

/* 字符计数 */
.char-counter {
  position: absolute;
  right: 0;
  bottom: -20px;
  font-size: 12px;
  color: var(--md-sys-color-on-surface-variant);
  transition: color 0.2s;
}

.is-focused .char-counter {
  color: var(--md-sys-color-primary);
}
</style>
