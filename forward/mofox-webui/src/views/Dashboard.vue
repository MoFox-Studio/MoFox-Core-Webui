<template>
  <div class="dashboard-wrapper">
    <Sidebar />
    <div class="main-layout">
      <main class="dashboard-content">
        <router-view v-slot="{ Component }">
          <Transition name="page-fade" mode="out-in">
            <component :is="Component" />
          </Transition>
        </router-view>
      </main>
    </div>
  </div>
</template>

<script setup lang="ts">
import Sidebar from '@/components/Sidebar.vue'
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
  filter: blur(20px);
  opacity: 0.5;
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
  filter: blur(20px);
  opacity: 0.5;
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
