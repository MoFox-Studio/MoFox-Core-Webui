<!--
  @file SchemaConfigEditor.vue
  @description Schema 驱动的插件配置编辑器
  
  功能说明
  1. 根据插件 Schema 自动生成配置表单
  2. 支持 Section 分组�?Tab 布局
  3. 支持条件显示（depends_on�?
  4. 支持保存、重置、备份恢�?
  
  使用方式
  <SchemaConfigEditor :plugin-name="pluginName" />
-->
<template>
  <div class="schema-config-editor">
    <!-- 加载状�?-->
    <div v-if="loading" class="loading-state">
      <span class="material-symbols-rounded spinning">progress_activity</span>
      <p>加载配置�?..</p>
    </div>

    <!-- 错误状�?-->
    <div v-else-if="error" class="error-state">
      <span class="material-symbols-rounded error-icon">error</span>
      <p>{{ error }}</p>
      <button class="m3-button text" @click="loadData">
        <span class="material-symbols-rounded">refresh</span>
        重试
      </button>
    </div>

    <!-- �?Schema 状�?-->
    <div v-else-if="!hasSchema" class="empty-state">
      <span class="material-symbols-rounded empty-icon">description</span>
      <p>该插件没有定义配�?Schema</p>
      <p class="hint">可以切换到源码模式直接编�?TOML 文件</p>
    </div>

    <!-- 配置表单 -->
    <template v-else>
      <!-- Tab 布局 -->
      <div v-if="layout?.type === 'tabs' && layout.tabs" class="tabs-layout">
        <div class="tab-nav">
          <button
            v-for="tab in layout.tabs"
            :key="tab.id"
            class="tab-button"
            :class="{ active: activeTab === tab.id }"
            @click="activeTab = tab.id"
          >
            <span v-if="tab.icon" class="material-symbols-rounded">{{ tab.icon }}</span>
            {{ tab.title }}
            <span v-if="tab.badge" class="tab-badge">{{ tab.badge }}</span>
          </button>
        </div>
        <div class="tab-content">
          <template v-for="tab in layout.tabs" :key="tab.id">
            <div v-show="activeTab === tab.id" class="tab-panel">
              <template v-for="sectionName in tab.sections" :key="sectionName">
                <ConfigSection
                  v-if="schema[sectionName]"
                  :section="getSectionMeta(sectionName)"
                  :fields="schema[sectionName]"
                  :values="configValues"
                  @update="handleFieldUpdate"
                />
              </template>
            </div>
          </template>
        </div>
      </div>

      <!-- Section 布局（默认） -->
      <div v-else class="sections-layout">
        <div class="sections-nav" v-if="Object.keys(schema).length > 1">
          <button
            v-for="sectionMeta in sections"
            :key="sectionMeta.name"
            class="section-nav-item"
            :class="{ active: activeSection === sectionMeta.name }"
            @click="activeSection = sectionMeta.name"
          >
            <span v-if="sectionMeta.icon" class="material-symbols-rounded">{{ sectionMeta.icon }}</span>
            {{ sectionMeta.title }}
            <span class="field-count">{{ schema[sectionMeta.name]?.length || 0 }}</span>
          </button>
        </div>

        <div class="sections-content">
          <template v-for="sectionMeta in sections" :key="sectionMeta.name">
            <ConfigSection
              v-show="activeSection === sectionMeta.name || Object.keys(schema).length === 1"
              :section="sectionMeta"
              :fields="schema[sectionMeta.name] || []"
              :values="configValues"
              @update="handleFieldUpdate"
            />
          </template>
        </div>
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import ConfigSection from './ConfigSection.vue'
import {
  getPluginSchema,
  getPluginConfigContent,
  type SchemaField,
  type SectionMeta,
  type LayoutConfig,
} from '@/api/pluginConfigApi'

const props = defineProps<{
  pluginName: string
}>()

