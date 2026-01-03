<!--
  @file ModelConfigView.vue
  @description AI 模型配置页面
  
  功能说明：
  1. 配置 AI 模型提供商（OpenAI、Azure 等）
  2. 管理 API 密钥和端点
  3. 设置模型参数（temperature、max_tokens 等）
  4. 支持可视化编辑和源码编辑
  
  编辑模式：
  - visual: 可视化表单编辑，使用 ModelConfigEditor 组件
  - source: 源码编辑，使用 Monaco Editor
  
  安全特性：
  - API 密钥默认隐藏显示
  - 支持配置备份和还原
-->
<template>
  <div class="model-config-view">
    <!-- 顶部操作栏：标题、编辑模式切换、备份、保存 -->
    <header class="config-header">
      <div class="header-left">
        <div class="header-icon-container">
          <span class="material-symbols-rounded header-icon">psychology</span>
        </div>
        <div class="header-info">
          <h1>模型配置</h1>
          <p>配置 AI 模型提供商、API 密钥和模型参数</p>
        </div>
      </div>
      <div class="header-actions">
        <div class="m3-segmented-button">
          <button 
            :class="['segment', { active: editorMode === 'visual' }]"
            @click="editorMode = 'visual'"
          >
            <span class="material-symbols-rounded">grid_view</span>
            可视化
          </button>
          <button 
            :class="['segment', { active: editorMode === 'source' }]"
            @click="editorMode = 'source'"
          >
            <span class="material-symbols-rounded">code</span>
            源码
          </button>
        </div>
        <button class="m3-icon-button" @click="showBackupsModal = true" title="备份历史">
          <span class="material-symbols-rounded">history</span>
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
    </header>

    <!-- 可视化编辑模式 -->
    <div v-if="editorMode === 'visual'" class="visual-editor">
      <div v-if="loading" class="loading-state">
        <span class="material-symbols-rounded spinning">progress_activity</span>
        加载配置中...
      </div>
      <div v-else-if="loadError" class="error-state">
        <span class="material-symbols-rounded">error</span>
        {{ loadError }}
      </div>
      <template v-else>
        <ModelConfigEditor 
          :parsed-data="originalParsed"
          :edited-values="editedValues"
          @update="updateFieldValue"
        />
      </template>
    </div>

    <!-- 源码编辑模式 (Monaco Editor) -->
    <div v-else class="source-editor">
      <div class="source-toolbar">
        <span class="file-path">
          <span class="material-symbols-rounded">description</span>
          {{ configPath }}
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
          :language="'ini'"
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

    <!-- 备份管理弹窗 -->
    <Transition name="dialog">
      <div v-if="showBackupsModal" class="m3-dialog-overlay" @click.self="showBackupsModal = false">
        <div class="m3-dialog">
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
              <span class="material-symbols-rounded spinning">progress_activity</span>
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
import ModelConfigEditor from '@/components/config/ModelConfigEditor.vue'

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
const loading = ref(true)
const saving = ref(false)
const loadError = ref('')
const editorMode = ref<'visual' | 'source'>('visual')
const isDarkMode = ref(true)

// 配置数据
const configPath = ref('')
const configSchema = ref<ConfigSection[]>([])
const editedValues = ref<Record<string, unknown>>({})
const originalParsed = ref<Record<string, unknown>>({})

// 源码编辑状态
const sourceContent = ref('')
const originalContent = ref('')
const validationError = ref('')

// 备份相关
const showBackupsModal = ref(false)
const backups = ref<ConfigBackupInfo[]>([])
const backupsLoading = ref(false)
const restoringBackup = ref('')

// Toast 提示
const toast = ref({ show: false, message: '', type: 'success' as 'success' | 'error' })

// 计算属性
const hasChanges = computed(() => {
  if (editorMode.value === 'source') {
    return sourceContent.value !== originalContent.value
  }
  return Object.keys(editedValues.value).length > 0
})

// 方法
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

async function loadConfig() {
  loading.value = true
  loadError.value = ''
  
  try {
    // 获取配置列表，找到model类型的配置
    const listRes = await getConfigList()
    if (!listRes.success || !listRes.data) {
      loadError.value = '获取配置列表失败'
      return
    }
    
    const modelConfig = listRes.data.configs.find((c: ConfigFileInfo) => c.type === 'model')
    if (!modelConfig) {
      loadError.value = '未找到模型配置文件'
      return
    }
    
    configPath.value = modelConfig.path
    
    // 加载配置内容
    const contentRes = await getConfigContent(modelConfig.path)
    if (contentRes.success && contentRes.data && contentRes.data.success) {
      sourceContent.value = contentRes.data.content || ''
      originalContent.value = contentRes.data.content || ''
      originalParsed.value = contentRes.data.parsed || {}
    } else {
      loadError.value = contentRes.data?.error || contentRes.error || '加载配置内容失败'
      return
    }
    
    // 加载配置结构
    const schemaRes = await getConfigSchema(modelConfig.path)
    if (schemaRes.success && schemaRes.data && schemaRes.data.success) {
      configSchema.value = schemaRes.data.sections
    }
  } catch (e) {
    loadError.value = '加载配置时发生错误'
    console.error(e)
  } finally {
    loading.value = false
  }
}

