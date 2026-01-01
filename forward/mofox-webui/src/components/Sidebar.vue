<template>
  <aside class="sidebar" :class="{ collapsed: isCollapsed }">
    <!-- 侧边栏头部 -->
    <div class="sidebar-header">
      <div class="logo-wrapper">
        <div class="logo-icon">
          <span class="material-symbols-rounded">smart_toy</span>
        </div>
        <Transition name="fade">
          <span v-if="!isCollapsed" class="logo-text">MoFox</span>
        </Transition>
      </div>
    </div>
    
    <!-- 导航菜单 -->
    <nav class="sidebar-nav">
      <div class="nav-section">
        <Transition name="fade">
          <span v-if="!isCollapsed" class="nav-section-title">菜单</span>
        </Transition>
        
        <!-- 菜单项 -->
        <template v-for="item in menuItems" :key="item.name">
          <!-- 有子菜单的项目 -->
          <div v-if="item.children && item.key" class="nav-group">
            <div 
              class="nav-item-content nav-group-header"
              :class="{ active: isGroupActive(item), expanded: expandedGroups[item.key] }"
              @click="toggleGroup(item.key)"
              :title="item.name"
            >
              <div class="nav-icon-wrapper">
                <span class="material-symbols-rounded nav-icon">{{ item.icon }}</span>
              </div>
              <Transition name="slide-fade">
                <span v-if="!isCollapsed" class="nav-text">{{ item.name }}</span>
              </Transition>
              <Transition name="fade">
                <span 
                  v-if="!isCollapsed" 
                  class="material-symbols-rounded nav-arrow"
                >
                  {{ expandedGroups[item.key] ? 'expand_less' : 'expand_more' }}
                </span>
              </Transition>
            </div>
            
            <!-- 子菜单列表 -->
            <Transition name="expand">
              <div v-if="expandedGroups[item.key] && !isCollapsed" class="nav-children">
                <router-link 
                  v-for="child in item.children" 
                  :key="child.path"
                  :to="child.path" 
                  custom
                  v-slot="{ navigate }"
                >
                  <div 
                    class="nav-item nav-child-item"
                    @click="navigate"
                    :title="child.name"
                  >
                    <div 
                      class="nav-item-content"
                      :class="{ active: isActive(child.path) }"
                    >
                      <div class="nav-icon-wrapper">
                        <span class="material-symbols-rounded nav-icon">{{ child.icon }}</span>
                      </div>
                      <span class="nav-text">{{ child.name }}</span>
                    </div>
                  </div>
                </router-link>
              </div>
            </Transition>
          </div>
          
          <!-- 自定义动作菜单项 -->
          <div 
            v-else-if="item.action"
            class="nav-item"
            @click="item.action"
            :title="item.name"
          >
            <div 
              class="nav-item-content"
              :class="{ active: item.isActive ? item.isActive() : false }"
            >
              <div class="nav-icon-wrapper">
                <span class="material-symbols-rounded nav-icon">{{ item.icon }}</span>
              </div>
              <Transition name="slide-fade">
                <span v-if="!isCollapsed" class="nav-text">{{ item.name }}</span>
              </Transition>
            </div>
          </div>

          <!-- 普通菜单项 -->
          <router-link 
            v-else
            :to="item.path" 
            custom
            v-slot="{ navigate }"
          >
            <div 
              class="nav-item"
              @click="navigate"
              :title="item.name"
            >
              <div 
                class="nav-item-content"
                :class="{ active: isActive(item.path) }"
              >
                <div class="nav-icon-wrapper">
                  <span class="material-symbols-rounded nav-icon">{{ item.icon }}</span>
                </div>
                <Transition name="slide-fade">
                  <span v-if="!isCollapsed" class="nav-text">{{ item.name }}</span>
                </Transition>
              </div>
            </div>
          </router-link>
        </template>
      </div>
    </nav>
    
    <!-- 侧边栏底部 -->
    <div class="sidebar-footer">
      <!-- Bot 控制 -->
      <button 
        class="footer-button" 
        @click="handleRestart"
        title="重启 Bot"
      >
        <span class="material-symbols-rounded footer-icon">refresh</span>
        <Transition name="slide-fade">
          <span v-if="!isCollapsed">重启 Bot</span>
        </Transition>
      </button>

      <button 
        class="footer-button" 
        @click="handleShutdown"
        title="关闭 Bot"
      >
        <span class="material-symbols-rounded footer-icon">power_settings_new</span>
        <Transition name="slide-fade">
          <span v-if="!isCollapsed">关闭 Bot</span>
        </Transition>
      </button>

      <!-- 退出登录 -->
      <button 
        class="footer-button" 
        @click="handleLogout"
        title="退出登录"
      >
        <span class="material-symbols-rounded footer-icon">logout</span>
        <Transition name="slide-fade">
          <span v-if="!isCollapsed">退出登录</span>
        </Transition>
      </button>

      <!-- 折叠按钮 -->
      <button 
        class="footer-button collapse-button" 
        @click="toggleSidebar"
        :title="isCollapsed ? '展开侧边栏' : '收起侧边栏'"
      >
        <span class="material-symbols-rounded footer-icon collapse-icon">
          {{ isCollapsed ? 'last_page' : 'first_page' }}
        </span>
        <Transition name="slide-fade">
          <span v-if="!isCollapsed">收起菜单</span>
        </Transition>
      </button>
    </div>
  </aside>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useUserStore } from '@/stores/user'
