<!--
  @file PluginManageView.vue
  @description 插件管理页面
  
  功能说明：
  1. 查看所有插件的加载状态和运行状态
  2. 插件加载/卸载/重载操作
  3. 插件启用/禁用控制
  4. 插件删除功能
  5. 扫描新插件
  
  统计信息：
  - 插件总数、已加载、已启用、加载失败数量
  
  筛选功能：
  - 按状态筛选（全部/已加载/已启用/已禁用/失败）
  - 关键词搜索
  
  特殊处理：
  - 系统插件标记为只读
  - 失败插件单独展示错误信息
-->
<template>
  <div class="plugin-manage-view">
    <!-- 顶部标题栏：标题、扫描、重载、刷新按钮 -->
    <header class="page-header">
      <div class="header-content">
        <h1>插件管理</h1>
        <p class="subtitle">管理系统插件的加载、启用和配置</p>
      </div>
      <div class="header-actions">
        <button class="m3-button text" @click="handleScanPlugins" :disabled="loading">
          <span class="material-symbols-rounded">search_check</span>
          扫描新插件
        </button>
        <button class="m3-button text" @click="handleReloadAll" :disabled="loading">
          <span class="material-symbols-rounded">refresh</span>
          重载所有
        </button>
        <button class="m3-button filled" @click="refreshPluginList" :disabled="loading">
          <span class="material-symbols-rounded" :class="{ spinning: loading }">
            {{ loading ? 'progress_activity' : 'sync' }}
          </span>
          刷新列表
        </button>
      </div>
    </header>

    <!-- 统计卡片 -->
    <div class="stats-grid">
      <div class="m3-card stat-card primary-container">
        <div class="stat-icon">
          <span class="material-symbols-rounded">extension</span>
        </div>
        <div class="stat-content">
          <div class="stat-value">{{ pluginStore.stats.total }}</div>
          <div class="stat-label">插件总数</div>
        </div>
      </div>
      <div class="m3-card stat-card success-container">
        <div class="stat-icon">
          <span class="material-symbols-rounded">check_circle</span>
        </div>
        <div class="stat-content">
          <div class="stat-value">{{ pluginStore.stats.loaded }}</div>
          <div class="stat-label">已加载</div>
        </div>
      </div>
      <div class="m3-card stat-card tertiary-container">
        <div class="stat-icon">
          <span class="material-symbols-rounded">bolt</span>
        </div>
        <div class="stat-content">
          <div class="stat-value">{{ pluginStore.stats.enabled }}</div>
          <div class="stat-label">已启用</div>
        </div>
      </div>
      <div class="m3-card stat-card error-container">
        <div class="stat-icon">
          <span class="material-symbols-rounded">error</span>
        </div>
        <div class="stat-content">
          <div class="stat-value">{{ pluginStore.stats.failed }}</div>
          <div class="stat-label">加载失败</div>
        </div>
      </div>
    </div>

    <!-- 筛选和搜索栏 -->
    <div class="filter-bar">
      <div class="filter-chips">
        <button 
          v-for="filter in filters" 
          :key="filter.value"
          class="m3-filter-chip"
          :class="{ selected: pluginStore.statusFilter === filter.value }"
          @click="pluginStore.setStatusFilter(filter.value)"
        >
          <span v-if="pluginStore.statusFilter === filter.value" class="material-symbols-rounded check-icon">check</span>
          {{ filter.label }}
        </button>
      </div>
      <div class="search-box">
        <span class="material-symbols-rounded search-icon">search</span>
        <input 
          type="text" 
          class="m3-input"
          placeholder="搜索插件名称或描述..." 
          v-model="pluginStore.searchKeyword"
        />
      </div>
    </div>

    <!-- 失败插件区域 -->
    <div v-if="!loading && pluginStore.failedPlugins.length > 0" class="section-container">
      <div class="section-header error-text">
        <span class="material-symbols-rounded">error</span>
        <h2>加载失败 ({{ pluginStore.failedPlugins.length }})</h2>
      </div>
      <div class="plugin-grid">
        <div 
          v-for="plugin in pluginStore.failedPlugins" 
          :key="plugin.name"
          class="m3-card plugin-card error-card"
        >
          <div class="card-content">
            <div class="card-header">
              <div class="plugin-icon error">
                <span class="material-symbols-rounded">error</span>
              </div>
              <div class="header-text">
                <h3>{{ plugin.display_name }}</h3>
                <p>v{{ plugin.version }} • {{ plugin.author }}</p>
              </div>
            </div>
            <div class="plugin-description">
              {{ plugin.description || '暂无描述' }}
            </div>
            <div class="error-message">
              <span class="material-symbols-rounded">warning</span>
              {{ plugin.error || '未知错误' }}
            </div>
          </div>
          <div class="card-actions">
            <button class="m3-button text" @click="handleReloadPlugin(plugin.name)">
              <span class="material-symbols-rounded">refresh</span>
              重试
            </button>
            <button 
              v-if="!isSystemPlugin(plugin)"
              class="m3-button text error" 
              @click="handleDeletePlugin(plugin.name, plugin.display_name)"
            >
              <span class="material-symbols-rounded">delete</span>
              删除
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- 插件列表 -->
    <div class="plugin-list-container">
      <div v-if="loading" class="loading-state">
        <span class="material-symbols-rounded spinning loading-icon">progress_activity</span>
        <p>加载插件列表...</p>
      </div>
      <div v-else-if="error" class="error-state">
        <span class="material-symbols-rounded error-icon">error</span>
        <p>{{ error }}</p>
        <button class="m3-button filled" @click="refreshPluginList">重试</button>
      </div>
      <div v-else-if="pluginStore.filteredPlugins.length === 0 && pluginStore.failedPlugins.length === 0" class="empty-state">
        <span class="material-symbols-rounded empty-icon">extension_off</span>
        <p>没有找到插件</p>
        <span class="hint">尝试调整筛选条件或扫描新插件</span>
      </div>
      <div v-else-if="pluginStore.filteredPlugins.length > 0">
        <div class="section-header" v-if="pluginStore.failedPlugins.length > 0">
          <span class="material-symbols-rounded success-text">check_circle</span>
          <h2>正常插件 ({{ pluginStore.filteredPlugins.length }})</h2>
        </div>
        <div class="plugin-grid">
          <div 
            v-for="plugin in pluginStore.filteredPlugins" 
            :key="plugin.name"
            class="m3-card plugin-card"
            :class="{ 'disabled': !plugin.loaded }"
            @click="plugin.loaded ? goToDetail(plugin.name) : null"
          >
            <div class="card-content">
              <div class="card-header">
                <div class="plugin-icon">
                  <span class="material-symbols-rounded">{{ plugin.error ? 'error' : 'extension' }}</span>
                </div>
                <div class="header-text">
                  <h3>{{ plugin.display_name }}</h3>
                  <p>v{{ plugin.version }} • {{ plugin.author }}</p>
                </div>
                <div class="badges">
                  <span v-if="isSystemPlugin(plugin)" class="m3-assist-chip system">系统</span>
                  <span v-if="plugin.loaded" class="m3-assist-chip success">已加载</span>
                  <span v-else class="m3-assist-chip">未加载</span>
                </div>
              </div>
              
              <div class="plugin-description">
                {{ plugin.description || '暂无描述' }}
              </div>

              <div v-if="plugin.error" class="error-message">
                <span class="material-symbols-rounded">warning</span>
                {{ plugin.error }}
              </div>

              <div class="plugin-meta">
                <span class="meta-item">
                  <span class="material-symbols-rounded">widgets</span>
                  {{ plugin.components_count }} 个组件
                </span>
              </div>
            </div>

            <div class="card-actions" @click.stop>
              <div class="action-left">
                <label class="m3-switch" v-if="plugin.loaded && !isSystemPlugin(plugin)">
                  <input 
                    type="checkbox" 
                    :checked="plugin.enabled"
                    @change="handleTogglePlugin(plugin)"
                    :disabled="!plugin.loaded"
                  >
                  <span class="slider"></span>
                </label>
                <div class="system-lock" v-if="isSystemPlugin(plugin)">
                  <span class="material-symbols-rounded">lock</span>
                  <span>系统锁定</span>
                </div>
              </div>
              
              <div class="action-right">
                <button 
                  v-if="!plugin.loaded && !isSystemPlugin(plugin)"
                  class="m3-icon-button" 
                  @click="handleLoadPlugin(plugin.name)"
                  title="加载插件"
                >
                  <span class="material-symbols-rounded">download</span>
                </button>
                <button 
                  v-if="plugin.loaded && !isSystemPlugin(plugin)"
                  class="m3-icon-button" 
                  @click="handleReloadPlugin(plugin.name)"
                  title="重载插件"
                >
                  <span class="material-symbols-rounded">refresh</span>
                </button>
                <button 
                  v-if="!isSystemPlugin(plugin)"
                  class="m3-icon-button error" 
                  @click="handleDeletePlugin(plugin.name, plugin.display_name)"
                  title="删除插件"
                >
                  <span class="material-symbols-rounded">delete</span>
                </button>
                <button 
                  v-if="plugin.loaded"
                  class="m3-icon-button filled-tonal" 
                  @click="goToDetail(plugin.name)"
                  title="查看详情"
                >
                  <span class="material-symbols-rounded">arrow_forward</span>
                </button>
              </div>
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
    <Transition name="dialog">
      <div v-if="confirmDialog.show" class="m3-dialog-overlay" @click="confirmDialog.show = false">
        <div class="m3-dialog" @click.stop>
          <div class="dialog-icon">
            <span class="material-symbols-rounded">warning</span>
          </div>
          <div class="dialog-content">
            <h3 class="headline">{{ confirmDialog.title }}</h3>
            <p class="supporting-text">{{ confirmDialog.message }}</p>
          </div>
          <div class="dialog-actions">
            <button class="m3-button text" @click="confirmDialog.show = false">取消</button>
            <button class="m3-button text" @click="confirmDialog.onConfirm">确认</button>
          </div>
        </div>
      </div>
    </Transition>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { usePluginStore } from '@/stores/plugin'
