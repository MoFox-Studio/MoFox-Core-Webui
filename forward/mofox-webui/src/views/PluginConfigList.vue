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

/* 顶部 */
.page-header {
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

.btn-ghost:disabled {
  opacity: 0.5;
  cursor: not-allowed;
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

/* 插件列表容器 */
.plugin-list-container {
  flex: 1;
  overflow: auto;
  padding: 8px;
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
  font-size: 64px;
  opacity: 0.5;
  margin-bottom: 8px;
}

.error-state {
  color: var(--danger);
}

.empty-state .hint {
  font-size: 14px;
  color: var(--text-tertiary);
}

/* 插件网格 */
.plugin-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: 20px;
}

.plugin-card {
  display: flex;
  align-items: center;
  gap: 20px;
  padding: 24px;
  background: var(--bg-primary);
  border: 1px solid transparent;
  border-radius: var(--radius-lg);
  cursor: pointer;
  transition: all var(--transition);
  box-shadow: var(--shadow-sm);
}

.plugin-card:hover {
  border-color: var(--border-light);
  box-shadow: var(--shadow-md);
  transform: translateY(-4px);
}

.plugin-icon {
  width: 56px;
  height: 56px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--primary-bg);
  border-radius: 18px;
  color: var(--primary);
  font-size: 28px;
  transition: all var(--transition);
}

.plugin-card:hover .plugin-icon {
  background: var(--primary);
  color: white;
  transform: scale(1.1) rotate(5deg);
}

.plugin-info {
  flex: 1;
  min-width: 0;
}

.plugin-info h3 {
  font-size: 16px;
  font-weight: 700;
  color: var(--text-primary);
  margin: 0 0 6px 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.plugin-info h3:hover {
  color: var(--primary);
}

.plugin-path {
  font-size: 13px;
  color: var(--text-tertiary);
  margin: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-family: monospace;
}

.arrow-icon {
  font-size: 24px;
  color: var(--text-tertiary);
  transition: all var(--transition);
  opacity: 0;
  transform: translateX(-10px);
}

.plugin-card:hover .arrow-icon {
  opacity: 1;
  color: var(--primary);
  transform: translateX(0);
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
