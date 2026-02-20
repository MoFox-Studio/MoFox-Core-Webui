<!--
  @file BotConfigView.vue
  @description Core 配置管理页面
  
  功能说明：
  1. Neo-MoFox Core 层配置管理
  2. 从后端动态获取配置 Schema
  3. 支持可视化编辑模式（表单）和源码编辑模式（Monaco Editor）
  4. 实时保存配置到后端
  5. 备份管理：创建、列出、恢复备份
  
  特性：
  - 后端管理配置描述和元数据
  - 类型安全的配置更新
  - 自动检测配置变更
  - 实时保存反馈
  - Monaco Editor TOML 源码编辑
  - 备份历史管理
-->
<template>
  <div class="core-config-view">
    <!-- 顶部操作栏 -->
    <header class="config-header">
      <div class="header-left">
        <div class="header-icon-container">
          <span class="material-symbols-rounded header-icon">settings</span>
        </div>
        <div class="header-info">
          <h1>Core 配置</h1>
          <p>管理 Neo-MoFox Core 层配置 <span v-if="configVersion" class="version-tag">v{{ configVersion }}</span></p>
        </div>
      </div>
      <div class="header-actions">
        <!-- 编辑模式切换 -->
        <div class="segmented-button-group">
          <button 
            class="segmented-btn" :class="{ active: editorMode === 'visual' }" 
            @click="editorMode = 'visual'" title="可视化编辑"
          >
            <span class="material-symbols-rounded">tune</span>
            可视化
          </button>
          <button 
            class="segmented-btn" :class="{ active: editorMode === 'source' }" 
            @click="switchToSource" title="源码编辑"
          >
            <span class="material-symbols-rounded">code</span>
            源码
          </button>
        </div>

        <!-- 备份历史 -->
        <button class="m3-icon-button" @click="openBackupsModal" title="备份历史">
          <span class="material-symbols-rounded">history</span>
        </button>

        <!-- 刷新 -->
        <button class="m3-icon-button" @click="reloadConfig" title="刷新配置">
          <span class="material-symbols-rounded" :class="{ spinning: loading }">refresh</span>
        </button>

        <!-- 保存 -->
        <button 
          class="m3-button filled" 
          @click="saveCurrentConfig" 
          :disabled="saving || !hasChanges"
        >
          <span class="material-symbols-rounded" :class="{ spinning: saving }">
            {{ saving ? 'progress_activity' : 'save' }}
          </span>
          {{ saving ? '保存中...' : (hasChanges ? '保存配置' : '无变更') }}
        </button>
      </div>
    </header>

    <!-- 可视化编辑器 -->
    <div v-show="editorMode === 'visual'" class="editor-area">
      <div v-if="loading" class="loading-state">
        <span class="material-symbols-rounded spinning">progress_activity</span>
        加载配置中...
      </div>
      <div v-else-if="loadError" class="error-state">
        <span class="material-symbols-rounded">error</span>
        {{ loadError }}
        <button class="m3-button text" @click="reloadConfig">
          <span class="material-symbols-rounded">refresh</span>
          重试
        </button>
      </div>
      <template v-else>
        <BotConfigEditor 
          :parsed-data="originalConfig"
          :edited-values="editedValues"
          :config-schema="configSchema"
          @update="updateFieldValue"
        />
      </template>
    </div>

    <!-- 源码编辑器 -->
    <div v-show="editorMode === 'source'" class="editor-area source-editor-wrap">
      <div class="source-toolbar">
        <span class="material-symbols-rounded">description</span>
        <span class="source-path">config/core.toml</span>
        <div class="source-toolbar-actions">
          <button class="m3-icon-button small" @click="formatSource" title="格式化">
            <span class="material-symbols-rounded">format_align_left</span>
          </button>
        </div>
      </div>
        <vue-monaco-editor
          v-model:value="sourceContent"
          :language="'ini'"
          :theme="isDarkMode ? 'vs-dark' : 'vs'"
          :options="monacoOptions"
        />
    </div>

    <!-- 备份管理 Modal -->
    <Transition name="modal">
      <div v-if="showBackupsModal" class="modal-overlay" @click.self="showBackupsModal = false">
        <div class="modal-panel">
          <div class="modal-header">
            <span class="material-symbols-rounded modal-header-icon">history</span>
            <h2>配置备份历史</h2>
            <button class="m3-icon-button" @click="showBackupsModal = false">
              <span class="material-symbols-rounded">close</span>
            </button>
          </div>

          <div class="modal-body">
            <div v-if="backupsLoading" class="loading-state small">
              <span class="material-symbols-rounded spinning">progress_activity</span>
              加载备份列表...
            </div>
            <div v-else-if="backups.length === 0" class="empty-state">
              <span class="material-symbols-rounded">folder_open</span>
              暂无备份记录
            </div>
            <ul v-else class="backup-list">
              <li v-for="bk in backups" :key="bk.name" class="backup-item">
                <div class="backup-info">
                  <span class="backup-name">{{ bk.name }}</span>
                  <div class="backup-meta">
                    <span class="material-symbols-rounded small-icon">schedule</span>
                    {{ formatDate(bk.created_at) }}
                    <span class="sep">·</span>
                    <span class="material-symbols-rounded small-icon">data_object</span>
                    {{ formatSize(bk.size) }}
                  </div>
                </div>
                <button 
                  class="m3-button tonal small" 
                  @click="restoreBackupItem(bk.name)"
                  :disabled="restoring === bk.name"
                >
                  <span class="material-symbols-rounded" :class="{ spinning: restoring === bk.name }">
                    {{ restoring === bk.name ? 'progress_activity' : 'restore' }}
                  </span>
                  {{ restoring === bk.name ? '恢复中...' : '恢复' }}
                </button>
              </li>
            </ul>
          </div>
        </div>
      </div>
    </Transition>

    <!-- Toast 通知 -->
    <Transition name="toast">
      <div v-if="toast.visible" class="m3-snackbar" :class="toast.type">
        <span class="material-symbols-rounded">
          {{ toast.type === 'success' ? 'check_circle' : 'error' }}
        </span>
        {{ toast.message }}
      </div>
    </Transition>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { VueMonacoEditor } from '@guolao/vue-monaco-editor'
