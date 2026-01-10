<!--
  @file GitUpdateView.vue
  @description 更新管理页面 - 三标签页设计
  
  功能说明：
  1. UI 更新标签页 - WebUI 静态文件更新
  2. 主程序更新标签页 - MoFox-Bot 主程序 Git 更新
  3. Git 设置标签页 - Git 环境配置
  
  特殊处理：
  - 非 Git 仓库时主程序更新功能受限
  - Git 未安装时显示安装指引
  - 更新完成后显示重启提示
-->
<template>
  <div class="update-view">
    <!-- 头部 -->
    <div class="page-header">
      <div class="header-content">
        <div class="header-icon">
          <span class="material-symbols-rounded">system_update</span>
        </div>
        <div class="header-text">
          <h1>更新管理</h1>
          <p>管理 MoFox-Bot 和 WebUI 的更新</p>
        </div>
      </div>
    </div>

    <!-- 标签页导航 -->
    <div class="tabs-nav">
      <button 
        v-for="tab in tabs" 
        :key="tab.id"
        class="tab-item"
        :class="{ active: activeTab === tab.id }"
        @click="activeTab = tab.id"
      >
        <span class="material-symbols-rounded">{{ tab.icon }}</span>
        <span class="tab-label">{{ tab.label }}</span>
      </button>
    </div>

    <!-- 标签页内容 -->
    <div class="tab-content">
      <!-- UI 更新标签页 -->
      <UIUpdateTab 
        v-show="activeTab === 'ui'"
        ref="uiUpdateTabRef"
        @update-complete="handleUIUpdateComplete"
      />
      
      <!-- 主程序更新标签页 -->
      <MainUpdateTab 
        v-show="activeTab === 'main'"
        ref="mainUpdateTabRef"
        @update-complete="handleMainUpdateComplete"
      />
      
      <!-- Git 设置标签页 -->
      <GitSettingsTab 
        v-show="activeTab === 'git'"
        ref="gitSettingsTabRef"
      />
    </div>

    <!-- 重启提示弹窗 -->
    <RestartDialog
      v-model="showRestartDialog"
      :update-type="restartType"
      :changelog="restartChangelog"
      @restart="handleRestart"
      @later="handleRestartLater"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import UIUpdateTab from '@/components/update/UIUpdateTab.vue'
import MainUpdateTab from '@/components/update/MainUpdateTab.vue'
import GitSettingsTab from '@/components/update/GitSettingsTab.vue'
import RestartDialog from '@/components/update/RestartDialog.vue'
import { restartBot } from '@/api'

// 标签页配置
const tabs = [
  { id: 'ui', label: 'UI 更新', icon: 'web' },
  { id: 'main', label: '主程序', icon: 'terminal' },
  { id: 'git', label: 'Git 设置', icon: 'settings' }
]

// 当前激活的标签页
const activeTab = ref('ui')

// 组件引用
const uiUpdateTabRef = ref<InstanceType<typeof UIUpdateTab> | null>(null)
const mainUpdateTabRef = ref<InstanceType<typeof MainUpdateTab> | null>(null)
const gitSettingsTabRef = ref<InstanceType<typeof GitSettingsTab> | null>(null)

// 重启弹窗状态
const showRestartDialog = ref(false)
const restartType = ref<'main' | 'ui' | 'both'>('main')
const restartChangelog = ref<string[]>([])

// UI 更新完成
function handleUIUpdateComplete(needsRestart: boolean) {
  if (needsRestart) {
    restartType.value = 'ui'
    restartChangelog.value = []
    showRestartDialog.value = true
  }
}

// 主程序更新完成
function handleMainUpdateComplete(needsRestart: boolean) {
  if (needsRestart) {
    restartType.value = 'main'
    restartChangelog.value = []
    showRestartDialog.value = true
  }
}

// 重启
async function handleRestart() {
  showRestartDialog.value = false
  try {
    // 调用后端重启接口
    await restartBot()
  } catch (error) {
    console.error('重启失败:', error)
  }
}

// 稍后重启
function handleRestartLater() {
  showRestartDialog.value = false
}

// 初始化
onMounted(() => {
  // 可以在这里添加初始化逻辑
})
</script>

<style scoped>
.update-view {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  padding: 16px;
  gap: 16px;
  animation: fadeIn 0.3s ease;
  background: var(--md-sys-color-surface);
  overflow-y: auto;
}

@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

/* 头部 */
.page-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 20px;
  padding: 24px;
  background: var(--md-sys-color-surface-container);
  border-radius: 32px;
  flex-shrink: 0;
}

.header-content {
  display: flex;
  align-items: center;
  gap: 16px;
}

.header-icon {
  width: 56px;
  height: 56px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--md-sys-color-primary-container);
  border-radius: 16px;
  color: var(--md-sys-color-on-primary-container);
}

.header-icon .material-symbols-rounded {
  font-size: 28px;
}

.header-text h1 {
  margin: 0;
  font-size: 28px;
  font-weight: 400;
  color: var(--md-sys-color-on-surface);
  line-height: 1.2;
}

.header-text p {
  margin: 4px 0 0 0;
  font-size: 14px;
  color: var(--md-sys-color-on-surface-variant);
}

/* 标签页导航 */
.tabs-nav {
  display: flex;
  gap: 8px;
  padding: 8px;
  background: var(--md-sys-color-surface-container-low);
  border-radius: 32px;
  flex-shrink: 0;
}

.tab-item {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 12px 16px;
  border: none;
  border-radius: 24px;
  background: transparent;
  color: var(--md-sys-color-on-surface-variant);
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.tab-item:hover:not(.active) {
  background: var(--md-sys-color-surface-container);
}

.tab-item.active {
  background: var(--md-sys-color-secondary-container);
  color: var(--md-sys-color-on-secondary-container);
}

.tab-item .material-symbols-rounded {
  font-size: 20px;
}

/* 标签页内容 */
.tab-content {
  flex: 1;
}

/* 响应式 */
@media (max-width: 768px) {
  .update-view {
    padding: 16px;
  }

  .header-icon {
    width: 48px;
    height: 48px;
  }

  .header-icon .material-symbols-rounded {
    font-size: 24px;
  }

  .header-text h1 {
    font-size: 24px;
  }

  .tabs-nav {
    flex-wrap: wrap;
  }

  .tab-item {
    padding: 10px 12px;
  }

  .tab-label {
    display: none;
  }
}
</style>
