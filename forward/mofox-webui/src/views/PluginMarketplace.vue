<template>
  <div class="plugin-marketplace">
    <!-- 顶部 -->
    <header class="page-header">
      <div class="header-left">
        <Icon icon="lucide:store" class="header-icon" />
        <div class="header-info">
          <h1>插件市场</h1>
          <p>探索并安装 MoFox 社区插件</p>
        </div>
      </div>
      <div class="header-actions">
        <div class="search-box">
          <Icon icon="lucide:search" />
          <input 
            v-model="searchQuery" 
            type="text" 
            placeholder="搜索插件..."
            @input="handleSearch"
          />
        </div>
        <button class="btn btn-ghost" @click="refreshMarketplace" :disabled="loading">
          <Icon :icon="loading ? 'lucide:loader-2' : 'lucide:refresh-cw'" :class="{ spinning: loading }" />
          刷新
        </button>
      </div>
    </header>

    <!-- 分类筛选 -->
    <div class="category-filter">
      <button 
        v-for="category in categories" 
        :key="category"
        :class="['category-btn', { active: selectedCategory === category }]"
        @click="selectedCategory = category"
      >
        {{ category }}
      </button>
    </div>

    <!-- 插件列表 -->
    <div class="marketplace-container">
      <div v-if="loading" class="loading-state">
        <Icon icon="lucide:loader-2" class="spinning" />
        加载插件市场...
      </div>
      <div v-else-if="loadError" class="error-state">
        <Icon icon="lucide:alert-circle" />
        {{ loadError }}
        <button class="btn btn-primary" @click="refreshMarketplace">重试</button>
      </div>
      <div v-else-if="filteredPlugins.length === 0" class="empty-state">
        <Icon icon="lucide:search-x" />
        <p>未找到匹配的插件</p>
      </div>
      <div v-else class="plugin-grid">
        <div 
          v-for="plugin in filteredPlugins" 
          :key="plugin.id"
          class="plugin-card"
        >
          <div class="plugin-header">
            <div class="plugin-icon">
              <Icon :icon="getPluginIcon(plugin)" />
            </div>
            <div class="plugin-status">
              <span v-if="isInstalled(plugin)" class="badge badge-success">
                <Icon icon="lucide:check-circle" />
                已安装
              </span>
              <span v-else class="badge badge-default">
                <Icon icon="lucide:download" />
                未安装
              </span>
            </div>
          </div>
          
          <div class="plugin-info">
            <h3>{{ plugin.manifest.name }}</h3>
            <p class="description">{{ plugin.manifest.description }}</p>
            
            <div class="plugin-meta">
              <span class="meta-item">
                <Icon icon="lucide:user" />
                {{ plugin.manifest.author }}
              </span>
              <span class="meta-item">
                <Icon icon="lucide:tag" />
                v{{ plugin.manifest.version }}
              </span>
            </div>

            <div v-if="plugin.manifest.keywords && plugin.manifest.keywords.length > 0" class="plugin-keywords">
              <span v-for="keyword in plugin.manifest.keywords.slice(0, 3)" :key="keyword" class="keyword">
                {{ keyword }}
              </span>
            </div>
          </div>

          <div class="plugin-actions">
            <button class="btn btn-ghost" @click="viewPluginDetail(plugin.id)">
              <Icon icon="lucide:info" />
              详情
            </button>
            <button 
              v-if="!isInstalled(plugin)"
              class="btn btn-primary" 
              @click="installPluginAction(plugin)"
              :disabled="installingPlugins.has(plugin.id)"
            >
              <Icon :icon="installingPlugins.has(plugin.id) ? 'lucide:loader-2' : 'lucide:download'" 
                    :class="{ spinning: installingPlugins.has(plugin.id) }" />
              {{ installingPlugins.has(plugin.id) ? '安装中...' : '安装' }}
            </button>
            <button 
              v-else
              class="btn btn-secondary" 
              @click="viewPluginConfig()"
            >
              <Icon icon="lucide:settings" />
              配置
            </button>
          </div>
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
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { Icon } from '@iconify/vue'
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
  // 使用仓库名检查是否安装
  const repoName = plugin.manifest.repository_url.split('/').pop() || ''
  return installedPlugins.value.includes(repoName)
}

function getPluginIcon(plugin: MarketplacePlugin): string {
  const categories = plugin.manifest.categories || []
  if (categories.includes('Entertainment') || categories.includes('Fun')) return 'lucide:smile'
  if (categories.includes('Games')) return 'lucide:gamepad-2'
  if (categories.includes('Tools')) return 'lucide:wrench'
  return 'lucide:puzzle'
}

function viewPluginDetail(pluginId: string) {
  router.push(`/dashboard/marketplace/${encodeURIComponent(pluginId)}`)
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
        showToast(`安装失败: ${responseData.message || '未知错误'}`, 'error')
      }
    } else {
      showToast(`安装失败: ${res.error || '未知错误'}`, 'error')
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
.plugin-marketplace {
  height: 100%;
  display: flex;
  flex-direction: column;
  animation: fadeIn 0.4s ease-out;
}

.page-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 24px 32px;
  background: rgba(255, 255, 255, 0.8);
  backdrop-filter: blur(12px);
  border-bottom: 1px solid rgba(0, 0, 0, 0.05);
  position: sticky;
  top: 0;
  z-index: 10;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 16px;
}

.header-icon {
  font-size: 32px;
  color: var(--primary);
  background: rgba(249, 115, 22, 0.1);
  padding: 10px;
  border-radius: 12px;
}

