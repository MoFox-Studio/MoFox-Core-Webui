<!--
  @file ListEditor.vue
  @description 列表编辑器组件 - Material Design 3 风格
-->
<template>
  <div class="list-editor">
    <!-- 列表头部 -->
    <div class="list-header">
      <div class="header-info">
        <span class="material-symbols-rounded header-icon">list</span>
        <span class="item-count">{{ listValue.length }} </span>
      </div>
      <div v-if="field.min_items || field.max_items" class="limit-badge">
        <span v-if="field.min_items">最小{{ field.min_items }}</span>
        <span v-if="field.min_items && field.max_items"> / </span>
        <span v-if="field.max_items">最大{{ field.max_items }}</span>
      </div>
    </div>

    <div class="list-items">
      <!-- 字符串列表 -->
      <template v-if="!field.item_type || field.item_type === 'string'">
        <TransitionGroup name="list">
          <div 
            v-for="(item, index) in listValue" 
            :key="'item-' + index" 
            class="list-item"
            :class="{ 'is-dragging': draggedIndex === index }"
            draggable="true"
            @dragstart="onDragStart(index, $event)"
            @dragover.prevent="onDragOver(index)"
            @drop="onDrop(index)"
            @dragend="onDragEnd"
          >
            <div class="item-handle">
              <span class="material-symbols-rounded">drag_indicator</span>
            </div>
            <div class="item-index">{{ index + 1 }}</div>
            <div class="item-input-wrapper">
              <input 
                type="text"
                class="item-input"
                :value="item"
                :placeholder="field.placeholder || `输入第 ${index + 1} 项`"
                @input="updateListItem(index, ($event.target as HTMLInputElement).value)"
              >
            </div>
            <button 
              type="button"
              class="item-remove-button"
              :disabled="field.min_items !== undefined && listValue.length <= field.min_items"
              @click="removeListItem(index)"
              title="删除"
            >
              <span class="material-symbols-rounded">close</span>
            </button>
          </div>
        </TransitionGroup>
      </template>

      <!-- 数字列表 -->
      <template v-else-if="field.item_type === 'number'">
        <TransitionGroup name="list">
          <div 
            v-for="(item, index) in listValue" 
            :key="'item-' + index" 
            class="list-item"
            :class="{ 'is-dragging': draggedIndex === index }"
            draggable="true"
            @dragstart="onDragStart(index, $event)"
            @dragover.prevent="onDragOver(index)"
            @drop="onDrop(index)"
            @dragend="onDragEnd"
          >
            <div class="item-handle">
              <span class="material-symbols-rounded">drag_indicator</span>
            </div>
            <div class="item-index">{{ index + 1 }}</div>
            <div class="item-input-wrapper">
              <input 
                type="number"
                class="item-input"
                :value="item"
                :placeholder="field.placeholder || `输入第 ${index + 1} 项`"
                :min="field.min"
                :max="field.max"
                :step="field.step || 1"
                @input="updateListItem(index, parseFloat(($event.target as HTMLInputElement).value) || 0)"
              >
            </div>
            <button 
              type="button"
              class="item-remove-button"
              :disabled="field.min_items !== undefined && listValue.length <= field.min_items"
              @click="removeListItem(index)"
              title="删除"
            >
              <span class="material-symbols-rounded">close</span>
            </button>
          </div>
        </TransitionGroup>
      </template>

      <!-- 对象列表 -->
      <template v-else-if="field.item_type === 'object' && field.item_fields">
        <TransitionGroup name="list">
          <div 
            v-for="(item, index) in listValue" 
            :key="'item-' + index" 
            class="list-item object-item"
            :class="{ 'is-expanded': expandedItems.includes(index), 'is-dragging': draggedIndex === index }"
            draggable="true"
            @dragstart="onDragStart(index, $event)"
            @dragover.prevent="onDragOver(index)"
            @drop="onDrop(index)"
            @dragend="onDragEnd"
          >
            <div class="object-item-header" @click="toggleObjectItem(index)">
              <div class="item-handle" @click.stop>
                <span class="material-symbols-rounded">drag_indicator</span>
              </div>
              <div class="item-index">{{ index + 1 }}</div>
              <span class="object-item-title">{{ getObjectItemTitle(item, index) }}</span>
              <div class="object-item-actions">
                <button 
                  type="button"
                  class="expand-button"
                  @click.stop="toggleObjectItem(index)"
                >
                  <span class="material-symbols-rounded">
                    {{ expandedItems.includes(index) ? 'expand_less' : 'expand_more' }}
                  </span>
                </button>
                <button 
                  type="button"
                  class="item-remove-button"
                  :disabled="field.min_items !== undefined && listValue.length <= field.min_items"
                  @click.stop="removeListItem(index)"
                  title="删除"
                >
                  <span class="material-symbols-rounded">close</span>
                </button>
              </div>
            </div>
            
            <Transition name="expand">
              <div v-show="expandedItems.includes(index)" class="object-item-content">
                <template v-for="subField in field.item_fields" :key="subField.key">
                  <SchemaFieldEditor
                    :field="subField"
                    :model-value="item[subField.key]"
                    @update:model-value="(v: unknown) => updateObjectItemField(index, subField.key, v)"
                  />
                </template>
              </div>
            </Transition>
          </div>
        </TransitionGroup>
      </template>

      <!-- 空状态 -->
      <div v-if="listValue.length === 0" class="empty-state">
        <span class="material-symbols-rounded empty-icon">inbox</span>
        <span class="empty-text">暂无项目，点击下方按钮添加</span>
      </div>
    </div>

    <!-- 添加按钮 -->
    <button 
      type="button"
      class="add-button"
      :disabled="field.max_items !== undefined && listValue.length >= field.max_items"
      @click="addListItem"
    >
      <span class="material-symbols-rounded">add</span>
      <span>添加一项</span>
    </button>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import type { SchemaField } from '@/api/pluginConfigApi'
