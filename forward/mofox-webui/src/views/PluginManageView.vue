<template>
  <div class="plugin-manage-view">
    <!-- 顶部标题栏 -->
    <header class="page-header">
      <div class="header-left">
        <Icon icon="lucide:package" class="header-icon" />
        <div class="header-info">
          <h1>插件管理</h1>
          <p>管理系统插件的加载、启用和配置</p>
        </div>
      </div>
      <div class="header-actions">
        <button class="btn btn-ghost" @click="handleScanPlugins" :disabled="loading">
          <Icon icon="lucide:scan" />
          扫描新插件
        </button>
        <button class="btn btn-ghost" @click="handleReloadAll" :disabled="loading">
          <Icon icon="lucide:refresh-cw" />
          重载所有
        </button>
        <button class="btn btn-primary" @click="refreshPluginList" :disabled="loading">
          <Icon :icon="loading ? 'lucide:loader-2' : 'lucide:refresh-cw'" :class="{ spinning: loading }" />
          刷新列表
        </button>
      </div>
    </header>

    <!-- 统计卡片 -->
    <div class="stats-cards">
      <div class="stat-card">
        <div class="stat-icon" style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%)">
          <Icon icon="lucide:package" />
        </div>
        <div class="stat-content">
          <div class="stat-value">{{ pluginStore.stats.total }}</div>
          <div class="stat-label">插件总数</div>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon" style="background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%)">
          <Icon icon="lucide:check-circle" />
        </div>
        <div class="stat-content">
          <div class="stat-value">{{ pluginStore.stats.loaded }}</div>
          <div class="stat-label">已加载</div>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon" style="background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)">
          <Icon icon="lucide:zap" />
        </div>
        <div class="stat-content">
          <div class="stat-value">{{ pluginStore.stats.enabled }}</div>
          <div class="stat-label">已启用</div>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon" style="background: linear-gradient(135deg, #fa709a 0%, #fee140 100%)">
          <Icon icon="lucide:alert-circle" />
        </div>
        <div class="stat-content">
          <div class="stat-value">{{ pluginStore.stats.failed }}</div>
          <div class="stat-label">加载失败</div>
        </div>
      </div>
    </div>

    <!-- 筛选和搜索栏 -->
    <div class="filter-bar">
      <div class="filter-buttons">
        <button 
          v-for="filter in filters" 
          :key="filter.value"
          class="filter-btn"
          :class="{ active: pluginStore.statusFilter === filter.value }"
          @click="pluginStore.setStatusFilter(filter.value)"
        >
          {{ filter.label }}
        </button>
      </div>
      <div class="search-box">
        <Icon icon="lucide:search" class="search-icon" />
        <input 
          type="text" 
          placeholder="搜索插件名称或描述..." 
          v-model="pluginStore.searchKeyword"
        />
      </div>
    </div>

    <!-- 失败插件区域 -->
    <div v-if="!loading && pluginStore.failedPlugins.length > 0" class="failed-plugins-section">
      <div class="section-header">
        <Icon icon="lucide:alert-circle" class="section-icon error" />
        <h2>加载失败的插件 ({{ pluginStore.failedPlugins.length }})</h2>
      </div>
      <div class="plugin-grid failed-grid">
        <div 
          v-for="plugin in pluginStore.failedPlugins" 
          :key="plugin.name"
          class="plugin-card plugin-card-failed"
        >
          <!-- 插件卡片头部 -->
          <div class="plugin-card-header">
            <div class="plugin-icon error">
              <Icon icon="lucide:alert-circle" />
            </div>
            <div class="plugin-header-info">
              <h3 class="plugin-name">{{ plugin.display_name }}</h3>
              <p class="plugin-version">v{{ plugin.version }} • {{ plugin.author }}</p>
            </div>
            <div class="plugin-badges">
              <span class="badge badge-error">加载失败</span>
            </div>
          </div>

          <!-- 插件描述 -->
          <div class="plugin-description">
            {{ plugin.description || '暂无描述' }}
          </div>

          <!-- 错误信息 -->
          <div class="plugin-error">
            <Icon icon="lucide:alert-triangle" />
            {{ plugin.error || '未知错误' }}
          </div>

          <!-- 操作按钮 -->
          <div class="plugin-actions" @click.stop>
            <button 
              class="btn btn-sm btn-ghost" 
              @click="handleReloadPlugin(plugin.name)"
              title="重试加载"
            >
              <Icon icon="lucide:refresh-cw" />
              重试
            </button>
            <button 
              v-if="!isSystemPlugin(plugin)"
              class="btn btn-sm btn-error" 
              @click="handleDeletePlugin(plugin.name, plugin.display_name)"
              title="删除插件"
            >
              <Icon icon="lucide:trash-2" />
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- 插件列表 -->
    <div class="plugin-list-container">
      <div v-if="loading" class="loading-state">
        <Icon icon="lucide:loader-2" class="spinning" />
        加载插件列表...
      </div>
      <div v-else-if="error" class="error-state">
        <Icon icon="lucide:alert-circle" />
        {{ error }}
        <button class="btn btn-primary" @click="refreshPluginList">重试</button>
      </div>
      <div v-else-if="pluginStore.filteredPlugins.length === 0 && pluginStore.failedPlugins.length === 0" class="empty-state">
        <Icon icon="lucide:package" />
        <p>没有找到插件</p>
        <span class="hint">尝试调整筛选条件或扫描新插件</span>
      </div>
      <div v-else-if="pluginStore.filteredPlugins.length > 0">
        <div class="section-header" v-if="pluginStore.failedPlugins.length > 0">
          <Icon icon="lucide:check-circle" class="section-icon success" />
          <h2>正常插件 ({{ pluginStore.filteredPlugins.length }})</h2>
        </div>
        <div class="plugin-grid">
        <div 
          v-for="plugin in pluginStore.filteredPlugins" 
          :key="plugin.name"
          class="plugin-card"
          :class="{ 'plugin-card-disabled': !plugin.loaded }"
          @click="plugin.loaded ? goToDetail(plugin.name) : null"
        >
          <!-- 插件卡片头部 -->
          <div class="plugin-card-header">
            <div class="plugin-icon">
              <Icon :icon="plugin.error ? 'lucide:alert-circle' : 'lucide:package'" />
            </div>
            <div class="plugin-header-info">
              <h3 class="plugin-name">{{ plugin.display_name }}</h3>
              <p class="plugin-version">v{{ plugin.version }} • {{ plugin.author }}</p>
            </div>
            <div class="plugin-badges">
              <span v-if="isSystemPlugin(plugin)" class="badge badge-system">系统插件</span>
              <span v-if="plugin.loaded" class="badge badge-success">已加载</span>
              <span v-else class="badge badge-secondary">未加载</span>
              <span v-if="plugin.error" class="badge badge-error">错误</span>
            </div>
          </div>

          <!-- 插件描述 -->
          <div class="plugin-description">
            {{ plugin.description || '暂无描述' }}
          </div>

          <!-- 错误信息 -->
          <div v-if="plugin.error" class="plugin-error">
            <Icon icon="lucide:alert-triangle" />
            {{ plugin.error }}
          </div>

          <!-- 插件信息 -->
          <div class="plugin-info">
            <div class="info-item">
              <Icon icon="lucide:puzzle" />
              {{ plugin.components_count }} 个组件
            </div>
          </div>

          <!-- 操作按钮 -->
          <div class="plugin-actions" @click.stop>
            <div class="toggle-switch" v-if="plugin.loaded && !isSystemPlugin(plugin)">
              <input 
                type="checkbox" 
                :id="`toggle-${plugin.name}`"
                :checked="plugin.enabled"
                @change="handleTogglePlugin(plugin)"
                :disabled="!plugin.loaded"
              />
              <label :for="`toggle-${plugin.name}`">
                {{ plugin.enabled ? '已启用' : '已禁用' }}
              </label>
            </div>
            <div class="system-plugin-lock" v-if="isSystemPlugin(plugin)">
              <Icon icon="lucide:lock" />
              <span>系统插件</span>
            </div>
            <button 
              v-if="!plugin.loaded && !isSystemPlugin(plugin)"
              class="btn btn-sm btn-success" 
              @click="handleLoadPlugin(plugin.name)"
              title="加载插件"
            >
              <Icon icon="lucide:download" />
              加载
            </button>
            <button 
              v-if="plugin.loaded && !isSystemPlugin(plugin)"
              class="btn btn-sm btn-ghost" 
              @click="handleReloadPlugin(plugin.name)"
              title="重载插件"
            >
              <Icon icon="lucide:refresh-cw" />
            </button>
            <button 
              v-if="!isSystemPlugin(plugin)"
              class="btn btn-sm btn-error" 
              @click="handleDeletePlugin(plugin.name, plugin.display_name)"
              title="删除插件"
            >
              <Icon icon="lucide:trash-2" />
            </button>
            <button 
              v-if="plugin.loaded"
              class="btn btn-sm btn-primary" 
              @click="goToDetail(plugin.name)"
              title="查看详情"
            >
              <Icon icon="lucide:arrow-right" />
            </button>
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
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { Icon } from '@iconify/vue'
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
  if (plugin.enabled) {
    const result = await pluginStore.disablePluginAction(plugin.name)
    showToast(
      result.success ? `插件 ${plugin.display_name} 已禁用` : result.error || '操作失败',
      result.success ? 'success' : 'error'
    )
  } else {
    const result = await pluginStore.enablePluginAction(plugin.name)
    showToast(
      result.success ? `插件 ${plugin.display_name} 已启用` : result.error || '操作失败',
      result.success ? 'success' : 'error'
    )
  }
}

