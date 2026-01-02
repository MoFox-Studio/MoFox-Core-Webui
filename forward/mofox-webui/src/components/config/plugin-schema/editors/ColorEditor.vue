<!--
  @file ColorEditor.vue
  @description 颜色选择器组�?- Material Design 3 风格
-->
<template>
  <div class="color-editor">
    <div class="color-preview-wrapper">
      <div 
        class="color-preview" 
        :style="{ backgroundColor: colorValue }"
        @click="openColorPicker"
      >
        <div class="color-overlay"></div>
        <span class="material-symbols-rounded preview-icon">colorize</span>
      </div>
      <input 
        ref="colorInput"
        type="color"
        class="hidden-color-input"
        :value="colorValue"
        :disabled="field.disabled"
        @input="handleColorInput"
      >
    </div>
    
    <div class="color-info">
      <div class="hex-input-wrapper">
        <span class="hex-prefix">#</span>
        <input 
          type="text"
          class="hex-input"
          :value="hexWithoutHash"
          placeholder="RRGGBB"
          maxlength="6"
          :disabled="field.disabled"
          @input="handleHexInput"
        >
      </div>
      
      <div class="color-chips">
        <button 
          v-for="preset in presetColors" 
          :key="preset"
          type="button"
          class="color-chip"
          :class="{ 'is-selected': colorValue.toLowerCase() === preset.toLowerCase() }"
          :style="{ backgroundColor: preset }"
          @click="selectPreset(preset)"
          :title="preset"
        ></button>
      </div>
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

const colorInput = ref<HTMLInputElement | null>(null)

const colorValue = computed(() => {
  const val = String(props.modelValue || '#6750A4')
  return val.startsWith('#') ? val : `#${val}`
})

const hexWithoutHash = computed(() => {
  return colorValue.value.replace('#', '').toUpperCase()
})

const presetColors = [
  '#6750A4', '#D0BCFF', '#7F67BE', 
  '#4285F4', '#34A853', '#FBBC05', 
  '#EA4335', '#FF6D00', '#00BCD4'
]

function openColorPicker() {
  colorInput.value?.click()
}

function handleColorInput(event: Event) {
  const target = event.target as HTMLInputElement
  emit('update:modelValue', target.value.toUpperCase())
}

function handleHexInput(event: Event) {
  const target = event.target as HTMLInputElement
  let value = target.value.replace(/[^0-9A-Fa-f]/g, '').toUpperCase()
  if (value.length <= 6) {
    emit('update:modelValue', `#${value}`)
  }
}

function selectPreset(color: string) {
  emit('update:modelValue', color.toUpperCase())
}
</script>

<style scoped>
.color-editor {
  display: flex;
  align-items: flex-start;
  gap: 16px;
  padding: 8px 0;
}

.color-preview-wrapper {
  position: relative;
}

.color-preview {
  width: 64px;
  height: 64px;
  border-radius: 16px;
  cursor: pointer;
  position: relative;
  overflow: hidden;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
  transition: transform 0.2s, box-shadow 0.2s;
}

.color-preview:hover {
  transform: scale(1.05);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
}

.color-preview:active {
  transform: scale(0.98);
}

.color-overlay {
  position: absolute;
  inset: 0;
  background: linear-gradient(135deg, rgba(255,255,255,0.2) 0%, transparent 50%, rgba(0,0,0,0.1) 100%);
}

.preview-icon {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  font-size: 24px;
  color: white;
  text-shadow: 0 1px 3px rgba(0,0,0,0.3);
  opacity: 0;
  transition: opacity 0.2s;
}

.color-preview:hover .preview-icon {
  opacity: 1;
}

.hidden-color-input {
  position: absolute;
  opacity: 0;
  width: 0;
  height: 0;
  pointer-events: none;
}

.color-info {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.hex-input-wrapper {
  display: flex;
  align-items: center;
  background: var(--md-sys-color-surface-container-highest);
  border-radius: 12px;
  overflow: hidden;
  border: 1px solid var(--md-sys-color-outline-variant);
  transition: border-color 0.2s;
}

.hex-input-wrapper:focus-within {
  border-color: var(--md-sys-color-primary);
}

.hex-prefix {
  padding: 0 12px;
  font-size: 16px;
  font-weight: 500;
  color: var(--md-sys-color-on-surface-variant);
  background: var(--md-sys-color-surface-container-high);
  height: 44px;
  display: flex;
  align-items: center;
}

.hex-input {
  flex: 1;
  height: 44px;
  padding: 0 12px;
  font-size: 16px;
  font-family: 'JetBrains Mono', monospace;
  text-transform: uppercase;
  letter-spacing: 1px;
  color: var(--md-sys-color-on-surface);
  background: transparent;
  border: none;
}

.hex-input:focus {
  outline: none;
}

.hex-input::placeholder {
  color: var(--md-sys-color-on-surface-variant);
  opacity: 0.5;
}

.color-chips {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.color-chip {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  border: 2px solid transparent;
  cursor: pointer;
  transition: all 0.2s;
  box-shadow: 0 1px 3px rgba(0,0,0,0.15);
}

.color-chip:hover {
  transform: scale(1.15);
}

.color-chip.is-selected {
  border-color: var(--md-sys-color-on-surface);
  transform: scale(1.1);
  box-shadow: 0 0 0 2px var(--md-sys-color-surface), 0 2px 8px rgba(0,0,0,0.2);
}
</style>
