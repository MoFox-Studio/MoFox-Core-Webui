<!--
  @file PluginConfigView.vue
  @description 插件配置编辑页面
  
  功能说明：
  1. 编辑单个插件的配置文件
  2. 支持可视化编辑和源码编辑
  3. 自动解析配置结构生成表单
  4. 支持多种字段类型（布尔、文本、数组等）
  
  路由参数：
  - path: 配置文件路径（URL 编码）
  
  字段类型支持：
  - boolean: 开关切换
  - string/number: 文本输入
  - array: 列表编辑
  - array_of_objects: 对象数组编辑
  - object: 嵌套对象编辑
-->
<template>
  <div class="plugin-config-view">
    <!-- 顶部操作栏：返回按钮、标题、编辑模式切换、保存 -->
    <header class="config-header">
      <div class="header-left">
        <button class="m3-icon-button" @click="goBack" title="返回">
          <span class="material-symbols-rounded">arrow_back</span>
        </button>
        <div class="header-icon-container">
          <span class="material-symbols-rounded header-icon">
            {{ configInfo?.type === 'plugin' ? 'extension' : configInfo?.type === 'model' ? 'psychology' : 'settings' }}
          </span>
        </div>
        <div class="header-info">
          <h1>{{ configInfo?.display_name || '配置编辑器' }}</h1>
          <p class="config-path">
            <span class="material-symbols-rounded path-icon">folder</span>
            {{ decodedPath }}
          </p>
          <p v-if="configInfo?.description" class="config-description">
            {{ configInfo.description }}
          </p>
        </div>
      </div>
      <div class="header-actions">
        <div class="m3-segmented-button">
          <button 
            :class="['segment', { active: editorMode === 'visual' }]"
            @click="switchMode('visual')"
            :disabled="loading"
          >
            <span class="material-symbols-rounded">grid_view</span>
            可视化
          </button>
          <button 
            :class="['segment', { active: editorMode === 'source' }]"
            @click="switchMode('source')"
            :disabled="loading"
          >
            <span class="material-symbols-rounded">code</span>
            源码
          </button>
        </div>
        <button 
          class="m3-icon-button" 
          @click="showBackupsModal = true" 
          title="备份历史"
          :disabled="loading"
        >
          <span class="material-symbols-rounded">history</span>
        </button>
        <button 
          class="m3-button filled" 
          @click="saveCurrentConfig" 
          :disabled="saving || !hasChanges || loading"
        >
          <span class="material-symbols-rounded" :class="{ spinning: saving }">
            {{ saving ? 'progress_activity' : 'save' }}
          </span>
          {{ saving ? '保存中...' : '保存配置' }}
        </button>
      </div>
    </header>

    <!-- 可视化编辑模式 (合并 Schema 增强模式和传统模式) -->
    <div v-if="editorMode === 'visual'" class="visual-editor" :class="{ 'schema-mode': hasPluginSchema }">
      <div v-if="loading" class="loading-state">
        <span class="material-symbols-rounded spinning">progress_activity</span>
        <p>加载配置中...</p>
      </div>
      <div v-else-if="loadError" class="error-state">
        <span class="material-symbols-rounded error-icon">error</span>
        <p>{{ loadError }}</p>
        <button class="m3-button text" @click="loadConfig">
          <span class="material-symbols-rounded">refresh</span>
          重试
        </button>
      </div>
      <template v-else-if="mergedSections.length > 0">
        <!-- 配置导航栏 -->
        <div class="config-nav-bar" v-if="mergedSections.length > 1">
          <div class="nav-tabs" ref="navTabsRef" @wheel="handleNavTabsWheel">
            <button
              v-for="(section, idx) in mergedSections"
              :key="section.name"
              class="nav-tab"
              :class="{ active: activeSection === idx, 'has-schema': section.hasSchema }"
              @click="activeSection = idx"
            >
              <span class="material-symbols-rounded">{{ section.icon || getSectionIcon(section.name) }}</span>
              {{ section.display_name }}
              <span class="field-badge">{{ section.hasSchema ? (section.schemaFields?.length || 0) : section.fields.length }}</span>
              <span v-if="section.hasSchema" class="schema-badge" title="Schema 增强">
                <span class="material-symbols-rounded">auto_awesome</span>
              </span>
            </button>
          </div>
        </div>

        <!-- 配置内容 -->
        <div class="config-content">
          <div v-if="currentMergedSection" class="config-section">
            <div class="section-header">
              <div class="section-title">
                <span v-if="currentMergedSection.icon" class="material-symbols-rounded section-icon">{{ currentMergedSection.icon }}</span>
                <h3>{{ currentMergedSection.display_name }}</h3>
                <span class="section-badge">{{ currentMergedSection.fields.length }} 项配置</span>
                <span v-if="currentMergedSection.hasSchema" class="schema-indicator">
                  <span class="material-symbols-rounded">auto_awesome</span>
                  Schema
                </span>
              </div>
              <p v-if="currentMergedSection.description" class="section-description">
                {{ currentMergedSection.description }}
              </p>
            </div>
            
            <div class="fields-list">
              <!-- Schema 增强字段 -->
              <template v-if="currentMergedSection.hasSchema && currentMergedSection.schemaFields">
                <template v-for="field in currentMergedSection.schemaFields" :key="field.key">
                  <SchemaFieldEditor
                    v-if="!field.depends_on || checkSchemaFieldVisibility(field)"
                    :field="field"
                    :model-value="getSchemaFieldValue(currentMergedSection.name, field.key)"
                    :all-values="flatConfigValues"
                    @update:model-value="(v: unknown) => updateSchemaFieldValue(currentMergedSection!.name, field.key, v)"
                  />
                </template>
              </template>
              
              <!-- 传统字段 -->
              <template v-else>
                <div 
                  v-for="field in currentMergedSection.fields" 
                  :key="field.full_key" 
                  class="m3-card field-card"
                  :class="{ 
                    'inline-field': field.type === 'boolean',
                    'has-description': !!field.description 
                  }"
                >
                  <!-- Boolean 类型 -->
                  <template v-if="field.type === 'boolean'">
                    <div class="field-left">
                      <div class="field-header">
                        <span class="field-name">{{ field.key }}</span>
                        <span class="field-type-badge">{{ getTypeLabel(field.type) }}</span>
                      </div>
                      <div v-if="field.description" class="field-description">
                        <span class="material-symbols-rounded desc-icon">info</span>
                        <span>{{ field.description }}</span>
                      </div>
                    </div>
                    <label class="m3-switch">
                      <input 
                        type="checkbox" 
                        :checked="Boolean(getFieldValue(field.full_key))"
                        @change="(e: any) => updateFieldValue(field.full_key, e.target.checked)"
                      >
                      <span class="m3-switch-track">
                        <span class="m3-switch-thumb"></span>
                      </span>
                    </label>
                  </template>

                  <!-- 数组对象类型 (如 api_providers) -->
                  <template v-else-if="field.type === 'array_of_objects'">
                    <div class="field-header">
                      <span class="field-name">{{ field.key }}</span>
                      <span class="field-type-badge">{{ getTypeLabel(field.type) }}</span>
                    </div>
                    <div v-if="field.description" class="field-description">
                      <span class="material-symbols-rounded desc-icon">info</span>
                      <span>{{ field.description }}</span>
                    </div>
                    <div class="array-objects-container">
                      <div class="array-objects-info">
                        <span class="material-symbols-rounded">dataset</span>
                        包含 {{ field.items_count || 0 }} 个项目
                      </div>
                      <button 
                        class="m3-button text small" 
                        @click="expandArrayField(field)"
                      >
                        <span class="material-symbols-rounded">open_in_full</span>
                        在源码模式中编辑
                      </button>
                    </div>
                  </template>

                  <!-- 其他类型 -->
                  <template v-else>
                    <div class="field-header">
                      <span class="field-name">{{ field.key }}</span>
                      <span class="field-type-badge">{{ getTypeLabel(field.type) }}</span>
                    </div>
                    <div v-if="field.description" class="field-description with-margin">
                      <span class="material-symbols-rounded desc-icon">info</span>
                      <span>{{ field.description }}</span>
                    </div>
                    
                    <!-- 数组/列表类型 -->
                    <div v-if="field.type === 'array'" class="field-input-container">
                      <div class="array-input-wrapper">
                        <textarea
                          class="m3-input array-textarea"
                          :value="formatArrayValue(getFieldValue(field.full_key))"
                          @input="(e: any) => updateArrayValue(field.full_key, e.target.value)"
                          placeholder="每行一个值"
                          rows="5"
                        ></textarea>
                        <div class="input-hint">
                          <span class="material-symbols-rounded">info</span>
                          每行输入一个值
                        </div>
                      </div>
                    </div>

                    <!-- 数字类型 -->
                    <div v-else-if="field.type === 'integer' || field.type === 'number'" class="field-input-container">
                      <input 
                        type="number"
                        class="m3-input"
                        :value="getFieldValue(field.full_key)"
                        @input="(e: any) => updateFieldValue(field.full_key, parseNumber(e.target.value, field.type))"
                        :step="field.type === 'number' ? '0.01' : '1'"
                      >
                    </div>

                    <!-- 字符串/默认类型 -->
                    <div v-else class="field-input-container">
                      <input 
                        type="text"
                        class="m3-input"
                        :value="getFieldValue(field.full_key)"
                        @input="(e: any) => updateFieldValue(field.full_key, e.target.value)"
                        :placeholder="`输入 ${field.key}`"
                      >
                    </div>
                  </template>
                </div>
              </template>
            </div>
          </div>
        </div>
      </template>
      <div v-else class="empty-state">
        <span class="material-symbols-rounded empty-icon">description</span>
        <p>该配置文件为空</p>
      </div>
    </div>

    <!-- 源码编辑模式 (Monaco Editor) -->
    <div v-else class="source-editor">
      <div class="source-toolbar">
        <div class="toolbar-left">
          <span class="material-symbols-rounded">description</span>
          <span class="file-path">{{ decodedPath }}</span>
        </div>
        <div class="toolbar-actions">
          <button 
            class="m3-button text small" 
            @click="formatSource"
            :disabled="!sourceContent"
          >
            <span class="material-symbols-rounded">format_align_left</span>
            格式化
          </button>
          <button 
            class="m3-button text small" 
            @click="validateSource"
            :disabled="!sourceContent"
          >
            <span class="material-symbols-rounded">check_circle</span>
            验证
          </button>
        </div>
      </div>
      <div class="monaco-container">
        <vue-monaco-editor
          v-model:value="sourceContent"
          language="ini"
          :theme="isDarkMode ? 'vs-dark' : 'vs'"
          :options="monacoOptions"
          @mount="onEditorMount"
        />
      </div>
    </div>

    <!-- 备份管理弹窗 -->
    <div v-if="showBackupsModal" class="m3-dialog-overlay" @click.self="closeBackupsModal">
      <div class="m3-dialog">
        <div class="dialog-header">
          <div class="dialog-title">
            <span class="material-symbols-rounded">history</span>
            <h3>备份管理</h3>
          </div>
          <button class="m3-icon-button" @click="closeBackupsModal">
            <span class="material-symbols-rounded">close</span>
          </button>
        </div>
        <div class="dialog-content">
          <div v-if="backupsLoading" class="loading-state">
            <span class="material-symbols-rounded spinning">progress_activity</span>
            <p>加载备份列表...</p>
          </div>
          <div v-else-if="backups.length" class="backup-list">
            <div class="backup-item" v-for="backup in backups" :key="backup.path">
              <div class="backup-icon">
                <span class="material-symbols-rounded">save</span>
              </div>
              <div class="backup-info">
                <span class="backup-name">{{ backup.name }}</span>
                <span class="backup-meta">
                  <span class="material-symbols-rounded meta-icon">schedule</span>
                  {{ backup.created_at }}
                  <span class="separator">·</span>
                  <span class="material-symbols-rounded meta-icon">storage</span>
                  {{ formatSize(backup.size) }}
                </span>
              </div>
              <div class="backup-actions">
                <button 
                  class="m3-button text small" 
                  @click="restoreBackup(backup)"
                >
                  <span class="material-symbols-rounded">restore</span>
                  还原
                </button>
              </div>
            </div>
          </div>
          <div v-else class="empty-state">
            <span class="material-symbols-rounded empty-icon">history_toggle_off</span>
            <p>暂无备份记录</p>
            <p class="empty-hint">保存配置时将自动创建备份</p>
          </div>
        </div>
      </div>
    </div>

    <!-- Toast 通知 -->
    <Transition name="toast">
      <div v-if="toast.show" class="m3-snackbar" :class="toast.type">
        <span class="material-symbols-rounded">
          {{ toast.type === 'success' ? 'check_circle' : 'error' }}
        </span>
        {{ toast.message }}
      </div>
    </Transition>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useThemeStore } from '@/stores/theme'
