<template>
  <div class="main-config-editor">
    <!-- 顶部导航栏 -->
    <div class="config-nav-bar">
      <div class="nav-tabs">
        <button
          v-for="tab in navTabs"
          :key="tab.key"
          class="nav-tab"
          :class="{ active: activeTab === tab.key }"
          @click="activeTab = tab.key"
        >
          {{ tab.name }}
        </button>
      </div>
    </div>

    <!-- 当前标签页标题和描述 -->
    <div class="tab-header">
      <h3 class="tab-title">{{ currentTabInfo?.name }}</h3>
      <p class="tab-description">{{ currentTabInfo?.description }}</p>
      <button 
        v-if="hasAdvancedFieldsInCurrentTab"
        class="add-rule-btn"
        @click="showAdvanced = !showAdvanced"
      >
        <Icon :icon="showAdvanced ? 'lucide:eye-off' : 'lucide:eye'" />
        {{ showAdvanced ? '隐藏高级选项' : '显示高级选项' }}
      </button>
    </div>

    <!-- 搜索框 -->
    <div class="config-toolbar" v-if="currentTabGroups.length > 1">
      <div class="search-box">
        <Icon icon="lucide:search" />
        <input 
          v-model="searchQuery" 
          type="text" 
          placeholder="搜索配置项..." 
          class="search-input"
        />
      </div>
    </div>

    <!-- 配置内容 -->
    <div class="config-content">
      <div 
        v-for="group in filteredCurrentTabGroups" 
        :key="group.key" 
        class="config-group"
        :class="{ 
          collapsed: collapsedGroups[group.key],
          'expert-group': group.expert,
          'single-group': currentTabGroups.length === 1
        }"
      >
        <!-- 当只有一个分组时不显示分组头部 -->
        <div 
          v-if="currentTabGroups.length > 1" 
          class="group-header" 
          @click="toggleGroup(group.key)"
        >
          <div class="group-title">
            <Icon :icon="group.icon" />
            <h3>{{ group.name }}</h3>
            <span v-if="group.expert" class="expert-badge">专家</span>
          </div>
          <div class="group-meta">
            <span class="group-hint">{{ group.description }}</span>
            <Icon :icon="collapsedGroups[group.key] ? 'lucide:chevron-down' : 'lucide:chevron-up'" />
          </div>
        </div>
        
        <div v-show="currentTabGroups.length === 1 || !collapsedGroups[group.key]" class="group-content">
          <template v-for="field in getVisibleFields(group)" :key="field.key">
            <!-- 特殊编辑器 -->
            <div v-if="field.specialEditor" class="field-card special-editor-card">
              <StringArrayEditor
                v-if="field.specialEditor === 'string_array'"
                :value="getFieldValue(field.key)"
                :title="field.name"
                :description="field.description"
                :placeholder="field.placeholder"
                :emptyText="'暂无' + field.name"
                :addButtonText="'添加' + field.name"
                @update="(v: unknown) => emit('update', field.key, v)"
              />
              <KeyValueEditor
                v-else-if="field.specialEditor === 'key_value'"
                :value="getFieldValue(field.key)"
                :title="field.name"
                :description="field.description"
                @update="(v: unknown) => emit('update', field.key, v)"
              />
              <MasterUsersEditor 
                v-else-if="field.specialEditor === 'master_users'"
                :value="getFieldValue(field.key)"
                @update="(v: unknown) => emit('update', field.key, v)"
              />
              <ExpressionRulesEditor 
                v-else-if="field.specialEditor === 'expression_rules'"
                :value="getFieldValue(field.key)"
                @update="(v: unknown) => emit('update', field.key, v)"
              />
              <ReactionRulesEditor 
                v-else-if="field.specialEditor === 'reaction_rules'"
                :value="getFieldValue(field.key)"
                @update="(v: unknown) => emit('update', field.key, v)"
              />
              <WebSearchEnginesEditor 
                v-else-if="field.specialEditor === 'web_search_engines'"
                :value="getFieldValue(field.key)"
                :configData="mergedConfigData"
                @update="(v: unknown) => emit('update', field.key, v)"
                @updateConfig="(key: string, v: unknown) => emit('update', key, v)"
              />
              <ChatListEditor 
                v-else-if="field.specialEditor === 'chat_list'"
                :value="getFieldValue(field.key)"
                :title="field.name"
                :description="field.description"
                @update="(v: unknown) => emit('update', field.key, v)"
              />
            </div>
            
            <!-- 普通字段 -->
            <div 
              v-else
              class="field-card"
              :class="{ 
                inline: field.type === 'boolean',
                advanced: field.advanced,
                expert: field.expert,
                readonly: field.readonly
              }"
            >
              <!-- 只读标签 -->
              <span v-if="field.readonly" class="readonly-badge">只读</span>
              
              <!-- Boolean 类型 -->
              <template v-if="field.type === 'boolean'">
                <div class="field-left">
                  <div class="field-header">
                    <span class="field-name">{{ field.name }}</span>
                    <span v-if="field.advanced" class="advanced-badge">高级</span>
                    <span v-if="field.expert" class="expert-badge">专家</span>
                  </div>
                  <div class="field-description">{{ field.description }}</div>
                </div>
                <label class="toggle-switch" :class="{ disabled: field.readonly }">
                  <input 
                    type="checkbox" 
                    :checked="Boolean(getFieldValue(field.key))"
                    :disabled="field.readonly"
                    @change="emit('update', field.key, ($event.target as HTMLInputElement).checked)"
                  />
                  <span class="toggle-slider"></span>
                </label>
              </template>

              <!-- 其他类型 -->
              <template v-else>
                <div class="field-header">
                  <span class="field-name">{{ field.name }}</span>
                  <span class="field-key">{{ field.key }}</span>
                  <span v-if="field.advanced" class="advanced-badge">高级</span>
                  <span v-if="field.expert" class="expert-badge">专家</span>
                </div>
                <div class="field-description">{{ field.description }}</div>
                
                <div class="field-input">
                  <!-- Select 类型 -->
                  <div 
                    v-if="field.type === 'select'"
                    class="custom-select-container"
                    :class="{ 'is-open': openDropdownId === field.key, 'is-disabled': field.readonly }"
                  >
                    <div 
                      class="custom-select-trigger"
                      @click="!field.readonly && toggleDropdown(field.key)"
                    >
                      <span>{{ getOptionLabel(field.options || [], getFieldValue(field.key) ?? field.default) }}</span>
                      <Icon icon="lucide:chevron-down" class="select-arrow" />
                    </div>
                    
                    <transition name="select-fade">
                      <div v-if="openDropdownId === field.key" class="custom-select-dropdown">
                        <div 
                          v-for="opt in field.options" 
                          :key="opt.value" 
                          class="custom-select-option"
                          :class="{ 'is-selected': (getFieldValue(field.key) ?? field.default) === opt.value }"
                          @click="emit('update', field.key, opt.value); closeDropdown()"
                        >
                          {{ opt.label }}
                          <Icon v-if="(getFieldValue(field.key) ?? field.default) === opt.value" icon="lucide:check" class="check-icon" />
                        </div>
                      </div>
                    </transition>
                  </div>

                  <!-- Textarea 类型 -->
                  <textarea 
                    v-else-if="field.type === 'textarea'"
                    class="input textarea"
                    :value="String(getFieldValue(field.key) ?? field.default ?? '')"
                    :placeholder="field.placeholder"
                    :disabled="field.readonly"
                    :readonly="field.readonly"
                    @input="emit('update', field.key, ($event.target as HTMLTextAreaElement).value)"
                    rows="3"
                  ></textarea>

                  <!-- Password 类型 -->
                  <div v-else-if="field.type === 'password'" class="password-input">
                    <input 
                      :type="showPasswords[field.key] ? 'text' : 'password'"
                      class="input"
                      :value="getFieldValue(field.key) ?? ''"
                      :placeholder="field.placeholder"
                      :disabled="field.readonly"
                      :readonly="field.readonly"
                      @input="emit('update', field.key, ($event.target as HTMLInputElement).value)"
                    />
                    <button 
                      class="toggle-visibility" 
                      type="button"
                      :disabled="field.readonly"
                      @click="showPasswords[field.key] = !showPasswords[field.key]"
                    >
                      <Icon :icon="showPasswords[field.key] ? 'lucide:eye-off' : 'lucide:eye'" />
                    </button>
                  </div>

                  <!-- Number 类型 -->
                  <template v-else-if="field.type === 'number'">
                    <div v-if="field.min !== undefined && field.max !== undefined && (field.max - field.min) <= 100" class="slider-input">
                      <input 
                        type="range" 
                        :min="field.min"
                        :max="field.max"
                        :step="field.step ?? 1"
                        :value="getFieldValue(field.key) ?? field.default ?? field.min"
                        :disabled="field.readonly"
                        @input="emit('update', field.key, parseFloat(($event.target as HTMLInputElement).value))"
                      />
                      <span class="slider-value">{{ getFieldValue(field.key) ?? field.default ?? field.min }}</span>
                    </div>
                    <input 
                      v-else
                      type="number" 
                      class="input"
                      :min="field.min"
                      :max="field.max"
                      :step="field.step"
                      :value="getFieldValue(field.key) ?? field.default ?? ''"
                      :placeholder="field.placeholder"
                      :disabled="field.readonly"
                      :readonly="field.readonly"
                      @input="emit('update', field.key, parseFloat(($event.target as HTMLInputElement).value) || 0)"
                    />
                  </template>

                  <!-- Array 类型 -->
                  <div v-else-if="field.type === 'array'" class="array-input">
                    <input 
                      type="text" 
                      class="input"
                      :value="formatArrayValue(getFieldValue(field.key))"
                      :placeholder="field.placeholder"
                      :disabled="field.readonly"
                      :readonly="field.readonly"
                      @input="emit('update', field.key, parseArrayValue(($event.target as HTMLInputElement).value))"
                    />
                    <span class="input-hint">多个值用逗号分隔</span>
                  </div>

                  <!-- String 类型 (默认) -->
                  <input 
                    v-else
                    type="text" 
                    class="input"
                    :value="getFieldValue(field.key) ?? field.default ?? ''"
                    :placeholder="field.placeholder"
                    :disabled="field.readonly"
                    :readonly="field.readonly"
                    @input="emit('update', field.key, ($event.target as HTMLInputElement).value)"
                  />
                </div>
              </template>
            </div>
          </template>
        </div>
      </div>
    </div>

    <!-- 自定义配置区域（显示未在描述文件中定义的配置），仅在"其他"标签页显示 -->
    <div v-if="activeTab === 'other' && customSections.length > 0" class="config-content">
      <div class="config-group custom-section">
        <div class="group-header" @click="toggleGroup('__custom__')">
          <div class="group-title">
            <Icon icon="lucide:file-json" />
            <h3>未分类配置</h3>
          </div>
          <div class="group-meta">
            <span class="group-hint">配置文件中未注释的配置项</span>
            <Icon :icon="collapsedGroups['__custom__'] ? 'lucide:chevron-down' : 'lucide:chevron-up'" />
          </div>
        </div>
        <div v-show="!collapsedGroups['__custom__']" class="group-content">
          <div v-for="section in customSections" :key="section.name" class="custom-subsection">
            <h4 class="subsection-title">{{ section.display_name }}</h4>
            <div 
              v-for="field in section.fields" 
              :key="field.full_key" 
              class="field-card"
              :class="{ inline: field.type === 'boolean' }"
            >
              <div class="field-left" v-if="field.type === 'boolean'">
                <div class="field-header">
                  <span class="field-name">{{ field.key }}</span>
                </div>
                <div v-if="field.description" class="field-description">
                  {{ field.description }}
                </div>
              </div>
              <template v-else>
                <div class="field-header">
                  <span class="field-name">{{ field.key }}</span>
                  <span class="field-key">{{ field.full_key }}</span>
                </div>
                <div v-if="field.description" class="field-description">
                  {{ field.description }}
                </div>
              </template>
              
              <div class="field-input" v-if="field.type !== 'boolean'">
                <FieldEditor 
                  :field="field"
                  :value="getFieldValue(field.full_key)"
                  @update="(v) => emit('update', field.full_key, v)"
                />
              </div>
              <label v-else class="toggle-switch">
                <input 
                  type="checkbox" 
                  :checked="Boolean(getFieldValue(field.full_key))"
                  @change="emit('update', field.full_key, ($event.target as HTMLInputElement).checked)"
                />
                <span class="toggle-slider"></span>
              </label>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { Icon } from '@iconify/vue'