import { useUIStore } from '@/stores/ui'
import { restartBot, shutdownBot } from '@/api'
import { showConfirm, showSuccess, showError } from '@/utils/dialog'

interface MenuItem {
  name: string
  path: string
  icon: string
  key?: string
  children?: MenuItem[]
  action?: () => void
  isActive?: () => boolean
}

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()
const uiStore = useUIStore()

const isCollapsed = ref(true)

// 可折叠组的展开状态
const expandedGroups = reactive<Record<string, boolean>>({
  config: true,
  'ai-management': true,
  'ui-settings': true,
  'log-management': true
})

const handleRestart = async () => {
  const confirmed = await showConfirm({
    title: '重启 Bot',
    message: '确定要重启 MoFox Bot 吗？这将中断当前的所有连接。',
    confirmText: '重启'
  })
  
  if (confirmed) {
    try {
      await restartBot()
      showSuccess('Bot 重启指令已发送')
    } catch (error) {
      showError('重启失败: ' + error)
    }
  }
}

const handleShutdown = async () => {
  const confirmed = await showConfirm({
    title: '关闭 Bot',
    message: '确定要关闭 MoFox Bot 吗？WebUI 也将失去连接。',
    confirmText: '关闭'
  })
  
  if (confirmed) {
    try {
      await shutdownBot()
      showSuccess('Bot 关闭指令已发送')
    } catch (error) {
      showError('关闭失败: ' + error)
    }
  }
}

const handleLogout = () => {
  userStore.logout()
  router.push('/login')
}

const menuItems: MenuItem[] = [
  { name: '仪表盘', path: '/dashboard', icon: 'dashboard' },
  { name: 'UI 聊天室', path: '/dashboard/chatroom', icon: 'forum' },
  { name: '实时消息', path: '/dashboard/live-chat', icon: 'chat' },
  { 
    name: '配置管理', 
    path: '/dashboard/config', 
    icon: 'settings',
    key: 'config',
    children: [
      { name: '机器人配置', path: '/dashboard/bot-config', icon: 'smart_toy' },
      { name: '模型配置', path: '/dashboard/model-config', icon: 'psychology' },
      { name: '模型统计', path: '/dashboard/model-stats', icon: 'bar_chart' },
      { name: '插件配置', path: '/dashboard/plugin-config', icon: 'extension' },
    ]
  },
  { 
    name: '智能管理', 
    path: '/dashboard/ai-management', 
    icon: 'psychology_alt',
    key: 'ai-management',
    children: [
      { name: '关系管理', path: '/dashboard/relationship', icon: 'group' },
      { name: '表达方式', path: '/dashboard/expression', icon: 'record_voice_over' },
      { name: '插件管理', path: '/dashboard/plugin-manage', icon: 'deployed_code' },
      { name: '插件市场', path: '/dashboard/marketplace', icon: 'storefront' },
      { name: '表情管理', path: '/dashboard/emoji-manager', icon: 'insert_emoticon' },
    ]
  },
  { 
    name: 'UI 设置', 
    path: '/dashboard/ui-settings', 
    icon: 'tune',
    key: 'ui-settings',
    children: [
      { name: '风格与壁纸', path: '/dashboard/theme', icon: 'palette' },
    ]
  },
  { 
    name: '日志管理', 
    path: '/dashboard/log-management', 
    icon: 'description',
    key: 'log-management',
    children: [
      { name: '日志查看器', path: '/dashboard/log-viewer', icon: 'article' },
      { name: '实时日志', path: '/dashboard/live-log', icon: 'sensors' },
    ]
  },
  { name: '系统更新', path: '/dashboard/git-update', icon: 'system_update' },
  { name: 'GitHub 仓库', path: '/dashboard/github', icon: 'code' },
  { 
    name: '官方文档', 
    path: '', 
    icon: 'menu_book',
    action: () => uiStore.toggleDoc(),
    isActive: () => uiStore.isDocOpen
  },
]

