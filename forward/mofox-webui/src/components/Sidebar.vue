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
        <template v-for="item in menuItems" :key="item.path">
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
                  class="nav-item nav-child-item"
                  :class="{ active: isActive(child.path) }"
                  v-slot="{ navigate }"
                  custom
                >
                  <div class="nav-item-content" @click="navigate" :title="child.name">
                    <div class="nav-icon-wrapper">
                      <span class="material-symbols-rounded nav-icon">{{ child.icon }}</span>
                    </div>
                    <span class="nav-text">{{ child.name }}</span>
                    <Transition name="fade">
                      <div v-if="isActive(child.path)" class="active-indicator"></div>
                    </Transition>
                  </div>
                </router-link>
              </div>
            </Transition>
          </div>
          
          <!-- 普通菜单项 -->
          <router-link 
            v-else
            :to="item.path" 
            class="nav-item"
            :class="{ active: isActive(item.path) }"
            v-slot="{ navigate }"
            custom
          >
            <div class="nav-item-content" @click="navigate" :title="item.name">
              <div class="nav-icon-wrapper">
                <span class="material-symbols-rounded nav-icon">{{ item.icon }}</span>
              </div>
              <Transition name="slide-fade">
                <span v-if="!isCollapsed" class="nav-text">{{ item.name }}</span>
              </Transition>
              <Transition name="fade">
                <div v-if="isActive(item.path)" class="active-indicator"></div>
              </Transition>
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

      <!-- 主题切换 -->
      <button 
        class="footer-button theme-button" 
        @click="themeStore.toggleTheme"
        :title="themeStore.theme === 'light' ? '切换到深色模式' : '切换到浅色模式'"
      >
        <span class="material-symbols-rounded footer-icon">
          {{ themeStore.theme === 'light' ? 'dark_mode' : 'light_mode' }}
        </span>
        <Transition name="slide-fade">
          <span v-if="!isCollapsed">{{ themeStore.theme === 'light' ? '深色模式' : '浅色模式' }}</span>
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
import { useRoute } from 'vue-router'
import { useThemeStore } from '@/stores/theme'
import { useUserStore } from '@/stores/user'
import { restartBot, shutdownBot } from '@/api'
import { showConfirm, showSuccess, showError } from '@/utils/dialog'

interface MenuItem {
  name: string
  path: string
  icon: string
  key?: string
  children?: MenuItem[]
}

const route = useRoute()
const themeStore = useThemeStore()
const userStore = useUserStore()

const isCollapsed = ref(false)

// 可折叠组的展开状态
const expandedGroups = reactive<Record<string, boolean>>({
  config: true,
  'log-management': true
})

const handleRestart = async () => {
  const confirmed = await showConfirm({
    title: '重启 Bot',
    message: '确定要重启 MoFox Bot 吗？这将中断当前的所有连接。',
    confirmText: '重启',
    confirmColor: 'warning'
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
    confirmText: '关闭',
    confirmColor: 'error'
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
}

const menuItems: MenuItem[] = [
  { name: '仪表盘', path: '/dashboard', icon: 'dashboard' },
  { 
    name: '配置管理', 
    path: '/dashboard/config', 
    icon: 'settings',
    key: 'config',
    children: [
      { name: '机器人配置', path: '/dashboard/bot-config', icon: 'smart_toy' },
      { name: '模型配置', path: '/dashboard/model-config', icon: 'psychology' },
      { name: '插件配置', path: '/dashboard/plugin-config', icon: 'extension' },
      { name: '表达方式', path: '/dashboard/expression', icon: 'record_voice_over' },
      { name: '关系管理', path: '/dashboard/relationship', icon: 'group' },
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
  { name: '插件管理', path: '/dashboard/plugin-manage', icon: 'deployed_code' },
  { name: '插件市场', path: '/dashboard/marketplace', icon: 'storefront' },
  { name: '系统更新', path: '/dashboard/git-update', icon: 'system_update' },
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
  height: 100vh;
  background: var(--md-sys-color-surface-container);
  border-right: 1px solid var(--md-sys-color-outline-variant);
  display: flex;
  flex-direction: column;
  position: sticky;
  top: 0;
  z-index: 100;
  width: 280px;
  transition: width 0.3s cubic-bezier(0.2, 0, 0, 1);
  overflow: hidden;
}

.sidebar.collapsed {
  width: 80px;
}

/* 侧边栏头部 */
.sidebar-header {
  height: 64px;
  display: flex;
  align-items: center;
  padding: 0 16px;
  margin-bottom: 12px;
}

.logo-wrapper {
  display: flex;
  align-items: center;
  gap: 12px;
  overflow: hidden;
  padding: 0 8px;
}

.logo-icon {
  width: 40px;
  height: 40px;
  min-width: 40px;
  background: var(--md-sys-color-primary-container);
  color: var(--md-sys-color-on-primary-container);
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.logo-icon span {
  font-size: 24px;
}

.logo-text {
  font-size: 22px;
  font-weight: 500;
  color: var(--md-sys-color-on-surface);
  white-space: nowrap;
  font-family: 'Google Sans', sans-serif;
}

/* 导航菜单 */
.sidebar-nav {
  flex: 1;
  padding: 0 12px;
  overflow-y: auto;
  overflow-x: hidden;
}

.nav-section {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.nav-section-title {
  font-size: 11px;
  font-weight: 500;
  color: var(--md-sys-color-on-surface-variant);
  padding: 16px 16px 8px;
  white-space: nowrap;
}

.nav-item {
  text-decoration: none;
  display: block;
}

.nav-item-content {
  display: flex;
  align-items: center;
  gap: 12px;
  height: 56px;
  padding: 0 16px;
  border-radius: 28px;
  cursor: pointer;
  position: relative;
  transition: all 0.2s;
  overflow: hidden;
  color: var(--md-sys-color-on-surface-variant);
}

.nav-item-content:hover {
  background: var(--md-sys-color-surface-container-highest);
  color: var(--md-sys-color-on-surface);
}

.nav-item.active .nav-item-content {
  background: var(--md-sys-color-secondary-container);
  color: var(--md-sys-color-on-secondary-container);
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
  height: 48px;
  padding-left: 24px; /* 增加缩进 */
}

.sidebar.collapsed .nav-child-item .nav-item-content {
  padding-left: 16px; /* 折叠时恢复 */
}

.nav-child-item .nav-icon {
  font-size: 20px;
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
  height: 56px;
  padding: 0 16px;
  border-radius: 28px;
  background: transparent;
  border: none;
  color: var(--md-sys-color-on-surface-variant);
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
  white-space: nowrap;
  overflow: hidden;
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
</style>
