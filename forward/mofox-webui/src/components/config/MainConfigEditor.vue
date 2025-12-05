<template>
  <div class="main-config-editor">
    <!-- 配置概览 -->
    <div class="config-overview">
      <div class="overview-card">
        <div class="overview-icon bot">
          <Icon icon="lucide:bot" />
        </div>
        <div class="overview-info">
          <h4>机器人配置</h4>
          <p>管理机器人的基础设置和行为参数</p>
        </div>
      </div>
    </div>

    <!-- 搜索和筛选 -->
    <div class="config-toolbar">
      <div class="search-box">
        <Icon icon="lucide:search" />
        <input 
          v-model="searchQuery" 
          type="text" 
          placeholder="搜索配置项..." 
          class="search-input"
        />
      </div>
      <div class="filter-buttons">
        <button 
          class="filter-btn" 
          :class="{ active: showAdvanced }"
          @click="showAdvanced = !showAdvanced"
        >
          <Icon icon="lucide:settings-2" />
          {{ showAdvanced ? '隐藏高级选项' : '显示高级选项' }}
        </button>
      </div>
    </div>

    <!-- 配置分组 -->
    <div class="config-groups">
      <div 
        v-for="group in filteredGroups" 
        :key="group.key" 
        class="config-group"
        :class="{ collapsed: collapsedGroups[group.key] }"
      >
        <div class="group-header" @click="toggleGroup(group.key)">
          <div class="group-title">
            <Icon :icon="group.icon" />
            <h3>{{ group.name }}</h3>
          </div>
          <div class="group-meta">
            <span class="group-hint">{{ group.description }}</span>
            <Icon :icon="collapsedGroups[group.key] ? 'lucide:chevron-down' : 'lucide:chevron-up'" />
          </div>
        </div>
        
        <div v-show="!collapsedGroups[group.key]" class="group-content">
          <template v-for="field in getVisibleFields(group)" :key="field.key">
            <div 
              class="field-card"
              :class="{ 
                inline: field.type === 'boolean',
                advanced: field.advanced
              }"
            >
              <!-- Boolean 类型 -->
              <template v-if="field.type === 'boolean'">
                <div class="field-left">
                  <div class="field-header">
                    <span class="field-name">{{ field.name }}</span>
                    <span v-if="field.advanced" class="advanced-badge">高级</span>
                  </div>
                  <div class="field-description">{{ field.description }}</div>
                </div>
                <label class="toggle-switch">
                  <input 
                    type="checkbox" 
                    :checked="Boolean(getFieldValue(field.key))"
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
                </div>
                <div class="field-description">{{ field.description }}</div>
                
                <div class="field-input">
                  <!-- Select 类型 -->
                  <select 
                    v-if="field.type === 'select'"
                    class="input"
                    :value="getFieldValue(field.key) ?? field.default"
                    @change="emit('update', field.key, ($event.target as HTMLSelectElement).value)"
                  >
                    <option 
                      v-for="opt in field.options" 
                      :key="opt.value" 
                      :value="opt.value"
                    >
                      {{ opt.label }}
                    </option>
                  </select>

                  <!-- Textarea 类型 -->
                  <textarea 
                    v-else-if="field.type === 'textarea'"
                    class="input textarea"
                    :value="String(getFieldValue(field.key) ?? field.default ?? '')"
                    :placeholder="field.placeholder"
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
                      @input="emit('update', field.key, ($event.target as HTMLInputElement).value)"
                    />
                    <button 
                      class="toggle-visibility" 
                      type="button"
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
                    @input="emit('update', field.key, ($event.target as HTMLInputElement).value)"
                  />
                </div>
              </template>
            </div>
          </template>
        </div>
      </div>
    </div>

    <!-- 自定义配置区域（显示未在描述文件中定义的配置） -->
    <div v-if="customSections.length > 0" class="config-group custom-section">
      <div class="group-header" @click="toggleGroup('__custom__')">
        <div class="group-title">
          <Icon icon="lucide:file-json" />
          <h3>其他配置</h3>
        </div>
        <div class="group-meta">
          <span class="group-hint">未分类的配置项</span>
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
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { Icon } from '@iconify/vue'
import type { ConfigSection } from '@/api'
import FieldEditor from './FieldEditor.vue'
import { botConfigGroups, type ConfigGroupDef, type ConfigFieldDef } from '@/config/configDescriptions'

const props = defineProps<{
  parsedData: Record<string, unknown>
  editedValues: Record<string, unknown>
  configSchema: ConfigSection[]
}>()

const emit = defineEmits<{
  (e: 'update', key: string, value: unknown): void
}>()

// 状态
const searchQuery = ref('')
const showAdvanced = ref(false)
const showPasswords = ref<Record<string, boolean>>({})
const collapsedGroups = ref<Record<string, boolean>>({})

// 过滤后的配置分组
const filteredGroups = computed(() => {
  if (!searchQuery.value) {
    return botConfigGroups
  }
  
  const query = searchQuery.value.toLowerCase()
  return botConfigGroups.filter(group => {
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

// 获取可见字段（考虑高级选项过滤）
function getVisibleFields(group: ConfigGroupDef): ConfigFieldDef[] {
  let fields = group.fields
  
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
  botConfigGroups.forEach(group => {
    group.fields.forEach(field => {
      definedKeys.add(field.key)
    })
  })
  
  // 过滤出未定义的配置节
  return props.configSchema.filter(section => {
    // 检查是否有任何字段不在定义中
    return section.fields.some(field => !definedKeys.has(field.full_key))
  }).map(section => ({
    ...section,
    fields: section.fields.filter(field => !definedKeys.has(field.full_key))
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
  display: flex;
  flex-direction: column;
  gap: 24px;
}

/* 配置概览 */
.config-overview {
  display: flex;
  gap: 16px;
}

.overview-card {
  flex: 1;
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 20px;
  background: linear-gradient(135deg, var(--primary-bg), rgba(59, 130, 246, 0.2));
  border-radius: var(--radius-lg);
  border: 1px solid var(--border-color);
}

.overview-icon {
  width: 56px;
  height: 56px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: var(--radius);
  font-size: 28px;
}

.overview-icon.bot {
  background: linear-gradient(135deg, #3b82f6, #1d4ed8);
  color: white;
}

.overview-info h4 {
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0 0 4px 0;
}

.overview-info p {
  font-size: 13px;
  color: var(--text-tertiary);
  margin: 0;
}

/* 工具栏 */
.config-toolbar {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 16px;
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

.filter-buttons {
  display: flex;
  gap: 8px;
}

.filter-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 10px 16px;
  background: var(--bg-secondary);
  border: 1px solid var(--border-color);
  border-radius: var(--radius);
  color: var(--text-secondary);
  font-size: 13px;
  cursor: pointer;
  transition: all var(--transition-fast);
}

.filter-btn:hover {
  background: var(--bg-hover);
  color: var(--text-primary);
}

.filter-btn.active {
  background: var(--primary-bg);
  border-color: var(--primary);
  color: var(--primary);
}

/* 配置分组 */
.config-groups {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.config-group {
  background: var(--bg-primary);
  border-radius: var(--radius-lg);
  border: 1px solid var(--border-color);
  overflow: hidden;
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

.input.textarea {
  resize: vertical;
  min-height: 80px;
  line-height: 1.5;
}

select.input {
  cursor: pointer;
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
</style>
