<!--
  @file Dashboard.vue
  @description 仪表盘布局容器
  
  功能说明：
  1. 作为登录后的主布局容器
  2. 包含侧边栏导航 (Sidebar)
  3. 包含浮动文档按钮 (FloatingDoc)
  4. 提供路由视图容器，渲染子页面
  
  布局结构：
  - 左侧：可折叠的侧边栏导航
  - 右侧：主内容区域（由 router-view 渲染）
  - 背景：支持自定义壁纸和模糊效果
  
  动画效果：
  - 页面切换时的淡入淡出动画
-->
<template>
  <div class="dashboard-wrapper">
    <!-- 侧边栏导航组件 -->
    <Sidebar />
    <!-- 主布局区域 -->
    <div class="main-layout">
      <main class="dashboard-content">
        <router-view v-slot="{ Component }">
          <Transition name="page-fade" mode="out-in">
            <component :is="Component" />
          </Transition>
        </router-view>
      </main>
    </div>
    <FloatingDoc />
  </div>
</template>

<script setup lang="ts">
import { onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import Sidebar from '@/components/Sidebar.vue'
import FloatingDoc from '@/components/FloatingDoc.vue'
import { checkInitStatus } from '@/router'

const router = useRouter()
const route = useRoute()

// 完全非阻塞式初始化状态检查
// 使用 requestIdleCallback 或 setTimeout 延迟执行，确保不阻塞首屏渲染
onMounted(() => {
  // 如果当前在初始化页面，跳过检查
  if (route.path === '/initialization') {
    return
  }
  
  // 延迟检查，让页面和背景先渲染
  const doCheck = async () => {
    try {
      const isInitialized = await checkInitStatus()
      
      if (!isInitialized && route.path !== '/initialization') {
        // 未初始化，跳转到初始化页面
        router.replace('/initialization')
      }
    } catch (error) {
      console.error('初始化状态检查失败:', error)
    }
  }
  
  // 使用 requestIdleCallback（如果可用）或 setTimeout 延迟执行
  if ('requestIdleCallback' in window) {
    requestIdleCallback(() => doCheck(), { timeout: 250 })
  } else {
    setTimeout(doCheck, 100)
  }
})
</script>

<style scoped>
.dashboard-wrapper {
  height: 100vh;
  background-color: transparent;
  display: flex;
  overflow: hidden;
  position: relative;
  z-index: 0;
}

.dashboard-wrapper::before {
  content: "";
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background-image: var(--app-wallpaper);
  background-size: cover;
  background-position: center;
  background-repeat: no-repeat;
  filter: blur(var(--app-wallpaper-blur, 20px));
  opacity: var(--app-wallpaper-opacity, 0.5);
  z-index: -1;
}

.main-layout {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  min-width: 0;
  background-color: transparent;
}

.main-layout::before {
  content: "";
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background-image: var(--app-wallpaper);
  background-size: cover;
  background-position: center;
  background-repeat: no-repeat;
  filter: blur(var(--app-wallpaper-blur, 20px));
  opacity: var(--app-wallpaper-opacity, 0.5);
  z-index: -1;
}

.dashboard-content {
  flex: 1;
  padding: 24px;
  width: 100%;
  margin: 0 auto;
  overflow-y: auto;
  height: 100%;
}

/* 页面过渡动画 */
.page-fade-enter-active,
.page-fade-leave-active {
  transition: opacity 0.3s cubic-bezier(0.2, 0, 0, 1), transform 0.3s cubic-bezier(0.2, 0, 0, 1);
}

.page-fade-enter-from {
  opacity: 0;
  transform: translateY(20px);
}

.page-fade-leave-to {
  opacity: 0;
  transform: translateY(-20px);
}

/* 响应式 */
@media (max-width: 768px) {
  .dashboard-content {
    padding: 16px;
  }
}
</style>
