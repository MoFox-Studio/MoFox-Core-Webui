<template>
  <div class="plugin-config-list">
    <!-- 顶部 -->
    <header class="page-header">
      <div class="header-left">
        <Icon icon="lucide:puzzle" class="header-icon" />
        <div class="header-info">
          <h1>插件配置</h1>
          <p>管理已安装插件的配置文件</p>
        </div>
      </div>
      <div class="header-actions">
        <button class="btn btn-ghost" @click="refreshPluginList" :disabled="loading">
          <Icon :icon="loading ? 'lucide:loader-2' : 'lucide:refresh-cw'" :class="{ spinning: loading }" />
          刷新列表
        </button>
      </div>
    </header>

    <!-- 插件列表 -->
    <div class="plugin-list-container">
      <div v-if="loading" class="loading-state">
        <Icon icon="lucide:loader-2" class="spinning" />
        加载插件配置列表...
      </div>
      <div v-else-if="loadError" class="error-state">
        <Icon icon="lucide:alert-circle" />
        {{ loadError }}
        <button class="btn btn-primary" @click="refreshPluginList">重试</button>
      </div>
      <div v-else-if="pluginConfigs.length === 0" class="empty-state">
        <Icon icon="lucide:puzzle" />
        <p>暂无插件配置文件</p>
        <span class="hint">插件安装后，其配置文件将显示在这里</span>
      </div>
      <div v-else class="plugin-grid">
        <div 
          v-for="config in pluginConfigs" 
          :key="config.path"
          class="plugin-card"
          @click="openPluginConfig(config)"
        >
          <div class="plugin-icon">
            <Icon icon="lucide:puzzle" />
          </div>
          <div class="plugin-info">
            <h3>{{ config.display_name }}</h3>
            <p class="plugin-path">{{ getShortPath(config.path) }}</p>
          </div>
          <Icon icon="lucide:chevron-right" class="arrow-icon" />
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
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { Icon } from '@iconify/vue'
import {
  getConfigList,
  type ConfigFileInfo
} from '@/api'

const router = useRouter()

// 状态
const loading = ref(true)
const loadError = ref('')
const pluginConfigs = ref<ConfigFileInfo[]>([])

// Toast 提示
const toast = ref({ show: false, message: '', type: 'success' as 'success' | 'error' })

// 方法
function getShortPath(path: string): string {
  // 截取较短的路径显示
  const parts = path.split(/[/\\]/)
  if (parts.length > 3) {
    return '...' + parts.slice(-3).join('/')
  }
  return path
}

function openPluginConfig(config: ConfigFileInfo) {
  // 将路径编码后作为参数传递
  const encodedPath = encodeURIComponent(config.path)
  router.push(`/dashboard/plugin-config/${encodedPath}`)
}

async function refreshPluginList() {
  loading.value = true
  loadError.value = ''
  
  try {
    const res = await getConfigList()
    if (res.success && res.data) {
      pluginConfigs.value = res.data.configs.filter((c: ConfigFileInfo) => c.type === 'plugin')
    } else {
      loadError.value = '获取插件配置列表失败'
    }
  } catch (e) {
    loadError.value = '加载插件配置时发生错误'
    console.error(e)
  } finally {
    loading.value = false
  }
}

function showToast(message: string, type: 'success' | 'error') {
  toast.value = { show: true, message, type }
  setTimeout(() => {
    toast.value.show = false
  }, 3000)
}

onMounted(() => {
  refreshPluginList()
})
</script>

<style scoped>
.plugin-config-list {
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

/* 顶部 */
.page-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 20px 24px;
  background: var(--bg-primary);
  border-bottom: 1px solid var(--border-color);
}

.header-left {
  display: flex;
  align-items: center;
  gap: 16px;
}

.header-icon {
  font-size: 32px;
  color: #10b981;
}

.header-info h1 {
  font-size: 20px;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0 0 4px 0;
}

.header-info p {
  font-size: 13px;
  color: var(--text-tertiary);
  margin: 0;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 12px;
}

.btn {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 16px;
  border: none;
  border-radius: var(--radius);
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: all var(--transition-fast);
}

.btn-ghost {
  background: transparent;
  color: var(--text-secondary);
}

.btn-ghost:hover {
  background: var(--bg-secondary);
  color: var(--text-primary);
}

.btn-ghost:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn-primary {
  background: var(--primary);
  color: white;
}

.btn-primary:hover {
  background: var(--primary-dark);
}

/* 插件列表容器 */
.plugin-list-container {
  flex: 1;
  overflow: auto;
  padding: 24px;
  background: var(--bg-secondary);
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
  color: var(--text-tertiary);
  font-size: 14px;
}

.loading-state svg,
.error-state svg,
.empty-state svg {
  font-size: 64px;
  opacity: 0.5;
}

.error-state {
  color: #ef4444;
}

.empty-state .hint {
  font-size: 13px;
  color: var(--text-tertiary);
}

/* 插件网格 */
.plugin-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: 16px;
}

.plugin-card {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 20px;
  background: var(--bg-primary);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-lg);
  cursor: pointer;
  transition: all var(--transition-fast);
}

.plugin-card:hover {
  border-color: var(--primary);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  transform: translateY(-2px);
}

.plugin-icon {
  width: 48px;
  height: 48px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #10b981, #059669);
  border-radius: var(--radius);
  color: white;
  font-size: 24px;
}

.plugin-info {
  flex: 1;
  min-width: 0;
}

.plugin-info h3 {
  font-size: 15px;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0 0 6px 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.plugin-path {
  font-size: 12px;
  color: var(--text-tertiary);
  margin: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.arrow-icon {
  font-size: 20px;
  color: var(--text-tertiary);
  transition: all var(--transition-fast);
}

.plugin-card:hover .arrow-icon {
  color: var(--primary);
  transform: translateX(4px);
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
  background: var(--bg-primary);
  border-radius: var(--radius);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  font-size: 14px;
  z-index: 2000;
  animation: slideIn 0.3s ease;
}

.toast.success {
  border-left: 4px solid #10b981;
  color: #10b981;
}

.toast.error {
  border-left: 4px solid #ef4444;
  color: #ef4444;
}

@keyframes slideIn {
  from {
    opacity: 0;
    transform: translateX(20px);
  }
  to {
    opacity: 1;
    transform: translateX(0);
  }
}
</style>
