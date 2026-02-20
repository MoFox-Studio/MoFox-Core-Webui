<!--
  @file SchemaFieldEditor.vue
  @description Schema 驱动的字段编辑器组件（新 API）

  功能说明：
  1. 根据 PluginSchemaField 的 type 自动渲染对应的输入组件
  2. 支持 boolean -> SwitchEditor
  3. 支持 number -> NumberEditor（不使用滑块）
  4. 支持 select -> SelectEditor
  5. 支持 array -> ListEditor
  6. 支持 textarea -> TextareaEditor
  7. 支持 string / object -> TextEditor
-->
<template>
  <div
    class="schema-field-editor"
    :class="{
      'has-error': errorMessage,
      'inline-field': field.type === 'boolean',
    }"
  >
    <!-- 开关类型（内联显示，包含 Label）-->
    <SwitchEditor
      v-if="field.type === 'boolean'"
      :field="compatField"
      :model-value="modelValue"
      @update:model-value="handleUpdate"
    />

    <!-- 其他类型 -->
    <template v-else>
      <!-- 字段头部 -->
      <div class="field-header">
        <span class="field-label">{{ field.name || field.key }}</span>
        <span class="field-type-badge">{{ getTypeLabel(field.type) }}</span>
      </div>

      <!-- 描述 -->
      <div v-if="field.description" class="field-description">
        <span class="material-symbols-rounded desc-icon">info</span>
        <span>{{ field.description }}</span>
      </div>

      <!-- 输入区域 -->
      <div class="field-input-container">
        <!-- Select -->
        <SelectEditor
          v-if="field.type === 'select'"
          :field="compatField"
          :model-value="modelValue"
          @update:model-value="handleUpdate"
        />
        <!-- Array / List -->
        <ListEditor
          v-else-if="field.type === 'array'"
          :field="compatField"
          :model-value="modelValue"
          @update:model-value="handleUpdate"
        />
        <!-- Number -->
        <NumberEditor
          v-else-if="field.type === 'number'"
          :field="compatField"
          :model-value="modelValue"
          @update:model-value="handleUpdate"
        />
        <!-- Textarea -->
        <TextareaEditor
          v-else-if="field.type === 'textarea'"
          :field="compatField"
          :model-value="modelValue"
          @update:model-value="handleUpdate"
        />
        <!-- Object -> JSON Editor -->
        <JsonEditor
          v-else-if="field.type === 'object'"
          :field="compatField"
          :model-value="modelValue"
          @update:model-value="handleUpdate"
        />
        <!-- String / 其他 -> TextEditor -->
        <TextEditor
          v-else
          :field="compatField"
          :model-value="modelValue"
          @update:model-value="handleUpdate"
        />
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
import { ref, computed } from 'vue'
import type { PluginSchemaField } from '@/api/pluginConfig'

// 导入编辑器组件
import SwitchEditor from './editors/SwitchEditor.vue'
import TextEditor from './editors/TextEditor.vue'
import NumberEditor from './editors/NumberEditor.vue'
import SelectEditor from './editors/SelectEditor.vue'
import TextareaEditor from './editors/TextareaEditor.vue'
import ListEditor from './editors/ListEditor.vue'
import JsonEditor from './editors/JsonEditor.vue'

const props = defineProps<{
  field: PluginSchemaField
  modelValue: unknown
}>()

const emit = defineEmits<{
  (e: 'update:modelValue', value: unknown): void
}>()

const errorMessage = ref('')

/**
 * 将新的 PluginSchemaField 转换为编辑器组件期望的兼容格式
 * 这样旧的编辑器组件不需要修改
 */
const compatField = computed(() => ({
  key: props.field.key,
  label: props.field.name || props.field.key,
  description: props.field.description,
  input_type: mapTypeToInputType(props.field.type),
  // select 选项
  choices: props.field.options?.map(o => ({ value: o.value, label: o.label })) ?? [],
  // 默认值
  default: props.field.default,
  // 以下是旧字段的占位，避免编辑器报错
  placeholder: '',
  hint: '',
  disabled: false,
  required: false,
  min: undefined,
  max: undefined,
  step: 1,
  min_items: undefined,
  max_items: undefined,
  item_type: 'string',
}))

function mapTypeToInputType(type: string): string {
  const map: Record<string, string> = {
    string: 'text',
    number: 'number',
    boolean: 'switch',
    array: 'list',
    object: 'json',
    textarea: 'textarea',
    select: 'select',
  }
  return map[type] || 'text'
}

// 类型标签
function getTypeLabel(type: string): string {
  const labels: Record<string, string> = {
    string: '文本',
    number: '数字',
    boolean: '开关',
    select: '选择',
    textarea: '多行文本',
    array: '列表',
    object: '对象',
  }
  return labels[type] || type
}

// 处理更新
function handleUpdate(value: unknown) {
  emit('update:modelValue', value)
  validateValue(value)
}

// 简单验证
function validateValue(_value: unknown) {
  errorMessage.value = ''
  // 可在此扩展验证逻辑
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

/* 描述 */
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
