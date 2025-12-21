<template>
  <div class="string-array-editor">
    <div v-if="title || description || isSecret" class="editor-header">
      <div class="header-top">
        <h4 v-if="title">
          <Icon icon="lucide:list" />
          {{ title }}
        </h4>
        <button 
          v-if="isSecret" 
          class="icon-btn toggle-secret-btn" 
          @click="showSecret = !showSecret" 
          :title="showSecret ? '隐藏内容' : '显示内容'"
        >
          <Icon :icon="showSecret ? 'lucide:eye-off' : 'lucide:eye'" />
        </button>
      </div>
      <p v-if="description" class="editor-hint">{{ description }}</p>
    </div>
    
    <div class="array-items">
      <div 
        v-for="(item, index) in items" 
        :key="index" 
        class="array-item"
      >
        <input 
          :type="isSecret && !showSecret ? 'password' : 'text'"
          class="input"
          :value="item"
          :placeholder="placeholder || `项 ${index + 1}`"
          @input="updateItem(index, ($event.target as HTMLInputElement).value)"
        />
        <button 
          class="btn-icon delete-btn" 
          @click="removeItem(index)" 
          title="删除"
        >
          <Icon icon="lucide:trash-2" />
        </button>
      </div>
      
      <div v-if="items.length === 0" class="empty-state">
        <Icon icon="lucide:inbox" />
        <p>{{ emptyText || '暂无项目' }}</p>
      </div>
    </div>
    
    <button class="btn btn-outline add-btn" @click="addItem">
      <Icon icon="lucide:plus" />
      {{ addButtonText || '添加项' }}
    </button>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import { Icon } from '@iconify/vue'

const props = defineProps<{
  value: unknown
  title?: string
  description?: string
  placeholder?: string
  emptyText?: string
  addButtonText?: string
  isSecret?: boolean
}>()

const emit = defineEmits<{
  (e: 'update', value: string[]): void
}>()

const showSecret = ref(false)

// 确保数据是字符串数组
const items = computed(() => {
  if (Array.isArray(props.value)) {
    return props.value.map(item => String(item || ''))
  }
  return []
})

// 添加项
function addItem() {
  const newItems = [...items.value, '']
  emit('update', newItems)
}

// 删除项
function removeItem(index: number) {
  const newItems = items.value.filter((_, i) => i !== index)
  emit('update', newItems)
}

// 更新项
function updateItem(index: number, value: string) {
  const newItems = [...items.value]
  newItems[index] = value
  emit('update', newItems)
}
</script>

<style scoped>
.string-array-editor {
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding: 16px;
  background: var(--bg-secondary);
  border: 1px solid var(--border-color);
  border-radius: var(--radius);
}

.header-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 4px;
}

.editor-header h4 {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0;
}

.toggle-secret-btn {
  padding: 4px;
  background: transparent;
  border: none;
  color: var(--text-secondary);
  cursor: pointer;
  border-radius: var(--radius);
  display: flex;
  align-items: center;
  justify-content: center;
}

.toggle-secret-btn:hover {
  background: var(--bg-primary);
  color: var(--primary);
}

.editor-header h4 svg {
  color: var(--primary);
}

.editor-hint {
  font-size: 12px;
  color: var(--text-tertiary);
  margin: 0 0 12px 0;
}

.

.array-items {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.array-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  background: var(--bg-secondary);
  border-radius: var(--radius);
  border: 1px solid var(--border-color);
  transition: all var(--transition-fast);
}

.array-item:hover {
  border-color: var(--border-hover);
}

.input {
  flex: 1;
  padding: 0 12px;
  height: 34px;
  background: var(--bg-primary);
  border: 1px solid var(--border-color);
  border-radius: var(--radius);
  color: var(--text-primary);
  font-family: 'Roboto Mono', 'Noto Sans SC', sans-serif !important;
  font-size: 13px;
  transition: all var(--transition-fast);
}

.input:focus {
  border-color: var(--primary);
  outline: none;
}

.delete-btn {
  padding: 6px;
  background: transparent;
  border: none;
  color: var(--text-tertiary);
  cursor: pointer;
  border-radius: var(--radius);
  transition: all var(--transition-fast);
  flex-shrink: 0;
}

.delete-btn:hover {
  background: var(--danger-bg);
  color: var(--danger);
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  padding: 24px;
  color: var(--text-tertiary);
}

.empty-state svg {
  font-size: 24px;
}

.empty-state p {
  margin: 0;
  font-size: 13px;
}

.add-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 10px 16px;
  background: var(--bg-secondary);
  border: 1px dashed var(--border-color);
  border-radius: var(--radius);
  color: var(--text-secondary);
  font-size: 13px;
  cursor: pointer;
  transition: all var(--transition-fast);
}

.add-btn:hover {
  border-color: var(--primary);
  color: var(--primary);
  background: var(--primary-bg);
}
</style>
