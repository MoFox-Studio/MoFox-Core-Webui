<template>
  <div class="plugin-marketplace-view">
    <!-- 顶部 -->
    <header class="page-header">
      <div class="header-content">
        <div class="header-left">
          <div class="header-icon-container">
            <span class="material-symbols-rounded header-icon">storefront</span>
          </div>
          <div class="header-info">
            <h1>插件市场</h1>
            <p>探索并安装 MoFox 社区插件</p>
          </div>
        </div>
        <div class="header-actions">
          <div class="search-box">
            <span class="material-symbols-rounded search-icon">search</span>
            <input 
              v-model="searchQuery" 
              type="text" 
              class="m3-input search-input"
              placeholder="搜索插件..."
              @input="handleSearch"
            />
          </div>
          <button class="m3-icon-button" @click="refreshMarketplace" :disabled="loading" title="刷新">
            <span class="material-symbols-rounded" :class="{ spinning: loading }">refresh</span>
          </button>
        </div>
      </div>
    </header>

    <!-- 分类筛选 -->
    <div class="category-filter">
      <button 
        v-for="category in categories" 
        :key="category"
        class="m3-filter-chip"
        :class="{ selected: selectedCategory === category }"
        @click="selectedCategory = category"
      >
        <span v-if="selectedCategory === category" class="material-symbols-rounded check-icon">check</span>
        {{ category }}
      </button>
    </div>

    <!-- 插件列表 -->
    <div class="marketplace-container">
      <div v-if="loading" class="loading-state">
        <span class="material-symbols-rounded spinning loading-icon">progress_activity</span>
        <p>加载插件市场...</p>
      </div>
      <div v-else-if="loadError" class="error-state">
        <span class="material-symbols-rounded error-icon">error</span>
        <p>{{ loadError }}</p>
        <button class="m3-button filled" @click="refreshMarketplace">重试</button>
      </div>
      <div v-else-if="filteredPlugins.length === 0" class="empty-state">
        <span class="material-symbols-rounded empty-icon">search_off</span>
        <p>未找到匹配的插件</p>
      </div>
      <div v-else class="plugin-grid">
        <div 
          v-for="plugin in filteredPlugins" 
          :key="plugin.id"
          class="m3-card plugin-card"
        >
          <div class="plugin-header">
            <div class="plugin-icon">
              <span class="material-symbols-rounded">{{ getPluginIcon(plugin) }}</span>
            </div>
            <div class="plugin-status">
              <span v-if="isInstalled(plugin)" class="status-badge success">
                <span class="material-symbols-rounded">check_circle</span>
                已安装
              </span>
            </div>
          </div>
          
          <div class="plugin-info">
            <h3>{{ plugin.manifest.name }}</h3>
            <p class="description">{{ plugin.manifest.description }}</p>
            
            <div class="plugin-meta">
              <span class="meta-item">
                <span class="material-symbols-rounded">person</span>
                {{ plugin.manifest.author }}
              </span>
              <span class="meta-item">
                <span class="material-symbols-rounded">sell</span>
                v{{ plugin.manifest.version }}
              </span>
            </div>

            <div v-if="plugin.manifest.keywords && plugin.manifest.keywords.length > 0" class="plugin-keywords">
              <span v-for="keyword in plugin.manifest.keywords.slice(0, 3)" :key="keyword" class="keyword-chip">
                {{ keyword }}
              </span>
            </div>
          </div>

          <div class="plugin-actions">
            <button class="m3-button text" @click="viewPluginDetail(plugin.id)">
              详情
            </button>
            <button 
              v-if="!isInstalled(plugin)"
              class="m3-button filled" 
              @click="installPluginAction(plugin)"
              :disabled="installingPlugins.has(plugin.id)"
            >
              <span class="material-symbols-rounded" :class="{ spinning: installingPlugins.has(plugin.id) }">
                {{ installingPlugins.has(plugin.id) ? 'progress_activity' : 'download' }}
              </span>
              {{ installingPlugins.has(plugin.id) ? '安装中...' : '安装' }}
            </button>
            <button 
              v-else
              class="m3-button tonal" 
              @click="viewPluginConfig()"
            >
              <span class="material-symbols-rounded">settings</span>
              配置
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
  getMarketplacePlugins,
  installPlugin,
  type MarketplacePlugin
} from '@/api/marketplace'

