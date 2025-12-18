<template>
  <div class="reaction-rules-editor">
    <div class="editor-header">
      <h4>
        <Icon icon="lucide:zap" />
        反应规则配置
      </h4>
      <p class="editor-hint">配置基于关键词或正则表达式的自动回复规则</p>
    </div>
    
    <div class="rules-list">
      <div 
        v-for="(rule, index) in rules" 
        :key="index" 
        class="rule-card"
        :class="{ 
          'global-rule': !rule.chat_stream_id,
          'regex-rule': rule.rule_type === 'regex'
        }"
      >
        <div class="rule-header">
          <div class="rule-info">
            <span class="rule-type-badge" :class="rule.rule_type">
              <Icon :icon="rule.rule_type === 'regex' ? 'lucide:regex' : 'lucide:key'" />
              {{ rule.rule_type === 'regex' ? '正则' : '关键词' }}
            </span>
            <span v-if="!rule.chat_stream_id" class="scope-badge">
              <Icon icon="lucide:globe" />
              全局
            </span>
          </div>
          <button 
            class="btn-icon delete-btn" 
            @click="removeRule(index)" 
            title="删除规则"
          >
            <Icon icon="lucide:trash-2" />
          </button>
        </div>
        
        <div class="rule-fields">
          <div class="field-row">
            <label>聊天流ID</label>
            <input 
              type="text" 
              class="input"
              :value="rule.chat_stream_id || ''"
              @input="updateRule(index, 'chat_stream_id', ($event.target as HTMLInputElement).value)"
              placeholder='留空为全局，格式: "platform:id:type"'
            />
          </div>
          
          <div class="field-row">
            <label>规则类型</label>
            <div 
              class="custom-select-container"
              :class="{ 'is-open': openDropdownId === `rule_type_${index}` }"
            >
              <div 
                class="custom-select-trigger"
                @click="toggleDropdown(`rule_type_${index}`)"
              >
                <span>{{ rule.rule_type === 'regex' ? '正则表达式' : '关键词匹配' }}</span>
                <Icon icon="lucide:chevron-down" class="select-arrow" />
              </div>
              
              <transition name="select-fade">
                <div v-if="openDropdownId === `rule_type_${index}`" class="custom-select-dropdown">
                  <div 
                    class="custom-select-option"
                    :class="{ 'is-selected': rule.rule_type === 'keyword' }"
                    @click="updateRule(index, 'rule_type', 'keyword'); closeDropdown()"
                  >
                    关键词匹配
                    <Icon v-if="rule.rule_type === 'keyword'" icon="lucide:check" class="check-icon" />
                  </div>
                  <div 
                    class="custom-select-option"
                    :class="{ 'is-selected': rule.rule_type === 'regex' }"
                    @click="updateRule(index, 'rule_type', 'regex'); closeDropdown()"
                  >
                    正则表达式
                    <Icon v-if="rule.rule_type === 'regex'" icon="lucide:check" class="check-icon" />
                  </div>
                </div>
              </transition>
            </div>
          </div>
          
          <div class="field-row">
            <label>
              {{ rule.rule_type === 'regex' ? '正则表达式' : '关键词列表' }}
            </label>
            <div class="patterns-editor">
              <div 
                v-for="(pattern, pIndex) in (rule.patterns || [])" 
                :key="pIndex" 
                class="pattern-item"
              >
                <input 
                  type="text" 
                  class="input"
                  :value="pattern"
                  @input="updatePattern(index, pIndex, ($event.target as HTMLInputElement).value)"
                  :placeholder="rule.rule_type === 'regex' ? '输入正则表达式' : '输入关键词'"
                />
                <button 
                  class="btn-icon" 
                  @click="removePattern(index, pIndex)"
                  title="删除"
                >
                  <Icon icon="lucide:x" />
                </button>
              </div>
              <button class="btn btn-sm add-pattern-btn" @click="addPattern(index)">
                <Icon icon="lucide:plus" />
                添加{{ rule.rule_type === 'regex' ? '正则' : '关键词' }}
              </button>
            </div>
          </div>
          
          <div class="field-row">
            <label>回复模板</label>
            <textarea 
              class="input textarea"
              :value="rule.reaction || ''"
              @input="updateRule(index, 'reaction', ($event.target as HTMLTextAreaElement).value)"
              placeholder="触发规则后的回复内容或提示词"
              rows="3"
            ></textarea>
            <span class="field-hint">
              提示：对于正则表达式，可以使用 (?P&lt;name&gt;...) 定义命名捕获组，并在回复中用 [name] 引用
            </span>
          </div>
        </div>
      </div>
      
      <div v-if="rules.length === 0" class="empty-state">
        <Icon icon="lucide:list-x" />
        <p>暂无反应规则</p>
      </div>
    </div>
    
    <button class="btn btn-outline add-btn" @click="addRule">
      <Icon icon="lucide:plus" />
      添加规则
    </button>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, onMounted, onUnmounted } from 'vue'
