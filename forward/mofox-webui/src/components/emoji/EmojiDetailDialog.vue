<template>
  <Teleport to="body">
    <Transition name="dialog">
      <div v-if="modelValue && emojiDetail" class="dialog-overlay" @click="handleClose">
        <div class="dialog-container" @click.stop>
          <div class="dialog-header">
            <h2>表情包详情</h2>
            <button class="close-button" @click="handleClose">
              <span class="material-symbols-rounded">close</span>
            </button>
          </div>

          <div class="dialog-content">
            <!-- 完整图片 -->
            <div class="full-image-container">
              <img
                v-if="emojiDetail.full_image"
                :src="emojiDetail.full_image"
                alt="表情包图片"
                class="full-image"
              />
            </div>

            <!-- 基本信息 -->
            <div class="detail-section">
              <h3>基本信息</h3>
              <div class="info-grid">
                <div class="info-item">
                  <label>哈希值</label>
                  <div class="value">{{ emojiDetail.hash }}</div>
                </div>
                <div class="info-item">
                  <label>格式</label>
                  <div class="value">{{ emojiDetail.format.toUpperCase() }}</div>
                </div>
                <div class="info-item">
                  <label>文件路径</label>
                  <div class="value truncate" :title="emojiDetail.full_path">
                    {{ emojiDetail.full_path }}
                  </div>
                </div>
              </div>
            </div>

            <!-- 描述编辑（解析联合格式） -->
            <div class="detail-section">
              <h3>精炼描述</h3>
              <textarea
                v-model="editableRefinedDescription"
                class="description-input"
                rows="2"
                placeholder="输入精炼的自然语言描述..."
              ></textarea>
            </div>

            <!-- 详细描述 -->
            <div class="detail-section">
              <h3>详细描述</h3>
              <textarea
                v-model="editableDetailedDescription"
                class="description-input"
                rows="4"
                placeholder="输入详细描述（不超过250字）..."
              ></textarea>
            </div>

            <!-- 情感标签编辑 -->
            <div class="detail-section">
              <h3>情感标签</h3>
              <div class="emotion-editor">
                <div class="emotion-chips">
                  <span
                    v-for="(emotion, index) in editableEmotions"
                    :key="index"
                    class="emotion-chip"
                  >
                    {{ emotion }}
                    <button @click="removeEmotion(index)">
                      <span class="material-symbols-rounded">close</span>
                    </button>
                  </span>
                </div>
                <div class="add-emotion">
                  <input
                    v-model="newEmotion"
                    type="text"
                    placeholder="添加情感标签..."
                    @keyup.enter="addEmotion"
                  />
                  <button @click="addEmotion">
                    <span class="material-symbols-rounded">add</span>
                  </button>
                </div>
              </div>
            </div>

            <!-- 统计信息 -->
            <div class="detail-section">
              <h3>统计信息</h3>
              <div class="stats-grid">
                <div class="stat-card">
                  <span class="material-symbols-rounded">visibility</span>
                  <div>
                    <div class="stat-value">{{ emojiDetail.query_count }}</div>
                    <div class="stat-label">查询次数</div>
                  </div>
                </div>
                <div class="stat-card">
                  <span class="material-symbols-rounded">emoji_emotions</span>
                  <div>
                    <div class="stat-value">{{ emojiDetail.usage_count }}</div>
                    <div class="stat-label">使用次数</div>
                  </div>
                </div>
              </div>
            </div>

            <!-- 时间信息 -->
            <div class="detail-section">
              <h3>时间信息</h3>
              <div class="info-grid">
                <div class="info-item">
                  <label>记录时间</label>
                  <div class="value">{{ formatTime(emojiDetail.record_time) }}</div>
                </div>
                <div class="info-item">
                  <label>注册时间</label>
                  <div class="value">{{ formatTime(emojiDetail.register_time) }}</div>
                </div>
                <div class="info-item">
                  <label>最后使用</label>
                  <div class="value">{{ formatTime(emojiDetail.last_used_time) }}</div>
                </div>
              </div>
            </div>

            <!-- 状态控制 -->
            <div class="detail-section">
              <h3>状态控制</h3>
              <div class="status-controls">
                <label class="switch">
                  <input v-model="editableIsBanned" type="checkbox" />
                  <span class="slider"></span>
                  <span class="label">禁用表情包</span>
                </label>
              </div>
            </div>
          </div>

          <div class="dialog-footer">
            <button class="secondary-button" @click="handleClose">
              取消
            </button>
            <button class="danger-button" @click="handleDelete">
              删除
            </button>
            <button class="primary-button" @click="handleSave" :disabled="!hasChanges">
              保存更改
            </button>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup lang="ts">
