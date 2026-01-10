<!--
  @file GitHubView.vue
  @description GitHub 仓库信息页面
  
  功能说明：
  1. 显示 MoFox 相关的 GitHub 仓库信息（Core、Docs、WebUI）
  2. 标签栏切换不同仓库
  3. 快速访问仓库、Issues、Pull Requests
  4. 显示仓库统计（Stars、Forks、Issues 数量）
  
  数据来源：
  - GitHub API: 获取仓库实时统计数据
  
  仓库列表：
  - MoFox-Core: 核心代码仓库
  - MoFox-Bot-Docs: 文档仓库
  - MoFox-Core-Webui: WebUI 仓库
-->
<template>
  <div class="github-view">
    <div class="github-container">
      <div class="github-header">
        <div class="header-content">
          <span class="material-symbols-rounded header-icon">code</span>
          <h1>MoFox 仓库</h1>
        </div>
        <p class="header-description">访问 MoFox 的 GitHub 仓库，查看源代码、提交问题或参与开发</p>
      </div>

      <!-- 标签栏 -->
      <div class="tabs-container">
        <div class="tabs">
          <button 
            v-for="repo in repos" 
            :key="repo.key"
            :class="['tab-btn', { active: activeTab === repo.key }]"
            @click="activeTab = repo.key"
          >
            <span class="material-symbols-rounded">{{ repo.icon }}</span>
            <span class="tab-label">{{ repo.label }}</span>
          </button>
        </div>
      </div>

      <!-- MoFox-Core 仓库 -->
      <div v-show="activeTab === 'core'" class="github-card">
        <div class="card-icon">
          <svg class="github-logo" viewBox="0 0 98 96" xmlns="http://www.w3.org/2000/svg">
            <path fill-rule="evenodd" clip-rule="evenodd" d="M48.854 0C21.839 0 0 22 0 49.217c0 21.756 13.993 40.172 33.405 46.69 2.427.49 3.316-1.059 3.316-2.362 0-1.141-.08-5.052-.08-9.127-13.59 2.934-16.42-5.867-16.42-5.867-2.184-5.704-5.42-7.17-5.42-7.17-4.448-3.015.324-3.015.324-3.015 4.934.326 7.523 5.052 7.523 5.052 4.367 7.496 11.404 5.378 14.235 4.074.404-3.178 1.699-5.378 3.074-6.6-10.839-1.141-22.243-5.378-22.243-24.283 0-5.378 1.94-9.778 5.014-13.2-.485-1.222-2.184-6.275.486-13.038 0 0 4.125-1.304 13.426 5.052a46.97 46.97 0 0 1 12.214-1.63c4.125 0 8.33.571 12.213 1.63 9.302-6.356 13.427-5.052 13.427-5.052 2.67 6.763.97 11.816.485 13.038 3.155 3.422 5.015 7.822 5.015 13.2 0 18.905-11.404 23.06-22.324 24.283 1.78 1.548 3.316 4.481 3.316 9.126 0 6.6-.08 11.897-.08 13.526 0 1.304.89 2.853 3.316 2.364 19.412-6.52 33.405-24.935 33.405-46.691C97.707 22 75.788 0 48.854 0z" fill="currentColor"/>
          </svg>
        </div>
        
        <div class="card-content">
          <h2 class="repo-name">MoFox-Studio/MoFox-Core</h2>
          <p class="repo-description">
            MoFox Bot 的核心代码仓库，包含机器人的主要功能实现和插件系统。
          </p>
          
          <div class="repo-stats">
            <div class="stat-item">
              <span class="material-symbols-rounded">star</span>
              <span>{{ repoInfo.core.stars }} Stars</span>
            </div>
            <div class="stat-item">
              <span class="material-symbols-rounded">fork_right</span>
              <span>{{ repoInfo.core.forks }} Forks</span>
            </div>
            <div class="stat-item">
              <span class="material-symbols-rounded">bug_report</span>
              <span>{{ repoInfo.core.issues }} Issues</span>
            </div>
          </div>

          <div class="action-buttons">
            <a 
              href="https://github.com/MoFox-Studio/MoFox-Core" 
              target="_blank"
              class="btn btn-primary"
            >
              <span class="material-symbols-rounded">open_in_new</span>
              访问仓库
            </a>
            <a 
              href="https://github.com/MoFox-Studio/MoFox-Core/issues" 
              target="_blank"
              class="btn btn-secondary"
            >
              <span class="material-symbols-rounded">bug_report</span>
              提交问题
            </a>
            <a 
              href="https://github.com/MoFox-Studio/MoFox-Core/pulls" 
              target="_blank"
              class="btn btn-secondary"
            >
              <span class="material-symbols-rounded">code_blocks</span>
              Pull Requests
            </a>
          </div>
        </div>
      </div>

      <!-- MoFox-Bot-Docs 仓库 -->
      <div v-show="activeTab === 'docs'" class="github-card">
        <div class="card-icon">
          <svg class="github-logo" viewBox="0 0 98 96" xmlns="http://www.w3.org/2000/svg">
            <path fill-rule="evenodd" clip-rule="evenodd" d="M48.854 0C21.839 0 0 22 0 49.217c0 21.756 13.993 40.172 33.405 46.69 2.427.49 3.316-1.059 3.316-2.362 0-1.141-.08-5.052-.08-9.127-13.59 2.934-16.42-5.867-16.42-5.867-2.184-5.704-5.42-7.17-5.42-7.17-4.448-3.015.324-3.015.324-3.015 4.934.326 7.523 5.052 7.523 5.052 4.367 7.496 11.404 5.378 14.235 4.074.404-3.178 1.699-5.378 3.074-6.6-10.839-1.141-22.243-5.378-22.243-24.283 0-5.378 1.94-9.778 5.014-13.2-.485-1.222-2.184-6.275.486-13.038 0 0 4.125-1.304 13.426 5.052a46.97 46.97 0 0 1 12.214-1.63c4.125 0 8.33.571 12.213 1.63 9.302-6.356 13.427-5.052 13.427-5.052 2.67 6.763.97 11.816.485 13.038 3.155 3.422 5.015 7.822 5.015 13.2 0 18.905-11.404 23.06-22.324 24.283 1.78 1.548 3.316 4.481 3.316 9.126 0 6.6-.08 11.897-.08 13.526 0 1.304.89 2.853 3.316 2.364 19.412-6.52 33.405-24.935 33.405-46.691C97.707 22 75.788 0 48.854 0z" fill="currentColor"/>
          </svg>
        </div>
        
        <div class="card-content">
          <h2 class="repo-name">MoFox-Studio/MoFox-Bot-Docs</h2>
          <p class="repo-description">
            MoFox Bot 的官方文档仓库，包含使用指南、API 文档和开发教程。
          </p>
          
          <div class="repo-stats">
            <div class="stat-item">
              <span class="material-symbols-rounded">star</span>
              <span>{{ repoInfo.docs.stars }} Stars</span>
            </div>
            <div class="stat-item">
              <span class="material-symbols-rounded">fork_right</span>
              <span>{{ repoInfo.docs.forks }} Forks</span>
            </div>
            <div class="stat-item">
              <span class="material-symbols-rounded">bug_report</span>
              <span>{{ repoInfo.docs.issues }} Issues</span>
            </div>
          </div>

          <div class="action-buttons">
            <a 
              href="https://github.com/MoFox-Studio/MoFox-Bot-Docs" 
              target="_blank"
              class="btn btn-primary"
            >
              <span class="material-symbols-rounded">open_in_new</span>
              访问仓库
            </a>
            <a 
              href="https://github.com/MoFox-Studio/MoFox-Bot-Docs/issues" 
              target="_blank"
              class="btn btn-secondary"
            >
              <span class="material-symbols-rounded">bug_report</span>
              提交问题
            </a>
            <a 
              href="https://github.com/MoFox-Studio/MoFox-Bot-Docs/pulls" 
              target="_blank"
              class="btn btn-secondary"
            >
              <span class="material-symbols-rounded">code_blocks</span>
              Pull Requests
            </a>
          </div>
        </div>
      </div>

      <!-- MoFox-Core-Webui 仓库 -->
      <div v-show="activeTab === 'webui'" class="github-card">
        <div class="card-icon">
          <svg class="github-logo" viewBox="0 0 98 96" xmlns="http://www.w3.org/2000/svg">
            <path fill-rule="evenodd" clip-rule="evenodd" d="M48.854 0C21.839 0 0 22 0 49.217c0 21.756 13.993 40.172 33.405 46.69 2.427.49 3.316-1.059 3.316-2.362 0-1.141-.08-5.052-.08-9.127-13.59 2.934-16.42-5.867-16.42-5.867-2.184-5.704-5.42-7.17-5.42-7.17-4.448-3.015.324-3.015.324-3.015 4.934.326 7.523 5.052 7.523 5.052 4.367 7.496 11.404 5.378 14.235 4.074.404-3.178 1.699-5.378 3.074-6.6-10.839-1.141-22.243-5.378-22.243-24.283 0-5.378 1.94-9.778 5.014-13.2-.485-1.222-2.184-6.275.486-13.038 0 0 4.125-1.304 13.426 5.052a46.97 46.97 0 0 1 12.214-1.63c4.125 0 8.33.571 12.213 1.63 9.302-6.356 13.427-5.052 13.427-5.052 2.67 6.763.97 11.816.485 13.038 3.155 3.422 5.015 7.822 5.015 13.2 0 18.905-11.404 23.06-22.324 24.283 1.78 1.548 3.316 4.481 3.316 9.126 0 6.6-.08 11.897-.08 13.526 0 1.304.89 2.853 3.316 2.364 19.412-6.52 33.405-24.935 33.405-46.691C97.707 22 75.788 0 48.854 0z" fill="currentColor"/>
          </svg>
        </div>
        
        <div class="card-content">
          <h2 class="repo-name">MoFox-Studio/MoFox-Core-Webui</h2>
          <p class="repo-description">
            MoFox Bot 的 Web 管理界面仓库，提供现代化的可视化配置和管理功能。
          </p>
          
          <div class="repo-stats">
            <div class="stat-item">
              <span class="material-symbols-rounded">star</span>
              <span>{{ repoInfo.webui.stars }} Stars</span>
            </div>
            <div class="stat-item">
              <span class="material-symbols-rounded">fork_right</span>
              <span>{{ repoInfo.webui.forks }} Forks</span>
            </div>
            <div class="stat-item">
              <span class="material-symbols-rounded">bug_report</span>
              <span>{{ repoInfo.webui.issues }} Issues</span>
            </div>
          </div>

          <div class="action-buttons">
            <a 
              href="https://github.com/MoFox-Studio/MoFox-Core-Webui" 
              target="_blank"
              class="btn btn-primary"
            >
              <span class="material-symbols-rounded">open_in_new</span>
              访问仓库
            </a>
            <a 
              href="https://github.com/MoFox-Studio/MoFox-Core-Webui/issues" 
              target="_blank"
              class="btn btn-secondary"
            >
              <span class="material-symbols-rounded">bug_report</span>
              提交问题
            </a>
            <a 
              href="https://github.com/MoFox-Studio/MoFox-Core-Webui/pulls" 
              target="_blank"
              class="btn btn-secondary"
            >
              <span class="material-symbols-rounded">code_blocks</span>
              Pull Requests
            </a>
          </div>
        </div>
      </div>

      <!-- Core 仓库的信息卡片 -->
      <div v-show="activeTab === 'core'" class="info-grid">
        <div class="info-card">
          <span class="material-symbols-rounded card-icon">memory</span>
          <h3>核心引擎</h3>
          <p>MoFox 的核心功能和消息处理引擎</p>
        </div>
        
        <div class="info-card">
          <span class="material-symbols-rounded card-icon">extension</span>
          <h3>插件系统</h3>
          <p>灵活的插件架构，支持热加载</p>
        </div>
        
        <div class="info-card">
          <span class="material-symbols-rounded card-icon">psychology</span>
          <h3>AI 集成</h3>
          <p>多模型支持，智能对话能力</p>
        </div>
        
        <div class="info-card">
          <span class="material-symbols-rounded card-icon">groups</span>
          <h3>参与贡献</h3>
          <p>欢迎提交 PR，一起完善项目</p>
        </div>
      </div>

      <!-- Docs 仓库的信息卡片 -->
      <div v-show="activeTab === 'docs'" class="info-grid">
        <div class="info-card">
          <span class="material-symbols-rounded card-icon">menu_book</span>
          <h3>使用指南</h3>
          <p>快速入门和详细使用教程</p>
        </div>
        
        <div class="info-card">
          <span class="material-symbols-rounded card-icon">api</span>
          <h3>API 文档</h3>
          <p>完整的 API 参考和示例</p>
        </div>
        
        <div class="info-card">
          <span class="material-symbols-rounded card-icon">school</span>
          <h3>开发教程</h3>
          <p>插件开发和自定义功能指南</p>
        </div>
        
        <div class="info-card">
          <span class="material-symbols-rounded card-icon">edit_note</span>
          <h3>完善文档</h3>
          <p>帮助改进文档，让更多人受益</p>
        </div>
      </div>

      <!-- WebUI 仓库的信息卡片 -->
      <div v-show="activeTab === 'webui'" class="info-grid">
        <div class="info-card">
          <span class="material-symbols-rounded card-icon">dashboard</span>
          <h3>管理面板</h3>
          <p>现代化的 Web 管理界面</p>
        </div>
        
        <div class="info-card">
          <span class="material-symbols-rounded card-icon">tune</span>
          <h3>可视化配置</h3>
          <p>直观的配置编辑和管理</p>
        </div>
        
        <div class="info-card">
          <span class="material-symbols-rounded card-icon">monitoring</span>
          <h3>实时监控</h3>
          <p>Bot 状态和日志实时查看</p>
        </div>
        
        <div class="info-card">
          <span class="material-symbols-rounded card-icon">palette</span>
          <h3>主题定制</h3>
          <p>Material Design 3 风格界面</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'

