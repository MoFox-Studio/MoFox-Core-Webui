<template>
  <div class="plugin-marketplace-detail">
    <!-- 顶部导航 -->
    <header class="page-header">
      <button class="m3-button text" @click="goBack">
        <span class="material-symbols-rounded">arrow_back</span>
        返回市场
      </button>
      <div class="header-actions" v-if="!loading && pluginData">
        <button 
          v-if="!pluginData.is_installed"
          class="m3-button filled" 
          @click="installPluginAction"
          :disabled="installing"
        >
          <span class="material-symbols-rounded" :class="{ spinning: installing }">
            {{ installing ? 'progress_activity' : 'download' }}
          </span>
          {{ installing ? '安装中...' : '安装插件' }}
        </button>
        <button 
          v-else
          class="m3-button tonal" 
          @click="goToConfig"
        >
          <span class="material-symbols-rounded">settings</span>
          配置插件
        </button>
      </div>
    </header>

    <!-- 内容区域 -->
    <div class="detail-container">
      <div v-if="loading" class="loading-state">
        <span class="material-symbols-rounded spinning loading-icon">progress_activity</span>
        <p>加载插件详情...</p>
      </div>
      <div v-else-if="loadError" class="error-state">
        <span class="material-symbols-rounded error-icon">error</span>
        <p>{{ loadError }}</p>
        <button class="m3-button filled" @click="loadPluginDetail">重试</button>
      </div>
      <div v-else-if="pluginData" class="detail-content">
        <!-- 插件基本信息 -->
        <div class="m3-card plugin-header-info">
          <div class="plugin-icon">
            <span class="material-symbols-rounded">{{ getPluginIcon() }}</span>
          </div>
          <div class="plugin-title-section">
            <h1>{{ pluginData.plugin.manifest.name }}</h1>
            <div class="plugin-badges">
              <span class="m3-assist-chip">
                <span class="material-symbols-rounded">sell</span>
                v{{ pluginData.plugin.manifest.version }}
              </span>
              <span v-if="pluginData.is_installed" class="m3-assist-chip success">
                <span class="material-symbols-rounded">check_circle</span>
                已安装 {{ pluginData.installed_version ? (v) : '' }}
              </span>
              <span class="m3-assist-chip">
                <span class="material-symbols-rounded">person</span>
                {{ pluginData.plugin.manifest.author }}
              </span>
              <span class="m3-assist-chip">
                <span class="material-symbols-rounded">description</span>
                {{ pluginData.plugin.manifest.license }}
              </span>
            </div>
          </div>
        </div>

        <!-- 描述 -->
        <div class="m3-card section">
          <h2>
            <span class="material-symbols-rounded">subject</span>
            描述
          </h2>
          <p class="description-text">{{ pluginData.plugin.manifest.description }}</p>
        </div>

        <!-- 关键词 -->
        <div v-if="pluginData.plugin.manifest.keywords && pluginData.plugin.manifest.keywords.length > 0" class="m3-card section">
          <h2>
            <span class="material-symbols-rounded">tag</span>
            关键词
          </h2>
          <div class="keywords-list">
            <span v-for="keyword in pluginData.plugin.manifest.keywords" :key="keyword" class="m3-filter-chip">
              {{ keyword }}
            </span>
          </div>
        </div>

        <!-- 分类 -->
        <div v-if="pluginData.plugin.manifest.categories && pluginData.plugin.manifest.categories.length > 0" class="m3-card section">
          <h2>
            <span class="material-symbols-rounded">folder</span>
            分类
          </h2>
          <div class="categories-list">
            <span v-for="category in pluginData.plugin.manifest.categories" :key="category" class="m3-filter-chip">
              {{ category }}
            </span>
          </div>
        </div>

        <!-- Python 依赖 -->
        <div v-if="pluginData.plugin.manifest.python_dependencies && pluginData.plugin.manifest.python_dependencies.length > 0" class="m3-card section">
          <h2>
            <span class="material-symbols-rounded">package</span>
            Python 依赖
          </h2>
          <ul class="dependencies-list">
            <li v-for="dep in pluginData.plugin.manifest.python_dependencies" :key="dep">
              <span class="material-symbols-rounded bullet">circle</span>
              {{ dep }}
            </li>
          </ul>
        </div>

        <!-- 使用说明 -->
        <div v-if="pluginData.plugin.manifest.usage" class="m3-card section">
          <h2>
            <span class="material-symbols-rounded">menu_book</span>
            使用说明
          </h2>
          <pre class="usage-text">{{ pluginData.plugin.manifest.usage }}</pre>
        </div>

        <!-- README -->
        <div v-if="pluginData.readme" class="m3-card section">
          <h2>
            <span class="material-symbols-rounded">description</span>
            README
          </h2>
          <div class="readme-content" v-html="renderedReadme"></div>
        </div>

        <!-- 仓库链接 -->
        <div class="m3-card section">
          <h2>
            <span class="material-symbols-rounded">code</span>
            仓库地址
          </h2>
          <a :href="pluginData.plugin.manifest.repository_url" target="_blank" class="repo-link">
            {{ pluginData.plugin.manifest.repository_url }}
            <span class="material-symbols-rounded">open_in_new</span>
          </a>
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
import { useRouter, useRoute } from 'vue-router'
import { marked } from 'marked'
import {
  getPluginDetail,
  installPlugin,
  type PluginDetailResponse
} from '@/api/marketplace'

