<!--
  @file SelectEditor.vue
  @description 下拉选择编辑器组件 - Material Design 3 风格
-->
<template>
  <div class="select-editor" :class="{ 'is-focused': isFocused, 'has-value': hasValue, 'is-open': isOpen }" ref="editorRef">
    <div 
      class="field-wrapper"
      @click="toggleDropdown"
      tabindex="0"
      @focus="isFocused = true"
      @blur="handleBlur"
      @keydown.space.prevent="toggleDropdown"
      @keydown.enter.prevent="toggleDropdown"
      @keydown.esc="closeDropdown"
    >
      <div class="select-display">
        <span v-if="hasValue" class="selected-text">{{ selectedLabel }}</span>
        <span v-else class="placeholder-text">{{ field.placeholder || '请选择' }}</span>
      </div>
      
      <span class="select-arrow material-symbols-rounded">expand_more</span>
      
      <div class="field-decoration">
        <div class="field-border"></div>
        <div class="field-focus-indicator"></div>
      </div>
    </div>

    <!-- 自定义下拉菜单 -->
    <Teleport to="body">
      <Transition name="dropdown">
        <div 
          v-if="isOpen" 
          class="select-dropdown"
          :style="dropdownStyle"
        >
          <div class="dropdown-content">
            <div 
              v-for="choice in normalizedChoices" 
              :key="String(choice.value)"
              class="dropdown-item"
              :class="{ 'is-selected': choice.value === modelValue }"
              @click.stop="selectOption(choice.value)"
            >
              <span class="item-label">{{ choice.label }}</span>
              <span v-if="choice.value === modelValue" class="material-symbols-rounded item-check">check</span>
            </div>
            <div v-if="normalizedChoices.length === 0" class="dropdown-empty">
              无选项
            </div>
          </div>
        </div>
      </Transition>
    </Teleport>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, nextTick } from 'vue'
import type { SchemaField } from '@/api/pluginConfig'

const props = defineProps<{
  field: SchemaField
  modelValue: unknown
}>()

const emit = defineEmits<{
  (e: 'update:modelValue', value: unknown): void
}>()

const isFocused = ref(false)
const isOpen = ref(false)
const editorRef = ref<HTMLElement | null>(null)
const dropdownStyle = ref({
  top: '0px',
  left: '0px',
  width: '0px'
})

const hasValue = computed(() => {
  return props.modelValue !== undefined && props.modelValue !== null && props.modelValue !== ''
})

// 标准化选项格式
const normalizedChoices = computed(() => {
  if (!props.field.choices) return []
  return props.field.choices.map(choice => {
    if (typeof choice === 'object' && choice !== null && 'value' in choice) {
      return choice as { value: unknown, label: string }
    }
    return { value: choice, label: String(choice) }
  })
})

const selectedLabel = computed(() => {
  const found = normalizedChoices.value.find(c => c.value === props.modelValue)
  return found?.label || String(props.modelValue)
})

function updateDropdownPosition() {
  if (!editorRef.value) return
  const wrapper = editorRef.value.querySelector('.field-wrapper')
  if (!wrapper) return
  
  const rect = wrapper.getBoundingClientRect()
  dropdownStyle.value = {
    top: `${rect.bottom + 4}px`,
    left: `${rect.left}px`,
    width: `${rect.width}px`
  }
}

function toggleDropdown() {
  if (props.field.disabled) return
  isOpen.value = !isOpen.value
  isFocused.value = isOpen.value
  
  if (isOpen.value) {
    nextTick(() => {
      updateDropdownPosition()
      window.addEventListener('scroll', updateDropdownPosition, true)
      window.addEventListener('resize', updateDropdownPosition)
    })
  } else {
    window.removeEventListener('scroll', updateDropdownPosition, true)
    window.removeEventListener('resize', updateDropdownPosition)
  }
}

function closeDropdown() {
  isOpen.value = false
  isFocused.value = false
  window.removeEventListener('scroll', updateDropdownPosition, true)
  window.removeEventListener('resize', updateDropdownPosition)
}