const emit = defineEmits<{
  (e: 'update', values: Record<string, Record<string, unknown>>): void
  (e: 'change', hasChanges: boolean): void
}>()

// 状�?
const loading = ref(true)
const error = ref('')
const schema = ref<Record<string, SchemaField[]>>({})
const sections = ref<SectionMeta[]>([])
const layout = ref<LayoutConfig | null>(null)
const configValues = ref<Record<string, Record<string, unknown>>>({})
const originalValues = ref<Record<string, Record<string, unknown>>>({})

// 当前激活的 Tab/Section
const activeTab = ref('')
const activeSection = ref('')

// 是否�?Schema
const hasSchema = computed(() => Object.keys(schema.value).length > 0)

// 是否有更�?
const hasChanges = computed(() => {
  return JSON.stringify(configValues.value) !== JSON.stringify(originalValues.value)
})

// 监听变化
watch(hasChanges, (value) => {
  emit('change', value)
})

// 获取 Section 元数�?
function getSectionMeta(name: string): SectionMeta {
  return sections.value.find(s => s.name === name) || {
    name,
    title: name.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())
  }
}

// 加载数据
async function loadData() {
  loading.value = true
  error.value = ''

  try {
    // 并行加载 Schema 和配置内�?
    const [schemaRes, contentRes] = await Promise.all([
      getPluginSchema(props.pluginName),
      getPluginConfigContent(props.pluginName),
    ])

    // 处理 Schema
    if (schemaRes.success && schemaRes.data) {
      schema.value = schemaRes.data.schema || {}
      sections.value = schemaRes.data.sections || []
      layout.value = schemaRes.data.layout || null

      // 设置默认激活的 Tab/Section
      if (layout.value?.tabs?.length) {
        activeTab.value = layout.value.tabs[0]?.id || ''
      }
      if (sections.value.length) {
        activeSection.value = sections.value[0]?.name || ''
      }
    } else {
      error.value = schemaRes.data?.error || schemaRes.error || '获取 Schema 失败'
      return
    }

    // 处理配置内容
    if (contentRes.success && contentRes.data?.parsed) {
      configValues.value = contentRes.data.parsed as Record<string, Record<string, unknown>>
      originalValues.value = JSON.parse(JSON.stringify(contentRes.data.parsed))
    } else {
      // 使用 Schema 默认�?
      configValues.value = getDefaultValues()
      originalValues.value = JSON.parse(JSON.stringify(configValues.value))
    }
  } catch (e) {
    error.value = e instanceof Error ? e.message : '加载失败'
  } finally {
    loading.value = false
  }
}

// �?Schema 获取默认�?
function getDefaultValues(): Record<string, Record<string, unknown>> {
  const defaults: Record<string, Record<string, unknown>> = {}
  
  for (const [sectionName, fields] of Object.entries(schema.value)) {
    defaults[sectionName] = {}
    for (const field of fields) {
      defaults[sectionName][field.key] = field.default
    }
  }
  
  return defaults
}

// 处理字段更新
function handleFieldUpdate(section: string, key: string, value: unknown) {
  if (!configValues.value[section]) {
    configValues.value[section] = {}
  }
  configValues.value[section][key] = value
  emit('update', configValues.value)
}

// 重置为原始�?
function reset() {
  configValues.value = JSON.parse(JSON.stringify(originalValues.value))
}

// 重置为默认�?
function resetToDefaults() {
  configValues.value = getDefaultValues()
}

// 获取当前配置�?
function getValues(): Record<string, Record<string, unknown>> {
  return configValues.value
}

// 暴露方法
defineExpose({
  reset,
  resetToDefaults,
  getValues,
  hasChanges,
  reload: loadData,
})

// 初始�?
onMounted(() => {
  loadData()
})

// 监听插件名变�?
watch(() => props.pluginName, () => {
  loadData()
})
</script>

<style scoped>
.schema-config-editor {
  display: flex;
  flex-direction: column;
  gap: 16px;
  height: 100%;
}

