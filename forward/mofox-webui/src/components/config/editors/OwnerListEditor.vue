<template>
  <div class="owner-list-editor">
    <!-- 标题区 -->
    <div class="editor-header">
      <div class="header-title">
        <Icon icon="lucide:shield-check" />
        <h4>{{ title ?? '所有者列表' }}</h4>
      </div>
      <p class="editor-hint">
        {{ description ?? 'Bot 所有者，格式：platform:user_id（如 qq:123456）' }}
      </p>
    </div>

    <!-- 条目列表 -->
    <div class="owner-items">
      <div
        v-for="(entry, index) in parsed"
        :key="index"
        class="owner-item"
      >
        <!-- Platform 选择 -->
        <div
          class="platform-select"
          :class="{ 'is-open': openPlatformIdx === index }"
          @click="openPlatformIdx = openPlatformIdx === index ? -1 : index"
        >
          <span class="platform-label">{{ entry.platform || '平台' }}</span>
          <Icon icon="lucide:chevron-down" class="chevron" />

          <transition name="drop">
            <div v-if="openPlatformIdx === index" class="platform-dropdown">
              <div
                v-for="p in PLATFORMS"
                :key="p"
                class="platform-option"
                :class="{ active: entry.platform === p }"
                @click.stop="selectPlatform(index, p)"
              >
                {{ p }}
                <Icon v-if="entry.platform === p" icon="lucide:check" />
              </div>
            </div>
          </transition>
        </div>


        <!-- User ID 输入 -->
        <input
          class="input uid-input"
          type="text"
          placeholder="user_id"
          :value="entry.uid"
          @input="updateUid(index, ($event.target as HTMLInputElement).value)"
        />

        <!-- 删除按钮 -->
        <button type="button" class="btn-icon delete-btn" @click="removeEntry(index)" title="删除">
          <Icon icon="lucide:trash-2" />
        </button>
      </div>

      <div v-if="parsed.length === 0" class="empty-state">
        <Icon icon="lucide:inbox" />
        <p>暂无所有者</p>
      </div>
    </div>

    <!-- 添加按钮 -->
    <button type="button" class="add-btn" @click="addEntry">
      <Icon icon="lucide:plus" />
      添加所有者
    </button>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import { Icon } from '@iconify/vue'

interface OwnerEntry {
  platform: string
  uid: string
}

const PLATFORMS = ['qq', 'discord', 'telegram', 'wechat', 'slack', 'custom']

const props = defineProps<{
  value: unknown
  title?: string
  description?: string
}>()

const emit = defineEmits<{
  (e: 'update', value: string[]): void
}>()

const openPlatformIdx = ref(-1)

// 解析 "platform:uid" 字符串数组 → 结构化对象数组
const parsed = computed<OwnerEntry[]>(() => {
  const arr = Array.isArray(props.value) ? props.value : []
  return arr.map((item: unknown) => {
    const s = String(item ?? '')
    const colonIdx = s.indexOf(':')
    if (colonIdx === -1) return { platform: 'qq', uid: s }
    return { platform: s.slice(0, colonIdx), uid: s.slice(colonIdx + 1) }
  })
})

function emit_update(entries: OwnerEntry[]) {
  emit('update', entries.map(e => `${e.platform}:${e.uid}`))
}

function addEntry() {
  emit_update([...parsed.value, { platform: 'qq', uid: '' }])
}

function removeEntry(index: number) {
  const next = parsed.value.filter((_, i) => i !== index)
  emit_update(next)
}

function selectPlatform(index: number, platform: string) {
  openPlatformIdx.value = -1
  const next = parsed.value.map((e, i) => i === index ? { ...e, platform } : e)
  emit_update(next)
}

function updateUid(index: number, uid: string) {
  const next = parsed.value.map((e, i) => i === index ? { ...e, uid } : e)
  emit_update(next)
}
</script>

