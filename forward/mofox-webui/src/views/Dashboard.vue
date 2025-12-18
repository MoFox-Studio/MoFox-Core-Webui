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
  min-height: 100vh;
  background-color: var(--md-sys-color-surface);
  display: flex;
}

.main-layout {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow-x: hidden;
  min-width: 0;
  background-color: var(--md-sys-color-surface);
}

.dashboard-content {
  flex: 1;
  padding: 24px;
  width: 100%;
  margin: 0 auto;
}

/* 页面过渡动画 */
.page-fade-enter-active,
.page-fade-leave-active {
  transition: opacity 0.2s ease, transform 0.2s ease;
}

.page-fade-enter-from {
  opacity: 0;
  transform: translateY(10px);
}

.page-fade-leave-to {
  opacity: 0;
  transform: translateY(-10px);
}

/* 响应式 */
@media (max-width: 768px) {
  .dashboard-content {
    padding: 16px;
  }
}
</style>