const router = useRouter()
const route = useRoute()

// 状态
const loading = ref(true)
const loadError = ref('')
const installing = ref(false)
const pluginData = ref<PluginDetailResponse | null>(null)

// Toast
const toast = ref({ show: false, message: '', type: 'success' as 'success' | 'error' })

// 渲染的 README
const renderedReadme = computed(() => {
  if (!pluginData.value?.readme) return ''
  try {
    return marked(pluginData.value.readme)
  } catch (e) {
    console.error('Markdown 渲染失败:', e)
    return '<pre>Markdown 渲染失败</pre>'
  }
})

// 方法
function goBack() {
  router.push('/dashboard/marketplace')
}

function goToConfig() {
  // 跳转到插件配置主页面
  router.push('/dashboard/plugin-config')
}

function getPluginIcon(): string {
  if (!pluginData.value) return 'extension'
  
  const categories = pluginData.value.plugin.manifest.categories || []
  if (categories.includes('Entertainment') || categories.includes('Fun')) return 'sentiment_satisfied'
  if (categories.includes('Games')) return 'sports_esports'
  if (categories.includes('Tools')) return 'build'
  return 'extension'
}

async function loadPluginDetail() {
  loading.value = true
  loadError.value = ''
  
  const pluginId = route.params.pluginId as string
  
  try {
    const res = await getPluginDetail(decodeURIComponent(pluginId))
    console.log('详情响应:', res)
    
    if (res.success && res.data) {
      // 处理双重嵌套
      const responseData = res.data as any
      if (responseData.success && responseData.data) {
        pluginData.value = responseData.data
      } else {
        loadError.value = responseData.error || '获取插件详情失败'
      }
    } else {
      loadError.value = res.error || '获取插件详情失败'
    }
  } catch (e) {
    loadError.value = '加载插件详情时发生错误'
    console.error(e)
  } finally {
    loading.value = false
  }
}

