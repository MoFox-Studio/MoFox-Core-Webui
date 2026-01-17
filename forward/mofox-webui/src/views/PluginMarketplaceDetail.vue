<!--
  @file PluginMarketplaceDetail.vue
  @description 插件市场详情页 - 现代化重构版
-->
<template>
  <div class="plugin-marketplace-detail">
    <!-- 顶部导航 -->
    <header class="page-header">
      <button class="m3-button text" @click="goBack">
        <span class="material-symbols-rounded">arrow_back</span>
        返回市场
      </button>
      <div class="header-title" v-if="pluginData">
        {{ pluginData.plugin.manifest.name }}
      </div>
    </header>

    <!-- 加载与错误状态 -->
    <div v-if="loading" class="state-container">
      <div class="loading-spinner"></div>
      <p>正在加载插件详情...</p>
    </div>
    
    <div v-else-if="loadError" class="state-container error">
      <span class="material-symbols-rounded icon">error_outline</span>
      <p>{{ loadError }}</p>
      <button class="m3-button filled" @click="loadPluginDetail">重新加载</button>
    </div>

    <!-- 主要内容区域 -->
    <div v-else-if="pluginData" class="main-content-grid">
      
      <!-- 左侧：侧边信息栏 (Sticky) -->
      <aside class="sidebar">
        <div class="plugin-card m3-card">
          <!-- 图标与标题 -->
          <div class="card-header">
            <div class="plugin-icon-large">
              <span class="material-symbols-rounded">{{ getPluginIcon() }}</span>
            </div>
            <h1 class="plugin-name">{{ pluginData.plugin.manifest.name }}</h1>
            <p class="plugin-desc-short">{{ pluginData.plugin.manifest.description }}</p>
          </div>

          <!-- 操作按钮区 -->
          <div class="card-actions">
            <button 
              v-if="!pluginData.is_installed"
              class="m3-button filled full-width" 
              @click="installPluginAction"
              :disabled="installing"
            >
              <span class="material-symbols-rounded" :class="{ spinning: installing }">
                {{ installing ? 'progress_activity' : 'download' }}
              </span>
              {{ installing ? '正在安装...' : '安装插件' }}
            </button>
            <button 
              v-else
              class="m3-button tonal full-width" 
              @click="goToConfig"
            >
              <span class="material-symbols-rounded">settings</span>
              配置插件
            </button>
            <a :href="pluginData.plugin.manifest.repository_url" target="_blank" class="m3-button text full-width repo-btn">
              <span class="material-symbols-rounded">open_in_new</span>
              访问仓库
            </a>
          </div>

          <div class="m3-divider"></div>

          <!-- 元数据列表 -->
          <div class="meta-list">
            <div class="meta-item">
              <span class="label">版本</span>
              <span class="value">v{{ pluginData.plugin.manifest.version }}</span>
            </div>
             <div class="meta-item" v-if="pluginData.is_installed">
              <span class="label">当前</span>
              <span class="value success-text">
                <span class="material-symbols-rounded small-icon">check_circle</span>
                已安装
              </span>
            </div>
            <div class="meta-item">
              <span class="label">作者</span>
              <span class="value">{{ pluginData.plugin.manifest.author }}</span>
            </div>
            <div class="meta-item">
              <span class="label">协议</span>
              <span class="value">{{ pluginData.plugin.manifest.license }}</span>
            </div>
            <div class="meta-item">
              <span class="label">ID</span>
              <span class="value mono">{{ pluginData.plugin.id }}</span>
            </div>
          </div>
        </div>

        <!-- 标签与分类 -->
        <div class="sidebar-section" v-if="hasTags">
          <h3 class="sidebar-title">标签</h3>
          <div class="tags-container">
            <span v-for="cat in pluginData.plugin.manifest.categories" :key="'cat-'+cat" class="m3-filter-chip category">
              {{ cat }}
            </span>
            <span v-for="kw in pluginData.plugin.manifest.keywords" :key="'kw-'+kw" class="m3-filter-chip">
              {{ kw }}
            </span>
          </div>
        </div>

        <!-- Python 依赖 -->
        <div class="sidebar-section" v-if="normalizedDependencies.length > 0">
          <h3 class="sidebar-title">Python 依赖</h3>
          <div class="dependencies-grid">
            <div v-for="dep in normalizedDependencies" :key="dep" class="dep-chip">
              <span class="material-symbols-rounded">package_2</span>
              {{ dep }}
            </div>
          </div>
        </div>
      </aside>

      <!-- 右侧：详细文档区域 -->
      <main class="content-area">
        
        <!-- 使用说明卡片 -->
        <section v-if="pluginData.plugin.manifest.usage" class="info-section m3-card">
          <h2 class="section-title">
            <span class="material-symbols-rounded">menu_book</span>
            使用说明
          </h2>
          <div class="usage-block">
            <pre>{{ pluginData.plugin.manifest.usage }}</pre>
          </div>
        </section>

        <!-- README 卡片 -->
        <section class="info-section m3-card readme-section">
          <div class="readme-header">
            <span class="material-symbols-rounded">article</span>
            README.md
          </div>
          
          <div v-if="pluginData.readme" class="readme-content markdown-body" v-html="renderedReadme"></div>
          <div v-else class="empty-readme">
            <span class="material-symbols-rounded">description</span>
            <p>暂无详细文档</p>
          </div>
        </section>

      </main>
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

