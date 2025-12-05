<template>
  <div class="model-config-editor">
    <!-- 快速操作栏 -->
    <div class="quick-actions">
      <h3>
        <Icon icon="lucide:zap" />
        快速操作
      </h3>
      <div class="action-buttons">
        <button class="action-btn" @click="showAddProviderModal = true">
          <Icon icon="lucide:plus-circle" />
          <span>添加提供商</span>
          <small>配置新的 AI 服务提供商</small>
        </button>
        <button class="action-btn" @click="showAddModelModal = true">
          <Icon icon="lucide:bot" />
          <span>添加模型</span>
          <small>配置新的 AI 模型</small>
        </button>
      </div>
    </div>

    <!-- API 提供商列表 -->
    <div class="providers-section">
      <div class="section-header">
        <h3>
          <Icon icon="lucide:cloud" />
          API 服务提供商
        </h3>
        <span class="provider-count">{{ apiProviders.length }} 个提供商</span>
      </div>
      
      <div v-if="apiProviders.length === 0" class="empty-state">
        <Icon icon="lucide:cloud-off" />
        <p>暂无配置的提供商</p>
        <button class="btn btn-primary" @click="showAddProviderModal = true">
          <Icon icon="lucide:plus" />
          添加第一个提供商
        </button>
      </div>
      
      <div v-else class="providers-grid">
        <div 
          v-for="(provider, index) in apiProviders" 
          :key="index" 
          class="provider-card"
          :class="{ expanded: expandedProvider === index }"
        >
          <div class="provider-header" @click="toggleProvider(index)">
            <div class="provider-icon">
              <Icon :icon="getProviderIcon(provider.name || '')" />
            </div>
            <div class="provider-info">
              <h4>{{ provider.name || '未命名提供商' }}</h4>
              <span class="provider-type">{{ getClientTypeLabel(provider.client_type) }}</span>
            </div>
            <div class="provider-meta">
              <span class="model-count">{{ getProviderModelCount(provider.name) }} 个模型</span>
              <Icon :icon="expandedProvider === index ? 'lucide:chevron-up' : 'lucide:chevron-down'" />
            </div>
          </div>
          
          <div v-show="expandedProvider === index" class="provider-content">
            <!-- 基础配置 -->
            <div class="config-group">
              <h5>
                <Icon icon="lucide:settings" />
                基础配置
              </h5>
              <div class="config-fields">
                <div class="config-field">
                  <label>
                    提供商名称
                    <span class="field-hint">API 服务商名称，用于在模型配置中引用</span>
                  </label>
                  <input 
                    type="text" 
                    class="input" 
                    :value="provider.name"
                    @input="updateProvider(index, 'name', ($event.target as HTMLInputElement).value)"
                    placeholder="例如: DeepSeek, OpenAI, SiliconFlow"
                  />
                </div>
                <div class="config-field">
                  <label>
                    API 地址 (Base URL)
                    <span class="field-hint">API 服务商的 BaseURL</span>
                  </label>
                  <input 
                    type="text" 
                    class="input" 
                    :value="provider.base_url"
                    @input="updateProvider(index, 'base_url', ($event.target as HTMLInputElement).value)"
                    placeholder="例如: https://api.deepseek.com/v1"
                  />
                </div>
                <div class="config-field">
                  <label>
                    API 密钥
                    <span class="field-hint">支持单个密钥或密钥列表轮询（用逗号分隔）</span>
                  </label>
                  <div class="password-input">
                    <input 
                      :type="showApiKey[index] ? 'text' : 'password'" 
                      class="input" 
                      :value="formatApiKey(provider.api_key)"
                      @input="updateProvider(index, 'api_key', parseApiKey(($event.target as HTMLInputElement).value))"
                      placeholder="sk-xxx 或 key1, key2, key3"
                    />
                    <button class="toggle-visibility" @click="toggleApiKeyVisibility(index)">
                      <Icon :icon="showApiKey[index] ? 'lucide:eye-off' : 'lucide:eye'" />
                    </button>
                  </div>
                </div>
                <div class="config-field">
                  <label>
                    客户端类型
                    <span class="field-hint">API 请求客户端，Gemini 需要选择专用客户端</span>
                  </label>
                  <select 
                    class="input"
                    :value="provider.client_type || 'openai'"
                    @change="updateProvider(index, 'client_type', ($event.target as HTMLSelectElement).value)"
                  >
                    <option value="openai">OpenAI 兼容</option>
                    <option value="aiohttp_gemini">Gemini（Google）</option>
                  </select>
                </div>
              </div>
            </div>
            
            <!-- 高级设置 -->
            <div class="config-group collapsible">
              <div class="group-header clickable" @click="toggleAdvanced(index)">
                <h5>
                  <Icon icon="lucide:sliders" />
                  高级设置
                </h5>
                <Icon :icon="showAdvanced[index] ? 'lucide:chevron-up' : 'lucide:chevron-down'" />
              </div>
              <div v-show="showAdvanced[index]" class="advanced-fields">
                <div class="config-field">
                  <label>
                    最大重试次数
                    <span class="field-hint">单个模型 API 调用失败时的最大重试次数</span>
                  </label>
                  <input 
                    type="number" 
                    class="input" 
                    :value="provider.max_retry ?? 2"
                    @input="updateProvider(index, 'max_retry', parseInt(($event.target as HTMLInputElement).value))"
                    min="0"
                    max="10"
                  />
                </div>
                <div class="config-field">
                  <label>
                    请求超时（秒）
                    <span class="field-hint">API 请求超时时间</span>
                  </label>
                  <input 
                    type="number" 
                    class="input" 
                    :value="provider.timeout ?? 30"
                    @input="updateProvider(index, 'timeout', parseInt(($event.target as HTMLInputElement).value))"
                    min="5"
                    max="300"
                  />
                </div>
                <div class="config-field">
                  <label>
                    重试间隔（秒）
                    <span class="field-hint">重试间隔时间</span>
                  </label>
                  <input 
                    type="number" 
                    class="input" 
                    :value="provider.retry_interval ?? 10"
                    @input="updateProvider(index, 'retry_interval', parseInt(($event.target as HTMLInputElement).value))"
                    min="1"
                    max="60"
                  />
                </div>
              </div>
            </div>
            
            <!-- 操作按钮 -->
            <div class="provider-actions">
              <button class="btn btn-danger" @click="removeProvider(index)">
                <Icon icon="lucide:trash-2" />
                删除此提供商
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 模型列表 -->
    <div class="models-section">
      <div class="section-header">
        <h3>
          <Icon icon="lucide:cpu" />
          模型配置
        </h3>
        <span class="model-count">{{ models.length }} 个模型</span>
      </div>
      
      <div v-if="models.length === 0" class="empty-state">
        <Icon icon="lucide:bot" />
        <p>暂无配置的模型</p>
        <button class="btn btn-primary" @click="showAddModelModal = true">
          <Icon icon="lucide:plus" />
          添加第一个模型
        </button>
      </div>
      
      <div v-else class="models-grid">
        <div 
          v-for="(model, index) in models" 
          :key="index" 
          class="model-card"
          :class="{ expanded: expandedModel === index }"
        >
          <div class="model-header" @click="toggleModel(index)">
            <div class="model-icon">
              <Icon :icon="getProviderIcon(model.api_provider || '')" />
            </div>
            <div class="model-info">
              <h4>{{ model.name || model.model_identifier || '未命名模型' }}</h4>
              <span class="model-provider">{{ model.api_provider || '未指定提供商' }}</span>
            </div>
            <div class="model-meta">
              <span v-if="model.price_in || model.price_out" class="model-price">
                ¥{{ model.price_in ?? 0 }}/{{ model.price_out ?? 0 }} /M
              </span>
              <Icon :icon="expandedModel === index ? 'lucide:chevron-up' : 'lucide:chevron-down'" />
            </div>
          </div>
          
          <div v-show="expandedModel === index" class="model-content">
            <div class="config-fields">
              <div class="config-field">
                <label>
                  模型标识符
                  <span class="field-hint">API 服务商提供的模型标识符</span>
                </label>
                <input 
                  type="text" 
                  class="input" 
                  :value="model.model_identifier"
                  @input="updateModel(index, 'model_identifier', ($event.target as HTMLInputElement).value)"
                  placeholder="例如: deepseek-chat, gpt-4"
                />
              </div>
              <div class="config-field">
                <label>
                  模型名称
                  <span class="field-hint">模型的自定义名称，在任务配置中使用</span>
                </label>
                <input 
                  type="text" 
                  class="input" 
                  :value="model.name"
                  @input="updateModel(index, 'name', ($event.target as HTMLInputElement).value)"
                  placeholder="例如: deepseek-v3"
                />
              </div>
              <div class="config-field">
                <label>
                  API 提供商
                  <span class="field-hint">对应在 api_providers 中配置的服务商名称</span>
                </label>
                <select 
                  class="input"
                  :value="model.api_provider"
                  @change="updateModel(index, 'api_provider', ($event.target as HTMLSelectElement).value)"
                >
                  <option value="">请选择提供商</option>
                  <option v-for="provider in apiProviders" :key="provider.name" :value="provider.name">
                    {{ provider.name }}
                  </option>
                </select>
              </div>
              <div class="config-field-row">
                <div class="config-field">
                  <label>
                    输入价格
                    <span class="field-hint">元/M token</span>
                  </label>
                  <input 
                    type="number" 
                    class="input" 
                    :value="model.price_in ?? 0"
                    @input="updateModel(index, 'price_in', parseFloat(($event.target as HTMLInputElement).value))"
                    step="0.1"
                    min="0"
                  />
                </div>
                <div class="config-field">
                  <label>
                    输出价格
                    <span class="field-hint">元/M token</span>
                  </label>
                  <input 
                    type="number" 
                    class="input" 
                    :value="model.price_out ?? 0"
                    @input="updateModel(index, 'price_out', parseFloat(($event.target as HTMLInputElement).value))"
                    step="0.1"
                    min="0"
                  />
                </div>
              </div>
            </div>
            
            <!-- 模型高级选项 -->
            <div class="config-group collapsible">
              <div class="group-header clickable" @click="toggleModelAdvanced(index)">
                <h5>
                  <Icon icon="lucide:sliders" />
                  高级选项
                </h5>
                <Icon :icon="showModelAdvanced[index] ? 'lucide:chevron-up' : 'lucide:chevron-down'" />
              </div>
              <div v-show="showModelAdvanced[index]" class="advanced-fields">
                <div class="config-field inline">
                  <div class="field-left">
                    <label>强制流式输出</label>
                    <span class="field-hint">如果模型不支持非流式输出，请启用此选项</span>
                  </div>
                  <label class="toggle-switch">
                    <input 
                      type="checkbox" 
                      :checked="Boolean(model.force_stream_mode)"
                      @change="updateModel(index, 'force_stream_mode', ($event.target as HTMLInputElement).checked)"
                    />
                    <span class="toggle-slider"></span>
                  </label>
                </div>
                <div class="config-field inline">
                  <div class="field-left">
                    <label>防截断</label>
                    <span class="field-hint">当模型输出不完整时，系统会自动重试</span>
                  </div>
                  <label class="toggle-switch">
                    <input 
                      type="checkbox" 
                      :checked="Boolean(model.anti_truncation)"
                      @change="updateModel(index, 'anti_truncation', ($event.target as HTMLInputElement).checked)"
                    />
                    <span class="toggle-slider"></span>
                  </label>
                </div>
                <div class="config-field inline">
                  <div class="field-left">
                    <label>提示词扰动</label>
                    <span class="field-hint">启用提示词扰动，整合内容混淆和注意力优化</span>
                  </div>
                  <label class="toggle-switch">
                    <input 
                      type="checkbox" 
                      :checked="Boolean(model.enable_prompt_perturbation)"
                      @change="updateModel(index, 'enable_prompt_perturbation', ($event.target as HTMLInputElement).checked)"
                    />
                    <span class="toggle-slider"></span>
                  </label>
                </div>
              </div>
            </div>
            
            <!-- 操作按钮 -->
            <div class="model-actions">
              <button class="btn btn-danger" @click="removeModel(index)">
                <Icon icon="lucide:trash-2" />
                删除此模型
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 模型任务配置 -->
    <div class="task-config-section">
      <div class="section-header">
        <h3>
          <Icon icon="lucide:list-checks" />
          模型任务配置
        </h3>
        <span class="task-count">配置各功能使用的模型</span>
      </div>
      
      <div class="task-configs">
        <div 
          v-for="(task, taskKey) in modelTaskConfigs" 
          :key="taskKey" 
          class="task-card"
        >
          <div class="task-info">
            <h4>{{ task.name }}</h4>
            <p>{{ task.description }}</p>
          </div>
          <div class="task-config">
            <select 
              class="input"
              :value="getTaskModel(taskKey)"
              @change="updateTaskModel(taskKey, ($event.target as HTMLSelectElement).value)"
            >
              <option value="">未配置</option>
              <option v-for="model in models" :key="model.name" :value="model.name">
                {{ model.name }}
              </option>
            </select>
          </div>
        </div>
      </div>
    </div>

    <!-- 添加提供商弹窗 -->
    <div v-if="showAddProviderModal" class="modal-overlay" @click.self="showAddProviderModal = false">
      <div class="modal-content">
        <div class="modal-header">
          <h3>
            <Icon icon="lucide:plus-circle" />
            添加 API 提供商
          </h3>
          <button class="close-btn" @click="showAddProviderModal = false">
            <Icon icon="lucide:x" />
          </button>
        </div>
        <div class="modal-body">
          <!-- 预设模板 -->
          <div class="preset-providers">
            <h4>选择预设模板</h4>
            <div class="preset-grid">
              <button 
                v-for="preset in providerPresets" 
                :key="preset.name"
                class="preset-btn"
                :class="{ active: newProvider.name === preset.name }"
                @click="selectPreset(preset)"
              >
                <Icon :icon="preset.icon" />
                <span>{{ preset.name }}</span>
                <small>{{ preset.description }}</small>
              </button>
            </div>
          </div>
          
          <div class="divider">
            <span>配置详情</span>
          </div>
          
          <div class="manual-config">
            <div class="config-field">
              <label>提供商名称</label>
              <input v-model="newProvider.name" type="text" class="input" placeholder="例如: DeepSeek" />
            </div>
            <div class="config-field">
              <label>API 地址</label>
              <input v-model="newProvider.base_url" type="text" class="input" placeholder="https://api.example.com/v1" />
            </div>
            <div class="config-field">
              <label>API 密钥</label>
              <input v-model="newProvider.api_key" type="password" class="input" placeholder="你的 API 密钥" />
            </div>
            <div class="config-field">
              <label>客户端类型</label>
              <select v-model="newProvider.client_type" class="input">
                <option value="openai">OpenAI 兼容</option>
                <option value="aiohttp_gemini">Gemini（Google）</option>
              </select>
            </div>
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn btn-secondary" @click="showAddProviderModal = false">取消</button>
          <button class="btn btn-primary" @click="confirmAddProvider" :disabled="!newProvider.name || !newProvider.base_url">
            <Icon icon="lucide:check" />
            添加
          </button>
        </div>
      </div>
    </div>

    <!-- 添加模型弹窗 -->
    <div v-if="showAddModelModal" class="modal-overlay" @click.self="showAddModelModal = false">
      <div class="modal-content">
        <div class="modal-header">
          <h3>
            <Icon icon="lucide:bot" />
            添加模型
          </h3>
          <button class="close-btn" @click="showAddModelModal = false">
            <Icon icon="lucide:x" />
          </button>
        </div>
        <div class="modal-body">
          <div class="config-field">
            <label>
              模型标识符
              <span class="field-hint">API 服务商提供的模型标识符</span>
            </label>
            <input v-model="newModel.model_identifier" type="text" class="input" placeholder="例如: deepseek-chat, gpt-4" />
          </div>
          <div class="config-field">
            <label>
              模型名称
              <span class="field-hint">模型的自定义名称，在任务配置中使用</span>
            </label>
            <input v-model="newModel.name" type="text" class="input" placeholder="例如: deepseek-v3" />
          </div>
          <div class="config-field">
            <label>API 提供商</label>
            <select v-model="newModel.api_provider" class="input">
              <option value="">请选择提供商</option>
              <option v-for="provider in apiProviders" :key="provider.name" :value="provider.name">
                {{ provider.name }}
              </option>
            </select>
          </div>
          <div class="config-field-row">
            <div class="config-field">
              <label>输入价格 (元/M token)</label>
              <input v-model.number="newModel.price_in" type="number" class="input" step="0.1" min="0" />
            </div>
            <div class="config-field">
              <label>输出价格 (元/M token)</label>
              <input v-model.number="newModel.price_out" type="number" class="input" step="0.1" min="0" />
            </div>
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn btn-secondary" @click="showAddModelModal = false">取消</button>
          <button class="btn btn-primary" @click="confirmAddModel" :disabled="!newModel.model_identifier || !newModel.name">
            <Icon icon="lucide:check" />
            添加
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { Icon } from '@iconify/vue'
import { providerPresets, modelTaskConfigs } from '@/config/configDescriptions'

