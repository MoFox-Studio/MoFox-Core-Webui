<template>
  <div class="plugin-detail-view">
    <!-- 返回按钮和标题 -->
    <header class="page-header">
      <button class="m3-button text" @click="goBack">
        <span class="material-symbols-rounded">arrow_back</span>
        返回
      </button>
      <div v-if="currentPlugin" class="header-info">
        <h1>{{ currentPlugin.display_name }}</h1>
        <p>v{{ currentPlugin.version }} • {{ currentPlugin.author }}</p>
      </div>
      <div class="header-actions">
        <div v-if="isSystemPlugin(currentPlugin)" class="system-plugin-badge">
          <span class="material-symbols-rounded">lock</span>
          <span>系统插件 - 仅可查看</span>
        </div>
        <div v-if="!isSystemPlugin(currentPlugin)" class="m3-switch-container">
          <label class="m3-switch">
            <input 
              type="checkbox" 
              id="plugin-enable-toggle"
              :checked="currentPlugin?.enabled"
              @change="handleTogglePlugin"
              :disabled="!currentPlugin?.loaded"
            />
            <span class="slider"></span>
          </label>
          <span class="switch-label">
            {{ currentPlugin?.enabled ? '已启用' : '已禁用' }}
          </span>
        </div>
        <button 
          v-if="!currentPlugin?.loaded && !isSystemPlugin(currentPlugin)"
          class="m3-button filled" 
          @click="handleLoad"
        >
          <span class="material-symbols-rounded">download</span>
          加载
        </button>
        <button 
          v-if="currentPlugin?.loaded && !isSystemPlugin(currentPlugin)"
          class="m3-button tonal" 
          @click="handleReload"
        >
          <span class="material-symbols-rounded">refresh</span>
          重载
        </button>
        <button 
          v-if="currentPlugin?.loaded && !isSystemPlugin(currentPlugin)"
          class="m3-button tonal error" 
          @click="handleUnload"
        >
          <span class="material-symbols-rounded">power_settings_new</span>
          卸载
        </button>
        <button 
          v-if="!isSystemPlugin(currentPlugin)"
          class="m3-button text error" 
          @click="handleDelete"
        >
          <span class="material-symbols-rounded">delete</span>
          删除
        </button>
      </div>
    </header>

    <!-- 加载状态 -->
    <div v-if="detailLoading" class="loading-state">
      <span class="material-symbols-rounded spinning loading-icon">progress_activity</span>
      <p>加载插件详情...</p>
    </div>

    <!-- 错误状态 -->
    <div v-else-if="error" class="error-state">
      <span class="material-symbols-rounded error-icon">error</span>
      <p>{{ error }}</p>
      <button class="m3-button filled" @click="loadPluginDetail">重试</button>
    </div>

    <!-- 插件详情内容 -->
    <div v-else-if="currentPlugin" class="detail-content">
      <!-- Tab 导航 -->
      <div class="m3-tabs">
        <button 
          v-for="tab in tabs" 
          :key="tab.value"
          class="m3-tab-item"
          :class="{ active: activeTab === tab.value }"
          @click="activeTab = tab.value as 'overview' | 'components' | 'config'"
        >
          <span class="material-symbols-rounded">{{ tab.icon }}</span>
          {{ tab.label }}
        </button>
      </div>

      <!-- Tab 内容 -->
      <div class="tab-content">
        <!-- 概览 Tab -->
        <div v-if="activeTab === 'overview'" class="tab-pane">
          <div class="m3-card info-section">
            <h3 class="section-title">基本信息</h3>
            <div class="info-grid">
              <div class="info-item">
                <div class="info-label">插件名称</div>
                <div class="info-value">{{ currentPlugin.name }}</div>
              </div>
              <div class="info-item">
                <div class="info-label">显示名称</div>
                <div class="info-value">{{ currentPlugin.display_name }}</div>
              </div>
              <div class="info-item">
                <div class="info-label">版本</div>
                <div class="info-value">{{ currentPlugin.version }}</div>
              </div>
              <div class="info-item">
                <div class="info-label">作者</div>
                <div class="info-value">{{ currentPlugin.author }}</div>
              </div>
              <div class="info-item">
                <div class="info-label">状态</div>
                <div class="info-value">
                  <span v-if="currentPlugin.loaded" class="m3-badge success">已加载</span>
                  <span v-else class="m3-badge secondary">未加载</span>
                  <span v-if="currentPlugin.enabled" class="m3-badge primary">已启用</span>
                  <span v-else class="m3-badge secondary">已禁用</span>
                </div>
              </div>
              <div class="info-item">
                <div class="info-label">组件数量</div>
                <div class="info-value">{{ currentPlugin.components_count }}</div>
              </div>
            </div>
          </div>

          <div class="m3-card info-section">
            <h3 class="section-title">描述</h3>
            <p class="description">{{ currentPlugin.description || '暂无描述' }}</p>
          </div>

          <div v-if="currentPlugin.metadata && Object.keys(currentPlugin.metadata).length > 0" class="m3-card info-section">
            <h3 class="section-title">元数据</h3>
            <div class="info-grid">
              <div v-for="(value, key) in currentPlugin.metadata" :key="key" class="info-item">
                <div class="info-label">{{ key }}</div>
                <div class="info-value">{{ value }}</div>
              </div>
            </div>
          </div>
        </div>

        <!-- 组件 Tab -->
        <div v-if="activeTab === 'components'" class="tab-pane">
          <div v-if="currentComponents.length === 0" class="empty-state">
            <span class="material-symbols-rounded empty-icon">extension_off</span>
            <p>该插件没有组件</p>
          </div>
          <div v-else class="components-list">
            <div 
              v-for="(component, index) in currentComponents" 
              :key="component.name + index"
              class="m3-card component-card"
            >
              <div class="component-header">
                <div class="component-icon">
                  <span class="material-symbols-rounded">{{ getComponentIcon(component.type) }}</span>
                </div>
                <div class="component-info">
                  <h4>{{ component.name }}</h4>
                  <p class="component-type">{{ component.type }}</p>
                </div>
                <div class="component-actions">
                  <div v-if="!isSystemPlugin(currentPlugin)" class="m3-switch-container">
                    <label class="m3-switch">
                      <input 
                        type="checkbox" 
                        :id="`comp-${index}`"
                        :checked="component.enabled"
                        @change="handleToggleComponent(component)"
                      />
                      <span class="slider"></span>
                    </label>
                    <span class="switch-label">
                      {{ component.enabled ? '已启用' : '已禁用' }}
                    </span>
                  </div>
                  <div v-else class="component-locked">
                    <span class="material-symbols-rounded">lock</span>
                    <span>{{ component.enabled ? '已启用' : '已禁用' }}</span>
                  </div>
                </div>
              </div>
              <div v-if="component.description" class="component-description">
                {{ component.description }}
              </div>
            </div>
          </div>
        </div>

        <!-- 配置 Tab -->
        <div v-if="activeTab === 'config'" class="tab-pane">
          <div class="m3-card info-section">
            <h3 class="section-title">配置文件</h3>
            <div class="config-info">
              <div class="info-item">
                <div class="info-label">配置路径</div>
                <div class="info-value code">{{ currentPlugin.config.path }}</div>
              </div>
              <div class="info-item">
                <div class="info-label">文件状态</div>
                <div class="info-value">
                  <span v-if="currentPlugin.config.exists" class="m3-badge success">
                    <span class="material-symbols-rounded">check</span>
                    已存在
                  </span>
                  <span v-else class="m3-badge error">
                    <span class="material-symbols-rounded">close</span>
                    不存在
                  </span>
                </div>
              </div>
            </div>
            <button 
              v-if="currentPlugin.config.exists"
              class="m3-button filled" 
              @click="goToConfig"
            >
              <span class="material-symbols-rounded">settings</span>
              打开配置编辑器
            </button>
            <div v-else class="config-not-found">
              <span class="material-symbols-rounded">error</span>
              <span>配置文件不存在</span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Toast 提示 -->
    <Transition name="toast">
      <div v-if="toast.show" class="m3-snackbar" :class="toast.type">
        <span class="material-symbols-rounded">
          {{ toast.type === 'success' ? 'check_circle' : 'error' }}
        </span>
        {{ toast.message }}
      </div>
    </Transition>

    <!-- 确认对话框 -->
    <ConfirmDialog
      :visible="confirmDialog.show"
      :title="confirmDialog.title"
      :message="confirmDialog.message"
      @confirm="confirmDialog.onConfirm"
      @cancel="confirmDialog.show = false"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { usePluginStore } from '@/stores/plugin'
