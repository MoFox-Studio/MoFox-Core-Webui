<!--
  @file NumberEditor.vue
  @description 数字编辑器组�?- Material Design 3 风格
-->
<template>
  <div class="number-editor" :class="{ 'is-focused': isFocused }">
    <button 
      type="button"
      class="stepper-button decrease"
      :disabled="field.disabled || isAtMin"
      @click="decrease"
    >
      <span class="material-symbols-rounded">remove</span>
    </button>
    
    <div class="number-input-wrapper">
      <input 
        type="number"
        class="number-input"
        :value="modelValue"
        :placeholder="field.placeholder"
        :disabled="field.disabled"
        :min="field.min"
        :max="field.max"
        :step="field.step || 1"
        @input="handleNumberInput"
        @focus="isFocused = true"
        @blur="isFocused = false"
      >
      <div v-if="field.min !== undefined || field.max !== undefined" class="range-indicator">
        <span v-if="field.min !== undefined">{{ field.min }}</span>
        <span v-if="field.min !== undefined && field.max !== undefined"> ~ </span>
        <span v-if="field.max !== undefined">{{ field.max }}</span>
      </div>
    </div>
    
    <button 
      type="button"
      class="stepper-button increase"
      :disabled="field.disabled || isAtMax"
      @click="increase"
    >
      <span class="material-symbols-rounded">add</span>
    </button>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import type { SchemaField } from '@/api/pluginConfig'

const props = defineProps<{
  field: SchemaField
  modelValue: unknown
}>()

const emit = defineEmits<{
  (e: 'update:modelValue', value: unknown): void
}>()

const isFocused = ref(false)

const currentValue = computed(() => {
  const val = Number(props.modelValue)
  return isNaN(val) ? 0 : val
})

const isAtMin = computed(() => {
  return props.field.min !== undefined && currentValue.value <= props.field.min
})

const isAtMax = computed(() => {
  return props.field.max !== undefined && currentValue.value >= props.field.max
})

function handleNumberInput(event: Event) {
  const target = event.target as HTMLInputElement
  const value = props.field.type === 'int' 
    ? parseInt(target.value, 10) 
    : parseFloat(target.value)
  emit('update:modelValue', isNaN(value) ? 0 : value)
}

function decrease() {
  const step = props.field.step || 1
  let newValue = currentValue.value - step
  if (props.field.min !== undefined && newValue < props.field.min) {
    newValue = props.field.min
  }
  emit('update:modelValue', props.field.type === 'int' ? Math.floor(newValue) : newValue)
}

function increase() {
  const step = props.field.step || 1
  let newValue = currentValue.value + step
  if (props.field.max !== undefined && newValue > props.field.max) {
    newValue = props.field.max
  }
  emit('update:modelValue', props.field.type === 'int' ? Math.floor(newValue) : newValue)
}
</script>

<style scoped>
.number-editor {
  display: flex;
  align-items: center;
  gap: 8px;
  background: var(--md-sys-color-surface-container-highest);
  border-radius: 28px;
  padding: 4px;
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
  border: 1px solid transparent;
}

.number-editor:hover {
  background: var(--md-sys-color-surface-container-high);
}

.number-editor.is-focused {
  border-color: var(--md-sys-color-primary);
  background: var(--md-sys-color-surface-container-high);
}

/* 步进按钮 */
.stepper-button {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 48px;
  height: 48px;
  border: none;
  border-radius: 50%;
  background: var(--md-sys-color-primary-container);
  color: var(--md-sys-color-on-primary-container);
  cursor: pointer;
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
  flex-shrink: 0;
}

.stepper-button .material-symbols-rounded {
  font-size: 24px;
}

.stepper-button:hover:not(:disabled) {
  background: var(--md-sys-color-primary);
  color: var(--md-sys-color-on-primary);
  transform: scale(1.05);
}

.stepper-button:active:not(:disabled) {
  transform: scale(0.95);
}

.stepper-button:disabled {
  background: var(--md-sys-color-surface-container-highest);
  color: var(--md-sys-color-on-surface);
  opacity: 0.38;
  cursor: not-allowed;
}

/* 数字输入�?*/
.number-input-wrapper {
  flex: 1;
  min-width: 80px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 2px;
}

.number-input {
  width: 100%;
  height: 40px;
  padding: 0 12px;
  font-size: 1.25rem;
  font-weight: 500;
  text-align: center;
  color: var(--md-sys-color-on-surface);
  background: transparent;
  border: none;
  caret-color: var(--md-sys-color-primary);
  -moz-appearance: textfield;
  appearance: textfield;
}

.number-input::-webkit-outer-spin-button,
.number-input::-webkit-inner-spin-button {
  -webkit-appearance: none;
  margin: 0;
}

.number-input:focus {
  outline: none;
}

.number-input:disabled {
  color: var(--md-sys-color-on-surface);
  opacity: 0.38;
  cursor: not-allowed;
}

.number-input::placeholder {
  color: var(--md-sys-color-on-surface-variant);
  font-weight: 400;
}

/* 范围提示 */
.range-indicator {
  font-size: 11px;
  color: var(--md-sys-color-on-surface-variant);
  opacity: 0.7;
}
</style>