// API 提供商接口
interface ApiProvider {
  name?: string
  base_url?: string
  api_key?: string | string[]
  client_type?: string
  max_retry?: number
  timeout?: number
  retry_interval?: number
  [key: string]: unknown
}

// 模型接口
interface Model {
  model_identifier?: string
  name?: string
  api_provider?: string
  price_in?: number
  price_out?: number
  force_stream_mode?: boolean
  anti_truncation?: boolean
  enable_prompt_perturbation?: boolean
  extra_params?: Record<string, unknown>
  [key: string]: unknown
}

const props = defineProps<{
  parsedData: Record<string, unknown>
  editedValues: Record<string, unknown>
}>()

const emit = defineEmits<{
  (e: 'update', key: string, value: unknown): void
}>()

// 状态
const expandedProvider = ref<number | null>(0)
const expandedModel = ref<number | null>(null)
const showApiKey = ref<Record<number, boolean>>({})
const showAdvanced = ref<Record<number, boolean>>({})
const showModelAdvanced = ref<Record<number, boolean>>({})
const showAddProviderModal = ref(false)
const showAddModelModal = ref(false)

// 新提供商表单
const newProvider = ref({
  name: '',
  base_url: '',
  api_key: '',
  client_type: 'openai'
})

// 新模型表单
const newModel = ref({
  model_identifier: '',
  name: '',
  api_provider: '',
  price_in: 0,
  price_out: 0
})

