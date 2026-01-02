<!--
  @file SelectEditor.vue
  @description 下拉选择编辑器组件 - Material Design 3 风格
-->
<template>
  <div class="select-editor" :class="{ 'is-focused': isFocused, 'has-value': hasValue }">
    <div class="field-wrapper">
      <select 
        class="select-input"
        :value="modelValue"
        :disabled="field.disabled"
        @change="handleSelectChange"
        @focus="isFocused = true"
        @blur="isFocused = false"
      >
        <option value="" disabled>{{ field.placeholder || '请选择' }}</option>
        <option 
          v-for="choice in normalizedChoices" 
          :key="String(choice.value)" 
          :value="choice.value"
        >
          {{ choice.label }}
        </option>
      </select>
      <span class="select-arrow material-symbols-rounded">expand_more</span>
      <div class="field-decoration">
        <div class="field-border"></div>
        <div class="field-focus-indicator"></div>
      </div>
    </div>
    <!-- 已选择标签 -->
    <div v-if="hasValue" class="selected-chip">
      <span class="chip-content">{{ selectedLabel }}</span>
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

// 标准化选项格式
const normalizedChoices = computed(() => {
  if (!props.field.choices) return []
  return props.field.choices.map(choice => {
    if (typeof choice === 'object' && choice !== null && 'value' in choice) {
      return choice as { value: unknown, label: string }
    }
    return { value: choice, label: String(choice) }
  })
})

const selectedLabel = computed(() => {
  const found = normalizedChoices.value.find(c => c.value === props.modelValue)
  return found?.label || String(props.modelValue)
})

function handleSelectChange(event: Event) {
  const target = event.target as HTMLSelectElement
  emit('update:modelValue', target.value)
}
</script>

<style scoped>
.select-editor {
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

.select-input {
  width: 100%;
  height: 56px;
  padding: 0 48px 0 16px;
  font-size: 1rem;
  line-height: 24px;
  color: var(--md-sys-color-on-surface);
  background: transparent;
  border: none;
  cursor: pointer;
  appearance: none;
  transition: background 0.2s cubic-bezier(0.4, 0, 0.2, 1);
}

.select-input:hover:not(:disabled) {
  background: color-mix(in srgb, var(--md-sys-color-on-surface) 8%, transparent);
}

.select-input:focus {
  outline: none;
}

.select-input:disabled {
  color: var(--md-sys-color-on-surface);
  opacity: 0.38;
  cursor: not-allowed;
}

.select-arrow {
  position: absolute;
  right: 12px;
  font-size: 24px;
  color: var(--md-sys-color-on-surface-variant);
  pointer-events: none;
  transition: transform 0.2s cubic-bezier(0.4, 0, 0.2, 1), color 0.2s;
}

.is-focused .select-arrow {
  transform: rotate(180deg);
  color: var(--md-sys-color-primary);
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

/* 已选择标签 */
.selected-chip {
  display: none; /* 隐藏，如果需要可以开�?*/
  align-items: center;
  gap: 6px;
  padding: 6px 12px;
  background: var(--md-sys-color-primary-container);
  color: var(--md-sys-color-on-primary-container);
  border-radius: 16px;
  font-size: 13px;
  width: fit-content;
}

.chip-content {
  font-weight: 500;
}
</style>
