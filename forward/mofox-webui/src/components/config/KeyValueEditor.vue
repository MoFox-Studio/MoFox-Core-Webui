<template>
  <div class="key-value-editor">
    <div class="editor-header">
      <h4>
        <Icon icon="lucide:settings-2" />
        {{ title || '键值对配置' }}
      </h4>
      <p v-if="description" class="editor-hint">{{ description }}</p>
    </div>
    
    <div class="kv-list">
      <div 
        v-for="(pair, index) in pairs" 
        :key="index" 
        class="kv-item"
      >
        <input 
          type="text" 
          class="input key-input"
          :value="pair.key"
          :placeholder="keyPlaceholder || '键'"
          @input="updateKey(index, ($event.target as HTMLInputElement).value)"
        />
        <span class="separator">=</span>
        <input 
          type="text" 
          class="input value-input"
          :value="pair.value"
          :placeholder="valuePlaceholder || '值'"
          @input="updateValue(index, ($event.target as HTMLInputElement).value)"
        />
        <button 
          class="btn-icon delete-btn" 
          @click="removePair(index)" 
          title="删除"
        >
          <Icon icon="lucide:trash-2" />
        </button>
      </div>
      
      <div v-if="pairs.length === 0" class="empty-state">
        <Icon icon="lucide:package-open" />
        <p>{{ emptyText || '暂无配置项' }}</p>
      </div>
    </div>
    
    <button class="btn btn-outline add-btn" @click="addPair">
      <Icon icon="lucide:plus" />
      {{ addButtonText || '添加配置' }}
    </button>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { Icon } from '@iconify/vue'

const props = defineProps<{
  value: unknown
  title?: string
  description?: string
  keyPlaceholder?: string
  valuePlaceholder?: string
  emptyText?: string
  addButtonText?: string
}>()

const emit = defineEmits<{
  (e: 'update', value: Record<string, string>): void
}>()

interface KeyValuePair {
  key: string
  value: string
}

// 将对象转换为键值对数组
const pairs = computed<KeyValuePair[]>(() => {
  if (!props.value || typeof props.value !== 'object') {
    return []
  }
  return Object.entries(props.value).map(([key, value]) => ({
    key,
    value: String(value || '')
  }))
})

// 将键值对数组转换回对象
function pairsToObject(pairsList: KeyValuePair[]): Record<string, string> {
  const obj: Record<string, string> = {}
  pairsList.forEach(pair => {
    if (pair.key) { // 只保存有键的项
      obj[pair.key] = pair.value
    }
  })
  return obj
}

// 添加键值对
function addPair() {
  const newPairs = [...pairs.value, { key: '', value: '' }]
  emit('update', pairsToObject(newPairs))
}

// 删除键值对
function removePair(index: number) {
  const newPairs = pairs.value.filter((_, i) => i !== index)
  emit('update', pairsToObject(newPairs))
}

// 更新键
function updateKey(index: number, key: string) {
  const newPairs = [...pairs.value]
  newPairs[index] = { ...newPairs[index], key }
  emit('update', pairsToObject(newPairs))
}

// 更新值
function updateValue(index: number, value: string) {
  const newPairs = [...pairs.value]
  newPairs[index] = { ...newPairs[index], value }
  emit('update', pairsToObject(newPairs))
}
</script>

<style scoped>
.key-value-editor {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.editor-header h4 {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0 0 4px 0;
}

.editor-header h4 svg {
  color: var(--primary);
}

.editor-hint {
  font-size: 12px;
  color: var(--text-tertiary);
  margin: 0;
}

.kv-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.kv-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  background: var(--bg-secondary);
  border-radius: var(--radius);
  border: 1px solid var(--border-color);
  transition: all var(--transition-fast);
}

.kv-item:hover {
  border-color: var(--border-hover);
}

.key-input {
  width: 180px;
  flex-shrink: 0;
}

.separator {
  color: var(--text-tertiary);
  font-weight: 500;
  user-select: none;
}

.value-input {
  flex: 1;
}

.input {
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