// 当前激活的标签
const activeTab = ref('core')

// 仓库配置
const repos = [
  { key: 'core', label: 'MoFox Core', icon: 'memory', url: 'MoFox-Studio/MoFox-Core' },
  { key: 'docs', label: 'Bot Docs', icon: 'menu_book', url: 'MoFox-Studio/MoFox-Bot-Docs' },
  { key: 'webui', label: 'Core WebUI', icon: 'dashboard', url: 'MoFox-Studio/MoFox-Core-Webui' }
]

// 各仓库的信息
const repoInfo = ref({
  core: { stars: 0, forks: 0, issues: 0 },
  docs: { stars: 0, forks: 0, issues: 0 },
  webui: { stars: 0, forks: 0, issues: 0 }
})

const fetchRepoInfo = async (key: string, repoPath: string) => {
  try {
    const response = await fetch(`https://api.github.com/repos/${repoPath}`)
    if (response.ok) {
      const data = await response.json()
      repoInfo.value[key as keyof typeof repoInfo.value] = {
        stars: data.stargazers_count,
        forks: data.forks_count,
        issues: data.open_issues_count
      }
    }
  } catch (error) {
    console.error(`Failed to fetch ${key} repo info:`, error)
  }
}

const fetchAllRepoInfo = () => {
  repos.forEach(repo => {
    fetchRepoInfo(repo.key, repo.url)
  })
}

