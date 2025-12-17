<template>
  <div class="config-manager">
    <!-- 配置文件列表侧边栏 -->
    <aside class="config-sidebar">
      <div class="sidebar-header">
        <h3>
          <Icon icon="lucide:settings-2" />
          配置管理
        </h3>
        <button class="btn-icon" @click="refreshConfigList" :disabled="loading" title="刷新">
          <Icon icon="lucide:refresh-cw" :class="{ spinning: loading }" />
        </button>
      </div>
      
      <!-- 分类区域 -->
      <div class="config-categories">
        <!-- 核心配置 -->
        <div class="category-section">
          <div class="category-title">
            <Icon icon="lucide:star" />
            核心配置
          </div>
          <div 
            v-for="config in coreConfigs" 
            :key="config.path"
            :class="['config-item', { active: selectedConfig?.path === config.path }]"
            @click="selectConfig(config)"
          >
            <div class="config-item-icon" :class="config.type">
              <Icon :icon="getConfigIcon(config.type)" />
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
            <Icon icon="lucide:puzzle" />
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
                <Icon icon="lucide:puzzle" />
              </div>
              <div class="config-item-info">
                <span class="config-name">{{ config.display_name }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </aside>

    <!-- 配置编辑区（全屏展开） -->
    <main class="config-editor-area">
      <div v-if="!selectedConfig" class="no-selection">
        <Icon icon="lucide:file-cog" />
        <h3>选择配置文件开始编辑</h3>
        <p>从左侧选择一个配置文件，可以进行可视化编辑或源码编辑</p>
      </div>
      
      <template v-else>
        <!-- 编辑器头部 -->
        <div class="editor-header">
          <div class="editor-title">
            <Icon :icon="getConfigIcon(selectedConfig.type)" />
            <h2>{{ selectedConfig.display_name }}</h2>
            <span class="config-type-badge" :class="selectedConfig.type">
              {{ getConfigTypeLabel(selectedConfig.type) }}
            </span>
          </div>
          <div class="editor-controls">
            <div class="editor-tabs">
              <button 
                :class="['tab-btn', { active: editorMode === 'visual' }]"
                @click="editorMode = 'visual'"
              >
                <Icon icon="lucide:layout-grid" />
                可视化
              </button>
              <button 
                :class="['tab-btn', { active: editorMode === 'source' }]"
                @click="editorMode = 'source'"
              >
                <Icon icon="lucide:code" />
                源码
              </button>
            </div>
            <div class="editor-actions">
              <button class="btn btn-ghost" @click="showBackupsModal = true">
                <Icon icon="lucide:history" />
                备份
              </button>
              <button 
                class="btn btn-primary" 
                @click="saveCurrentConfig" 
                :disabled="saving || !hasChanges"
              >
                <Icon :icon="saving ? 'lucide:loader-2' : 'lucide:save'" :class="{ spinning: saving }" />
                {{ saving ? '保存中...' : '保存配置' }}
              </button>
            </div>
          </div>
        </div>

        <!-- 可视化编辑模式 -->
        <div v-if="editorMode === 'visual'" class="visual-editor">
          <div v-if="schemaLoading" class="loading-state">
            <Icon icon="lucide:loader-2" class="spinning" />
            加载配置结构...
          </div>
          <div v-else-if="schemaError" class="error-state">
            <Icon icon="lucide:alert-circle" />
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
                class="config-section"
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
              <Icon icon="lucide:file-text" />
              {{ selectedConfig.path }}
            </span>
            <div class="toolbar-actions">
              <button class="btn btn-sm btn-ghost" @click="formatSource">
                <Icon icon="lucide:align-left" />
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
            <Icon icon="lucide:alert-triangle" />
            {{ validationError }}
          </div>
        </div>
      </template>
    </main>

    <!-- 备份管理弹窗 -->
    <div v-if="showBackupsModal" class="modal-overlay" @click.self="showBackupsModal = false">
      <div class="modal-content">
        <div class="modal-header">
          <h3>
            <Icon icon="lucide:history" />
            备份管理
          </h3>
          <button class="close-btn" @click="showBackupsModal = false">
            <Icon icon="lucide:x" />
          </button>
        </div>
        <div class="modal-body">
          <div v-if="backupsLoading" class="loading-state">
            <Icon icon="lucide:loader-2" class="spinning" />
            加载备份列表...
          </div>
          <div v-else-if="backups.length === 0" class="empty-state">
            <Icon icon="lucide:archive-x" />
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
                class="btn btn-sm btn-ghost" 
                @click="restoreBackup(backup.name)"
                :disabled="restoringBackup === backup.name"
              >
                <Icon :icon="restoringBackup === backup.name ? 'lucide:loader-2' : 'lucide:rotate-ccw'" 
                      :class="{ spinning: restoringBackup === backup.name }" />
                恢复
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Toast 提示 -->
    <div v-if="toast.show" :class="['toast', toast.type]">
      <Icon :icon="toast.type === 'success' ? 'lucide:check-circle' : 'lucide:alert-circle'" />
      {{ toast.message }}
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch, shallowRef } from 'vue'
import { Icon } from '@iconify/vue'
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
import FieldEditor from '@/components/config/FieldEditor.vue'
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
    main: 'lucide:bot',
    model: 'lucide:brain',
    plugin: 'lucide:puzzle'
  }
  return icons[type] || 'lucide:file-cog'
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
  background: var(--bg-primary);
  border-right: 1px solid var(--border-color);
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.sidebar-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px;
  border-bottom: 1px solid var(--border-color);
}

