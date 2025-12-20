<template>
  <div class="field-editor" :class="{ 'is-readonly': field.readonly }">
    <!-- 只读提示 -->
    <div v-if="field.readonly" class="readonly-badge">
      <Icon icon="lucide:lock" />
      只读
    </div>
    
    <!-- 布尔值 -->
    <label v-if="field.type === 'boolean'" class="toggle-switch">
      <input 
        type="checkbox" 
        :checked="Boolean(value)"
        :disabled="field.readonly"
        @change="emit('update', ($event.target as HTMLInputElement).checked)"
      />
      <span class="toggle-slider"></span>
      <span class="toggle-label">{{ Boolean(value) ? '启用' : '禁用' }}</span>
    </label>
    
    <!-- 数字 -->
    <input 
      v-else-if="field.type === 'integer' || field.type === 'number'"
      type="number"
      class="input"
      :value="value"
      :readonly="field.readonly"
      :disabled="field.readonly"
      @input="emit('update', parseNumber(($event.target as HTMLInputElement).value, field.type))"
    />
    
    <!-- 数组 -->
    <div v-else-if="field.type === 'array'" class="array-field">
      <div class="array-preview" @click="showArrayModal = true">
        <span class="array-count">{{ (value as unknown[])?.length || 0 }} 项</span>
        <Icon icon="lucide:edit-3" />
      </div>
      
      <!-- 数组编辑弹窗 -->
      <div v-if="showArrayModal" class="modal-overlay" @click.self="showArrayModal = false">
        <div class="modal-content">
          <div class="modal-header">
            <h3>
              <Icon icon="lucide:list" />
              编辑数组: {{ field.key }}
            </h3>
            <button class="close-btn" @click="showArrayModal = false">
              <Icon icon="lucide:x" />
            </button>
          </div>
          <div class="modal-body">
            <div class="array-items">
              <div v-for="(item, index) in arrayValue" :key="index" class="array-item">
                <input 
                  type="text" 
                  class="input" 
                  :value="typeof item === 'object' ? JSON.stringify(item) : item"
                  @input="updateArrayItem(index, ($event.target as HTMLInputElement).value)"
                />
                <button class="btn btn-sm btn-ghost btn-danger" @click="removeArrayItem(index)">
                  <Icon icon="lucide:trash-2" />
                </button>
              </div>
            </div>
            <button class="btn btn-sm btn-ghost add-item-btn" @click="addArrayItem">
              <Icon icon="lucide:plus" />
              添加项
            </button>
          </div>
          <div class="modal-footer">
            <button class="btn btn-secondary" @click="showArrayModal = false">取消</button>
            <button class="btn btn-primary" @click="saveArrayEdit">保存</button>
          </div>
        </div>
      </div>
    </div>
    
    <!-- 对象数组 -->
    <div v-else-if="field.type === 'array_of_objects'" class="object-array-field">
      <button class="btn btn-sm btn-ghost" @click="showObjectArrayModal = true">
        <Icon icon="lucide:edit-3" />
        编辑 {{ field.items_count || 0 }} 个配置项
      </button>
      
      <!-- 对象数组编辑弹窗 -->
      <div v-if="showObjectArrayModal" class="modal-overlay" @click.self="showObjectArrayModal = false">
        <div class="modal-content modal-large">
          <div class="modal-header">
            <h3>
              <Icon icon="lucide:layers" />
              编辑: {{ field.key }}
            </h3>
            <button class="close-btn" @click="showObjectArrayModal = false">
              <Icon icon="lucide:x" />
            </button>
          </div>
          <div class="modal-body">
            <div class="object-array-tabs">
              <button 
                v-for="(item, index) in objectArrayValue" 
                :key="index"
                :class="['tab-btn', { active: activeObjectIndex === index }]"
                @click="activeObjectIndex = index"
              >
                {{ getObjectLabel(item, index) }}
                <span class="tab-close" @click.stop="removeObjectArrayItem(index)">
                  <Icon icon="lucide:x" />
                </span>
              </button>
              <button class="btn btn-sm btn-ghost add-tab-btn" @click="addObjectArrayItem">
                <Icon icon="lucide:plus" />
              </button>
            </div>
            <div v-if="objectArrayValue.length > 0" class="object-fields">
              <div 
                v-for="(val, key) in objectArrayValue[activeObjectIndex]" 
                :key="key" 
                class="field-row"
              >
                <div class="field-label">
                  <span class="field-name">{{ key }}</span>
                </div>
                <div class="field-input">
                  <input 
                    v-if="typeof val !== 'object' || val === null"
                    type="text"
                    class="input"
                    :value="formatObjectValue(val)"
                    @input="updateObjectField(key as string, ($event.target as HTMLInputElement).value)"
                  />
                  <textarea 
                    v-else
                    class="input textarea"
                    :value="JSON.stringify(val, null, 2)"
                    @input="updateObjectField(key as string, ($event.target as HTMLInputElement).value, true)"
                  ></textarea>
                </div>
              </div>
            </div>
          </div>
          <div class="modal-footer">
            <button class="btn btn-secondary" @click="showObjectArrayModal = false">取消</button>
            <button class="btn btn-primary" @click="saveObjectArrayEdit">保存</button>
          </div>
        </div>
      </div>
    </div>
    
    <!-- 对象 -->
    <div v-else-if="field.type === 'object'" class="object-field">
      <button class="btn btn-sm btn-ghost" @click="openObjectEditor" :disabled="field.readonly">
        <Icon icon="lucide:edit-3" />
        编辑对象
      </button>
    </div>
    
    <!-- 多行文本 -->
    <textarea 
      v-else-if="field.type === 'textarea' || isMultilineText"
      class="input textarea"
      :value="value as string"
      :readonly="field.readonly"
      :disabled="field.readonly"
      @input="emit('update', ($event.target as HTMLInputElement).value)"
    ></textarea>
    
    <!-- 字符串（默认） -->
    <input 
      v-else
      type="text"
      class="input"
      :value="value as string"
      :readonly="field.readonly"
      :disabled="field.readonly"
      @input="emit('update', ($event.target as HTMLInputElement).value)"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { Icon } from '@iconify/vue'
