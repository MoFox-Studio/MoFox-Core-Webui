<!--
  @file BotConfigView.vue
  @description 机器人配置页面
  
  功能说明：
  1. 机器人基础信息配置（名称、人格等）
  2. 聊天行为参数设置
  3. 支持可视化编辑和源码编辑两种模式
  4. 配置备份和还原功能
  
  编辑模式：
  - visual: 可视化表单编辑，使用 MainConfigEditor 组件
  - source: 源码编辑，使用 Monaco Editor
  
  配置管理：
  - 自动检测配置变更
  - 保存前验证配置格式
  - 支持查看和还原历史备份
-->
<template>
  <div class="bot-config-view">
    <!-- 顶部操作栏：标题、编辑模式切换、保存按钮 -->
    <header class="config-header">
      <div class="header-left">
        <div class="header-icon-container">
          <span class="material-symbols-rounded header-icon">smart_toy</span>
        </div>
        <div class="header-info">
          <h1>机器人配置</h1>
          <p>配置机器人的基础信息、人格、聊天行为等</p>
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
          :theme="'vs-dark'"
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
        <div class="dialog-content">
          <div v-if="backupsLoading" class="loading-state">
            <span class="material-symbols-rounded spinning">progress_activity</span>
            加载备份列表...
          </div>
          <div v-else-if="backups.length" class="backup-list">
            <div class="backup-item" v-for="backup in backups" :key="backup.path">
              <div class="backup-info">
                <span class="backup-name">{{ backup.name }}</span>
                <span class="backup-meta">{{ formatDate(backup.created_at) }} · {{ formatSize(backup.size) }}</span>
              </div>
              <div class="backup-actions">
                <button class="m3-button text small" @click="restoreBackup(backup)">
                  <span class="material-symbols-rounded">restore</span>
                  还原
                </button>
              </div>
            </div>
          </div>
          <div v-else class="empty-state">
            <span class="material-symbols-rounded empty-icon">history_toggle_off</span>
            <p>暂无备份记录</p>
          </div>
        </div>
      </div>
    </div>

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
import { ref, computed, onMounted, watch } from 'vue'
import { useThemeStore } from '@/stores/theme'
import MainConfigEditor from '@/components/config/MainConfigEditor.vue'
import { VueMonacoEditor } from '@guolao/vue-monaco-editor'
import { 
  getConfigContent, 
  saveConfig, 
  updateConfig,
  getConfigBackups, 
  restoreConfigBackup 
} from '@/api'
import { botConfigGroups } from '@/config/configDescriptions'

// 状态定义
const editorMode = ref<'visual' | 'source'>('visual')
const loading = ref(false)
const saving = ref(false)
const loadError = ref('')
const configPath = ref('bot_config.toml') // 默认主配置路径
const originalParsed = ref<any>({})
const editedValues = ref<any>({})
const sourceContent = ref('')
const originalSource = ref('')
const validationError = ref('')

// 备份相关
const showBackupsModal = ref(false)
const backupsLoading = ref(false)
const backups = ref<any[]>([])

// Toast
const toast = ref({ visible: false, message: '', type: 'success' })

const themeStore = useThemeStore()

// 配置 Schema
const configSchema = ref<any>(botConfigGroups)

// Monaco 配置
const monacoOptions = {
  minimap: { enabled: false },
  fontSize: 14,
  lineHeight: 24,
  fontFamily: "'Roboto Mono', 'Noto Sans SC', monospace",
  scrollBeyondLastLine: false,
  automaticLayout: true,
  padding: { top: 16, bottom: 16 }
}

// 计算是否有变更
const hasChanges = computed(() => {
  if (editorMode.value === 'source') {
    return sourceContent.value !== originalSource.value
  } else {
    // 简单比较，实际可能需要深比较
    return JSON.stringify(editedValues.value) !== JSON.stringify(originalParsed.value)
  }
})

// 初始化
onMounted(async () => {
  await loadConfig()
})

// 加载配置
async function loadConfig() {
  loading.value = true
  loadError.value = ''
  try {
    const res = await getConfigContent('bot_config.toml')
    if (res.success && res.data && res.data.success) {
      originalParsed.value = res.data.parsed
      editedValues.value = JSON.parse(JSON.stringify(res.data.parsed))
      sourceContent.value = res.data.content || ''
      originalSource.value = res.data.content || ''
      configPath.value = res.data.path
    } else {
      loadError.value = res.data?.error || res.error || '加载配置失败'
    }
  } catch (e) {
    loadError.value = '网络请求失败'
    console.error(e)
  } finally {
    loading.value = false
  }
}

// 更新字段值
function updateFieldValue(sectionOrFullKey: string, keyOrValue: string | any, value?: any) {
  // 支持两种调用方式：
  // 1. updateFieldValue(fullKey, value) - 来自 MainConfigEditor 的特殊编辑器
  // 2. updateFieldValue(section, key, value) - 传统方式
  
  if (value === undefined) {
    // 单key模式: (fullKey, value)
    const fullKey = sectionOrFullKey
    const val = keyOrValue
    editedValues.value[fullKey] = val
  } else {
    // 双key模式: (section, key, value)
    const section = sectionOrFullKey
    const key = keyOrValue
    if (!editedValues.value[section]) {
      editedValues.value[section] = {}
    }
    editedValues.value[section][key] = value
  }
}