onMounted(() => {
  fetchAllRepoInfo()
})
</script>

<style scoped>
.github-view {
  width: 100%;
  height: 100%;
  padding: 16px;
  overflow-y: auto;
  background: var(--md-sys-color-surface);
}

.github-container {
  display: flex;
  flex-direction: column;
  gap: 2rem;
  max-width: 1200px;
  margin: 0 auto;
}

.github-header {
  text-align: center;
  margin-bottom: 1rem;
}

.header-content {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 1rem;
  margin-bottom: 0.5rem;
}

.header-icon {
  font-size: 3rem;
  color: var(--md-sys-color-primary);
}

.github-header h1 {
  font-size: 2.5rem;
  font-weight: 600;
  color: var(--md-sys-color-on-surface);
  margin: 0;
}

.header-description {
  font-size: 1.1rem;
  color: var(--md-sys-color-on-surface-variant);
  margin: 0;
}

/* 标签栏样式 */
.tabs-container {
  display: flex;
  justify-content: center;
}

.tabs {
  display: flex;
  gap: 0.5rem;
  background: var(--md-sys-color-surface-container);
  padding: 0.5rem;
  border-radius: 2rem;
}

.tab-btn {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.75rem 1.5rem;
  border: none;
  border-radius: 1.5rem;
  background: transparent;
  color: var(--md-sys-color-on-surface-variant);
  font-size: 0.95rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s ease;
}

