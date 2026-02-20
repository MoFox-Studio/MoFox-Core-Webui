<!--
  @file SwitchEditor.vue
  @description 开关编辑器组件 - Material Design 3 风格
-->
<template>
  <div class="switch-editor" :class="{ 'is-checked': Boolean(modelValue), 'is-disabled': field.disabled }">
    <div class="field-left">
      <div class="field-header">
        <span v-if="field.icon" class="material-symbols-rounded field-icon">{{ field.icon }}</span>
        <span class="field-label">{{ field.label || field.key }}</span>
        <span v-if="field.required" class="required-badge">必填</span>
      </div>
      <div v-if="field.description || field.hint" class="field-description">
        <span class="material-symbols-rounded desc-icon">info</span>
        <span>{{ field.hint || field.description }}</span>
      </div>
    </div>
    
    <label class="m3-switch">
      <input 
        type="checkbox" 
        :checked="Boolean(modelValue)"
        :disabled="field.disabled"
        @change="handleSwitchChange"
      >
      <span class="switch-track">
        <span class="switch-thumb">
          <span class="thumb-icon material-symbols-rounded">
            {{ Boolean(modelValue) ? 'check' : '' }}
          </span>
        </span>
      </span>
    </label>
  </div>
</template>

<script setup lang="ts">
import type { SchemaField } from '@/api/pluginConfig'

defineProps<{
  field: SchemaField
  modelValue: unknown
}>()

const emit = defineEmits<{
  (e: 'update:modelValue', value: unknown): void
}>()

function handleSwitchChange(event: Event) {
  const target = event.target as HTMLInputElement
  emit('update:modelValue', target.checked)
}
</script>

<style scoped>
.switch-editor {
  display: flex;
  align-items: center;
  justify-content: space-between;
  width: 100%;
  padding: 12px 16px;
  background: var(--md-sys-color-surface-container-highest);
  border-radius: 16px;
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
  cursor: pointer;
}

.switch-editor:hover {
  background: color-mix(in srgb, var(--md-sys-color-on-surface) 8%, var(--md-sys-color-surface-container-highest));
}

.switch-editor.is-disabled {
  opacity: 0.5;
  pointer-events: none;
}

.field-left {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 4px;
  padding-right: 16px;
}

.field-header {
  display: flex;
  align-items: center;
  gap: 8px;
}

.field-icon {
  font-size: 22px;
  color: var(--md-sys-color-primary);
  transition: color 0.2s;
}

.is-checked .field-icon {
  color: var(--md-sys-color-primary);
}

.field-label {
  font-size: 15px;
  font-weight: 500;
  color: var(--md-sys-color-on-surface);
  line-height: 22px;
}

.required-badge {
  font-size: 11px;
  padding: 2px 8px;
  background: var(--md-sys-color-error-container);
  color: var(--md-sys-color-on-error-container);
  border-radius: 8px;
  font-weight: 500;
}

.field-description {
  display: flex;
  align-items: flex-start;
  gap: 6px;
  font-size: 13px;
  color: var(--md-sys-color-on-surface-variant);
  line-height: 18px;
}

.desc-icon {
  font-size: 16px;
  margin-top: 1px;
  flex-shrink: 0;
  opacity: 0.7;
}

/* M3 Switch Styles */
.m3-switch {
  position: relative;
  display: inline-block;
  width: 52px;
  height: 32px;
  flex-shrink: 0;
}

.m3-switch input {
  opacity: 0;
  width: 0;
  height: 0;
}

.switch-track {
  position: absolute;
  cursor: pointer;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: var(--md-sys-color-surface-container-highest);
  border: 2px solid var(--md-sys-color-outline);
  border-radius: 16px;
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
}

.switch-thumb {
  position: absolute;
  display: flex;
  align-items: center;
  justify-content: center;
  height: 16px;
  width: 16px;
  left: 6px;
  bottom: 6px;
  background-color: var(--md-sys-color-outline);
  border-radius: 50%;
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
}

.thumb-icon {
  font-size: 12px;
  color: var(--md-sys-color-on-primary);
  opacity: 0;
  transition: opacity 0.2s;
}

/* Checked State */
.m3-switch input:checked + .switch-track {
  background-color: var(--md-sys-color-primary);
  border-color: var(--md-sys-color-primary);
}

.m3-switch input:checked + .switch-track .switch-thumb {
  transform: translateX(20px);
  background-color: var(--md-sys-color-on-primary);
  width: 24px;
  height: 24px;
  bottom: 2px;
  left: 2px;
}

.m3-switch input:checked + .switch-track .thumb-icon {
  opacity: 1;
  color: var(--md-sys-color-primary);
}

/* Hover States */
.m3-switch:hover input:not(:checked) + .switch-track {
  border-color: var(--md-sys-color-on-surface);
}

.m3-switch:hover input:not(:checked) + .switch-track .switch-thumb {
  background-color: var(--md-sys-color-on-surface);
}

.m3-switch:hover input:checked + .switch-track {
  filter: brightness(1.08);
}

/* Disabled States */
.m3-switch input:disabled + .switch-track {
  opacity: 0.38;
  cursor: not-allowed;
}
</style>
