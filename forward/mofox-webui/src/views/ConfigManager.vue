<!--
  @file ConfigManager.vue
  @description 统一配置管理器
  
  功能说明：
  1. 集中管理所有配置文件（核心配置 + 插件配置）
  2. 左侧显示配置文件列表，右侧显示编辑器
  3. 支持可视化编辑和源码编辑
  4. 根据配置类型自动选择合适的编辑器组件
  
  配置分类：
  - 核心配置：主配置(main)、模型配置(model)
  - 插件配置：各插件的配置文件
  
  编辑器组件：
  - MainConfigEditor: 主配置专用
  - ModelConfigEditor: 模型配置专用
  - 通用编辑器: 其他配置
-->
<template>
  <div class="config-manager">
    <!-- 配置文件列表侧边栏：分类显示所有配置 -->
    <aside class="config-sidebar">
      <div class="sidebar-header">
        <h3>
          <span class="material-symbols-rounded">settings_suggest</span>
          配置管理
        </h3>
        <button class="m3-icon-button" @click="refreshConfigList" :disabled="loading" title="刷新">
          <span class="material-symbols-rounded" :class="{ spinning: loading }">refresh</span>
        </button>
      </div>
      
      <!-- 分类区域 -->
      <div class="config-categories">
        <!-- 核心配置 -->
        <div class="category-section">
          <div class="category-title">
            <span class="material-symbols-rounded">star</span>
            核心配置
          </div>
          <div 
            v-for="config in coreConfigs" 
            :key="config.path"
            :class="['config-item', { active: selectedConfig?.path === config.path }]"
            @click="selectConfig(config)"
          >
            <div class="config-item-icon" :class="config.type">
              <span class="material-symbols-rounded">{{ getConfigIcon(config.type) }}</span>
            </div>
            <div class="config-item-info">
              <span class="config-name">{{ config.display_name }}</span>
              <span class="config-desc">{{ getConfigDescription(config) }}</span>
            </div>
          </div>
        </div>

        <!-- 插件配置 -->
        <div class="category-section" v-if="pluginConfigs.length > 0">
          <div class="category-title">
            <span class="material-symbols-rounded">extension</span>
            插件配置
            <span class="count">{{ pluginConfigs.length }}</span>
          </div>
          <div class="plugin-config-list">
            <div 
              v-for="config in pluginConfigs" 
              :key="config.path"
              :class="['config-item compact', { active: selectedConfig?.path === config.path }]"
              @click="selectConfig(config)"
            >
              <div class="config-item-icon plugin">
                <span class="material-symbols-rounded">extension</span>
              </div>
              <div class="config-item-info">
                <span class="config-name">{{ config.display_name }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </aside>

    <!-- 配置编辑区 -->
    <main class="config-editor-area">
      <div v-if="!selectedConfig" class="no-selection">
        <span class="material-symbols-rounded empty-icon">settings_applications</span>
        <h3>选择配置文件开始编辑</h3>
        <p>从左侧选择一个配置文件，可以进行可视化编辑或源码编辑</p>
      </div>
      
      <template v-else>
        <!-- 编辑器头部 -->
        <div class="editor-header">
          <div class="editor-title">
            <span class="material-symbols-rounded header-icon">{{ getConfigIcon(selectedConfig.type) }}</span>
            <h2>{{ selectedConfig.display_name }}</h2>
            <span class="m3-assist-chip" :class="selectedConfig.type">
              {{ getConfigTypeLabel(selectedConfig.type) }}
            </span>
          </div>
          <div class="editor-controls">
            <div class="m3-segmented-button">
              <button 
                :class="['segment', { selected: editorMode === 'visual' }]"
                @click="editorMode = 'visual'"
              >
                <span class="material-symbols-rounded">grid_view</span>
                可视化
              </button>
              <button 
                :class="['segment', { selected: editorMode === 'source' }]"
                @click="editorMode = 'source'"
              >
                <span class="material-symbols-rounded">code</span>
                源码
              </button>
            </div>
            <div class="editor-actions">
              <button class="m3-button text" @click="showBackupsModal = true">
                <span class="material-symbols-rounded">history</span>
                备份
              </button>
              <button 
                class="m3-button filled" 
                @click="saveCurrentConfig" 
                :disabled="saving || !hasChanges"
              >
                <span class="material-symbols-rounded" :class="{ spinning: saving }">
                  {{ saving ? 'progress_activity' : 'save' }}
                </span>
                {{ saving ? '保存中...' : '保存配置' }}
              </button>
            </div>
          </div>
        </div>

        <!-- 可视化编辑模式 -->
        <div v-if="editorMode === 'visual'" class="visual-editor">
          <div v-if="schemaLoading" class="loading-state">
            <span class="material-symbols-rounded spinning loading-icon">progress_activity</span>
            加载配置结构...
          </div>
          <div v-else-if="schemaError" class="error-state">
            <span class="material-symbols-rounded error-icon">error</span>
            {{ schemaError }}
          </div>
          
          <!-- 模型配置专用界面 -->
          <template v-else-if="selectedConfig.type === 'model'">
            <ModelConfigEditor 
              :parsed-data="originalParsed"
              :edited-values="editedValues"
              @update="updateFieldValue"
            />
          </template>
          
          <!-- 主配置专用界面 -->
          <template v-else-if="selectedConfig.type === 'main'">
            <MainConfigEditor 
              :parsed-data="originalParsed"
              :edited-values="editedValues"
              :config-schema="configSchema"
              @update="updateFieldValue"
            />
          </template>
          
          <!-- 通用插件配置界面 -->
          <template v-else>
            <div class="fields-grid">
              <div 
                v-for="section in configSchema" 
                :key="section.name" 
                class="m3-card config-section"
              >
                <div class="section-header">
                  <h3>{{ section.display_name }}</h3>
                  <span class="field-count">{{ section.fields.length }} 项配置</span>
                </div>
                <div class="section-content">
                  <div 
                    v-for="field in section.fields" 
                    :key="field.full_key" 
                    class="field-item"
                  >
                    <div class="field-header">
                      <span class="field-name">{{ field.key }}</span>
                      <span class="field-type">{{ field.type }}</span>
                    </div>
                    <div v-if="field.description" class="field-description">
                      {{ field.description }}
                    </div>
                    <div class="field-input">
                      <FieldEditor 
                        :field="field"
                        :value="getFieldValue(field.full_key)"
                        @update="(v: unknown) => updateFieldValue(field.full_key, v)"
                      />
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </template>
        </div>

        <!-- 源码编辑模式 (Monaco Editor) -->
        <div v-else class="source-editor">
          <div class="source-toolbar">
            <span class="file-path">
              <span class="material-symbols-rounded">description</span>
              {{ selectedConfig.path }}
            </span>
            <div class="toolbar-actions">
              <button class="m3-button text small" @click="formatSource">
                <span class="material-symbols-rounded">format_align_left</span>
                格式化
              </button>
            </div>
          </div>
          <div class="monaco-container">
            <vue-monaco-editor
              v-model:value="sourceContent"
              :language="getEditorLanguage(selectedConfig.path)"
              :theme="isDarkMode ? 'vs-dark' : 'vs'"
              :options="monacoOptions"
              @mount="onEditorMount"
            />
          </div>
          <div v-if="validationError" class="validation-error">
            <span class="material-symbols-rounded">warning</span>
            {{ validationError }}
          </div>
        </div>
      </template>
    </main>

    <!-- 备份管理弹窗 -->
    <Transition name="dialog">
      <div v-if="showBackupsModal" class="m3-dialog-overlay" @click.self="showBackupsModal = false">
        <div class="m3-dialog large">
          <div class="dialog-header">
            <h3>
              <span class="material-symbols-rounded">history</span>
              备份管理
            </h3>
            <button class="m3-icon-button" @click="showBackupsModal = false">
              <span class="material-symbols-rounded">close</span>
            </button>
          </div>
          <div class="dialog-body">
            <div v-if="backupsLoading" class="loading-state">
              <span class="material-symbols-rounded spinning loading-icon">progress_activity</span>
              加载备份列表...
            </div>
            <div v-else-if="backups.length === 0" class="empty-state">
              <span class="material-symbols-rounded empty-icon">history_toggle_off</span>
              暂无备份
            </div>
            <div v-else class="backup-list">
              <div v-for="backup in backups" :key="backup.name" class="backup-item">
                <div class="backup-info">
                  <span class="backup-name">{{ backup.name }}</span>
                  <span class="backup-meta">
                    {{ backup.created_at }} · {{ formatSize(backup.size) }}
                  </span>
                </div>
                <button 
                  class="m3-button text" 
                  @click="restoreBackup(backup.name)"
                  :disabled="restoringBackup === backup.name"
                >
                  <span class="material-symbols-rounded" :class="{ spinning: restoringBackup === backup.name }">
                    {{ restoringBackup === backup.name ? 'progress_activity' : 'restore' }}
                  </span>
                  恢复
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </Transition>

    <!-- Toast 提示 -->
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
import { ref, computed, onMounted, watch, shallowRef } from 'vue'
import { VueMonacoEditor } from '@guolao/vue-monaco-editor'
import type { editor } from 'monaco-editor'
import {
  getConfigList,
  getConfigContent,
  getConfigSchema,
  saveConfig,
  updateConfig,
  getConfigBackups,
  restoreConfigBackup,
  type ConfigFileInfo,
  type ConfigSection,
  type ConfigBackupInfo
} from '@/api'
import { FieldEditor } from '@/components/config/editors'
import ModelConfigEditor from '@/components/config/ModelConfigEditor.vue'
import MainConfigEditor from '@/components/config/MainConfigEditor.vue'

// Monaco Editor 配置
const monacoOptions: editor.IStandaloneEditorConstructionOptions = {
  minimap: { enabled: true },
  fontSize: 14,
  lineNumbers: 'on',
  roundedSelection: true,
  scrollBeyondLastLine: false,
  automaticLayout: true,
  tabSize: 2,
  wordWrap: 'on',
  folding: true,
  lineDecorationsWidth: 10,
  lineNumbersMinChars: 3,
  renderLineHighlight: 'all',
  scrollbar: {
    verticalScrollbarSize: 10,
    horizontalScrollbarSize: 10
  }
}

// Editor 实例
const editorInstance = shallowRef<editor.IStandaloneCodeEditor | null>(null)

// 状态
const loading = ref(false)
const saving = ref(false)
const schemaLoading = ref(false)
const backupsLoading = ref(false)
const configList = ref<ConfigFileInfo[]>([])
const selectedConfig = ref<ConfigFileInfo | null>(null)
const editorMode = ref<'visual' | 'source'>('visual')
const isDarkMode = ref(true)

// 可视化编辑状态
const configSchema = ref<ConfigSection[]>([])
const schemaError = ref('')
const editedValues = ref<Record<string, unknown>>({})
const originalParsed = ref<Record<string, unknown>>({})

// 源码编辑状态
const sourceContent = ref('')
const originalContent = ref('')
const validationError = ref('')

// 备份相关
const showBackupsModal = ref(false)
const backups = ref<ConfigBackupInfo[]>([])
const restoringBackup = ref('')

// Toast 提示
const toast = ref({ show: false, message: '', type: 'success' as 'success' | 'error' })

// 计算属性
const coreConfigs = computed(() => {
  return configList.value.filter(c => c.type === 'main' || c.type === 'model')
})

const pluginConfigs = computed(() => {
  return configList.value.filter(c => c.type === 'plugin')
})

const hasChanges = computed(() => {
  if (editorMode.value === 'source') {
    return sourceContent.value !== originalContent.value
  }
  return Object.keys(editedValues.value).length > 0
})

// 方法
function getConfigIcon(type: string): string {
  const icons: Record<string, string> = {
    main: 'smart_toy',
    model: 'psychology',
    plugin: 'extension'
  }
  return icons[type] || 'settings_applications'
}

function getConfigTypeLabel(type: string): string {
  const labels: Record<string, string> = {
    main: '机器人配置',
    model: '模型配置',
    plugin: '插件配置'
  }
  return labels[type] || '配置'
}

function getConfigDescription(config: ConfigFileInfo): string {
  if (config.type === 'main') {
    return '机器人基础设置、行为参数'
  } else if (config.type === 'model') {
    return 'AI 模型提供商、API 密钥配置'
  }
  return config.description || ''
}

function getEditorLanguage(path: string): string {
  if (path.endsWith('.toml')) return 'ini'
  if (path.endsWith('.json')) return 'json'
  if (path.endsWith('.yaml') || path.endsWith('.yml')) return 'yaml'
  return 'plaintext'
}

function formatSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / 1024 / 1024).toFixed(1)} MB`
}

function onEditorMount(editor: editor.IStandaloneCodeEditor) {
  editorInstance.value = editor
}

function formatSource() {
  if (editorInstance.value) {
    editorInstance.value.getAction('editor.action.formatDocument')?.run()
  }
}

async function refreshConfigList() {
  loading.value = true
  try {
    const res = await getConfigList()
    if (res.success && res.data) {
      configList.value = res.data.configs
    }
  } catch {
    showToast('加载配置列表失败', 'error')
  } finally {
    loading.value = false
  }
}

async function selectConfig(config: ConfigFileInfo) {
  if (hasChanges.value) {
    if (!confirm('当前有未保存的更改，确定要切换吗？')) {
      return
    }
  }
  
  selectedConfig.value = config
  editedValues.value = {}
  validationError.value = ''
  
  await loadConfigContent(config.path)
  
  if (editorMode.value === 'visual') {
    await loadConfigSchema(config.path)
  }
}

async function loadConfigContent(path: string) {
  try {
    const res = await getConfigContent(path)
    if (res.success && res.data) {
      sourceContent.value = res.data.content || ''
      originalContent.value = res.data.content || ''
      originalParsed.value = res.data.parsed || {}
    } else {
      showToast(res.data?.error || '加载配置失败', 'error')
    }
  } catch {
    showToast('加载配置内容失败', 'error')
  }
}

async function loadConfigSchema(path: string) {
  schemaLoading.value = true
  schemaError.value = ''
  
  try {
    const res = await getConfigSchema(path)
    if (res.success && res.data) {
      if (res.data.success) {
        configSchema.value = res.data.sections
      } else {
        schemaError.value = res.data.error || '加载配置结构失败'
      }
    }
  } catch {
    schemaError.value = '加载配置结构失败'
  } finally {
    schemaLoading.value = false
  }
}

function getFieldValue(fullKey: string): unknown {
  if (fullKey in editedValues.value) {
    return editedValues.value[fullKey]
  }
  
  const keys = fullKey.split('.')
  let current: unknown = originalParsed.value
  for (const key of keys) {
    if (current && typeof current === 'object' && key in (current as Record<string, unknown>)) {
      current = (current as Record<string, unknown>)[key]
    } else {
      return undefined
    }
  }
  return current
}

function updateFieldValue(fullKey: string, value: unknown) {
  editedValues.value[fullKey] = value
}

async function saveCurrentConfig() {
  if (!selectedConfig.value) return
  
  saving.value = true
  try {
    if (editorMode.value === 'source') {
      const res = await saveConfig(selectedConfig.value.path, sourceContent.value)
      if (res.success && res.data?.success) {
        originalContent.value = sourceContent.value
        showToast('配置已保存', 'success')
        await loadConfigContent(selectedConfig.value.path)
      } else {
        showToast(res.data?.error || '保存失败', 'error')
      }
    } else {
      if (Object.keys(editedValues.value).length === 0) {
        showToast('没有需要保存的更改', 'error')
        return
      }
      
      const res = await updateConfig(selectedConfig.value.path, editedValues.value)
      if (res.success && res.data?.success) {
        editedValues.value = {}
        showToast('配置已保存', 'success')
        await loadConfigContent(selectedConfig.value.path)
        await loadConfigSchema(selectedConfig.value.path)
      } else {
        showToast(res.data?.error || '保存失败', 'error')
      }
    }
  } catch {
    showToast('保存配置失败', 'error')
  } finally {
    saving.value = false
  }
}

async function loadBackups() {
  if (!selectedConfig.value) return
  
  backupsLoading.value = true
  try {
    const res = await getConfigBackups(selectedConfig.value.path)
    if (res.success && res.data?.success) {
      backups.value = res.data.backups
    }
  } catch {
    showToast('加载备份列表失败', 'error')
  } finally {
    backupsLoading.value = false
  }
}

async function restoreBackup(backupName: string) {
  if (!selectedConfig.value) return
  
  if (!confirm(`确定要从备份 "${backupName}" 恢复配置吗？当前配置将被覆盖。`)) {
    return
  }
  
  restoringBackup.value = backupName
  try {
    const res = await restoreConfigBackup(selectedConfig.value.path, backupName)
    if (res.success && res.data?.success) {
      showToast('配置已恢复', 'success')
      showBackupsModal.value = false
      await loadConfigContent(selectedConfig.value.path)
      await loadConfigSchema(selectedConfig.value.path)
    } else {
      showToast(res.data?.error || '恢复失败', 'error')
    }
  } catch {
    showToast('恢复备份失败', 'error')
  } finally {
    restoringBackup.value = ''
  }
}

function showToast(message: string, type: 'success' | 'error') {
  toast.value = { show: true, message, type }
  setTimeout(() => {
    toast.value.show = false
  }, 3000)
}

watch(editorMode, async (newMode) => {
  if (selectedConfig.value) {
    if (newMode === 'visual') {
      await loadConfigSchema(selectedConfig.value.path)
    }
  }
})

watch(showBackupsModal, (show) => {
  if (show) {
    loadBackups()
  }
})

onMounted(() => {
  refreshConfigList()
  isDarkMode.value = window.matchMedia('(prefers-color-scheme: dark)').matches
})
</script>

<style scoped>
.config-manager {
  display: flex;
  height: 100%;
  gap: 0;
  animation: fadeIn 0.3s ease;
  background: var(--md-sys-color-surface);
  border-radius: 32px;
  overflow: hidden;
  box-shadow: 0 4px 30px rgba(0, 0, 0, 0.1);
}

@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.spinning {
  animation: spin 1s linear infinite;
}

/* 侧边栏 */
.config-sidebar {
  width: 280px;
  min-width: 280px;
  background: var(--md-sys-color-surface-container-low);
  border-right: 1px solid var(--md-sys-color-outline-variant);
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.sidebar-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px;
  border-bottom: 1px solid var(--md-sys-color-outline-variant);
}

.sidebar-header h3 {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 16px;
  font-weight: 500;
  color: var(--md-sys-color-on-surface);
  margin: 0;
}

.sidebar-header h3 .material-symbols-rounded {
  color: var(--md-sys-color-primary);
}

/* 配置分类 */
.config-categories {
  flex: 1;
  overflow-y: auto;
  padding: 12px;
}

.category-section {
  margin-bottom: 20px;
}

.category-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
  font-weight: 500;
  color: var(--md-sys-color-on-surface-variant);
  text-transform: uppercase;
  letter-spacing: 0.5px;
  padding: 8px 12px;
}

.category-title .count {
  margin-left: auto;
  padding: 2px 8px;
  background: var(--md-sys-color-surface-container-highest);
  border-radius: 12px;
  font-size: 11px;
}

.config-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  border-radius: 12px;
  cursor: pointer;
  transition: all 0.2s;
  margin-bottom: 4px;
}

.config-item:hover {
  background: var(--md-sys-color-surface-container-highest);
}

.config-item.active {
  background: var(--md-sys-color-secondary-container);
  color: var(--md-sys-color-on-secondary-container);
}

.config-item.compact {
  padding: 10px 12px;
}

.config-item-icon {
  width: 36px;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 12px;
  color: var(--md-sys-color-on-primary-container);
  background: var(--md-sys-color-primary-container);
}

.config-item-icon.main {
  background: var(--md-sys-color-primary-container);
  color: var(--md-sys-color-on-primary-container);
}

.config-item-icon.model {
  background: var(--md-sys-color-tertiary-container);
  color: var(--md-sys-color-on-tertiary-container);
}

.config-item-icon.plugin {
  background: var(--md-sys-color-secondary-container);
  color: var(--md-sys-color-on-secondary-container);
}

.config-item-info {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.config-name {
  font-size: 14px;
  font-weight: 500;
  color: var(--md-sys-color-on-surface);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.config-desc {
  font-size: 12px;
  color: var(--md-sys-color-on-surface-variant);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.plugin-config-list {
  max-height: 300px;
  overflow-y: auto;
}

/* 配置编辑区 */
.config-editor-area {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  background: var(--md-sys-color-surface);
}

.no-selection {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 16px;
  color: var(--md-sys-color-on-surface-variant);
}

.no-selection .empty-icon {
  font-size: 64px;
  opacity: 0.3;
}

.no-selection h3 {
  font-size: 18px;
  font-weight: 500;
  margin: 0;
  color: var(--md-sys-color-on-surface);
}

.no-selection p {
  font-size: 14px;
  margin: 0;
}

/* 编辑器头部 */
.editor-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 24px;
  background: var(--md-sys-color-surface);
  border-bottom: 1px solid var(--md-sys-color-outline-variant);
}

.editor-title {
  display: flex;
  align-items: center;
  gap: 12px;
}

.editor-title .header-icon {
  font-size: 24px;
  color: var(--md-sys-color-primary);
}

.editor-title h2 {
  font-size: 18px;
  font-weight: 500;
  color: var(--md-sys-color-on-surface);
  margin: 0;
}

.m3-assist-chip {
  height: 24px;
  padding: 0 8px;
  font-size: 11px;
  border: 1px solid var(--md-sys-color-outline);
  border-radius: 8px;
  display: flex;
  align-items: center;
}

.m3-assist-chip.main {
  background: var(--md-sys-color-primary-container);
  color: var(--md-sys-color-on-primary-container);
  border: none;
}

.m3-assist-chip.model {
  background: var(--md-sys-color-tertiary-container);
  color: var(--md-sys-color-on-tertiary-container);
  border: none;
}

.m3-assist-chip.plugin {
  background: var(--md-sys-color-secondary-container);
  color: var(--md-sys-color-on-secondary-container);
  border: none;
}

.editor-controls {
  display: flex;
  align-items: center;
  gap: 16px;
}

.m3-segmented-button {
  display: flex;
  border: 1px solid var(--md-sys-color-outline);
  border-radius: 20px;
  overflow: hidden;
}

.m3-segmented-button .segment {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 16px;
  border: none;
  background: transparent;
  color: var(--md-sys-color-on-surface-variant);
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  border-right: 1px solid var(--md-sys-color-outline);
}

.m3-segmented-button .segment:last-child {
  border-right: none;
}

.m3-segmented-button .segment.selected {
  background: var(--md-sys-color-secondary-container);
  color: var(--md-sys-color-on-secondary-container);
}

.m3-segmented-button .segment .material-symbols-rounded {
  font-size: 18px;
}

.editor-actions {
  display: flex;
  gap: 8px;
}

/* 可视化编辑器 */
.visual-editor {
  flex: 1;
  overflow-y: auto;
  padding: 24px;
}

.fields-grid {
  display: grid;
  gap: 24px;
}

.config-section {
  padding: 0;
  overflow: hidden;
}

.section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 20px;
  background: var(--md-sys-color-surface-container-low);
  border-bottom: 1px solid var(--md-sys-color-outline-variant);
}

.section-header h3 {
  font-size: 14px;
  font-weight: 500;
  color: var(--md-sys-color-on-surface);
  margin: 0;
}

.field-count {
  font-size: 12px;
  color: var(--md-sys-color-on-surface-variant);
}

.section-content {
  padding: 20px;
  display: grid;
  gap: 20px;
}

.field-item {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.field-header {
  display: flex;
  align-items: center;
  gap: 8px;
}

.field-name {
  font-size: 14px;
  font-weight: 500;
  color: var(--md-sys-color-on-surface);
}

.field-type {
  font-size: 11px;
  padding: 2px 8px;
  background: var(--md-sys-color-surface-container-highest);
  border-radius: 4px;
  color: var(--md-sys-color-on-surface-variant);
}

.field-description {
  font-size: 12px;
  color: var(--md-sys-color-on-surface-variant);
  line-height: 1.5;
}

.field-input {
  margin-top: 4px;
}

/* 源码编辑器 */
.source-editor {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.source-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 20px;
  background: var(--md-sys-color-surface);
  border-bottom: 1px solid var(--md-sys-color-outline-variant);
}

.file-path {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  font-family: 'Roboto Mono', 'Noto Sans SC', monospace;
  color: var(--md-sys-color-on-surface-variant);
}

.toolbar-actions {
  display: flex;
  gap: 8px;
}

.monaco-container {
  flex: 1;
  min-height: 0;
}

.validation-error {
  padding: 12px 20px;
  background: var(--md-sys-color-error-container);
  color: var(--md-sys-color-on-error-container);
  font-size: 13px;
  display: flex;
  align-items: center;
  gap: 8px;
}

/* 弹窗样式 */
.m3-dialog-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.32);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  backdrop-filter: blur(2px);
}

.m3-dialog {
  background: var(--md-sys-color-surface-container-high);
  border-radius: 28px;
  padding: 24px;
  width: 90%;
  max-width: 320px;
  box-shadow: var(--md-sys-elevation-3);
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.m3-dialog.large {
  max-width: 500px;
  max-height: 80vh;
}

.dialog-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.dialog-header h3 {
  display: flex;
  align-items: center;
  gap: 8px;
  margin: 0;
  font-size: 20px;
  font-weight: 400;
  color: var(--md-sys-color-on-surface);
}

.dialog-body {
  overflow-y: auto;
  flex: 1;
}

/* 备份列表 */
.backup-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.backup-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px;
  background: var(--md-sys-color-surface-container-highest);
  border-radius: 12px;
}

.backup-info {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.backup-name {
  font-size: 14px;
  font-weight: 500;
  color: var(--md-sys-color-on-surface);
}

.backup-meta {
  font-size: 12px;
  color: var(--md-sys-color-on-surface-variant);
}

/* 加载和空状态 */
.loading-state,
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 12px;
  padding: 60px;
  color: var(--md-sys-color-on-surface-variant);
}

.loading-icon,
.error-icon,
.empty-icon {
  font-size: 48px;
  opacity: 0.5;
}

.error-state {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 20px;
  color: var(--md-sys-color-error);
  background: var(--md-sys-color-error-container);
  border-radius: 12px;
}

/* Toast */
.m3-snackbar {
  position: fixed;
  bottom: 24px;
  left: 50%;
  transform: translateX(-50%);
  background: var(--md-sys-color-inverse-surface);
  color: var(--md-sys-color-inverse-on-surface);
  padding: 14px 24px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  gap: 12px;
  box-shadow: var(--md-sys-elevation-3);
  z-index: 2000;
  min-width: 300px;
}

.m3-snackbar.error {
  background: var(--md-sys-color-error-container);
  color: var(--md-sys-color-on-error-container);
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

.dialog-enter-active,
.dialog-leave-active {
  transition: all 0.2s cubic-bezier(0.2, 0, 0, 1);
}

.dialog-enter-from,
.dialog-leave-to {
  opacity: 0;
  transform: scale(0.95);
}

/* 响应式 */
@media (max-width: 768px) {
  .config-manager {
    flex-direction: column;
  }
  
  .config-sidebar {
    width: 100%;
    min-width: auto;
    max-height: 40vh;
    border-right: none;
    border-bottom: 1px solid var(--md-sys-color-outline-variant);
  }
  
  .editor-header {
    flex-direction: column;
    gap: 12px;
    align-items: flex-start;
  }
  
  .editor-controls {
    width: 100%;
    flex-direction: column;
  }
  
  .m3-segmented-button {
    width: 100%;
  }
  
  .m3-segmented-button .segment {
    flex: 1;
    justify-content: center;
  }
  
  .editor-actions {
    width: 100%;
  }
  
  .editor-actions button {
    flex: 1;
  }
}
</style>
