<template>
  <div class="plugin-config-view">
    <!-- 顶部操作栏 -->
    <header class="config-header">
      <div class="header-left">
        <button class="m3-icon-button" @click="goBack">
          <span class="material-symbols-rounded">arrow_back</span>
        </button>
        <div class="header-icon-container">
          <span class="material-symbols-rounded header-icon">settings_applications</span>
        </div>
        <div class="header-info">
          <h1>{{ configInfo?.display_name || '插件配置' }}</h1>
          <p>{{ getShortPath(decodedPath) }}</p>
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
        <!-- 配置导航栏 -->
        <div class="config-nav-bar" v-if="configSchema.length > 1">
          <div class="nav-tabs">
            <button
              v-for="(section, idx) in configSchema"
              :key="section.name"
              class="nav-tab"
              :class="{ active: activeSection === idx }"
              @click="activeSection = idx"
            >
              {{ section.display_name || section.name }}
            </button>
          </div>
        </div>

        <!-- 配置内容 -->
        <div class="config-content">
          <div v-if="currentSection" class="config-section">
            <div class="section-header" v-if="configSchema.length > 1">
              <h3>{{ currentSection.display_name || currentSection.name }}</h3>
              <span class="field-count">{{ currentSection.fields.length }} 项配置</span>
            </div>
            <div class="fields-list">
              <div 
                v-for="field in currentSection.fields" 
                :key="field.full_key" 
                class="m3-card field-card"
                :class="{ inline: field.type === 'boolean' }"
              >
                <!-- Boolean 类型 -->
                <template v-if="field.type === 'boolean'">
                  <div class="field-left">
                    <div class="field-header">
                      <span class="field-name">{{ field.key }}</span>
                    </div>
                    <div v-if="field.description" class="field-description">
                      {{ field.description }}
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

                <!-- 其他类型 -->
                <template v-else>
                  <div class="field-header">
                    <span class="field-name">{{ field.key }}</span>
                    <span class="field-type-badge">{{ field.type }}</span>
                  </div>
                  <div v-if="field.description" class="field-description">
                    {{ field.description }}
                  </div>
                  
                  <!-- 数组/列表类型 -->
                  <div v-if="field.type === 'list' || field.type === 'array'" class="field-input-container">
                    <div class="array-input-wrapper">
                      <textarea
                        class="m3-input array-textarea"
                        :value="formatArrayValue(getFieldValue(field.full_key))"
                        @input="(e: any) => updateArrayValue(field.full_key, e.target.value)"
                        placeholder="每行一个值"
                      ></textarea>
                      <div class="input-hint">每行输入一个值</div>
                    </div>
                  </div>

                  <!-- 数字类型 -->
                  <div v-else-if="field.type === 'integer' || field.type === 'float'" class="field-input-container">
                    <input 
                      type="number"
                      class="m3-input"
                      :value="getFieldValue(field.full_key)"
                      @input="(e: any) => updateFieldValue(field.full_key, Number(e.target.value))"
                      :step="field.type === 'float' ? '0.1' : '1'"
                    >
                  </div>

                  <!-- 字符串/默认类型 -->
                  <div v-else class="field-input-container">
                    <input 
                      type="text"
                      class="m3-input"
                      :value="getFieldValue(field.full_key)"
                      @input="(e: any) => updateFieldValue(field.full_key, e.target.value)"
                    >
                  </div>
                </template>
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
          {{ decodedPath }}
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
                <span class="backup-meta">{{ formatDate(backup.time) }} · {{ formatSize(backup.size) }}</span>
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
import { 
  getConfigContent, 
  saveConfig, 
  updateConfig,
  getConfigBackups, 
  restoreConfigBackup 
} from '@/api'
import type { ConfigFileInfo } from '@/api'

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
const configSchema = ref<any[]>([])

// 备份
const showBackupsModal = ref(false)
const backupsLoading = ref(false)
const backups = ref<any[]>([])