import { ref, watch, computed } from 'vue'
import { useEmojiStore } from '@/stores/emojiStore'
import { showConfirm, showAlert } from '@/utils/dialog'
import type { EmojiDetail } from '@/api/emoji'

const props = defineProps<{
  modelValue: boolean
  emojiHash: string
}>()

const emit = defineEmits<{
  'update:modelValue': [value: boolean]
  updated: []
  deleted: []
}>()

const emojiStore = useEmojiStore()
const emojiDetail = ref<EmojiDetail | null>(null)
const editableRefinedDescription = ref('')
const editableDetailedDescription = ref('')
const editableEmotions = ref<string[]>([])
const editableIsBanned = ref(false)
const newEmotion = ref('')

// 原始值，用于比较是否有变化
const originalRefinedDescription = ref('')
const originalDetailedDescription = ref('')
const originalEmotions = ref<string[]>([])
const originalIsBanned = ref(false)

// 解析联合格式的描述
const parseDescription = (description: string) => {
  // 格式: "精炼描述 Keywords: [关键词] Desc: 详细描述"
  const keywordsMatch = description.match(/Keywords:\s*\[(.*?)\]/)
  const descMatch = description.match(/Desc:\s*(.*)/)
  const refinedMatch = description.match(/^(.*?)\s*Keywords:/)

  return {
    refined: refinedMatch ? refinedMatch[1].trim() : '',
    keywords: keywordsMatch ? keywordsMatch[1].split(',').map(k => k.trim()).filter(Boolean) : [],
    detailed: descMatch ? descMatch[1].trim() : description
  }
}

// 组装联合格式的描述
const buildDescription = () => {
  const keywords = editableEmotions.value.join(',')
  return `${editableRefinedDescription.value.trim()} Keywords: [${keywords}] Desc: ${editableDetailedDescription.value.trim()}`
}

// 检查是否有变化
const hasChanges = computed(() => {
  // 比较精炼描述
  if (editableRefinedDescription.value.trim() !== originalRefinedDescription.value.trim()) {
    return true
  }
  // 比较详细描述
  if (editableDetailedDescription.value.trim() !== originalDetailedDescription.value.trim()) {
    return true
  }
  // 比较禁用状态
  if (editableIsBanned.value !== originalIsBanned.value) {
    return true
  }
  // 比较情感标签（数组）
  if (editableEmotions.value.length !== originalEmotions.value.length) {
    return true
  }
  const sortedEditable = [...editableEmotions.value].sort()
  const sortedOriginal = [...originalEmotions.value].sort()
  return !sortedEditable.every((emotion, index) => emotion === sortedOriginal[index])
})

// 监听打开，加载详情
watch(() => [props.modelValue, props.emojiHash], async ([isOpen, hash]) => {
  if (isOpen && hash) {
    try {
      emojiDetail.value = await emojiStore.getEmojiDetail(hash)
      if (emojiDetail.value) {
        // 解析联合格式
        const parsed = parseDescription(emojiDetail.value.description)
        editableRefinedDescription.value = parsed.refined
        editableDetailedDescription.value = parsed.detailed
        
        // 优先使用解析出的关键词，否则使用 emotions 字段
        editableEmotions.value = parsed.keywords.length > 0 
          ? parsed.keywords 
          : [...emojiDetail.value.emotions]
        
        editableIsBanned.value = emojiDetail.value.is_banned

        // 保存原始值
        originalRefinedDescription.value = parsed.refined
        originalDetailedDescription.value = parsed.detailed
        originalEmotions.value = parsed.keywords.length > 0 
          ? [...parsed.keywords] 
          : [...emojiDetail.value.emotions]
        originalIsBanned.value = emojiDetail.value.is_banned
      }
    } catch (error) {
      console.error('加载表情包详情失败:', error)
      handleClose()
    }
  }
}, { immediate: true })

