<template>
  <div class="plugin-marketplace-detail">
    <!-- 顶部导航 -->
    <header class="page-header">
      <button class="btn btn-ghost back-btn" @click="goBack">
        <Icon icon="lucide:arrow-left" />
        返回市场
      </button>
      <div class="header-actions" v-if="!loading && pluginData">
        <button 
          v-if="!pluginData.is_installed"
          class="btn btn-primary" 
          @click="installPluginAction"
          :disabled="installing"
        >
          <Icon :icon="installing ? 'lucide:loader-2' : 'lucide:download'" 
                :class="{ spinning: installing }" />
          {{ installing ? '安装中...' : '安装插件' }}
        </button>
        <button 
          v-else
          class="btn btn-secondary" 
          @click="goToConfig"
        >
          <Icon icon="lucide:settings" />
          配置插件
        </button>
      </div>
    </header>

    <!-- 内容区域 -->
    <div class="detail-container">
      <div v-if="loading" class="loading-state">
        <Icon icon="lucide:loader-2" class="spinning" />
        加载插件详情...
      </div>
      <div v-else-if="loadError" class="error-state">
        <Icon icon="lucide:alert-circle" />
        {{ loadError }}
        <button class="btn btn-primary" @click="loadPluginDetail">重试</button>
      </div>
      <div v-else-if="pluginData" class="detail-content">
        <!-- 插件基本信息 -->
        <div class="plugin-header-info">
          <div class="plugin-icon">
            <Icon :icon="getPluginIcon()" />
          </div>
          <div class="plugin-title-section">
            <h1>{{ pluginData.plugin.manifest.name }}</h1>
            <div class="plugin-badges">
              <span class="badge badge-version">
                <Icon icon="lucide:tag" />
                v{{ pluginData.plugin.manifest.version }}
              </span>
              <span v-if="pluginData.is_installed" class="badge badge-success">
                <Icon icon="lucide:check-circle" />
                已安装 {{ pluginData.installed_version ? `(v${pluginData.installed_version})` : '' }}
              </span>
              <span class="badge badge-author">
                <Icon icon="lucide:user" />
                {{ pluginData.plugin.manifest.author }}
              </span>
              <span class="badge badge-license">
                <Icon icon="lucide:file-text" />
                {{ pluginData.plugin.manifest.license }}
              </span>
            </div>
          </div>
        </div>

        <!-- 描述 -->
        <div class="section">
          <h2>
            <Icon icon="lucide:align-left" />
            描述
          </h2>
          <p class="description-text">{{ pluginData.plugin.manifest.description }}</p>
        </div>

        <!-- 关键词 -->
        <div v-if="pluginData.plugin.manifest.keywords && pluginData.plugin.manifest.keywords.length > 0" class="section">
          <h2>
            <Icon icon="lucide:hash" />
            关键词
          </h2>
          <div class="keywords-list">
            <span v-for="keyword in pluginData.plugin.manifest.keywords" :key="keyword" class="keyword-tag">
              {{ keyword }}
            </span>
          </div>
        </div>

        <!-- 分类 -->
        <div v-if="pluginData.plugin.manifest.categories && pluginData.plugin.manifest.categories.length > 0" class="section">
          <h2>
            <Icon icon="lucide:folder" />
            分类
          </h2>
          <div class="categories-list">
            <span v-for="category in pluginData.plugin.manifest.categories" :key="category" class="category-tag">
              {{ category }}
            </span>
          </div>
        </div>

        <!-- Python 依赖 -->
        <div v-if="pluginData.plugin.manifest.python_dependencies && pluginData.plugin.manifest.python_dependencies.length > 0" class="section">
          <h2>
            <Icon icon="lucide:package" />
            Python 依赖
          </h2>
          <ul class="dependencies-list">
            <li v-for="dep in pluginData.plugin.manifest.python_dependencies" :key="dep">
              <Icon icon="lucide:dot" />
              {{ dep }}
            </li>
          </ul>
        </div>

        <!-- 使用说明 -->
        <div v-if="pluginData.plugin.manifest.usage" class="section">
          <h2>
            <Icon icon="lucide:book-open" />
            使用说明
          </h2>
          <pre class="usage-text">{{ pluginData.plugin.manifest.usage }}</pre>
        </div>

        <!-- README -->
        <div v-if="pluginData.readme" class="section">
          <h2>
            <Icon icon="lucide:file-text" />
            README
          </h2>
          <div class="readme-content" v-html="renderedReadme"></div>
        </div>

        <!-- 仓库链接 -->
        <div class="section">
          <h2>
            <Icon icon="lucide:github" />
            仓库地址
          </h2>
          <a :href="pluginData.plugin.manifest.repository_url" target="_blank" class="repo-link">
            {{ pluginData.plugin.manifest.repository_url }}
            <Icon icon="lucide:external-link" />
          </a>
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
import { useRouter, useRoute } from 'vue-router'
import { Icon } from '@iconify/vue'
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
    return `<pre>${pluginData.value.readme}</pre>`
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
  if (!pluginData.value) return 'lucide:puzzle'
  
  const categories = pluginData.value.plugin.manifest.categories || []
  if (categories.includes('Entertainment') || categories.includes('Fun')) return 'lucide:smile'
  if (categories.includes('Games')) return 'lucide:gamepad-2'
  if (categories.includes('Tools')) return 'lucide:wrench'
  return 'lucide:puzzle'
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
        showToast(`插件 ${pluginData.value.plugin.manifest.name} 安装成功！`, 'success')
        
        // 重新加载插件详情以更新状态
        await loadPluginDetail()
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
  animation: fadeIn 0.3s ease;
}

