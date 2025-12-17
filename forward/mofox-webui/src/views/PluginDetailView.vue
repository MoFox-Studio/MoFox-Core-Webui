<template>
  <div class="plugin-detail-view">
    <!-- 返回按钮和标题 -->
    <header class="page-header">
      <button class="btn-back" @click="goBack">
        <Icon icon="lucide:arrow-left" />
        返回
      </button>
      <div v-if="currentPlugin" class="header-info">
        <h1>{{ currentPlugin.display_name }}</h1>
        <p>v{{ currentPlugin.version }} • {{ currentPlugin.author }}</p>
      </div>
      <div class="header-actions">
        <div v-if="isSystemPlugin(currentPlugin)" class="system-plugin-badge">
          <Icon icon="lucide:lock" />
          <span>系统插件 - 仅可查看</span>
        </div>
        <div v-if="!isSystemPlugin(currentPlugin)" class="toggle-switch">
          <input 
            type="checkbox" 
            id="plugin-enable-toggle"
            :checked="currentPlugin?.enabled"
            @change="handleTogglePlugin"
            :disabled="!currentPlugin?.loaded"
          />
          <label for="plugin-enable-toggle">
            {{ currentPlugin?.enabled ? '已启用' : '已禁用' }}
          </label>
        </div>
        <button 
          v-if="!currentPlugin?.loaded && !isSystemPlugin(currentPlugin)"
          class="btn btn-success" 
          @click="handleLoad"
        >
          <Icon icon="lucide:download" />
          加载
        </button>
        <button 
          v-if="currentPlugin?.loaded && !isSystemPlugin(currentPlugin)"
          class="btn btn-ghost" 
          @click="handleReload"
        >
          <Icon icon="lucide:refresh-cw" />
          重载
        </button>
        <button 
          v-if="currentPlugin?.loaded && !isSystemPlugin(currentPlugin)"
          class="btn btn-warning" 
          @click="handleUnload"
        >
          <Icon icon="lucide:power-off" />
          卸载
        </button>
        <button 
          v-if="!isSystemPlugin(currentPlugin)"
          class="btn btn-error" 
          @click="handleDelete"
        >
          <Icon icon="lucide:trash-2" />
          删除
        </button>
      </div>
    </header>

    <!-- 加载状态 -->
    <div v-if="detailLoading" class="loading-state">
      <Icon icon="lucide:loader-2" class="spinning" />
      加载插件详情...
    </div>

    <!-- 错误状态 -->
    <div v-else-if="error" class="error-state">
      <Icon icon="lucide:alert-circle" />
      {{ error }}
      <button class="btn btn-primary" @click="loadPluginDetail">重试</button>
    </div>

    <!-- 插件详情内容 -->
    <div v-else-if="currentPlugin" class="detail-content">
      <!-- Tab 导航 -->
      <div class="tabs">
        <button 
          v-for="tab in tabs" 
          :key="tab.value"
          class="tab"
          :class="{ active: activeTab === tab.value }"
          @click="activeTab = tab.value as 'overview' | 'components' | 'config'"
        >
          <Icon :icon="tab.icon" />
          {{ tab.label }}
        </button>
      </div>

      <!-- Tab 内容 -->
      <div class="tab-content">
        <!-- 概览 Tab -->
        <div v-if="activeTab === 'overview'" class="tab-pane">
          <div class="info-section">
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
                  <span v-if="currentPlugin.loaded" class="badge badge-success">已加载</span>
                  <span v-else class="badge badge-secondary">未加载</span>
                  <span v-if="currentPlugin.enabled" class="badge badge-primary">已启用</span>
                  <span v-else class="badge badge-secondary">已禁用</span>
                </div>
              </div>
              <div class="info-item">
                <div class="info-label">组件数量</div>
                <div class="info-value">{{ currentPlugin.components_count }}</div>
              </div>
            </div>
          </div>

          <div class="info-section">
            <h3 class="section-title">描述</h3>
            <p class="description">{{ currentPlugin.description || '暂无描述' }}</p>
          </div>

          <div v-if="currentPlugin.metadata" class="info-section">
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
            <Icon icon="lucide:puzzle" />
            <p>该插件没有组件</p>
          </div>
          <div v-else class="components-list">
            <div 
              v-for="component in currentComponents" 
              :key="component.name"
              class="component-card"
            >
              <div class="component-header">
                <div class="component-icon">
                  <Icon :icon="getComponentIcon(component.type)" />
                </div>
                <div class="component-info">
                  <h4>{{ component.name }}</h4>
                  <p class="component-type">{{ component.type }}</p>
                </div>
                <div class="component-actions">
                  <div v-if="!isSystemPlugin(currentPlugin)" class="toggle-switch">
                    <input 
                      type="checkbox" 
                      :id="`comp-${component.name}`"
                      :checked="component.enabled"
                      @change="handleToggleComponent(component)"
                    />
                    <label :for="`comp-${component.name}`">
                      {{ component.enabled ? '已启用' : '已禁用' }}
                    </label>
                  </div>
                  <div v-else class="component-locked">
                    <Icon icon="lucide:lock" />
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
          <div class="info-section">
            <h3 class="section-title">配置文件</h3>
            <div class="config-info">
              <div class="info-item">
                <div class="info-label">配置路径</div>
                <div class="info-value code">{{ currentPlugin.config.path }}</div>
              </div>
              <div class="info-item">
                <div class="info-label">文件状态</div>
                <div class="info-value">
                  <span v-if="currentPlugin.config.exists" class="badge badge-success">
                    <Icon icon="lucide:check" />
                    已存在
                  </span>
                  <span v-else class="badge badge-error">
                    <Icon icon="lucide:x" />
                    不存在
                  </span>
                </div>
              </div>
            </div>
            <button 
              v-if="currentPlugin.config.exists"
              class="btn btn-primary" 
              @click="goToConfig"
            >
              <Icon icon="lucide:settings" />
              打开配置编辑器
            </button>
            <div v-else class="config-not-found">
              <Icon icon="lucide:alert-circle" />
              <span>配置文件不存在</span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Toast 提示 -->
    <Transition name="toast">
      <div v-if="toast.show" :class="['toast', toast.type]">
        <Icon :icon="toast.type === 'success' ? 'lucide:check-circle' : 'lucide:alert-circle'" />
        {{ toast.message }}
      </div>
    </Transition>

    <!-- 确认对话框 -->
    <Transition name="modal">
      <div v-if="confirmDialog.show" class="modal-overlay" @click="confirmDialog.show = false">
        <div class="modal-content" @click.stop>
          <div class="modal-header">
            <Icon icon="lucide:alert-triangle" class="warning-icon" />
            <h3>{{ confirmDialog.title }}</h3>
          </div>
          <div class="modal-body">
            <p>{{ confirmDialog.message }}</p>
          </div>
          <div class="modal-footer">
            <button class="btn btn-ghost" @click="confirmDialog.show = false">取消</button>
            <button class="btn btn-primary" @click="confirmDialog.onConfirm">确认</button>
          </div>
        </div>
      </div>
    </Transition>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { Icon } from '@iconify/vue'
