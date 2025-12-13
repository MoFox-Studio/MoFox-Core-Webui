<template>
  <aside class="sidebar" :class="{ collapsed: isCollapsed }">
    <!-- 侧边栏头部 -->
    <div class="sidebar-header">
      <div class="logo-wrapper">
        <div class="logo-icon">
          <Icon icon="lucide:bot" />
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
        
        <!-- 普通菜单项 -->
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
                <Icon :icon="item.icon" class="nav-icon" />
              </div>
              <Transition name="slide-fade">
                <span v-if="!isCollapsed" class="nav-text">{{ item.name }}</span>
              </Transition>
              <Transition name="fade">
                <Icon 
                  v-if="!isCollapsed" 
                  :icon="expandedGroups[item.key] ? 'lucide:chevron-down' : 'lucide:chevron-right'" 
                  class="nav-arrow"
                />
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
                      <Icon :icon="child.icon" class="nav-icon" />
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
                <Icon :icon="item.icon" class="nav-icon" />
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
      <!-- 主题切换 -->
      <button 
        class="footer-button theme-button" 
        @click="themeStore.toggleTheme"
        :title="themeStore.theme === 'light' ? '切换到深色模式' : '切换到浅色模式'"
      >
        <Icon :icon="themeStore.theme === 'light' ? 'lucide:moon' : 'lucide:sun'" />
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
        <Icon :icon="isCollapsed ? 'lucide:chevrons-right' : 'lucide:chevrons-left'" class="collapse-icon" />
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
import { Icon } from '@iconify/vue'
import { useThemeStore } from '@/stores/theme'

interface MenuItem {
  name: string
  path: string
  icon: string
  key?: string
  children?: MenuItem[]
}

const route = useRoute()
const themeStore = useThemeStore()

const isCollapsed = ref(false)

// 可折叠组的展开状态
const expandedGroups = reactive<Record<string, boolean>>({
  config: true  // 默认展开配置组
})

const menuItems: MenuItem[] = [
  { name: '仪表盘', path: '/dashboard', icon: 'lucide:layout-dashboard' },
  { 
    name: '配置管理', 
    path: '/dashboard/config', 
    icon: 'lucide:settings',
    key: 'config',
    children: [
      { name: '机器人配置', path: '/dashboard/bot-config', icon: 'lucide:bot' },
      { name: '模型配置', path: '/dashboard/model-config', icon: 'lucide:brain' },
      { name: '插件配置', path: '/dashboard/plugin-config', icon: 'lucide:puzzle' },
    ]
  },
  { 
    name: '日志管理', 
    path: '/dashboard/log-management', 
    icon: 'lucide:settings',
    key: 'log-management',
    children: [
      { name: '日志查看器', path: '/dashboard/log-viewer', icon: 'lucide:file-text' },
      { name: '实时日志', path: '/dashboard/live-log', icon: 'lucide:radio' },
    ]
  },
  { name: '插件管理', path: '/dashboard/plugin-manage', icon: 'lucide:package' },
  { name: '插件市场', path: '/dashboard/marketplace', icon: 'lucide:store' },
  { name: 'MoFox-Bot更新', path: '/dashboard/git-update', icon: 'lucide:git-branch' },
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
  background: rgba(255, 255, 255, 0.8);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border-right: 1px solid rgba(255, 255, 255, 0.5);
  display: flex;
  flex-direction: column;
  position: sticky;
  top: 0;
  z-index: 100;
  width: var(--sidebar-width);
  transition: width var(--transition-slow) cubic-bezier(0.4, 0, 0.2, 1);
  overflow: hidden;
  box-shadow: var(--shadow-sm);
}

[data-theme="dark"] .sidebar {
  background: rgba(30, 41, 59, 0.8);
  border-right: 1px solid rgba(255, 255, 255, 0.05);
}

.sidebar.collapsed {
  width: var(--sidebar-collapsed-width);
}

/* 侧边栏头部 */
.sidebar-header {
  height: 88px;
  display: flex;
  align-items: center;
  padding: 0 24px;
  margin-bottom: 12px;
}

.logo-wrapper {
  display: flex;
  align-items: center;
  gap: 16px;
  overflow: hidden;
}

