<template>
  <div 
    :class="['emoji-card', { selected, banned: emoji.is_banned }]"
    @click="$emit('view-detail')"
  >
    <!-- 选择框 -->
    <div class="select-checkbox" :class="{ checked: selected }" @click.stop="$emit('select')">
      <span class="material-symbols-rounded check-icon">check</span>
    </div>

    <!-- 表情图片 -->
    <div class="emoji-image-container">
      <img
        v-if="emoji.thumbnail"
        :src="emoji.thumbnail"
        alt="表情包缩略图"
        class="emoji-image"
        loading="lazy"
      />
      <div v-else class="placeholder">
        <span class="material-symbols-rounded">broken_image</span>
      </div>

      <!-- 禁用标记 -->
      <div v-if="emoji.is_banned" class="banned-badge">
        <span class="material-symbols-rounded">block</span>
      </div>

      <!-- 悬浮操作按钮 -->
      <div class="hover-actions">
        <button 
          class="action-button view" 
          title="查看详情"
          @click.stop="$emit('view-detail')"
        >
          <span class="material-symbols-rounded">visibility</span>
        </button>
        <button 
          class="action-button delete" 
          title="删除"
          @click.stop="handleDelete"
        >
          <span class="material-symbols-rounded">delete</span>
        </button>
      </div>
    </div>

    <!-- 表情信息 -->
    <div class="emoji-info">
      <div class="emoji-description" :title="fullDescription">
        {{ refinedDescription }}
      </div>
      
      <!-- 情感标签 -->
      <div v-if="displayEmotions && displayEmotions.length > 0" class="emotion-tags">
        <span 
          v-for="emotion in displayEmotions.slice(0, 3)" 
          :key="emotion" 
          class="emotion-tag"
        >
          {{ emotion }}
        </span>
      </div>

      <!-- 统计信息 -->
      <div class="stats">
        <span class="stat-item" title="查询次数">
          <span class="material-symbols-rounded">visibility</span>
          {{ emoji.query_count }}
        </span>
        <span class="stat-item" title="使用次数">
          <span class="material-symbols-rounded">emoji_emotions</span>
          {{ emoji.usage_count }}
        </span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { EmojiItem } from '@/api/emoji'

const props = defineProps<{
  emoji: EmojiItem
  selected: boolean
}>()

const emit = defineEmits<{
  select: []
  'view-detail': []
  delete: []
}>()

// 解析联合格式的描述
const parseDescription = (description: string) => {
  // 格式: "精炼描述 Keywords: [关键词] Desc: 详细描述"
  const keywordsMatch = description.match(/Keywords:\s*\[(.*?)\]/)
  const refinedMatch = description.match(/^(.*?)\s*Keywords:/)

  return {
    refined: refinedMatch ? refinedMatch[1].trim() : description,
    keywords: keywordsMatch ? keywordsMatch[1].split(',').map(k => k.trim()).filter(Boolean) : []
  }
}

// 计算显示的精炼描述
const refinedDescription = computed(() => {
  const parsed = parseDescription(props.emoji.description)
  return parsed.refined || props.emoji.description
})

// 计算显示的完整描述（用于 title）
const fullDescription = computed(() => props.emoji.description)

// 计算显示的情感标签（优先使用解析出的关键词）
const displayEmotions = computed(() => {
  const parsed = parseDescription(props.emoji.description)
  return parsed.keywords.length > 0 ? parsed.keywords : props.emoji.emotions
})

const handleDelete = () => {
  if (confirm(`确定要删除表情包"${refinedDescription.value}"吗？`)) {
    emit('delete')
  }
}

</script>

<style scoped>
.emoji-card {
  position: relative;
  background: var(--md-sys-color-surface);
  border-radius: 12px;
  overflow: hidden;
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  box-shadow: var(--md-sys-elevation-1);
}

.emoji-card:hover {
  box-shadow: var(--md-sys-elevation-3);
  transform: translateY(-4px);
}

.emoji-card.selected::after {
  content: "";
  position: absolute;
  inset: 0;
  border: 3px solid var(--md-sys-color-primary);
  border-radius: 12px;
  pointer-events: none;
  z-index: 10;
}

.emoji-card.banned {
  opacity: 0.6;
}

.select-checkbox {
  position: absolute;
  top: 8px;
  left: 8px;
  z-index: 2;
  width: 24px;
  height: 24px;
  background: rgba(0, 0, 0, 0.4);
  border: 2px solid var(--md-sys-color-outline-variant);
  border-radius: 4px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
  backdrop-filter: blur(4px);
}

.select-checkbox.checked {
  background: var(--md-sys-color-primary);
  border-color: var(--md-sys-color-primary);
}

.check-icon {
  font-size: 18px;
  color: var(--md-sys-color-on-primary);
  opacity: 0;
  transform: scale(0.5);
  transition: all 0.2s;
}

.select-checkbox.checked .check-icon {
  opacity: 1;
  transform: scale(1);
}

.emoji-image-container {
  position: relative;
  width: 100%;
  padding-top: 100%; /* 1:1 aspect ratio */
  background: var(--md-sys-color-surface-container);
  overflow: hidden;
}

.emoji-image {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  object-fit: contain;
  padding: 8px;
}

.placeholder {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--md-sys-color-on-surface-variant);
  opacity: 0.3;
}

.placeholder .material-symbols-rounded {
  font-size: 48px;
}

.banned-badge {
  position: absolute;
  top: 8px;
  right: 8px;
  width: 32px;
  height: 32px;
  background: var(--md-sys-color-error);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 2px 4px rgba(0,0,0,0.2);
}

.banned-badge .material-symbols-rounded {
  font-size: 20px;
  color: var(--md-sys-color-on-error);
}

.hover-actions {
  position: absolute;
  bottom: 8px;
  left: 50%;
  transform: translateX(-50%);
  display: flex;
  gap: 8px;
  opacity: 0;
  transition: opacity 0.2s;
}

.emoji-card:hover .hover-actions {
  opacity: 1;
}

.action-button {
  width: 36px;
  height: 36px;
  border: none;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.2s;
  box-shadow: 0 2px 8px rgba(0,0,0,0.3);
}

.action-button.view {
  background: var(--md-sys-color-primary);
  color: var(--md-sys-color-on-primary);
}

.action-button.view:hover {
  background: var(--md-sys-color-primary-container);
  color: var(--md-sys-color-on-primary-container);
}

.action-button.delete {
  background: var(--md-sys-color-error);
  color: var(--md-sys-color-on-error);
}

.action-button.delete:hover {
  background: var(--md-sys-color-error-container);
  color: var(--md-sys-color-on-error-container);
}

.action-button .material-symbols-rounded {
  font-size: 20px;
}

.emoji-info {
  padding: 12px;
}

.emoji-description {
  font-size: 14px;
  font-weight: 500;
  color: var(--md-sys-color-on-surface);
  margin-bottom: 8px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.emotion-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
  margin-bottom: 8px;
}

.emotion-tag {
  font-size: 11px;
  padding: 2px 8px;
  background: var(--md-sys-color-secondary-container);
  color: var(--md-sys-color-on-secondary-container);
  border-radius: 12px;
}

.stats {
  display: flex;
  gap: 12px;
  font-size: 12px;
  color: var(--md-sys-color-on-surface-variant);
}

.stat-item {
  display: flex;
  align-items: center;
  gap: 4px;
}

.stat-item .material-symbols-rounded {
  font-size: 16px;
}

@media (max-width: 768px) {
  .hover-actions {
    opacity: 1; /* 移动端始终显示 */
  }

  .action-button {
    width: 32px;
    height: 32px;
  }
}
</style>