function handleBlur(_e: FocusEvent) {
  // 延迟关闭以允许点击事件触发
  setTimeout(() => {
    closeDropdown()
  }, 200)
}

function selectOption(value: unknown) {
  emit('update:modelValue', value)
  closeDropdown()
}

// 点击外部关闭
function handleClickOutside(event: MouseEvent) {
  // 检查点击是否在编辑器内部或者下拉菜单内部
  // 由于下拉菜单被 Teleport 到了 body，所以需要额外检查
  const target = event.target as HTMLElement
  const dropdown = document.querySelector('.select-dropdown')
  
  if (editorRef.value && !editorRef.value.contains(target) && 
      dropdown && !dropdown.contains(target)) {
    closeDropdown()
  }
}

onMounted(() => {
  document.addEventListener('click', handleClickOutside)
})

onUnmounted(() => {
  document.removeEventListener('click', handleClickOutside)
  window.removeEventListener('scroll', updateDropdownPosition, true)
  window.removeEventListener('resize', updateDropdownPosition)
})
</script>

<style scoped>
.select-editor {
  position: relative;
  width: 100%;
  display: flex;
  flex-direction: column;
  gap: 8px;
  z-index: 1;
}

.field-wrapper {
  position: relative;
  display: flex;
  align-items: center;
  height: 56px;
  padding: 0 16px;
  background: var(--md-sys-color-surface-container-highest);
  border-radius: 16px;
  cursor: pointer;
  transition: background 0.2s cubic-bezier(0.4, 0, 0.2, 1), outline 0.2s;
  outline: 2px solid transparent;
  outline-offset: -2px;
}

.field-wrapper:hover {
  background: color-mix(in srgb, var(--md-sys-color-on-surface) 8%, var(--md-sys-color-surface-container-highest));
}

.select-editor.is-focused .field-wrapper {
  outline-color: var(--md-sys-color-primary);
}

.select-display {
  flex: 1;
  display: flex;
  align-items: center;
  overflow: hidden;
}

.selected-text {
  color: var(--md-sys-color-on-surface);
  font-size: 1rem;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.placeholder-text {
  color: var(--md-sys-color-on-surface-variant);
  font-size: 1rem;
}

.select-arrow {
  font-size: 24px;
  color: var(--md-sys-color-on-surface-variant);
  transition: transform 0.2s cubic-bezier(0.4, 0, 0.2, 1), color 0.2s;
}

.select-editor.is-focused .select-arrow {
  transform: rotate(180deg);
  color: var(--md-sys-color-primary);
}

.field-decoration {
  display: none;
}
</style>

<style>
.select-dropdown {
  position: absolute;
  z-index: 9999;
  background: var(--md-sys-color-surface-container);
  border-radius: 4px;
  box-shadow: 0 2px 6px 2px rgba(0, 0, 0, 0.15), 0 1px 2px 0 rgba(0, 0, 0, 0.3);
  overflow: hidden;
  transform-origin: top left;
  margin-top: 4px;
}

.dropdown-enter-active,
.dropdown-leave-active {
  transition: opacity 0.2s, transform 0.2s;
}

.dropdown-enter-from,
.dropdown-leave-to {
  opacity: 0;
  transform: scaleY(0.8);
}

.dropdown-content {
  max-height: 300px;
  overflow-y: auto;
  padding: 4px 0;
}

.dropdown-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: 48px;
  padding: 0 16px;
  cursor: pointer;
  color: var(--md-sys-color-on-surface);
  transition: background 0.2s;
}

.dropdown-item:hover {
  background: var(--md-sys-color-surface-container-high);
}

.dropdown-item.is-selected {
  background: var(--md-sys-color-secondary-container);
  color: var(--md-sys-color-on-secondary-container);
}

.item-check {
  font-size: 20px;
}

.dropdown-empty {
  padding: 16px;
  text-align: center;
  color: var(--md-sys-color-on-surface-variant);
}
</style>
