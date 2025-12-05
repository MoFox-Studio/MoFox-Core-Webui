<template>
  <header class="dashboard-header">
    <div class="header-container">
      <!-- 左侧：页面标题 -->
      <div class="header-left">
        <h1 class="page-title">{{ pageTitle }}</h1>
        <p class="page-subtitle">欢迎回来，一切运行正常</p>
      </div>
      
      <!-- 右侧：项目名称、状态、操作 -->
      <div class="header-right">
        <!-- 系统状态 -->
        <div class="status-indicator">
          <span class="status-dot"></span>
          <span class="status-text">运行中</span>
        </div>
        
        <!-- 项目名称 -->
        <div class="project-badge">
          <Icon icon="lucide:bot" class="project-icon" />
          <span class="project-name">MoFox Bot</span>
        </div>
        
        <!-- 登出按钮 -->
        <button class="logout-button" @click="handleLogout" title="退出登录">
          <Icon icon="lucide:log-out" />
          <span>退出</span>
        </button>
      </div>
    </div>
  </header>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useUserStore } from '@/stores/user'
import { Icon } from '@iconify/vue'

const router = useRouter()
const route = useRoute()
const userStore = useUserStore()

const pageTitle = computed(() => {
  const titles: Record<string, string> = {
    '/dashboard': '仪表盘',
    '/dashboard/': '仪表盘',
  }
  return titles[route.path] || '仪表盘'
})

const handleLogout = () => {
  userStore.logout()
  router.push('/login')
}
</script>

<style scoped>
.dashboard-header {
  background: var(--bg-primary);
  border-bottom: 1px solid var(--border-color);
  position: sticky;
  top: 0;
  z-index: 50;
}

.header-container {
  max-width: 1400px;
  margin: 0 auto;
  padding: 20px 32px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 24px;
}

/* 左侧标题区 */
.header-left {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.page-title {
  font-size: 24px;
  font-weight: 700;
  color: var(--text-primary);
  letter-spacing: -0.5px;
  margin: 0;
}

.page-subtitle {
  font-size: 14px;
  color: var(--text-tertiary);
  margin: 0;
}

/* 右侧操作区 */
.header-right {
  display: flex;
  align-items: center;
  gap: 16px;
}

/* 状态指示器 */
.status-indicator {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 14px;
  background: var(--success-bg);
  border-radius: var(--radius-full);
}

.status-dot {
  width: 8px;
  height: 8px;
  background: var(--success);
  border-radius: 50%;
  animation: pulse-dot 2s ease-in-out infinite;
}

@keyframes pulse-dot {
  0%, 100% {
    opacity: 1;
    transform: scale(1);
  }
  50% {
    opacity: 0.6;
    transform: scale(1.1);
  }
}

.status-text {
  font-size: 13px;
  font-weight: 500;
  color: var(--success);
}

/* 项目徽章 */
.project-badge {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 16px;
  background: linear-gradient(135deg, var(--primary) 0%, var(--primary-dark) 100%);
  border-radius: var(--radius);
  box-shadow: 0 2px 8px rgba(59, 130, 246, 0.3);
}

.project-icon {
  font-size: 18px;
  color: white;
}

.project-name {
  font-size: 14px;
  font-weight: 600;
  color: white;
  letter-spacing: -0.3px;
}

/* 登出按钮 */
.logout-button {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 16px;
  background: var(--bg-tertiary);
  border: 1px solid var(--border-color);
  border-radius: var(--radius);
  color: var(--text-secondary);
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all var(--transition);
}

.logout-button:hover {
  background: var(--danger-bg);
  border-color: var(--danger);
  color: var(--danger);
}

.logout-button svg {
  font-size: 18px;
}

/* 响应式 */
@media (max-width: 768px) {
  .header-container {
    padding: 16px 20px;
    flex-direction: column;
    align-items: flex-start;
  }
  
  .header-right {
    width: 100%;
    justify-content: flex-start;
    flex-wrap: wrap;
  }
  
  .page-title {
    font-size: 20px;
  }
  
  .project-badge span,
  .logout-button span {
    display: none;
  }
  
  .project-badge,
  .logout-button {
    padding: 10px;
  }
}
</style>