import type { ConfigSchemaField } from '@/api'

const props = defineProps<{
  field: ConfigSchemaField
  value: unknown
}>()

const emit = defineEmits<{
  (e: 'update', value: unknown): void
}>()

// 数组编辑
const showArrayModal = ref(false)
const arrayValue = ref<unknown[]>([])

// 对象数组编辑
const showObjectArrayModal = ref(false)
const objectArrayValue = ref<Record<string, unknown>[]>([])
const activeObjectIndex = ref(0)

// 计算属性
const isMultilineText = computed(() => {
  const val = props.value
  return typeof val === 'string' && (val.includes('\n') || val.length > 100)
})

// 初始化数组值
watch(() => [showArrayModal.value, props.value], ([show]) => {
  if (show) {
    arrayValue.value = Array.isArray(props.value) ? [...props.value] : []
  }
}, { immediate: true })

// 初始化对象数组值
watch(() => [showObjectArrayModal.value, props.value], ([show]) => {
  if (show) {
    objectArrayValue.value = Array.isArray(props.value) 
      ? props.value.map(v => ({ ...v as Record<string, unknown> }))
      : []
    activeObjectIndex.value = 0
  }
}, { immediate: true })

function parseNumber(value: string, type: string): number {
  if (type === 'integer') {
    return parseInt(value) || 0
  }
  return parseFloat(value) || 0
}

function updateArrayItem(index: number, value: string) {
  arrayValue.value[index] = value
}

function removeArrayItem(index: number) {
  arrayValue.value.splice(index, 1)
}

function addArrayItem() {
  arrayValue.value.push('')
}

function saveArrayEdit() {
  emit('update', [...arrayValue.value])
  showArrayModal.value = false
}

function getObjectLabel(obj: Record<string, unknown>, index: number): string {
  if (obj.name) return String(obj.name)
  if (obj.model_identifier) return String(obj.model_identifier)
  return `项 ${index + 1}`
}

function formatObjectValue(value: unknown): string {
  if (typeof value === 'string') return value
  if (typeof value === 'number' || typeof value === 'boolean') return String(value)
  if (Array.isArray(value)) return JSON.stringify(value)
  return String(value)
}

