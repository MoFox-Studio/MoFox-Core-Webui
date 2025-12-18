<template>
  <div class="plugin-config-list">
    <!-- 顶部 -->
    <header class="page-header">
      <div class="header-left">
        <div class="header-icon-container">
          <span class="material-symbols-rounded header-icon">extension</span>
        </div>
        <div class="header-info">
          <h1>插件配置</h1>
          <p>管理已安装插件的配置文件</p>
        </div>
      </div>
      <div class="header-actions">
        <button class="m3-button text" @click="refreshPluginList" :disabled="loading">
          <span class="material-symbols-rounded" :class="{ spinning: loading }">
            {{ loading ? 'progress_activity' : 'refresh' }}
          </span>
          刷新列表
        </button>
      </div>
    </header>

    <!-- 插件列表 -->
    <div class="plugin-list-container">
      <div v-if="loading" class="loading-state">
        <span class="material-symbols-rounded spinning">progress_activity</span>
        加载插件配置列表...
      </div>
      <div v-else-if="loadError" class="error-state">
        <span class="material-symbols-rounded">error</span>
        {{ loadError }}
        <button class="m3-button filled" @click="refreshPluginList">重试</button>
      </div>
      <div v-else-if="pluginConfigs.length === 0" class="empty-state">
        <span class="material-symbols-rounded empty-icon">extension_off</span>
        <p>暂无插件配置文件</p>
        <span class="hint">插件安装后，其配置文件将显示在这里</span>
      </div>
      <div v-else class="plugin-grid">
        <div 
          v-for="config in pluginConfigs" 
          :key="config.path"
          class="m3-card plugin-card clickable"
          @click="openPluginConfig(config)"
        >
          <div class="plugin-icon">
            <span class="material-symbols-rounded">settings_applications</span>
          </div>
          <div class="plugin-info">
            <h3>{{ config.display_name }}</h3>
            <p class="plugin-path">{{ getShortPath(config.path) }}</p>
          </div>
          <span class="material-symbols-rounded arrow-icon">chevron_right</span>
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
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
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
  if (!path) return ''
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
    if (res.success && res.data && res.data.configs) {
      // 过滤出插件类型的配置
      pluginConfigs.value = res.data.configs.filter((c: ConfigFileInfo) => c.type === 'plugin')
    } else {
      loadError.value = res.data?.error || res.error || '获取列表失败'
    }
  } catch (e) {
    loadError.value = '网络请求失败'
    console.error(e)
  } finally {
    loading.value = false
  }
}

function showToast(msg: string, type: 'success' | 'error' = 'success') {
  toast.value = { show: true, message: msg, type }
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
  display: flex;
  flex-direction: column;
  height: 100%;
  gap: 24px;
  animation: fadeIn 0.4s cubic-bezier(0.2, 0, 0, 1);
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}

/* 头部样式 */
.page-header {
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
  background: var(--md-sys-color-tertiary-container);
  color: var(--md-sys-color-on-tertiary-container);
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

/* 列表容器 */
.plugin-list-container {
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
}

.plugin-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 16px;
  padding-bottom: 24px;
}

.plugin-card {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 16px;
  cursor: pointer;
  position: relative;
  overflow: hidden;
}

.plugin-card:hover {
  background: var(--md-sys-color-surface-container-high);
  transform: translateY(-2px);
  box-shadow: var(--md-sys-elevation-2);
}

.plugin-icon {
  width: 40px;
  height: 40px;
  border-radius: 12px;
  background: var(--md-sys-color-secondary-container);
  color: var(--md-sys-color-on-secondary-container);
  display: flex;
  align-items: center;
  justify-content: center;
}

.plugin-info {
  flex: 1;
  min-width: 0;
}

.plugin-info h3 {
  font-size: 16px;
  font-weight: 500;
  color: var(--md-sys-color-on-surface);
  margin: 0 0 4px 0;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.plugin-path {
  font-size: 12px;
  color: var(--md-sys-color-on-surface-variant);
  margin: 0;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.arrow-icon {
  color: var(--md-sys-color-on-surface-variant);
  transition: transform 0.2s;
}

.plugin-card:hover .arrow-icon {
  transform: translateX(4px);
  color: var(--md-sys-color-primary);
}

/* 状态展示 */
.loading-state, .error-state, .empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  flex: 1;
  gap: 16px;
  color: var(--md-sys-color-on-surface-variant);
  min-height: 300px;
}

.spinning {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.empty-icon {
  font-size: 48px;
  opacity: 0.5;
}

.hint {
  font-size: 12px;
  opacity: 0.7;
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