const handleClose = () => {
  emit('update:modelValue', false)
  emojiDetail.value = null
}

const addEmotion = () => {
  if (newEmotion.value.trim()) {
    editableEmotions.value.push(newEmotion.value.trim())
    newEmotion.value = ''
  }
}

const removeEmotion = (index: number) => {
  editableEmotions.value.splice(index, 1)
}

const handleSave = async () => {
  if (!emojiDetail.value) return

  try {
    // 组装联合格式的描述
    const fullDescription = buildDescription()
    
    await emojiStore.updateEmoji(emojiDetail.value.hash, {
      description: fullDescription,
      emotions: editableEmotions.value,
      is_banned: editableIsBanned.value
    })
    emit('updated')
    handleClose()
  } catch (error) {
    console.error('保存失败:', error)
    await showAlert({
      title: '错误',
      message: '保存失败，请重试',
      type: 'danger'
    })
  }
}

const handleDelete = async () => {
  if (!emojiDetail.value) return
  
  const confirmed = await showConfirm({
    title: '删除表情包',
    message: `确定要删除表情包"${emojiDetail.value.description}"吗？`,
    type: 'danger',
    confirmText: '删除'
  })
  
  if (!confirmed) return

  try {
    await emojiStore.deleteEmoji(emojiDetail.value.hash)
    emit('deleted')
    handleClose()
  } catch (error) {
    console.error('删除失败:', error)
    await showAlert({
      title: '错误',
      message: '删除失败，请重试',
      type: 'danger'
    })
  }
}

const formatTime = (timestamp: number | null) => {
  if (!timestamp) return '未记录'
  return new Date(timestamp * 1000).toLocaleString('zh-CN')
}
</script>

<style scoped>
.dialog-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.6);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  padding: 20px;
}

.dialog-container {
  background: var(--md-sys-color-surface);
  border-radius: 28px;
  width: 100%;
  max-width: 800px;
  max-height: 90vh;
  display: flex;
  flex-direction: column;
  box-shadow: var(--md-sys-elevation-5);
}

.dialog-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 24px;
  border-bottom: 1px solid var(--md-sys-color-outline-variant);
}

.dialog-header h2 {
  font-size: 24px;
  font-weight: 500;
  color: var(--md-sys-color-on-surface);
  margin: 0;
}

.close-button {
  width: 40px;
  height: 40px;
  border: none;
  background: transparent;
  border-radius: 50%;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--md-sys-color-on-surface-variant);
  transition: all 0.2s;
}

.close-button:hover {
  background: var(--md-sys-color-surface-container-highest);
}

.dialog-content {
  flex: 1;
  overflow-y: auto;
  padding: 24px;
}

.full-image-container {
  width: 100%;
  max-height: 300px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--md-sys-color-surface-container);
  border-radius: 16px;
  margin-bottom: 24px;
  padding: 24px;
}

.full-image {
  max-width: 100%;
  max-height: 300px;
  object-fit: contain;
}

.detail-section {
  margin-bottom: 24px;
}

.detail-section h3 {
  font-size: 16px;
  font-weight: 500;
  color: var(--md-sys-color-on-surface);
  margin: 0 0 12px 0;
}

.info-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 16px;
}

.info-item label {
  display: block;
  font-size: 12px;
  color: var(--md-sys-color-on-surface-variant);
  margin-bottom: 4px;
}

.info-item .value {
  font-size: 14px;
  color: var(--md-sys-color-on-surface);
  word-break: break-all;
}