import type { ConfigSection } from '@/api'
import FieldEditor from './FieldEditor.vue'
import StringArrayEditor from './StringArrayEditor.vue'
import KeyValueEditor from './KeyValueEditor.vue'
import MasterUsersEditor from './special/MasterUsersEditor.vue'
import ExpressionRulesEditor from './special/ExpressionRulesEditor.vue'
import ReactionRulesEditor from './special/ReactionRulesEditor.vue'
import WebSearchEnginesEditor from './special/WebSearchEnginesEditor.vue'
import ChatListEditor from './special/ChatListEditor.vue'
import { botConfigGroups, type ConfigGroupDef, type ConfigFieldDef } from '@/config/configDescriptions'

const props = defineProps<{
  parsedData: Record<string, unknown>
  editedValues: Record<string, unknown>
  configSchema: ConfigSection[]
}>()

const emit = defineEmits<{
  (e: 'update', key: string, value: unknown): void
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

const getOptionLabel = (options: { value: any, label: string }[], value: any) => {
  const option = options.find(opt => opt.value === value)
  return option ? option.label : value
}

onMounted(() => {
  document.addEventListener('click', handleOutsideClick)
})

onUnmounted(() => {
  document.removeEventListener('click', handleOutsideClick)
})

// 导航栏标签页定义
interface NavTab {
  key: string
  name: string
  description: string
  groupKeys: string[]  // 该标签页包含的配置组 key
}

const navTabs: NavTab[] = [
  {
    key: 'basic',
    name: '基本信息',
    description: '配置机器人的基础信息和账号设置',
    groupKeys: ['inner', 'bot', 'command', 'permission']
  },
  {
    key: 'personality',
    name: '人格',
    description: '配置机器人的性格特点和身份设定',
    groupKeys: ['personality']
  },
  {
    key: 'chat',
    name: '聊天',
    description: '配置机器人的聊天行为、私聊和群聊模式',
    groupKeys: ['chat', 'message_receive', 'kokoro_flow_chatter', 'cross_context', 'affinity_flow', 'proactive_thinking']
  },
  {
    key: 'expression',
    name: '表达',
    description: '配置机器人学习和使用表达方式',
    groupKeys: ['expression', 'reaction']
  },
  {
    key: 'function',
    name: '功能',
    description: '配置机器人的各项功能模块',
    groupKeys: ['tool', 'voice', 'web_search', 'video_analysis', 'planning_system', 'notice', 'plugin_http_system']
  },
  {
    key: 'process',
    name: '处理',
    description: '配置回复的后处理和优化',
    groupKeys: ['response_post_process', 'chinese_typo', 'response_splitter']
  },
  {
    key: 'emotion',
    name: '情绪',
    description: '配置机器人的情绪系统和表情包',
    groupKeys: ['mood', 'emoji']
  },
  {
    key: 'memory',
    name: '知识库',
    description: '配置记忆系统和向量数据库',
    groupKeys: ['memory', 'database', 'lpmm_knowledge']
  },
  {
    key: 'advanced',
    name: '高级',
    description: '高级配置选项，包括视频分析、消息总线等',
    groupKeys: ['video_analysis_expert', 'message_bus', 'custom_prompt', 'dependency_management']
  },
  {
    key: 'other',
    name: '其他',
    description: '日志、调试等其他配置',
    groupKeys: ['log', 'debug']
  }
]

// 状态
const activeTab = ref('basic')
const searchQuery = ref('')
const showAdvanced = ref(false)
const showPasswords = ref<Record<string, boolean>>({})
const collapsedGroups = ref<Record<string, boolean>>({})

// 合并 parsedData 和 editedValues 的计算属性
const mergedConfigData = computed(() => {
  const merged = JSON.parse(JSON.stringify(props.parsedData)) as Record<string, any>
  
  // 将 editedValues 中的值合并进去
  for (const [fullKey, value] of Object.entries(props.editedValues)) {
    const keys = fullKey.split('.')
    let current = merged as Record<string, any>
    
    // 遍历到倒数第二个键，创建嵌套对象
    for (let i = 0; i < keys.length - 1; i++) {
      const key = keys[i]
      if (!key) continue
      if (!current[key] || typeof current[key] !== 'object') {
        current[key] = {}
      }
      current = current[key] as Record<string, any>
    }
    
    // 设置最后一个键的值
    const lastKey = keys[keys.length - 1]
    if (lastKey) {
      current[lastKey] = value
    }
  }
  
  return merged
})

// 获取当前标签页信息
const currentTabInfo = computed(() => {
  const tab = navTabs.find(t => t.key === activeTab.value)
  return tab ?? navTabs[0]
})

// 获取当前标签页的配置组（原始）
const currentTabGroups = computed(() => {
  const tab = currentTabInfo.value
  return botConfigGroups.filter(group => tab?.groupKeys.includes(group.key))
})

// 获取当前标签页的过滤后配置组
const filteredCurrentTabGroups = computed(() => {
  let groups = currentTabGroups.value
  
  if (!searchQuery.value) {
    return groups
  }
  
  const query = searchQuery.value.toLowerCase()
  return groups.filter(group => {
    // 检查分组名称
    if (group.name.toLowerCase().includes(query)) return true
    // 检查字段
    return group.fields.some(field => 
      field.name.toLowerCase().includes(query) ||
      field.description.toLowerCase().includes(query) ||
      field.key.toLowerCase().includes(query)
    )
  })
})

// 检查当前标签页是否有高级字段
const hasAdvancedFieldsInCurrentTab = computed(() => {
  return currentTabGroups.value.some(group => 
    group.fields.some(field => field.advanced)
  )
})

// 获取可见字段（考虑高级选项过滤）
function getVisibleFields(group: ConfigGroupDef): ConfigFieldDef[] {
  let fields = group.fields
  
  // 过滤隐藏字段（由特殊编辑器管理的字段）
  fields = fields.filter(field => !field.hidden)
  
  // 搜索过滤
  if (searchQuery.value) {
    const query = searchQuery.value.toLowerCase()
    fields = fields.filter(field =>
      field.name.toLowerCase().includes(query) ||
      field.description.toLowerCase().includes(query) ||
      field.key.toLowerCase().includes(query)
    )
  }
  
  // 高级选项过滤
  if (!showAdvanced.value) {
    fields = fields.filter(field => !field.advanced)
  }
  
  return fields
}

// 自定义配置（未在描述中定义的）
const customSections = computed(() => {
  const definedKeys = new Set<string>()
  const objectTypeKeys = new Set<string>() // 对象类型的键，用于匹配嵌套属性
  
  botConfigGroups.forEach(group => {
    group.fields.forEach(field => {
      definedKeys.add(field.key)
      // 如果字段类型是 object，记录下来用于匹配子属性
      if (field.type === 'object') {
        objectTypeKeys.add(field.key)
      }
    })
  })
  
  // 检查一个键是否已被定义（包括作为对象类型的子属性）
  function isKeyDefined(fullKey: string): boolean {
    if (definedKeys.has(fullKey)) return true
    // 检查是否是某个对象类型配置的子属性
    for (const objKey of objectTypeKeys) {
      if (fullKey.startsWith(objKey + '.')) {
        return true
      }
    }
    return false
  }
  
  // 过滤出未定义的配置节
  return props.configSchema.filter(section => {
    // 检查是否有任何字段不在定义中
    return section.fields.some(field => !isKeyDefined(field.full_key))
  }).map(section => ({
    ...section,
    fields: section.fields.filter(field => !isKeyDefined(field.full_key))
  }))
})

// 切换分组展开/折叠
function toggleGroup(key: string) {
  collapsedGroups.value[key] = !collapsedGroups.value[key]
}

// 获取字段值
function getFieldValue(fullKey: string): unknown {
  // 优先返回编辑后的值
  if (fullKey in props.editedValues) {
    return props.editedValues[fullKey]
  }
  
  // 否则从原始解析数据中获取
  const keys = fullKey.split('.')
  let current: unknown = props.parsedData
  for (const key of keys) {
    if (current && typeof current === 'object' && key in (current as Record<string, unknown>)) {
      current = (current as Record<string, unknown>)[key]
    } else {
      return undefined
    }
  }
  return current
}

// 格式化数组值
function formatArrayValue(value: unknown): string {
  if (Array.isArray(value)) {
    return value.join(', ')
  }
  return ''
}

// 解析数组值
function parseArrayValue(value: string): string[] {
  return value.split(',').map(s => s.trim()).filter(s => s)
}
</script>

<style scoped>
.main-config-editor {
  /* Map MD3 variables to component variables */
  --bg-primary: var(--md-sys-color-surface);
  --bg-secondary: var(--md-sys-color-surface-container);
  --bg-tertiary: var(--md-sys-color-surface-container-high);
  --bg-hover: var(--md-sys-color-surface-container-highest);
  
  --text-primary: var(--md-sys-color-on-surface);
  --text-secondary: var(--md-sys-color-on-surface-variant);
  --text-tertiary: var(--md-sys-color-outline);
  
  --border-color: var(--md-sys-color-outline-variant);
  
  --primary: var(--md-sys-color-primary);
  --primary-bg: var(--md-sys-color-primary-container);
  
  --radius-sm: var(--md-sys-shape-corner-extra-small);
  --radius: var(--md-sys-shape-corner-medium);
  --radius-lg: var(--md-sys-shape-corner-large);
  
  --transition-fast: 0.2s ease;
  --warning: #f59e0b;

  display: flex;
  flex-direction: column;
  gap: 20px;
}

/* 顶部导航栏 */
.config-nav-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 16px;
  background: var(--bg-primary);
  border-radius: var(--radius-lg);
  border: 1px solid var(--border-color);
}