import { VueMonacoEditor } from '@guolao/vue-monaco-editor'
import { SchemaFieldEditor } from '@/components/config/plugin-schema'
import { 
  getConfigList,
  getConfigContent,
  getConfigSchema,
  saveConfig, 
  updateConfig,
  getConfigBackups, 
  restoreConfigBackup 
} from '@/api'
import {
  getPluginSchema,
  updatePluginConfig as updateSchemaConfig,
  type SchemaField,
} from '@/api/pluginConfigApi'
import type { 
  ConfigFileInfo, 
  ConfigSection, 
  ConfigSchemaField 
} from '@/api'

// 合并后的配置节类型
interface MergedSection {
  name: string
  display_name: string
  description?: string
  icon?: string
  hasSchema: boolean
  fields: ConfigSchemaField[]  // 传统字段
  schemaFields?: SchemaField[] // Schema 字段
}

const route = useRoute()
const router = useRouter()
const themeStore = useThemeStore()

// 路由参数
const decodedPath = computed(() => decodeURIComponent(route.params.path as string))

// 状态
const editorMode = ref<'visual' | 'source'>('visual')
const loading = ref(false)
const saving = ref(false)
const loadError = ref('')
const configInfo = ref<ConfigFileInfo | null>(null)
const activeSection = ref(0)

