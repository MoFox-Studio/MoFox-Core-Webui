<template>
  <div class="chat-stream-id-input">
    <div class="stream-inputs">
      <div class="custom-select-wrapper" :ref="el => dropdownRef = el as HTMLElement">
        <div 
          class="custom-select-trigger input" 
          :class="{ active: isDropdownOpen }"
          @click.stop="toggleDropdown"
        >
          <span>{{ platforms.find(p => p.value === streamData.platform)?.label || streamData.platform || '选择平台' }}</span>
          <Icon icon="lucide:chevron-down" class="select-arrow" :class="{ rotated: isDropdownOpen }" />
        </div>
        
        <Transition name="fade">
          <div v-if="isDropdownOpen" class="custom-select-dropdown">
            <div 
              v-for="platform in platforms" 
              :key="platform.value"
              class="custom-select-option"
              :class="{ selected: streamData.platform === platform.value }"
              @click.stop="selectPlatform(platform.value)"
            >
              <span>{{ platform.label }}</span>
              <Icon v-if="streamData.platform === platform.value" icon="lucide:check" class="check-icon" />
            </div>
          </div>
        </Transition>
      </div>

      <input 
        type="text" 
        class="input id-input"
        :value="streamData.id"
        @input="updateId(($event.target as HTMLInputElement).value)"
        placeholder="聊天ID"
      />

      <div class="custom-select-wrapper" :ref="el => typeDropdownRef = el as HTMLElement">
        <div 
          class="custom-select-trigger input" 
          :class="{ active: isTypeDropdownOpen }"
          @click.stop="toggleTypeDropdown"
        >
          <span>{{ types.find(t => t.value === streamData.type)?.label || streamData.type || '类型' }}</span>
          <Icon icon="lucide:chevron-down" class="select-arrow" :class="{ rotated: isTypeDropdownOpen }" />
        </div>
        
        <Transition name="fade">
          <div v-if="isTypeDropdownOpen" class="custom-select-dropdown">
            <div 
              v-for="type in types" 
              :key="type.value"
              class="custom-select-option"
              :class="{ selected: streamData.type === type.value }"
              @click.stop="selectType(type.value)"
            >
              <span>{{ type.label }}</span>
              <Icon v-if="streamData.type === type.value" icon="lucide:check" class="check-icon" />
            </div>
          </div>
        </Transition>
      </div>
    </div>

    <div class="hint-text">
      <Icon icon="lucide:info" />
      留空表示全局配置 · 当前: {{ currentStreamId || '全局' }}
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, onMounted, onUnmounted } from 'vue'
import { Icon } from '@iconify/vue'

const props = defineProps<{
  value: string
}>()

const emit = defineEmits<{
  (e: 'update', value: string): void
}>()

const platforms = [
  { value: 'qq', label: 'QQ' },
  { value: 'telegram', label: 'Telegram' },
  { value: 'discord', label: 'Discord' }
]

const types = [
  { value: 'group', label: '群聊' },
  { value: 'private', label: '私聊' }
]

const isDropdownOpen = ref(false)
const isTypeDropdownOpen = ref(false)
const dropdownRef = ref<HTMLElement | null>(null)
const typeDropdownRef = ref<HTMLElement | null>(null)

// 解析聊天流ID: "platform:id:type"
const streamData = computed(() => {
  if (!props.value) {
    return { platform: '', id: '', type: '' }
  }
  const parts = props.value.split(':')
  return {
    platform: parts[0] || '',
    id: parts[1] || '',
    type: parts[2] || ''
  }
})

// 当前完整的聊天流ID
const currentStreamId = computed(() => {
  const { platform, id, type } = streamData.value
  if (!platform || !id || !type) return ''
  return `${platform}:${id}:${type}`
})

function toggleDropdown() {
  isDropdownOpen.value = !isDropdownOpen.value
  if (isDropdownOpen.value) {
    isTypeDropdownOpen.value = false
  }
}

function toggleTypeDropdown() {
  isTypeDropdownOpen.value = !isTypeDropdownOpen.value
  if (isTypeDropdownOpen.value) {
    isDropdownOpen.value = false
  }
}

function selectPlatform(platform: string) {
  const { id, type } = streamData.value
  const newValue = `${platform}:${id}:${type}`
  emit('update', newValue)
  isDropdownOpen.value = false
}

function updateId(id: string) {
  const { platform, type } = streamData.value
  const newValue = `${platform}:${id}:${type}`
  emit('update', newValue)
}

function selectType(type: string) {
  const { platform, id } = streamData.value
  const newValue = `${platform}:${id}:${type}`
  emit('update', newValue)
  isTypeDropdownOpen.value = false
}

function handleClickOutside(event: MouseEvent) {
  if (dropdownRef.value && !dropdownRef.value.contains(event.target as Node)) {
    isDropdownOpen.value = false
  }
  if (typeDropdownRef.value && !typeDropdownRef.value.contains(event.target as Node)) {
    isTypeDropdownOpen.value = false
  }
}

onMounted(() => {
  document.addEventListener('click', handleClickOutside)
})

onUnmounted(() => {
  document.removeEventListener('click', handleClickOutside)
})
</script>

<style scoped>
.chat-stream-id-input {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.stream-inputs {
  display: flex;
  align-items: center;
  gap: 8px;
}

.custom-select-wrapper {
  position: relative;
  width: 120px;
  flex-shrink: 0;
}

.custom-select-trigger {
  display: flex;
  align-items: center;
  justify-content: space-between;
  cursor: pointer;
  user-select: none;
  height: 34px;
}

.custom-select-trigger.active {
  border-color: var(--primary);
  background: var(--bg-secondary);
}

.select-arrow {
  font-size: 16px;
  color: var(--text-tertiary);
  transition: transform 0.2s;
  flex-shrink: 0;
}

.select-arrow.rotated {
  transform: rotate(180deg);
}

.custom-select-dropdown {
  position: absolute;
  top: calc(100% + 4px);
  left: 0;
  width: 100%;
  background: var(--bg-secondary);
  border: 1px solid var(--border-color);
  border-radius: var(--radius);
  padding: 4px;
  z-index: 100;
  box-shadow: var(--shadow-lg);
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.custom-select-option {
  padding: 6px 10px;
  border-radius: 4px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: space-between;
  font-size: 13px;
  color: var(--text-primary);
  transition: background 0.2s;
}

.custom-select-option:hover {
  background: var(--bg-tertiary);
}

.custom-select-option.selected {
  background: var(--primary-bg);
  color: var(--primary);
  font-weight: 500;
}

.check-icon {
  font-size: 14px;
}

.id-input {
  flex: 1;
}

.input {
  padding: 0 12px;
  height: 34px;
  display: flex;
  align-items: center;
  background: var(--bg-primary);
  border: 1px solid var(--border-color);
  border-radius: var(--radius);
  color: var(--text-primary);
  font-family: 'Roboto Mono', 'Noto Sans SC', sans-serif !important;
  font-size: 13px;
  transition: all var(--transition-fast);
}

.input:focus {
  border-color: var(--primary);
  outline: none;
}

.hint-text {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: var(--text-tertiary);
  padding-left: 4px;
}

.hint-text svg {
  font-size: 14px;
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s, transform 0.2s;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
  transform: translateY(-4px);
}
</style>