import BotConfigEditor from '@/components/config/BotConfigEditor.vue'
import { showConfirm } from '@/utils/dialog'
import { 
  getCoreConfigSchema,
  getCoreConfig,
  getCoreConfigRaw,
  saveCoreConfigRaw,
  updateCoreConfig,
  getCoreConfigBackups,
  restoreCoreConfigBackup,
  type ConfigGroupSchema,
  type ConfigBackupInfo,
} from '@/api/coreConfig'

// ==================== 状态 ====================

const loading = ref(false)
const saving = ref(false)
const loadError = ref('')

// 编辑模式：visual | source
const editorMode = ref<'visual' | 'source'>('visual')

// 配置数据
const configVersion = ref('')
const configSchema = ref<ConfigGroupSchema[]>([])
const originalConfig = ref<Record<string, Record<string, unknown>>>({})
const editedValues = ref<Record<string, unknown>>({})

// 源码编辑
const sourceContent = ref('')
const originalSource = ref('')
let monacoEditorInstance: any = null

const monacoOptions = {
  minimap: { enabled: true },
  fontSize: 14,
  lineNumbers: 'on',
  roundedSelection: true,
  scrollBeyondLastLine: false,
  automaticLayout: true,
  tabSize: 2,
  wordWrap: 'on',
  lineHeight: 24,
  fontFamily: "'JetBrains Mono', 'Fira Code', Consolas, monospace",
  padding: { top: 16, bottom: 16 },
  folding: true,
  lineDecorationsWidth: 10,
  lineNumbersMinChars: 3,
  renderLineHighlight: 'all',
  scrollbar: {
    verticalScrollbarSize: 10,
    horizontalScrollbarSize: 10
  }
}