.sidebar-header h3 {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0;
}

.sidebar-header h3 svg {
  color: var(--primary);
}

.btn-icon {
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  border: none;
  background: transparent;
  border-radius: var(--radius);
  color: var(--text-secondary);
  cursor: pointer;
  transition: all var(--transition-fast);
}

.btn-icon:hover {
  background: var(--bg-secondary);
  color: var(--text-primary);
}

.btn-icon:disabled {
  opacity: 0.5;
  cursor: not-allowed;
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
  font-weight: 600;
  color: var(--text-tertiary);
  text-transform: uppercase;
  letter-spacing: 0.5px;
  padding: 8px 12px;
}

.category-title .count {
  margin-left: auto;
  padding: 2px 8px;
  background: var(--bg-secondary);
  border-radius: var(--radius-full);
  font-size: 11px;
}

.config-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  border-radius: var(--radius);
  cursor: pointer;
  transition: all var(--transition-fast);
  margin-bottom: 4px;
}

.config-item:hover {
  background: var(--bg-secondary);
}

.config-item.active {
  background: var(--primary-bg);
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
  border-radius: var(--radius);
  color: white;
}

.config-item-icon.main {
  background: linear-gradient(135deg, #3b82f6, #1d4ed8);
}

.config-item-icon.model {
  background: linear-gradient(135deg, #8b5cf6, #6d28d9);
}

.config-item-icon.plugin {
  background: linear-gradient(135deg, #10b981, #059669);
}

.config-item.active .config-item-icon {
  box-shadow: 0 4px 12px rgba(59, 130, 246, 0.4);
}

.config-item-info {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.config-name {
  font-size: 13px;
  font-weight: 500;
  color: var(--text-primary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.config-desc {
  font-size: 11px;
  color: var(--text-tertiary);
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
  background: var(--bg-secondary);
}

.no-selection {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 16px;
  color: var(--text-tertiary);
}

.no-selection svg {
  font-size: 64px;
  opacity: 0.3;
}

.no-selection h3 {
  font-size: 18px;
  font-weight: 500;
  margin: 0;
  color: var(--text-secondary);
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
  background: var(--bg-primary);
  border-bottom: 1px solid var(--border-color);
}

.editor-title {
  display: flex;
  align-items: center;
  gap: 12px;
}

.editor-title svg {
  font-size: 24px;
  color: var(--primary);
}

.editor-title h2 {
  font-size: 18px;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0;
}

.config-type-badge {
  font-size: 11px;
  font-weight: 500;
  padding: 4px 10px;
  border-radius: var(--radius-full);
}

.config-type-badge.main {
  background: rgba(59, 130, 246, 0.1);
  color: #3b82f6;
}

.config-type-badge.model {
  background: rgba(139, 92, 246, 0.1);
  color: #8b5cf6;
}

.config-type-badge.plugin {
  background: rgba(16, 185, 129, 0.1);
  color: #10b981;
}

.editor-controls {
  display: flex;
  align-items: center;
  gap: 16px;
}

.editor-tabs {
  display: flex;
  gap: 4px;
  background: var(--bg-secondary);
  padding: 4px;
  border-radius: var(--radius);
}

.tab-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 16px;
  border: none;
  background: transparent;
  border-radius: var(--radius-sm);
  font-size: 13px;
  color: var(--text-secondary);
  cursor: pointer;
  transition: all var(--transition-fast);
}

.tab-btn:hover {
  color: var(--text-primary);
}

.tab-btn.active {
  background: var(--bg-primary);
  color: var(--primary);
  box-shadow: var(--shadow-sm);
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
  background: var(--bg-primary);
  border-radius: var(--radius-lg);
  overflow: hidden;
  border: 1px solid var(--border-color);
}

.section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 20px;
  background: var(--bg-secondary);
  border-bottom: 1px solid var(--border-color);
}

.section-header h3 {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0;
}

.field-count {
  font-size: 12px;
  color: var(--text-tertiary);
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
  color: var(--text-primary);
}

.field-type {
  font-size: 11px;
  padding: 2px 8px;
  background: var(--bg-secondary);
  border-radius: var(--radius-sm);
  color: var(--text-tertiary);
}

.field-description {
  font-size: 12px;
  color: var(--text-tertiary);
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
  background: var(--bg-primary);
  border-bottom: 1px solid var(--border-color);
}

.file-path {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  font-family: 'JetBrains Mono', 'Fira Code', monospace;
  color: var(--text-secondary);
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
  background: rgba(239, 68, 68, 0.1);
  border-top: 1px solid rgba(239, 68, 68, 0.3);
  color: #ef4444;
  font-size: 13px;
  display: flex;
  align-items: center;
  gap: 8px;
}

/* 按钮样式 */
.btn {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  padding: 8px 16px;
  border: none;
  border-radius: var(--radius);
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: all var(--transition-fast);
}

.btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn-primary {
  background: var(--primary);
  color: white;
}

.btn-primary:hover:not(:disabled) {
  background: var(--primary-hover);
}

.btn-ghost {
  background: transparent;
  color: var(--text-secondary);
}

.btn-ghost:hover:not(:disabled) {
  background: var(--bg-secondary);
  color: var(--text-primary);
}

.btn-sm {
  padding: 6px 12px;
  font-size: 12px;
}

/* 弹窗样式 */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.6);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  backdrop-filter: blur(4px);
}

.modal-content {
  background: var(--bg-primary);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-lg);
  width: 90%;
  max-width: 500px;
  max-height: 80vh;
  overflow: hidden;
  animation: modalIn 0.2s ease;
  display: flex;
  flex-direction: column;
}

@keyframes modalIn {
  from { opacity: 0; transform: scale(0.95); }
  to { opacity: 1; transform: scale(1); }
}

.modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 20px;
  border-bottom: 1px solid var(--border-color);
}

