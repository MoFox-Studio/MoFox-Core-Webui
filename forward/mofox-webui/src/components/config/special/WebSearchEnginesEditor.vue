<template>
  <div class="web-search-engines-editor">
    <div class="editor-header">
      <h4>
        <Icon icon="lucide:search" />
        搜索引擎配置
      </h4>
      <p class="editor-hint">选择要启用的搜索引擎，启用需要 API 密钥的引擎时会显示对应配置项</p>
    </div>

    <div class="engines-grid">
      <div 
        v-for="engine in availableEngines" 
        :key="engine.id"
        class="engine-card"
        :class="{ 'is-enabled': isEngineEnabled(engine.id) }"
      >
        <div class="engine-header">
          <label class="engine-toggle">
            <input 
              type="checkbox" 
              :checked="isEngineEnabled(engine.id)"
              @change="toggleEngine(engine.id)"
            />
            <span class="toggle-slider"></span>
          </label>
          <div class="engine-info">
            <Icon :icon="engine.icon" class="engine-icon" />
            <span class="engine-name">{{ engine.name }}</span>
          </div>
          <span v-if="engine.needsApiKey" class="api-badge">需要API密钥</span>
          <span v-else class="free-badge">免费</span>
        </div>
        <p class="engine-desc">{{ engine.description }}</p>
        
        <!-- API 密钥配置区域 -->
        <div v-if="isEngineEnabled(engine.id) && engine.needsApiKey" class="api-config">
          <div v-for="field in engine.apiFields" :key="field.key" class="api-field">
            <label class="api-field-label">
              <Icon :icon="field.icon || 'lucide:key'" />
              {{ field.label }}
            </label>
            <div class="api-keys-list">
              <div 
                v-for="(keyValue, index) in getApiKeys(field.key)" 
                :key="index"
                class="api-key-item"
              >
                <input 
                  type="password" 
                  class="input api-key-input"
                  :value="keyValue"
                  :placeholder="field.placeholder"
                  @input="updateApiKey(field.key, index, ($event.target as HTMLInputElement).value)"
                />
                <button class="btn-icon delete-btn" @click="removeApiKey(field.key, index)" title="删除">
                  <Icon icon="lucide:trash-2" />
                </button>
              </div>
              <button class="btn btn-sm btn-outline add-key-btn" @click="addApiKey(field.key)">
                <Icon icon="lucide:plus" />
                添加{{ field.label }}
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { Icon } from '@iconify/vue'

interface ApiField {
  key: string
  label: string
  placeholder: string
  icon?: string
}

interface Engine {
  id: string
  name: string
  icon: string
  description: string
  needsApiKey: boolean
  apiFields?: ApiField[]
}

const props = defineProps<{
  value: unknown
  configData: Record<string, unknown>
}>()

const emit = defineEmits<{
  (e: 'update', value: string[]): void
  (e: 'updateConfig', key: string, value: unknown): void
}>()