const router = useRouter()

// 状态
const loading = ref(true)
const loadError = ref('')
const plugins = ref<MarketplacePlugin[]>([])
const installedPlugins = ref<string[]>([])
const searchQuery = ref('')
const selectedCategory = ref('全部')
const installingPlugins = ref(new Set<string>())

// Toast
const toast = ref({ show: false, message: '', type: 'success' as 'success' | 'error' })

// 分类列表
const categories = computed(() => {
  const cats = new Set<string>(['全部'])
  if (plugins.value) {
    plugins.value.forEach(plugin => {
      if (plugin.manifest.categories) {
        plugin.manifest.categories.forEach(cat => cats.add(cat))
      }
    })
  }
  return Array.from(cats)
})

// 过滤后的插件列表
const filteredPlugins = computed(() => {
  if (!plugins.value) {
    return []
  }
  
  let result = plugins.value

  // 分类筛选
  if (selectedCategory.value !== '全部') {
    result = result.filter(p => 
      p.manifest.categories?.includes(selectedCategory.value)
    )
  }

  // 搜索筛选
  if (searchQuery.value) {
    const query = searchQuery.value.toLowerCase()
    result = result.filter(p => {
      const matchName = p.manifest.name.toLowerCase().includes(query)
      const matchDesc = p.manifest.description.toLowerCase().includes(query)
      const matchKeywords = p.manifest.keywords?.some(k => 
        k.toLowerCase().includes(query)
      )
      return matchName || matchDesc || matchKeywords
    })
  }

  return result
})

// 方法
function isInstalled(plugin: MarketplacePlugin): boolean {
  // 检查必要属性是否存在
  if (!plugin?.manifest?.repository_url) {
    return false
  }
  // 使用仓库名检查是否安装
  const repoName = plugin.manifest.repository_url.split('/').pop() || ''
  return installedPlugins.value.includes(repoName)
}

function getPluginIcon(plugin: MarketplacePlugin): string {
  if (!plugin?.manifest) return 'extension'
  const categories = plugin.manifest.categories || []
  if (categories.includes('Entertainment') || categories.includes('Fun')) return 'sentiment_satisfied'
  if (categories.includes('Games')) return 'sports_esports'
  if (categories.includes('Tools')) return 'build'
  return 'extension'
}

function viewPluginDetail(pluginId: string) {
  router.push(`/dashboard/marketplace/${pluginId}`)
}

function viewPluginConfig() {
  // 跳转到插件配置主页面
  router.push('/dashboard/plugin-config')
}

async function installPluginAction(plugin: MarketplacePlugin) {
  installingPlugins.value.add(plugin.id)
  
  try {
    const res = await installPlugin(plugin.id, plugin.manifest.repository_url, true)
    console.log('安装响应:', res)
    
    if (res.success && res.data) {
      // 处理双重嵌套
      const responseData = res.data as any
      if (responseData.success) {
        // 后端已经自动加载了，直接提示成功
        showToast(`插件 ${plugin.manifest.name} 安装成功！`, 'success')
        // 使用仓库名添加到已安装列表
        const repoName = plugin.manifest.repository_url.split('/').pop() || ''
        installedPlugins.value.push(repoName)
      } else {
        showToast(`安装失败: ${responseData.error || '未知错误'}`, 'error')
      }
    } else {
      showToast(`安装请求失败: ${res.error || '未知错误'}`, 'error')
    }
  } catch (e) {
    showToast('安装插件时发生错误', 'error')
    console.error(e)
  } finally {
    installingPlugins.value.delete(plugin.id)
  }
}