// Toast
const toast = ref({ show: false, message: '', type: 'success' as 'success' | 'error' })

const isDarkMode = computed(() => themeStore.isDark)

// Monaco 配置
const monacoOptions = {
  minimap: { enabled: false },
  fontSize: 14,
  lineHeight: 24,
  fontFamily: "'JetBrains Mono', 'Fira Code', Consolas, monospace",
  scrollBeyondLastLine: false,
  automaticLayout: true,
  padding: { top: 16, bottom: 16 }
}

// 当前选中的配置节
const currentSection = computed(() => {
  if (configSchema.value.length > 0 && activeSection.value < configSchema.value.length) {
    return configSchema.value[activeSection.value]
  }
  return null
})

// 是否有变更
const hasChanges = computed(() => {
  if (editorMode.value === 'source') {
    return sourceContent.value !== originalSource.value
  } else {
    return JSON.stringify(editedValues.value) !== JSON.stringify(originalParsed.value)
  }
})

// 初始化
onMounted(() => {
  loadConfig()
})

function goBack() {
  router.back()
}

function getShortPath(path: string): string {
  const parts = path.split(/[/\\]/)
  if (parts.length > 3) {
    return '...' + parts.slice(-3).join('/')
  }
  return path
}

// 加载配置
async function loadConfig() {
  loading.value = true
  loadError.value = ''
  try {
    const res = await getConfigContent(decodedPath.value)
    if (res.success && res.parsed) {
      configInfo.value = {
        path: res.path,
        display_name: '未命名插件', // ConfigContentResponse doesn't have display_name
        description: '',
        type: 'plugin', // Add missing required property
        name: '' // Add missing required property
      }
      originalParsed.value = res.parsed
      editedValues.value = JSON.parse(JSON.stringify(res.parsed))
      sourceContent.value = res.content || ''
      originalSource.value = res.content || ''
      
      // 生成 Schema
      generateSchema(res.parsed)
    } else {
      loadError.value = res.error || '加载配置失败'
    }
  } catch (e) {
    loadError.value = '网络请求失败'
    console.error(e)
  } finally {
    loading.value = false
  }
}

// 简单的 Schema 生成逻辑
function generateSchema(data: any) {
  const schema: any[] = []
  
  // 遍历所有节
  for (const sectionKey in data) {
    const section = data[sectionKey]
    const fields: any[] = []
    
    for (const key in section) {
      const value = section[key]
      let type = 'string'
      
      if (typeof value === 'boolean') type = 'boolean'
      else if (typeof value === 'number') type = Number.isInteger(value) ? 'integer' : 'float'
      else if (Array.isArray(value)) type = 'list'
      
      fields.push({
        key,
        full_key: `${sectionKey}.${key}`,
        type,
        value,
        description: '' // 暂时没有描述
      })
    }
    
    schema.push({
      name: sectionKey,
      display_name: sectionKey,
      fields
    })
  }
  
  configSchema.value = schema
}

// 获取字段值
function getFieldValue(fullKey: string) {
  const [section, key] = fullKey.split('.')
  return editedValues.value[section]?.[key]
}

// 更新字段值
function updateFieldValue(fullKey: string, value: any) {
  const [section, key] = fullKey.split('.')
  if (!editedValues.value[section]) editedValues.value[section] = {}
  editedValues.value[section][key] = value
}

// 数组值处理
function formatArrayValue(val: any): string {
  if (Array.isArray(val)) return val.join('\n')
  return String(val || '')
}

function updateArrayValue(fullKey: string, val: string) {
  const arr = val.split('\n').map(s => s.trim()).filter(s => s)
  updateFieldValue(fullKey, arr)
}