import type { PluginItem } from '@/api'

const router = useRouter()
const pluginStore = usePluginStore()

// 筛选选项
const filters = [
  { label: '全部', value: 'all' as const },
  { label: '已加载', value: 'loaded' as const },
  { label: '已启用', value: 'enabled' as const },
  { label: '失败', value: 'failed' as const },
]

// 状态
const loading = ref(false)
const error = ref('')

// 系统插件列表（这些插件不允许修改）
const SYSTEM_PLUGINS = [
  'Affinity Flow Chatter',
  'Kokoro Flow Chatter',
  'napcat_adapter_plugin',
  'Emoji插件 (Emoji Actions)'
]

// 判断是否为系统插件
function isSystemPlugin(plugin: PluginItem): boolean {
  return SYSTEM_PLUGINS.includes(plugin.display_name)
}

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

async function refreshPluginList() {
  loading.value = true
  error.value = ''
  
  const success = await pluginStore.fetchPlugins()
  
  if (!success && pluginStore.error) {
    error.value = pluginStore.error
  }
  
  loading.value = false
}

async function handleTogglePlugin(plugin: PluginItem) {
  try {
    if (plugin.enabled) {
      const result = await pluginStore.disablePluginAction(plugin.name)
      if (!result) {
        showToast('操作失败：无返回结果', 'error')
        return
      }
      showToast(
        result.success ? `插件 ${plugin.display_name} 已禁用` : (result.error || '操作失败'),
        result.success ? 'success' : 'error'
      )
    } else {
      const result = await pluginStore.enablePluginAction(plugin.name)
      if (!result) {
        showToast('操作失败：无返回结果', 'error')
        return
      }
      showToast(
        result.success ? `插件 ${plugin.display_name} 已启用` : (result.error || '操作失败'),
        result.success ? 'success' : 'error'
      )
    }
  } catch (error) {
    showToast(`操作异常: ${error instanceof Error ? error.message : '未知错误'}`, 'error')
  }
}

