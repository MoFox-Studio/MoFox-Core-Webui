<template>
  <div class="quick-actions">
    <div class="quick-actions-grid">
      <div
        v-for="(shortcut, index) in shortcuts"
        :key="shortcut.id"
        class="quick-action-card m3-card"
        :style="{ animationDelay: `${index * 0.05}s` }"
        @click="handleClick(shortcut)"
      >
        <span class="material-symbols-rounded action-icon">{{ shortcut.icon }}</span>
        <span class="action-name">{{ shortcut.name }}</span>
        <span class="action-desc">{{ shortcut.description }}</span>
        <span v-if="shortcut.badge" class="action-badge">{{ shortcut.badge }}</span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useRouter } from 'vue-router'

const router = useRouter()

interface Shortcut {
  id: string
  name: string
  icon: string
  route: string
  description: string
  badge?: string | number
}

const shortcuts: Shortcut[] = [
  { id: '1', name: 'UI聊天室', icon: 'forum', route: '/dashboard/chatroom', description: '会话管理' },
  { id: '2', name: '实时消息', icon: 'chat', route: '/dashboard/live-chat', description: '消息流' },
  { id: '3', name: '插件管理', icon: 'deployed_code', route: '/dashboard/plugin-manage', description: '插件管理' },
  { id: '4', name: '关系管理', icon: 'group', route: '/dashboard/relationship', description: '人物关系' },
  { id: '5', name: '模型配置', icon: 'psychology', route: '/dashboard/model-config', description: 'LLM模型' },
  { id: '6', name: '日志查看器', icon: 'article', route: '/dashboard/log-viewer', description: '系统日志' },
  { id: '7', name: '表情管理', icon: 'insert_emoticon', route: '/dashboard/emoji-manager', description: '表情库' },
  { id: '8', name: '机器人配置', icon: 'smart_toy', route: '/dashboard/bot-config', description: '配置编辑' },
]

function handleClick(shortcut: Shortcut) {
  router.push(shortcut.route)
}
</script>

<style scoped>
.quick-actions {
  margin-bottom: 24px;
}

.quick-actions-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
}

.quick-action-card {
  position: relative;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 20px 16px;
  min-height: 120px;
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.2, 0, 0, 1);
  overflow: hidden;
  animation: cardFadeIn 0.4s cubic-bezier(0.2, 0, 0, 1) backwards;
}

.quick-action-card::before {
  content: '';
  position: absolute;
  top: 50%;
  left: 50%;
  width: 0;
  height: 0;
  border-radius: 50%;
  background: var(--md-sys-color-primary);
  opacity: 0.1;
  transform: translate(-50%, -50%);
  transition: width 0.6s, height 0.6s;
}

.quick-action-card:hover::before {
  width: 300px;
  height: 300px;
}

.quick-action-card:hover {
  transform: translateY(-8px);
  box-shadow: var(--md-sys-elevation-3);
  background: var(--md-sys-color-surface-container-high);
}

.quick-action-card:active {
  transform: translateY(-4px) scale(0.98);
}

.action-icon {
  font-size: 36px;
  color: var(--md-sys-color-primary);
  margin-bottom: 8px;
  transition: transform 0.3s ease;
  z-index: 1;
}

.quick-action-card:hover .action-icon {
  transform: scale(1.15) rotate(5deg);
}

.action-name {
  font-size: 15px;
  font-weight: 600;
  color: var(--md-sys-color-on-surface);
  margin-bottom: 4px;
  z-index: 1;
}

.action-desc {
  font-size: 12px;
  color: var(--md-sys-color-on-surface-variant);
  opacity: 0.8;
  z-index: 1;
}

.action-badge {
  position: absolute;
  top: 12px;
  right: 12px;
  background: var(--md-sys-color-error);
  color: var(--md-sys-color-on-error);
  font-size: 11px;
  font-weight: 600;
  padding: 2px 8px;
  border-radius: 10px;
  min-width: 20px;
  text-align: center;
  z-index: 1;
}

@keyframes cardFadeIn {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* 响应式布局 */
@media (max-width: 1200px) {
  .quick-actions-grid {
    grid-template-columns: repeat(3, 1fr);
  }
}

@media (max-width: 768px) {
  .quick-actions-grid {
    grid-template-columns: repeat(2, 1fr);
    gap: 12px;
  }

  .quick-action-card {
    min-height: 100px;
    padding: 16px 12px;
  }

  .action-icon {
    font-size: 28px;
  }

  .action-name {
    font-size: 14px;
  }

  .action-desc {
    font-size: 11px;
  }
}

@media (max-width: 480px) {
  .quick-actions-grid {
    gap: 8px;
  }

  .quick-action-card {
    min-height: 90px;
    padding: 12px 8px;
  }
}
</style>