// 可用的搜索引擎列表
const availableEngines: Engine[] = [
  {
    id: 'ddg',
    name: 'DuckDuckGo',
    icon: 'simple-icons:duckduckgo',
    description: '免费的隐私优先搜索引擎，无需 API 密钥',
    needsApiKey: false
  },
  {
    id: 'bing',
    name: 'Bing',
    icon: 'logos:bing',
    description: '微软必应搜索，无需 API 密钥',
    needsApiKey: false
  },
  {
    id: 'tavily',
    name: 'Tavily',
    icon: 'lucide:search-code',
    description: '专为 AI 应用优化的搜索引擎，结果精准',
    needsApiKey: true,
    apiFields: [
      {
        key: 'web_search.tavily_api_keys',
        label: 'API 密钥',
        placeholder: '输入 Tavily API 密钥...',
        icon: 'lucide:key'
      }
    ]
  },
  {
    id: 'exa',
    name: 'EXA',
    icon: 'lucide:brain',
    description: '神经网络驱动的智能搜索引擎',
    needsApiKey: true,
    apiFields: [
      {
        key: 'web_search.exa_api_keys',
        label: 'API 密钥',
        placeholder: '输入 EXA API 密钥...',
        icon: 'lucide:key'
      }
    ]
  },
  {
    id: 'metaso',
    name: 'Metaso',
    icon: 'lucide:sparkles',
    description: '秘塔AI搜索引擎，支持中文搜索',
    needsApiKey: true,
    apiFields: [
      {
        key: 'web_search.metaso_api_keys',
        label: 'API 密钥',
        placeholder: '输入 Metaso API 密钥...',
        icon: 'lucide:key'
      }
    ]
  },
  {
    id: 'serper',
    name: 'Serper',
    icon: 'lucide:globe',
    description: 'Google 搜索结果 API，结果丰富',
    needsApiKey: true,
    apiFields: [
      {
        key: 'web_search.serper_api_keys',
        label: 'API 密钥',
        placeholder: '输入 Serper API 密钥...',
        icon: 'lucide:key'
      }
    ]
  },
  {
    id: 'searxng',
    name: 'SearXNG',
    icon: 'lucide:server',
    description: '自托管的元搜索引擎，支持自定义实例',
    needsApiKey: true,
    apiFields: [
      {
        key: 'web_search.searxng_instances',
        label: '实例 URL',
        placeholder: '输入 SearXNG 实例地址...',
        icon: 'lucide:link'
      },
      {
        key: 'web_search.searxng_api_keys',
        label: 'API 密钥（可选）',
        placeholder: '输入 SearXNG API 密钥...',
        icon: 'lucide:key'
      }
    ]
  }
]

// 解析已启用的引擎列表
// 优先从 value 获取（这是 editedValues 中的值），如果没有则从 configData 获取
const enabledEngines = computed(() => {
  // props.value 是当前编辑的值（来自 editedValues）
  if (props.value !== undefined && props.value !== null) {
    if (Array.isArray(props.value)) {
      return props.value as string[]
    }
  }
  
  // 如果没有编辑值，从 configData 中获取原始值
  if (props.configData && typeof props.configData === 'object') {
    const webSearch = (props.configData as any).web_search
    if (webSearch && Array.isArray(webSearch.enabled_engines)) {
      return webSearch.enabled_engines as string[]
    }
  }
  
  return []
})

// 检查引擎是否启用
function isEngineEnabled(engineId: string): boolean {
  return enabledEngines.value.includes(engineId)
}

// 切换引擎启用状态
function toggleEngine(engineId: string) {
  const currentEngines = [...enabledEngines.value]
  const newEngines = isEngineEnabled(engineId)
    ? currentEngines.filter(id => id !== engineId)
    : [...currentEngines, engineId]
  
  emit('update', newEngines)
}

// 获取指定配置的 API 密钥列表
function getApiKeys(configKey: string): string[] {
  // 处理嵌套的配置键，如 'web_search.exa_api_keys'
  const keys = configKey.split('.')
  let value: any = props.configData
  
  for (const key of keys) {
    if (value && typeof value === 'object') {
      value = value[key]
    } else {
      return []
    }
  }
  
  if (Array.isArray(value)) {
    return value as string[]
  }
  return []
}

// 添加 API 密钥
function addApiKey(configKey: string) {
  const currentKeys = getApiKeys(configKey)
  emit('updateConfig', configKey, [...currentKeys, ''])
}

// 删除 API 密钥
function removeApiKey(configKey: string, index: number) {
  const currentKeys = getApiKeys(configKey)
  const newKeys = currentKeys.filter((_, i) => i !== index)
  emit('updateConfig', configKey, newKeys)
}

// 更新 API 密钥
function updateApiKey(configKey: string, index: number, value: string) {
  const currentKeys = getApiKeys(configKey)
  const newKeys = [...currentKeys]
  newKeys[index] = value
  emit('updateConfig', configKey, newKeys)
}
</script>

<style scoped>
.web-search-engines-editor {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.editor-header h4 {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 15px;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0 0 6px 0;
}

.editor-header h4 svg {
  color: var(--primary);
}

.editor-hint {
  font-size: 13px;
  color: var(--text-tertiary);
  margin: 0;
}

.engines-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(340px, 1fr));
  gap: 16px;
}