<style scoped>
.owner-list-editor {
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding: 16px;
  background: var(--bg-secondary);
  border: 1px solid var(--border-color);
  border-radius: var(--radius);
}

/* 标题 */
.editor-header {
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.header-title {
  display: flex;
  align-items: center;
  gap: 8px;
}
.header-title h4 {
  margin: 0;
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary);
}
.header-title svg {
  color: var(--primary);
}
.editor-hint {
  margin: 0;
  font-size: 12px;
  color: var(--text-tertiary);
}

/* 条目列表 */
.owner-items {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.owner-item {
  display: flex;
  align-items: center;
  gap: 8px;
}

/* Platform 选择器 */
.platform-select {
  position: relative;
  min-width: 100px;
  height: 34px;
  padding: 0 10px;
  background: var(--bg-primary);
  border: 1px solid var(--border-color);
  border-radius: var(--radius);
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 6px;
  cursor: pointer;
  user-select: none;
  transition: border-color var(--transition-fast);
  flex-shrink: 0;
}
.platform-select:hover,
.platform-select.is-open {
  border-color: var(--primary);
}
.platform-label {
  font-size: 13px;
  color: var(--text-primary);
  font-family: 'Roboto Mono', monospace;
}
.chevron {
  font-size: 12px;
  color: var(--text-tertiary);
  transition: transform var(--transition-fast);
}
.platform-select.is-open .chevron {
  transform: rotate(180deg);
}

/* 下拉列表 */
.platform-dropdown {
  position: absolute;
  top: calc(100% + 4px);
  left: 0;
  min-width: 120px;
  background: var(--bg-overlay, var(--bg-primary));
  border: 1px solid var(--border-color);
  border-radius: var(--radius);
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.2);
  z-index: 100;
  overflow: hidden;
}
.platform-option {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 12px;
  font-size: 13px;
  color: var(--text-primary);
  font-family: 'Roboto Mono', monospace;
  cursor: pointer;
  transition: background var(--transition-fast);
}
.platform-option:hover {
  background: var(--bg-secondary);
}
.platform-option.active {
  color: var(--primary);
}

/* 冒号分隔符 */
.colon {
  font-size: 16px;
  font-weight: 600;
  color: var(--text-tertiary);
  flex-shrink: 0;
}

/* UID 输入 */
.uid-input {
  flex: 1;
  height: 34px;
  padding: 0 12px;
  background: var(--bg-primary);
  border: 1px solid var(--border-color);
  border-radius: var(--radius);
  color: var(--text-primary);
  font-family: 'Roboto Mono', monospace;
  font-size: 13px;
  transition: border-color var(--transition-fast);
}
.uid-input:focus {
  border-color: var(--primary);
  outline: none;
}

/* 删除按钮 */
.delete-btn {
  padding: 6px;
  background: transparent;
  border: none;
  color: var(--text-tertiary);
  cursor: pointer;
  border-radius: var(--radius);
  transition: all var(--transition-fast);
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
}
.delete-btn:hover {
  background: var(--danger-bg);
  color: var(--danger);
}

/* 空状态 */
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  padding: 20px;
  color: var(--text-tertiary);
  font-size: 13px;
}
.empty-state p {
  margin: 0;
}

/* 添加按钮 */
.add-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 10px 16px;
  background: var(--bg-secondary);
  border: 1px dashed var(--border-color);
  border-radius: var(--radius);
  color: var(--text-secondary);
  font-size: 13px;
  cursor: pointer;
  transition: all var(--transition-fast);
}
.add-btn:hover {
  border-color: var(--primary);
  color: var(--primary);
  background: var(--primary-bg);
}

/* 下拉动画 */
.drop-enter-active,
.drop-leave-active {
  transition: opacity var(--transition-fast), transform var(--transition-fast);
}
.drop-enter-from,
.drop-leave-to {
  opacity: 0;
  transform: translateY(-4px);
}
</style>