/* 加载和错误状�?*/
.loading-state,
.error-state,
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 48px;
  gap: 16px;
  color: var(--md-sys-color-on-surface-variant);
  height: 100%;
}

.loading-state .spinning {
  font-size: 40px;
  animation: spin 1s linear infinite;
  color: var(--md-sys-color-primary);
}

.error-state .error-icon {
  font-size: 48px;
  color: var(--md-sys-color-error);
}

.empty-state .empty-icon {
  font-size: 48px;
  opacity: 0.5;
}

.empty-state .hint {
  font-size: 14px;
  opacity: 0.7;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

/* Tab 布局 */
.tabs-layout {
  display: flex;
  flex-direction: column;
  height: 100%;
  gap: 16px;
}

.tab-nav {
  display: flex;
  gap: 8px;
  padding: 8px;
  background: var(--md-sys-color-surface-container);
  border-radius: 16px;
  overflow-x: auto;
  flex-shrink: 0;
}

.tab-button {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 20px;
  background: transparent;
  border: none;
  border-radius: 12px;
  font-size: 14px;
  font-weight: 500;
  color: var(--md-sys-color-on-surface-variant);
  cursor: pointer;
  white-space: nowrap;
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
  position: relative;
  overflow: hidden;
}

.tab-button:hover {
  background: var(--md-sys-color-surface-container-high);
  color: var(--md-sys-color-on-surface);
}

.tab-button.active {
  background: var(--md-sys-color-secondary-container);
  color: var(--md-sys-color-on-secondary-container);
  font-weight: 600;
}

.tab-badge {
  padding: 2px 6px;
  background: var(--md-sys-color-error-container);
  color: var(--md-sys-color-on-error-container);
  border-radius: 10px;
  font-size: 11px;
  font-weight: 700;
}

.tab-content {
  flex: 1;
  overflow-y: auto;
  padding-right: 8px; /* Space for scrollbar */
}

.tab-panel {
  display: flex;
  flex-direction: column;
  gap: 24px;
  padding-bottom: 24px;
}

/* Section 布局 */
.sections-layout {
  display: flex;
  gap: 24px;
  height: 100%;
}

.sections-nav {
  display: flex;
  flex-direction: column;
  gap: 4px;
  min-width: 240px;
  max-width: 300px;
  padding: 12px;
  background: var(--md-sys-color-surface-container);
  border-radius: 16px;
  height: fit-content;
  max-height: 100%;
  overflow-y: auto;
}

.section-nav-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  background: transparent;
  border: none;
  border-radius: 28px; /* Pill shape */
  font-size: 14px;
  font-weight: 500;
  color: var(--md-sys-color-on-surface-variant);
  cursor: pointer;
  text-align: left;
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
}

.section-nav-item:hover {
  background: var(--md-sys-color-surface-container-high);
  color: var(--md-sys-color-on-surface);
}

.section-nav-item.active {
  background: var(--md-sys-color-secondary-container);
  color: var(--md-sys-color-on-secondary-container);
  font-weight: 600;
}

.field-count {
  margin-left: auto;
  padding: 2px 8px;
  background: var(--md-sys-color-surface-container-highest);
  border-radius: 12px;
  font-size: 11px;
  color: var(--md-sys-color-on-surface-variant);
}

.section-nav-item.active .field-count {
  background: var(--md-sys-color-on-secondary-container);
  color: var(--md-sys-color-secondary-container);
}

.sections-content {
  flex: 1;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 24px;
  padding-right: 8px;
  padding-bottom: 24px;
}

/* 按钮 */
.m3-button {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 10px 24px;
  font-size: 14px;
  font-weight: 500;
  border: none;
  border-radius: 20px;
  cursor: pointer;
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
}

.m3-button.text {
  background: transparent;
  color: var(--md-sys-color-primary);
}

.m3-button.text:hover {
  background: var(--md-sys-color-primary-container);
  color: var(--md-sys-color-on-primary-container);
}
</style>