.nav-tabs {
  display: flex;
  gap: 4px;
  flex-wrap: wrap;
}

.nav-tab {
  padding: 10px 20px;
  background: transparent;
  border: none;
  border-radius: var(--radius);
  color: var(--text-secondary);
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all var(--transition-fast);
  white-space: nowrap;
}

.nav-tab:hover {
  background: var(--bg-hover);
  color: var(--text-primary);
}

.nav-tab.active {
  background: var(--primary-bg);
  color: var(--primary);
}

.nav-actions {
  display: flex;
  align-items: center;
  gap: 12px;
}

/* 专家模式勾选框 */
.expert-checkbox-wrapper {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 14px;
  background: var(--bg-secondary);
  border-radius: var(--radius);
  cursor: pointer;
  transition: all var(--transition-fast);
  user-select: none;
}

.expert-checkbox-wrapper:hover {
  background: var(--bg-hover);
}

.expert-checkbox {
  position: absolute;
  opacity: 0;
  width: 0;
  height: 0;
}

.checkbox-mark {
  width: 18px;
  height: 18px;
  border: 2px solid var(--border-color);
  border-radius: 4px;
  position: relative;
  transition: all var(--transition-fast);
}

.expert-checkbox:checked + .checkbox-mark {
  background: linear-gradient(135deg, #f59e0b, #d97706);
  border-color: #f59e0b;
}

.expert-checkbox:checked + .checkbox-mark::after {
  content: '';
  position: absolute;
  left: 5px;
  top: 2px;
  width: 5px;
  height: 9px;
  border: solid white;
  border-width: 0 2px 2px 0;
  transform: rotate(45deg);
}

.checkbox-label {
  font-size: 13px;
  color: var(--text-secondary);
}

.expert-checkbox:checked ~ .checkbox-label {
  color: #f59e0b;
}

/* 标签页标题 */
.tab-header {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 16px 20px;
  background: var(--bg-primary);
  border-radius: var(--radius-lg);
  border: 1px solid var(--border-color);
}

.tab-title {
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0;
}

.tab-description {
  flex: 1;
  font-size: 13px;
  color: var(--text-tertiary);
  margin: 0;
}

.add-rule-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 14px;
  background: var(--bg-secondary);
  border: 1px solid var(--border-color);
  border-radius: var(--radius);
  color: var(--text-secondary);
  font-size: 13px;
  cursor: pointer;
  transition: all var(--transition-fast);
}