// 状态管理
const loading = ref(true)
const loadError = ref('')
const installing = ref(false)
const pluginData = ref<PluginDetailResponse | null>(null)
const toast = ref({ show: false, message: '', type: 'success' as 'success' | 'error' })

// 计算属性：依赖列表标准化 (修复"每个字占一行"的问题)
const normalizedDependencies = computed(() => {
  const deps = pluginData.value?.plugin.manifest.python_dependencies
  if (!deps) return []
  if (Array.isArray(deps)) return deps
  // 如果后端意外返回了字符串，尝试分割或作为单项处理
  if (typeof deps === 'string') return [deps]
  return []
})

const hasTags = computed(() => {
  const m = pluginData.value?.plugin.manifest
  return (m?.categories?.length ?? 0) > 0 || (m?.keywords?.length ?? 0) > 0
})

// Markdown 渲染
const renderedReadme = computed(() => {
  if (!pluginData.value?.readme) return ''
  try {
    // 基础配置，防止 XSS (在真实项目中应使用 sanitize-html)
    return marked(pluginData.value.readme)
  } catch (e) {
    console.error('Markdown 渲染失败:', e)
    return '<div class="render-error">Markdown 渲染失败</div>'
  }
})

// 业务逻辑
function goBack() {
  router.push('/dashboard/marketplace')
}

function goToConfig() {
  router.push('/dashboard/plugin-config')
}

function getPluginIcon(): string {
  if (!pluginData.value) return 'extension'
  const categories = pluginData.value.plugin.manifest.categories || []
  if (categories.some(c => /fun|game/i.test(c))) return 'sports_esports'
  if (categories.some(c => /tool|utility/i.test(c))) return 'build'
  if (categories.some(c => /media|image/i.test(c))) return 'image'
  return 'extension'
}

async function loadPluginDetail() {
  loading.value = true
  loadError.value = ''
  
  const pluginId = route.params.pluginId as string
  if (!pluginId) {
    loadError.value = '未指定插件 ID'
    loading.value = false
    return
  }
  
  try {
    // 模拟延迟以展示加载动画 (可移除)
    // await new Promise(r => setTimeout(r, 300))
    const res = await getPluginDetail(decodeURIComponent(pluginId))
    
    // 健壮性处理：应对可能的双层嵌套数据结构
    let data : any = res.data;
    if (res.success) {
      if(data && data.success && data.data) {
          data = data.data; // 解包
      }
      pluginData.value = data as PluginDetailResponse;
    } else {
      loadError.value = res.error || '获取插件详情失败'
    }
  } catch (e) {
    loadError.value = '网络请求异常，请稍后重试'
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
    
    // 统一处理响应结果
    const responseData = res.data as any
    const isSuccess = res.success && (responseData?.success !== false)

    if (isSuccess) {
      showToast(`插件 ${pluginData.value?.plugin.manifest.name} 安装成功！`, 'success')
      await loadPluginDetail() // 刷新状态
    } else {
      const msg = responseData?.message || res.error || '未知错误'
      showToast(`安装失败: ${msg}`, 'error')
    }
  } catch (e) {
    showToast('安装过程中发生系统错误', 'error')
    console.error(e)
  } finally {
    installing.value = false
  }
}

function showToast(message: string, type: 'success' | 'error') {
  toast.value = { show: true, message, type }
  setTimeout(() => toast.value.show = false, 3000)
}

onMounted(() => {
  loadPluginDetail()
})
</script>

