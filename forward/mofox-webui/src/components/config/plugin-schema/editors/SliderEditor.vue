<!--
  @file SliderEditor.vue
  @description 滑块编辑器组�?- Material Design 3 风格
-->
<template>
  <div class="slider-editor">
    <div class="slider-container">
      <!-- 滑块轨道 -->
      <div class="slider-track">
        <div class="track-inactive"></div>
        <div class="track-active" :style="{ width: progressPercent + '%' }"></div>
      </div>
      
      <!-- 原生滑块 -->
      <input 
        type="range"
        class="slider-input"
        :value="modelValue"
        :disabled="field.disabled"
        :min="field.min ?? 0"
        :max="field.max ?? 100"
        :step="field.step || 1"
        @input="handleNumberInput"
        @mousedown="isDragging = true"
        @mouseup="isDragging = false"
        @mouseleave="isDragging = false"
      >
      
      <!-- 滑块拇指 -->
      <div 
        class="slider-thumb" 
        :class="{ 'is-dragging': isDragging }"
        :style="{ left: progressPercent + '%' }"
      >
        <div class="thumb-ripple"></div>
        <div class="thumb-dot"></div>
      </div>
      
      <!-- 值气�?-->
      <div 
        class="value-tooltip" 
        :class="{ 'is-visible': isDragging }"
        :style="{ left: progressPercent + '%' }"
      >
        {{ displayValue }}
      </div>
    </div>
    
    <!-- 范围和值显�?-->
    <div class="slider-info">
      <span class="range-min">{{ field.min ?? 0 }}</span>
      <div class="value-input-wrapper">
        <input 
          type="number" 
          class="value-input"
          :value="modelValue"
          :min="field.min ?? 0"
          :max="field.max ?? 100"
          :step="field.step || 1"
          @input="handleNumberInput"
        >
      </div>
      <span class="range-max">{{ field.max ?? 100 }}</span>
    </div>
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

const isDragging = ref(false)

const currentValue = computed(() => {
  const val = Number(props.modelValue)
  return isNaN(val) ? (props.field.min ?? 0) : val
})

const progressPercent = computed(() => {
  const min = props.field.min ?? 0
  const max = props.field.max ?? 100
  const val = currentValue.value
  return Math.min(100, Math.max(0, ((val - min) / (max - min)) * 100))
})

const displayValue = computed(() => {
  const step = props.field.step || 1
  if (step < 1) {
    const decimals = String(step).split('.')[1]?.length || 0
    return currentValue.value.toFixed(decimals)
  }
  return Math.round(currentValue.value)
})

function handleNumberInput(event: Event) {
  const target = event.target as HTMLInputElement
  const value = props.field.type === 'int' 
    ? parseInt(target.value, 10) 
    : parseFloat(target.value)
  emit('update:modelValue', isNaN(value) ? 0 : value)
}
</script>

<style scoped>
.slider-editor {
  display: flex;
  flex-direction: column;
  gap: 16px;
  padding: 8px 0;
}

.slider-container {
  position: relative;
  height: 48px;
  display: flex;
  align-items: center;
  padding: 0 12px;
}

/* 滑块轨道 */
.slider-track {
  position: absolute;
  left: 12px;
  right: 12px;
  height: 4px;
  border-radius: 2px;
  overflow: hidden;
}

.track-inactive {
  position: absolute;
  inset: 0;
  background: var(--md-sys-color-surface-container-highest);
}

.track-active {
  position: absolute;
  top: 0;
  left: 0;
  bottom: 0;
  background: var(--md-sys-color-primary);
  border-radius: 2px;
  transition: width 0.05s ease-out;
}

/* 原生滑块输入 */
.slider-input {
  position: absolute;
  left: 0;
  right: 0;
  width: 100%;
  height: 100%;
  opacity: 0;
  cursor: pointer;
  z-index: 10;
  margin: 0;
}

.slider-input:disabled {
  cursor: not-allowed;
}

/* 滑块拇指 */
.slider-thumb {
  position: absolute;
  width: 20px;
  height: 20px;
  transform: translateX(-50%);
  pointer-events: none;
  z-index: 5;
}

.thumb-ripple {
  position: absolute;
  top: 50%;
  left: 50%;
  width: 40px;
  height: 40px;
  transform: translate(-50%, -50%) scale(0);
  background: var(--md-sys-color-primary);
  border-radius: 50%;
  opacity: 0;
  transition: transform 0.2s, opacity 0.2s;
}

.slider-thumb.is-dragging .thumb-ripple {
  transform: translate(-50%, -50%) scale(1);
  opacity: 0.12;
}

.thumb-dot {
  position: absolute;
  top: 50%;
  left: 50%;
  width: 20px;
  height: 20px;
  transform: translate(-50%, -50%);
  background: var(--md-sys-color-primary);
  border-radius: 50%;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
  transition: transform 0.2s cubic-bezier(0.4, 0, 0.2, 1), box-shadow 0.2s;
}

.slider-thumb.is-dragging .thumb-dot {
  transform: translate(-50%, -50%) scale(1.2);
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.3);
}

/* 值气�?*/
.value-tooltip {
  position: absolute;
  bottom: calc(100% + 8px);
  transform: translateX(-50%) scale(0.8);
  padding: 6px 12px;
  background: var(--md-sys-color-inverse-surface);
  color: var(--md-sys-color-inverse-on-surface);
  font-size: 14px;
  font-weight: 500;
  border-radius: 8px;
  white-space: nowrap;
  opacity: 0;
  pointer-events: none;
  transition: opacity 0.2s, transform 0.2s cubic-bezier(0.4, 0, 0.2, 1);
}

.value-tooltip::after {
  content: '';
  position: absolute;
  top: 100%;
  left: 50%;
  transform: translateX(-50%);
  border: 6px solid transparent;
  border-top-color: var(--md-sys-color-inverse-surface);
}

.value-tooltip.is-visible {
  opacity: 1;
  transform: translateX(-50%) scale(1);
}

/* 范围和值显�?*/
.slider-info {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 0 4px;
}

.range-min,
.range-max {
  font-size: 12px;
  color: var(--md-sys-color-on-surface-variant);
  min-width: 32px;
}

.range-min {
  text-align: left;
}

.range-max {
  text-align: right;
}

.value-input-wrapper {
  display: flex;
  justify-content: center;
}

.value-input {
  width: 72px;
  height: 36px;
  padding: 0 12px;
  font-size: 14px;
  font-weight: 500;
  text-align: center;
  color: var(--md-sys-color-on-surface);
  background: var(--md-sys-color-surface-container-highest);
  border: 1px solid var(--md-sys-color-outline-variant);
  border-radius: 18px;
  transition: all 0.2s;
  -moz-appearance: textfield;
  appearance: textfield;
}

.value-input::-webkit-outer-spin-button,
.value-input::-webkit-inner-spin-button {
  -webkit-appearance: none;
  margin: 0;
}

.value-input:focus {
  outline: none;
  border-color: var(--md-sys-color-primary);
  background: var(--md-sys-color-surface-container-high);
}
</style>