.tab-btn:hover {
  background: var(--md-sys-color-surface-container-high);
  color: var(--md-sys-color-on-surface);
}

.tab-btn.active {
  background: var(--md-sys-color-primary);
  color: var(--md-sys-color-on-primary);
}

.tab-btn .material-symbols-rounded {
  font-size: 1.25rem;
}

.github-card {
  background: var(--md-sys-color-surface-container);
  border-radius: 2rem;
  padding: 3rem;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 2rem;
  box-shadow: none;
  position: relative;
  overflow: hidden;
}

.github-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 4px;
  background: var(--md-sys-color-primary);
}

.card-icon {
  display: flex;
  align-items: center;
  justify-content: center;
}

.github-logo {
  width: 80px;
  height: 80px;
  color: var(--md-sys-color-on-surface);
}

.card-content {
  text-align: center;
  width: 100%;
}

.repo-name {
  font-size: 2rem;
  font-weight: 600;
  color: var(--md-sys-color-primary);
  margin: 0 0 1rem 0;
}

.repo-description {
  font-size: 1.1rem;
  color: var(--md-sys-color-on-surface-variant);
  margin: 0 0 2rem 0;
  line-height: 1.6;
}

.repo-stats {
  display: flex;
  gap: 2rem;
  justify-content: center;
  margin-bottom: 2rem;
  padding: 1.5rem;
  background: var(--md-sys-color-surface);
  border-radius: 1rem;
}