// 计算 API 提供商列表
const apiProviders = computed(() => {
  const data = props.parsedData
  if (Array.isArray(data.api_providers)) {
    return data.api_providers as ApiProvider[]
  }
  return []
})

// 计算模型列表
const models = computed(() => {
  const data = props.parsedData
  if (Array.isArray(data.models)) {
    return data.models as Model[]
  }
  return []
})

// 方法
function toggleProvider(index: number) {
  expandedProvider.value = expandedProvider.value === index ? null : index
}

function toggleModel(index: number) {
  expandedModel.value = expandedModel.value === index ? null : index
}

function toggleApiKeyVisibility(index: number) {
  showApiKey.value[index] = !showApiKey.value[index]
}

function toggleAdvanced(index: number) {
  showAdvanced.value[index] = !showAdvanced.value[index]
}

function toggleModelAdvanced(index: number) {
  showModelAdvanced.value[index] = !showModelAdvanced.value[index]
}

function getProviderIcon(name: string): string {
  const iconMap: Record<string, string> = {
    'openai': 'simple-icons:openai',
    'claude': 'simple-icons:anthropic',
    'anthropic': 'simple-icons:anthropic',
    'gemini': 'simple-icons:google',
    'google': 'simple-icons:google',
    'qwen': 'lucide:brain',
    '通义': 'lucide:brain',
    'deepseek': 'lucide:brain-circuit',
    'siliconflow': 'lucide:cpu',
    '硅基': 'lucide:cpu',
  }
  
  const lowerName = name.toLowerCase()
  for (const [key, icon] of Object.entries(iconMap)) {
    if (lowerName.includes(key)) {
      return icon
    }
  }
  return 'lucide:cloud'
}

