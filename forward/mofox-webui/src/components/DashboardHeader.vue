<template>
  <header class="dashboard-header">
    <div class="header-container">
      <!-- 左侧：页面标题 -->
      <div class="header-left">
        <h1 class="page-title">{{ pageTitle }}</h1>
        <p class="page-subtitle">{{ currentSubtitle }}</p>
      </div>
      
      <!-- 右侧:项目名称、状态、操作 -->
      <div class="header-right">
        <!-- 系统状态 -->
        <div class="status-indicator">
          <span class="status-dot"></span>
          <span class="status-text">运行中</span>
        </div>
        
        <!-- Bot 控制菜单 -->
        <div class="bot-control-menu" @click="toggleBotMenu" v-click-outside="closeBotMenu">
          <div class="project-badge">
            <Icon icon="lucide:bot" class="project-icon" />
            <span class="project-name">MoFox Bot</span>
            <Icon icon="lucide:chevron-down" class="dropdown-icon" :class="{ 'rotate': showBotMenu }" />
          </div>
          
          <!-- 下拉菜单 -->
          <transition name="dropdown">
            <div v-if="showBotMenu" class="dropdown-menu">
              <button class="menu-item restart-item" @click.stop="handleRestart">
                <Icon icon="lucide:refresh-cw" />
                <span>重启 Bot</span>
              </button>
              <button class="menu-item shutdown-item" @click.stop="handleShutdown">
                <Icon icon="lucide:power" />
                <span>关闭 Bot</span>
              </button>
            </div>
          </transition>
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
import { computed, ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '@/stores/user'
import { Icon } from '@iconify/vue'
import { restartBot, shutdownBot } from '@/api'
import { showConfirm, showSuccess, showError } from '@/utils/dialog'

const router = useRouter()
const userStore = useUserStore()

// 主标题改为通用名称
const pageTitle = computed(() => {
  return 'MoFox Bot WebUI'
})

// 随机副标题
const subtitles = [
  '欢迎回来，一切运行正常',
  '今天也要元气满满哦',
  '系统运行稳定，请放心使用',
  '新的一天，新的开始',
  '愿你有美好的一天',
  '继续保持，做得很好',
  '万事顺意，心想事成',
  '让我们一起创造美好',
]

const currentSubtitle = ref<string>('')
const showBotMenu = ref(false)

onMounted(() => {
  // 随机选择一个副标题
  currentSubtitle.value = subtitles[Math.floor(Math.random() * subtitles.length)] ?? ''
})

const toggleBotMenu = () => {
  showBotMenu.value = !showBotMenu.value
}

const closeBotMenu = () => {
  showBotMenu.value = false
}

const handleLogout = () => {
  userStore.logout()
  router.push('/login')
}

const handleRestart = async () => {
  closeBotMenu() // 关闭菜单
  
  const confirmed = await showConfirm({
    title: '重启 Bot',
    message: '确定要重启 Bot 吗？\n\n重启期间所有服务将暂时不可用，大约需要 10-30 秒。',
    type: 'warning',
    confirmText: '确定重启',
    cancelText: '取消'
  })
  
  if (!confirmed) {
    return
  }

  try {
    const result = await restartBot()
    if (result.success && result.data) {
      await showSuccess(
        result.data.message || '重启请求已发送\n\n页面将在 3 秒后自动刷新',
        '重启成功'
      )
      // 3秒后刷新页面，等待Bot重启完成
      setTimeout(() => {
        window.location.reload()
      }, 3000)
    } else {
      await showError(
        result.error || '未知错误',
        '重启失败'
      )
    }
  } catch (error) {
    await showError(
      error instanceof Error ? error.message : '网络错误',
      '重启失败'
    )
  }
}

const handleShutdown = async () => {
  closeBotMenu() // 关闭菜单
  
  // 第一次确认
  const firstConfirm = await showConfirm({
    title: '⚠️ 关闭 Bot',
    message: '确定要关闭 Bot 吗？\n\n关闭后需要手动重新启动 Bot 程序。\n此操作不可撤销！',
    type: 'danger',
    confirmText: '继续',
    cancelText: '取消'
  })
  
  if (!firstConfirm) {
    return
  }

  // 二次确认
  const secondConfirm = await showConfirm({
    title: '🚨 最后确认',
    message: '真的要关闭 Bot 吗？\n\n关闭后所有服务将停止，需要手动重启！',
    type: 'danger',
    confirmText: '确定关闭',
    cancelText: '我再想想'
  })
  
  if (!secondConfirm) {
    return
  }

  try {
    const result = await shutdownBot()
    if (result.success && result.data) {
      await showSuccess(
        result.data.message || '关闭请求已发送\n\nBot 将在 1 秒后关闭，请手动重启。',
        '关闭成功'
      )
      // 登出并跳转到登录页
      setTimeout(() => {
        userStore.logout()
        router.push('/login')
      }, 1000)
    } else {
      await showError(
        result.error || '未知错误',
        '关闭失败'
      )
    }
  } catch (error) {
    await showError(
      error instanceof Error ? error.message : '网络错误',
      '关闭失败'
    )
  }
}

// v-click-outside 指令
const vClickOutside = {
  mounted(el: HTMLElement & { clickOutsideEvent?: (event: Event) => void }, binding: { value: () => void }) {
    el.clickOutsideEvent = (event: Event) => {
      if (!(el === event.target || el.contains(event.target as Node))) {
        binding.value()
      }
    }
    document.addEventListener('click', el.clickOutsideEvent)
  },
  unmounted(el: HTMLElement & { clickOutsideEvent?: (event: Event) => void }) {
    if (el.clickOutsideEvent) {
      document.removeEventListener('click', el.clickOutsideEvent)
    }
  }
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

/* Bot 控制菜单 */
.bot-control-menu {
  position: relative;
  cursor: pointer;
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
  transition: all var(--transition);
}

.bot-control-menu:hover .project-badge {
  box-shadow: 0 4px 12px rgba(59, 130, 246, 0.4);
  transform: translateY(-1px);
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

.dropdown-icon {
  font-size: 16px;
  color: white;
  transition: transform var(--transition);
}

.dropdown-icon.rotate {
  transform: rotate(180deg);
}

/* 下拉菜单 */
.dropdown-menu {
  position: absolute;
  top: calc(100% + 8px);
  right: 0;
  min-width: 160px;
  background: var(--bg-primary);
  border: 1px solid var(--border-color);
  border-radius: var(--radius);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  overflow: hidden;
  z-index: 1000;
}

.menu-item {
  display: flex;
  align-items: center;
  gap: 10px;
  width: 100%;
  padding: 12px 16px;
  background: transparent;
  border: none;
  color: var(--text-primary);
  font-size: 14px;
  font-weight: 500;
  text-align: left;
  cursor: pointer;
  transition: all var(--transition);
}

.menu-item svg {
  font-size: 18px;
  flex-shrink: 0;
}

.restart-item:hover {
  background: rgba(59, 130, 246, 0.1);
  color: var(--primary);
}

.restart-item:hover svg {
  color: var(--primary);
}

.shutdown-item:hover {
  background: rgba(239, 68, 68, 0.1);
  color: var(--danger);
}

.shutdown-item:hover svg {
  color: var(--danger);
}

/* 下拉动画 */
.dropdown-enter-active,
.dropdown-leave-active {
  transition: all 0.2s ease;
}

.dropdown-enter-from {
  opacity: 0;
  transform: translateY(-10px);
}

.dropdown-leave-to {
  opacity: 0;
  transform: translateY(-10px);
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
  
  .project-name,
  .dropdown-icon,
  .logout-button span {
    display: none;
  }
  
  .project-badge,
  .logout-button {
    padding: 10px;
  }
  
  .dropdown-menu {
    right: auto;
    left: 0;
  }
}
</style>