function updateFieldValue(fullKey: string, value: unknown) {
  editedValues.value[fullKey] = value
}

async function saveCurrentConfig() {
  if (!configPath.value) return
  
  saving.value = true
  try {
    if (editorMode.value === 'source') {
      const res = await saveConfig(configPath.value, sourceContent.value)
      if (res.success && res.data && res.data.success) {
        originalContent.value = sourceContent.value
        showToast('配置已保存', 'success')
        await loadConfig()
      } else {
        showToast(res.data?.error || res.error || '保存失败', 'error')
      }
    } else {
      if (Object.keys(editedValues.value).length === 0) {
        showToast('没有需要保存的更改', 'error')
        return
      }
      
      const res = await updateConfig(configPath.value, editedValues.value)
      if (res.success && res.data && res.data.success) {
        editedValues.value = {}
        showToast('配置已保存', 'success')
        await loadConfig()
      } else {
        showToast(res.data?.error || res.error || '保存失败', 'error')
      }
    }
  } catch {
    showToast('保存配置失败', 'error')
  } finally {
    saving.value = false
  }
}

async function loadBackups() {
  if (!configPath.value) return
  
  backupsLoading.value = true
  try {
    const res = await getConfigBackups(configPath.value)
    if (res.success && res.data && res.data.success) {
      backups.value = res.data.backups
    }
  } catch {
    showToast('加载备份列表失败', 'error')
  } finally {
    backupsLoading.value = false
  }
}

async function restoreBackup(backupName: string) {
  if (!configPath.value) return
  
  if (!confirm(`确定要从备份 "${backupName}" 恢复配置吗？当前配置将被覆盖。`)) {
    return
  }
  
  restoringBackup.value = backupName
  try {
    const res = await restoreConfigBackup(configPath.value, backupName)
    if (res.success && res.data && res.data.success) {
      showToast('配置已恢复', 'success')
      showBackupsModal.value = false
      await loadConfig()
    } else {
      showToast(res.data?.error || res.error || '恢复失败', 'error')
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

watch(showBackupsModal, (show) => {
  if (show) {
    loadBackups()
  }
})

onMounted(() => {
  loadConfig()
  isDarkMode.value = window.matchMedia('(prefers-color-scheme: dark)').matches
})
</script>

<style scoped>
.model-config-view {
  height: 100%;
  display: flex;
  flex-direction: column;
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

/* 顶部操作栏 */
.config-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 20px 24px;
  background: var(--md-sys-color-surface);
  border-radius: 16px;
  margin: 16px 16px 0 16px;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 16px;
}

.header-icon-container {
  width: 48px;
  height: 48px;
  background: var(--md-sys-color-tertiary-container);
  color: var(--md-sys-color-on-tertiary-container);
  border-radius: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.header-icon {
  font-size: 28px;
}

.header-info h1 {
  font-size: 20px;
  font-weight: 500;
  color: var(--md-sys-color-on-surface);
  margin: 0 0 4px 0;
}

.header-info p {
  font-size: 13px;
  color: var(--md-sys-color-on-surface-variant);
  margin: 0;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 12px;
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

.m3-segmented-button .segment.active {
  background: var(--md-sys-color-secondary-container);
  color: var(--md-sys-color-on-secondary-container);
}

.m3-segmented-button .segment .material-symbols-rounded {
  font-size: 18px;
}

/* 可视化编辑器 */
.visual-editor {
  flex: 1;
  overflow: auto;
  padding: 24px;
  background: var(--md-sys-color-surface-container-low);
  border-radius: 16px;
  margin: 16px;
}

/* 源码编辑器 */
.source-editor {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  margin: 16px;
  background: var(--md-sys-color-surface-container-low);
  border-radius: 16px;
  border: 1px solid var(--md-sys-color-outline-variant);
}

.source-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  background: transparent;
  border-bottom: 1px solid var(--md-sys-color-outline-variant);
}

.file-path {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  color: var(--md-sys-color-on-surface-variant);
  font-family: 'Roboto Mono', 'Noto Sans SC', monospace;
}

.toolbar-actions {
  display: flex;
  gap: 8px;
}

.monaco-container {
  flex: 1;
  overflow: hidden;
}

.validation-error {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 16px;
  background: var(--md-sys-color-error-container);
  color: var(--md-sys-color-on-error-container);
  font-size: 13px;
}

/* 状态提示 */
.loading-state,
.error-state,
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 16px;
  padding: 60px 20px;
  color: var(--md-sys-color-on-surface-variant);
  font-size: 14px;
}

.loading-state .material-symbols-rounded,
.error-state .material-symbols-rounded,
.empty-state .empty-icon {
  font-size: 48px;
  opacity: 0.5;
}

.error-state {
  color: var(--md-sys-color-error);
}

/* 弹窗 */
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
  max-width: 500px;
  max-height: 80vh;
  display: flex;
  flex-direction: column;
  gap: 16px;
  box-shadow: var(--md-sys-elevation-3);
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
  font-size: 20px;
  font-weight: 400;
  color: var(--md-sys-color-on-surface);
  margin: 0;
}

.dialog-body {
  flex: 1;
  overflow-y: auto;
}

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
  gap: 4px;
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
</style>
