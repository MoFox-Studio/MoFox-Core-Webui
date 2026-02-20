<!--
  @file PasswordEditor.vue
  @description 密码编辑器组�?- Material Design 3 风格
-->
<template>
  <div class="password-editor" :class="{ 'is-focused': isFocused, 'has-value': hasValue }">
    <div class="field-wrapper">
      <span class="leading-icon material-symbols-rounded">key</span>
      <input 
        :type="showPassword ? 'text' : 'password'"
        class="password-input"
        :value="modelValue"
        :placeholder="field.placeholder || '输入密码'"
        :disabled="field.disabled"
        autocomplete="off"
        :maxlength="field.max_length"
        @input="handleInput"
        @focus="isFocused = true"
        @blur="isFocused = false"
      >
      <button 
        type="button"
        class="password-toggle"
        @click="showPassword = !showPassword"
        :aria-label="showPassword ? '隐藏密码' : '显示密码'"
        tabindex="-1"
      >
        <span class="material-symbols-rounded">
          {{ showPassword ? 'visibility_off' : 'visibility' }}
        </span>
      </button>
      <div class="field-decoration">
        <div class="field-border"></div>
        <div class="field-focus-indicator"></div>
      </div>
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

const showPassword = ref(false)
const isFocused = ref(false)

const hasValue = computed(() => {
  return props.modelValue !== undefined && props.modelValue !== null && props.modelValue !== ''
})

function handleInput(event: Event) {
  const target = event.target as HTMLInputElement
  emit('update:modelValue', target.value)
}
</script>

<style scoped>
.password-editor {
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
  border-radius: 16px;
  transition: background 0.2s cubic-bezier(0.4, 0, 0.2, 1), outline 0.2s;
  outline: 2px solid transparent;
  outline-offset: -2px;
}

.field-wrapper:hover {
  background: color-mix(in srgb, var(--md-sys-color-on-surface) 8%, var(--md-sys-color-surface-container-highest));
}

.password-editor.is-focused .field-wrapper {
  outline-color: var(--md-sys-color-primary);
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

.password-input {
  width: 100%;
  height: 56px;
  padding: 0 48px 0 44px;
  font-size: 1rem;
  line-height: 24px;
  color: var(--md-sys-color-on-surface);
  background: transparent;
  border: none;
  transition: background 0.2s cubic-bezier(0.4, 0, 0.2, 1);
  caret-color: var(--md-sys-color-primary);
  letter-spacing: 0.5px;
}

.password-input:hover:not(:disabled) {
  background: color-mix(in srgb, var(--md-sys-color-on-surface) 4%, transparent);
}

.password-input:focus {
  outline: none;
}

.password-input:disabled {
  color: var(--md-sys-color-on-surface);
  opacity: 0.38;
  cursor: not-allowed;
}

.password-input::placeholder {
  color: var(--md-sys-color-on-surface-variant);
  letter-spacing: 0;
}

/* 底部边框装饰 */
.field-decoration {
  display: none;
}


/* 密码可见性切换按�?*/
.password-toggle {
  position: absolute;
  right: 8px;
  top: 50%;
  transform: translateY(-50%);
  display: flex;
  align-items: center;
  justify-content: center;
  width: 40px;
  height: 40px;
  border: none;
  background: transparent;
  color: var(--md-sys-color-on-surface-variant);
  border-radius: 50%;
  cursor: pointer;
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
}

.password-toggle .material-symbols-rounded {
  font-size: 22px;
}

.password-toggle:hover {
  background: var(--md-sys-color-surface-container);
  color: var(--md-sys-color-on-surface);
}
</style>
