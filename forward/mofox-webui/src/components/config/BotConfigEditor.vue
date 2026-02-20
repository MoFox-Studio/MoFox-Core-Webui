<template>
  <div class="bot-config-editor">
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
      <div class="search-box" :class="{ focused: isSearchFocused }">
        <Icon icon="lucide:search" />
        <input
          ref="searchInputRef"
          v-model="searchQuery"
          type="text"
          placeholder="搜索配置项... (Ctrl+K)"
          class="search-input"
          @focus="isSearchFocused = true"
          @blur="isSearchFocused = false"
          @keydown.escape="clearSearch"
        />
        <button
          v-if="searchQuery"
          class="clear-search-btn"
          @click="clearSearch"
          title="清除搜索"
        >
          <Icon icon="lucide:x" />
        </button>
        <span class="search-shortcut" v-if="!searchQuery && !isSearchFocused">Ctrl+K</span>
      </div>
      <div v-if="searchQuery" class="search-results-hint">
        找到 {{ filteredFieldsCount }} 个匹配项
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
              <OwnerListEditor
                v-if="field.specialEditor === 'owner_list'"
                :value="getFieldValue(field.key)"
                :title="field.name"
                :description="field.description"
                @update="(v: unknown) => emit('update', field.key, v)"
              />
              <StringArrayEditor
                v-else-if="field.specialEditor === 'string_array'"
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

                  <!-- Textarea Tall 类型（人格/长文本专用） -->
                  <textarea 
                    v-else-if="field.type === 'textarea_tall'"
                    class="input textarea textarea-tall"
                    :value="String(getFieldValue(field.key) ?? field.default ?? '')"
                    :placeholder="field.placeholder"
                    :disabled="field.readonly"
                    :readonly="field.readonly"
                    @input="emit('update', field.key, ($event.target as HTMLTextAreaElement).value)"
                    rows="7"
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
                  <input
                    v-else-if="field.type === 'number'"
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

  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted, onUnmounted, nextTick } from 'vue'
import { Icon } from '@iconify/vue'
import { StringArrayEditor, KeyValueEditor, OwnerListEditor } from './editors'
import type { ConfigGroupSchema as ConfigGroupSchema, ConfigFieldSchema as ConfigFieldSchema } from '@/api/coreConfig'

