<template>
  <div class="expression-rules-editor">
    <div class="editor-header">
      <h4>
        <Icon icon="lucide:sparkles" />
        表达学习规则配置
      </h4>
      <p class="editor-hint">按共享组管理表达学习规则，同组内的聊天流共享学到的表达方式</p>
    </div>
    
    <!-- 全局规则 -->
    <div class="group-card global-group">
      <div class="group-header">
        <div class="group-info">
          <Icon icon="lucide:globe" class="group-icon" />
          <span class="group-name">全局规则</span>
          <span class="group-badge">默认配置</span>
        </div>
      </div>
      
      <div class="group-content">
        <div class="field-row switches">
          <label class="switch-label">
            <input 
              type="checkbox" 
              :checked="globalRule.use_expression !== false"
              @change="updateGlobalRule('use_expression', ($event.target as HTMLInputElement).checked)"
            />
            <span>使用表达</span>
          </label>
          <label class="switch-label">
            <input 
              type="checkbox" 
              :checked="globalRule.learn_expression !== false"
              @change="updateGlobalRule('learn_expression', ($event.target as HTMLInputElement).checked)"
            />
            <span>学习表达</span>
          </label>
        </div>
        
        <div class="field-row">
          <label>学习强度</label>
          <div class="slider-input">
            <input 
              type="range" 
              :value="globalRule.learning_strength ?? 1.0"
              @input="updateGlobalRule('learning_strength', parseFloat(($event.target as HTMLInputElement).value))"
              min="0"
              max="5"
              step="0.1"
              class="slider"
            />
            <span class="slider-value">{{ (globalRule.learning_strength ?? 1.0).toFixed(1) }}</span>
          </div>
        </div>
      </div>
    </div>
    
    <!-- 共享组列表 -->
    <div class="groups-list">
      <div 
        v-for="(group, groupIndex) in groups" 
        :key="groupIndex" 
        class="group-card"
      >
        <div class="group-header">
          <div class="group-info">
            <Icon icon="lucide:users" class="group-icon" />
            <input 
              type="text" 
              class="group-name-input"
              :value="group.name"
              @input="updateGroupName(groupIndex, ($event.target as HTMLInputElement).value)"
              placeholder="组名称"
            />
            <span class="stream-count">{{ group.streams.length }} 个聊天流</span>
          </div>
          <button 
            class="btn-icon delete-btn" 
            @click="removeGroup(groupIndex)" 
            title="删除组"
          >
            <Icon icon="lucide:trash-2" />
          </button>
        </div>
        
        <div class="group-content">
          <div class="field-row switches">
            <label class="switch-label">
              <input 
                type="checkbox" 
                :checked="group.use_expression !== false"
                @change="updateGroupSetting(groupIndex, 'use_expression', ($event.target as HTMLInputElement).checked)"
              />
              <span>使用表达</span>
            </label>
            <label class="switch-label">
              <input 
                type="checkbox" 
                :checked="group.learn_expression !== false"
                @change="updateGroupSetting(groupIndex, 'learn_expression', ($event.target as HTMLInputElement).checked)"
              />
              <span>学习表达</span>
            </label>
          </div>
          
          <div class="field-row">
            <label>学习强度</label>
            <div class="slider-input">
              <input 
                type="range" 
                :value="group.learning_strength ?? 1.0"
                @input="updateGroupSetting(groupIndex, 'learning_strength', parseFloat(($event.target as HTMLInputElement).value))"
                min="0"
                max="5"
                step="0.1"
                class="slider"
              />
              <span class="slider-value">{{ (group.learning_strength ?? 1.0).toFixed(1) }}</span>
            </div>
          </div>
          
          <!-- 组内的聊天流列表 -->
          <div class="streams-section">
            <label class="section-label">
              <Icon icon="lucide:message-square" />
              聊天流列表
            </label>
            <div class="streams-list">
              <div 
                v-for="(stream, streamIndex) in group.streams" 
                :key="streamIndex"
                class="stream-item"
              >
                <ChatStreamIdInput
                  :value="stream"
                  @update="(v: string) => updateStream(groupIndex, streamIndex, v)"
                />
                <button 
                  class="btn-icon delete-btn" 
                  @click="removeStream(groupIndex, streamIndex)" 
                  title="删除聊天流"
                >
                  <Icon icon="lucide:x" />
                </button>
              </div>
              
              <button 
                class="btn btn-sm btn-outline add-stream-btn" 
                @click="addStream(groupIndex)"
              >
                <Icon icon="lucide:plus" />
                添加聊天流
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
    
    <button class="btn btn-outline add-btn" @click="addGroup">
      <Icon icon="lucide:plus" />
      添加共享组
    </button>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { Icon } from '@iconify/vue'
import ChatStreamIdInput from '../ChatStreamIdInput.vue'

interface ExpressionRule {
  chat_stream_id?: string
  group?: string
  use_expression?: boolean
  learn_expression?: boolean
  learning_strength?: number
}

interface GroupData {
  name: string
  streams: string[]
  use_expression: boolean
  learn_expression: boolean
  learning_strength: number
}