function getClientTypeLabel(clientType?: string): string {
  const labels: Record<string, string> = {
    'openai': 'OpenAI 兼容',
    'aiohttp_gemini': 'Gemini（Google）'
  }
  return labels[clientType || 'openai'] || 'OpenAI 兼容'
}

function getProviderModelCount(providerName?: string): number {
  if (!providerName) return 0
  return models.value.filter(m => m.api_provider === providerName).length
}

function formatApiKey(apiKey: unknown): string {
  if (Array.isArray(apiKey)) {
    return apiKey.join(', ')
  }
  return String(apiKey || '')
}

function parseApiKey(value: string): string | string[] {
  if (value.includes(',')) {
    return value.split(',').map(s => s.trim()).filter(s => s)
  }
  return value
}

function updateProvider(index: number, key: string, value: unknown) {
  emit('update', `api_providers.${index}.${key}`, value)
}

function updateModel(index: number, key: string, value: unknown) {
  emit('update', `models.${index}.${key}`, value)
}

function selectPreset(preset: typeof providerPresets[0]) {
  newProvider.value = {
    name: preset.name === '自定义' ? '' : preset.name,
    base_url: preset.base_url,
    api_key: '',
    client_type: preset.client_type
  }
}

function confirmAddProvider() {
  if (!newProvider.value.name || !newProvider.value.base_url) return
  
  const newProviders = [...apiProviders.value, {
    name: newProvider.value.name,
    base_url: newProvider.value.base_url,
    api_key: newProvider.value.api_key,
    client_type: newProvider.value.client_type,
    max_retry: 2,
    timeout: 30,
    retry_interval: 10
  }]
  
  emit('update', 'api_providers', newProviders)
  
  showAddProviderModal.value = false
  newProvider.value = { name: '', base_url: '', api_key: '', client_type: 'openai' }
  
  // 展开新添加的提供商
  expandedProvider.value = newProviders.length - 1
}