.value.truncate {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.description-input {
  width: 100%;
  padding: 12px;
  border: 1px solid var(--md-sys-color-outline);
  border-radius: 8px;
  background: var(--md-sys-color-surface-container);
  color: var(--md-sys-color-on-surface);
  font-size: 14px;
  font-family: inherit;
  resize: vertical;
}

.emotion-editor {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.emotion-chips {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.emotion-chip {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 6px 12px;
  background: var(--md-sys-color-secondary-container);
  color: var(--md-sys-color-on-secondary-container);
  border-radius: 16px;
  font-size: 14px;
}

.emotion-chip button {
  width: 20px;
  height: 20px;
  border: none;
  background: transparent;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  color: currentColor;
  border-radius: 50%;
  padding: 0;
}

.emotion-chip button:hover {
  background: rgba(0, 0, 0, 0.1);
}

.emotion-chip .material-symbols-rounded {
  font-size: 16px;
}

.add-emotion {
  display: flex;
  gap: 8px;
}

.add-emotion input {
  flex: 1;
  padding: 8px 12px;
  border: 1px solid var(--md-sys-color-outline);
  border-radius: 8px;
  background: var(--md-sys-color-surface-container);
  color: var(--md-sys-color-on-surface);
  font-size: 14px;
}

.add-emotion button {
  width: 40px;
  height: 40px;
  border: none;
  background: var(--md-sys-color-primary);
  color: var(--md-sys-color-on-primary);
  border-radius: 50%;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: 16px;
}

.stat-card {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 16px;
  background: var(--md-sys-color-surface-container);
  border-radius: 12px;
}

.stat-card .material-symbols-rounded {
  font-size: 32px;
  color: var(--md-sys-color-primary);
}

.stat-value {
  font-size: 24px;
  font-weight: 600;
  color: var(--md-sys-color-on-surface);
}

.stat-label {
  font-size: 12px;
  color: var(--md-sys-color-on-surface-variant);
}

.status-controls {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.switch {
  display: flex;
  align-items: center;
  gap: 12px;
  cursor: pointer;
}

.switch input {
  display: none;
}

.slider {
  position: relative;
  width: 52px;
  height: 32px;
  background: var(--md-sys-color-surface-container-highest);
  border-radius: 16px;
  transition: all 0.3s;
}

.slider::before {
  content: '';
  position: absolute;
  width: 24px;
  height: 24px;
  left: 4px;
  top: 4px;
  background: var(--md-sys-color-outline);
  border-radius: 50%;
  transition: all 0.3s;
}

.switch input:checked + .slider {
  background: var(--md-sys-color-primary);
}

.switch input:checked + .slider::before {
  transform: translateX(20px);
  background: var(--md-sys-color-on-primary);
}

.switch .label {
  font-size: 14px;
  color: var(--md-sys-color-on-surface);
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  padding: 24px;
  border-top: 1px solid var(--md-sys-color-outline-variant);
}

.secondary-button,
.danger-button,
.primary-button {
  padding: 10px 24px;
  border: none;
  border-radius: 20px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.secondary-button {
  background: transparent;
  color: var(--md-sys-color-primary);
}

.secondary-button:hover {
  background: var(--md-sys-color-surface-container-highest);
}

.danger-button {
  background: var(--md-sys-color-error);
  color: var(--md-sys-color-on-error);
}

.danger-button:hover {
  background: var(--md-sys-color-error-container);
  color: var(--md-sys-color-on-error-container);
}

.primary-button {
  background: var(--md-sys-color-primary);
  color: var(--md-sys-color-on-primary);
}

.primary-button:hover {
  background: var(--md-sys-color-primary-container);
  color: var(--md-sys-color-on-primary-container);
}

.primary-button:disabled {
  background: var(--md-sys-color-surface-container-highest);
  color: var(--md-sys-color-on-surface-variant);
  cursor: not-allowed;
  opacity: 0.5;
}

/* 对话框动画 */
.dialog-enter-active,
.dialog-leave-active {
  transition: opacity 0.3s;
}

.dialog-enter-active .dialog-container,
.dialog-leave-active .dialog-container {
  transition: transform 0.3s, opacity 0.3s;
}

.dialog-enter-from,
.dialog-leave-to {
  opacity: 0;
}

.dialog-enter-from .dialog-container,
.dialog-leave-to .dialog-container {
  transform: scale(0.9);
  opacity: 0;
}

@media (max-width: 768px) {
  .dialog-container {
    max-height: 95vh;
  }

  .info-grid,
  .stats-grid {
    grid-template-columns: 1fr;
  }
}
</style>