import { Icon } from '@iconify/vue'

interface ReactionRule {
  chat_stream_id?: string
  rule_type: 'keyword' | 'regex'
  patterns: string[]
  reaction: string
}

const props = defineProps<{
  value: unknown
}>()

const emit = defineEmits<{
  (e: 'update', value: ReactionRule[]): void
}>()

// Dropdown state
const openDropdownId = ref<string | null>(null)

const toggleDropdown = (id: string) => {
  if (openDropdownId.value === id) {
    openDropdownId.value = null
  } else {
    openDropdownId.value = id
  }
}

const closeDropdown = () => {
  openDropdownId.value = null
}

const handleOutsideClick = (event: MouseEvent) => {
  const target = event.target as HTMLElement
  if (!target.closest('.custom-select-container')) {
    closeDropdown()
  }
}

onMounted(() => {
  document.addEventListener('click', handleOutsideClick)
})

onUnmounted(() => {
  document.removeEventListener('click', handleOutsideClick)
})

// 解析规则列表
const rules = computed(() => {
  if (Array.isArray(props.value)) {
    return props.value as ReactionRule[]
  }
  return []
})

// 添加规则
function addRule() {
  const newRules = [...rules.value, {
    chat_stream_id: '',
    rule_type: 'keyword' as const,
    patterns: [],
    reaction: ''
  }]
  emit('update', newRules)
}

// 删除规则
function removeRule(index: number) {
  const newRules = rules.value.filter((_, i) => i !== index)
  emit('update', newRules)
}

// 更新规则
function updateRule(index: number, field: keyof ReactionRule, value: unknown) {
  const newRules = rules.value.map((rule, i) => {
    if (i === index) {
      return { ...rule, [field]: value }
    }
    return rule
  })
  emit('update', newRules)
}

// 添加匹配模式
function addPattern(ruleIndex: number) {
  const newRules = rules.value.map((rule, i) => {
    if (i === ruleIndex) {
      return {
        ...rule,
        patterns: [...(rule.patterns || []), '']
      }
    }
    return rule
  })
  emit('update', newRules)
}

// 删除匹配模式
function removePattern(ruleIndex: number, patternIndex: number) {
  const newRules = rules.value.map((rule, i) => {
    if (i === ruleIndex) {
      return {
        ...rule,
        patterns: rule.patterns.filter((_, pi) => pi !== patternIndex)
      }
    }
    return rule
  })
  emit('update', newRules)
}

// 更新匹配模式
function updatePattern(ruleIndex: number, patternIndex: number, value: string) {
  const newRules = rules.value.map((rule, i) => {
    if (i === ruleIndex) {
      const newPatterns = [...rule.patterns]
      newPatterns[patternIndex] = value
      return { ...rule, patterns: newPatterns }
    }
    return rule
  })
  emit('update', newRules)
}
</script>

<style scoped>
.reaction-rules-editor {
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
  color: #f59e0b;
}

.editor-hint {
  font-size: 12px;
  color: var(--text-tertiary);
  margin: 0;
}

.rules-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.rule-card {
  padding: 16px;
  background: var(--bg-secondary);
  border-radius: var(--radius-lg);
  border: 1px solid var(--border-color);
}

.rule-card.global-rule {
  border-left: 3px solid var(--primary);
}

.rule-card.regex-rule {
  border-left: 3px solid #8b5cf6;
}