.stat-item {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  color: var(--md-sys-color-on-surface-variant);
  font-weight: 500;
}

.stat-item .material-symbols-rounded {
  font-size: 1.5rem;
}

.action-buttons {
  display: flex;
  gap: 1rem;
  justify-content: center;
  flex-wrap: wrap;
}

.btn {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.875rem 1.5rem;
  border-radius: 2rem;
  font-size: 1rem;
  font-weight: 500;
  text-decoration: none;
  transition: all 0.2s;
  cursor: pointer;
}

.btn-primary {
  background: var(--md-sys-color-primary);
  color: var(--md-sys-color-on-primary);
}

.btn-primary:hover {
  background: var(--md-sys-color-primary-container);
  color: var(--md-sys-color-on-primary-container);
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.btn-secondary {
  background: var(--md-sys-color-secondary-container);
  color: var(--md-sys-color-on-secondary-container);
}

.btn-secondary:hover {
  background: var(--md-sys-color-secondary);
  color: var(--md-sys-color-on-secondary);
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.btn .material-symbols-rounded {
  font-size: 1.25rem;
}

.info-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 1.5rem;
}

.info-card {
  background: var(--md-sys-color-surface-container);
  border-radius: 1rem;
  padding: 2rem;
  text-align: center;
  transition: all 0.3s;
}

.info-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.1);
}

.info-card .card-icon {
  font-size: 3rem;
  color: var(--md-sys-color-primary);
  margin-bottom: 1rem;
}

.info-card h3 {
  font-size: 1.25rem;
  font-weight: 600;
  color: var(--md-sys-color-on-surface);
  margin: 0 0 0.5rem 0;
}

.info-card p {
  font-size: 0.95rem;
  color: var(--md-sys-color-on-surface-variant);
  margin: 0;
  line-height: 1.5;
}

@media (max-width: 768px) {
  .github-view {
    padding: 1rem;
  }

  .github-card {
    padding: 2rem 1.5rem;
  }

  .github-header h1 {
    font-size: 2rem;
  }

  .repo-name {
    font-size: 1.5rem;
  }

  .action-buttons {
    flex-direction: column;
  }

  .btn {
    width: 100%;
    justify-content: center;
  }

  .repo-stats {
    flex-direction: column;
    gap: 1rem;
  }

  .info-grid {
    grid-template-columns: 1fr;
  }

  .tabs {
    flex-direction: column;
    width: 100%;
  }

  .tab-btn {
    justify-content: center;
  }

  .tab-label {
    display: inline;
  }
}
</style>