async function handleReloadPlugin(pluginName: string) {
  const plugin = pluginStore.plugins.find(p => p.name === pluginName)
  showConfirm(
    '重载插件',
    `确定要重载插件 "${plugin?.display_name || pluginName}" 吗？`,
    async () => {
      const result = await pluginStore.reloadPluginAction(pluginName)
      showToast(
        result.success ? '插件重载成功' : result.error || '重载失败',
        result.success ? 'success' : 'error'
      )
    }
  )
}

async function handleLoadPlugin(pluginName: string) {
  const plugin = pluginStore.plugins.find(p => p.name === pluginName)
  showConfirm(
    '加载插件',
    `确定要加载插件 "${plugin?.display_name || pluginName}" 吗？`,
    async () => {
      const result = await pluginStore.loadPluginAction(pluginName)
      showToast(
        result.success ? '插件加载成功' : result.error || '加载失败',
        result.success ? 'success' : 'error'
      )
    }
  )
}

async function handleDeletePlugin(pluginName: string, displayName: string) {
  showConfirm(
    '删除插件',
    `确定要删除插件 "${displayName || pluginName}" 吗？此操作将删除插件的所有文件，且无法撤销！`,
    async () => {
      const result = await pluginStore.deletePluginAction(pluginName)
      showToast(
        result.success ? '插件已删除' : result.error || '删除失败',
        result.success ? 'success' : 'error'
      )
      if (result.success) {
        // 刷新插件列表
        await refreshPluginList()
      }
    }
  )
}