.add-rule-btn:hover {
  background: var(--bg-hover);
  color: var(--text-primary);
}

/* 工具栏 */
.config-toolbar {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 12px 16px;
  background: var(--bg-primary);
  border-radius: var(--radius-lg);
  border: 1px solid var(--border-color);
}

.search-box {
  flex: 1;
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 14px;
  background: var(--bg-secondary);
  border-radius: var(--radius);
  border: 1px solid var(--border-color);
}

.search-box svg {
  color: var(--text-tertiary);
  font-size: 18px;
}

.search-input {
  flex: 1;
  border: none;
  background: transparent;
  color: var(--text-primary);
  font-size: 14px;
  outline: none;
}

.search-input::placeholder {
  color: var(--text-tertiary);
}

/* 配置内容区域 */
.config-content {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.expert-badge {
  font-size: 10px;
  padding: 2px 6px;
  border-radius: 4px;
  background: linear-gradient(135deg, #f59e0b, #d97706);
  color: white;
  margin-left: 8px;
}

/* 配置分组 */
.config-group {
  background: var(--bg-primary);
  border-radius: var(--radius-lg);
  border: 1px solid var(--border-color);
}

.config-group.single-group {
  border: none;
  background: transparent;
}

.config-group.single-group .group-content {
  padding: 0;
}

.config-group.expert-group {
  border-color: #f59e0b;
  border-width: 2px;
}

.config-group.expert-group .group-header {
  background: linear-gradient(135deg, rgba(245, 158, 11, 0.1), rgba(217, 119, 6, 0.05));
}

.group-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 20px;
  background: var(--bg-secondary);
  border-bottom: 1px solid var(--border-color);
  cursor: pointer;
  transition: background var(--transition-fast);
  border-top-left-radius: var(--radius-lg);
  border-top-right-radius: var(--radius-lg);
}

.group-header:hover {
  background: var(--bg-hover);
}

.config-group.collapsed .group-header {
  border-bottom: none;
}

.group-title {
  display: flex;
  align-items: center;
  gap: 10px;
}

.group-title svg {
  color: var(--primary);
  font-size: 18px;
}

.group-title h3 {
  font-size: 15px;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0;
}

.group-meta {
  display: flex;
  align-items: center;
  gap: 12px;
}

.group-hint {
  font-size: 12px;
  color: var(--text-tertiary);
}

.group-meta svg {
  color: var(--text-tertiary);
  font-size: 16px;
}

.group-content {
  padding: 20px;
  display: grid;
  gap: 16px;
}

/* 字段卡片 */
.field-card {
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding: 16px;
  background: var(--bg-secondary);
  border-radius: var(--radius);
  border: 1px solid transparent;
  transition: all var(--transition-fast);
  position: relative;
}

.field-card:hover {
  border-color: var(--border-color);
}

.field-card.inline {
  flex-direction: row;
  align-items: center;
  justify-content: space-between;
}

.field-card.advanced {
  border-left: 3px solid var(--warning);
}

.field-card.expert {
  border-left: 3px solid #f59e0b;
}

.field-card.readonly {
  opacity: 0.8;
  background: var(--bg-tertiary);
}

.field-card.special-editor-card {
  padding: 0;
  background: transparent;
  border: none;
}

/* 只读标签 */
.readonly-badge {
  position: absolute;
  top: 8px;
  right: 8px;
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 2px 8px;
  background: var(--bg-primary);
  border: 1px solid var(--border-color);
  border-radius: 10px;
  font-size: 10px;
  color: var(--text-tertiary);
}

.field-left {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.field-header {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}

.field-name {
  font-size: 14px;
  font-weight: 500;
  color: var(--text-primary);
}

.field-key {
  font-size: 11px;
  font-family: 'JetBrains Mono', monospace;
  color: var(--text-tertiary);
  padding: 2px 8px;
  background: var(--bg-primary);
  border-radius: var(--radius-sm);
}

.advanced-badge {
  font-size: 10px;
  padding: 2px 6px;
  background: var(--warning);
  color: white;
  border-radius: var(--radius-sm);
}

.field-description {
  font-size: 12px;
  color: var(--text-tertiary);
  line-height: 1.5;
}

.field-input {
  margin-top: 4px;
}

/* 输入框 */
.input {
  width: 100%;
  padding: 10px 14px;
  border: 1px solid var(--border-color);
  border-radius: var(--radius);
  background: var(--bg-primary);
  color: var(--text-primary);
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
  background: var(--bg-tertiary);
  color: var(--text-tertiary);
  cursor: not-allowed;
}

.input:disabled:focus,
.input:read-only:focus {
  border-color: var(--border-color);
  box-shadow: none;
}

.input.textarea {
  resize: vertical;
  min-height: 80px;
  line-height: 1.5;
}

select.input {
  cursor: pointer;
}

select.input:disabled {
  cursor: not-allowed;
}

/* 密码输入 */
.password-input {
  position: relative;
  display: flex;
}

.password-input .input {
  padding-right: 44px;
}

.toggle-visibility {
  position: absolute;
  right: 8px;
  top: 50%;
  transform: translateY(-50%);
  width: 28px;
  height: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: transparent;
  border: none;
  border-radius: var(--radius-sm);
  color: var(--text-tertiary);
  cursor: pointer;
  transition: all var(--transition-fast);
}

.toggle-visibility:hover {
  background: var(--bg-secondary);
  color: var(--text-primary);
}

/* Toggle 开关 */
.toggle-switch {
  display: flex;
  align-items: center;
  cursor: pointer;
  flex-shrink: 0;
}

.toggle-switch.disabled {
  cursor: not-allowed;
  opacity: 0.5;
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
  top: 3px;
  left: 3px;
  width: 20px;
  height: 20px;
  background: white;
  border-radius: 50%;
  transition: transform var(--transition-fast);
  box-shadow: var(--shadow-sm);
}

.toggle-switch input:checked + .toggle-slider {
  background: var(--primary);
}

.toggle-switch input:checked + .toggle-slider::after {
  transform: translateX(22px);
}

/* 滑块输入 */
.slider-input {
  display: flex;
  align-items: center;
  gap: 16px;
}

.slider-input input[type="range"] {
  flex: 1;
  height: 6px;
  -webkit-appearance: none;
  appearance: none;
  background: var(--bg-hover);
  border-radius: 3px;
  outline: none;
}

.slider-input input[type="range"]::-webkit-slider-thumb {
  -webkit-appearance: none;
  appearance: none;
  width: 18px;
  height: 18px;
  background: var(--primary);
  border-radius: 50%;
  cursor: pointer;
  box-shadow: 0 2px 6px rgba(59, 130, 246, 0.4);
}

.slider-input input[type="range"]::-moz-range-thumb {
  width: 18px;
  height: 18px;
  background: var(--primary);
  border-radius: 50%;
  cursor: pointer;
  border: none;
  box-shadow: 0 2px 6px rgba(59, 130, 246, 0.4);
}

.slider-value {
  min-width: 48px;
  text-align: right;
  font-size: 14px;
  font-weight: 500;
  color: var(--primary);
}

/* 数组输入 */
.array-input {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.input-hint {
  font-size: 11px;
  color: var(--text-tertiary);
}

/* 自定义配置区域 */
.custom-section {
  border-color: var(--border-color);
}

.custom-subsection {
  margin-bottom: 16px;
}

.custom-subsection:last-child {
  margin-bottom: 0;
}

.subsection-title {
  font-size: 13px;
  font-weight: 600;
  color: var(--text-secondary);
  margin: 0 0 12px 0;
  padding-bottom: 8px;
  border-bottom: 1px solid var(--border-color);
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

.custom-select-container.is-disabled .custom-select-trigger {
  opacity: 0.6;
  cursor: not-allowed;
  background-color: var(--bg-tertiary);
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
</style>