import type { PluginComponent, PluginDetailInfo } from '@/api'
import ConfirmDialog from '@/components/ConfirmDialog.vue'

const router = useRouter()
const route = useRoute()
const pluginStore = usePluginStore()

const pluginName = route.params.pluginName as string

// Tab 选项
const tabs = [
  { label: '概览', value: 'overview', icon: 'info' },
  { label: '组件', value: 'components', icon: 'extension' },
  { label: '配置', value: 'config', icon: 'settings' },
]

// 状态
const activeTab = ref<'overview' | 'components' | 'config'>('overview')
const detailLoading = ref(false)
const error = ref('')

// Toast 提示
const toast = ref({
  show: false,
  message: '',
  type: 'success' as 'success' | 'error'
})

// 确认对话框
const confirmDialog = ref({
  show: false,
  title: '',
  message: '',
  onConfirm: () => {}
})

// 计算属性
const currentPlugin = computed(() => pluginStore.currentPlugin)
const currentComponents = computed(() => pluginStore.currentComponents)

// 判断是否为系统插件
const SYSTEM_PLUGINS = [
  'Affinity Flow Chatter',
  'Kokoro Flow Chatter',
  'napcat_adapter_plugin',
  'Emoji插件 (Emoji Actions)'
]

// 判断是否为系统插件
function isSystemPlugin(plugin: PluginDetailInfo | null): boolean {
  if (!plugin) return false
  return SYSTEM_PLUGINS.includes(plugin.display_name)
}

