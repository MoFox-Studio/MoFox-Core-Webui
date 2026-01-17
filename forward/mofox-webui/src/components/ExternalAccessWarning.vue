<!--
  @file ExternalAccessWarning.vue
  @description 外网访问警告卡片组件
  
  该组件负责：
  1. 检测用户是否通过外网访问
  2. 检测是否使用 HTTPS 协议
  3. 显示安全警告信息和建议
  4. 支持用户关闭（30分钟内不再显示）
-->
<template>
  <!-- 外网访问警告卡片 -->
  <Transition name="warning">
    <div v-if="showWarning" class="external-warning-card">
      <div class="warning-content">
        <span class="material-symbols-rounded warning-icon">shield_locked</span>
        <div class="warning-text">
          <div class="warning-title">
            <span class="material-symbols-rounded title-icon">public</span>
            外网访问安全警告
          </div>
          <div class="warning-message">
            检测到您正在通过公网 IP 访问本系统。为保护您的数据安全，请注意以下事项：
          </div>
          <ul class="warning-list">
            <li>
              <span class="material-symbols-rounded list-icon">lock</span>
              <span>确保使用 HTTPS 加密连接，避免数据被窃听</span>
            </li>
            <li>
              <span class="material-symbols-rounded list-icon">vpn_key</span>
              <span>请勿在公共网络环境下输入敏感信息</span>
            </li>
            <li>
              <span class="material-symbols-rounded list-icon">verified_user</span>
              <span>建议启用双因素认证以增强账户安全</span>
            </li>
            <li>
              <span class="material-symbols-rounded list-icon">network_check</span>
              <span>推荐使用 VPN 或内网访问以获得最佳安全性</span>
            </li>
          </ul>
          <div class="warning-footer">
            <span class="material-symbols-rounded footer-icon">info</span>
            <span>关闭此提醒后将在 30 分钟内不再显示</span>
          </div>
        </div>
        <button class="close-btn" @click="dismissWarning" aria-label="关闭警告">
          <span class="material-symbols-rounded">close</span>
        </button>
      </div>
    </div>
  </Transition>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'

// ==================== 状态管理 ====================

/**
 * 控制警告卡片显示状态
 */
const showWarning = ref(false)

// ==================== 检测函数 ====================

/**
 * 检测是否使用 HTTPS 协议
 * @returns {boolean} 如果使用 HTTPS 返回 true
 */
function isHttps(): boolean {
  return window.location.protocol === 'https:'
}

/**
 * 检测是否为外网访问
 * 通过检查当前访问的 hostname 判断是否为内网地址
 * @returns {boolean} 如果是外网访问返回 true
 */
function isExternalAccess(): boolean {
  const hostname = window.location.hostname
  
  // 内网地址判断
  const isLocalhost = hostname === 'localhost' || hostname === '127.0.0.1'
  const isPrivateIP = /^(10\.|172\.(1[6-9]|2[0-9]|3[01])\.|192\.168\.)/.test(hostname)
  const isLocalIPv6 = hostname === '::1' || hostname === '[::1]'
  
  return !(isLocalhost || isPrivateIP || isLocalIPv6)
}

/**
 * 检查警告是否应该显示
 * 如果距离上次关闭超过30分钟，则重新显示
 * @returns {boolean} 是否应该显示警告
 */
function shouldShowWarning(): boolean {
  const dismissedTime = localStorage.getItem('external-warning-dismissed')
  if (!dismissedTime) return true
  
  const timePassed = Date.now() - parseInt(dismissedTime)
  const thirtyMinutes = 30 * 60 * 1000 // 30分钟的毫秒数
  
  return timePassed > thirtyMinutes
}

/**
 * 关闭外网访问警告
 * 存储关闭时间戳，30分钟后重新显示
 */
function dismissWarning() {
  showWarning.value = false
  // 存储关闭时间戳
  const dismissTime = Date.now()
  localStorage.setItem('external-warning-dismissed', dismissTime.toString())
}

// ==================== 生命周期钩子 ====================

/**
 * 组件挂载时检测访问状态
 * 只有在外网访问且非 HTTPS 且超过30分钟时才显示警告
 */
onMounted(() => {
  // 如果使用 HTTPS，不显示警告
  if (isHttps()) {
    return
  }
  
  // 检测外网访问（如果是外网且超过30分钟则显示警告）
  if (isExternalAccess() && shouldShowWarning()) {
    showWarning.value = true
  }
})
</script>

<style scoped>
/* ==================== 外网访问警告卡片样式 ==================== */

/**
 * 外网访问警告卡片容器
 * - 固定在页面顶部
 * - 使用 M3 的 error container 颜色方案
 */
.external-warning-card {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  z-index: 10000;
  background: var(--md-sys-color-error-container);
  color: var(--md-sys-color-on-error-container);
  box-shadow: var(--md-sys-elevation-2);
}

/**
 * 警告内容容器
 */
.warning-content {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 16px 24px;
  max-width: 1200px;
  margin: 0 auto;
}

/**
 * 警告图标
 */
.warning-icon {
  font-size: 28px;
  color: var(--md-sys-color-error);
  flex-shrink: 0;
}

/**
 * 警告文本区域
 */
.warning-text {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

/**
 * 警告标题
 */
.warning-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 18px;
  font-weight: 600;
  line-height: 28px;
}

.warning-title .title-icon {
  font-size: 20px;
}

/**
 * 警告消息
 */
.warning-message {
  font-size: 14px;
  line-height: 20px;
  opacity: 0.9;
  margin-bottom: 4px;
}

/**
 * 警告列表
 */
.warning-list {
  list-style: none;
  padding: 0;
  margin: 0;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.warning-list li {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  font-size: 13px;
  line-height: 20px;
  opacity: 0.85;
}

.warning-list .list-icon {
  font-size: 18px;
  margin-top: 1px;
  flex-shrink: 0;
  color: var(--md-sys-color-error);
}

/**
 * 警告底部说明
 */
.warning-footer {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  line-height: 16px;
  opacity: 0.7;
  margin-top: 4px;
  font-style: italic;
}

.warning-footer .footer-icon {
  font-size: 16px;
}

/**
 * 关闭按钮
 */
.close-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 40px;
  height: 40px;
  border: none;
  background: transparent;
  color: var(--md-sys-color-on-error-container);
  border-radius: 20px;
  cursor: pointer;
  transition: background 0.2s;
  flex-shrink: 0;
}

.close-btn:hover {
  background: rgba(0, 0, 0, 0.08);
}

.close-btn:active {
  background: rgba(0, 0, 0, 0.12);
}

.close-btn .material-symbols-rounded {
  font-size: 24px;
}

/* ==================== 警告卡片动画 ==================== */

.warning-enter-active,
.warning-leave-active {
  transition: all 0.3s cubic-bezier(0.2, 0, 0, 1);
}

.warning-enter-from,
.warning-leave-to {
  opacity: 0;
  transform: translateY(-100%);
}

/* 移动端适配 */
@media (max-width: 768px) {
  .warning-content {
    padding: 12px 16px;
    gap: 12px;
  }
  
  .warning-icon {
    font-size: 24px;
  }
  
  .warning-title {
    font-size: 16px;
  }
  
  .warning-title .title-icon {
    font-size: 18px;
  }
  
  .warning-message {
    font-size: 13px;
  }
  
  .warning-list li {
    font-size: 12px;
    gap: 6px;
  }
  
  .warning-list .list-icon {
    font-size: 16px;
  }
  
  .warning-footer {
    font-size: 11px;
  }
  
  .close-btn {
    width: 36px;
    height: 36px;
  }
}
</style>