<style scoped>
/* 全局布局 */
.plugin-marketplace-detail {
  height: 100%;
  overflow: hidden; /* 内部滚动 */
  display: flex;
  flex-direction: column;
  background-color: var(--md-sys-color-background, #fdfcff);
  color: var(--md-sys-color-on-background);
  border-radius: 24px;
  font-family: 'JetBrains Mono', 'Fira Code', 'Roboto Mono', monospace;
}

.page-header {
  flex-shrink: 0;
  height: 64px;
  display: flex;
  align-items: center;
  padding: 0 16px;
  background: var(--md-sys-color-surface);
  border-bottom: 1px solid var(--md-sys-color-outline-variant);
  gap: 16px;
  z-index: 10;
}

.header-title {
  font-size: 18px;
  font-weight: 500;
  opacity: 0.8;
}

/* 状态展示 */
.state-container {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 16px;
  color: var(--md-sys-color-on-surface-variant);
}

.loading-spinner {
  width: 40px;
  height: 40px;
  border: 4px solid var(--md-sys-color-surface-container-high);
  border-top-color: var(--md-sys-color-primary);
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin { to { transform: rotate(360deg); } }

/* Grid 布局 */
.main-content-grid {
  flex: 1;
  overflow-y: auto;
  padding: 24px;
  display: grid;
  grid-template-columns: 320px minmax(0, 1fr);
  gap: 24px;
  max-width: 1600px;
  margin: 0 auto;
  width: 100%;
}

@media (max-width: 900px) {
  .main-content-grid {
    grid-template-columns: 1fr;
  }
}

/* 左侧栏 */
.sidebar {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.plugin-card {
  padding: 24px;
  background: var(--md-sys-color-surface);
  border-radius: 16px;
  border: 1px solid var(--md-sys-color-outline-variant);
  box-shadow: var(--md-sys-elevation-1);
}

.card-header {
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  margin-bottom: 24px;
}

.plugin-icon-large {
  width: 96px;
  height: 96px;
  background: var(--md-sys-color-tertiary-container);
  color: var(--md-sys-color-on-tertiary-container);
  border-radius: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 16px;
  box-shadow: var(--md-sys-elevation-2);
}

.plugin-icon-large .material-symbols-rounded {
  font-size: 48px;
}

.plugin-name {
  margin: 0 0 8px 0;
  font-size: 22px;
  font-weight: 600;
  line-height: 1.3;
  color: var(--md-sys-color-on-surface);
}

.plugin-desc-short {
  margin: 0;
  font-size: 14px;
  color: var(--md-sys-color-on-surface-variant);
  line-height: 1.5;
}

.card-actions {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-bottom: 24px;
}

.full-width {
  width: 100%;
  justify-content: center;
}

.m3-divider {
  height: 1px;
  background-color: var(--md-sys-color-outline-variant);
  margin: 16px 0;
}

.meta-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.meta-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 14px;
}

.meta-item .label {
  color: var(--md-sys-color-on-surface-variant);
}

.meta-item .value {
  color: var(--md-sys-color-on-surface);
  font-weight: 500;
  display: flex;
  align-items: center;
  gap: 4px;
}

.meta-item .mono {
  font-family: inherit;
  font-size: 12px;
  background: var(--md-sys-color-surface-container);
  padding: 2px 6px;
  border-radius: 4px;
}

.success-text {
  color: var(--md-sys-color-primary) !important;
}

.small-icon {
  font-size: 16px;
}

.sidebar-title {
  font-size: 14px;
  font-weight: 600;
  color: var(--md-sys-color-on-surface-variant);
  text-transform: uppercase;
  letter-spacing: 0.5px;
  margin: 0 0 12px 0;
}

.tags-container {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.m3-filter-chip {
  height: 32px;
  border-radius: 8px;
  padding: 0 12px;
  font-size: 13px;
  display: inline-flex;
  align-items: center;
  border: 1px solid var(--md-sys-color-outline);
  color: var(--md-sys-color-on-surface-variant);
  background: transparent;
}

.m3-filter-chip.category {
  background: var(--md-sys-color-secondary-container);
  color: var(--md-sys-color-on-secondary-container);
  border: none;
}

.dependencies-grid {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.dep-chip {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 6px 10px;
  background: var(--md-sys-color-surface-container);
  border-radius: 6px;
  font-size: 13px;
  font-family: inherit;
  color: var(--md-sys-color-on-surface);
}

.dep-chip .material-symbols-rounded {
  font-size: 16px;
  color: var(--md-sys-color-secondary);
}

/* 右侧内容区 */
.content-area {
  display: flex;
  flex-direction: column;
  gap: 24px;
  min-width: 0; /* 防止 grid 溢出 */
}

.info-section {
  background: var(--md-sys-color-surface);
  border-radius: 16px;
  border: 1px solid var(--md-sys-color-outline-variant);
  overflow: hidden;
}

.section-title {
  padding: 16px 24px;
  margin: 0;
  font-size: 18px;
  font-weight: 500;
  display: flex;
  align-items: center;
  gap: 12px;
  border-bottom: 1px solid var(--md-sys-color-outline-variant);
  background: var(--md-sys-color-surface-container-low);
}

.usage-block {
  padding: 24px;
  background: var(--md-sys-color-surface);
}

.usage-block pre {
  margin: 0;
  padding: 16px;
  background: var(--md-sys-color-surface-container-highest);
  border-radius: 8px;
  font-family: inherit;
  font-size: 13px;
  line-height: 1.5;
  white-space: pre-wrap;
  word-break: break-all;
  color: var(--md-sys-color-on-surface-variant);
}

/* README 美化 */
.readme-section {
  min-height: 400px;
}

.readme-header {
  padding: 12px 24px;
  background: var(--md-sys-color-surface-container);
  border-bottom: 1px solid var(--md-sys-color-outline-variant);
  font-size: 14px;
  font-weight: 500;
  color: var(--md-sys-color-on-surface-variant);
  display: flex;
  align-items: center;
  gap: 8px;
}

.readme-content {
  padding: 32px;
  width: 100%;
  box-sizing: border-box;
}

/* Markdown 专业样式 (Github/Modern 风格) */
.markdown-body :deep(h1),
.markdown-body :deep(h2),
.markdown-body :deep(h3),
.markdown-body :deep(h4) {
  margin-top: 24px;
  margin-bottom: 16px;
  font-weight: 600;
  line-height: 1.25;
  color: var(--md-sys-color-on-surface);
}

.markdown-body :deep(h1) { 
  font-size: 2em; 
  padding-bottom: .3em; 
  border-bottom: 1px solid var(--md-sys-color-outline-variant); 
}
.markdown-body :deep(h2) { 
  font-size: 1.5em; 
  padding-bottom: .3em; 
  border-bottom: 1px solid var(--md-sys-color-outline-variant); 
}
.markdown-body :deep(p) {
  margin-top: 0;
  margin-bottom: 16px;
  line-height: 1.6;
  color: var(--md-sys-color-on-surface-variant);
}

.markdown-body :deep(a) {
  color: var(--md-sys-color-primary);
  text-decoration: none;
}
.markdown-body :deep(a:hover) {
  text-decoration: underline;
}

.markdown-body :deep(code) {
  padding: .2em .4em;
  margin: 0;
  font-size: 85%;
  background-color: var(--md-sys-color-surface-container);
  border-radius: 6px;
  font-family: inherit;
}

.markdown-body :deep(pre) {
  padding: 16px;
  overflow: auto;
  font-size: 85%;
  line-height: 1.45;
  background-color: var(--md-sys-color-surface-container-low);
  border-radius: 8px;
  margin-bottom: 16px;
  border: 1px solid var(--md-sys-color-outline-variant);
}

.markdown-body :deep(pre code) {
  background-color: transparent;
  padding: 0;
}

.markdown-body :deep(blockquote) {
  padding: 0 1em;
  color: var(--md-sys-color-on-surface-variant);
  border-left: .25em solid var(--md-sys-color-outline-variant);
  margin: 0 0 16px 0;
  opacity: 0.8;
}

.markdown-body :deep(img) {
  max-width: 100%;
  box-sizing: content-box;
  background-color: var(--md-sys-color-surface);
  border-radius: 8px;
  border: 1px solid var(--md-sys-color-outline-variant);
}

.markdown-body :deep(ul),
.markdown-body :deep(ol) {
  padding-left: 2em;
  margin-bottom: 16px;
  color: var(--md-sys-color-on-surface-variant);
}

.markdown-body :deep(table) {
  border-spacing: 0;
  border-collapse: collapse;
  margin-bottom: 16px;
  width: 100%;
  overflow: auto;
  display: block; /* 响应式表格 */
}

.markdown-body :deep(table th),
.markdown-body :deep(table td) {
  padding: 6px 13px;
  border: 1px solid var(--md-sys-color-outline-variant);
}

.markdown-body :deep(table th) {
  font-weight: 600;
  background-color: var(--md-sys-color-surface-container);
}

.markdown-body :deep(table tr) {
  background-color: var(--md-sys-color-surface); 
}

.markdown-body :deep(table tr:nth-child(2n)) {
  background-color: var(--md-sys-color-surface-container-low);
}

.empty-readme {
  padding: 60px;
  text-align: center;
  color: var(--md-sys-color-outline);
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 16px;
}
.empty-readme .material-symbols-rounded {
  font-size: 48px;
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
