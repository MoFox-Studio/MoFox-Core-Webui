<template>
  <div class="master-users-editor">
    <div class="editor-header">
      <h4>
        <Icon icon="lucide:crown" />
        主人用户配置
      </h4>
      <p class="editor-hint">配置拥有最高权限的用户，格式为 [平台, 用户ID]</p>
    </div>
    
    <div class="users-list">
      <div 
        v-for="(user, index) in users" 
        :key="index" 
        class="user-item"
      >
        <div class="user-inputs">
          <div 
            class="custom-select-wrapper" 
            :ref="el => dropdownRefs[index] = el as HTMLElement"
          >
            <div 
              class="custom-select-trigger input" 
              :class="{ active: openDropdownIndex === index }"
              @click.stop="toggleDropdown(index)"
            >
              <span>{{ platforms.find(p => p.value === user[0])?.label || user[0] }}</span>
              <Icon icon="lucide:chevron-down" class="select-arrow" :class="{ rotated: openDropdownIndex === index }" />
            </div>
            
            <Transition name="fade">
              <div v-if="openDropdownIndex === index" class="custom-select-dropdown">
                <div 
                  v-for="platform in platforms" 
                  :key="platform.value"
                  class="custom-select-option"
                  :class="{ selected: user[0] === platform.value }"
                  @click.stop="selectPlatform(index, platform.value)"
                >
                  <span>{{ platform.label }}</span>
                  <Icon v-if="user[0] === platform.value" icon="lucide:check" class="check-icon" />
                </div>
              </div>
            </Transition>
          </div>

          <input 
            type="text" 
            class="input user-id-input"
            :value="user[1]"
            @input="updateUser(index, 1, ($event.target as HTMLInputElement).value)"
            placeholder="用户ID"
          />
        </div>
        <button class="btn-icon delete-btn" @click="removeUser(index)" title="删除">
          <Icon icon="lucide:trash-2" />
        </button>
      </div>
      
      <div v-if="users.length === 0" class="empty-state">
        <Icon icon="lucide:user-x" />
        <p>暂无主人用户</p>
      </div>
    </div>
    
    <button class="btn btn-outline add-btn" @click="addUser">
      <Icon icon="lucide:plus" />
      添加主人用户
    </button>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, onMounted, onUnmounted } from 'vue'
import { Icon } from '@iconify/vue'

const props = defineProps<{
  value: unknown
}>()

const emit = defineEmits<{
  (e: 'update', value: string[][]): void
}>()

const platforms = [
  { value: 'qq', label: 'QQ' },
  { value: 'telegram', label: 'Telegram' },
  { value: 'discord', label: 'Discord' }
]

const openDropdownIndex = ref<number>(-1)
const dropdownRefs = ref<(HTMLElement | null)[]>([])

function toggleDropdown(index: number) {
  if (openDropdownIndex.value === index) {
    openDropdownIndex.value = -1
  } else {
    openDropdownIndex.value = index
  }
}

function selectPlatform(index: number, platform: string) {
  updateUser(index, 0, platform)
  openDropdownIndex.value = -1
}

function handleClickOutside(event: MouseEvent) {
  if (openDropdownIndex.value !== -1) {
    const activeDropdown = dropdownRefs.value[openDropdownIndex.value]
    if (activeDropdown && !activeDropdown.contains(event.target as Node)) {
      openDropdownIndex.value = -1
    }
  }
}

onMounted(() => {
  document.addEventListener('click', handleClickOutside)
})

onUnmounted(() => {
  document.removeEventListener('click', handleClickOutside)
})

// 解析用户列表
const users = computed(() => {
  if (Array.isArray(props.value)) {
    return props.value.filter(item => Array.isArray(item) && item.length === 2) as string[][]
  }
  return []
})

// 添加用户
function addUser() {
  const newUsers = [...users.value, ['qq', '']]
  emit('update', newUsers)
}

// 删除用户
function removeUser(index: number) {
  const newUsers = users.value.filter((_, i) => i !== index)
  emit('update', newUsers)
}

// 更新用户
function updateUser(index: number, field: number, value: string) {
  const newUsers = users.value.map((user, i) => {
    if (i === index) {
      const newUser = [...user]
      newUser[field] = value
      return newUser
    }
    return user
  })
  emit('update', newUsers)
}
</script>

<style scoped>
.master-users-editor {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.editor-header h4 {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0 0 4px 0;
}

.editor-header h4 svg {
  color: #f59e0b;
}

.editor-hint {
  font-size: 12px;
  color: var(--text-tertiary);
  margin: 0;
}

.users-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.user-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  background: var(--bg-secondary);
  border-radius: var(--radius);
  border: 1px solid var(--border-color);
}

.user-inputs {
  display: flex;
  flex: 1;
  gap: 8px;
}

.custom-select-wrapper {
  position: relative;
  width: 140px;
}

.custom-select-trigger {
  display: flex;
  align-items: center;
  justify-content: space-between;
  cursor: pointer;
  user-select: none;
  height: 34px; /* Match input height */
}

.custom-select-trigger.active {
  border-color: var(--primary);
  background: var(--bg-secondary);
}

.select-arrow {
  font-size: 16px;
  color: var(--text-tertiary);
  transition: transform 0.2s;
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

.user-id-input {
  flex: 1;
  height: 34px;
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
  font-size: 13px;
}

.input:focus {
  border-color: var(--primary);
  outline: none;
}

.delete-btn {
  padding: 6px;
  background: transparent;
  border: none;
  color: var(--text-tertiary);
  cursor: pointer;
  border-radius: var(--radius);
  transition: all var(--transition-fast);
}

.delete-btn:hover {
  background: var(--danger-bg);
  color: var(--danger);
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  padding: 24px;
  color: var(--text-tertiary);
}

.empty-state svg {
  font-size: 24px;
}

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
</style>
