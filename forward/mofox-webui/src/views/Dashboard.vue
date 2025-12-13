<template>
  <div class="dashboard-wrapper">
    <Sidebar />
    <div class="main-layout">
      <DashboardHeader />
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
import DashboardHeader from '@/components/DashboardHeader.vue'
</script>

<style scoped>
.dashboard-wrapper {
  min-height: 100vh;
  background-color: var(--bg-secondary);
  display: flex;
}

.main-layout {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow-x: hidden;
  min-width: 0;
}

.dashboard-content {
  flex: 1;
  padding: 24px 32px;
  max-width: 1400px;
  width: 100%;
  margin: 0 auto;
}

/* 页面过渡动画 */
.page-fade-enter-active,
.page-fade-leave-active {
  transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
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
    padding: 16px 20px;
  }
}
</style>