async function handleScanPlugins() {
  showConfirm(
    '扫描新插件',
    '将扫描插件目录并注册新发现的插件，是否继续？',
    async () => {
      loading.value = true
      const result = await pluginStore.scanForNewPlugins()
      loading.value = false
      
      if (result.success && result.data) {
        showToast(
          `扫描完成：注册 ${result.data.registered} 个，加载 ${result.data.loaded} 个，失败 ${result.data.failed} 个`,
          'success'
        )
      } else {
        showToast(result.error || '扫描失败', 'error')
      }
    }
  )
}

async function handleReloadAll() {
  showConfirm(
    '重载所有插件',
    '确定要重载所有已加载的插件吗？这可能需要一些时间。',
    async () => {
      loading.value = true
      const result = await pluginStore.reloadAll()
      loading.value = false
      
      showToast(
        result.success ? '所有插件重载成功' : result.error || '重载失败',
        result.success ? 'success' : 'error'
      )
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
  animation: fadeIn 0.4s ease;
  gap: 24px;
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}

/* 顶部标题栏 */
.page-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 20px 32px;
  background: var(--bg-primary);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-sm);
  border: 1px solid transparent;
  transition: all var(--transition);
}

.page-header:hover {
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

/* 统计卡片 */
.stats-cards {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 20px;
}

.stat-card {
  display: flex;
  align-items: center;
  gap: 20px;
  padding: 24px;
  background: var(--bg-primary);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-sm);
  transition: all var(--transition);
  border: 1px solid transparent;
}