// 备份管理
const showBackupsModal = ref(false)
const backupsLoading = ref(false)
const backups = ref<ConfigBackupInfo[]>([])
const restoring = ref('')

const isDarkMode = ref(true)

// Toast
const toast = ref({ visible: false, message: '', type: 'success' as 'success' | 'error' })

// ==================== 计算属性 ====================

const hasChanges = computed(() => {
  if (editorMode.value === 'source') {
    return sourceContent.value !== originalSource.value
  }
  return Object.keys(editedValues.value).length > 0
})

// ==================== 生命周期 ====================

onMounted(async () => {
  await loadConfig()
  isDarkMode.value = window.matchMedia('(prefers-color-scheme: dark)').matches
})

// ==================== 加载配置 ====================

async function loadConfig() {
  loading.value = true
  loadError.value = ''

  try {
    const [schemaData, configData, rawData] = await Promise.all([
      getCoreConfigSchema(),
      getCoreConfig(),
      getCoreConfigRaw(),
    ])

    configSchema.value = schemaData.groups
    configVersion.value = schemaData.version
    originalConfig.value = configData.config
    editedValues.value = {}

    sourceContent.value = rawData.content
    originalSource.value = rawData.content
  } catch (error: any) {
    loadError.value = error.message || '加载配置失败'
    console.error('加载配置失败:', error)
  } finally {
    loading.value = false
  }
}

async function reloadConfig() {
  if (hasChanges.value) {
    const ok = await showConfirm({
      title: '放弃更改',
      message: '当前有未保存的更改，刷新将丢失这些更改。确定要继续吗？',
      type: 'warning',
      confirmText: '继续刷新',
      cancelText: '取消',
    })
    if (!ok) return
  }
  await loadConfig()
}

// ==================== 可视化编辑 ====================

function updateFieldValue(fullKey: string, value: unknown) {
  editedValues.value[fullKey] = value

  const parts = fullKey.split('.')
  if (parts.length === 2) {
    const [section, field] = parts
    if (section && field) {
      if (!originalConfig.value[section]) originalConfig.value[section] = {}
      originalConfig.value[section][field] = value
    }
  }
}

// ==================== 源码编辑 ====================

async function switchToSource() {
  editorMode.value = 'source'
  // 若已有编辑的表单值，先从后端拉取最新文本
  if (Object.keys(editedValues.value).length > 0) {
    const ok = await showConfirm({
      title: '切换编辑模式',
      message: '切换到源码模式将丢弃未保存的可视化更改，确定继续？',
      type: 'warning',
      confirmText: '切换',
      cancelText: '取消',
    })
    if (!ok) {
      editorMode.value = 'visual'
      return
    }
  }
  try {
    const rawData = await getCoreConfigRaw()
    sourceContent.value = rawData.content
    originalSource.value = rawData.content
    editedValues.value = {}
  } catch (error: any) {
    showToast(error.message || '获取源码失败', 'error')
    editorMode.value = 'visual'
  }
}

function onEditorMount(editor: any) {
  monacoEditorInstance = editor
}

function formatSource() {
  if (monacoEditorInstance) {
    monacoEditorInstance.getAction('editor.action.formatDocument')?.run()
  }
}

// ==================== 保存 ====================

async function saveCurrentConfig() {
  if (!hasChanges.value) return

  saving.value = true
  try {
    if (editorMode.value === 'source') {
      const result = await saveCoreConfigRaw(sourceContent.value)
      if (result.success) {
        showToast(result.message || '配置已保存', 'success')
        originalSource.value = sourceContent.value
        // 同步可视化数据
        await loadConfig()
      } else {
        showToast(result.message || '保存失败', 'error')
      }
    } else {
      const result = await updateCoreConfig(editedValues.value)
      if (result.success) {
        showToast('配置已保存', 'success')
        editedValues.value = {}
        await loadConfig()
      } else {
        showToast(result.message || '保存配置失败', 'error')
        if (result.failed_keys?.length) {
          console.error('以下配置项保存失败:', result.failed_keys)
        }
      }
    }
  } catch (error: any) {
    showToast(error.message || '保存请求失败', 'error')
    console.error('保存配置失败:', error)
  } finally {
    saving.value = false
  }
}