async function refreshMarketplace() {
  loading.value = true
  loadError.value = ''
  
  try {
    const res = await getMarketplacePlugins()
    console.log('API 响应:', res)
    
    if (res.success && res.data) {
      // 后端返回的数据结构是 { success, data: { plugins, installed_plugins } }
      // API 客户端又包装了一层，所以需要访问 res.data.data
      const responseData = res.data as any
      if (responseData.success && responseData.data) {
        plugins.value = responseData.data.plugins || []
        installedPlugins.value = responseData.data.installed_plugins || []
      } else {
        loadError.value = responseData.error || '获取插件市场数据失败'
        plugins.value = []
        installedPlugins.value = []
      }
    } else {
      loadError.value = res.error || '获取插件市场数据失败'
      plugins.value = []
      installedPlugins.value = []
    }
  } catch (e) {
    loadError.value = '加载插件市场时发生错误'
    plugins.value = []
    installedPlugins.value = []
    console.error(e)
  } finally {
    loading.value = false
  }
}

function handleSearch() {
  // 搜索由 computed 自动处理
}

function showToast(message: string, type: 'success' | 'error') {
  toast.value = { show: true, message, type }
  setTimeout(() => {
    toast.value.show = false
  }, 3000)
}

onMounted(() => {
  refreshMarketplace()
})
</script>

<style scoped>
.plugin-marketplace-view {
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

/* 页面标题 */
.page-header {
  padding: 0 8px;
}

.header-content {
  display: flex;
  align-items: center;
  justify-content: space-between;
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

.search-box {
  position: relative;
  width: 240px;
}

.search-icon {
  position: absolute;
  left: 12px;
  top: 50%;
  transform: translateY(-50%);
  font-size: 20px;
  color: var(--md-sys-color-on-surface-variant);
  pointer-events: none;
}

.search-input {
  padding-left: 44px;
  width: 100%;
}

/* 分类筛选 */
.category-filter {
  display: flex;
  gap: 8px;
  padding: 0 8px;
  overflow-x: auto;
  padding-bottom: 4px;
}

.m3-filter-chip {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 16px;
  border: 1px solid var(--md-sys-color-outline);
  border-radius: 8px;
  background: transparent;
  color: var(--md-sys-color-on-surface-variant);
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
  white-space: nowrap;
}

.m3-filter-chip:hover {
  background: var(--md-sys-color-surface-container-highest);
}

.m3-filter-chip.selected {
  background: var(--md-sys-color-secondary-container);
  color: var(--md-sys-color-on-secondary-container);
  border-color: transparent;
}

.check-icon {
  font-size: 18px;
}

/* 插件列表 */
.marketplace-container {
  flex: 1;
  overflow-y: auto;
  padding: 8px;
}

.plugin-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: 16px;
}

.plugin-card {
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 16px;
  transition: all 0.2s;
}

.plugin-card:hover {
  transform: translateY(-2px);
  box-shadow: var(--md-sys-elevation-2);
}

.plugin-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
}

.plugin-icon {
  width: 56px;
  height: 56px;
  border-radius: 16px;
  background: var(--md-sys-color-tertiary-container);
  color: var(--md-sys-color-on-tertiary-container);
  display: flex;
  align-items: center;
  justify-content: center;
}

.plugin-icon .material-symbols-rounded {
  font-size: 28px;
}

.status-badge {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 4px 8px;
  border-radius: 6px;
  font-size: 12px;
  font-weight: 500;
}

.status-badge.success {
  background: var(--md-sys-color-primary-container);
  color: var(--md-sys-color-on-primary-container);
}

.status-badge .material-symbols-rounded {
  font-size: 16px;
}

.plugin-info h3 {
  font-size: 16px;
  font-weight: 600;
  color: var(--md-sys-color-on-surface);
  margin: 0 0 8px;
}

.description {
  font-size: 14px;
  color: var(--md-sys-color-on-surface-variant);
  line-height: 1.5;
  margin: 0 0 12px;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.plugin-meta {
  display: flex;
  gap: 16px;
  margin-bottom: 12px;
}

.meta-item {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
  color: var(--md-sys-color-on-surface-variant);
}

.meta-item .material-symbols-rounded {
  font-size: 16px;
}

.plugin-keywords {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.keyword-chip {
  padding: 2px 8px;
  background: var(--md-sys-color-surface-container-highest);
  border-radius: 6px;
  font-size: 11px;
  color: var(--md-sys-color-on-surface-variant);
}

.plugin-actions {
  display: flex;
  gap: 8px;
  margin-top: auto;
}

.plugin-actions button {
  flex: 1;
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
  padding: 40px;
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
</style>