const toggleSidebar = () => {
  isCollapsed.value = !isCollapsed.value
}

const toggleGroup = (key: string) => {
  if (isCollapsed.value) {
    // 如果侧边栏已折叠，先展开侧边栏
    isCollapsed.value = false
    expandedGroups[key] = true
  } else {
    expandedGroups[key] = !expandedGroups[key]
  }
}

const isActive = (path: string) => {
  if (path === '/dashboard') {
    return route.path === '/dashboard' || route.path === '/dashboard/'
  }
  return route.path === path || route.path.startsWith(path + '/')
}

const isGroupActive = (item: MenuItem) => {
  if (item.children) {
    return item.children.some(child => isActive(child.path))
  }
  return isActive(item.path)
}
</script>

<style scoped>
.sidebar {
  height: calc(100vh - 32px);
  margin: 16px;
  background: var(--md-sys-color-surface-container);
  border-right: none;
  border-radius: 28px;
  display: flex;
  flex-direction: column;
  position: sticky;
  top: 16px;
  z-index: 100;
  width: 260px;
  transition: all 0.4s cubic-bezier(0.2, 0, 0, 1);
  overflow: hidden;
  box-shadow: var(--md-sys-elevation-2);
  user-select: none;
  -webkit-user-drag: none;
}

.sidebar.collapsed {
  width: 68px;
}

/* 侧边栏头部 */
.sidebar-header {
  height: 64px;
  display: flex;
  align-items: center;
  padding: 0 20px;
  margin-bottom: 8px;
}

.logo-wrapper {
  display: flex;
  align-items: center;
  gap: 16px;
  overflow: hidden;
  padding: 0;
}

.logo-icon {
  width: 40px;
  height: 40px;
  min-width: 40px;
  background: linear-gradient(135deg, var(--md-sys-color-primary), var(--md-sys-color-tertiary));
  color: var(--md-sys-color-on-primary);
  border-radius: 14px;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: var(--md-sys-elevation-2);
  transition: all 0.3s ease;
}

.sidebar.collapsed .logo-icon {
  width: 36px;
  height: 36px;
  min-width: 36px;
  border-radius: 12px;
}

.logo-icon span {
  font-size: 24px;
}

.logo-text {
  font-size: 24px;
  font-weight: 700;
  color: var(--md-sys-color-on-surface);
  white-space: nowrap;
  font-family: 'Google Sans', sans-serif;
  letter-spacing: -0.5px;
  background: linear-gradient(90deg, var(--md-sys-color-primary), var(--md-sys-color-tertiary));
  -webkit-background-clip: text;
  background-clip: text;
  -webkit-text-fill-color: transparent;
}

/* 导航菜单 */
.sidebar-nav {
  flex: 1;
  padding: 0 16px;
  overflow-y: auto;
  overflow-x: hidden;
}

.nav-section {
  display: flex;
  flex-direction: column;
  gap: 6px;
  margin-bottom: 16px;
}

.nav-section-title {
  font-size: 12px;
  font-weight: 600;
  color: var(--md-sys-color-primary);
  padding: 16px 16px 8px;
  white-space: nowrap;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  opacity: 0.8;
}

.nav-item {
  text-decoration: none;
  display: block;
}

.nav-item-content {
  display: flex;
  align-items: center;
  gap: 12px;
  height: 44px;
  padding: 0 16px;
  border-radius: 22px;
  cursor: pointer;
  position: relative;
  transition: all 0.2s cubic-bezier(0.2, 0, 0, 1);
  overflow: visible;
  color: var(--md-sys-color-on-surface-variant);
  font-weight: 500;
}

