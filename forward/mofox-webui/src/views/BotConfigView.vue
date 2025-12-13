<template>
  <div class="bot-config-view">
    <!-- 顶部操作栏 -->
    <header class="config-header">
      <div class="header-left">
        <Icon icon="lucide:bot" class="header-icon" />
        <div class="header-info">
          <h1>机器人配置</h1>
          <p>配置机器人的基础信息、人格、聊天行为等</p>
        </div>
      </div>
      <div class="header-actions">
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
    </header>

    <!-- 可视化编辑模式 -->
    <div v-if="editorMode === 'visual'" class="visual-editor">
      <div v-if="loading" class="loading-state">
        <Icon icon="lucide:loader-2" class="spinning" />
        加载配置中...
      </div>
      <div v-else-if="loadError" class="error-state">
        <Icon icon="lucide:alert-circle" />
        {{ loadError }}
      </div>
      <template v-else>
        <MainConfigEditor 
          :parsed-data="originalParsed"
          :edited-values="editedValues"
          :config-schema="configSchema"
          @update="updateFieldValue"
        />
      </template>
    </div>

    <!-- 源码编辑模式 (Monaco Editor) -->
    <div v-else class="source-editor">
      <div class="source-toolbar">
        <span class="file-path">
          <Icon icon="lucide:file-text" />
          {{ configPath }}
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
          :language="'ini'"
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
    // 获取配置列表，找到main类型的配置
    const listRes = await getConfigList()
    if (!listRes.success || !listRes.data) {
      loadError.value = '获取配置列表失败'
      return
    }
    
    const mainConfig = listRes.data.configs.find((c: ConfigFileInfo) => c.type === 'main')
    if (!mainConfig) {
      loadError.value = '未找到机器人配置文件'
      return
    }
    
    configPath.value = mainConfig.path
    
    // 加载配置内容
    const contentRes = await getConfigContent(mainConfig.path)
    if (contentRes.success && contentRes.data) {
      sourceContent.value = contentRes.data.content || ''
      originalContent.value = contentRes.data.content || ''
      originalParsed.value = contentRes.data.parsed || {}
    } else {
      loadError.value = '加载配置内容失败'
      return
    }
    
    // 加载配置结构
    const schemaRes = await getConfigSchema(mainConfig.path)
    if (schemaRes.success && schemaRes.data?.success) {
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
      if (res.success && res.data?.success) {
        originalContent.value = sourceContent.value
        showToast('配置已保存', 'success')
        // 重新加载
        await loadConfig()
      } else {
        showToast(res.data?.error || '保存失败', 'error')
      }
    } else {
      if (Object.keys(editedValues.value).length === 0) {
        showToast('没有需要保存的更改', 'error')
        return
      }
      
      const res = await updateConfig(configPath.value, editedValues.value)
      if (res.success && res.data?.success) {
        editedValues.value = {}
        showToast('配置已保存', 'success')
        await loadConfig()
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
  if (!configPath.value) return
  
  backupsLoading.value = true
  try {
    const res = await getConfigBackups(configPath.value)
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
  if (!configPath.value) return
  
  if (!confirm(`确定要从备份 "${backupName}" 恢复配置吗？当前配置将被覆盖。`)) {
    return
  }
  
  restoringBackup.value = backupName
  try {
    const res = await restoreConfigBackup(configPath.value, backupName)
    if (res.success && res.data?.success) {
      showToast('配置已恢复', 'success')
      showBackupsModal.value = false
      await loadConfig()
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
.bot-config-view {
  height: 100%;
  display: flex;
  flex-direction: column;
  animation: fadeIn 0.4s ease;
  gap: 16px;
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
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
  padding: 20px 32px;
  background: var(--bg-primary);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-sm);
  margin-bottom: 8px;
  border: 1px solid transparent;
  transition: all var(--transition);
}

.config-header:hover {
  box-shadow: var(--shadow-md);
  border-color: var(--border-light);
}

.header-left {
  display: flex;
  align-items: center;
  gap: 20px;
}

.header-icon {
  font-size: 36px;
  color: var(--primary);
  background: var(--primary-bg);
  padding: 8px;
  border-radius: 12px;
}

.header-info h1 {
  font-size: 22px;
  font-weight: 700;
  color: var(--text-primary);
  margin: 0 0 4px 0;
}

.header-info p {
  font-size: 14px;
  color: var(--text-secondary);
  margin: 0;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 16px;
}

.editor-tabs {
  display: flex;
  background: var(--bg-secondary);
  border-radius: var(--radius-full);
  padding: 4px;
  border: 1px solid var(--border-light);
}

.tab-btn {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 20px;
  background: transparent;
  border: none;
  border-radius: var(--radius-full);
  color: var(--text-secondary);
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: all var(--transition);
}

.tab-btn:hover {
  color: var(--text-primary);
}

.tab-btn.active {
  background: var(--bg-primary);
  color: var(--primary);
  box-shadow: var(--shadow-sm);
}

.btn {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 20px;
  border: none;
  border-radius: var(--radius-full);
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: all var(--transition);
}

.btn-ghost {
  background: transparent;
  color: var(--text-secondary);
}

.btn-ghost:hover {
  background: var(--bg-secondary);
  color: var(--text-primary);
}

.btn-primary {
  background: var(--primary);
  color: white;
  box-shadow: var(--shadow-sm);
}

.btn-primary:hover {
  background: var(--primary-hover);
  box-shadow: var(--shadow-md);
  transform: translateY(-1px);
}

.btn-primary:disabled {
  opacity: 0.6;
  cursor: not-allowed;
  transform: none;
}

/* 可视化编辑器 */
.visual-editor {
  flex: 1;
  overflow: auto;
  padding: 24px;
  background: var(--bg-primary);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-sm);
  border: 1px solid transparent;
}

/* 源码编辑器 */
.source-editor {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  background: var(--bg-primary);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-sm);
  border: 1px solid transparent;
}

.source-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 24px;
  background: var(--bg-primary);
  border-bottom: 1px solid var(--border-light);
}

.file-path {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 14px;
  color: var(--text-secondary);
  font-weight: 500;
}

.toolbar-actions {
  display: flex;
  gap: 12px;
}

.btn-sm {
  padding: 6px 16px;
  font-size: 13px;
}

.monaco-container {
  flex: 1;
  overflow: hidden;
}

.validation-error {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 16px 24px;
  background: var(--danger-bg);
  border-top: 1px solid rgba(248, 113, 113, 0.2);
  color: var(--danger);
  font-size: 14px;
  font-weight: 500;
}

/* 状态提示 */
.loading-state,
.error-state,
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 20px;
  padding: 80px 20px;
  color: var(--text-tertiary);
  font-size: 15px;
  font-weight: 500;
}