.page-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 24px;
  background: var(--bg-primary);
  border-bottom: 1px solid var(--border-color);
}

.back-btn {
  display: flex;
  align-items: center;
  gap: 8px;
}

.header-actions {
  display: flex;
  gap: 12px;
}

.detail-container {
  flex: 1;
  overflow: auto;
  padding: 24px;
  background: var(--bg-secondary);
}

.detail-content {
  max-width: 900px;
  margin: 0 auto;
}

.plugin-header-info {
  display: flex;
  align-items: start;
  gap: 20px;
  padding: 32px;
  background: var(--bg-primary);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-lg);
  margin-bottom: 24px;
}

.plugin-icon {
  width: 80px;
  height: 80px;
  min-width: 80px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #8b5cf6, #7c3aed);
  border-radius: var(--radius-lg);
  color: white;
  font-size: 40px;
}

.plugin-title-section h1 {
  margin: 0 0 12px 0;
  font-size: 28px;
  font-weight: 600;
  color: var(--text-primary);
}

.plugin-badges {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.badge {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 6px 12px;
  border-radius: var(--radius);
  font-size: 13px;
  font-weight: 500;
}

.badge-version {
  background: rgba(99, 102, 241, 0.1);
  color: #6366f1;
}

.badge-success {
  background: rgba(16, 185, 129, 0.1);
  color: #10b981;
}

.badge-author {
  background: rgba(245, 158, 11, 0.1);
  color: #f59e0b;
}

.badge-license {
  background: rgba(139, 92, 246, 0.1);
  color: #8b5cf6;
}

.section {
  background: var(--bg-primary);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-lg);
  padding: 24px;
  margin-bottom: 20px;
}

.section h2 {
  display: flex;
  align-items: center;
  gap: 8px;
  margin: 0 0 16px 0;
  font-size: 18px;
  font-weight: 600;
  color: var(--text-primary);
}

.description-text {
  margin: 0;
  font-size: 14px;
  line-height: 1.7;
  color: var(--text-secondary);
}

.keywords-list,
.categories-list {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.keyword-tag,
.category-tag {
  padding: 6px 14px;
  background: var(--bg-secondary);
  border: 1px solid var(--border-color);
  border-radius: var(--radius);
  font-size: 13px;
  color: var(--text-primary);
}

.dependencies-list {
  list-style: none;
  margin: 0;
  padding: 0;
}

.dependencies-list li {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 0;
  font-size: 14px;
  color: var(--text-secondary);
  font-family: 'Courier New', monospace;
}

.usage-text {
  margin: 0;
  padding: 16px;
  background: var(--bg-secondary);
  border: 1px solid var(--border-color);
  border-radius: var(--radius);
  font-size: 13px;
  line-height: 1.6;
  color: var(--text-primary);
  white-space: pre-wrap;
  overflow-x: auto;
}

.readme-content {
  padding: 16px;
  background: var(--bg-secondary);
  border: 1px solid var(--border-color);
  border-radius: var(--radius);
  font-size: 14px;
  line-height: 1.7;
  color: var(--text-secondary);
}

.readme-content :deep(h1),
.readme-content :deep(h2),
.readme-content :deep(h3) {
  margin-top: 20px;
  margin-bottom: 12px;
  color: var(--text-primary);
}

.readme-content :deep(code) {
  padding: 2px 6px;
  background: rgba(0, 0, 0, 0.1);
  border-radius: 4px;
  font-family: 'Courier New', monospace;
  font-size: 0.9em;
}

.readme-content :deep(pre) {
  padding: 12px;
  background: rgba(0, 0, 0, 0.05);
  border-radius: 6px;
  overflow-x: auto;
}

.readme-content :deep(a) {
  color: var(--primary);
  text-decoration: none;
}

.readme-content :deep(a:hover) {
  text-decoration: underline;
}

.repo-link {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 10px 16px;
  background: var(--bg-secondary);
  border: 1px solid var(--border-color);
  border-radius: var(--radius);
  color: var(--primary);
  text-decoration: none;
  font-size: 14px;
  transition: all var(--transition-fast);
}

.repo-link:hover {
  background: var(--primary);
  color: white;
  border-color: var(--primary);
}

.btn {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  padding: 10px 20px;
  border: none;
  border-radius: var(--radius);
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all var(--transition-fast);
}

.btn-primary {
  background: var(--primary);
  color: white;
}

.btn-primary:hover:not(:disabled) {
  background: var(--primary-dark);
}

.btn-secondary {
  background: transparent;
  border: 1px solid var(--border-color);
  color: var(--text-primary);
}

.btn-secondary:hover {
  background: var(--bg-secondary);
}

.btn-ghost {
  background: transparent;
  color: var(--text-secondary);
}

.btn-ghost:hover:not(:disabled) {
  background: var(--bg-secondary);
  color: var(--text-primary);
}

.btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.spinning {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
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

/* 状态提示 */
.loading-state,
.error-state {
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
.error-state svg {
  font-size: 64px;
  opacity: 0.5;
}

.error-state {
  color: #ef4444;
}
</style>