// 数据
const originalParsed = ref<any>({})
const editedValues = ref<any>({})
const sourceContent = ref('')
const originalSource = ref('')
const configSchema = ref<ConfigSection[]>([])

// Schema 增强模式
const hasPluginSchema = ref(false)
const pluginName = ref('')
const pluginSchema = ref<Record<string, SchemaField[]>>({})

// 备份
const showBackupsModal = ref(false)
const backupsLoading = ref(false)
const backups = ref<any[]>([])

// 导航标签滚动
const navTabsRef = ref<HTMLElement | null>(null)

// Toast
const toast = ref({ 
  show: false, 
  message: '', 
  type: 'success' as 'success' | 'error' 
})

const isDarkMode = computed(() => themeStore.isDark)

// Monaco 配置
const monacoOptions = {
  minimap: { enabled: false },
  fontSize: 14,
  lineHeight: 24,
  fontFamily: "'JetBrains Mono', 'Fira Code', Consolas, monospace",
  scrollBeyondLastLine: false,
  automaticLayout: true,
  padding: { top: 16, bottom: 16 },
  wordWrap: 'on' as const,
  tabSize: 2
}

// 合并后的配置节列表（Schema 优先，传统兜底）
const mergedSections = computed<MergedSection[]>(() => {
  const sections: MergedSection[] = []
  const processedNames = new Set<string>()

  // 首先处理 Schema 定义的配置节
  if (hasPluginSchema.value && Object.keys(pluginSchema.value).length > 0) {
    for (const [sectionName, schemaFields] of Object.entries(pluginSchema.value)) {
      processedNames.add(sectionName)
      sections.push({
        name: sectionName,
        display_name: formatSectionName(sectionName),
        icon: getSectionIcon(sectionName),
        hasSchema: true,
        fields: [],
        schemaFields: schemaFields,
      })
    }
  }

  // 然后处理传统配置节（未被 Schema 覆盖的）
  for (const section of configSchema.value) {
    if (!processedNames.has(section.name)) {
      sections.push({
        name: section.name,
        display_name: section.display_name,
        hasSchema: false,
        fields: section.fields,
      })
    }
  }

  return sections
})

// 当前合并配置节
const currentMergedSection = computed<MergedSection | null>(() => {
  if (mergedSections.value.length > 0 && activeSection.value < mergedSections.value.length) {
    return mergedSections.value[activeSection.value] ?? null
  }
  return null
})

// 扁平化配置值（用于条件判断）
const flatConfigValues = computed(() => {
  const flat: Record<string, unknown> = {}
  for (const [sectionName, sectionValues] of Object.entries(editedValues.value)) {
    if (typeof sectionValues === 'object' && sectionValues !== null) {
      for (const [key, value] of Object.entries(sectionValues)) {
        flat[key] = value
        flat[`${sectionName}.${key}`] = value
      }
    }
  }
  return flat
})

// 是否有变更
const hasChanges = computed(() => {
  if (editorMode.value === 'source') {
    return sourceContent.value !== originalSource.value
  } else {
    // 混合模式：统一使用 editedValues 检测变更
    return JSON.stringify(editedValues.value) !== JSON.stringify(originalParsed.value)
  }
})

// 初始化
onMounted(() => {
  loadConfig()
})