function updateObjectField(key: string, value: string, isJson: boolean = false) {
  if (activeObjectIndex.value >= objectArrayValue.value.length) return
  
  let parsedValue: unknown = value
  
  if (isJson) {
    try {
      parsedValue = JSON.parse(value)
    } catch {
      parsedValue = value
    }
  } else if (value === 'true') {
    parsedValue = true
  } else if (value === 'false') {
    parsedValue = false
  } else if (/^\d+$/.test(value)) {
    parsedValue = parseInt(value)
  } else if (/^\d+\.\d+$/.test(value)) {
    parsedValue = parseFloat(value)
  }
  
  const targetObj = objectArrayValue.value[activeObjectIndex.value]
  if (targetObj) {
    targetObj[key] = parsedValue
  }
}

function addObjectArrayItem() {
  if (objectArrayValue.value.length > 0) {
    const template = { ...objectArrayValue.value[0] }
    for (const key in template) {
      if (typeof template[key] === 'string') template[key] = ''
      else if (typeof template[key] === 'number') template[key] = 0
      else if (typeof template[key] === 'boolean') template[key] = false
      else if (Array.isArray(template[key])) template[key] = []
    }
    objectArrayValue.value.push(template)
  } else {
    objectArrayValue.value.push({})
  }
  activeObjectIndex.value = objectArrayValue.value.length - 1
}

function removeObjectArrayItem(index: number) {
  if (objectArrayValue.value.length <= 1) return
  objectArrayValue.value.splice(index, 1)
  if (activeObjectIndex.value >= objectArrayValue.value.length) {
    activeObjectIndex.value = objectArrayValue.value.length - 1
  }
}

function saveObjectArrayEdit() {
  emit('update', [...objectArrayValue.value])
  showObjectArrayModal.value = false
}

function openObjectEditor() {
  const value = props.value
  if (typeof value === 'object' && value !== null) {
    objectArrayValue.value = [{ ...value as Record<string, unknown> }]
    activeObjectIndex.value = 0
    showObjectArrayModal.value = true
  }
}
</script>

<style scoped>
.field-editor {
  width: 100%;
  position: relative;
}

.field-editor.is-readonly {
  opacity: 0.8;
}

.readonly-badge {
  position: absolute;
  top: -8px;
  right: -8px;
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 2px 8px;
  background: var(--bg-tertiary);
  border-radius: 10px;
  font-size: 11px;
  color: var(--text-tertiary);
  z-index: 1;
}

.readonly-badge svg {
  font-size: 12px;
}

.input {
  width: 100%;
  padding: 10px 14px;
  border: 1px solid var(--border-color);
  border-radius: var(--radius);
  background: var(--bg-primary);
  color: var(--text-primary);
  font-family: 'Roboto Mono', 'Noto Sans SC', 'Microsoft YaHei', monospace !important;
  font-size: 14px;
  outline: none;
  transition: all var(--transition-fast);
}

.input:focus {
  border-color: var(--primary);
  box-shadow: 0 0 0 3px var(--primary-bg);
}

.input:disabled,
.input:read-only {
  background: var(--bg-secondary);
  color: var(--text-secondary);
  cursor: not-allowed;
}

.textarea {
  min-height: 100px;
  resize: vertical;
  font-family: 'Roboto Mono', 'Noto Sans SC', 'Microsoft YaHei', monospace !important;
  font-size: 13px;
  line-height: 1.5;
}

/* Toggle 开关 */
.toggle-switch {
  display: flex;
  align-items: center;
  gap: 12px;
  cursor: pointer;
}

.toggle-switch input {
  display: none;
}

.toggle-slider {
  width: 48px;
  height: 26px;
  background: var(--bg-hover);
  border-radius: 13px;
  position: relative;
  transition: background var(--transition-fast);
}

.toggle-slider::after {
  content: '';
  position: absolute;
  top: 50%;
  left: 3px;
  width: 20px;
  height: 20px;
  background: white;
  border-radius: 50%;
  transform: translateY(-50%);
  transition: transform var(--transition-fast);
  box-shadow: var(--shadow-sm);
}

.toggle-switch input:checked + .toggle-slider {
  background: var(--primary);
}

.toggle-switch input:checked + .toggle-slider::after {
  transform: translate(22px, -50%);
}