const props = defineProps<{
  value: unknown
}>()

const emit = defineEmits<{
  (e: 'update', value: ExpressionRule[]): void
}>()

// 解析规则列表并按组组织
const globalRule = computed(() => {
  const rules = Array.isArray(props.value) ? props.value as ExpressionRule[] : []
  return rules.find(r => !r.chat_stream_id && !r.group) || {
    use_expression: true,
    learn_expression: true,
    learning_strength: 1.0
  }
})

const groups = computed((): GroupData[] => {
  const rules = Array.isArray(props.value) ? props.value as ExpressionRule[] : []
  const groupMap = new Map<string, GroupData>()
  
  rules.forEach(rule => {
    if (rule.group) {
      if (!groupMap.has(rule.group)) {
        groupMap.set(rule.group, {
          name: rule.group,
          streams: [],
          use_expression: rule.use_expression ?? true,
          learn_expression: rule.learn_expression ?? true,
          learning_strength: rule.learning_strength ?? 1.0
        })
      }
      if (rule.chat_stream_id !== undefined && rule.chat_stream_id !== null) {
        groupMap.get(rule.group)!.streams.push(rule.chat_stream_id)
      }
    }
  })
  
  return Array.from(groupMap.values())
})

// 将组数据转换回规则数组
function groupsToRules(): ExpressionRule[] {
  const rules: ExpressionRule[] = []
  
  // 全局规则
  rules.push({
    chat_stream_id: '',
    use_expression: globalRule.value.use_expression,
    learn_expression: globalRule.value.learn_expression,
    learning_strength: globalRule.value.learning_strength
  })
  
  // 每个组的规则
  groups.value.forEach(group => {
    group.streams.forEach(stream => {
      rules.push({
        chat_stream_id: stream,
        group: group.name,
        use_expression: group.use_expression,
        learn_expression: group.learn_expression,
        learning_strength: group.learning_strength
      })
    })
  })
  
  return rules
}

// 更新全局规则
function updateGlobalRule(field: string, value: any) {
  const rules = Array.isArray(props.value) ? props.value as ExpressionRule[] : []
  const globalIdx = rules.findIndex(r => !r.chat_stream_id && !r.group)
  
  if (globalIdx >= 0) {
    const newRules = [...rules]
    newRules[globalIdx] = { ...newRules[globalIdx], [field]: value }
    emit('update', newRules)
  } else {
    emit('update', [{ chat_stream_id: '', [field]: value }, ...rules])
  }
}

// 添加组
function addGroup() {
  const newGroupName = `group_${groups.value.length + 1}`
  const rules = groupsToRules()
  rules.push({
    chat_stream_id: '',
    group: newGroupName,
    use_expression: true,
    learn_expression: true,
    learning_strength: 1.0
  })
  emit('update', rules)
}

// 删除组
function removeGroup(groupIndex: number) {
  const newGroups = groups.value.filter((_, i) => i !== groupIndex)
  const rules: ExpressionRule[] = [
    {
      chat_stream_id: '',
      use_expression: globalRule.value.use_expression,
      learn_expression: globalRule.value.learn_expression,
      learning_strength: globalRule.value.learning_strength
    }
  ]
  
  newGroups.forEach(group => {
    group.streams.forEach(stream => {
      rules.push({
        chat_stream_id: stream,
        group: group.name,
        use_expression: group.use_expression,
        learn_expression: group.learn_expression,
        learning_strength: group.learning_strength
      })
    })
  })
  
  emit('update', rules)
}

// 更新组名
function updateGroupName(groupIndex: number, newName: string) {
  const group = groups.value[groupIndex]
  if (!group) return

  const rules = groupsToRules()
  const oldName = group.name
  
  rules.forEach(rule => {
    if (rule.group === oldName) {
      rule.group = newName
    }
  })
  
  emit('update', rules)
}

// 更新组设置
function updateGroupSetting(groupIndex: number, field: string, value: any) {
  const group = groups.value[groupIndex]
  if (!group) return

  const rules = groupsToRules()
  const groupName = group.name
  
  rules.forEach(rule => {
    if (rule.group === groupName) {
      (rule as any)[field] = value
    }
  })
  
  emit('update', rules)
}

// 添加聊天流
function addStream(groupIndex: number) {
  const group = groups.value[groupIndex]
  if (!group) return

  const rules = groupsToRules()
  
  rules.push({
    chat_stream_id: '',
    group: group.name,
    use_expression: group.use_expression,
    learn_expression: group.learn_expression,
    learning_strength: group.learning_strength
  })
  
  emit('update', rules)
}

// 删除聊天流
function removeStream(groupIndex: number, streamIndex: number) {
  const newRules: ExpressionRule[] = []
  
  // 添加全局规则
  newRules.push({
    chat_stream_id: '',
    use_expression: globalRule.value.use_expression,
    learn_expression: globalRule.value.learn_expression,
    learning_strength: globalRule.value.learning_strength
  })
  
  // 重建所有组的规则
  groups.value.forEach((group, gIdx) => {
    group.streams.forEach((stream, sIdx) => {
      // 如果是当前组，且索引匹配，则跳过（即删除）
      if (gIdx === groupIndex && sIdx === streamIndex) {
        return
      }
      
      newRules.push({
        chat_stream_id: stream,
        group: group.name,
        use_expression: group.use_expression,
        learn_expression: group.learn_expression,
        learning_strength: group.learning_strength
      })
    })
  })
  
  emit('update', newRules)
}

