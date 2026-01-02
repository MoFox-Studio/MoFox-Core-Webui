<!--
  @file SchemaFieldEditor.vue
  @description Schema 驱动的字段编辑器组件
  
  功能说明：
  1. 根据 SchemaField 的 input_type 自动渲染对应的输入组件
  2. 支持验证规则（min/max/pattern 等）
  3. 支持条件显示（depends_on）
  4. 支持所有增�?UI 属性（placeholder/hint/icon 等）
-->
<template>
  <div 
    class="schema-field-editor"
    :class="{
      'is-disabled': field.disabled,
      'is-hidden': field.hidden,
      'is-required': field.required,
      'has-error': errorMessage,
      'inline-field': field.input_type === 'switch'
    }"
  >
    <!-- 开关类型（内联显示，包含 Label）-->
    <SwitchEditor
      v-if="field.input_type === 'switch'"
      :field="field"
      :model-value="modelValue"
      @update:model-value="handleUpdate"
    />

    <!-- 其他类型 -->
    <template v-else>
      <!-- 字段头部 -->
      <div class="field-header">
        <span v-if="field.icon" class="material-symbols-rounded field-icon">{{ field.icon }}</span>
        <span class="field-label">{{ field.label || field.key }}</span>
        <span class="field-type-badge">{{ getTypeLabel(field.input_type) }}</span>
        <span v-if="field.required" class="required-badge">必填</span>
      </div>

      <!-- 描述 -->
      <div v-if="field.description" class="field-description">
        <span class="material-symbols-rounded desc-icon">info</span>
        <span>{{ field.description }}</span>
      </div>

      <!-- 输入区域 -->
      <div class="field-input-container">
        <component
          :is="getEditorComponent(field.input_type)"
          :field="field"
          :model-value="modelValue"
          @update:model-value="handleUpdate"
        />
      </div>

      <!-- 提示信息 -->
      <div v-if="field.hint && !field.description" class="field-hint">
        <span class="material-symbols-rounded">lightbulb</span>
        {{ field.hint }}
      </div>

      <!-- 示例 -->
      <div v-if="field.example" class="field-example">
        <span class="material-symbols-rounded">code</span>
        示例: {{ field.example }}
      </div>

      <!-- 错误信息 -->
      <div v-if="errorMessage" class="field-error">
        <span class="material-symbols-rounded">error</span>
        {{ errorMessage }}
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import type { SchemaField } from '@/api/pluginConfigApi'

// 导入编辑器组件
import SwitchEditor from './editors/SwitchEditor.vue'
import TextEditor from './editors/TextEditor.vue'
import PasswordEditor from './editors/PasswordEditor.vue'
import NumberEditor from './editors/NumberEditor.vue'
import SliderEditor from './editors/SliderEditor.vue'
import SelectEditor from './editors/SelectEditor.vue'
import TextareaEditor from './editors/TextareaEditor.vue'
import ListEditor from './editors/ListEditor.vue'
import JsonEditor from './editors/JsonEditor.vue'
import ColorEditor from './editors/ColorEditor.vue'
import FileEditor from './editors/FileEditor.vue'

const props = defineProps<{
  field: SchemaField
  modelValue: unknown
}>()

const emit = defineEmits<{
  (e: 'update:modelValue', value: unknown): void
}>()

const errorMessage = ref('')

// 获取编辑器组件
function getEditorComponent(inputType: string) {
  const map: Record<string, any> = {
    text: TextEditor,
    password: PasswordEditor,
    number: NumberEditor,
    slider: SliderEditor,
    select: SelectEditor,
    textarea: TextareaEditor,
    list: ListEditor,
    json: JsonEditor,
    color: ColorEditor,
    file: FileEditor,
  }
  return map[inputType] || TextEditor
}

// 类型标签
function getTypeLabel(inputType: string): string {
  const labels: Record<string, string> = {
    text: '文本',
    password: '密码',
    number: '数字',
    slider: '滑块',
    switch: '开关',
    select: '选择',
    textarea: '多行文本',
    list: '列表',
    json: 'JSON',
    color: '颜色',
    file: '路径',
  }
  return labels[inputType] || inputType
}

// 处理更新
function handleUpdate(value: unknown) {
  emit('update:modelValue', value)
  validateValue(value)
}

// 验证
function validateValue(value: unknown) {
  errorMessage.value = ''
  
  // 必填验证
  if (props.field.required && (value === '' || value === null || value === undefined)) {
    errorMessage.value = '此字段为必填项'
    return
  }
  
  // 数字范围验证
  if (typeof value === 'number') {
    if (props.field.min !== undefined && value < props.field.min) {
      errorMessage.value = `最小值为 ${props.field.min}`
      return
    }
    if (props.field.max !== undefined && value > props.field.max) {
      errorMessage.value = `最大值为 ${props.field.max}`
      return
    }
  }
  
  // 字符串长度验证
  if (typeof value === 'string') {
    if (props.field.min_length && value.length < props.field.min_length) {
      errorMessage.value = `最少 ${props.field.min_length} 个字符`
      return
    }
    if (props.field.max_length && value.length > props.field.max_length) {
      errorMessage.value = `最多 ${props.field.max_length} 个字符`
      return
    }
    
    // 正则验证
    if (props.field.pattern) {
      const regex = new RegExp(props.field.pattern)
      if (!regex.test(value)) {
        errorMessage.value = '格式不正确'
        return
      }
    }
  }
}
</script>