function removeProvider(index: number) {
  if (!confirm('确定要删除此提供商吗？')) return
  
  const newProviders = apiProviders.value.filter((_, i) => i !== index)
  emit('update', 'api_providers', newProviders)
  
  if (expandedProvider.value === index) {
    expandedProvider.value = null
  }
}

function confirmAddModel() {
  if (!newModel.value.model_identifier || !newModel.value.name) return
  
  const newModels = [...models.value, {
    model_identifier: newModel.value.model_identifier,
    name: newModel.value.name,
    api_provider: newModel.value.api_provider,
    price_in: newModel.value.price_in,
    price_out: newModel.value.price_out
  }]
  
  emit('update', 'models', newModels)
  
  showAddModelModal.value = false
  newModel.value = { model_identifier: '', name: '', api_provider: '', price_in: 0, price_out: 0 }
  
  // 展开新添加的模型
  expandedModel.value = newModels.length - 1
}

function removeModel(index: number) {
  if (!confirm('确定要删除此模型吗？')) return
  
  const newModels = models.value.filter((_, i) => i !== index)
  emit('update', 'models', newModels)
  
  if (expandedModel.value === index) {
    expandedModel.value = null
  }
}

// 任务模型配置
function getTaskModel(taskKey: string): string {
  const data = props.parsedData
  const taskConfig = data.model_task_config as Record<string, Record<string, unknown>> | undefined
  if (!taskConfig || !taskConfig[taskKey]) return ''
  
  const modelList = taskConfig[taskKey].model_list as string[] | undefined
  return modelList?.[0] || ''
}