// 保存配置
async function saveCurrentConfig() {
  saving.value = true
  try {
    let res
    if (editorMode.value === 'source') {
      res = await saveConfig(configPath.value, sourceContent.value)
    } else {
      res = await updateConfig(configPath.value, editedValues.value)
    }

    if (res.success && res.data && res.data.success) {
      showToast('配置已保存', 'success')
      // 重新加载以同步状态
      await loadConfig()
    } else {
      showToast(res.data?.error || res.error || '保存失败', 'error')
    }
  } catch (e) {
    showToast('保存请求失败', 'error')
    console.error(e)
  } finally {
    saving.value = false
  }
}

// 格式化源码
function formatSource() {
  // 简单的 INI 格式化逻辑，实际可以使用库
  // 这里暂时不做处理，Monaco 可能有插件
}

// Monaco 挂载
function onEditorMount(_editor: any) {
  // 可以在这里配置快捷键等
}

// 监听备份弹窗打开
watch(showBackupsModal, (val) => {
  if (val) fetchBackups()
})

// 获取备份列表
async function fetchBackups() {
  backupsLoading.value = true
  try {
    const res = await getConfigBackups(configPath.value)
    if (res.success && res.data && res.data.success) {
      backups.value = res.data.backups
    }
  } catch (e) {
    console.error(e)
  } finally {
    backupsLoading.value = false
  }
}

// 还原备份
async function restoreBackup(backup: any) {
  if (!confirm(`确定要还原到 ${formatDate(backup.created_at)} 的版本吗？当前未保存的更改将丢失。`)) return
  
  try {
    const res = await restoreConfigBackup(configPath.value, backup.name)
    if (res.success && res.data && res.data.success) {
      showToast('配置已还原', 'success')
      showBackupsModal.value = false
      await loadConfig()
    } else {
      showToast(res.data?.error || res.error || '还原失败', 'error')
    }
  } catch (e) {
    showToast('还原请求失败', 'error')
  }
}

// 工具函数
function formatDate(dateStr: string) {
  return new Date(dateStr).toLocaleString()
}

function formatSize(bytes: number) {
  if (bytes < 1024) return bytes + ' B'
  return (bytes / 1024).toFixed(1) + ' KB'
}

function showToast(msg: string, type: 'success' | 'error' = 'success') {
  toast.value = { visible: true, message: msg, type }
  setTimeout(() => {
    toast.value.visible = false
  }, 3000)
}
</script>

<style scoped>
.bot-config-view {
  display: flex;
  flex-direction: column;
  height: 100%;
  gap: 16px;
  animation: fadeIn 0.4s cubic-bezier(0.2, 0, 0, 1);
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}

/* 头部样式 */
.config-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 24px;
  background: var(--md-sys-color-surface-container);
  border-radius: 24px;
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
}

.header-icon {
  font-size: 24px;
}

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
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 12px;
}

/* 分段按钮 */
.m3-segmented-button {
  display: flex;
  border: 1px solid var(--md-sys-color-outline);
  border-radius: 20px;
  overflow: hidden;
  height: 40px;
}

.segment {
  background: transparent;
  border: none;
  padding: 0 16px;
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  font-weight: 500;
  color: var(--md-sys-color-on-surface-variant);
  cursor: pointer;
  transition: all 0.2s;
  border-right: 1px solid var(--md-sys-color-outline);
}

.segment:last-child {
  border-right: none;
}

.segment:hover {
  background: var(--md-sys-color-surface-container-highest);
}

.segment.active {
  background: var(--md-sys-color-secondary-container);
  color: var(--md-sys-color-on-secondary-container);
}

.segment .material-symbols-rounded {
  font-size: 18px;
}

/* 编辑器区域 */
.visual-editor, .source-editor {
  flex: 1;
  background: var(--md-sys-color-surface-container-low);
  border-radius: 24px;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  position: relative;
}

.visual-editor {
  padding: 24px;
  overflow-y: auto;
}

.source-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 24px;
  background: var(--md-sys-color-surface-container);
  border-bottom: 1px solid var(--md-sys-color-outline-variant);
}

.file-path {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  color: var(--md-sys-color-on-surface-variant);
  font-family: monospace;
}

.file-path .material-symbols-rounded {
  font-size: 16px;
}

.monaco-container {
  flex: 1;
  min-height: 0;
}

/* 状态展示 */
.loading-state, .error-state, .empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  gap: 16px;
  color: var(--md-sys-color-on-surface-variant);
}

.spinning {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
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
  padding: 12px 16px;
  background: var(--md-sys-color-surface-container-highest);
  border-radius: 12px;
}

.backup-name {
  font-size: 14px;
  font-weight: 500;
  color: var(--md-sys-color-on-surface);
  display: block;
}

.backup-meta {
  font-size: 12px;
  color: var(--md-sys-color-on-surface-variant);
}

/* Snackbar */
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
</style>