async function handleReloadPlugin(pluginName: string) {
  const plugin = pluginStore.plugins.find(p => p.name === pluginName)
  showConfirm(
    '重载插件',
    `确定要重载插件 "${plugin?.display_name || pluginName}" 吗？`,
    async () => {
      try {
        const result = await pluginStore.reloadPluginAction(pluginName)
        if (!result) {
          showToast('重载失败：无返回结果', 'error')
          return
        }
        showToast(
          result.success ? '插件重载成功' : (result.error || '重载失败'),
          result.success ? 'success' : 'error'
        )
      } catch (error) {
        showToast(`重载异常: ${error instanceof Error ? error.message : '未知错误'}`, 'error')
      }
    }
  )
}

async function handleLoadPlugin(pluginName: string) {
  const plugin = pluginStore.plugins.find(p => p.name === pluginName)
  showConfirm(
    '加载插件',
    `确定要加载插件 "${plugin?.display_name || pluginName}" 吗？`,
    async () => {
      try {
        const result = await pluginStore.loadPluginAction(pluginName)
        if (!result) {
          showToast('加载失败：无返回结果', 'error')
          return
        }
        showToast(
          result.success ? '插件加载成功' : (result.error || '加载失败'),
          result.success ? 'success' : 'error'
        )
      } catch (error) {
        showToast(`加载异常: ${error instanceof Error ? error.message : '未知错误'}`, 'error')
      }
    }
  )
}