function updateTaskModel(taskKey: string, modelName: string) {
  emit('update', `model_task_config.${taskKey}.model_list`, modelName ? [modelName] : [])
}

// 初始化
watch(() => props.parsedData, () => {
  // 如果有提供商，默认展开第一个
  if (apiProviders.value.length > 0 && expandedProvider.value === null) {
    expandedProvider.value = 0
  }
}, { immediate: true })
</script>

<style scoped>
.model-config-editor {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

/* 快速操作栏 */
.quick-actions {
  background: linear-gradient(135deg, var(--primary-bg), rgba(139, 92, 246, 0.1));
  border-radius: var(--radius-lg);
  padding: 20px;
  border: 1px solid var(--border-color);
}

.quick-actions h3 {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0 0 16px 0;
}

.quick-actions h3 svg {
  color: var(--primary);
}

.action-buttons {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 12px;
}

.action-btn {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 4px;
  padding: 16px;
  background: var(--bg-primary);
  border: 1px solid var(--border-color);
  border-radius: var(--radius);
  cursor: pointer;
  transition: all var(--transition-fast);
}

.action-btn:hover {
  border-color: var(--primary);
  box-shadow: 0 4px 12px rgba(59, 130, 246, 0.15);
}

.action-btn svg {
  font-size: 24px;
  color: var(--primary);
}

.action-btn span {
  font-size: 14px;
  font-weight: 500;
  color: var(--text-primary);
}

.action-btn small {
  font-size: 12px;
  color: var(--text-tertiary);
}

/* 提供商区域 */
.providers-section {
  background: var(--bg-primary);
  border-radius: var(--radius-lg);
  border: 1px solid var(--border-color);
  overflow: hidden;
}

.section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 20px;
  background: var(--bg-secondary);
  border-bottom: 1px solid var(--border-color);
}

.section-header h3 {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0;
}

.provider-count {
  font-size: 12px;
  color: var(--text-tertiary);
  padding: 4px 10px;
  background: var(--bg-primary);
  border-radius: var(--radius-full);
}

.providers-grid {
  display: flex;
  flex-direction: column;
}

/* 提供商卡片 */
.provider-card {
  border-bottom: 1px solid var(--border-color);
}

.provider-card:last-child {
  border-bottom: none;
}

.provider-header {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 16px 20px;
  cursor: pointer;
  transition: background var(--transition-fast);
}

.provider-header:hover {
  background: var(--bg-secondary);
}

.provider-icon {
  width: 44px;
  height: 44px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, var(--primary), #6d28d9);
  border-radius: var(--radius);
  color: white;
  font-size: 20px;
}

.provider-info {
  flex: 1;
}

.provider-info h4 {
  font-size: 15px;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0 0 4px 0;
}

.provider-type {
  font-size: 12px;
  color: var(--text-tertiary);
}

.provider-meta {
  display: flex;
  align-items: center;
  gap: 12px;
  color: var(--text-secondary);
}

.model-count {
  font-size: 12px;
  padding: 4px 10px;
  background: var(--bg-secondary);
  border-radius: var(--radius-full);
}

.provider-content {
  padding: 0 20px 20px;
  display: flex;
  flex-direction: column;
  gap: 20px;
}

/* 配置组 */
.config-group {
  background: var(--bg-secondary);
  border-radius: var(--radius);
  padding: 16px;
}

.config-group h5 {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0 0 16px 0;
}

.group-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16px;
}

.group-header h5 {
  margin: 0;
}

.group-header.clickable {
  cursor: pointer;
  margin-bottom: 0;
  padding: 4px 0;
}

.group-header.clickable:hover {
  color: var(--primary);
}

.config-fields {
  display: grid;
  gap: 16px;
}