// ==================== 备份管理 ====================

async function openBackupsModal() {
  showBackupsModal.value = true
  await fetchBackups()
}

async function fetchBackups() {
  backupsLoading.value = true
  try {
    const data = await getCoreConfigBackups()
    backups.value = data.backups
  } catch (error: any) {
    showToast(error.message || '获取备份列表失败', 'error')
  } finally {
    backupsLoading.value = false
  }
}

async function restoreBackupItem(name: string) {
  const ok = await showConfirm({
    title: '恢复备份',
    message: `确定要从备份 "${name}" 恢复配置吗？当前配置将被覆盖。`,
    type: 'danger',
    confirmText: '确认恢复',
    cancelText: '取消',
  })
  if (!ok) return

  restoring.value = name
  try {
    const result = await restoreCoreConfigBackup(name)
    if (result.success) {
      showToast(result.message || '恢复成功', 'success')
      showBackupsModal.value = false
      await loadConfig()
    } else {
      showToast(result.message || '恢复失败', 'error')
    }
  } catch (error: any) {
    showToast(error.message || '恢复请求失败', 'error')
  } finally {
    restoring.value = ''
  }
}

function formatDate(iso: string): string {
  if (!iso) return ''
  const d = new Date(iso)
  return d.toLocaleString('zh-CN', { hour12: false })
}

function formatSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / 1024 / 1024).toFixed(2)} MB`
}

// ==================== Toast ====================

function showToast(msg: string, type: 'success' | 'error' = 'success') {
  toast.value = { visible: true, message: msg, type }
  setTimeout(() => { toast.value.visible = false }, 3000)
}
</script>

<style scoped>
.core-config-view {
  display: flex;
  flex-direction: column;
  height: 100%;
  padding: 16px;
  gap: 16px;
  animation: fadeIn 0.4s cubic-bezier(0.2, 0, 0, 1);
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}

/* ===== 头部 ===== */
.config-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 24px;
  background: var(--md-sys-color-surface-container);
  border-radius: 32px;
  flex-shrink: 0;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 16px;
}

.header-icon-container {
  width: 48px;
  height: 48px;
  border-radius: 16px;
  background: var(--md-sys-color-primary-container);
  color: var(--md-sys-color-on-primary-container);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.header-icon { font-size: 24px; }

.header-info h1 {
  font-size: 22px;
  font-weight: 400;
  color: var(--md-sys-color-on-surface);
  margin: 0 0 4px;
}

.header-info p {
  font-size: 14px;
  color: var(--md-sys-color-on-surface-variant);
  margin: 0;
  display: flex;
  align-items: center;
  gap: 8px;
}

.version-tag {
  display: inline-block;
  padding: 2px 8px;
  background: var(--md-sys-color-tertiary-container);
  color: var(--md-sys-color-on-tertiary-container);
  border-radius: 12px;
  font-size: 11px;
  font-weight: 500;
  font-family: 'Roboto Mono', monospace;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 12px;
}

/* ===== 分段按钮 ===== */
.segmented-button-group {
  display: flex;
  border: 1px solid var(--md-sys-color-outline);
  border-radius: 20px;
  overflow: hidden;
}

.segmented-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 16px;
  font-size: 13px;
  font-weight: 500;
  background: transparent;
  color: var(--md-sys-color-on-surface-variant);
  border: none;
  cursor: pointer;
  transition: background 0.2s, color 0.2s;
}

.segmented-btn:hover {
  background: var(--md-sys-color-surface-container-highest);
}

.segmented-btn.active {
  background: var(--md-sys-color-secondary-container);
  color: var(--md-sys-color-on-secondary-container);
}

.segmented-btn .material-symbols-rounded {
  font-size: 18px;
}

/* ===== 编辑区域 ===== */
.editor-area {
  flex: 1;
  background: var(--md-sys-color-surface-container);
  border-radius: 32px;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  position: relative;
  min-height: 0;
}

/* 可视化模式 */
.editor-area:not(.source-editor-wrap) {
  padding: 24px;
  overflow-y: auto;
}

/* 源码模式 */
.source-editor-wrap {
  padding: 0;
}

.source-toolbar {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 16px;
  background: var(--md-sys-color-surface-container-high);
  border-bottom: 1px solid var(--md-sys-color-outline-variant);
  color: var(--md-sys-color-on-surface-variant);
  font-size: 13px;
  flex-shrink: 0;
}

.source-path {
  font-family: 'Roboto Mono', monospace;
  flex: 1;
}

.source-toolbar-actions {
  display: flex;
  gap: 4px;
}

.monaco-editor-instance {
  flex: 1;
  min-height: 0;
}

/* ===== 状态 ===== */
.loading-state, .error-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 400px;
  gap: 16px;
  color: var(--md-sys-color-on-surface-variant);
}

.loading-state.small {
  min-height: 120px;
}

.error-state { color: var(--md-sys-color-error); }

.error-state .material-symbols-rounded {
  font-size: 48px;
  color: var(--md-sys-color-error);
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  padding: 48px;
  color: var(--md-sys-color-on-surface-variant);
}

.empty-state .material-symbols-rounded {
  font-size: 40px;
  opacity: 0.5;
}

/* ===== 旋转 ===== */
.spinning { animation: spin 1s linear infinite; }

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

/* ===== Modal ===== */
.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.5);
  z-index: 1000;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 24px;
}

.modal-panel {
  background: var(--md-sys-color-surface-container-high);
  border-radius: 28px;
  width: 100%;
  max-width: 540px;
  max-height: 80vh;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.24);
}

.modal-header {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 20px 24px;
  border-bottom: 1px solid var(--md-sys-color-outline-variant);
  flex-shrink: 0;
}

.modal-header-icon {
  font-size: 24px;
  color: var(--md-sys-color-primary);
}

.modal-header h2 {
  flex: 1;
  font-size: 18px;
  font-weight: 500;
  color: var(--md-sys-color-on-surface);
  margin: 0;
}

.modal-body {
  flex: 1;
  overflow-y: auto;
  padding: 8px 0;
}

.backup-list {
  list-style: none;
  margin: 0;
  padding: 0;
}

.backup-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 24px;
  border-bottom: 1px solid var(--md-sys-color-outline-variant);
  transition: background 0.15s;
}

.backup-item:last-child { border-bottom: none; }

.backup-item:hover {
  background: var(--md-sys-color-surface-container-highest);
}

.backup-info {
  flex: 1;
  min-width: 0;
}

.backup-name {
  display: block;
  font-family: 'Roboto Mono', monospace;
  font-size: 13px;
  color: var(--md-sys-color-on-surface);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.backup-meta {
  display: flex;
  align-items: center;
  gap: 4px;
  margin-top: 4px;
  font-size: 12px;
  color: var(--md-sys-color-on-surface-variant);
}

.sep { margin: 0 4px; opacity: 0.5; }

.small-icon {
  font-size: 14px !important;
}

/* ===== 按钮扩展 ===== */
.m3-button.small {
  padding: 6px 12px;
  font-size: 13px;
}

.m3-icon-button.small {
  width: 32px;
  height: 32px;
}

.m3-icon-button.small .material-symbols-rounded {
  font-size: 18px;
}

/* ===== Snackbar ===== */
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
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.18);
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

/* ===== Modal 动画 ===== */
.modal-enter-active,
.modal-leave-active {
  transition: opacity 0.25s cubic-bezier(0.2, 0, 0, 1);
}

.modal-enter-from,
.modal-leave-to {
  opacity: 0;
}

.modal-enter-active .modal-panel,
.modal-leave-active .modal-panel {
  transition: transform 0.25s cubic-bezier(0.2, 0, 0, 1);
}

.modal-enter-from .modal-panel,
.modal-leave-to .modal-panel {
  transform: scale(0.95) translateY(8px);
}
</style>