.modal-header h3 {
  display: flex;
  align-items: center;
  gap: 8px;
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary);
}

.close-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  border: none;
  background: transparent;
  border-radius: var(--radius);
  color: var(--text-secondary);
  cursor: pointer;
  transition: all var(--transition-fast);
}

.close-btn:hover {
  background: var(--bg-secondary);
  color: var(--text-primary);
}

.modal-body {
  padding: 20px;
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
  background: var(--bg-secondary);
  border-radius: var(--radius);
}

.backup-info {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.backup-name {
  font-size: 13px;
  font-weight: 500;
  color: var(--text-primary);
}

.backup-meta {
  font-size: 12px;
  color: var(--text-tertiary);
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
  color: var(--text-tertiary);
}

.error-state {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 20px;
  color: #ef4444;
  background: rgba(239, 68, 68, 0.1);
  border-radius: var(--radius);
}

/* Toast */
.toast {
  position: fixed;
  bottom: 24px;
  right: 24px;
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 20px;
  border-radius: var(--radius);
  font-size: 14px;
  font-weight: 500;
  box-shadow: var(--shadow-lg);
  animation: toastIn 0.3s ease;
  z-index: 2000;
}

.toast.success {
  background: #10b981;
  color: white;
}

.toast.error {
  background: #ef4444;
  color: white;
}

@keyframes toastIn {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
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
    border-bottom: 1px solid var(--border-color);
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
  
  .editor-tabs {
    width: 100%;
  }
  
  .tab-btn {
    flex: 1;
    justify-content: center;
  }
  
  .editor-actions {
    width: 100%;
  }
  
  .editor-actions .btn {
    flex: 1;
  }
}
</style>