.logo-icon {
  width: 48px;
  height: 48px;
  min-width: 48px;
  background: linear-gradient(135deg, var(--primary) 0%, var(--primary-hover) 100%);
  border-radius: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 26px;
  color: white;
  box-shadow: var(--shadow-soft);
  transition: transform var(--transition);
}

.logo-wrapper:hover .logo-icon {
  transform: rotate(-5deg) scale(1.05);
}

.logo-text {
  font-size: 24px;
  font-weight: 800;
  color: var(--text-primary);
  white-space: nowrap;
  letter-spacing: -0.5px;
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
}

.nav-section-title {
  font-size: 12px;
  font-weight: 700;
  color: var(--text-tertiary);
  text-transform: uppercase;
  letter-spacing: 1px;
  padding: 16px 16px 8px;
  white-space: nowrap;
}

.nav-item {
  text-decoration: none;
}

.nav-item-content {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 14px 16px;
  border-radius: var(--radius);
  cursor: pointer;
  position: relative;
  transition: all var(--transition);
  overflow: hidden;
  color: var(--text-secondary);
}

.nav-item-content:hover {
  background: var(--bg-tertiary);
  color: var(--primary);
}

.nav-item.active .nav-item-content {
  background: var(--primary-bg);
  color: var(--primary);
  font-weight: 600;
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
  font-size: 22px;
  transition: all var(--transition);
}

.nav-item.active .nav-icon {
  transform: scale(1.1);
}

.nav-text {
  font-size: 15px;
  white-space: nowrap;
  transition: all var(--transition);
}

.active-indicator {
  position: absolute;
  right: 12px;
  top: 50%;
  transform: translateY(-50%);
  width: 6px;
  height: 6px;
  background: var(--primary);
  border-radius: 50%;
  box-shadow: 0 0 0 2px var(--primary-lighter);
}

/* 导航组样式 */
.nav-group {
  display: flex;
  flex-direction: column;
}

.nav-group-header {
  user-select: none;
}

.nav-group-header.active .nav-icon {
  color: var(--primary);
}

.nav-group-header.active .nav-text {
  color: var(--primary);
}

.nav-group-header.expanded {
  background: var(--bg-tertiary);
}

.nav-arrow {
  margin-left: auto;
  font-size: 18px;
  color: var(--text-tertiary);
  transition: transform var(--transition);
}

.nav-group-header.expanded .nav-arrow {
  color: var(--primary);
  transform: rotate(180deg);
}

/* 子菜单样式 */
.nav-children {
  display: flex;
  flex-direction: column;
  gap: 4px;
  padding-left: 12px;
  margin-top: 6px;
  overflow: hidden;
}

.nav-child-item .nav-item-content {
  padding: 10px 16px;
  font-size: 14px;
}

.nav-child-item .nav-icon {
  font-size: 18px;
}

.nav-child-item.active .nav-item-content {
  background: var(--primary-bg);
}

/* 侧边栏底部 */
.sidebar-footer {
  padding: 24px 16px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.footer-button {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 14px 16px;
  border-radius: var(--radius);
  background: transparent;
  border: none;
  color: var(--text-secondary);
  font-size: 15px;
  font-weight: 600;
  cursor: pointer;
  transition: all var(--transition);
  white-space: nowrap;
  overflow: hidden;
}

.footer-button:hover {
  background: var(--bg-tertiary);
  color: var(--primary);
}

.footer-button svg {
  font-size: 22px;
  min-width: 22px;
}

.collapse-icon {
  transition: transform var(--transition-slow);
}

/* 过渡动画 */
.fade-enter-active,
.fade-leave-active {
  transition: opacity var(--transition);
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

.slide-fade-enter-active,
.slide-fade-leave-active {
  transition: all var(--transition);
}

.slide-fade-enter-from,
.slide-fade-leave-to {
  opacity: 0;
  transform: translateX(-10px);
}

/* 展开动画 */
.expand-enter-active,
.expand-leave-active {
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
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
  max-height: 300px;
  margin-top: 6px;
}

/* 折叠状态下的样式调整 */
.sidebar.collapsed .nav-item-content {
  justify-content: center;
  padding: 14px 0;
}

.sidebar.collapsed .sidebar-header {
  justify-content: center;
  padding: 0;
}

.sidebar.collapsed .footer-button {
  justify-content: center;
  padding: 14px 0;
}

.sidebar.collapsed .active-indicator {
  right: 8px;
  top: 12px;
  transform: none;
}
</style>
