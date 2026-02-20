<!--
  @file PluginConfigList.vue
  @description 插件配置列表页面

  功能说明：
  1. 显示所有已加载插件的配置文件列表
  2. 点击配置项跳转到配置编辑页面
  3. 支持刷新列表

  数据来源：
  - listAllPluginConfigs: 获取所有已加载插件的配置文件

  导航：
  - 点击配置卡片跳转到 /dashboard/plugin-config/{plugin_name}/{config_name}
-->
<template>
  <div class="plugin-config-list">
    <!-- 顶部标题和操作栏 -->
    <header class="page-header">
      <div class="header-content">
        <div class="header-title-area">
          <div class="header-icon-container">
            <span class="material-symbols-rounded header-icon">extension</span>
          </div>
          <div class="header-info">
            <h1>插件配置</h1>
            <p>管理已安装插件的配置文件</p>
          </div>
        </div>
        
        <div class="header-controls">
          <!-- 搜索框 -->
          <div class="search-box">
            <span class="material-symbols-rounded search-icon">search</span>
            <input 
              v-model="searchQuery" 
              type="text" 
              placeholder="搜索插件..." 
              class="search-input"
            />
            <button 
              v-if="searchQuery" 
              class="clear-search-btn" 
              @click="searchQuery = ''"
            >
              <span class="material-symbols-rounded">close</span>
            </button>
          </div>

          <button class="m3-button tonal" @click="refreshPluginList" :disabled="loading">
            <span class="material-symbols-rounded" :class="{ spinning: loading }">
              {{ loading ? 'progress_activity' : 'refresh' }}
            </span>
            刷新
          </button>
        </div>
      </div>
    </header>

    <!-- 插件列表 -->
    <div class="plugin-list-container">
      <div v-if="loading && pluginConfigs.length === 0" class="loading-state">
        <div class="loading-spinner">
          <span class="material-symbols-rounded spinning">progress_activity</span>
        </div>
        <p>正在加载插件配置...</p>
      </div>
      
      <div v-else-if="loadError" class="error-state">
        <div class="error-icon-container">
          <span class="material-symbols-rounded">error</span>
        </div>
        <h3>加载失败</h3>
        <p>{{ loadError }}</p>
        <button class="m3-button filled" @click="refreshPluginList">重试</button>
      </div>
      
      <div v-else-if="filteredConfigs.length === 0" class="empty-state">
        <div class="empty-icon-container">
          <span class="material-symbols-rounded">extension_off</span>
        </div>
        <h3>{{ searchQuery ? '未找到匹配的插件' : '暂无插件配置文件' }}</h3>
        <p>{{ searchQuery ? '请尝试更换搜索关键词' : '插件安装后，其配置文件将显示在这里' }}</p>
        <button v-if="searchQuery" class="m3-button text" @click="searchQuery = ''">清除搜索</button>
      </div>
      
      <div v-else class="plugin-grid">
        <div 
          v-for="config in filteredConfigs" 
          :key="config.config_path"
          class="plugin-card"
          @click="openPluginConfig(config)"
        >
          <div class="card-content">
            <div class="plugin-icon-wrapper" :style="{ backgroundColor: getIconColor(config.plugin_name) }">
              <span class="material-symbols-rounded">settings_applications</span>
            </div>
            <div class="plugin-details">
              <h3 class="plugin-name" :title="config.plugin_name">{{ config.display_name }}</h3>
              <div class="plugin-path-container" :title="config.config_path">
                <span class="material-symbols-rounded path-icon">folder</span>
                <span class="plugin-path-text">{{ getShortPath(config.config_path) }}</span>
              </div>
            </div>
          </div>
          <div class="card-actions">
            <button class="action-btn">
              <span>配置</span>
              <span class="material-symbols-rounded">arrow_forward</span>
            </button>
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
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import {
  listAllPluginConfigs,
  type PluginConfigFileInfo,
} from '@/api/pluginConfig'

const router = useRouter()

// 状态
const loading = ref(true)
const loadError = ref('')
const pluginConfigs = ref<PluginConfigFileInfo[]>([])
const searchQuery = ref('')

// Toast 提示
const toast = ref({ show: false, message: '', type: 'success' as 'success' | 'error' })

// 计算属性：过滤后的配置列表
const filteredConfigs = computed(() => {
  if (!searchQuery.value) return pluginConfigs.value
  const query = searchQuery.value.toLowerCase()
  return pluginConfigs.value.filter(config =>
    config.display_name.toLowerCase().includes(query) ||
    config.plugin_name.toLowerCase().includes(query) ||
    config.config_name.toLowerCase().includes(query)
  )
})

// 方法
function getShortPath(path: string): string {
  if (!path) return ''
  const parts = path.split(/[/\\]/)
  if (parts.length > 2) {
    return '.../' + parts.slice(-2).join('/')
  }
  return path
}

// 根据名称生成确定的颜色，用于图标背景
function getIconColor(name: string): string {
  const colors = [
    'var(--md-sys-color-primary-container)',
    'var(--md-sys-color-secondary-container)',
    'var(--md-sys-color-tertiary-container)',
    'var(--md-sys-color-error-container)',
  ]
  let hash = 0
  for (let i = 0; i < name.length; i++) {
    hash = name.charCodeAt(i) + ((hash << 5) - hash)
  }
  const index = Math.abs(hash) % colors.length
  return colors[index]
}

function openPluginConfig(config: PluginConfigFileInfo) {
  // 路由格式：/dashboard/plugin-config/{plugin_name}/{config_name}
  const encoded = encodeURIComponent(config.plugin_name) + '/' + encodeURIComponent(config.config_name)
  router.push(`/dashboard/plugin-config/${encoded}`)
}