// 方法
function showToast(message: string, type: 'success' | 'error' = 'success') {
  toast.value = { show: true, message, type }
  setTimeout(() => {
    toast.value.show = false
  }, 3000)
}

function showConfirm(title: string, message: string, onConfirm: () => void) {
  confirmDialog.value = {
    show: true,
    title,
    message,
    onConfirm: () => {
      onConfirm()
      confirmDialog.value.show = false
    }
  }
}

async function loadPluginDetail() {
  console.log('[PluginDetail] 开始加载插件详情:', pluginName)
  detailLoading.value = true
  error.value = ''
  
  const success = await pluginStore.fetchPluginDetail(pluginName)
  
  console.log('[PluginDetail] 插件详情加载结果:', success)
  
  if (!success && pluginStore.error) {
    error.value = pluginStore.error
  }
  
  detailLoading.value = false
}

async function handleTogglePlugin() {
  if (!currentPlugin.value) return
  
  console.log('[PluginDetail] 切换插件状态:', currentPlugin.value.enabled ? '禁用' : '启用')
  
  if (currentPlugin.value.enabled) {
    const result = await pluginStore.disablePluginAction(pluginName)
    showToast(
      result.success ? '插件已禁用' : result.error || '操作失败',
      result.success ? 'success' : 'error'
    )
  } else {
    const result = await pluginStore.enablePluginAction(pluginName)
    showToast(
      result.success ? '插件已启用' : result.error || '操作失败',
      result.success ? 'success' : 'error'
    )
  }
}

async function handleLoad() {
  showConfirm(
    '加载插件',
    `确定要加载插件 "${pluginName}" 吗？`,
    async () => {
      const result = await pluginStore.loadPluginAction(pluginName)
      showToast(
        result.success ? '插件加载成功' : result.error || '加载失败',
        result.success ? 'success' : 'error'
      )
      if (result.success) {
        await loadPluginDetail()
      }
    }
  )
}

async function handleReload() {
  showConfirm(
    '重载插件',
    `确定要重载插件 "${pluginName}" 吗？`,
    async () => {
      const result = await pluginStore.reloadPluginAction(pluginName)
      showToast(
        result.success ? '插件重载成功' : result.error || '重载失败',
        result.success ? 'success' : 'error'
      )
      if (result.success) {
        await loadPluginDetail()
      }
    }
  )
}

async function handleUnload() {
  showConfirm(
    '卸载插件',
    `确定要卸载插件 "${pluginName}" 吗？卸载后需要重新加载才能使用。`,
    async () => {
      const result = await pluginStore.unloadPluginAction(pluginName)
      showToast(
        result.success ? '插件已卸载' : result.error || '卸载失败',
        result.success ? 'success' : 'error'
      )
      if (result.success) {
        goBack()
      }
    }
  )
}