async function handleDeletePlugin(pluginName: string, displayName: string) {
  showConfirm(
    '删除插件',
    `确定要删除插件 "${displayName || pluginName}" 吗？此操作将删除插件的所有文件，且无法撤销！`,
    async () => {
      try {
        const result = await pluginStore.deletePluginAction(pluginName)
        if (!result) {
          showToast('删除失败：无返回结果', 'error')
          return
        }
        showToast(
          result.success ? '插件已删除' : (result.error || '删除失败'),
          result.success ? 'success' : 'error'
        )
        if (result.success) {
          // 刷新插件列表
          await refreshPluginList()
        }
      } catch (error) {
        showToast(`删除异常: ${error instanceof Error ? error.message : '未知错误'}`, 'error')
      }
    }
  )
}

async function handleScanPlugins() {
  showConfirm(
    '扫描新插件',
    '将扫描插件目录并注册新发现的插件，是否继续？',
    async () => {
      try {
        loading.value = true
        const result = await pluginStore.scanForNewPlugins()
        loading.value = false
        
        if (!result) {
          showToast('扫描失败：无返回结果', 'error')
          return
        }
        
        if (result.success && result.data) {
          showToast(
            `扫描完成：注册 ${result.data.registered} 个，加载 ${result.data.loaded} 个，失败 ${result.data.failed} 个`,
            'success'
          )
        } else {
          showToast(result.error || '扫描失败', 'error')
        }
      } catch (error) {
        loading.value = false
        showToast(`扫描异常: ${error instanceof Error ? error.message : '未知错误'}`, 'error')
      }
    }
  )
}

async function handleReloadAll() {
  showConfirm(
    '重载所有插件',
    '确定要重载所有已加载的插件吗？这可能需要一些时间。',
    async () => {
      try {
        loading.value = true
        const result = await pluginStore.reloadAll()
        loading.value = false
        
        if (!result) {
          showToast('重载失败：无返回结果', 'error')
          return
        }
        
        showToast(
          result.success ? '所有插件重载成功' : (result.error || '重载失败'),
          result.success ? 'success' : 'error'
        )
      } catch (error) {
        loading.value = false
        showToast(`重载异常: ${error instanceof Error ? error.message : '未知错误'}`, 'error')
      }
    }
  )
}

function goToDetail(pluginName: string) {
  // 检查插件是否已加载
  const plugin = pluginStore.plugins.find(p => p.name === pluginName)
  if (!plugin || !plugin.loaded) {
    showToast('插件未加载，无法查看详情', 'error')
    return
  }
  router.push(`/dashboard/plugin-manage/${pluginName}`)
}

onMounted(() => {
  refreshPluginList()
})
</script>

<style scoped>
.plugin-manage-view {
  height: 100%;
  display: flex;
  flex-direction: column;
  gap: 24px;
  padding: 16px;
  animation: fadeIn 0.4s cubic-bezier(0.2, 0, 0, 1);
  overflow-y: auto;
  background: var(--md-sys-color-surface);
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}

/* 页面头部 */
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 24px;
  background: var(--md-sys-color-surface-container);
  border-radius: 32px;
}

.header-content h1 {
  font-size: 24px;
  font-weight: 400;
  color: var(--md-sys-color-on-surface);
  margin: 0 0 4px 0;
}

.subtitle {
  font-size: 14px;
  color: var(--md-sys-color-on-surface-variant);
  margin: 0;
}

.header-actions {
  display: flex;
  gap: 8px;
}

/* 统计卡片 */
.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 16px;
}

.stat-card {
  padding: 20px;
  display: flex;
  align-items: center;
  gap: 16px;
  border: none;
  border-radius: 24px;
}

.stat-card.primary-container {
  background: var(--md-sys-color-primary-container);
  color: var(--md-sys-color-on-primary-container);
}