import SchemaFieldEditor from '../SchemaFieldEditor.vue'

const props = defineProps<{
  field: SchemaField
  modelValue: unknown
}>()

const emit = defineEmits<{
  (e: 'update:modelValue', value: unknown): void
}>()

// 列表值
const listValue = computed(() => {
  return Array.isArray(props.modelValue) ? props.modelValue : []
})

// 展开的项目
const expandedItems = ref<number[]>([0]) // 默认展开第一项

// 拖拽状态
const draggedIndex = ref<number | null>(null)

// 更新列表项
function updateListItem(index: number, value: unknown) {
  const newList = [...listValue.value]
  newList[index] = value
  emit('update:modelValue', newList)
}

// 更新对象列表项字段
function updateObjectItemField(index: number, key: string, value: unknown) {
  const newList = [...listValue.value]
  newList[index] = { ...newList[index], [key]: value }
  emit('update:modelValue', newList)
}

// 添加列表项
function addListItem() {
  const newItem = getDefaultItemValue()
  const newList = [...listValue.value, newItem]
  emit('update:modelValue', newList)
  
  // 如果是对象，自动展开新项
  if (props.field.item_type === 'object') {
    expandedItems.value.push(newList.length - 1)
  }
}

// 获取默认值
function getDefaultItemValue() {
  if (props.field.item_type === 'number') return 0
  if (props.field.item_type === 'object') {
    const obj: Record<string, unknown> = {}
    if (props.field.item_fields) {
      for (const f of props.field.item_fields) {
        obj[f.key] = f.default
      }
    }
    return obj
  }
  return ''
}

// 删除列表项
function removeListItem(index: number) {
  const newList = [...listValue.value]
  newList.splice(index, 1)
  emit('update:modelValue', newList)
  
  // 更新展开状态
  expandedItems.value = expandedItems.value
    .filter(i => i !== index)
    .map(i => i > index ? i - 1 : i)
}

// 切换展开
function toggleObjectItem(index: number) {
  const i = expandedItems.value.indexOf(index)
  if (i > -1) {
    expandedItems.value.splice(i, 1)
  } else {
    expandedItems.value.push(index)
  }
}

// 获取对象项标题
function getObjectItemTitle(item: any, index: number): string {
  // 尝试找到第一个字符串字段作为标题
  if (props.field.item_fields) {
    const titleField = props.field.item_fields.find(f => f.input_type === 'text' || f.input_type === 'select')
    if (titleField && item[titleField.key]) {
      return String(item[titleField.key])
    }
  }
  return `项目 ${index + 1}`
}

// 拖拽处理
function onDragStart(index: number, event: DragEvent) {
  draggedIndex.value = index
  if (event.dataTransfer) {
    event.dataTransfer.effectAllowed = 'move'
    event.dataTransfer.setData('text/plain', String(index))
  }
}

function onDragOver(index: number) {
  // 允许放置
}

function onDrop(index: number) {
  if (draggedIndex.value === null || draggedIndex.value === index) return
  
  const newList = [...listValue.value]
  const [movedItem] = newList.splice(draggedIndex.value, 1)
  newList.splice(index, 0, movedItem)
  
  emit('update:modelValue', newList)
  draggedIndex.value = null
}

function onDragEnd() {
  draggedIndex.value = null
}
</script>

<style scoped>
.list-editor {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

/* 列表头部 */
.list-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 12px;
  background: var(--md-sys-color-surface-container);
  border-radius: 12px;
}

.header-info {
  display: flex;
  align-items: center;
  gap: 8px;
}

.header-icon {
  font-size: 20px;
  color: var(--md-sys-color-primary);
}

.item-count {
  font-size: 13px;
  font-weight: 500;
  color: var(--md-sys-color-on-surface-variant);
}

.limit-badge {
  font-size: 11px;
  padding: 4px 10px;
  background: var(--md-sys-color-surface-container-highest);
  color: var(--md-sys-color-on-surface-variant);
  border-radius: 12px;
}

/* 列表项容器 */
.list-items {
  display: flex;
  flex-direction: column;
  gap: 8px;
  min-height: 48px;
}