async function handleDelete() {
  showConfirm(
    '删除插件',
    `确定要删除插件 "${pluginName}" 吗？此操作将删除插件的所有文件，且无法撤销！`,
    async () => {
      const result = await pluginStore.deletePluginAction(pluginName)
      showToast(
        result.success ? '插件已删除' : result.error || '删除失败',
        result.success ? 'success' : 'error'
      )
      if (result.success) {
        goBack()
      }
    }
  )
}

async function handleToggleComponent(component: PluginComponent) {
  console.log('[PluginDetail] 切换组件状态:', component.name, component.type, component.enabled ? '禁用' : '启用')
  
  if (component.enabled) {
    const result = await pluginStore.disableComponentAction(pluginName, component.name, component.type)
    showToast(
      result.success ? '组件已禁用' : result.error || '操作失败',
      result.success ? 'success' : 'error'
    )
    if (result.success) {
      // 刷新插件详情以更新组件状态
      await loadPluginDetail()
    }
  } else {
    const result = await pluginStore.enableComponentAction(pluginName, component.name, component.type)
    showToast(
      result.success ? '组件已启用' : result.error || '操作失败',
      result.success ? 'success' : 'error'
    )
    if (result.success) {
      // 刷新插件详情以更新组件状态
      await loadPluginDetail()
    }
  }
}

function getComponentIcon(type: string): string {
  const icons: Record<string, string> = {
    'Command': 'terminal',
    'Action': 'bolt',
    'EventHandler': 'sensors',
    'Router': 'alt_route',
    'Tool': 'build',
    'Prompt': 'chat',
  }
  return icons[type] || 'extension'
}

function goBack() {
  router.push('/dashboard/plugin-manage')
}

function goToConfig() {
  // 使用配置文件的完整路径跳转
  if (currentPlugin.value?.name) {
    const configPath = `plugins/${currentPlugin.value.name}/config.toml`
    console.log('[PluginDetail] 跳转到配置编辑器:', configPath)
    router.push({
      name: 'PluginConfigView',
      params: { path: configPath }
    })
  } else {
    console.warn('[PluginDetail] 配置文件路径不存在')
    showToast('配置文件路径不存在', 'error')
  }
}

onMounted(() => {
  loadPluginDetail()
})
</script>

<style scoped>
.plugin-detail-view {
  height: 100%;
  display: flex;
  flex-direction: column;
  gap: 16px;
  animation: fadeIn 0.4s cubic-bezier(0.2, 0, 0, 1);
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}

/* 页面头部 */
.page-header {
  display: flex;
  align-items: center;
  gap: 20px;
  padding: 0 8px;
  flex-wrap: wrap;
}

.header-info {
  flex: 1;
  min-width: 200px;
}

.header-info h1 {
  font-size: 24px;
  font-weight: 400;
  color: var(--md-sys-color-on-surface);
  margin: 0 0 4px 0;
}

.header-info p {
  font-size: 14px;
  color: var(--md-sys-color-on-surface-variant);
  margin: 0;
}

.header-actions {
  display: flex;
  gap: 12px;
  align-items: center;
}

.system-plugin-badge {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 16px;
  background: var(--md-sys-color-tertiary-container);
  border-radius: 8px;
  color: var(--md-sys-color-on-tertiary-container);
  font-size: 14px;
  font-weight: 500;
}

.system-plugin-badge .material-symbols-rounded {
  font-size: 18px;
}

.m3-switch-container {
  display: flex;
  align-items: center;
  gap: 12px;
}

.switch-label {
  font-size: 14px;
  color: var(--md-sys-color-on-surface);
}

.m3-button.error {
  color: var(--md-sys-color-error);
}

.m3-button.tonal.error {
  background: var(--md-sys-color-error-container);
  color: var(--md-sys-color-on-error-container);
}

/* Tab 导航 */
.m3-tabs {
  display: flex;
  gap: 8px;
  border-bottom: 1px solid var(--md-sys-color-outline-variant);
  padding-bottom: 0;
}

.m3-tab-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 24px;
  border: none;
  background: transparent;
  color: var(--md-sys-color-on-surface-variant);
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  position: relative;
  transition: all 0.2s;
}

.m3-tab-item:hover {
  background: var(--md-sys-color-surface-container-highest);
  color: var(--md-sys-color-on-surface);
}

.m3-tab-item.active {
  color: var(--md-sys-color-primary);
}

.m3-tab-item.active::after {
  content: '';
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  height: 3px;
  background: var(--md-sys-color-primary);
  border-radius: 3px 3px 0 0;
}