.engine-card {
  background: var(--bg-secondary);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-lg);
  padding: 16px;
  transition: all 0.2s ease;
}

.engine-card:hover {
  border-color: var(--border-color-hover);
}

.engine-card.is-enabled {
  border-color: var(--primary);
  background: color-mix(in srgb, var(--primary) 5%, var(--bg-secondary));
}

.engine-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 8px;
}

.engine-toggle {
  position: relative;
  width: 44px;
  height: 24px;
  flex-shrink: 0;
}

.engine-toggle input {
  opacity: 0;
  width: 0;
  height: 0;
}

.toggle-slider {
  position: absolute;
  cursor: pointer;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: var(--bg-tertiary);
  border-radius: 24px;
  transition: 0.3s;
}

.toggle-slider:before {
  position: absolute;
  content: "";
  height: 18px;
  width: 18px;
  left: 3px;
  bottom: 3px;
  background-color: white;
  border-radius: 50%;
  transition: 0.3s;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.2);
}

.engine-toggle input:checked + .toggle-slider {
  background-color: var(--primary);
}

.engine-toggle input:checked + .toggle-slider:before {
  transform: translateX(20px);
}

.engine-info {
  display: flex;
  align-items: center;
  gap: 8px;
  flex: 1;
  min-width: 0;
}

.engine-icon {
  font-size: 20px;
  color: var(--text-secondary);
}

.engine-card.is-enabled .engine-icon {
  color: var(--primary);
}

.engine-name {
  font-weight: 600;
  font-size: 14px;
  color: var(--text-primary);
}

.api-badge,
.free-badge {
  padding: 2px 8px;
  border-radius: 10px;
  font-size: 11px;
  font-weight: 500;
  flex-shrink: 0;
}

.api-badge {
  background: color-mix(in srgb, #f59e0b 15%, transparent);
  color: #f59e0b;
}

.free-badge {
  background: color-mix(in srgb, #22c55e 15%, transparent);
  color: #22c55e;
}

.engine-desc {
  font-size: 12px;
  color: var(--text-tertiary);
  margin: 0;
  line-height: 1.5;
}

.api-config {
  margin-top: 16px;
  padding-top: 16px;
  border-top: 1px solid var(--border-color);
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.api-field {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.api-field-label {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  font-weight: 500;
  color: var(--text-secondary);
}

.api-field-label svg {
  font-size: 14px;
}

.api-keys-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.api-key-item {
  display: flex;
  gap: 8px;
}

.api-key-input {
  flex: 1;
  padding: 8px 12px;
  border: 1px solid var(--border-color);
  border-radius: var(--radius);
  background: var(--bg-primary);
  color: var(--text-primary);
  font-size: 13px;
  font-family: 'Roboto Mono', 'Noto Sans SC', monospace !important;
}

.api-key-input:focus {
  outline: none;
  border-color: var(--primary);
  box-shadow: 0 0 0 3px color-mix(in srgb, var(--primary) 20%, transparent);
}

.api-key-input::placeholder {
  color: var(--text-tertiary);
}

.btn-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  border: none;
  border-radius: var(--radius);
  background: transparent;
  color: var(--text-tertiary);
  cursor: pointer;
  transition: all 0.15s ease;
}

.btn-icon:hover {
  background: var(--bg-tertiary);
  color: var(--text-secondary);
}

.delete-btn:hover {
  background: color-mix(in srgb, #ef4444 15%, transparent);
  color: #ef4444;
}

.btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  padding: 8px 16px;
  border: none;
  border-radius: var(--radius);
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.15s ease;
}

.btn-sm {
  padding: 6px 12px;
  font-size: 12px;
}

.btn-outline {
  background: transparent;
  border: 1px solid var(--border-color);
  color: var(--text-secondary);
}

.btn-outline:hover {
  border-color: var(--primary);
  color: var(--primary);
  background: color-mix(in srgb, var(--primary) 5%, transparent);
}

.add-key-btn {
  align-self: flex-start;
}

/* 响应式 */
@media (max-width: 768px) {
  .engines-grid {
    grid-template-columns: 1fr;
  }
}
</style>