.stat-card.success-container {
  background: var(--md-sys-color-tertiary-container);
  color: var(--md-sys-color-on-tertiary-container);
}

.stat-card.tertiary-container {
  background: var(--md-sys-color-secondary-container);
  color: var(--md-sys-color-on-secondary-container);
}

.stat-card.error-container {
  background: var(--md-sys-color-error-container);
  color: var(--md-sys-color-on-error-container);
}

.stat-icon {
  width: 48px;
  height: 48px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(255, 255, 255, 0.2);
}

.stat-icon .material-symbols-rounded {
  font-size: 24px;
}

.stat-value {
  font-size: 28px;
  font-weight: 600;
  line-height: 1;
  margin-bottom: 4px;
}

.stat-label {
  font-size: 12px;
  opacity: 0.8;
}

/* 筛选栏 */
.filter-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 16px;
  flex-wrap: wrap;
}

.filter-chips {
  display: flex;
  gap: 8px;
}

.m3-filter-chip {
  height: 32px;
  padding: 0 16px;
  border-radius: 8px;
  border: 1px solid var(--md-sys-color-outline);
  background: var(--md-sys-color-surface-container-high);
  color: var(--md-sys-color-on-surface-variant);
  font-size: 14px;
  font-weight: 500;
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  transition: all 0.2s;
}

.m3-filter-chip:hover {
  background: var(--md-sys-color-surface-container-highest);
}

.m3-filter-chip.selected {
  background: var(--md-sys-color-secondary-container);
  color: var(--md-sys-color-on-secondary-container);
  border-color: transparent;
}

.m3-filter-chip .check-icon {
  font-size: 18px;
  margin-left: -4px;
}

.search-box {
  position: relative;
  width: 300px;
  height: 48px;
  background: var(--md-sys-color-surface-container-high);
  border-radius: 24px;
  display: flex;
  align-items: center;
  transition: all 0.2s;
}

.search-box:hover {
  background: var(--md-sys-color-surface-container-highest);
}

.search-box:focus-within {
  background: var(--md-sys-color-surface-container-highest);
  box-shadow: 0 0 0 2px var(--md-sys-color-primary);
}

.search-icon {
  position: absolute;
  left: 16px;
  font-size: 20px;
  color: var(--md-sys-color-on-surface-variant);
  pointer-events: none;
}

.search-box .m3-input {
  width: 100%;
  height: 100%;
  background: transparent;
  border: none;
  padding: 0 16px 0 48px;
  font-size: 14px;
  color: var(--md-sys-color-on-surface);
  outline: none;
  border-radius: 24px;
  font-family: inherit;
}

.search-box .m3-input::placeholder {
  color: var(--md-sys-color-on-surface-variant);
}

/* 插件列表 */
.section-container {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.section-header {
  display: flex;
  align-items: center;
  gap: 8px;
  color: var(--md-sys-color-on-surface);
}

.section-header h2 {
  font-size: 16px;
  font-weight: 500;
  margin: 0;
}

.section-header.error-text {
  color: var(--md-sys-color-error);
}

.success-text {
  color: var(--md-sys-color-primary);
}

.plugin-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(360px, 1fr));
  gap: 16px;
}

.plugin-card {
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  transition: all 0.2s;
  cursor: pointer;
  border: 1px solid transparent;
  border-radius: 24px;
}

.plugin-card:hover {
  transform: translateY(-2px);
  box-shadow: var(--md-sys-elevation-2);
  border-color: var(--md-sys-color-outline-variant);
}

.plugin-card.disabled {
  background: var(--md-sys-color-surface);
  border: 1px solid var(--md-sys-color-outline-variant);
}

.plugin-card.disabled .plugin-icon {
  background: var(--md-sys-color-surface-container-highest);
  color: var(--md-sys-color-on-surface-variant);
}

.plugin-card.error-card {
  border-color: var(--md-sys-color-error-container);
  background: var(--md-sys-color-surface-container-low);
  color: var(--md-sys-color-on-surface);
}

.plugin-card.error-card .plugin-description {
  color: var(--md-sys-color-on-surface-variant);
  opacity: 1;
}

.card-content {
  padding: 16px;
}

.card-header {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  margin-bottom: 12px;
}

.plugin-icon {
  width: 40px;
  height: 40px;
  min-width: 40px;
  border-radius: 8px;
  background: var(--md-sys-color-primary-container);
  color: var(--md-sys-color-on-primary-container);
  display: flex;
  align-items: center;
  justify-content: center;
}