.m3-tab-item .material-symbols-rounded {
  font-size: 18px;
}

/* Tab 内容 */
.tab-content {
  flex: 1;
  overflow-y: auto;
  padding: 8px;
}

.tab-pane {
  display: flex;
  flex-direction: column;
  gap: 16px;
  animation: fadeIn 0.3s ease;
}

/* 信息区块 */
.info-section {
  padding: 24px;
}

.section-title {
  font-size: 18px;
  font-weight: 500;
  color: var(--md-sys-color-on-surface);
  margin: 0 0 20px 0;
  padding-bottom: 12px;
  border-bottom: 1px solid var(--md-sys-color-outline-variant);
}

.info-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 24px;
}

.info-item {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.info-label {
  font-size: 12px;
  font-weight: 500;
  color: var(--md-sys-color-on-surface-variant);
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.info-value {
  font-size: 14px;
  color: var(--md-sys-color-on-surface);
  display: flex;
  gap: 8px;
  align-items: center;
  flex-wrap: wrap;
}

.info-value.code {
  font-family: 'JetBrains Mono', monospace;
  background: var(--md-sys-color-surface-container-highest);
  padding: 8px 12px;
  border-radius: 8px;
  font-size: 13px;
}

.description {
  font-size: 14px;
  color: var(--md-sys-color-on-surface-variant);
  line-height: 1.6;
  margin: 0;
}

/* Badge */
.m3-badge {
  padding: 4px 12px;
  border-radius: 8px;
  font-size: 12px;
  font-weight: 500;
  display: inline-flex;
  align-items: center;
  gap: 6px;
}

.m3-badge.success {
  background: var(--md-sys-color-primary-container);
  color: var(--md-sys-color-on-primary-container);
}

.m3-badge.primary {
  background: var(--md-sys-color-secondary-container);
  color: var(--md-sys-color-on-secondary-container);
}

.m3-badge.secondary {
  background: var(--md-sys-color-surface-container-highest);
  color: var(--md-sys-color-on-surface-variant);
}

.m3-badge.error {
  background: var(--md-sys-color-error-container);
  color: var(--md-sys-color-on-error-container);
}

.m3-badge .material-symbols-rounded {
  font-size: 16px;
}

/* 组件列表 */
.components-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.component-card {
  padding: 20px;
}

.component-header {
  display: flex;
  align-items: center;
  gap: 16px;
}

.component-icon {
  width: 40px;
  height: 40px;
  min-width: 40px;
  background: var(--md-sys-color-secondary-container);
  color: var(--md-sys-color-on-secondary-container);
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.component-icon .material-symbols-rounded {
  font-size: 20px;
}

.component-info {
  flex: 1;
  min-width: 0;
}

.component-info h4 {
  font-size: 16px;
  font-weight: 500;
  color: var(--md-sys-color-on-surface);
  margin: 0 0 4px 0;
}

.component-type {
  font-size: 12px;
  color: var(--md-sys-color-on-surface-variant);
  margin: 0;
}

.component-actions {
  display: flex;
  gap: 12px;
  align-items: center;
}

.component-locked {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 12px;
  background: var(--md-sys-color-surface-container-highest);
  border-radius: 8px;
  color: var(--md-sys-color-on-surface-variant);
  font-size: 12px;
  font-weight: 500;
}

.component-locked .material-symbols-rounded {
  font-size: 16px;
}

.component-description {
  margin-top: 16px;
  padding-top: 16px;
  border-top: 1px solid var(--md-sys-color-outline-variant);
  font-size: 14px;
  color: var(--md-sys-color-on-surface-variant);
  line-height: 1.6;
}

/* 配置信息 */
.config-info {
  display: flex;
  flex-direction: column;
  gap: 20px;
  margin-bottom: 24px;
}

.config-not-found {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 16px;
  background: var(--md-sys-color-error-container);
  border-radius: 8px;
  color: var(--md-sys-color-on-error-container);
  font-size: 14px;
  font-weight: 500;
}

.config-not-found .material-symbols-rounded {
  font-size: 18px;
}

/* 状态 */
.loading-state,
.error-state,
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px 20px;
  color: var(--md-sys-color-on-surface-variant);
  gap: 16px;
}

.loading-icon,
.error-icon,
.empty-icon {
  font-size: 48px;
  opacity: 0.5;
}

.error-state {
  color: var(--md-sys-color-error);
}

.spinning {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
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