/* 列表项 */
.list-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px;
  background: var(--md-sys-color-surface-container);
  border-radius: 16px;
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
  border: 1px solid transparent;
}

.list-item:hover {
  background: var(--md-sys-color-surface-container-high);
  border-color: var(--md-sys-color-outline-variant);
}

.list-item.is-dragging {
  opacity: 0.5;
  transform: scale(0.98);
}

.list-item.object-item {
  flex-direction: column;
  align-items: stretch;
  padding: 0;
  overflow: hidden;
}

/* 拖拽手柄 */
.item-handle {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  color: var(--md-sys-color-on-surface-variant);
  cursor: grab;
  opacity: 0.5;
  transition: opacity 0.2s;
  flex-shrink: 0;
}

.item-handle:hover {
  opacity: 1;
}

.item-handle:active {
  cursor: grabbing;
}

.item-handle .material-symbols-rounded {
  font-size: 20px;
}

/* 项目索引 */
.item-index {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 24px;
  height: 24px;
  background: var(--md-sys-color-primary-container);
  color: var(--md-sys-color-on-primary-container);
  font-size: 12px;
  font-weight: 600;
  border-radius: 8px;
  flex-shrink: 0;
}

/* 输入框 */
.item-input-wrapper {
  flex: 1;
}

.item-input {
  width: 100%;
  height: 40px;
  padding: 0 12px;
  font-size: 14px;
  color: var(--md-sys-color-on-surface);
  background: var(--md-sys-color-surface-container-highest);
  border: 1px solid transparent;
  border-radius: 20px;
  transition: all 0.2s;
}

.item-input:hover {
  background: color-mix(in srgb, var(--md-sys-color-on-surface) 5%, var(--md-sys-color-surface-container-highest));
}

.item-input:focus {
  outline: none;
  border-color: var(--md-sys-color-primary);
  background: var(--md-sys-color-surface);
}

.item-input::placeholder {
  color: var(--md-sys-color-on-surface-variant);
  opacity: 0.7;
}

/* 删除按钮 */
.item-remove-button {
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
  transition: all 0.2s;
  flex-shrink: 0;
  opacity: 0.6;
}

.item-remove-button:hover:not(:disabled) {
  background: var(--md-sys-color-error-container);
  color: var(--md-sys-color-on-error-container);
  opacity: 1;
}

.item-remove-button:disabled {
  opacity: 0.2;
  cursor: not-allowed;
}

.item-remove-button .material-symbols-rounded {
  font-size: 18px;
}

/* 对象项样式 */
.object-item-header {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px;
  background: var(--md-sys-color-surface-container);
  cursor: pointer;
  user-select: none;
  transition: background 0.2s;
}

.object-item-header:hover {
  background: var(--md-sys-color-surface-container-high);
}

.object-item-title {
  flex: 1;
  font-size: 14px;
  font-weight: 500;
  color: var(--md-sys-color-on-surface);
}

.object-item-actions {
  display: flex;
  gap: 4px;
}

.expand-button {
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
  transition: all 0.2s;
}

.expand-button:hover {
  background: var(--md-sys-color-surface-container-highest);
  color: var(--md-sys-color-on-surface);
}

.object-item-content {
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 12px;
  background: var(--md-sys-color-surface);
  border-top: 1px solid var(--md-sys-color-outline-variant);
}

/* 空状态 */
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 32px 16px;
  gap: 8px;
}

.empty-icon {
  font-size: 40px;
  color: var(--md-sys-color-on-surface-variant);
  opacity: 0.4;
}

.empty-text {
  font-size: 13px;
  color: var(--md-sys-color-on-surface-variant);
  opacity: 0.7;
}

/* 添加按钮 */
.add-button {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  height: 48px;
  padding: 0 24px;
  background: var(--md-sys-color-primary-container);
  color: var(--md-sys-color-on-primary-container);
  border: none;
  border-radius: 24px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
}

.add-button:hover:not(:disabled) {
  background: var(--md-sys-color-primary);
  color: var(--md-sys-color-on-primary);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
}

.add-button:active:not(:disabled) {
  transform: scale(0.98);
}

.add-button:disabled {
  background: var(--md-sys-color-surface-container-highest);
  color: var(--md-sys-color-on-surface);
  opacity: 0.38;
  cursor: not-allowed;
}

.add-button .material-symbols-rounded {
  font-size: 20px;
}

/* 列表动画 */
.list-enter-active,
.list-leave-active {
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.list-enter-from {
  opacity: 0;
  transform: translateX(-20px);
}

.list-leave-to {
  opacity: 0;
  transform: translateX(20px);
}

.list-move {
  transition: transform 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

/* 展开动画 */
.expand-enter-active,
.expand-leave-active {
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  overflow: hidden;
}

.expand-enter-from,
.expand-leave-to {
  opacity: 0;
  max-height: 0;
  padding-top: 0;
  padding-bottom: 0;
}

.expand-enter-to,
.expand-leave-from {
  max-height: 500px;
}
</style>