.stat-card:hover {
  transform: translateY(-4px);
  box-shadow: var(--shadow-md);
  border-color: var(--border-light);
}

.stat-icon {
  width: 56px;
  height: 56px;
  border-radius: 18px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24px;
  color: white;
  box-shadow: var(--shadow-sm);
}

.stat-content {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.stat-value {
  font-size: 28px;
  font-weight: 800;
  color: var(--text-primary);
  line-height: 1.2;
}

.stat-label {
  font-size: 14px;
  color: var(--text-secondary);
  font-weight: 600;
}

/* 筛选和搜索栏 */
.filter-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 20px;
  padding: 16px 24px;
  background: var(--bg-primary);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-sm);
}

.filter-buttons {
  display: flex;
  gap: 8px;
  background: var(--bg-secondary);
  padding: 4px;
  border-radius: var(--radius-full);
}

.filter-btn {
  padding: 8px 20px;
  border: none;
  background: transparent;
  border-radius: var(--radius-full);
  font-size: 14px;
  font-weight: 600;
  color: var(--text-secondary);
  cursor: pointer;
  transition: all var(--transition);
}

.filter-btn:hover {
  color: var(--text-primary);
}

.filter-btn.active {
  background: var(--bg-primary);
  color: var(--primary);
  box-shadow: var(--shadow-sm);
}

.search-box {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 20px;
  background: var(--bg-secondary);
  border-radius: var(--radius-full);
  width: 300px;
  border: 1px solid transparent;
  transition: all var(--transition);
}

.search-box:focus-within {
  background: var(--bg-primary);
  border-color: var(--primary);
  box-shadow: 0 0 0 3px var(--primary-bg);
}

.search-icon {
  font-size: 18px;
  color: var(--text-tertiary);
}

.search-box input {
  border: none;
  background: transparent;
  outline: none;
  width: 100%;
  font-size: 14px;
  color: var(--text-primary);
  padding: 0;
}

/* 插件网格 */
.plugin-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(340px, 1fr));
  gap: 20px;
}

.plugin-card {
  display: flex;
  flex-direction: column;
  padding: 24px;
  background: var(--bg-primary);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-sm);
  transition: all var(--transition);
  border: 1px solid transparent;
  position: relative;
  overflow: hidden;
}

.plugin-card:hover {
  transform: translateY(-4px);
  box-shadow: var(--shadow-md);
  border-color: var(--border-light);
}

.plugin-header {
  display: flex;
  gap: 16px;
  margin-bottom: 16px;
}

.plugin-icon {
  width: 56px;
  height: 56px;
  border-radius: 18px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 28px;
  color: white;
  flex-shrink: 0;
  box-shadow: var(--shadow-sm);
}

.plugin-title-area {
  flex: 1;
  min-width: 0;
}

.plugin-name-row {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 4px;
}