function goBack() {
  if (hasChanges.value) {
    if (confirm('有未保存的修改，确定要离开吗？')) {
      router.back()
    }
  } else {
    router.back()
  }
}

// 处理导航标签横向滚动（无需按住 Shift）
function handleNavTabsWheel(e: WheelEvent) {
  if (!navTabsRef.value) return
  
  // 只在有垂直滚动时转换为横向滚动
  if (Math.abs(e.deltaY) > Math.abs(e.deltaX)) {
    e.preventDefault()
    // 直接修改 scrollLeft，配合 CSS scroll-behavior 实现平滑效果
    navTabsRef.value.scrollLeft += e.deltaY * 0.3
  }
}

// 切换编辑模式
function switchMode(mode: 'visual' | 'source') {
  if (hasChanges.value && editorMode.value !== mode) {
    if (!confirm('切换模式将丢失未保存的修改，是否继续？')) {
      return
    }
  }
  editorMode.value = mode
  if (mode === 'visual') {
    // 从源码模式切回可视化，需要重新解析
    loadConfig()
  }
}

// 加载配置
async function loadConfig() {
  loading.value = true
  loadError.value = ''
  try {
    // 并行加载配置列表（获取display_name）和配置内容
    const [listRes, contentRes] = await Promise.all([
      getConfigList(),
      getConfigContent(decodedPath.value)
    ])
    
    // 从配置列表中找到当前文件的信息
    if (listRes.data?.configs) {
      const config = listRes.data.configs.find((c: ConfigFileInfo) => c.path === decodedPath.value)
      if (config) {
        configInfo.value = config
      }
    }
    
    // 处理配置内容
    console.log(contentRes)
    if (contentRes.data?.success && contentRes.data?.parsed) {
      originalParsed.value = contentRes.data.parsed
      editedValues.value = JSON.parse(JSON.stringify(contentRes.data.parsed))
      sourceContent.value = contentRes.data.content || ''
      originalSource.value = contentRes.data.content || ''
      
      // 检测是否是插件配置并尝试加载 Schema
      await checkPluginSchema()
      
      // 始终加载传统配置模式（用于没有 Schema 的配置节）
      await loadConfigSchema()
    } else {
      // 显示详细错误信息
      loadError.value = contentRes.data?.error || contentRes.error || '加载配置失败'
    }
  } catch (e: any) {
    loadError.value = e.message || '网络请求失败'
    console.error('加载配置失败:', e)
  } finally {
    loading.value = false
  }
}

// 检测插件 Schema
async function checkPluginSchema() {
  // 从路径提取插件名称 (格式: plugins/{plugin_name}/config.toml)
  const pathMatch = decodedPath.value.match(/plugins[\/\\]([^\/\\]+)[\/\\]config\.toml$/i)
  
  if (!pathMatch || !pathMatch[1]) {
    hasPluginSchema.value = false
    pluginSchema.value = {}
    return
  }
  
  pluginName.value = pathMatch[1]
  
  try {
    const schemaRes = await getPluginSchema(pluginName.value)
    if (schemaRes.success && schemaRes.data?.schema && Object.keys(schemaRes.data.schema).length > 0) {
      hasPluginSchema.value = true
      pluginSchema.value = schemaRes.data.schema
    } else {
      hasPluginSchema.value = false
      pluginSchema.value = {}
    }
  } catch (e) {
    hasPluginSchema.value = false
    pluginSchema.value = {}
  }
}

// 加载配置模式
async function loadConfigSchema() {
  try {
    const res = await getConfigSchema(decodedPath.value)
    
    if (res.data?.success && res.data?.sections) {
      configSchema.value = res.data.sections
    } else {
      console.error('加载配置模式失败:', res.error)
      // 如果加载模式失败，尝试生成简单的模式
      generateFallbackSchema(originalParsed.value)
    }
  } catch (e) {
    console.error('加载配置模式失败:', e)
    generateFallbackSchema(originalParsed.value)
  }
}

// 生成备用的简单 Schema（当后端接口失败时）
function generateFallbackSchema(data: any) {
  const schema: ConfigSection[] = []
  
  for (const sectionKey in data) {
    const section = data[sectionKey]
    const fields: ConfigSchemaField[] = []
    
    if (typeof section === 'object' && !Array.isArray(section)) {
      for (const key in section) {
        const value = section[key]
        let type = 'string'
        
        if (typeof value === 'boolean') type = 'boolean'
        else if (typeof value === 'number') {
          type = Number.isInteger(value) ? 'integer' : 'number'
        }
        else if (Array.isArray(value)) {
          if (value.length > 0 && typeof value[0] === 'object') {
            type = 'array_of_objects'
          } else {
            type = 'array'
          }
        }
        
        fields.push({
          key,
          full_key: `${sectionKey}.${key}`,
          type,
          value,
          description: undefined
        })
      }
    }
    
    schema.push({
      name: sectionKey,
      display_name: sectionKey.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase()),
      fields
    })
  }
  
  configSchema.value = schema
}

// 获取字段值
function getFieldValue(fullKey: string): any {
  const keys = fullKey.split('.')
  let value: any = editedValues.value
  
  for (const key of keys) {
    if (value && typeof value === 'object' && key in value) {
      value = value[key]
    } else {
      return undefined
    }
  }
  
  return value
}

// 更新字段值
function updateFieldValue(fullKey: string, value: any) {
  const keys = fullKey.split('.')
  let current: any = editedValues.value
  
  // 遍历到倒数第二层
  for (let i = 0; i < keys.length - 1; i++) {
    const key = keys[i]
    if (!key) continue
    if (!current[key] || typeof current[key] !== 'object') {
      current[key] = {}
    }
    current = current[key]
  }
  
  // 设置最终值
  const lastKey = keys[keys.length - 1]
  if (current && lastKey) {
    current[lastKey] = value
  }
}

// 数组值处理
function formatArrayValue(val: any): string {
  if (Array.isArray(val)) {
    return val.map(v => String(v)).join('\n')
  }
  return String(val || '')
}

