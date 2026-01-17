<!--
  @file App.vue
  @description 应用根组件
  
  该组件负责：
  1. 提供路由视图容器 (router-view)
  2. 初始化全局主题
  3. 管理全局 Toast 提示系统
  4. 启动/停止后台更新检查器
-->
<template>
  <!-- 外网访问警告卡片 -->
  <ExternalAccessWarning />

  <!-- 路由视图：根据当前路由渲染对应的页面组件 -->
  <router-view />
  
  <!-- 全局 Toast 提示：使用 Vue Transition 组件实现进入/离开动画 -->
  <Transition name="toast">
    <!-- M3 风格的 Snackbar 提示条 -->
    <div v-if="toast.show" :class="['m3-snackbar', toast.type]">
      <!-- 状态图标：成功显示勾选，错误显示叹号 -->
      <span class="material-symbols-rounded icon">
        {{ toast.type === 'success' ? 'check_circle' : 'error' }}
      </span>
      <!-- 提示消息文本 -->
      <span class="message">{{ toast.message }}</span>
    </div>
  </Transition>
</template>

<script setup lang="ts">
/**
 * 根组件脚本
 * 使用 <script setup> 语法糖，自动暴露顶层绑定到模板
 */

// ==================== 依赖导入 ====================
import { onMounted, onUnmounted, ref } from 'vue'
import { useThemeStore } from '@/stores/theme'  // 主题状态管理
import { startUpdateChecker, stopUpdateChecker, setToastCallback } from '@/utils/updateChecker'  // 更新检查工具
import ExternalAccessWarning from '@/components/ExternalAccessWarning.vue'  // 外网访问警告组件

// ==================== 主题初始化 ====================
// 调用 useThemeStore 会自动应用保存的主题设置
useThemeStore()

// ==================== Toast 状态管理 ====================

/**
 * Toast 提示的响应式状态
 * @property {boolean} show - 是否显示 Toast
 * @property {string} message - 提示消息内容
 * @property {'success' | 'error'} type - 提示类型（成功/错误）
 */
const toast = ref({ show: false, message: '', type: 'success' as 'success' | 'error' })

/**
 * 显示 Toast 提示
 * @param {string} message - 要显示的消息
 * @param {'success' | 'error'} type - 提示类型
 */
function showToast(message: string, type: 'success' | 'error') {
  toast.value = { show: true, message, type }
  // 3 秒后自动隐藏
  setTimeout(() => {
    toast.value.show = false
  }, 3000)
}

// ==================== 生命周期钩子 ====================

/**
 * 组件挂载完成后执行
 * - 设置 Toast 回调函数供其他模块调用
 * - 启动后台更新检查器
 */
onMounted(() => {
  setToastCallback(showToast)
  startUpdateChecker()
})

/**
 * 组件卸载前执行
 * - 停止更新检查器，防止内存泄漏
 */
onUnmounted(() => {
  stopUpdateChecker()
})
</script>

<style scoped>
/* ==================== 全局 Toast 样式 ==================== */

/**
 * M3 Snackbar 风格的 Toast 提示条
 * - 固定在页面右下角
 * - 使用 inverse 颜色方案确保在任何背景下都清晰可见
 */
.m3-snackbar {
  position: fixed;
  bottom: 24px;
  right: 24px;
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 14px 16px;
  background: var(--md-sys-color-inverse-surface);      /* 反色表面背景 */
  color: var(--md-sys-color-inverse-on-surface);        /* 反色表面上的文字 */
  border-radius: 4px;
  box-shadow: var(--md-sys-elevation-3);                /* M3 阴影层级 3 */
  font-size: 14px;
  line-height: 20px;
  z-index: 9999;                                         /* 确保在最上层 */
  min-width: 288px;
  max-width: 600px;
}

/* 成功状态图标颜色 - 浅绿色 */
.m3-snackbar.success .icon {
  color: #a5d6a7;
}

/* 错误状态图标颜色 - 浅红色 */
.m3-snackbar.error .icon {
  color: #ef9a9a;
}

/* 图标基础样式 */
.icon {
  font-size: 20px;
}

/* 消息文本填充剩余空间 */
.message {
  flex: 1;
}

/* ==================== Toast 动画 ==================== */

/* 进入和离开动画的持续时间和缓动函数 */
.toast-enter-active,
.toast-leave-active {
  transition: all 0.3s cubic-bezier(0.2, 0, 0, 1);  /* M3 标准缓动 */
}

/* 进入前和离开后的初始/最终状态 */
.toast-enter-from,
.toast-leave-to {
  opacity: 0;
  transform: translateY(20px);  /* 从下方滑入 */
}

/* ==================== 响应式适配 ==================== */

/* 移动端：Toast 占满底部宽度 */
@media (max-width: 768px) {
  .m3-snackbar {
    bottom: 12px;
    right: 12px;
    left: 12px;
    min-width: auto;
  }
}
</style>