.plugin-icon.error {
  background: var(--md-sys-color-error-container);
  color: var(--md-sys-color-on-error-container);
}

.header-text {
  flex: 1;
  min-width: 0;
}

.header-text h3 {
  margin: 0 0 4px 0;
  font-size: 16px;
  font-weight: 500;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.header-text p {
  margin: 0;
  font-size: 12px;
  opacity: 0.7;
}

.badges {
  display: flex;
  gap: 4px;
}

.m3-assist-chip {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  height: 24px;
  padding: 0 8px;
  font-size: 11px;
  font-weight: 500;
  border-radius: 6px;
}

.m3-assist-chip.system {
  background: var(--md-sys-color-secondary-container);
  color: var(--md-sys-color-on-secondary-container);
  border: none;
}

.m3-assist-chip.success {
  background: var(--md-sys-color-tertiary-container);
  color: var(--md-sys-color-on-tertiary-container);
  border: none;
}

.plugin-description {
  font-size: 14px;
  line-height: 1.5;
  color: var(--md-sys-color-on-surface-variant);
  margin-bottom: 12px;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.error-message {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  padding: 12px;
  background: var(--md-sys-color-error-container);
  color: var(--md-sys-color-on-error-container);
  border-radius: 8px;
  font-size: 13px;
  line-height: 1.4;
  margin-bottom: 12px;
}

.error-message .material-symbols-rounded {
  font-size: 18px;
  flex-shrink: 0;
  margin-top: 1px;
}

.plugin-meta {
  display: flex;
  gap: 12px;
  font-size: 12px;
  color: var(--md-sys-color-on-surface-variant);
}

.meta-item {
  display: flex;
  align-items: center;
  gap: 4px;
}

.meta-item .material-symbols-rounded {
  font-size: 16px;
}

.card-actions {
  padding: 8px 16px 16px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.action-left {
  display: flex;
  align-items: center;
}

.system-lock {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: var(--md-sys-color-outline);
  padding: 4px 8px;
  background: var(--md-sys-color-surface-container-highest);
  border-radius: 4px;
}

.system-lock .material-symbols-rounded {
  font-size: 14px;
}

.action-right {
  display: flex;
  gap: 4px;
}

.m3-icon-button {
  width: 32px;
  height: 32px;
  border-radius: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  border: none;
  background: transparent;
  color: var(--md-sys-color-on-surface-variant);
  cursor: pointer;
  transition: all 0.2s;
}

.m3-icon-button:hover {
  background: var(--md-sys-color-surface-container-highest);
  color: var(--md-sys-color-on-surface);
}

.m3-icon-button.filled-tonal {
  background: var(--md-sys-color-secondary-container);
  color: var(--md-sys-color-on-secondary-container);
}

.m3-icon-button.filled-tonal:hover {
  background: var(--md-sys-color-secondary);
  color: var(--md-sys-color-on-secondary);
}

.m3-icon-button.error:hover {
  background: var(--md-sys-color-error-container);
  color: var(--md-sys-color-on-error-container);
}

/* 状态展示 */
.loading-state, .error-state, .empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px 0;
  gap: 16px;
  color: var(--md-sys-color-on-surface-variant);
}

.loading-icon, .error-icon, .empty-icon {
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

/* Dialog */
.m3-dialog-overlay {
  position: fixed;
  inset: 0;
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
  width: 100%;
  max-width: 320px;
  box-shadow: var(--md-sys-elevation-3);
  display: flex;
  flex-direction: column;
  gap: 16px;
  align-items: center;
  text-align: center;
}

.dialog-icon {
  color: var(--md-sys-color-secondary);
}

.dialog-icon .material-symbols-rounded {
  font-size: 24px;
}

.dialog-content .headline {
  margin: 0 0 16px 0;
  font-size: 24px;
  color: var(--md-sys-color-on-surface);
}

.dialog-content .supporting-text {
  margin: 0;
  font-size: 14px;
  color: var(--md-sys-color-on-surface-variant);
  line-height: 20px;
}

.dialog-actions {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
  width: 100%;
}

.dialog-enter-active,
.dialog-leave-active {
  transition: all 0.2s cubic-bezier(0.2, 0, 0, 1);
}

.dialog-enter-from,
.dialog-leave-to {
  opacity: 0;
  transform: scale(0.9);
}
</style>