.loading-state svg,
.error-state svg,
.empty-state svg {
  font-size: 56px;
  opacity: 0.5;
  margin-bottom: 8px;
}

.error-state {
  color: var(--danger);
}

/* 弹窗 */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.4);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  backdrop-filter: blur(8px);
  animation: fadeIn 0.3s ease;
}

.modal-content {
  background: var(--bg-primary);
  border-radius: var(--radius-xl);
  width: 90%;
  max-width: 500px;
  max-height: 80vh;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  box-shadow: var(--shadow-lg);
  animation: modalIn 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

@keyframes modalIn {
  from { opacity: 0; transform: scale(0.95) translateY(10px); }
  to { opacity: 1; transform: scale(1) translateY(0); }
}

.modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 20px 24px;
  border-bottom: 1px solid var(--border-light);
}

.modal-header h3 {
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: 18px;
  font-weight: 700;
  color: var(--text-primary);
  margin: 0;
}

.close-btn {
  width: 36px;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: transparent;
  border: none;
  border-radius: var(--radius);
  color: var(--text-secondary);
  cursor: pointer;
  transition: all var(--transition-fast);
}

.close-btn:hover {
  background: var(--bg-secondary);
  color: var(--danger);
}

.modal-body {
  flex: 1;
  overflow-y: auto;
  padding: 24px;
}

.backup-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.backup-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px;
  background: var(--bg-secondary);
  border-radius: var(--radius);
  transition: all var(--transition-fast);
  border: 1px solid transparent;
}

.backup-item:hover {
  background: var(--bg-primary);
  box-shadow: var(--shadow-sm);
  border-color: var(--border-light);
}

.backup-info {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.backup-name {
  font-size: 15px;
  font-weight: 600;
  color: var(--text-primary);
}

.backup-meta {
  font-size: 13px;
  color: var(--text-tertiary);
}

/* Toast */
.toast {
  position: fixed;
  bottom: 32px;
  right: 32px;
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 16px 24px;
  background: var(--bg-primary);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-lg);
  font-size: 15px;
  font-weight: 500;
  z-index: 2000;
  animation: slideIn 0.4s cubic-bezier(0.4, 0, 0.2, 1);
  border: 1px solid var(--border-light);
}

.toast.success {
  border-left: 4px solid var(--success);
  color: var(--success);
}

.toast.error {
  border-left: 4px solid var(--danger);
  color: var(--danger);
}

@keyframes slideIn {
  from {
    opacity: 0;
    transform: translateX(40px);
  }
  to {
    opacity: 1;
    transform: translateX(0);
  }
}
</style>