const props = defineProps<{
  parsedData: Record<string, Record<string, unknown>>
  editedValues: Record<string, unknown>
  configSchema: ConfigGroupSchema[]
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

// 导航栏标签页：由后端 Schema 动态生成，每个 group 对应一个 tab
const navTabs = computed(() => {
  return props.configSchema.map(group => ({
    key: group.key,
    name: group.name,
    description: group.description,
  }))
})

// 状态：activeTab 初始为 schema 第一个 group 的 key，schema 加载后自动对齐
const activeTab = ref('')
watch(
  () => props.configSchema,
  (schema) => {
    if (schema.length > 0 && schema[0] && (!activeTab.value || !schema.find(g => g.key === activeTab.value))) {
      activeTab.value = schema[0].key
    }
  },
  { immediate: true }
)
const searchQuery = ref('')
const showAdvanced = ref(false)
const showPasswords = ref<Record<string, boolean>>({})
const collapsedGroups = ref<Record<string, boolean>>({})
const isSearchFocused = ref(false)
const searchInputRef = ref<HTMLInputElement | null>(null)

// 清除搜索
function clearSearch() {
  searchQuery.value = ''
  searchInputRef.value?.blur()
}

// 键盘快捷键处理
function handleKeydown(event: KeyboardEvent) {
  // Ctrl+K 或 Cmd+K 聚焦搜索框
  if ((event.ctrlKey || event.metaKey) && event.key === 'k') {
    event.preventDefault()
    nextTick(() => {
      searchInputRef.value?.focus()
    })
  }
}

// 计算匹配的字段数量
const filteredFieldsCount = computed(() => {
  if (!searchQuery.value) return 0
  let count = 0
  filteredCurrentTabGroups.value.forEach(group => {
    count += getVisibleFields(group).length
  })
  return count
})

onMounted(() => {
  document.addEventListener('keydown', handleKeydown)
})

onUnmounted(() => {
  document.removeEventListener('keydown', handleKeydown)
})

// 合并 parsedData 和 editedValues（供 WebSearchEnginesEditor 等特殊编辑器使用）
const mergedConfigData = computed(() => {
  const merged = JSON.parse(JSON.stringify(props.parsedData)) as Record<string, Record<string, any>>
  for (const [fullKey, value] of Object.entries(props.editedValues)) {
    const [section, field] = fullKey.split('.', 2)
    if (section && field) {
      if (!merged[section]) merged[section] = {}
      merged[section][field] = value
    }
  }
  return merged
})

// 获取当前标签页信息
const currentTabInfo = computed(() => {
  return navTabs.value.find(t => t.key === activeTab.value) ?? navTabs.value[0]
})

// 当前 tab 对应的 group（一个 tab = 一个 group）
const currentGroup = computed((): ConfigGroupSchema | undefined => {
  return props.configSchema.find(g => g.key === activeTab.value)
})

// 为了兼容模板中 currentTabGroups 的用法（数组形式），包装成单元素数组
const currentTabGroups = computed((): ConfigGroupSchema[] => {
  const g = currentGroup.value
  return g ? [g] : []
})

// 过滤后的配置组
const filteredCurrentTabGroups = computed((): ConfigGroupSchema[] => {
  if (!searchQuery.value) return currentTabGroups.value
  const query = searchQuery.value.toLowerCase()
  return currentTabGroups.value.filter(group => {
    if (group.name.toLowerCase().includes(query)) return true
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

// 获取可见字段（考虑高级/搜索过滤）
function getVisibleFields(group: ConfigGroupSchema): ConfigFieldSchema[] {
  let fields = group.fields.filter(f => !f.hidden)

  if (searchQuery.value) {
    const query = searchQuery.value.toLowerCase()
    fields = fields.filter(f =>
      f.name.toLowerCase().includes(query) ||
      f.description.toLowerCase().includes(query) ||
      f.key.toLowerCase().includes(query)
    )
  }

  if (!showAdvanced.value) {
    fields = fields.filter(f => !f.advanced)
  }

  return fields
}

// 切换分组展开/折叠
function toggleGroup(key: string) {
  collapsedGroups.value[key] = !collapsedGroups.value[key]
}

// 获取字段值 (fullKey 格式: "section.field")
function getFieldValue(fullKey: string): unknown {
  if (fullKey in props.editedValues) {
    return props.editedValues[fullKey]
  }
  const [section, field] = fullKey.split('.', 2)
  if (section && field && props.parsedData[section]) {
    return props.parsedData[section][field]
  }
  return undefined
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
.bot-config-editor {
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

.search-box.focused {
  border-color: var(--primary);
  box-shadow: 0 0 0 3px var(--primary-bg);
}

.clear-search-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 24px;
  height: 24px;
  background: var(--bg-hover);
  border: none;
  border-radius: 50%;
  color: var(--text-tertiary);
  cursor: pointer;
  transition: all var(--transition-fast);
}

.clear-search-btn:hover {
  background: var(--bg-tertiary);
  color: var(--text-primary);
}

.search-shortcut {
  font-size: 11px;
  padding: 2px 6px;
  background: var(--bg-tertiary);
  border-radius: 4px;
  color: var(--text-tertiary);
  font-family: monospace;
}

.search-results-hint {
  font-size: 12px;
  color: var(--text-secondary);
  padding: 4px 8px;
  background: var(--primary-bg);
  border-radius: var(--radius-sm);
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

.input.textarea.textarea-tall {
  min-height: 160px;
  line-height: 1.6;
  font-size: 13px;
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