import { usePluginStore } from '@/stores/plugin'
import type { PluginComponent, PluginDetailInfo } from '@/api'

const router = useRouter()
const route = useRoute()
const pluginStore = usePluginStore()

const pluginName = route.params.pluginName as string

// Tab 选项
const tabs = [
  { label: '概览', value: 'overview', icon: 'lucide:info' },
  { label: '组件', value: 'components', icon: 'lucide:puzzle' },
  { label: '配置', value: 'config', icon: 'lucide:settings' },
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
  console.log('[PluginDetail] 插件数据:', JSON.parse(JSON.stringify(pluginStore.currentPlugin)))
  console.log('[PluginDetail] 组件数据:', JSON.parse(JSON.stringify(pluginStore.currentComponents)))
  
  // 检查每个组件的详细信息
  if (pluginStore.currentComponents && pluginStore.currentComponents.length > 0) {
    const firstComp = pluginStore.currentComponents[0]
    console.log('[PluginDetail] 第一个组件详情:', {
      name: firstComp?.name,
      type: firstComp?.type,
      enabled: firstComp?.enabled
    })
  }
  
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
    console.log('[PluginDetail] 禁用插件结果:', result)
    showToast(
      result.success ? '插件已禁用' : result.error || '操作失败',
      result.success ? 'success' : 'error'
    )
  } else {
    const result = await pluginStore.enablePluginAction(pluginName)
    console.log('[PluginDetail] 启用插件结果:', result)
    showToast(
      result.success ? '插件已启用' : result.error || '操作失败',
      result.success ? 'success' : 'error'
    )
  }
}