.nav-item-content:hover {
  background: var(--md-sys-color-surface-container-high);
  color: var(--md-sys-color-on-surface);
  transform: translateX(4px);
}

.nav-item.active .nav-item-content,
.nav-item .nav-item-content.active {
  background: var(--md-sys-color-secondary-container);
  color: var(--md-sys-color-on-secondary-container);
  font-weight: 600;
}

.nav-item.active .nav-item-content:hover,
.nav-item .nav-item-content.active:hover {
  transform: none;
  box-shadow: var(--md-sys-elevation-1);
}

.nav-icon-wrapper {
  width: 24px;
  height: 24px;
  min-width: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.nav-icon {
  font-size: 24px;
}

.nav-text {
  font-size: 14px;
  font-weight: 500;
  white-space: nowrap;
}

/* 导航组样式 */
.nav-group {
  display: flex;
  flex-direction: column;
}

.nav-group-header.active {
  color: var(--md-sys-color-primary);
}

.nav-arrow {
  margin-left: auto;
  font-size: 20px;
  color: var(--md-sys-color-on-surface-variant);
}

/* 子菜单样式 */
.nav-children {
  display: flex;
  flex-direction: column;
  gap: 2px;
  margin-top: 4px;
  overflow: hidden;
}

.nav-child-item .nav-item-content {
  height: 40px;
  padding-left: 20px; /* 增加缩进 */
}

.nav-child-item .nav-icon {
  font-size: 18px;
}

/* 侧边栏底部 */
.sidebar-footer {
  padding: 12px;
  border-top: 1px solid var(--md-sys-color-outline-variant);
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.footer-button {
  display: flex;
  align-items: center;
  gap: 12px;
  height: 44px;
  padding: 0 16px;
  border-radius: 22px;
  background: transparent;
  border: none;
  color: var(--md-sys-color-on-surface-variant);
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
  white-space: nowrap;
  overflow: hidden;
  position: relative;
}

.footer-button.active {
  background: var(--md-sys-color-secondary-container);
  color: var(--md-sys-color-on-secondary-container);
}

.footer-button:hover {
  background: var(--md-sys-color-surface-container-highest);
  color: var(--md-sys-color-on-surface);
}

.footer-icon {
  font-size: 24px;
}

/* 过渡动画 */
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

.slide-fade-enter-active,
.slide-fade-leave-active {
  transition: all 0.2s;
}

.slide-fade-enter-from,
.slide-fade-leave-to {
  opacity: 0;
  transform: translateX(-10px);
}

/* 展开动画 */
.expand-enter-active,
.expand-leave-active {
  transition: all 0.25s cubic-bezier(0.2, 0, 0, 1);
  overflow: hidden;
}

.expand-enter-from,
.expand-leave-to {
  opacity: 0;
  max-height: 0;
  margin-top: 0;
}

.expand-enter-to,
.expand-leave-from {
  opacity: 1;
  max-height: 500px; /* 足够大的高度 */
  margin-top: 4px;
}

/* 折叠状态下的样式调整 */
.sidebar.collapsed .nav-item-content {
  justify-content: center;
  padding: 0;
}

.sidebar.collapsed .sidebar-header {
  justify-content: center;
  padding: 0;
}

.sidebar.collapsed .footer-button {
  justify-content: center;
  padding: 0;
}

.sidebar.collapsed .nav-child-item .nav-item-content {
  padding-left: 0;
}

/* 折叠状态下的悬停提示 */
.sidebar.collapsed .nav-item:hover .nav-item-content::after,
.sidebar.collapsed .footer-button:hover::after {
  content: attr(title);
  position: absolute;
  left: calc(100% + 12px);
  top: 50%;
  transform: translateY(-50%);
  background: var(--md-sys-color-inverse-surface);
  color: var(--md-sys-color-inverse-on-surface);
  padding: 8px 16px;
  border-radius: 8px;
  font-size: 13px;
  font-weight: 500;
  white-space: nowrap;
  z-index: 1000;
  box-shadow: var(--md-sys-elevation-2);
  animation: tooltipFadeIn 0.2s ease;
}

@keyframes tooltipFadeIn {
  from {
    opacity: 0;
    transform: translateY(-50%) translateX(-4px);
  }
  to {
    opacity: 1;
    transform: translateY(-50%) translateX(0);
  }
}
</style>