async function installPluginAction() {
  if (!pluginData.value) return
  
  installing.value = true
  
  try {
    const res = await installPlugin(
      pluginData.value.plugin.id,
      pluginData.value.plugin.manifest.repository_url,
      true
    )
    
    console.log('安装响应:', res)
    
    if (res.success && res.data) {
      // 处理双重嵌套
      const responseData = res.data as any
      if (responseData.success) {
        // 后端已经自动加载了，直接提示成功
        showToast(`插件 ${pluginData.value?.manifest.name} 安装成功！`, 'success')
        
        // 重新加载插件详情以更新状态
        await loadPluginDetail()
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
    installing.value = false
  }
}

function showToast(message: string, type: 'success' | 'error') {
  toast.value = { show: true, message, type }
  setTimeout(() => {
    toast.value.show = false
  }, 3000)
}

onMounted(() => {
  loadPluginDetail()
})
</script>

<style scoped>
.plugin-marketplace-detail {
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

.page-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 8px;
}

.header-actions {
  display: flex;
  gap: 12px;
}

.detail-container {
  flex: 1;
  overflow-y: auto;
  padding: 8px;
}

.detail-content {
  max-width: 900px;
  margin: 0 auto;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.plugin-header-info {
  display: flex;
  align-items: start;
  gap: 24px;
  padding: 32px;
}

.plugin-icon {
  width: 80px;
  height: 80px;
  min-width: 80px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--md-sys-color-tertiary-container);
  color: var(--md-sys-color-on-tertiary-container);
  border-radius: 24px;
}

.plugin-icon .material-symbols-rounded {
  font-size: 40px;
}

.plugin-title-section h1 {
  margin: 0 0 16px 0;
  font-size: 28px;
  font-weight: 400;
  color: var(--md-sys-color-on-surface);
}

.plugin-badges {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.m3-assist-chip {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 6px 16px;
  border: 1px solid var(--md-sys-color-outline);
  border-radius: 8px;
  font-size: 14px;
  font-weight: 500;
  color: var(--md-sys-color-on-surface-variant);
}

.m3-assist-chip.success {
  background: var(--md-sys-color-primary-container);
  color: var(--md-sys-color-on-primary-container);
  border-color: transparent;
}

.m3-assist-chip .material-symbols-rounded {
  font-size: 18px;
}

.section {
  padding: 24px;
}

.section h2 {
  display: flex;
  align-items: center;
  gap: 12px;
  margin: 0 0 16px 0;
  font-size: 18px;
  font-weight: 500;
  color: var(--md-sys-color-on-surface);
}

.description-text {
  margin: 0;
  font-size: 14px;
  line-height: 1.6;
  color: var(--md-sys-color-on-surface-variant);
}

.keywords-list,
.categories-list {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.m3-filter-chip {
  padding: 6px 16px;
  border: 1px solid var(--md-sys-color-outline);
  border-radius: 8px;
  font-size: 13px;
  color: var(--md-sys-color-on-surface-variant);
}

.dependencies-list {
  list-style: none;
  margin: 0;
  padding: 0;
}

.dependencies-list li {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 8px 0;
  font-size: 14px;
  color: var(--md-sys-color-on-surface-variant);
  font-family: 'JetBrains Mono', monospace;
}

.bullet {
  font-size: 8px;
  color: var(--md-sys-color-outline);
}

.usage-text {
  margin: 0;
  padding: 16px;
  background: var(--md-sys-color-surface-container-highest);
  border-radius: 12px;
  font-size: 13px;
  line-height: 1.6;
  color: var(--md-sys-color-on-surface-variant);
  white-space: pre-wrap;
  overflow-x: auto;
  font-family: 'JetBrains Mono', monospace;
}

.readme-content {
  padding: 24px;
  background: var(--md-sys-color-surface-container-low);
  border-radius: 12px;
  font-size: 14px;
  line-height: 1.7;
  color: var(--md-sys-color-on-surface-variant);
}

.readme-content :deep(h1),
.readme-content :deep(h2),
.readme-content :deep(h3) {
  margin-top: 24px;
  margin-bottom: 16px;
  color: var(--md-sys-color-on-surface);
  font-weight: 500;
}

.readme-content :deep(code) {
  padding: 2px 6px;
  background: var(--md-sys-color-surface-container-highest);
  border-radius: 4px;
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.9em;
}

.readme-content :deep(pre) {
  padding: 16px;
  background: var(--md-sys-color-surface-container-highest);
  border-radius: 8px;
  overflow-x: auto;
  margin: 16px 0;
}

.readme-content :deep(a) {
  color: var(--md-sys-color-primary);
  text-decoration: none;
}

.readme-content :deep(a:hover) {
  text-decoration: underline;
}

.repo-link {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 12px 20px;
  background: var(--md-sys-color-surface-container-highest);
  border-radius: 12px;
  color: var(--md-sys-color-primary);
  text-decoration: none;
  font-size: 14px;
  transition: all 0.2s;
}

.repo-link:hover {
  background: var(--md-sys-color-secondary-container);
  color: var(--md-sys-color-on-secondary-container);
}

/* 状态展示 */
.loading-state, .error-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  gap: 16px;
  color: var(--md-sys-color-on-surface-variant);
  padding: 40px;
}

.loading-icon, .error-icon {
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