.rule-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16px;
}

.rule-info {
  display: flex;
  align-items: center;
  gap: 8px;
}

.rule-type-badge {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 4px 8px;
  border-radius: var(--radius);
  font-size: 11px;
  font-weight: 600;
}

.rule-type-badge.keyword {
  background: #fef3c7;
  color: #92400e;
}

.rule-type-badge.regex {
  background: #ede9fe;
  color: #5b21b6;
}

.scope-badge {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 4px 8px;
  border-radius: var(--radius);
  font-size: 11px;
  background: var(--primary-bg);
  color: var(--primary);
}

.delete-btn {
  padding: 4px;
  background: transparent;
  border: none;
  color: var(--text-tertiary);
  cursor: pointer;
  border-radius: var(--radius);
  transition: all var(--transition-fast);
}

.delete-btn:hover {
  background: var(--danger-bg);
  color: var(--danger);
}

.rule-fields {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.field-row {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.field-row label {
  font-size: 12px;
  font-weight: 500;
  color: var(--text-secondary);
}

.field-hint {
  font-size: 11px;
  color: var(--text-tertiary);
}

.input {
  padding: 8px 12px;
  background: var(--bg-primary);
  border: 1px solid var(--border-color);
  border-radius: var(--radius);
  color: var(--text-primary);
  font-size: 13px;
}

.input:focus {
  border-color: var(--primary);
  outline: none;
}

.textarea {
  resize: vertical;
  min-height: 60px;
  font-family: inherit;
}

.patterns-editor {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.pattern-item {
  display: flex;
  gap: 8px;
}

.pattern-item .input {
  flex: 1;
}

.pattern-item .btn-icon {
  padding: 6px;
  background: transparent;
  border: none;
  color: var(--text-tertiary);
  cursor: pointer;
  border-radius: var(--radius);
}

.pattern-item .btn-icon:hover {
  background: var(--danger-bg);
  color: var(--danger);
}

/* Custom Select Styles */
.custom-select-container {
  position: relative;
  width: 100%;
}

.custom-select-trigger {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0.75rem 1rem;
  background-color: var(--bg-secondary);
  border: 1px solid var(--border-color);
  border-radius: 12px;
  cursor: pointer;
  transition: all 0.2s ease;
  font-size: 0.95rem;
  color: var(--text-primary);
}

.custom-select-trigger:hover {
  border-color: var(--primary);
  background-color: var(--bg-hover);
}

.custom-select-container.is-open .custom-select-trigger {
  border-color: var(--primary);
  box-shadow: 0 0 0 3px var(--primary-dim);
}

.select-arrow {
  color: var(--text-secondary);
  transition: transform 0.2s ease;
}

.custom-select-container.is-open .select-arrow {
  transform: rotate(180deg);
  color: var(--primary);
}

.custom-select-dropdown {
  position: absolute;
  top: calc(100% + 4px);
  left: 0;
  width: 100%;
  background-color: var(--bg-secondary);
  border: 1px solid var(--border-color);
  border-radius: 12px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
  z-index: 100;
  max-height: 300px;
  overflow-y: auto;
  padding: 4px;
}

.custom-select-option {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0.75rem 1rem;
  cursor: pointer;
  border-radius: 8px;
  transition: all 0.15s ease;
  color: var(--text-primary);
}

.custom-select-option:hover {
  background-color: var(--bg-hover);
}

.custom-select-option.is-selected {
  background-color: var(--primary-dim);
  color: var(--primary);
  font-weight: 500;
}

.check-icon {
  font-size: 1.1rem;
}

.select-fade-enter-active,
.select-fade-leave-active {
  transition: all 0.2s ease;
}

.select-fade-enter-from,
.select-fade-leave-to {
  opacity: 0;
  transform: translateY(-10px);
}

.add-pattern-btn {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 6px 12px;
  background: var(--bg-primary);
  border: 1px dashed var(--border-color);
  border-radius: var(--radius);
  color: var(--text-secondary);
  font-size: 12px;
  cursor: pointer;
  transition: all var(--transition-fast);
  width: fit-content;
}

.add-pattern-btn:hover {
  border-color: var(--primary);
  color: var(--primary);
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