.config-field {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.config-field label {
  font-size: 13px;
  font-weight: 500;
  color: var(--text-primary);
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.field-hint {
  font-size: 11px;
  font-weight: 400;
  color: var(--text-tertiary);
}

.input {
  width: 100%;
  padding: 10px 14px;
  border: 1px solid var(--border-color);
  border-radius: var(--radius);
  background: var(--bg-primary);
  color: var(--text-primary);
  font-size: 14px;
  outline: none;
  transition: all var(--transition-fast);
}

.input:focus {
  border-color: var(--primary);
  box-shadow: 0 0 0 3px var(--primary-bg);
}

select.input {
  cursor: pointer;
}

.password-input {
  position: relative;
  display: flex;
}

.password-input .input {
  padding-right: 44px;
}

.toggle-visibility {
  position: absolute;
  right: 8px;
  top: 50%;
  transform: translateY(-50%);
  width: 28px;
  height: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: transparent;
  border: none;
  border-radius: var(--radius-sm);
  color: var(--text-tertiary);
  cursor: pointer;
  transition: all var(--transition-fast);
}

.toggle-visibility:hover {
  background: var(--bg-secondary);
  color: var(--text-primary);
}

/* 模型列表 */
.models-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.model-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px;
  background: var(--bg-primary);
  border-radius: var(--radius);
}

.model-info {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.model-name {
  font-size: 13px;
  font-weight: 500;
  color: var(--text-primary);
  font-family: 'JetBrains Mono', monospace;
}

.model-display-name {
  font-size: 11px;
  color: var(--text-tertiary);
}

.model-actions {
  display: flex;
  gap: 4px;
}

.btn-icon {
  width: 28px;
  height: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: transparent;
  border: none;
  border-radius: var(--radius-sm);
  color: var(--text-tertiary);
  cursor: pointer;
  transition: all var(--transition-fast);
}

.btn-icon:hover {
  background: var(--bg-secondary);
  color: var(--text-primary);
}

.btn-icon.danger:hover {
  background: rgba(239, 68, 68, 0.1);
  color: #ef4444;
}

.empty-models {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 20px;
  color: var(--text-tertiary);
  font-size: 13px;
}

.advanced-fields {
  margin-top: 16px;
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 16px;
}

.provider-actions {
  display: flex;
  justify-content: flex-end;
  padding-top: 8px;
  border-top: 1px solid var(--border-color);
}

/* 按钮样式 */
.btn {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  padding: 8px 16px;
  border: none;
  border-radius: var(--radius);
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: all var(--transition-fast);
}

.btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn-primary {
  background: var(--primary);
  color: white;
}

.btn-primary:hover:not(:disabled) {
  background: var(--primary-hover);
}

.btn-secondary {
  background: var(--bg-secondary);
  color: var(--text-primary);
}

.btn-secondary:hover:not(:disabled) {
  background: var(--bg-hover);
}

.btn-ghost {
  background: transparent;
  color: var(--text-secondary);
}

.btn-ghost:hover:not(:disabled) {
  background: var(--bg-secondary);
  color: var(--text-primary);
}

.btn-danger {
  background: transparent;
  color: #ef4444;
}

.btn-danger:hover {
  background: rgba(239, 68, 68, 0.1);
}

.btn-sm {
  padding: 6px 12px;
  font-size: 12px;
}

/* 空状态 */
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 16px;
  padding: 60px;
  color: var(--text-tertiary);
}

.empty-state svg {
  font-size: 48px;
  opacity: 0.5;
}

.empty-state p {
  margin: 0;
  font-size: 14px;
}

/* 弹窗样式 */
.modal-overlay {
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
  backdrop-filter: blur(4px);
}

.modal-content {
  background: var(--bg-primary);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-lg);
  width: 90%;
  max-width: 500px;
  max-height: 80vh;
  overflow: hidden;
  animation: modalIn 0.2s ease;
  display: flex;
  flex-direction: column;
}

@keyframes modalIn {
  from { opacity: 0; transform: scale(0.95); }
  to { opacity: 1; transform: scale(1); }
}

.modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 20px;
  border-bottom: 1px solid var(--border-color);
}

.modal-header h3 {
  display: flex;
  align-items: center;
  gap: 8px;
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary);
}

.close-btn {
  width: 28px;
  height: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: transparent;
  border: none;
  border-radius: var(--radius);
  color: var(--text-secondary);
  cursor: pointer;
  transition: all var(--transition-fast);
}

.close-btn:hover {
  background: var(--bg-secondary);
  color: var(--text-primary);
}

.modal-body {
  padding: 20px;
  overflow-y: auto;
  flex: 1;
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  padding: 16px 20px;
  border-top: 1px solid var(--border-color);
}

/* 预设模板 */
.preset-providers h4 {
  font-size: 13px;
  font-weight: 500;
  color: var(--text-secondary);
  margin: 0 0 12px 0;
}