function updateArrayValue(fullKey: string, val: string) {
  const lines = val.split('\n').map(s => s.trim()).filter(s => s)
  updateFieldValue(fullKey, lines)
}

// 解析数字
function parseNumber(val: string, type: string): number {
  const num = type === 'integer' ? parseInt(val) : parseFloat(val)
  return isNaN(num) ? 0 : num
}

// 获取 Schema 字段值
function getSchemaFieldValue(sectionName: string, key: string): unknown {
  return editedValues.value[sectionName]?.[key]
}

// 更新 Schema 字段值
function updateSchemaFieldValue(sectionName: string, key: string, value: unknown) {
  if (!editedValues.value[sectionName]) {
    editedValues.value[sectionName] = {}
  }
  editedValues.value[sectionName][key] = value
}

// 检查 Schema 字段是否应该显示
function checkSchemaFieldVisibility(field: SchemaField): boolean {
  if (!field.depends_on) return true
  
  const dependValue = flatConfigValues.value[field.depends_on]
  
  if (field.depends_value !== undefined) {
    return dependValue === field.depends_value
  }
  
  return Boolean(dependValue)
}

// 格式化配置节名称
function formatSectionName(name: string): string {
  return name.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())
}

// 保存配置
async function saveCurrentConfig() {
  if (saving.value) return
  
  saving.value = true
  try {
    let res
    if (editorMode.value === 'source') {
      // 源码模式：保存原始TOML
      res = await saveConfig(decodedPath.value, sourceContent.value, true)
    } else if (hasPluginSchema.value && pluginName.value) {
      // 混合模式：使用插件专用 API 保存
      res = await updateSchemaConfig(pluginName.value, editedValues.value, true)
    } else {
      // 传统可视化模式：发送更新
      res = await updateConfig(decodedPath.value, editedValues.value, true)
    }

    if (res.success) {
      showToast('配置已保存', 'success')
      if (res.data?.backup_path) {
        console.log('备份已创建:', res.data.backup_path)
      }
      // 重新加载配置
      await loadConfig()
    } else {
      showToast(res.error || '保存失败', 'error')
    }
  } catch (e: any) {
    showToast(e.message || '保存请求失败', 'error')
    console.error('保存失败:', e)
  } finally {
    saving.value = false
  }
}

// 格式化源码
function formatSource() {
  // TOML格式化比较复杂，这里简单处理
  showToast('TOML格式化功能开发中', 'error')
}

// 验证源码
async function validateSource() {
  try {
    // 尝试解析TOML
    const toml = await import('toml')
    toml.parse(sourceContent.value)
    showToast('TOML格式验证通过', 'success')
  } catch (e: any) {
    showToast(`TOML格式错误: ${e.message}`, 'error')
  }
}

function onEditorMount(_editor: any) {
  console.log('Monaco编辑器已加载')
}

// 展开数组字段到源码模式
function expandArrayField(_field: ConfigSchemaField) {
  editorMode.value = 'source'
  showToast('已切换到源码模式，可以编辑复杂数组对象', 'success')
}

// 备份相关
watch(showBackupsModal, (val) => {
  if (val) fetchBackups()
})

async function fetchBackups() {
  backupsLoading.value = true
  try {
    const res = await getConfigBackups(decodedPath.value)
    if (res.success && res.data?.backups) {
      backups.value = res.data.backups
    }
  } catch (e) {
    console.error('获取备份列表失败:', e)
  } finally {
    backupsLoading.value = false
  }
}

async function restoreBackup(backup: any) {
  if (!confirm(`确定要还原到备份版本 "${backup.name}" 吗？当前配置将被覆盖。`)) {
    return
  }
  
  try {
    const res = await restoreConfigBackup(decodedPath.value, backup.name)
    if (res.success) {
      showToast('配置已从备份还原', 'success')
      closeBackupsModal()
      await loadConfig()
    } else {
      showToast(res.error || '还原失败', 'error')
    }
  } catch (e: any) {
    showToast(e.message || '还原请求失败', 'error')
  }
}

function closeBackupsModal() {
  showBackupsModal.value = false
}

// 工具函数
function formatSize(bytes: number): string {
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
  return (bytes / (1024 * 1024)).toFixed(1) + ' MB'
}

function showToast(msg: string, type: 'success' | 'error' = 'success') {
  toast.value = { show: true, message: msg, type }
  setTimeout(() => {
    toast.value.show = false
  }, 3000)
}

function getTypeLabel(type: string): string {
  const labels: Record<string, string> = {
    'string': '文本',
    'integer': '整数',
    'number': '数字',
    'boolean': '开关',
    'array': '列表',
    'array_of_objects': '对象数组',
    'object': '对象'
  }
  return labels[type] || type
}

function getSectionIcon(sectionName: string): string {
  const icons: Record<string, string> = {
    'database': 'database',
    'api_providers': 'cloud',
    'personality': 'psychology',
    'permission': 'lock',
    'feature': 'toggle_on',
    'bot': 'smart_toy',
    'system': 'settings',
    'ui': 'palette'
  }
  
  // 匹配关键词
  for (const [key, icon] of Object.entries(icons)) {
    if (sectionName.toLowerCase().includes(key)) {
      return icon
    }
  }
  
  return 'folder'
}
</script>

<style scoped>
.plugin-config-view {
  display: flex;
  flex-direction: column;
  height: 100%;
  gap: 16px;
  animation: fadeIn 0.4s cubic-bezier(0.2, 0, 0, 1);
}

@keyframes fadeIn {
  from { 
    opacity: 0; 
    transform: translateY(10px); 
  }
  to { 
    opacity: 1; 
    transform: translateY(0); 
  }
}

/* ==================== Schema 增强模式 ==================== */
.schema-mode {
  position: relative;
}