async function handleLoad() {
  showConfirm(
    '加载插件',
    `确定要加载插件 "${currentPlugin.value?.display_name}" 吗？`,
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
    `确定要重载插件 "${currentPlugin.value?.display_name}" 吗？`,
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
    `确定要卸载插件 "${currentPlugin.value?.display_name}" 吗？卸载后需要重新加载才能使用。`,
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
    `确定要删除插件 "${currentPlugin.value?.display_name}" 吗？此操作将删除插件的所有文件，且无法撤销！`,
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
    console.log('[PluginDetail] 禁用组件结果:', result)
    showToast(
      result.success ? `组件 ${component.name} 已禁用` : result.error || '操作失败',
      result.success ? 'success' : 'error'
    )
    if (result.success) {
      // 刷新插件详情以更新组件状态
      await loadPluginDetail()
    }
  } else {
    const result = await pluginStore.enableComponentAction(pluginName, component.name, component.type)
    console.log('[PluginDetail] 启用组件结果:', result)
    showToast(
      result.success ? `组件 ${component.name} 已启用` : result.error || '操作失败',
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
    'Command': 'lucide:terminal',
    'Action': 'lucide:zap',
    'EventHandler': 'lucide:radio',
    'Router': 'lucide:route',
    'Tool': 'lucide:wrench',
    'Prompt': 'lucide:message-square',
  }
  return icons[type] || 'lucide:puzzle'
}

function goBack() {
  router.push('/dashboard/plugin-manage')
}

function goToConfig() {
  // 使用配置文件的完整路径跳转
  if (currentPlugin.value?.config.path) {
    console.log('[PluginDetail] 跳转到配置编辑器:', currentPlugin.value.config.path)
    const encodedPath = encodeURIComponent(currentPlugin.value.config.path)
    router.push(`/dashboard/plugin-config/${encodedPath}`)
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
  padding: 24px;
  max-width: 1200px;
  margin: 0 auto;
}

/* 页面头部 */
.page-header {
  display: flex;
  align-items: center;
  gap: 20px;
  margin-bottom: 32px;
  flex-wrap: wrap;
}

.btn-back {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 16px;
  border-radius: var(--radius);
  background: var(--bg-primary);
  border: 1px solid var(--border-color);
  color: var(--text-secondary);
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all var(--transition);
}

.btn-back:hover {
  background: var(--bg-hover);
  color: var(--text-primary);
  border-color: var(--primary);
}

.header-info {
  flex: 1;
  min-width: 200px;
}

.header-info h1 {
  font-size: 28px;
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
  gap: 12px;
  align-items: center;
}

.system-plugin-badge {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 16px;
  background: linear-gradient(135deg, rgba(251, 191, 36, 0.15) 0%, rgba(245, 158, 11, 0.15) 100%);
  border: 1px solid rgba(251, 191, 36, 0.3);
  border-radius: var(--radius);
  color: rgb(251, 191, 36);
  font-size: 14px;
  font-weight: 500;
}

.system-plugin-badge svg {
  font-size: 16px;
}

/* Tab 导航 */
.tabs {
  display: flex;
  gap: 8px;
  margin-bottom: 24px;
  border-bottom: 2px solid var(--border-color);
}

.tab {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 20px;
  border: none;
  background: transparent;
  color: var(--text-secondary);
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all var(--transition);
  border-bottom: 2px solid transparent;
  margin-bottom: -2px;
}

.tab:hover {
  color: var(--text-primary);
  background: var(--bg-hover);
}

.tab.active {
  color: var(--primary);
  border-bottom-color: var(--primary);
}

/* Tab 内容 */
.tab-content {
  min-height: 400px;
}

.tab-pane {
  animation: fadeIn 0.3s ease;
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

/* 信息区块 */
.info-section {
  background: var(--bg-primary);
  border-radius: var(--radius-lg);
  padding: 24px;
  margin-bottom: 20px;
  border: 1px solid var(--border-color);
}

.section-title {
  font-size: 18px;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0 0 20px 0;
  padding-bottom: 12px;
  border-bottom: 1px solid var(--border-color);
}

.info-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 20px;
}

.info-item {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.info-label {
  font-size: 12px;
  font-weight: 600;
  color: var(--text-tertiary);
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.info-value {
  font-size: 14px;
  color: var(--text-primary);
  font-weight: 500;
  display: flex;
  gap: 8px;
  align-items: center;
  flex-wrap: wrap;
}

.info-value.code {
  font-family: 'Consolas', 'Monaco', monospace;
  background: var(--bg-tertiary);
  padding: 8px 12px;
  border-radius: var(--radius);
  font-size: 13px;
}

.description {
  font-size: 14px;
  color: var(--text-secondary);
  line-height: 1.8;
  margin: 0;
}

/* Badge */
.badge {
  padding: 4px 10px;
  border-radius: var(--radius-full);
  font-size: 11px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  display: inline-flex;
  align-items: center;
  gap: 4px;
}

.badge-success {
  background: rgba(34, 197, 94, 0.1);
  color: rgb(34, 197, 94);
}

.badge-primary {
  background: rgba(59, 130, 246, 0.1);
  color: rgb(59, 130, 246);
}

.badge-secondary {
  background: var(--bg-tertiary);
  color: var(--text-tertiary);
}

.badge-error {
  background: rgba(239, 68, 68, 0.1);
  color: rgb(239, 68, 68);
}

/* 组件列表 */
.components-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.component-card {
  background: var(--bg-secondary);
  border-radius: var(--radius-lg);
  padding: 20px;
  border: 1px solid var(--border-color);
  transition: all var(--transition);
}

.component-card:hover {
  border-color: var(--primary);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
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
  background: linear-gradient(135deg, var(--primary) 0%, var(--primary-dark) 100%);
  border-radius: var(--radius);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 20px;
  color: white;
}

.component-info {
  flex: 1;
  min-width: 0;
}

.component-info h4 {
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0 0 4px 0;
}

.component-type {
  font-size: 13px;
  color: var(--text-tertiary);
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
  padding: 8px 12px;
  background: rgba(156, 163, 175, 0.1);
  border-radius: var(--radius);
  color: var(--text-tertiary);
  font-size: 13px;
  font-weight: 500;
}

.component-locked svg {
  font-size: 14px;
}

.component-description {
  margin-top: 16px;
  padding-top: 16px;
  border-top: 1px solid var(--border-color);
  font-size: 14px;
  color: var(--text-secondary);
  line-height: 1.6;
}

/* 配置信息 */
.config-info {
  display: flex;
  flex-direction: column;
  gap: 20px;
  margin-bottom: 20px;
}

.config-not-found {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 16px;
  background: rgba(239, 68, 68, 0.1);
  border: 1px solid rgba(239, 68, 68, 0.2);
  border-radius: var(--radius);
  color: rgb(239, 68, 68);
  font-size: 14px;
  font-weight: 500;
}

.config-not-found svg {
  font-size: 18px;
}

/* Toggle Switch */
.toggle-switch {
  display: flex;
  align-items: center;
}

.toggle-switch input[type="checkbox"] {
  display: none;
}

.toggle-switch label {
  position: relative;
  display: flex;
  align-items: center;
  padding-left: 50px;
  cursor: pointer;
  user-select: none;
  font-size: 13px;
  font-weight: 500;
  color: var(--text-secondary);
  transition: color var(--transition);
}

.toggle-switch label::before {
  content: '';
  position: absolute;
  left: 0;
  width: 40px;
  height: 22px;
  background: var(--bg-tertiary);
  border-radius: var(--radius-full);
  transition: all var(--transition);
}

.toggle-switch label::after {
  content: '';
  position: absolute;
  left: 3px;
  width: 16px;
  height: 16px;
  background: white;
  border-radius: 50%;
  transition: all var(--transition);
  top: 50%;
  transform: translateY(-50%);
}

.toggle-switch input[type="checkbox"]:checked + label::before {
  background: var(--primary);
}

.toggle-switch input[type="checkbox"]:checked + label::after {
  left: 21px;
}

.toggle-switch input[type="checkbox"]:checked + label {
  color: var(--primary);
}

.toggle-switch input[type="checkbox"]:disabled + label {
  opacity: 0.5;
  cursor: not-allowed;
}

/* 按钮 */
.btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 10px 20px;
  border-radius: var(--radius);
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all var(--transition);
  border: none;
  white-space: nowrap;
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
  background: var(--primary-dark);
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(59, 130, 246, 0.3);
}

.btn-ghost {
  background: transparent;
  color: var(--text-secondary);
  border: 1px solid var(--border-color);
}

.btn-ghost:hover:not(:disabled) {
  background: var(--bg-hover);
  color: var(--text-primary);
  border-color: var(--primary);
}

.btn-warning {
  background: rgba(251, 191, 36, 0.1);
  color: rgb(251, 191, 36);
  border: 1px solid rgba(251, 191, 36, 0.2);
}

.btn-warning:hover:not(:disabled) {
  background: rgb(251, 191, 36);
  color: white;
  border-color: rgb(251, 191, 36);
}

.btn-error {
  background: rgba(239, 68, 68, 0.1);
  color: rgb(239, 68, 68);
  border: 1px solid rgba(239, 68, 68, 0.2);
}

.btn-error:hover:not(:disabled) {
  background: rgb(239, 68, 68);
  color: white;
  border-color: rgb(239, 68, 68);
}

/* 状态 */
.loading-state,
.error-state,
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 80px 20px;
  color: var(--text-secondary);
  font-size: 16px;
  gap: 16px;
}

.loading-state svg,
.error-state svg,
.empty-state svg {
  font-size: 48px;
  color: var(--text-tertiary);
}

/* Toast */
.toast {
  position: fixed;
  bottom: 24px;
  right: 24px;
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 16px 20px;
  border-radius: var(--radius);
  background: var(--bg-secondary);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.2);
  color: var(--text-primary);
  font-size: 14px;
  font-weight: 500;
  z-index: 1000;
  min-width: 300px;
}

.toast.success {
  border-left: 4px solid rgb(34, 197, 94);
}

.toast.error {
  border-left: 4px solid rgb(239, 68, 68);
}

.toast-enter-active,
.toast-leave-active {
  transition: all 0.3s ease;
}

.toast-enter-from,
.toast-leave-to {
  opacity: 0;
  transform: translateY(20px);
}

/* Modal */
.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  padding: 20px;
}

.modal-content {
  background: var(--bg-secondary);
  border-radius: var(--radius-lg);
  max-width: 480px;
  width: 100%;
  overflow: hidden;
}

.modal-header {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 24px;
  border-bottom: 1px solid var(--border-color);
}

.warning-icon {
  font-size: 24px;
  color: rgb(234, 179, 8);
}

.modal-header h3 {
  font-size: 20px;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0;
}

.modal-body {
  padding: 24px;
}

.modal-body p {
  font-size: 14px;
  color: var(--text-secondary);
  line-height: 1.6;
  margin: 0;
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  padding: 20px 24px;
  border-top: 1px solid var(--border-color);
}

.modal-enter-active,
.modal-leave-active {
  transition: all 0.3s ease;
}

.modal-enter-from,
.modal-leave-to {
  opacity: 0;
}

.modal-enter-from .modal-content,
.modal-leave-to .modal-content {
  transform: scale(0.9);
}

/* Animations */
.spinning {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}
</style>
