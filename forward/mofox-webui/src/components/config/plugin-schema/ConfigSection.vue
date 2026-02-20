<!--
  @file ConfigSection.vue
  @description 配置 Section 组件（新 API）

  功能说明:
  1. 显示 Section 标题、描述
  2. 渲染 Section 下的所有字段
  3. 支持展开/折叠
-->
<template>
  <div class="config-section" :class="{ collapsed: isCollapsed }">
    <!-- Section 头部 -->
    <div class="section-header" @click="toggleCollapse">
      <div class="header-left">
        <span class="section-icon material-symbols-rounded">{{ sectionIcon }}</span>
        <div class="header-text">
          <h3 class="section-title">{{ section.name || formatTitle(section.key) }}</h3>
          <p v-if="section.description" class="section-description">
            {{ section.description }}
          </p>
        </div>
      </div>
      <button class="collapse-toggle" :aria-label="isCollapsed ? '展开' : '折叠'">
        <span class="material-symbols-rounded">
          {{ isCollapsed ? 'expand_more' : 'expand_less' }}
        </span>
      </button>
    </div>

    <!-- Section 内容 -->
    <div class="section-content" v-show="!isCollapsed">
      <template v-for="field in section.fields" :key="field.key">
        <SchemaFieldEditor
          :field="field"
          :model-value="getFieldValue(field.key)"
          @update:model-value="(v: unknown) => updateField(field.key, v)"
        />
      </template>

      <!-- 空状态 -->
      <div v-if="section.fields.length === 0" class="empty-section">
        <span class="material-symbols-rounded">inbox</span>
        <p>该分组没有可显示的配置项</p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import SchemaFieldEditor from './SchemaFieldEditor.vue'
import type { PluginSchemaSection } from '@/api/pluginConfig'

const props = defineProps<{
  section: PluginSchemaSection
  /** 该 section 的值对象 { fieldName: value } */
  values: Record<string, unknown>
}>()

const emit = defineEmits<{
  (e: 'update', key: string, value: unknown): void
}>()

// 折叠状态
const isCollapsed = ref(false)

// section 图标
const sectionIcon = computed(() => {
  const icons: Record<string, string> = {
    database: 'database',
    api: 'cloud',
    personality: 'psychology',
    permission: 'lock',
    feature: 'toggle_on',
    bot: 'smart_toy',
    system: 'settings',
    ui: 'palette',
  }
  const key = props.section.key.toLowerCase()
  for (const [k, icon] of Object.entries(icons)) {
    if (key.includes(k)) return icon
  }
  return 'folder'
})

// 获取字段值（field.key 格式为 "section.fieldName"，只取 fieldName）
function getFieldValue(fullKey: string): unknown {
  const dotIdx = fullKey.indexOf('.')
  const fieldName = dotIdx === -1 ? fullKey : fullKey.slice(dotIdx + 1)
  return props.values?.[fieldName]
}

// 更新字段
function updateField(fullKey: string, value: unknown) {
  const dotIdx = fullKey.indexOf('.')
  const fieldName = dotIdx === -1 ? fullKey : fullKey.slice(dotIdx + 1)
  emit('update', fieldName, value)
}

// 格式化标题
function formatTitle(name: string): string {
  return name
    .replace(/_/g, ' ')
    .replace(/\b\w/g, l => l.toUpperCase())
}

// 切换折叠
function toggleCollapse() {
  isCollapsed.value = !isCollapsed.value
}
</script>

<style scoped>
.config-section {
  background: var(--md-sys-color-surface-container);
  border-radius: 24px;
  overflow: hidden;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  border: 1px solid var(--md-sys-color-outline-variant);
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04);
}

.config-section:hover {
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.08);
  border-color: var(--md-sys-color-outline);
}

.config-section.collapsed {
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.04);
}

/* Section 头部 */
.section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 20px 24px;
  cursor: pointer;
  transition: background 0.2s ease;
  background: linear-gradient(135deg, var(--md-sys-color-surface-container) 0%, var(--md-sys-color-surface-container-high) 100%);
  position: relative;
}

.section-header::after {
  content: '';
  position: absolute;
  bottom: 0;
  left: 24px;
  right: 24px;
  height: 1px;
  background: var(--md-sys-color-outline-variant);
  opacity: 0;
  transition: opacity 0.2s;
}

.config-section:not(.collapsed) .section-header::after {
  opacity: 1;
}

.section-header:hover {
  background: linear-gradient(135deg, var(--md-sys-color-surface-container-high) 0%, var(--md-sys-color-surface-container-highest) 100%);
}

.header-left {
  display: flex;
  align-items: center;
  gap: 16px;
}

.section-icon {
  font-size: 24px;
  color: var(--md-sys-color-on-primary-container);
  padding: 12px;
  background: var(--md-sys-color-primary-container);
  border-radius: 16px;
  transition: all 0.2s;
}

.section-header:hover .section-icon {
  background: var(--md-sys-color-primary);
  color: var(--md-sys-color-on-primary);
  transform: scale(1.05);
}

.header-text {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.section-title {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
  color: var(--md-sys-color-on-surface);
  letter-spacing: 0.15px;
}

.section-description {
  margin: 0;
  font-size: 13px;
  color: var(--md-sys-color-on-surface-variant);
  line-height: 18px;
  max-width: 400px;
}

.collapse-toggle {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 44px;
  height: 44px;
  background: var(--md-sys-color-surface-container-highest);
  border: none;
  border-radius: 50%;
  cursor: pointer;
  color: var(--md-sys-color-on-surface-variant);
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
}

.collapse-toggle:hover {
  background: var(--md-sys-color-primary-container);
  color: var(--md-sys-color-on-primary-container);
  transform: scale(1.05);
}

.collapse-toggle .material-symbols-rounded {
  font-size: 24px;
  transition: transform 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.collapsed .collapse-toggle .material-symbols-rounded {
  transform: rotate(0deg);
}

.config-section:not(.collapsed) .collapse-toggle .material-symbols-rounded {
  transform: rotate(180deg);
}

/* Section 内容 */
.section-content {
  padding: 16px 20px 24px;
  display: flex;
  flex-direction: column;
  gap: 8px;
  background: var(--md-sys-color-surface);
  animation: slideDown 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

@keyframes slideDown {
  from {
    opacity: 0;
    transform: translateY(-12px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* 空状态 */
.empty-section {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 48px 32px;
  gap: 12px;
  color: var(--md-sys-color-on-surface-variant);
}

.empty-section .material-symbols-rounded {
  font-size: 48px;
  opacity: 0.3;
}

.empty-section p {
  margin: 0;
  font-size: 14px;
  opacity: 0.7;
}
</style>