.schema-mode-banner {
  position: absolute;
  top: 16px;
  right: 16px;
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 14px;
  background: linear-gradient(135deg, var(--md-sys-color-tertiary-container), var(--md-sys-color-secondary-container));
  color: var(--md-sys-color-on-tertiary-container);
  border-radius: 100px;
  font-size: 12px;
  font-weight: 600;
  z-index: 10;
  box-shadow: var(--md-sys-elevation-1);
}

.schema-mode-banner .material-symbols-rounded {
  font-size: 16px;
}

/* ==================== 头部样式 ==================== */
.config-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 24px;
  background: var(--md-sys-color-surface-container);
  border-radius: 28px;
  box-shadow: var(--md-sys-elevation-1);
}

.header-left {
  display: flex;
  align-items: center;
  gap: 16px;
  flex: 1;
  min-width: 0;
}

.header-icon-container {
  width: 56px;
  height: 56px;
  border-radius: 16px;
  background: linear-gradient(135deg, var(--md-sys-color-primary-container), var(--md-sys-color-secondary-container));
  color: var(--md-sys-color-on-primary-container);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.header-icon {
  font-size: 28px;
}

.header-info {
  flex: 1;
  min-width: 0;
}

.header-info h1 {
  font-size: 24px;
  font-weight: 500;
  color: var(--md-sys-color-on-surface);
  margin: 0 0 6px;
}

.config-path {
  font-size: 13px;
  color: var(--md-sys-color-on-surface-variant);
  margin: 0 0 4px;
  font-family: 'Roboto Mono', monospace;
  display: flex;
  align-items: center;
  gap: 6px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.path-icon {
  font-size: 16px;
  flex-shrink: 0;
}

.config-description {
  font-size: 14px;
  color: var(--md-sys-color-on-surface-variant);
  margin: 0;
  line-height: 1.5;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-shrink: 0;
}

/* 分段按钮 */
.m3-segmented-button {
  display: flex;
  border: 1px solid var(--md-sys-color-outline);
  border-radius: 100px;
  overflow: hidden;
  height: 40px;
  background: var(--md-sys-color-surface);
}

.segment {
  background: transparent;
  border: none;
  padding: 0 20px;
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  font-weight: 500;
  color: var(--md-sys-color-on-surface-variant);
  cursor: pointer;
  transition: all 0.2s cubic-bezier(0.2, 0, 0, 1);
  position: relative;
}

.segment:not(:last-child)::after {
  content: '';
  position: absolute;
  right: 0;
  top: 25%;
  height: 50%;
  width: 1px;
  background: var(--md-sys-color-outline);
}

.segment:hover:not(:disabled) {
  background: var(--md-sys-color-surface-container-highest);
}

.segment.active {
  background: var(--md-sys-color-secondary-container);
  color: var(--md-sys-color-on-secondary-container);
}

.segment.active::after {
  display: none;
}

.segment:disabled {
  opacity: 0.38;
  cursor: not-allowed;
}

.segment .material-symbols-rounded {
  font-size: 18px;
}

/* ==================== 编辑器区域 ==================== */
.visual-editor, 
.source-editor {
  flex: 1;
  background: var(--md-sys-color-surface-container-low);
  border-radius: 28px;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  box-shadow: var(--md-sys-elevation-1);
  min-height: 0;
}

/* 配置导航栏 */
.config-nav-bar {
  padding: 16px 24px 0;
  border-bottom: 1px solid var(--md-sys-color-outline-variant);
  background: var(--md-sys-color-surface-container);
}

.nav-tabs {
  display: flex;
  gap: 8px;
  overflow-x: auto;
  overflow-y: hidden;
  scrollbar-width: none; /* Firefox */
  -ms-overflow-style: none; /* IE/Edge */
  padding-bottom: 2px;
}

.nav-tabs::-webkit-scrollbar {
  display: none; /* Chrome/Safari/Opera */
}

.nav-tab {
  background: transparent;
  border: none;
  padding: 12px 16px;
  font-size: 14px;
  font-weight: 500;
  color: var(--md-sys-color-on-surface-variant);
  cursor: pointer;
  position: relative;
  white-space: nowrap;
  display: flex;
  align-items: center;
  gap: 8px;
  border-radius: 12px 12px 0 0;
  transition: all 0.2s cubic-bezier(0.2, 0, 0, 1);
}

.nav-tab .material-symbols-rounded {
  font-size: 18px;
}

.field-badge {
  font-size: 11px;
  padding: 2px 6px;
  border-radius: 100px;
  background: var(--md-sys-color-surface-container-highest);
  color: var(--md-sys-color-on-surface-variant);
}

.nav-tab:hover {
  background: var(--md-sys-color-surface-container-high);
}

.nav-tab.has-schema {
  border-left: 2px solid var(--md-sys-color-tertiary);
}

.schema-badge {
  display: flex;
  align-items: center;
  padding: 2px;
  background: var(--md-sys-color-tertiary-container);
  color: var(--md-sys-color-on-tertiary-container);
  border-radius: 4px;
  margin-left: 4px;
}

.schema-badge .material-symbols-rounded {
  font-size: 12px;
}

.nav-tab.active {
  color: var(--md-sys-color-primary);
  background: var(--md-sys-color-surface-container-low);
}

.nav-tab.active .field-badge {
  background: var(--md-sys-color-primary-container);
  color: var(--md-sys-color-on-primary-container);
}

.nav-tab.active::after {
  content: '';
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  height: 3px;
  background: var(--md-sys-color-primary);
  border-radius: 3px 3px 0 0;
}

/* 配置内容 */
.config-content {
  flex: 1;
  overflow-y: auto;
  padding: 24px;
}

.section-header {
  margin-bottom: 20px;
}

.section-title {
  display: flex;
  align-items: center;
  gap: 12px;
}

.section-title h3 {
  font-size: 20px;
  font-weight: 500;
  color: var(--md-sys-color-on-surface);
  margin: 0;
}

.section-title .section-icon {
  font-size: 24px;
  color: var(--md-sys-color-primary);
}

.section-description {
  font-size: 13px;
  color: var(--md-sys-color-on-surface-variant);
  margin: 8px 0 0;
  line-height: 1.5;
}

.schema-indicator {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 4px 10px;
  background: linear-gradient(135deg, var(--md-sys-color-tertiary-container), var(--md-sys-color-secondary-container));
  color: var(--md-sys-color-on-tertiary-container);
  border-radius: 100px;
  font-size: 11px;
  font-weight: 600;
}

.schema-indicator .material-symbols-rounded {
  font-size: 14px;
}

.section-badge {
  font-size: 12px;
  color: var(--md-sys-color-on-surface-variant);
  background: var(--md-sys-color-surface-container-highest);
  padding: 4px 12px;
  border-radius: 100px;
  font-weight: 500;
}

/* 字段列表 */
.fields-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.field-card {
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 12px;
  transition: all 0.2s cubic-bezier(0.2, 0, 0, 1);
  border: 1px solid transparent;
}

.field-card:hover {
  border-color: var(--md-sys-color-outline-variant);
  box-shadow: var(--md-sys-elevation-1);
}

.field-card.inline-field {
  flex-direction: row;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
}

.field-card.has-description {
  background: linear-gradient(
    to right,
    var(--md-sys-color-surface-container-low),
    var(--md-sys-color-surface-container)
  );
}

.field-left {
  flex: 1;
  min-width: 0;
}

.field-header {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 8px;
}

.field-name {
  font-size: 15px;
  font-weight: 500;
  color: var(--md-sys-color-on-surface);
  font-family: 'Roboto Mono', monospace;
}

.field-type-badge {
  font-size: 11px;
  color: var(--md-sys-color-on-tertiary-container);
  background: var(--md-sys-color-tertiary-container);
  padding: 3px 8px;
  border-radius: 6px;
  text-transform: uppercase;
  font-weight: 600;
  letter-spacing: 0.5px;
}

.field-description {
  font-size: 13px;
  color: var(--md-sys-color-on-surface-variant);
  line-height: 1.6;
  display: flex;
  align-items: flex-start;
  gap: 8px;
  padding: 10px 12px;
  background: var(--md-sys-color-surface-container-highest);
  border-radius: 12px;
  border-left: 3px solid var(--md-sys-color-primary);
}

.field-description.with-margin {
  margin-bottom: 4px;
}

.desc-icon {
  font-size: 18px;
  color: var(--md-sys-color-primary);
  flex-shrink: 0;
  margin-top: 1px;
}

.field-input-container {
  width: 100%;
}

.m3-input {
  width: 100%;
  padding: 12px 16px;
  border: 1px solid var(--md-sys-color-outline);
  border-radius: 12px;
  background: var(--md-sys-color-surface);
  color: var(--md-sys-color-on-surface);
  font-size: 14px;
  font-family: inherit;
  transition: all 0.2s cubic-bezier(0.2, 0, 0, 1);
}

.m3-input:focus {
  outline: none;
  border-color: var(--md-sys-color-primary);
  box-shadow: 0 0 0 3px var(--md-sys-color-primary-container);
}

.m3-input::placeholder {
  color: var(--md-sys-color-on-surface-variant);
  opacity: 0.6;
}

/* 数组输入 */
.array-input-wrapper {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.array-textarea {
  min-height: 120px;
  resize: vertical;
  font-family: 'JetBrains Mono', monospace;
  line-height: 1.6;
}

.input-hint {
  font-size: 12px;
  color: var(--md-sys-color-on-surface-variant);
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 0 4px;
}

.input-hint .material-symbols-rounded {
  font-size: 16px;
}

/* 数组对象容器 */
.array-objects-container {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px;
  background: var(--md-sys-color-surface-container-high);
  border-radius: 12px;
  border: 1px dashed var(--md-sys-color-outline);
}

.array-objects-info {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  color: var(--md-sys-color-on-surface-variant);
}

.array-objects-info .material-symbols-rounded {
  font-size: 20px;
  color: var(--md-sys-color-primary);
}

/* Switch 开关 */
.m3-switch {
  display: inline-block;
  cursor: pointer;
  flex-shrink: 0;
}

.m3-switch input {
  display: none;
}

.m3-switch-track {
  position: relative;
  display: block;
  width: 52px;
  height: 32px;
  background: var(--md-sys-color-surface-container-highest);
  border: 2px solid var(--md-sys-color-outline);
  border-radius: 16px;
  transition: all 0.2s cubic-bezier(0.2, 0, 0, 1);
}

.m3-switch-thumb {
  position: absolute;
  top: 50%;
  left: 4px;
  width: 20px;
  height: 20px;
  background: var(--md-sys-color-outline);
  border-radius: 50%;
  transform: translateY(-50%);
  transition: all 0.2s cubic-bezier(0.2, 0, 0, 1);
}

.m3-switch input:checked + .m3-switch-track {
  background: var(--md-sys-color-primary);
  border-color: var(--md-sys-color-primary);
}

.m3-switch input:checked + .m3-switch-track .m3-switch-thumb {
  transform: translate(20px, -50%);
  background: var(--md-sys-color-on-primary);
}

/* ==================== 源码编辑器 ==================== */
.source-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 24px;
  background: var(--md-sys-color-surface-container);
  border-bottom: 1px solid var(--md-sys-color-outline-variant);
}

.toolbar-left {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 13px;
  color: var(--md-sys-color-on-surface-variant);
}

.file-path {
  font-family: 'Roboto Mono', 'Noto Sans SC', monospace;
}

.toolbar-left .material-symbols-rounded {
  font-size: 20px;
}

.toolbar-actions {
  display: flex;
  gap: 8px;
}

.monaco-container {
  flex: 1;
  min-height: 0;
}

/* ==================== 状态展示 ==================== */
.loading-state, 
.error-state, 
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 300px;
  gap: 16px;
  color: var(--md-sys-color-on-surface-variant);
  padding: 48px 24px;
}

.loading-state .material-symbols-rounded,
.error-state .material-symbols-rounded,
.empty-icon {
  font-size: 64px;
  opacity: 0.5;
}

.error-icon {
  color: var(--md-sys-color-error);
}

.loading-state p,
.error-state p,
.empty-state p {
  font-size: 16px;
  margin: 0;
}

.empty-hint {
  font-size: 14px;
  opacity: 0.7;
}

.spinning {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

/* ==================== 对话框 ==================== */
.m3-dialog-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.4);
  backdrop-filter: blur(4px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  padding: 24px;
  animation: fadeIn 0.2s ease;
}

.m3-dialog {
  background: var(--md-sys-color-surface-container-high);
  border-radius: 28px;
  width: 100%;
  max-width: 600px;
  max-height: 80vh;
  display: flex;
  flex-direction: column;
  box-shadow: var(--md-sys-elevation-3);
  animation: slideUp 0.3s cubic-bezier(0.2, 0, 0, 1);
}

@keyframes slideUp {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.dialog-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 24px;
  border-bottom: 1px solid var(--md-sys-color-outline-variant);
}

.dialog-title {
  display: flex;
  align-items: center;
  gap: 12px;
}

.dialog-title .material-symbols-rounded {
  font-size: 24px;
  color: var(--md-sys-color-primary);
}

.dialog-title h3 {
  font-size: 20px;
  font-weight: 500;
  color: var(--md-sys-color-on-surface);
  margin: 0;
}

.dialog-content {
  flex: 1;
  overflow-y: auto;
  padding: 24px;
}

/* 备份列表 */
.backup-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.backup-item {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 16px;
  background: var(--md-sys-color-surface-container);
  border-radius: 16px;
  transition: all 0.2s cubic-bezier(0.2, 0, 0, 1);
}

.backup-item:hover {
  background: var(--md-sys-color-surface-container-highest);
  box-shadow: var(--md-sys-elevation-1);
}

.backup-icon {
  width: 40px;
  height: 40px;
  border-radius: 12px;
  background: var(--md-sys-color-primary-container);
  color: var(--md-sys-color-on-primary-container);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.backup-icon .material-symbols-rounded {
  font-size: 20px;
}

.backup-info {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.backup-name {
  font-size: 14px;
  font-weight: 500;
  color: var(--md-sys-color-on-surface);
  font-family: 'JetBrains Mono', monospace;
}

.backup-meta {
  font-size: 12px;
  color: var(--md-sys-color-on-surface-variant);
  display: flex;
  align-items: center;
  gap: 6px;
}

.meta-icon {
  font-size: 14px;
}

.separator {
  opacity: 0.5;
}

.backup-actions {
  flex-shrink: 0;
}

/* ==================== Snackbar ==================== */
.m3-snackbar {
  position: fixed;
  bottom: 24px;
  left: 50%;
  transform: translateX(-50%);
  background: var(--md-sys-color-inverse-surface);
  color: var(--md-sys-color-inverse-on-surface);
  padding: 16px 24px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  gap: 12px;
  box-shadow: var(--md-sys-elevation-3);
  z-index: 2000;
  min-width: 300px;
  font-size: 14px;
  font-weight: 500;
}

.m3-snackbar.error {
  background: var(--md-sys-color-error);
  color: var(--md-sys-color-on-error);
}

.m3-snackbar .material-symbols-rounded {
  font-size: 20px;
}

.toast-enter-active,
.toast-leave-active {
  transition: all 0.3s cubic-bezier(0.2, 0, 0, 1);
}

.toast-enter-from,
.toast-leave-to {
  opacity: 0;
  transform: translate(-50%, 20px);
}

/* ==================== 按钮样式 ==================== */
.m3-icon-button {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  border: none;
  background: transparent;
  color: var(--md-sys-color-on-surface-variant);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.2s cubic-bezier(0.2, 0, 0, 1);
}

.m3-icon-button:hover:not(:disabled) {
  background: var(--md-sys-color-surface-container-highest);
}

.m3-icon-button:disabled {
  opacity: 0.38;
  cursor: not-allowed;
}

.m3-icon-button .material-symbols-rounded {
  font-size: 24px;
}

.m3-button {
  padding: 10px 24px;
  border-radius: 100px;
  border: none;
  font-size: 14px;
  font-weight: 500;
  display: inline-flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  transition: all 0.2s cubic-bezier(0.2, 0, 0, 1);
  font-family: inherit;
}

.m3-button.filled {
  background: var(--md-sys-color-primary);
  color: var(--md-sys-color-on-primary);
}

.m3-button.filled:hover:not(:disabled) {
  box-shadow: var(--md-sys-elevation-1);
}

.m3-button.text {
  background: transparent;
  color: var(--md-sys-color-primary);
}

.m3-button.text:hover:not(:disabled) {
  background: var(--md-sys-color-primary-container);
}

.m3-button:disabled {
  opacity: 0.38;
  cursor: not-allowed;
}

.m3-button.small {
  padding: 6px 16px;
  font-size: 13px;
}

.m3-button .material-symbols-rounded {
  font-size: 18px;
}

/* ==================== 卡片样式 ==================== */
.m3-card {
  background: var(--md-sys-color-surface-container);
  border-radius: 16px;
  box-shadow: var(--md-sys-elevation-0);
}

/* ==================== 响应式 ==================== */
@media (max-width: 768px) {
  .config-header {
    flex-direction: column;
    align-items: stretch;
    gap: 16px;
  }
  
  .header-actions {
    justify-content: space-between;
  }
  
  .field-card.inline-field {
    flex-direction: column;
  }
  
  .m3-switch {
    align-self: flex-start;
  }
}
</style>