<style scoped>
.schema-field-editor {
  display: flex;
  flex-direction: column;
  gap: 10px;
  padding: 16px;
  background: var(--md-sys-color-surface);
  border-radius: 16px;
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
  border: 1px solid transparent;
  position: relative;
  overflow: hidden;
}

.schema-field-editor::before {
  content: '';
  position: absolute;
  left: 0;
  top: 0;
  bottom: 0;
  width: 3px;
  background: var(--md-sys-color-primary);
  opacity: 0;
  transition: opacity 0.2s;
}

.schema-field-editor:hover {
  background: var(--md-sys-color-surface-container);
  border-color: var(--md-sys-color-outline-variant);
}

.schema-field-editor:focus-within {
  background: var(--md-sys-color-surface-container);
  border-color: var(--md-sys-color-primary);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
}

.schema-field-editor:focus-within::before {
  opacity: 1;
}

.schema-field-editor.inline-field {
  flex-direction: row;
  align-items: center;
  justify-content: space-between;
  padding: 8px 16px;
  background: transparent;
  border: none;
  border-radius: 0;
}

.schema-field-editor.inline-field::before {
  display: none;
}

.schema-field-editor.inline-field:hover {
  background: color-mix(in srgb, var(--md-sys-color-primary) 4%, transparent);
}

.schema-field-editor.is-disabled {
  opacity: 0.5;
  pointer-events: none;
}

.schema-field-editor.is-hidden {
  display: none;
}

.schema-field-editor.has-error {
  border-color: var(--md-sys-color-error);
  background: color-mix(in srgb, var(--md-sys-color-error) 4%, var(--md-sys-color-surface));
}

.schema-field-editor.has-error::before {
  background: var(--md-sys-color-error);
  opacity: 1;
}

.schema-field-editor.has-error .field-label {
  color: var(--md-sys-color-error);
}

/* 字段头部 */
.field-header {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}

.field-icon {
  font-size: 22px;
  color: var(--md-sys-color-primary);
  padding: 6px;
  background: var(--md-sys-color-primary-container);
  border-radius: 10px;
}

.field-label {
  font-size: 15px;
  font-weight: 600;
  color: var(--md-sys-color-on-surface);
  letter-spacing: 0.15px;
}

.field-type-badge {
  font-size: 11px;
  padding: 3px 8px;
  background: var(--md-sys-color-surface-container-highest);
  color: var(--md-sys-color-on-surface-variant);
  border-radius: 8px;
  font-weight: 500;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.required-badge {
  font-size: 11px;
  padding: 3px 8px;
  background: var(--md-sys-color-error-container);
  color: var(--md-sys-color-on-error-container);
  border-radius: 8px;
  font-weight: 600;
}

/* 描述和提示 */
.field-description {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  font-size: 13px;
  line-height: 1.5;
  color: var(--md-sys-color-on-surface-variant);
  padding: 10px 12px;
  background: var(--md-sys-color-surface-container);
  border-radius: 12px;
}

.field-description .desc-icon {
  font-size: 18px;
  flex-shrink: 0;
  margin-top: 1px;
  color: var(--md-sys-color-primary);
  opacity: 0.8;
}

.field-hint {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: var(--md-sys-color-on-surface-variant);
  opacity: 0.8;
}

.field-hint .material-symbols-rounded {
  font-size: 16px;
  color: #f59e0b;
}

.field-example {
  display: flex;
  align-items: center;
  gap: 8px;
  font-family: 'JetBrains Mono', 'Fira Code', monospace;
  font-size: 12px;
  background: var(--md-sys-color-surface-container-highest);
  padding: 10px 14px;
  border-radius: 10px;
  color: var(--md-sys-color-on-surface-variant);
}

.field-example .material-symbols-rounded {
  font-size: 16px;
  color: var(--md-sys-color-primary);
}

/* 输入区域 */
.field-input-container {
  width: 100%;
}

/* 错误信息 */
.field-error {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
  font-weight: 500;
  color: var(--md-sys-color-error);
  padding: 8px 12px;
  background: var(--md-sys-color-error-container);
  border-radius: 10px;
  animation: shakeError 0.4s ease-in-out;
}

.field-error .material-symbols-rounded {
  font-size: 18px;
}

@keyframes shakeError {
  0%, 100% { transform: translateX(0); }
  20% { transform: translateX(-4px); }
  40% { transform: translateX(4px); }
  60% { transform: translateX(-4px); }
  80% { transform: translateX(4px); }
}
</style>