.preset-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 8px;
}

.preset-btn {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  padding: 16px 12px;
  background: var(--bg-secondary);
  border: 1px solid var(--border-color);
  border-radius: var(--radius);
  cursor: pointer;
  transition: all var(--transition-fast);
}

.preset-btn:hover {
  border-color: var(--primary);
  background: var(--primary-bg);
}

.preset-btn svg {
  font-size: 24px;
  color: var(--text-secondary);
}

.preset-btn:hover svg {
  color: var(--primary);
}

.preset-btn span {
  font-size: 12px;
  color: var(--text-primary);
}

.divider {
  display: flex;
  align-items: center;
  gap: 16px;
  margin: 20px 0;
}

.divider::before,
.divider::after {
  content: '';
  flex: 1;
  height: 1px;
  background: var(--border-color);
}

.divider span {
  font-size: 12px;
  color: var(--text-tertiary);
}

.manual-config {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

/* 模型区域 */
.models-section {
  background: var(--bg-primary);
  border-radius: var(--radius-lg);
  border: 1px solid var(--border-color);
  overflow: hidden;
}

.models-grid {
  display: flex;
  flex-direction: column;
}

/* 模型卡片 */
.model-card {
  border-bottom: 1px solid var(--border-color);
}

.model-card:last-child {
  border-bottom: none;
}

.model-header {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 16px 20px;
  cursor: pointer;
  transition: background var(--transition-fast);
}

.model-header:hover {
  background: var(--bg-secondary);
}

.model-icon {
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #10b981, #059669);
  border-radius: var(--radius);
  color: white;
  font-size: 18px;
}

.model-info {
  flex: 1;
}

.model-info h4 {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0 0 4px 0;
  font-family: 'JetBrains Mono', monospace;
}

.model-provider {
  font-size: 12px;
  color: var(--text-tertiary);
}

.model-meta {
  display: flex;
  align-items: center;
  gap: 12px;
  color: var(--text-secondary);
}

.model-price {
  font-size: 12px;
  padding: 4px 10px;
  background: var(--bg-secondary);
  border-radius: var(--radius-full);
  font-family: 'JetBrains Mono', monospace;
}

.model-content {
  padding: 0 20px 20px;
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.config-field-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
}

.config-field.inline {
  flex-direction: row;
  align-items: center;
  justify-content: space-between;
}

.config-field.inline .field-left {
  flex: 1;
}

.config-field.inline label {
  margin-bottom: 0;
}

/* Toggle 开关 */
.toggle-switch {
  display: flex;
  align-items: center;
  cursor: pointer;
  flex-shrink: 0;
}

.toggle-switch input {
  display: none;
}

.toggle-slider {
  width: 44px;
  height: 24px;
  background: var(--bg-hover);
  border-radius: 12px;
  position: relative;
  transition: background var(--transition-fast);
}

.toggle-slider::after {
  content: '';
  position: absolute;
  top: 2px;
  left: 2px;
  width: 20px;
  height: 20px;
  background: white;
  border-radius: 50%;
  transition: transform var(--transition-fast);
  box-shadow: var(--shadow-sm);
}

.toggle-switch input:checked + .toggle-slider {
  background: var(--primary);
}

.toggle-switch input:checked + .toggle-slider::after {
  transform: translateX(20px);
}

.model-actions {
  display: flex;
  justify-content: flex-end;
  padding-top: 8px;
  border-top: 1px solid var(--border-color);
}

/* 任务配置区域 */
.task-config-section {
  background: var(--bg-primary);
  border-radius: var(--radius-lg);
  border: 1px solid var(--border-color);
  overflow: hidden;
}

.task-count {
  font-size: 12px;
  color: var(--text-tertiary);
}

.task-configs {
  display: grid;
  gap: 1px;
  background: var(--border-color);
}

.task-card {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  padding: 16px 20px;
  background: var(--bg-primary);
}

.task-info {
  flex: 1;
  min-width: 0;
}

.task-info h4 {
  font-size: 13px;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0 0 4px 0;
}

.task-info p {
  font-size: 12px;
  color: var(--text-tertiary);
  margin: 0;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.task-config {
  flex-shrink: 0;
  width: 200px;
}

.task-config .input {
  font-size: 13px;
  padding: 8px 12px;
}

/* 预设按钮激活状态 */
.preset-btn.active {
  border-color: var(--primary);
  background: var(--primary-bg);
}

.preset-btn.active svg {
  color: var(--primary);
}

.preset-btn small {
  font-size: 10px;
  color: var(--text-tertiary);
  text-align: center;
}

.field-left {
  display: flex;
  flex-direction: column;
  gap: 2px;
}
</style>
