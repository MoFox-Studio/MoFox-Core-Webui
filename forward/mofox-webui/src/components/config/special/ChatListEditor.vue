<template>
  <div class="chat-list-editor">
    <div v-if="title || description" class="editor-header">
      <h4 v-if="title">
        <Icon icon="lucide:list" />
        {{ title }}
      </h4>
      <p v-if="description" class="editor-hint">{{ description }}</p>
    </div>

    <div class="table-container">
      <table class="chat-table">
        <thead>
          <tr>
            <th style="width: 60px">序号</th>
            <th>ID</th>
            <th style="width: 120px">平台</th>
            <th style="width: 120px">类型</th>
            <th style="width: 60px">操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="(item, index) in parsedItems" :key="index">
            <td class="text-center">{{ index + 1 }}</td>
            <td>
              <input 
                type="text" 
                class="input" 
                v-model="item.id" 
                placeholder="聊天ID"
                @input="updateItem()"
              />
            </td>
            <td>
              <select class="select" v-model="item.platform" @change="updateItem()">
                <option value="qq">QQ</option>
                <option value="telegram">Telegram</option>
                <option value="discord">Discord</option>
                <option value="other">Other</option>
              </select>
            </td>
            <td>
              <select class="select" v-model="item.type" @change="updateItem()">
                <option value="group">群聊</option>
                <option value="private">私聊</option>
              </select>
            </td>
            <td class="text-center">
              <button class="btn-icon delete-btn" @click="removeItem(index)" title="删除">
                <Icon icon="lucide:trash-2" />
              </button>
            </td>
          </tr>
          <tr v-if="parsedItems.length === 0">
            <td colspan="5" class="empty-state">
              <Icon icon="lucide:inbox" />
              <span>暂无配置</span>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <button class="btn btn-outline add-btn" @click="addItem">
      <Icon icon="lucide:plus" />
      添加项
    </button>
  </div>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import { Icon } from '@iconify/vue'

const props = defineProps<{
  value: unknown
  title?: string
  description?: string
}>()

const emit = defineEmits<{
  (e: 'update', value: string[]): void
}>()

interface ChatItem {
  platform: string
  type: string
  id: string
}

const parsedItems = ref<ChatItem[]>([])

// Parse initial value
watch(() => props.value, (newVal) => {
  const newSerialized = Array.isArray(newVal) ? (newVal as string[]) : []
  const currentSerialized = serializeItems(parsedItems.value)
  
  // 比较两个字符串数组是否相等
  const isSame = JSON.stringify(newSerialized) === JSON.stringify(currentSerialized)
  
  if (!isSame) {
      parsedItems.value = newSerialized.map(str => {
        if (typeof str !== 'string') return { platform: 'qq', type: 'group', id: '' }
        const parts = str.split(':')
        if (parts.length >= 3) {
          return {
            platform: parts[0] || 'qq',
            type: parts[1] || 'group',
            id: parts.slice(2).join(':')
          }
        }
        return { platform: 'qq', type: 'group', id: str }
      })
  }
}, { immediate: true, deep: true })

function serializeItems(items: ChatItem[]): string[] {
  return items.map(item => `${item.platform}:${item.type}:${item.id}`)
}

function updateItem() {
  emit('update', serializeItems(parsedItems.value))
}

function addItem() {
  // 创建新项
  const newItem = { platform: 'qq', type: 'group', id: '' }
  // 创建新数组（触发响应式更新）
  const newItems = [...parsedItems.value, newItem]
  // 更新本地状态
  parsedItems.value = newItems
  // 通知父组件
  emit('update', serializeItems(newItems))
}

function removeItem(index: number) {
  const newItems = [...parsedItems.value]
  newItems.splice(index, 1)
  parsedItems.value = newItems
  emit('update', serializeItems(newItems))
}

</script>

<style scoped>
.chat-list-editor {
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding: 16px;
  background: var(--bg-secondary);
  border: 1px solid var(--border-color);
  border-radius: var(--radius);
}

.editor-header {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.editor-header h4 {
  display: flex;
  align-items: center;
  gap: 8px;
  margin: 0;
  font-size: 14px;
  font-weight: 600;
}

.editor-hint {
  margin: 0;
  font-size: 12px;
  color: var(--text-secondary);
}

.table-container {
  border: 1px solid var(--border-color);
  border-radius: var(--radius);
  overflow: hidden;
}

.chat-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 13px;
}

.chat-table th,
.chat-table td {
  padding: 8px 12px;
  border-bottom: 1px solid var(--border-color);
  text-align: left;
}

.chat-table th {
  background: var(--bg-tertiary);
  font-weight: 500;
  color: var(--text-secondary);
}

.chat-table tr:last-child td {
  border-bottom: none;
}

.text-center {
  text-align: center !important;
}

.input, .select {
  width: 100%;
  padding: 6px 10px;
  border: 1px solid var(--border-color);
  border-radius: 4px;
  background: var(--bg-primary);
  color: var(--text-primary);
  font-size: 13px;
}

.input:focus, .select:focus {
  outline: none;
  border-color: var(--primary-color);
}

.btn-icon {
  padding: 6px;
  border: none;
  background: transparent;
  color: var(--text-secondary);
  cursor: pointer;
  border-radius: 4px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
}

.btn-icon:hover {
  background: var(--bg-tertiary);
  color: var(--error-color);
}

.empty-state {
  padding: 24px;
  text-align: center;
  color: var(--text-secondary);
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
}

.add-btn {
  align-self: flex-start;
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 16px;
  border: 1px dashed var(--border-color);
  background: transparent;
  color: var(--primary-color);
  border-radius: var(--radius);
  cursor: pointer;
  font-size: 13px;
  transition: all 0.2s;
}

.add-btn:hover {
  background: var(--primary-color-alpha-10);
  border-color: var(--primary-color);
}
</style>
