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
        
        <router-link 
          v-for="item in menuItems" 
          :key="item.path"
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
import { ref } from 'vue'
import { useRoute } from 'vue-router'
import { Icon } from '@iconify/vue'
import { useThemeStore } from '@/stores/theme'

const route = useRoute()
const themeStore = useThemeStore()

const isCollapsed = ref(false)

const menuItems = [
  { name: '仪表盘', path: '/dashboard', icon: 'lucide:layout-dashboard' },
]

const toggleSidebar = () => {
  isCollapsed.value = !isCollapsed.value
}

const isActive = (path: string) => {
  if (path === '/dashboard') {
    return route.path === '/dashboard' || route.path === '/dashboard/'
  }
  return route.path.startsWith(path)
}
</script>

<style scoped>
.sidebar {
  height: 100vh;
  background: var(--bg-primary);
  border-right: 1px solid var(--border-color);
  display: flex;
  flex-direction: column;
  position: sticky;
  top: 0;
  z-index: 100;
  width: var(--sidebar-width);
  transition: width var(--transition-slow) cubic-bezier(0.4, 0, 0.2, 1);
  overflow: hidden;
}

.sidebar.collapsed {
  width: var(--sidebar-collapsed-width);
}

/* 侧边栏头部 */
.sidebar-header {
  height: 72px;
  display: flex;
  align-items: center;
  padding: 0 20px;
  border-bottom: 1px solid var(--border-color);
}

.logo-wrapper {
  display: flex;
  align-items: center;
  gap: 12px;
  overflow: hidden;
}

.logo-icon {
  width: 40px;
  height: 40px;
  min-width: 40px;
  background: linear-gradient(135deg, var(--primary) 0%, var(--primary-dark) 100%);
  border-radius: var(--radius);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 22px;
  color: white;
  box-shadow: 0 4px 12px rgba(59, 130, 246, 0.3);
}

.logo-text {
  font-size: 20px;
  font-weight: 700;
  color: var(--text-primary);
  white-space: nowrap;
  letter-spacing: -0.5px;
}

/* 导航菜单 */
.sidebar-nav {
  flex: 1;
  padding: 16px 12px;
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
  font-weight: 600;
  color: var(--text-tertiary);
  text-transform: uppercase;
  letter-spacing: 0.5px;
  padding: 8px 12px 12px;
  white-space: nowrap;
}

.nav-item {
  text-decoration: none;
}

.nav-item-content {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  border-radius: var(--radius);
  cursor: pointer;
  position: relative;
  transition: all var(--transition);
  overflow: hidden;
}

.nav-item-content:hover {
  background: var(--bg-hover);
}

.nav-item.active .nav-item-content {
  background: var(--primary-bg);
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
  font-size: 20px;
  color: var(--text-secondary);
  transition: all var(--transition);
}

.nav-item.active .nav-icon,
.nav-item-content:hover .nav-icon {
  color: var(--primary);
}

.nav-text {
  font-size: 14px;
  font-weight: 500;
  color: var(--text-secondary);
  white-space: nowrap;
  transition: all var(--transition);
}

.nav-item.active .nav-text,
.nav-item-content:hover .nav-text {
  color: var(--primary);
}

.active-indicator {
  position: absolute;
  left: 0;
  top: 50%;
  transform: translateY(-50%);
  width: 3px;
  height: 24px;
  background: var(--primary);
  border-radius: 0 var(--radius-full) var(--radius-full) 0;
}

/* 侧边栏底部 */
.sidebar-footer {
  padding: 12px;
  border-top: 1px solid var(--border-color);
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.footer-button {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  border-radius: var(--radius);
  background: transparent;
  border: none;
  color: var(--text-secondary);
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all var(--transition);
  white-space: nowrap;
  overflow: hidden;
}

.footer-button:hover {
  background: var(--bg-hover);
  color: var(--primary);
}

.footer-button svg {
  font-size: 20px;
  min-width: 20px;
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

/* 折叠状态下的样式调整 */
.sidebar.collapsed .nav-item-content {
  justify-content: center;
  padding: 12px 8px;
}

.sidebar.collapsed .sidebar-header {
  justify-content: center;
  padding: 0;
}

.sidebar.collapsed .footer-button {
  justify-content: center;
  padding: 12px 8px;
}

.sidebar.collapsed .active-indicator {
  left: auto;
  right: 0;
  border-radius: var(--radius-full) 0 0 var(--radius-full);
}
</style>