.plugin-name {
  font-size: 18px;
  font-weight: 700;
  color: var(--text-primary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.plugin-version {
  font-size: 12px;
  padding: 2px 8px;
  background: var(--bg-secondary);
  border-radius: var(--radius-sm);
  color: var(--text-secondary);
  font-weight: 600;
}

.plugin-desc {
  font-size: 14px;
  color: var(--text-secondary);
  line-height: 1.5;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.plugin-error {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px;
  background: var(--danger-bg);
  border-radius: var(--radius);
  color: var(--danger);
  font-size: 13px;
  margin-bottom: 16px;
  font-weight: 500;
}

.plugin-info {
  display: flex;
  gap: 16px;
  margin-bottom: 16px;
  padding-bottom: 16px;
  border-bottom: 1px solid var(--border-light);
}

.info-item {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  color: var(--text-secondary);
  font-weight: 500;
}

.plugin-actions {
  display: flex;
  align-items: center;
  gap: 12px;
}

.toggle-switch {
  flex: 1;
  display: flex;
  align-items: center;
}

.system-plugin-lock {
  flex: 1;
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  background: var(--bg-secondary);
  border-radius: var(--radius);
  color: var(--text-tertiary);
  font-size: 13px;
  font-weight: 600;
}

.system-plugin-lock svg {
  font-size: 14px;
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
  font-size: 14px;
  font-weight: 600;
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
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
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

/* 状态样式 */
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
  gap: 20px;
}

.loading-state svg,
.error-state svg,
.empty-state svg {
  font-size: 56px;
  color: var(--text-tertiary);
  opacity: 0.5;
}

.hint {
  font-size: 14px;
  color: var(--text-tertiary);
}

/* 按钮样式 */
.btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 10px 20px;
  border-radius: var(--radius-full);
  font-size: 14px;
  font-weight: 600;
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
  box-shadow: var(--shadow-sm);
}

.btn-primary:hover:not(:disabled) {
  background: var(--primary-hover);
  transform: translateY(-1px);
  box-shadow: var(--shadow-md);
}

.btn-ghost {
  background: transparent;
  color: var(--text-secondary);
  border: 1px solid transparent;
}

.btn-ghost:hover:not(:disabled) {
  background: var(--bg-secondary);
  color: var(--text-primary);
}

.btn-sm {
  padding: 6px 16px;
  font-size: 13px;
}

/* Toast 提示 */
.toast {
  position: fixed;
  bottom: 32px;
  right: 32px;
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 16px 24px;
  border-radius: var(--radius-lg);
  background: var(--bg-primary);
  box-shadow: var(--shadow-lg);
  color: var(--text-primary);
  font-size: 15px;
  font-weight: 500;
  z-index: 1000;
  min-width: 300px;
  border: 1px solid var(--border-light);
}

.toast.success {
  border-left: 4px solid var(--success);
}

.toast.error {
  border-left: 4px solid var(--danger);
}

.toast-enter-active,
.toast-leave-active {
  transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
}

.toast-enter-from,
.toast-leave-to {
  opacity: 0;
  transform: translateY(20px);
}

/* 确认对话框 */
.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.4);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  padding: 20px;
  backdrop-filter: blur(8px);
}

.modal-content {
  background: var(--bg-primary);
  border-radius: var(--radius-xl);
  max-width: 480px;
  width: 100%;
  overflow: hidden;
  box-shadow: var(--shadow-lg);
}

.modal-header {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 24px;
  border-bottom: 1px solid var(--border-light);
}

.warning-icon {
  font-size: 28px;
  color: var(--warning);
}

.modal-header h3 {
  font-size: 20px;
  font-weight: 700;
  color: var(--text-primary);
  margin: 0;
}

.modal-body {
  padding: 24px;
}

.modal-body p {
  font-size: 15px;
  color: var(--text-secondary);
  line-height: 1.6;
  margin: 0;
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  padding: 20px 24px;
  border-top: 1px solid var(--border-light);
}

.modal-enter-active,
.modal-leave-active {
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.modal-enter-from,
.modal-leave-to {
  opacity: 0;
}

.modal-enter-from .modal-content,
.modal-leave-to .modal-content {
  transform: scale(0.95) translateY(10px);
}

/* 失败插件区域 */
.failed-plugins-section {
  margin-bottom: 32px;
}

.section-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 20px;
}

.section-icon {
  font-size: 24px;
}

.section-icon.error {
  color: var(--danger);
}

.section-icon.success {
  color: var(--success);
}

.section-header h2 {
  font-size: 20px;
  font-weight: 700;
  color: var(--text-primary);
  margin: 0;
}

.plugin-card-failed {
  border-color: rgba(239, 68, 68, 0.3);
  background: rgba(239, 68, 68, 0.05);
}

.plugin-card-failed:hover {
  border-color: var(--danger);
  transform: translateY(-4px);
  box-shadow: var(--shadow-md);
}

.plugin-card-failed .plugin-icon {
  background: linear-gradient(135deg, var(--danger) 0%, #ef4444 100%);
}

.failed-grid {
  margin-bottom: 24px;
}

/* 动画 */
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

  gap: 6px;
  padding: 8px 12px;
  background: rgba(156, 163, 175, 0.1);
  border-radius: var(--radius);
  color: var(--text-tertiary);
  font-size: 13px;
  font-weight: 500;
}