// 保存配置
async function saveCurrentConfig() {
  saving.value = true
  try {
    let res
    if (editorMode.value === 'source') {
      res = await saveConfig(decodedPath.value, sourceContent.value)
    } else {
      res = await updateConfig(decodedPath.value, editedValues.value)
    }

    if (res.success) {
      showToast('配置已保存', 'success')
      await loadConfig()
    } else {
      showToast(res.error || '保存失败', 'error')
    }
  } catch (e) {
    showToast('保存请求失败', 'error')
  } finally {
    saving.value = false
  }
}

function formatSource() {
  // 占位
}

function onEditorMount(editor: any) {
  // 占位
}

// 备份相关
watch(showBackupsModal, (val) => {
  if (val) fetchBackups()
})

async function fetchBackups() {
  backupsLoading.value = true
  try {
    const res = await getConfigBackups(decodedPath.value)
    if (res.success && res.backups) {
      backups.value = res.backups
    }
  } catch (e) {
    console.error(e)
  } finally {
    backupsLoading.value = false
  }
}

async function restoreBackup(backup: any) {
  if (!confirm('确定要还原此版本吗？')) return
  try {
    const res = await restoreConfigBackup(decodedPath.value, backup.name)
    if (res.success) {
      showToast('还原成功', 'success')
      showBackupsModal.value = false
      await loadConfig()
    } else {
      showToast(res.error || '还原失败', 'error')
    }
  } catch (e) {
    showToast('还原请求失败', 'error')
  }
}

// 工具函数
function formatDate(ts: number) {
  return new Date(ts * 1000).toLocaleString()
}

function formatSize(bytes: number) {
  if (bytes < 1024) return bytes + ' B'
  return (bytes / 1024).toFixed(1) + ' KB'
}

function showToast(msg: string, type: 'success' | 'error' = 'success') {
  toast.value = { show: true, message: msg, type }
  setTimeout(() => {
    toast.value.show = false
  }, 3000)
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
  background: var(--md-sys-color-secondary-container);
  color: var(--md-sys-color-on-secondary-container);
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
  display: flex;
  flex-direction: column;
}

.config-nav-bar {
  padding: 16px 24px 0;
  border-bottom: 1px solid var(--md-sys-color-outline-variant);
  background: var(--md-sys-color-surface-container);
}

.nav-tabs {
  display: flex;
  gap: 24px;
  overflow-x: auto;
}

.nav-tab {
  background: transparent;
  border: none;
  padding: 12px 0;
  font-size: 14px;
  font-weight: 500;
  color: var(--md-sys-color-on-surface-variant);
  cursor: pointer;
  position: relative;
  white-space: nowrap;
}

.nav-tab.active {
  color: var(--md-sys-color-primary);
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

.config-content {
  flex: 1;
  overflow-y: auto;
  padding: 24px;
}

.section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16px;
}

.section-header h3 {
  font-size: 18px;
  font-weight: 500;
  color: var(--md-sys-color-on-surface);
  margin: 0;
}

.field-count {
  font-size: 12px;
  color: var(--md-sys-color-on-surface-variant);
  background: var(--md-sys-color-surface-container-highest);
  padding: 2px 8px;
  border-radius: 100px;
}

.fields-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.field-card {
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.field-card.inline {
  flex-direction: row;
  align-items: center;
  justify-content: space-between;
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

.field-type-badge {
  font-size: 11px;
  color: var(--md-sys-color-on-surface-variant);
  background: var(--md-sys-color-surface-container-highest);
  padding: 2px 6px;
  border-radius: 4px;
  text-transform: uppercase;
}

.field-description {
  font-size: 12px;
  color: var(--md-sys-color-on-surface-variant);
  line-height: 1.4;
}

.field-input-container {
  width: 100%;
}

.array-textarea {
  height: 100px;
  padding: 12px;
  font-family: monospace;
  resize: vertical;
}

.input-hint {
  font-size: 11px;
  color: var(--md-sys-color-on-surface-variant);
  margin-top: 4px;
}

/* 源码编辑器 */
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