.header-info h1 {
  margin: 0 0 4px 0;
  font-size: 24px;
  font-weight: 700;
  color: var(--text-primary);
  letter-spacing: -0.5px;
}

.header-info p {
  margin: 0;
  font-size: 14px;
  color: var(--text-secondary);
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 16px;
}

.search-box {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 16px;
  background: white;
  border: 1px solid var(--border-color);
  border-radius: 12px;
  transition: all 0.3s ease;
  box-shadow: 0 2px 4px rgba(0,0,0,0.02);
}

.search-box:focus-within {
  border-color: var(--primary);
  box-shadow: 0 0 0 3px rgba(249, 115, 22, 0.1);
  transform: translateY(-1px);
}

.search-box input {
  border: none;
  background: transparent;
  outline: none;
  width: 240px;
  color: var(--text-primary);
  font-size: 14px;
}

.category-filter {
  display: flex;
  gap: 10px;
  padding: 16px 32px;
  background: rgba(255, 255, 255, 0.6);
  border-bottom: 1px solid rgba(0, 0, 0, 0.05);
  overflow-x: auto;
  backdrop-filter: blur(8px);
}

.category-btn {
  padding: 8px 16px;
  border: 1px solid transparent;
  border-radius: 20px;
  background: rgba(255, 255, 255, 0.5);
  color: var(--text-secondary);
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  white-space: nowrap;
  transition: all 0.2s ease;
}

.category-btn:hover {
  background: white;
  color: var(--primary);
  transform: translateY(-1px);
  box-shadow: 0 2px 4px rgba(0,0,0,0.05);
}

.category-btn.active {
  background: var(--primary);
  color: white;
  box-shadow: 0 4px 12px rgba(249, 115, 22, 0.2);
}

.marketplace-container {
  flex: 1;
  overflow: auto;
  padding: 32px;
  background: var(--bg-secondary);
}

.plugin-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(360px, 1fr));
  gap: 24px;
}

.plugin-card {
  background: white;
  border: 1px solid rgba(0,0,0,0.05);
  border-radius: 16px;
  padding: 24px;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  display: flex;
  flex-direction: column;
  gap: 20px;
  position: relative;
  overflow: hidden;
}

.plugin-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 4px;
  background: linear-gradient(90deg, var(--primary), #fb923c);
  opacity: 0;
  transition: opacity 0.3s ease;
}

.plugin-card:hover {
  border-color: rgba(249, 115, 22, 0.2);
  box-shadow: 0 12px 32px rgba(0, 0, 0, 0.08);
  transform: translateY(-4px);
}

.plugin-card:hover::before {
  opacity: 1;
}

.plugin-header {
  display: flex;
  justify-content: space-between;
  align-items: start;
}

.plugin-icon {
  width: 64px;
  height: 64px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #fff7ed, #ffedd5);
  border-radius: 16px;
  color: var(--primary);
  font-size: 32px;
  box-shadow: inset 0 2px 4px rgba(255,255,255,0.5);
}

.plugin-status .badge {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 12px;
  border-radius: 20px;
  font-size: 12px;
  font-weight: 600;
}

.badge-success {
  background: #ecfdf5;
  color: #059669;
  border: 1px solid rgba(16, 185, 129, 0.1);
}

.badge-default {
  background: #f3f4f6;
  color: #6b7280;
}

.plugin-info h3 {
  font-size: 18px;
  font-weight: 700;
  color: var(--text-primary);
  margin: 0 0 8px 0;
}

.description {
  font-size: 14px;
  color: var(--text-secondary);
  line-height: 1.6;
  margin: 0 0 16px 0;
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
  padding-bottom: 16px;
  border-bottom: 1px solid rgba(0,0,0,0.05);
}

.meta-item {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  color: var(--text-tertiary);
}

.plugin-keywords {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.keyword {
  padding: 4px 10px;
  background: #f8fafc;
  border: 1px solid rgba(0,0,0,0.05);
  border-radius: 6px;
  font-size: 12px;
  color: var(--text-secondary);
  font-weight: 500;
}

.plugin-actions {
  display: flex;
  gap: 12px;
  margin-top: auto;
  padding-top: 4px;
}

.btn {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 10px 16px;
  border: none;
  border-radius: 10px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
}

.btn-primary {
  background: linear-gradient(135deg, var(--primary), #ea580c);
  color: white;
  box-shadow: 0 4px 12px rgba(249, 115, 22, 0.2);
}

.btn-primary:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: 0 6px 16px rgba(249, 115, 22, 0.3);
}

.btn-secondary {
  background: white;
  border: 1px solid var(--border-color);
  color: var(--text-primary);
}

.btn-secondary:hover {
  background: #f8fafc;
  border-color: var(--text-tertiary);
}

.btn-ghost {
  background: transparent;
  color: var(--text-secondary);
}

.btn-ghost:hover:not(:disabled) {
  background: rgba(0,0,0,0.03);
  color: var(--text-primary);
}

.btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
  filter: grayscale(1);
}

.spinning {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
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
  background: white;
  border-radius: 12px;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.1);
  font-size: 14px;
  font-weight: 500;
  z-index: 2000;
  animation: slideIn 0.4s cubic-bezier(0.16, 1, 0.3, 1);
  border: 1px solid rgba(0,0,0,0.05);
}

.toast.success {
  border-left: 4px solid #10b981;
  color: #065f46;
}

.toast.error {
  border-left: 4px solid #ef4444;
  color: #991b1b;
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
}

.loading-state svg,
.error-state svg,
.empty-state svg {
  font-size: 64px;
  opacity: 0.3;
  color: var(--primary);
}

.error-state {
  color: #ef4444;
}
</style>