// 更新聊天流
function updateStream(groupIndex: number, streamIndex: number, newValue: string) {
  const newRules: ExpressionRule[] = []
  
  // 添加全局规则
  newRules.push({
    chat_stream_id: '',
    use_expression: globalRule.value.use_expression,
    learn_expression: globalRule.value.learn_expression,
    learning_strength: globalRule.value.learning_strength
  })
  
  // 重建所有组的规则
  groups.value.forEach((group, gIdx) => {
    group.streams.forEach((stream, sIdx) => {
      let streamId = stream
      // 如果是当前组且索引匹配，使用新值
      if (gIdx === groupIndex && sIdx === streamIndex) {
        streamId = newValue
      }
      
      newRules.push({
        chat_stream_id: streamId,
        group: group.name,
        use_expression: group.use_expression,
        learn_expression: group.learn_expression,
        learning_strength: group.learning_strength
      })
    })
  })
  
  emit('update', newRules)
}
</script>

<style scoped>
.expression-rules-editor {
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
  color: #8b5cf6;
}

.editor-hint {
  font-size: 12px;
  color: var(--text-tertiary);
  margin: 0;
}

.group-card {
  background: var(--bg-secondary);
  border: 1px solid var(--border-color);
  border-radius: var(--radius);
  overflow: hidden;
  transition: all var(--transition-fast);
}

.global-group {
  border-color: var(--primary);
  background: var(--bg-secondary);
}

.group-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  background: var(--bg-tertiary);
  border-bottom: 1px solid var(--border-color);
}

.group-info {
  display: flex;
  align-items: center;
  gap: 10px;
  flex: 1;
}

.group-icon {
  font-size: 18px;
  color: var(--primary);
}

.group-name {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary);
}

.group-name-input {
  flex: 1;
  max-width: 200px;
  padding: 4px 8px;
  background: var(--bg-primary);
  border: 1px solid var(--border-color);
  border-radius: 4px;
  color: var(--text-primary);
  font-size: 14px;
  font-weight: 600;
}

.group-name-input:focus {
  border-color: var(--primary);
  outline: none;
}

.group-badge {
  padding: 2px 8px;
  background: var(--primary-bg);
  color: var(--primary);
  border-radius: 4px;
  font-size: 11px;
  font-weight: 500;
}

.stream-count {
  font-size: 12px;
  color: var(--text-tertiary);
}

.group-content {
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.field-row {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.field-row > label {
  font-size: 13px;
  font-weight: 500;
  color: var(--text-secondary);
}

.field-row.switches {
  flex-direction: row;
  gap: 16px;
}

.switch-label {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  color: var(--text-primary);
  cursor: pointer;
}

.switch-label input[type="checkbox"] {
  width: 16px;
  height: 16px;
  cursor: pointer;
}

.slider-input {
  display: flex;
  align-items: center;
  gap: 12px;
}

.slider {
  flex: 1;
  height: 6px;
  -webkit-appearance: none;
  appearance: none;
  background: var(--bg-tertiary);
  border-radius: 3px;
  outline: none;
}

.slider::-webkit-slider-thumb {
  -webkit-appearance: none;
  appearance: none;
  width: 16px;
  height: 16px;
  background: var(--primary);
  border-radius: 50%;
  cursor: pointer;
}

.slider::-moz-range-thumb {
  width: 16px;
  height: 16px;
  background: var(--primary);
  border-radius: 50%;
  cursor: pointer;
  border: none;
}

.slider-value {
  min-width: 32px;
  font-size: 13px;
  font-weight: 600;
  color: var(--primary);
  text-align: right;
}

.streams-section {
  margin-top: 8px;
  padding-top: 12px;
  border-top: 1px dashed var(--border-color);
}

.section-label {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  font-weight: 600;
  color: var(--text-secondary);
  margin-bottom: 8px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.section-label svg {
  font-size: 14px;
}

.streams-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.stream-item {
  display: flex;
  align-items: flex-start;
  gap: 8px;
}

.add-stream-btn {
  margin-top: 4px;
}

.groups-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
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

.btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  padding: 6px 12px;
  border: none;
  border-radius: var(--radius);
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: all var(--transition-fast);
}

.btn-sm {
  padding: 4px 8px;
  font-size: 12px;
}

.btn-outline {
  background: transparent;
  border: 1px solid var(--border-color);
  color: var(--text-secondary);
}

.btn-outline:hover {
  border-color: var(--primary);
  color: var(--primary);
  background: var(--primary-bg);
}

.btn-icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 6px;
  background: transparent;
  border: none;
  border-radius: var(--radius);
  cursor: pointer;
  transition: all var(--transition-fast);
}
</style>