async function refreshPluginList() {
  loading.value = true
  loadError.value = ''
  try {
    const res = await listAllPluginConfigs()
    if (res.success && res.data) {
      pluginConfigs.value = res.data.plugins
    } else {
      loadError.value = res.error || '获取列表失败'
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
  padding: 24px;
  animation: fadeIn 0.4s cubic-bezier(0.2, 0, 0, 1);
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}

/* 头部样式 */
.page-header {
  background: var(--md-sys-color-surface);
  border-radius: 24px;
  padding: 24px;
}

.header-content {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 24px;
}

.header-title-area {
  display: flex;
  align-items: center;
  gap: 16px;
}

.header-icon-container {
  width: 56px;
  height: 56px;
  border-radius: 16px;
  background: var(--md-sys-color-primary-container);
  color: var(--md-sys-color-on-primary-container);
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: var(--md-sys-elevation-1);
}

.header-icon {
  font-size: 28px;
}

.header-info h1 {
  font-size: 24px;
  font-weight: 500;
  color: var(--md-sys-color-on-surface);
  margin: 0 0 4px 0;
}

.header-info p {
  font-size: 14px;
  color: var(--md-sys-color-on-surface-variant);
  margin: 0;
}

.header-controls {
  display: flex;
  align-items: center;
  gap: 16px;
  flex-wrap: wrap;
}

/* 搜索框样式 */
.search-box {
  position: relative;
  display: flex;
  align-items: center;
  background: var(--md-sys-color-surface-container-high);
  border-radius: 24px;
  padding: 0 16px;
  height: 48px;
  width: 280px;
  transition: all 0.2s ease;
}

.search-box:focus-within {
  background: var(--md-sys-color-surface-container-highest);
  box-shadow: 0 0 0 2px var(--md-sys-color-primary);
}

.search-icon {
  color: var(--md-sys-color-on-surface-variant);
  font-size: 20px;
  margin-right: 8px;
}

.search-input {
  flex: 1;
  background: transparent;
  border: none;
  color: var(--md-sys-color-on-surface);
  font-size: 14px;
  outline: none;
  height: 100%;
}

.search-input::placeholder {
  color: var(--md-sys-color-on-surface-variant);
  opacity: 0.7;
}

.clear-search-btn {
  background: transparent;
  border: none;
  color: var(--md-sys-color-on-surface-variant);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 4px;
  border-radius: 50%;
}

.clear-search-btn:hover {
  background: var(--md-sys-color-surface-variant);
  color: var(--md-sys-color-on-surface);
}

/* 列表容器 */
.plugin-list-container {
  flex: 1;
  overflow-y: auto;
  padding-bottom: 24px;
}

/* 网格布局 */
.plugin-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 24px;
}

/* 卡片样式 */
.plugin-card {
  background: var(--md-sys-color-surface-container-low);
  border: 1px solid var(--md-sys-color-outline-variant);
  border-radius: 16px;
  padding: 20px;
  cursor: pointer;
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  height: 100%;
  position: relative;
  overflow: hidden;
}

.plugin-card:hover {
  background: var(--md-sys-color-surface-container);
  transform: translateY(-2px);
  box-shadow: var(--md-sys-elevation-2);
  border-color: var(--md-sys-color-primary);
}

.card-content {
  display: flex;
  align-items: flex-start;
  gap: 16px;
  margin-bottom: 20px;
}

.plugin-icon-wrapper {
  width: 48px;
  height: 48px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--md-sys-color-on-primary-container);
  flex-shrink: 0;
}

.plugin-details {
  flex: 1;
  min-width: 0; /* 防止文本溢出 */
}

.plugin-name {
  font-size: 16px;
  font-weight: 600;
  color: var(--md-sys-color-on-surface);
  margin: 0 0 8px 0;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.plugin-path-container {
  display: flex;
  align-items: center;
  gap: 6px;
  color: var(--md-sys-color-on-surface-variant);
  font-size: 12px;
  background: var(--md-sys-color-surface-container-high);
  padding: 4px 8px;
  border-radius: 6px;
  width: fit-content;
  max-width: 100%;
}

.path-icon {
  font-size: 14px;
}

.plugin-path-text {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.card-actions {
  display: flex;
  justify-content: flex-end;
  border-top: 1px solid var(--md-sys-color-outline-variant);
  padding-top: 16px;
  margin-top: auto;
}

.action-btn {
  display: flex;
  align-items: center;
  gap: 8px;
  background: transparent;
  border: none;
  color: var(--md-sys-color-primary);
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  padding: 8px 16px;
  border-radius: 20px;
  transition: background 0.2s;
}

.action-btn:hover {
  background: var(--md-sys-color-primary-container);
  color: var(--md-sys-color-on-primary-container);
}

/* 状态样式 */
.loading-state, .error-state, .empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 64px 0;
  text-align: center;
  color: var(--md-sys-color-on-surface-variant);
}

.loading-spinner, .error-icon-container, .empty-icon-container {
  width: 64px;
  height: 64px;
  border-radius: 50%;
  background: var(--md-sys-color-surface-container-highest);
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 16px;
}

.loading-spinner span, .error-icon-container span, .empty-icon-container span {
  font-size: 32px;
}

.spinning {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

/* 响应式调整 */
@media (max-width: 600px) {
  .header-content {
    flex-direction: column;
    align-items: stretch;
  }
  
  .search-box {
    width: 100%;
  }
  
  .header-controls {
    width: 100%;
    justify-content: space-between;
  }
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