.toggle-label {
  font-size: 14px;
  color: var(--text-secondary);
}

/* 数组预览 */
.array-preview {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 14px;
  background: var(--bg-primary);
  border: 1px solid var(--border-color);
  border-radius: var(--radius);
  cursor: pointer;
  transition: all var(--transition-fast);
}

.array-preview:hover {
  border-color: var(--primary);
}

.array-count {
  font-size: 14px;
  color: var(--text-secondary);
}

/* 按钮样式 */
.btn {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  padding: 8px 16px;
  border: none;
  border-radius: var(--radius);
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: all var(--transition-fast);
}

.btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn-primary {
  background: var(--primary);
  color: white;
}

.btn-primary:hover:not(:disabled) {
  background: var(--primary-hover);
}

.btn-secondary {
  background: var(--bg-secondary);
  color: var(--text-primary);
}

.btn-secondary:hover:not(:disabled) {
  background: var(--bg-hover);
}

.btn-ghost {
  background: transparent;
  color: var(--text-secondary);
}

.btn-ghost:hover:not(:disabled) {
  background: var(--bg-secondary);
  color: var(--text-primary);
}

.btn-sm {
  padding: 6px 12px;
  font-size: 12px;
}

.btn-danger:hover {
  background: rgba(239, 68, 68, 0.1);
  color: #ef4444;
}

/* 弹窗样式 */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.6);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  backdrop-filter: blur(4px);
}

.modal-content {
  background: var(--bg-primary);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-lg);
  width: 90%;
  max-width: 500px;
  max-height: 80vh;
  overflow: hidden;
  animation: modalIn 0.2s ease;
  display: flex;
  flex-direction: column;
}

.modal-content.modal-large {
  max-width: 800px;
}

@keyframes modalIn {
  from { opacity: 0; transform: scale(0.95); }
  to { opacity: 1; transform: scale(1); }
}

.modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 20px;
  border-bottom: 1px solid var(--border-color);
}

.modal-header h3 {
  display: flex;
  align-items: center;
  gap: 8px;
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary);
}

.close-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  border: none;
  background: transparent;
  border-radius: var(--radius);
  color: var(--text-secondary);
  cursor: pointer;
  transition: all var(--transition-fast);
}

.close-btn:hover {
  background: var(--bg-secondary);
  color: var(--text-primary);
}

.modal-body {
  padding: 20px;
  overflow-y: auto;
  flex: 1;
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  padding: 16px 20px;
  border-top: 1px solid var(--border-color);
}

/* 数组编辑 */
.array-items {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-bottom: 12px;
}

.array-item {
  display: flex;
  gap: 8px;
}

.array-item .input {
  flex: 1;
}

.add-item-btn {
  width: 100%;
  justify-content: center;
  border: 1px dashed var(--border-color);
}

/* 对象数组编辑 */
.object-array-tabs {
  display: flex;
  gap: 4px;
  flex-wrap: wrap;
  margin-bottom: 16px;
  padding-bottom: 12px;
  border-bottom: 1px solid var(--border-color);
}

.tab-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 14px;
  border: none;
  background: var(--bg-secondary);
  border-radius: var(--radius-sm);
  font-size: 13px;
  color: var(--text-secondary);
  cursor: pointer;
  transition: all var(--transition-fast);
  position: relative;
  padding-right: 28px;
}

.tab-btn:hover {
  background: var(--bg-hover);
  color: var(--text-primary);
}

.tab-btn.active {
  background: var(--primary-bg);
  color: var(--primary);
}

.tab-close {
  position: absolute;
  right: 6px;
  top: 50%;
  transform: translateY(-50%);
  width: 16px;
  height: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  opacity: 0;
  transition: all var(--transition-fast);
}

.tab-btn:hover .tab-close {
  opacity: 1;
}

.tab-close:hover {
  background: rgba(239, 68, 68, 0.2);
  color: #ef4444;
}

.add-tab-btn {
  padding: 8px 12px;
}

.object-fields {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.field-row {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.field-label {
  display: flex;
  align-items: center;
  gap: 6px;
}

.field-name {
  font-size: 13px;
  font-weight: 500;
  color: var(--text-secondary);
}

.field-input {
  width: 100%;
}
</style>
