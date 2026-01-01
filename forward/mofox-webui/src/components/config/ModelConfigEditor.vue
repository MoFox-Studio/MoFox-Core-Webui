<template>
  <div class="model-config-editor">
    <!-- 顶部导航栏 -->
    <div class="nav-header">
      <div class="nav-tabs">
        <button 
          v-for="tab in tabs" 
          :key="tab.key"
          class="nav-tab"
          :class="{ active: activeTab === tab.key }"
          @click="activeTab = tab.key"
        >
          <Icon :icon="tab.icon" />
          <span>{{ tab.name }}</span>
          <span v-if="tab.count !== undefined" class="tab-badge">{{ tab.count }}</span>
        </button>
      </div>
      <div class="nav-actions">
        <div class="search-box" v-if="activeTab !== 'providers'">
          <Icon icon="lucide:search" />
          <input 
            type="text" 
            v-model="searchQuery" 
            placeholder="搜索..." 
            class="search-input"
          />
          <button v-if="searchQuery" class="clear-search" @click="searchQuery = ''">
            <Icon icon="lucide:x" />
          </button>
        </div>
        <button 
          v-if="activeTab !== 'tasks'"
          class="add-btn" 
          @click="activeTab === 'providers' ? showAddProviderModal = true : showAddModelModal = true"
          :title="activeTab === 'providers' ? '添加提供商' : '添加模型'"
        >
          <Icon icon="lucide:plus" />
          <span>{{ activeTab === 'providers' ? '添加提供商' : activeTab === 'models' ? '添加模型' : '' }}</span>
        </button>
      </div>
    </div>

    <!-- API 提供商面板 -->
    <div v-show="activeTab === 'providers'" class="tab-panel">
      <div v-if="apiProviders.length === 0" class="empty-state">
        <div class="empty-icon">
          <Icon icon="lucide:cloud-off" />
        </div>
        <h3>暂无配置的提供商</h3>
        <p>添加一个 API 提供商以开始使用 AI 模型</p>
        <button class="btn btn-primary" @click="showAddProviderModal = true">
          <Icon icon="lucide:plus" />
          添加第一个提供商
        </button>
      </div>
      
      <div v-else class="provider-list">
        <div 
          v-for="(provider, index) in apiProviders" 
          :key="index" 
          class="provider-item"
          :class="{ active: selectedProvider === index }"
        >
          <div class="provider-row" @click="selectedProvider = selectedProvider === index ? null : index">
            <div class="provider-icon">
              <Icon :icon="getProviderIcon(provider.name || '')" />
            </div>
            <div class="provider-main">
              <div class="provider-name">{{ provider.name || '未命名提供商' }}</div>
              <div class="provider-meta">
                <span class="meta-tag">{{ getClientTypeLabel(provider.client_type) }}</span>
                <span class="meta-tag">{{ getProviderModelCount(provider.name) }} 个模型</span>
              </div>
            </div>
            <div class="provider-actions-row">
              <button class="icon-btn" @click.stop="removeProvider(index)" title="删除">
                <Icon icon="lucide:trash-2" />
              </button>
              <Icon :icon="selectedProvider === index ? 'lucide:chevron-up' : 'lucide:chevron-down'" class="expand-icon" />
            </div>
          </div>
          
          <Transition name="slide">
            <div v-if="selectedProvider === index" class="provider-detail">
              <div class="detail-grid">
                <div class="form-group">
                  <label>提供商名称</label>
                  <input 
                    type="text" 
                    class="form-input" 
                    :value="provider.name"
                    @input="updateProvider(index, 'name', ($event.target as HTMLInputElement).value)"
                    placeholder="例如: DeepSeek"
                  />
                </div>
                <div class="form-group">
                  <label>客户端类型</label>
                  <div class="custom-select" :class="{ open: activeDropdown === `provider-client-${index}` }">
                    <div class="select-trigger" @click.stop="toggleDropdown(`provider-client-${index}`, $event)">
                      <span>{{ getClientTypeLabel(provider.client_type) }}</span>
                      <Icon icon="lucide:chevron-down" class="chevron" :class="{ rotated: activeDropdown === `provider-client-${index}` }" />
                    </div>
                    <Teleport to="body">
                      <Transition name="dropdown-fade">
                        <div v-if="activeDropdown === `provider-client-${index}`" class="select-options" :style="dropdownStyle">
                          <div class="select-option" @click="updateProvider(index, 'client_type', 'openai'); activeDropdown = null">
                            <span>OpenAI 兼容</span>
                          </div>
                          <div class="select-option" @click="updateProvider(index, 'client_type', 'aiohttp_gemini'); activeDropdown = null">
                            <span>Gemini（Google）</span>
                          </div>
                          <div class="select-option" @click="updateProvider(index, 'client_type', 'bedrock'); activeDropdown = null">
                            <span>AWS Bedrock</span>
                          </div>
                        </div>
                      </Transition>
                    </Teleport>
                    <Teleport to="body">
                      <div v-if="activeDropdown === `provider-client-${index}`" class="dropdown-overlay" @click.stop="activeDropdown = null"></div>
                    </Teleport>
                  </div>
                </div>
                <div class="form-group full-width" v-if="provider.client_type !== 'bedrock'">
                  <label>API 地址</label>
                  <input 
                    type="text" 
                    class="form-input" 
                    :value="provider.base_url"
                    @input="updateProvider(index, 'base_url', ($event.target as HTMLInputElement).value)"
                    placeholder="https://api.example.com/v1"
                  />
                </div>
                <div class="form-group full-width">
                  <div class="label-row" style="display: flex; justify-content: space-between; align-items: center;">
                    <label>{{ provider.client_type === 'bedrock' ? 'AWS Access Key ID' : 'API 密钥' }}</label>
                  </div>
                  
                  <StringArrayEditor
                    :value="Array.isArray(provider.api_key) ? provider.api_key : (provider.api_key ? [String(provider.api_key)] : [])"
                    @update="updateProvider(index, 'api_key', $event)"
                    placeholder="输入 API 密钥"
                    add-button-text="添加备用密钥"
                    empty-text="请添加至少一个 API 密钥"
                    :is-secret="true"
                  />
                  <p class="field-hint" style="margin-top: 4px; font-size: 12px; color: var(--text-tertiary);">
                    支持配置多个 API 密钥，系统将自动轮询使用
                  </p>
                </div>
                
                <!-- Bedrock 专用配置 -->
                <template v-if="provider.client_type === 'bedrock'">
                  <div class="form-group full-width">
                    <label>AWS Secret Key</label>
                    <input 
                      type="password" 
                      class="form-input" 
                      :value="(provider.extra_params as Record<string, unknown>)?.aws_secret_key ?? ''"
                      @input="updateProviderExtraParam(index, 'aws_secret_key', ($event.target as HTMLInputElement).value)"
                      placeholder="你的 AWS Secret Access Key（IAM 角色模式可留空）"
                    />
                    <p class="field-hint" style="margin-top: 4px; font-size: 12px; color: var(--text-tertiary);">
                      IAM 角色模式下无需配置，系统将自动使用环境变量认证
                    </p>
                  </div>
                  <div class="form-group">
                    <label>AWS 区域</label>
                    <div class="custom-select" :class="{ open: activeDropdown === `provider-region-${index}` }">
                      <div class="select-trigger" @click.stop="toggleDropdown(`provider-region-${index}`, $event)">
                        <span>{{ (provider.extra_params as Record<string, unknown>)?.region ?? 'us-east-1' }}</span>
                        <Icon icon="lucide:chevron-down" class="chevron" :class="{ rotated: activeDropdown === `provider-region-${index}` }" />
                      </div>
                      <Teleport to="body">
                        <Transition name="dropdown-fade">
                          <div v-if="activeDropdown === `provider-region-${index}`" class="select-options" :style="dropdownStyle">
                            <div class="select-option" @click="updateProviderExtraParam(index, 'region', 'us-east-1'); activeDropdown = null">
                              <span>us-east-1 (弗吉尼亚北部)</span>
                            </div>
                            <div class="select-option" @click="updateProviderExtraParam(index, 'region', 'us-west-2'); activeDropdown = null">
                              <span>us-west-2 (俄勒冈)</span>
                            </div>
                            <div class="select-option" @click="updateProviderExtraParam(index, 'region', 'eu-central-1'); activeDropdown = null">
                              <span>eu-central-1 (法兰克福)</span>
                            </div>
                            <div class="select-option" @click="updateProviderExtraParam(index, 'region', 'eu-west-1'); activeDropdown = null">
                              <span>eu-west-1 (爱尔兰)</span>
                            </div>
                            <div class="select-option" @click="updateProviderExtraParam(index, 'region', 'ap-southeast-1'); activeDropdown = null">
                              <span>ap-southeast-1 (新加坡)</span>
                            </div>
                            <div class="select-option" @click="updateProviderExtraParam(index, 'region', 'ap-northeast-1'); activeDropdown = null">
                              <span>ap-northeast-1 (东京)</span>
                            </div>
                          </div>
                        </Transition>
                      </Teleport>
                      <Teleport to="body">
                        <div v-if="activeDropdown === `provider-region-${index}`" class="dropdown-overlay" @click.stop="activeDropdown = null"></div>
                      </Teleport>
                    </div>
                  </div>
                </template>
                
                <div class="form-group">
                  <label>最大重试</label>
                  <div class="number-input-wrapper">
                    <button 
                      class="number-btn" 
                      @click="updateProvider(index, 'max_retry', (provider.max_retry ?? 2) - 1)"
                      :disabled="(provider.max_retry ?? 2) <= 0"
                    >
                      <Icon icon="lucide:minus" />
                    </button>
                    <input 
                      type="number" 
                      class="form-input number-center" 
                      :value="provider.max_retry ?? 2"
                      @input="updateProvider(index, 'max_retry', parseInt(($event.target as HTMLInputElement).value))"
                      min="0" max="10"
                    />
                    <button 
                      class="number-btn" 
                      @click="updateProvider(index, 'max_retry', (provider.max_retry ?? 2) + 1)"
                      :disabled="(provider.max_retry ?? 2) >= 10"
                    >
                      <Icon icon="lucide:plus" />
                    </button>
                  </div>
                </div>
                <div class="form-group">
                  <label>超时(秒)</label>
                  <div class="number-input-wrapper">
                    <button 
                      class="number-btn" 
                      @click="updateProvider(index, 'timeout', (provider.timeout ?? 30) - 5)"
                      :disabled="(provider.timeout ?? 30) <= 5"
                    >
                      <Icon icon="lucide:minus" />
                    </button>
                    <input 
                      type="number" 
                      class="form-input number-center" 
                      :value="provider.timeout ?? 30"
                      @input="updateProvider(index, 'timeout', parseInt(($event.target as HTMLInputElement).value))"
                      min="5" max="300"
                      step="5"
                    />
                    <button 
                      class="number-btn" 
                      @click="updateProvider(index, 'timeout', (provider.timeout ?? 30) + 5)"
                      :disabled="(provider.timeout ?? 30) >= 300"
                    >
                      <Icon icon="lucide:plus" />
                    </button>
                  </div>
                </div>
                <div class="form-group">
                  <label>重试间隔(秒)</label>
                  <div class="number-input-wrapper">
                    <button 
                      class="number-btn" 
                      @click="updateProvider(index, 'retry_interval', (provider.retry_interval ?? 10) - 1)"
                      :disabled="(provider.retry_interval ?? 10) <= 1"
                    >
                      <Icon icon="lucide:minus" />
                    </button>
                    <input 
                      type="number" 
                      class="form-input number-center" 
                      :value="provider.retry_interval ?? 10"
                      @input="updateProvider(index, 'retry_interval', parseInt(($event.target as HTMLInputElement).value))"
                      min="1" max="60"
                    />
                    <button 
                      class="number-btn" 
                      @click="updateProvider(index, 'retry_interval', (provider.retry_interval ?? 10) + 1)"
                      :disabled="(provider.retry_interval ?? 10) >= 60"
                    >
                      <Icon icon="lucide:plus" />
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </Transition>
        </div>
      </div>
    </div>

    <!-- 模型面板 -->
    <div v-show="activeTab === 'models'" class="tab-panel">
      <div v-if="models.length === 0" class="empty-state">
        <div class="empty-icon">
          <Icon icon="lucide:bot" />
        </div>
        <h3>暂无配置的模型</h3>
        <p>添加一个 AI 模型以启用各项功能</p>
        <button class="btn btn-primary" @click="showAddModelModal = true">
          <Icon icon="lucide:plus" />
          添加第一个模型
        </button>
      </div>
      
      <div v-else class="model-list">
        <div 
          v-for="(model, index) in filteredModels" 
          :key="index" 
          class="model-item"
          :class="{ active: selectedModel === index }"
        >
          <div class="model-row" @click="selectedModel = selectedModel === index ? null : index">
            <div class="model-icon">
              <Icon :icon="getProviderIcon(model.api_provider || '')" />
            </div>
            <div class="model-main">
              <div class="model-name">{{ model.name || model.model_identifier || '未命名模型' }}</div>
              <div class="model-meta">
                <span class="meta-tag provider">{{ model.api_provider || '未指定' }}</span>
                <span v-if="model.price_in || model.price_out" class="meta-tag price">
                  ¥{{ model.price_in ?? 0 }}/{{ model.price_out ?? 0 }}/M
                </span>
                <span v-if="model.anti_truncation" class="meta-tag feature">防截断</span>
                <span v-if="model.enable_prompt_perturbation" class="meta-tag feature">扰动</span>
              </div>
            </div>
            <div class="model-actions-row">
              <button class="icon-btn" @click.stop="removeModel(index)" title="删除">
                <Icon icon="lucide:trash-2" />
              </button>
              <Icon :icon="selectedModel === index ? 'lucide:chevron-up' : 'lucide:chevron-down'" class="expand-icon" />
            </div>
          </div>
          
          <Transition name="slide">
            <div v-if="selectedModel === index" class="model-detail">
              <div class="detail-grid">
                <div class="form-group">
                  <label>模型标识符</label>
                  <input 
                    type="text" 
                    class="form-input" 
                    :value="model.model_identifier"
                    @input="updateModel(index, 'model_identifier', ($event.target as HTMLInputElement).value)"
                    placeholder="deepseek-chat"
                  />
                </div>
                <div class="form-group">
                  <label>模型名称</label>
                  <input 
                    type="text" 
                    class="form-input" 
                    :value="model.name"
                    @input="updateModel(index, 'name', ($event.target as HTMLInputElement).value)"
                    placeholder="deepseek-v3"
                  />
                </div>
                <div class="form-group">
                  <label>API 提供商</label>
                  <div class="custom-select" :class="{ open: activeDropdown === `model-provider-${index}` }">
                    <div class="select-trigger" @click.stop="toggleDropdown(`model-provider-${index}`, $event)">
                      <span>{{ model.api_provider || '请选择' }}</span>
                      <Icon icon="lucide:chevron-down" class="chevron" :class="{ rotated: activeDropdown === `model-provider-${index}` }" />
                    </div>
                    <Teleport to="body">
                      <Transition name="dropdown-fade">
                        <div v-if="activeDropdown === `model-provider-${index}`" class="select-options" :style="dropdownStyle">
                          <div class="select-option" @click="updateModel(index, 'api_provider', ''); activeDropdown = null">
                            <span>请选择</span>
                          </div>
                          <div 
                            v-for="p in apiProviders" 
                            :key="p.name" 
                            class="select-option"
                            @click="updateModel(index, 'api_provider', p.name); activeDropdown = null"
                          >
                            <span>{{ p.name }}</span>
                          </div>
                        </div>
                      </Transition>
                    </Teleport>
                    <Teleport to="body">
                      <div v-if="activeDropdown === `model-provider-${index}`" class="dropdown-overlay" @click.stop="activeDropdown = null"></div>
                    </Teleport>
                  </div>
                </div>
                <div class="form-group half">
                  <label>输入价格(元/M)</label>
                  <input 
                    type="number" 
                    class="form-input" 
                    :value="model.price_in ?? 0"
                    @input="updateModel(index, 'price_in', parseFloat(($event.target as HTMLInputElement).value))"
                    step="0.1" min="0"
                  />
                </div>
                <div class="form-group half">
                  <label>输出价格(元/M)</label>
                  <input 
                    type="number" 
                    class="form-input" 
                    :value="model.price_out ?? 0"
                    @input="updateModel(index, 'price_out', parseFloat(($event.target as HTMLInputElement).value))"
                    step="0.1" min="0"
                  />
                </div>
              </div>
              
              <!-- 模型测试 -->
              <div class="model-test-section">
                <button 
                  class="test-model-btn"
                  :class="{ 
                    testing: testingModels[model.name || ''], 
                    success: modelTestResults[model.name || '']?.connected === true,
                    error: modelTestResults[model.name || '']?.connected === false
                  }"
                  @click.stop="testModelConnection(model.name || '')"
                  :disabled="!model.name || testingModels[model.name || '']"
                  :title="getTestButtonTitle(model.name || '')"
                >
                  <Icon v-if="testingModels[model.name || '']" icon="lucide:loader-2" class="spinning" />
                  <Icon v-else-if="modelTestResults[model.name || '']?.connected === true" icon="lucide:check-circle" />
                  <Icon v-else-if="modelTestResults[model.name || '']?.connected === false" icon="lucide:x-circle" />
                  <Icon v-else icon="lucide:play-circle" />
                  <span>{{ getTestButtonText(model.name || '') }}</span>
                </button>
                <div v-if="modelTestResults[model.name || '']" class="test-result">
                  <div v-if="modelTestResults[model.name || '']?.connected" class="test-success">
                    <Icon icon="lucide:check-circle-2" />
                    <span>连接成功 · 响应时间: {{ modelTestResults[model.name || '']?.response_time?.toFixed(2) }}s</span>
                    <span v-if="modelTestResults[model.name || '']?.response_text" class="response-preview">
                      "{{ modelTestResults[model.name || '']?.response_text }}"
                    </span>
                  </div>
                  <div v-else class="test-error">
                    <Icon icon="lucide:alert-circle" />
                    <span>连接失败: {{ modelTestResults[model.name || '']?.error }}</span>
                  </div>
                </div>
              </div>
              
              <!-- 高级选项 -->
              <div class="advanced-section">
                <div class="advanced-header" @click="toggleModelAdvanced(index)">
                  <span>高级选项</span>
                  <Icon :icon="showModelAdvanced[index] ? 'lucide:chevron-up' : 'lucide:chevron-down'" />
                </div>
                <Transition name="slide">
                  <div v-if="showModelAdvanced[index]" class="advanced-content">
                    <div class="toggle-group">
                      <div class="toggle-item" @click="updateModel(index, 'force_stream_mode', !model.force_stream_mode)">
                        <div class="toggle-info">
                          <Icon icon="lucide:radio" />
                          <div>
                            <span class="toggle-label">强制流式</span>
                            <span class="toggle-hint">模型不支持非流式时启用</span>
                          </div>
                        </div>
                        <label class="switch" @click.stop>
                          <input type="checkbox" :checked="Boolean(model.force_stream_mode)" @change="updateModel(index, 'force_stream_mode', ($event.target as HTMLInputElement).checked)" />
                          <span class="slider"></span>
                        </label>
                      </div>
                      <div class="toggle-item" @click="updateModel(index, 'anti_truncation', !model.anti_truncation)">
                        <div class="toggle-info">
                          <Icon icon="lucide:shield-check" />
                          <div>
                            <span class="toggle-label">防截断</span>
                            <span class="toggle-hint">输出不完整时自动重试</span>
                          </div>
                        </div>
                        <label class="switch" @click.stop>
                          <input type="checkbox" :checked="Boolean(model.anti_truncation)" @change="updateModel(index, 'anti_truncation', ($event.target as HTMLInputElement).checked)" />
                          <span class="slider"></span>
                        </label>
                      </div>
                      <div class="toggle-item" @click="updateModel(index, 'enable_prompt_perturbation', !model.enable_prompt_perturbation)">
                        <div class="toggle-info">
                          <Icon icon="lucide:shuffle" />
                          <div>
                            <span class="toggle-label">提示词扰动</span>
                            <span class="toggle-hint">整合内容混淆和注意力优化</span>
                          </div>
                        </div>
                        <label class="switch" @click.stop>
                          <input type="checkbox" :checked="Boolean(model.enable_prompt_perturbation)" @change="updateModel(index, 'enable_prompt_perturbation', ($event.target as HTMLInputElement).checked)" />
                          <span class="slider"></span>
                        </label>
                      </div>
                      <div v-if="model.enable_prompt_perturbation" class="perturbation-options">
                        <div class="form-group">
                          <label>扰动强度</label>
                          <div class="custom-select" :class="{ open: activeDropdown === `model-perturbation-${index}` }">
                            <div class="select-trigger" @click.stop="toggleDropdown(`model-perturbation-${index}`, $event)">
                              <span>{{ {'light': '轻度', 'medium': '中度', 'heavy': '重度'}[model.perturbation_strength as string] || '轻度' }}</span>
                              <Icon icon="lucide:chevron-down" class="chevron" :class="{ rotated: activeDropdown === `model-perturbation-${index}` }" />
                            </div>
                            <Teleport to="body">
                              <Transition name="dropdown-fade">
                                <div v-if="activeDropdown === `model-perturbation-${index}`" class="select-options" :style="dropdownStyle">
                                  <div class="select-option" @click="updateModel(index, 'perturbation_strength', 'light'); activeDropdown = null">
                                    <span>轻度</span>
                                  </div>
                                  <div class="select-option" @click="updateModel(index, 'perturbation_strength', 'medium'); activeDropdown = null">
                                    <span>中度</span>
                                  </div>
                                  <div class="select-option" @click="updateModel(index, 'perturbation_strength', 'heavy'); activeDropdown = null">
                                    <span>重度</span>
                                  </div>
                                </div>
                              </Transition>
                            </Teleport>
                            <Teleport to="body">
                              <div v-if="activeDropdown === `model-perturbation-${index}`" class="dropdown-overlay" @click.stop="activeDropdown = null"></div>
                            </Teleport>
                          </div>
                        </div>
                        <div class="toggle-item compact">
                          <div class="toggle-info">
                            <span class="toggle-label">语义变体</span>
                          </div>
                          <label class="switch small" @click.stop>
                            <input type="checkbox" :checked="Boolean(model.enable_semantic_variants)" @change="updateModel(index, 'enable_semantic_variants', ($event.target as HTMLInputElement).checked)" />
                            <span class="slider"></span>
                          </label>
                        </div>
                      </div>
                    </div>
                  </div>
                </Transition>
              </div>
            </div>
          </Transition>
        </div>
      </div>
    </div>

    <!-- 任务配置面板 -->
    <div v-show="activeTab === 'tasks'" class="tab-panel">
      <div class="task-categories">
        <button 
          v-for="cat in taskCategories" 
          :key="cat.key"
          class="category-btn"
          :class="{ active: activeTaskCategory === cat.key }"
          @click="activeTaskCategory = cat.key"
        >
          <Icon :icon="cat.icon" />
          <span>{{ cat.name }}</span>
        </button>
      </div>
      
      <div class="task-list">
        <div 
          v-for="(task, taskKey) in filteredTasks" 
          :key="taskKey" 
          class="task-item"
        >
          <div class="task-header">
            <div class="task-info">
              <span class="task-name">{{ task.name }}</span>
              <span class="task-desc">{{ task.description }}</span>
            </div>
          </div>
          <div class="task-controls">
            <div class="control-row">
              <div class="control-group model-select">
                <label>模型 (可多选)</label>
                <div class="custom-select" :class="{ open: openTaskModelDropdown === taskKey }">
                  <div class="select-trigger" @click="toggleTaskModelDropdown(taskKey, $event)">
                    <span v-if="getTaskModel(taskKey).length === 0" class="placeholder">未配置</span>
                    <div v-else class="selected-tags">
                      <span 
                        v-for="model in getTaskModel(taskKey)" 
                        :key="model" 
                        class="selected-tag"
                      >
                        {{ model }}
                      </span>
                    </div>
                    <Icon icon="lucide:chevron-down" class="chevron" :class="{ rotated: openTaskModelDropdown === taskKey }" />
                  </div>
                  <Teleport to="body">
                    <Transition name="dropdown-fade">
                      <div v-if="openTaskModelDropdown === taskKey" class="select-options" :style="dropdownStyle">
                        <div 
                          v-for="m in models" 
                          :key="m.name" 
                          class="select-option"
                          @click.stop="toggleTaskModelSelection(taskKey, m.name!)"
                        >
                          <div class="checkbox" :class="{ checked: getTaskModel(taskKey).includes(m.name!) }">
                            <Icon icon="lucide:check" v-if="getTaskModel(taskKey).includes(m.name!)" />
                          </div>
                          <span>{{ m.name }}</span>
                        </div>
                      </div>
                    </Transition>
                  </Teleport>
                </div>
                <Teleport to="body">
                  <div v-if="openTaskModelDropdown === taskKey" class="dropdown-overlay" @click="openTaskModelDropdown = null"></div>
                </Teleport>
              </div>
              <div class="control-group small">
                <label>温度</label>
                <input 
                  type="number" 
                  class="form-input"
                  :value="getTaskTemperature(taskKey)"
                  @input="updateTaskTemperature(taskKey, parseFloat(($event.target as HTMLInputElement).value))"
                  step="0.1" min="0" max="2"
                  placeholder="0.7"
                />
              </div>
              <div class="control-group small">
                <label>最大Token</label>
                <input 
                  type="number" 
                  class="form-input"
                  :value="getTaskMaxTokens(taskKey)"
                  @input="updateTaskMaxTokens(taskKey, parseInt(($event.target as HTMLInputElement).value))"
                  min="1"
                  placeholder="800"
                />
              </div>
              <div class="control-group tiny">
                <label>并发</label>
                <input 
                  type="number" 
                  class="form-input"
                  :value="getTaskConcurrency(taskKey)"
                  @input="updateTaskConcurrency(taskKey, Number(($event.target as HTMLInputElement).value))"
                  min="1" max="100"
                  placeholder="1"
                />
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 添加提供商弹窗 -->
    <Teleport to="body">
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
            <!-- 预设模板选择 -->
            <div class="config-field">
              <label>提供商模板</label>
              <div class="searchable-select" :class="{ open: activeDropdown === 'preset-provider-select' }">
                <div class="select-trigger-with-search" @click.stop="toggleDropdown('preset-provider-select', $event)">
                  <Icon v-if="selectedPreset" :icon="selectedPreset.icon" class="preset-icon" />
                  <span>{{ selectedPreset ? selectedPreset.name : '选择预设模板' }}</span>
                  <small v-if="selectedPreset" class="preset-hint">{{ selectedPreset.description }}</small>
                  <Icon icon="lucide:chevron-down" class="chevron" :class="{ rotated: activeDropdown === 'preset-provider-select' }" />
                </div>
                <Teleport to="body">
                  <Transition name="dropdown-fade">
                    <div 
                      v-if="activeDropdown === 'preset-provider-select'" 
                      class="select-options searchable" 
                      :style="dropdownStyle"
                      @click.stop
                      @mousedown.stop
                    >
                      <div class="search-in-dropdown" @mousedown.stop>
                        <Icon icon="lucide:search" />
                        <input 
                          type="text" 
                          v-model="presetSearchQuery" 
                          placeholder="搜索提供商..." 
                          class="dropdown-search-input"
                          @click.stop
                          @mousedown.stop
                        />
                      </div>
                      <div class="options-list" @mousedown.stop>
                        <div 
                          v-for="preset in filteredProviderPresets" 
                          :key="preset.name" 
                          class="select-option with-icon"
                          :class="{ selected: selectedPreset?.name === preset.name }"
                          @click="selectPreset(preset); activeDropdown = null"
                        >
                          <Icon :icon="preset.icon" class="option-icon" />
                          <div class="option-content">
                            <span class="option-name">{{ preset.name }}</span>
                            <small class="option-desc">{{ preset.description }}</small>
                          </div>
                          <Icon v-if="selectedPreset?.name === preset.name" icon="lucide:check" class="check-icon" />
                        </div>
                        <div v-if="filteredProviderPresets.length === 0" class="no-results">
                          <Icon icon="lucide:search-x" />
                          <span>无匹配结果</span>
                        </div>
                      </div>
                    </div>
                  </Transition>
                </Teleport>
                <Teleport to="body">
                  <div 
                    v-if="activeDropdown === 'preset-provider-select'" 
                    class="dropdown-overlay" 
                    @click.stop="activeDropdown = null"
                  ></div>
                </Teleport>
              </div>
              <p class="field-tip">选择预设模板可自动填充 URL 和客户端类型，支持搜索</p>
            </div>
            
            <div class="divider">
              <span>配置详情</span>
            </div>
            
            <div class="manual-config">
              <div class="config-field">
                <label>提供商名称</label>
                <input v-model="newProvider.name" type="text" class="input" placeholder="例如: DeepSeek" />
              </div>
              <div class="config-field" v-if="newProvider.client_type !== 'bedrock'">
                <label>
                  API 地址
                  <span v-if="isUsingPreset" class="field-lock"><Icon icon="lucide:lock" /> 由模板指定</span>
                </label>
                <input 
                  v-model="newProvider.base_url" 
                  type="text" 
                  class="input" 
                  :class="{ disabled: isUsingPreset }"
                  :disabled="isUsingPreset"
                  placeholder="https://api.example.com/v1" 
                />
              </div>
              <div class="config-field">
                <label>
                  {{ newProvider.client_type === 'bedrock' ? 'AWS Access Key ID' : 'API 密钥' }}
                  <span class="field-hint">支持多行配置，系统将自动轮询</span>
                </label>
                <StringArrayEditor
                  :value="Array.isArray(newProvider.api_key) ? newProvider.api_key : (newProvider.api_key ? [String(newProvider.api_key)] : [])"
                  @update="newProvider.api_key = $event"
                  :placeholder="newProvider.client_type === 'bedrock' ? '你的 AWS Access Key ID' : '你的 API 密钥'"
                  add-button-text="添加备用密钥"
                  empty-text="请添加至少一个 API 密钥"
                  :is-secret="true"
                />
              </div>
              <div class="config-field">
                <label>
                  客户端类型
                  <span v-if="isUsingPreset" class="field-lock"><Icon icon="lucide:lock" /> 由模板指定</span>
                </label>
                <div class="custom-select" :class="{ open: activeDropdown === 'new-provider-client', disabled: isUsingPreset }">
                  <div 
                    class="select-trigger" 
                    :class="{ disabled: isUsingPreset }"
                    @click.stop="!isUsingPreset && toggleDropdown('new-provider-client', $event)"
                  >
                    <span>{{ getClientTypeLabel(newProvider.client_type) }}</span>
                    <Icon icon="lucide:chevron-down" class="chevron" :class="{ rotated: activeDropdown === 'new-provider-client' }" />
                  </div>
                  <Teleport to="body">
                    <Transition name="dropdown-fade">
                      <div v-if="activeDropdown === 'new-provider-client' && !isUsingPreset" class="select-options" :style="dropdownStyle">
                        <div class="select-option" @click="newProvider.client_type = 'openai'; activeDropdown = null">
                          <span>OpenAI 兼容</span>
                        </div>
                        <div class="select-option" @click="newProvider.client_type = 'aiohttp_gemini'; activeDropdown = null">
                          <span>Gemini（Google）</span>
                        </div>
                        <div class="select-option" @click="newProvider.client_type = 'bedrock'; activeDropdown = null">
                          <span>AWS Bedrock</span>
                        </div>
                      </div>
                    </Transition>
                  </Teleport>
                  <Teleport to="body">
                    <div v-if="activeDropdown === 'new-provider-client'" class="dropdown-overlay" @click.stop="activeDropdown = null"></div>
                  </Teleport>
                </div>
              </div>
              
              <!-- Bedrock 专用配置 -->
              <template v-if="newProvider.client_type === 'bedrock'">
                <div class="config-field">
                  <label>
                    AWS Secret Key
                    <span class="field-hint">IAM 角色模式下可留空</span>
                  </label>
                  <input 
                    v-model="newProvider.aws_secret_key" 
                    type="password" 
                    class="input" 
                    placeholder="你的 AWS Secret Access Key" 
                  />
                </div>
                <div class="config-field">
                  <label>AWS 区域</label>
                  <div class="custom-select" :class="{ open: activeDropdown === 'new-provider-region' }">
                    <div 
                      class="select-trigger" 
                      @click.stop="toggleDropdown('new-provider-region', $event)"
                    >
                      <span>{{ newProvider.aws_region || 'us-east-1' }}</span>
                      <Icon icon="lucide:chevron-down" class="chevron" :class="{ rotated: activeDropdown === 'new-provider-region' }" />
                    </div>
                    <Teleport to="body">
                      <Transition name="dropdown-fade">
                        <div v-if="activeDropdown === 'new-provider-region'" class="select-options" :style="dropdownStyle">
                          <div class="select-option" @click="newProvider.aws_region = 'us-east-1'; activeDropdown = null">
                            <span>us-east-1 (弗吉尼亚北部)</span>
                          </div>
                          <div class="select-option" @click="newProvider.aws_region = 'us-west-2'; activeDropdown = null">
                            <span>us-west-2 (俄勒冈)</span>
                          </div>
                          <div class="select-option" @click="newProvider.aws_region = 'eu-central-1'; activeDropdown = null">
                            <span>eu-central-1 (法兰克福)</span>
                          </div>
                          <div class="select-option" @click="newProvider.aws_region = 'eu-west-1'; activeDropdown = null">
                            <span>eu-west-1 (爱尔兰)</span>
                          </div>
                          <div class="select-option" @click="newProvider.aws_region = 'ap-southeast-1'; activeDropdown = null">
                            <span>ap-southeast-1 (新加坡)</span>
                          </div>
                          <div class="select-option" @click="newProvider.aws_region = 'ap-northeast-1'; activeDropdown = null">
                            <span>ap-northeast-1 (东京)</span>
                          </div>
                        </div>
                      </Transition>
                    </Teleport>
                    <Teleport to="body">
                      <div v-if="activeDropdown === 'new-provider-region'" class="dropdown-overlay" @click.stop="activeDropdown = null"></div>
                    </Teleport>
                  </div>
                </div>
              </template>
              
              <!-- 高级设置 -->
              <div class="advanced-settings-section">
                <div class="advanced-toggle" @click="showNewProviderAdvanced = !showNewProviderAdvanced">
                  <Icon :icon="showNewProviderAdvanced ? 'lucide:chevron-up' : 'lucide:chevron-down'" />
                  <span>高级设置</span>
                </div>
                <Transition name="slide">
                  <div v-if="showNewProviderAdvanced" class="advanced-fields">
                    <div class="config-field-row">
                      <div class="config-field half">
                        <label>最大重试次数</label>
                        <div class="number-input-wrapper">
                          <button 
                            class="number-btn" 
                            @click="newProvider.max_retry = Math.max(0, (newProvider.max_retry ?? 2) - 1)"
                            :disabled="(newProvider.max_retry ?? 2) <= 0"
                          >
                            <Icon icon="lucide:minus" />
                          </button>
                          <input 
                            type="number" 
                            class="form-input number-center" 
                            v-model.number="newProvider.max_retry"
                            min="0" max="10"
                            placeholder="2"
                          />
                          <button 
                            class="number-btn" 
                            @click="newProvider.max_retry = Math.min(10, (newProvider.max_retry ?? 2) + 1)"
                            :disabled="(newProvider.max_retry ?? 2) >= 10"
                          >
                            <Icon icon="lucide:plus" />
                          </button>
                        </div>
                        <p class="field-hint">请求失败时的最大重试次数</p>
                      </div>
                      <div class="config-field half">
                        <label>超时时间(秒)</label>
                        <div class="number-input-wrapper">
                          <button 
                            class="number-btn" 
                            @click="newProvider.timeout = Math.max(5, (newProvider.timeout ?? 30) - 5)"
                            :disabled="(newProvider.timeout ?? 30) <= 5"
                          >
                            <Icon icon="lucide:minus" />
                          </button>
                          <input 
                            type="number" 
                            class="form-input number-center" 
                            v-model.number="newProvider.timeout"
                            min="5" max="300" step="5"
                            placeholder="30"
                          />
                          <button 
                            class="number-btn" 
                            @click="newProvider.timeout = Math.min(300, (newProvider.timeout ?? 30) + 5)"
                            :disabled="(newProvider.timeout ?? 30) >= 300"
                          >
                            <Icon icon="lucide:plus" />
                          </button>
                        </div>
                        <p class="field-hint">单次请求的超时时间</p>
                      </div>
                    </div>
                    <div class="config-field-row">
                      <div class="config-field half">
                        <label>重试间隔(秒)</label>
                        <div class="number-input-wrapper">
                          <button 
                            class="number-btn" 
                            @click="newProvider.retry_interval = Math.max(1, (newProvider.retry_interval ?? 10) - 1)"
                            :disabled="(newProvider.retry_interval ?? 10) <= 1"
                          >
                            <Icon icon="lucide:minus" />
                          </button>
                          <input 
                            type="number" 
                            class="form-input number-center" 
                            v-model.number="newProvider.retry_interval"
                            min="1" max="60"
                            placeholder="10"
                          />
                          <button 
                            class="number-btn" 
                            @click="newProvider.retry_interval = Math.min(60, (newProvider.retry_interval ?? 10) + 1)"
                            :disabled="(newProvider.retry_interval ?? 10) >= 60"
                          >
                            <Icon icon="lucide:plus" />
                          </button>
                        </div>
                        <p class="field-hint">重试之间的等待时间</p>
                      </div>
                    </div>
                  </div>
                </Transition>
              </div>
            </div>
          </div>
          <div class="modal-footer">
            <button class="btn btn-secondary" @click="showAddProviderModal = false">取消</button>
            <button class="btn btn-primary" @click="confirmAddProvider" :disabled="!newProvider.name || (newProvider.client_type !== 'bedrock' && !newProvider.base_url)">
              <Icon icon="lucide:check" />
              添加
            </button>
          </div>
        </div>
      </div>
    </Teleport>

    <!-- 添加模型弹窗 -->
    <Teleport to="body">
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
              <div style="display: flex; gap: 8px;">
                <input 
                  v-model="newModel.model_identifier" 
                  type="text" 
                  class="input" 
                  placeholder="例如: deepseek-chat, gpt-4"
                  style="flex: 1;"
                />
              </div>
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
              <div class="custom-select" :class="{ open: activeDropdown === 'new-model-provider' }">
                <div class="select-trigger" @click.stop="toggleDropdown('new-model-provider', $event)">
                  <span>{{ newModel.api_provider || '请选择提供商' }}</span>
                  <Icon icon="lucide:chevron-down" class="chevron" :class="{ rotated: activeDropdown === 'new-model-provider' }" />
                </div>
                <Teleport to="body">
                  <Transition name="dropdown-fade">
                    <div v-if="activeDropdown === 'new-model-provider'" class="select-options" :style="dropdownStyle">
                      <div class="select-option" @click="newModel.api_provider = ''; fetchAvailableModels(); activeDropdown = null">
                        <span>请选择提供商</span>
                      </div>
                      <div 
                        v-for="provider in apiProviders" 
                        :key="provider.name" 
                        class="select-option"
                        @click="newModel.api_provider = provider.name || ''; fetchAvailableModels(); activeDropdown = null"
                      >
                        <span>{{ provider.name }}</span>
                      </div>
                    </div>
                  </Transition>
                </Teleport>
                <Teleport to="body">
                  <div v-if="activeDropdown === 'new-model-provider'" class="dropdown-overlay" @click.stop="activeDropdown = null"></div>
                </Teleport>
              </div>
            </div>
            
            <!-- 模型列表区域 -->
            <div v-if="newModel.api_provider && (fetchingModels || availableModels.length > 0 || fetchModelsError)" 
                 class="models-section">
              <div v-if="fetchingModels" class="loading-models">
                <Icon icon="lucide:loader-2" class="spinning" />
                <span>正在获取可用模型...</span>
              </div>
              <div v-else-if="fetchModelsError" class="fetch-error">
                <Icon icon="lucide:alert-circle" />
                <span>{{ fetchModelsError }}</span>
                <button class="btn-retry" @click="fetchAvailableModels">
                  <Icon icon="lucide:refresh-cw" />
                  重试
                </button>
              </div>
              <div v-else-if="availableModels.length > 0" class="available-models">
                <div class="models-header">
                  <span>可用模型 ({{ availableModels.length }})</span>
                  <button class="btn-refresh" @click="fetchAvailableModels" title="刷新列表">
                    <Icon icon="lucide:refresh-cw" />
                  </button>
                </div>
                <div class="models-list">
                  <button
                    v-for="model in availableModels"
                    :key="model.id"
                    class="model-option"
                    :class="{ active: newModel.model_identifier === model.id }"
                    @click="newModel.model_identifier = model.id; newModel.name = model.name"
                  >
                    <Icon icon="lucide:bot" />
                    <div class="model-info">
                      <span class="model-id">{{ model.id }}</span>
                      <span v-if="model.name !== model.id" class="model-name">{{ model.name }}</span>
                    </div>
                    <Icon v-if="newModel.model_identifier === model.id" icon="lucide:check" class="check-icon" />
                  </button>
                </div>
              </div>
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

            <!-- 高级参数 -->
            <div class="advanced-params-section">
              <div class="advanced-header" @click="showAddModelAdvanced = !showAddModelAdvanced">
                <div class="advanced-header-left">
                  <Icon :icon="showAddModelAdvanced ? 'lucide:chevron-down' : 'lucide:chevron-right'" />
                  <span>高级参数 (可选)</span>
                </div>
                <span class="advanced-hint">{{ showAddModelAdvanced ? '收起' : '展开' }}</span>
              </div>
              
              <div v-show="showAddModelAdvanced" class="advanced-params-content">
                <div class="config-field">
                  <label>
                    最大输出 Token
                    <span class="field-hint">留空使用默认值</span>
                  </label>
                  <input v-model.number="newModel.max_tokens" type="number" class="input" min="1" placeholder="例如: 4096" />
                </div>
                <div class="config-field">
                  <label>
                    温度 (temperature)
                    <span class="field-hint">0-2，留空使用默认值</span>
                  </label>
                  <div class="slider-with-input">
                    <input 
                      type="range" 
                      class="temp-slider"
                      :value="newModel.temperature ?? 0.7" 
                      @input="newModel.temperature = parseFloat(($event.target as HTMLInputElement).value)"
                      min="0" 
                      max="2" 
                      step="0.1"
                    />
                    <input 
                      v-model.number="newModel.temperature" 
                      type="number" 
                      class="input temp-input" 
                      step="0.1" 
                      min="0" 
                      max="2" 
                      placeholder="0.7" 
                    />
                  </div>
                </div>

                <div class="feature-toggles">
                  <div class="feature-toggle" @click="newModel.anti_truncation = !newModel.anti_truncation">
                    <div class="feature-toggle-info">
                      <div class="feature-toggle-icon" :class="{ active: newModel.anti_truncation }">
                        <Icon icon="lucide:shield-check" />
                      </div>
                      <div class="feature-toggle-text">
                        <span class="feature-name">反截断</span>
                        <span class="feature-hint">防止模型输出被截断</span>
                      </div>
                    </div>
                    <label class="switch small" @click.stop>
                      <input 
                        type="checkbox" 
                        v-model="newModel.anti_truncation"
                      />
                      <span class="slider"></span>
                    </label>
                  </div>
                  <div class="feature-toggle" @click="newModel.enable_prompt_perturbation = !newModel.enable_prompt_perturbation">
                    <div class="feature-toggle-info">
                      <div class="feature-toggle-icon" :class="{ active: newModel.enable_prompt_perturbation }">
                        <Icon icon="lucide:shuffle" />
                      </div>
                      <div class="feature-toggle-text">
                        <span class="feature-name">内容混淆</span>
                        <span class="feature-hint">对提示词进行微扰动，增加输出多样性</span>
                      </div>
                    </div>
                    <label class="switch small" @click.stop>
                      <input 
                        type="checkbox" 
                        v-model="newModel.enable_prompt_perturbation"
                      />
                      <span class="slider"></span>
                    </label>
                  </div>
                  
                  <div v-if="newModel.enable_prompt_perturbation" class="perturbation-sub-options">
                    <div class="config-field">
                      <label>扰动强度</label>
                      <div class="custom-select" :class="{ open: activeDropdown === 'new-model-perturbation' }">
                        <div class="select-trigger" @click.stop="toggleDropdown('new-model-perturbation', $event)">
                          <span>{{ {'light': '轻度', 'medium': '中度', 'heavy': '重度'}[newModel.perturbation_strength as string] || '轻度' }}</span>
                          <Icon icon="lucide:chevron-down" class="chevron" :class="{ rotated: activeDropdown === 'new-model-perturbation' }" />
                        </div>
                        <Teleport to="body">
                          <Transition name="dropdown-fade">
                            <div v-if="activeDropdown === 'new-model-perturbation'" class="select-options" :style="dropdownStyle">
                              <div class="select-option" @click="newModel.perturbation_strength = 'light'; activeDropdown = null">
                                <span>轻度</span>
                              </div>
                              <div class="select-option" @click="newModel.perturbation_strength = 'medium'; activeDropdown = null">
                                <span>中度</span>
                              </div>
                              <div class="select-option" @click="newModel.perturbation_strength = 'heavy'; activeDropdown = null">
                                <span>重度</span>
                              </div>
                            </div>
                          </Transition>
                        </Teleport>
                        <Teleport to="body">
                          <div v-if="activeDropdown === 'new-model-perturbation'" class="dropdown-overlay" @click.stop="activeDropdown = null"></div>
                        </Teleport>
                      </div>
                    </div>
                    <div class="feature-toggle compact" @click="newModel.enable_semantic_variants = !newModel.enable_semantic_variants">
                      <div class="feature-toggle-info">
                        <span class="feature-name">语义变体</span>
                      </div>
                      <label class="switch small" @click.stop>
                        <input 
                          type="checkbox" 
                          v-model="newModel.enable_semantic_variants"
                        />
                        <span class="slider"></span>
                      </label>
                    </div>
                  </div>
                </div>
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
    </Teleport>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted, onUnmounted } from 'vue'
import { Icon } from '@iconify/vue'
import StringArrayEditor from './StringArrayEditor.vue'
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
  perturbation_strength?: string
  enable_semantic_variants?: boolean
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

// 导航状态
const activeTab = ref<'providers' | 'models' | 'tasks'>('providers')
const searchQuery = ref('')
const selectedProvider = ref<number | null>(0)
const selectedModel = ref<number | null>(null)
const activeTaskCategory = ref('core')

// 标签页定义
const tabs = computed(() => [
  { key: 'providers' as const, name: '提供商', icon: 'lucide:cloud', count: apiProviders.value.length },
  { key: 'models' as const, name: '模型', icon: 'lucide:cpu', count: models.value.length },
  { key: 'tasks' as const, name: '任务配置', icon: 'lucide:list-checks', count: undefined }
])

// 任务分类
const taskCategories = [
  { key: 'core', name: '核心功能', icon: 'lucide:star' },
  { key: 'media', name: '多媒体', icon: 'lucide:image' },
  { key: 'memory', name: '记忆系统', icon: 'lucide:brain' },
  { key: 'lpmm', name: '知识库', icon: 'lucide:database' },
  { key: 'other', name: '其他', icon: 'lucide:more-horizontal' }
]

// 任务分类映射
const taskCategoryMap: Record<string, string> = {
  'utils': 'core',
  'utils_small': 'core',
  'replyer': 'core',
  'planner': 'core',
  'emotion': 'core',
  'mood': 'core',
  'maizone': 'core',
  'tool_use': 'core',
  'anti_injection': 'core',
  'vlm': 'media',
  'emoji_vlm': 'media',
  'utils_video': 'media',
  'voice': 'media',
  'embedding': 'memory',
  'memory_short_term_builder': 'memory',
  'memory_short_term_decider': 'memory',
  'memory_long_term_builder': 'memory',
  'memory_judge': 'memory',
  'lpmm_entity_extract': 'lpmm',
  'lpmm_rdf_build': 'lpmm',
  'lpmm_qa': 'lpmm',
  'schedule_generator': 'other',
  'monthly_plan_generator': 'other',
  'relationship_tracker': 'other'
}

// 状态
const showModelAdvanced = ref<Record<number, boolean>>({})
const showAddProviderModal = ref(false)
const showAddModelModal = ref(false)
const showAddModelAdvanced = ref(false)
const activeDropdown = ref<string | null>(null)
const dropdownStyle = ref<Record<string, string>>({})

function updateDropdownPosition(trigger: HTMLElement) {
  const rect = trigger.getBoundingClientRect()
  dropdownStyle.value = {
    top: `${rect.bottom}px`,
    left: `${rect.left}px`,
    width: `${rect.width}px`,
    position: 'fixed',
    zIndex: '9999',
    marginTop: '4px'
  }
}

function toggleDropdown(id: string, event?: Event) {
  if (activeDropdown.value === id) {
    activeDropdown.value = null
  } else {
    if (event) {
      updateDropdownPosition(event.currentTarget as HTMLElement)
    }
    activeDropdown.value = id
  }
}

// 新提供商表单
const newProvider = ref({
  name: '',
  base_url: '',
  api_key: [] as string[],
  client_type: 'openai',
  max_retry: 2,
  timeout: 30,
  retry_interval: 10,
  // Bedrock 额外参数
  aws_secret_key: '',
  aws_region: 'us-east-1'
})

// 预设模板相关状态
const selectedPreset = ref<typeof providerPresets[0] | null>(null)
const presetSearchQuery = ref('')
const showNewProviderAdvanced = ref(false)

// 是否正在使用预设模板（非自定义）
const isUsingPreset = computed(() => {
  return selectedPreset.value !== null && selectedPreset.value.name !== '自定义'
})

// 过滤后的预设模板列表
const filteredProviderPresets = computed(() => {
  if (!presetSearchQuery.value) return providerPresets
  const query = presetSearchQuery.value.toLowerCase()
  return providerPresets.filter(p => 
    p.name.toLowerCase().includes(query) ||
    p.description.toLowerCase().includes(query)
  )
})

// 新模型表单
const newModel = ref({
  model_identifier: '',
  name: '',
  api_provider: '',
  price_in: 0,
  price_out: 0,
  max_tokens: undefined as number | undefined,
  temperature: undefined as number | undefined,
  anti_truncation: false,
  enable_prompt_perturbation: false,
  perturbation_strength: 'light',
  enable_semantic_variants: false
})

// 计算 API 提供商列表
const apiProviders = computed(() => {
  if (props.editedValues && 'api_providers' in props.editedValues) {
    return props.editedValues['api_providers'] as ApiProvider[]
  }
  const data = props.parsedData
  if (Array.isArray(data.api_providers)) {
    return data.api_providers as ApiProvider[]
  }
  return []
})

// 计算模型列表
const models = computed(() => {
  if (props.editedValues && 'models' in props.editedValues) {
    return props.editedValues['models'] as Model[]
  }
  const data = props.parsedData
  if (Array.isArray(data.models)) {
    return data.models as Model[]
  }
  return []
})

// 过滤后的模型列表
const filteredModels = computed(() => {
  if (!searchQuery.value) return models.value
  const query = searchQuery.value.toLowerCase()
  return models.value.filter(m => 
    (m.name?.toLowerCase().includes(query)) ||
    (m.model_identifier?.toLowerCase().includes(query)) ||
    (m.api_provider?.toLowerCase().includes(query))
  )
})

// 过滤后的任务列表
const filteredTasks = computed(() => {
  const filtered: Record<string, { name: string; description: string }> = {}
  for (const [key, value] of Object.entries(modelTaskConfigs)) {
    const category = taskCategoryMap[key] || 'other'
    if (category === activeTaskCategory.value) {
      filtered[key] = value
    }
  }
  return filtered
})

// 方法
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
    'aws': 'simple-icons:amazonaws',
    'bedrock': 'simple-icons:amazonaws',
    'amazon': 'simple-icons:amazonaws',
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
    'aiohttp_gemini': 'Gemini（Google）',
    'bedrock': 'AWS Bedrock'
  }
  return labels[clientType || 'openai'] || 'OpenAI 兼容'
}

function getProviderModelCount(providerName?: string): number {
  if (!providerName) return 0
  return models.value.filter(m => m.api_provider === providerName).length
}

function updateProvider(index: number, key: string, value: unknown) {
  const updatedProvider = { ...apiProviders.value[index], [key]: value }
  const newProviders = [...apiProviders.value]
  newProviders[index] = updatedProvider
  emit('update', 'api_providers', newProviders)
}

// 更新提供商的 extra_params 中的某个字段
function updateProviderExtraParam(index: number, key: string, value: unknown) {
  const provider = apiProviders.value[index]
  if (!provider) return
  
  const currentExtraParams = (provider.extra_params as Record<string, unknown>) || {}
  const updatedExtraParams = { ...currentExtraParams, [key]: value }
  
  // 如果值为空字符串，删除该字段
  if (value === '') {
    delete updatedExtraParams[key]
  }
  
  const updatedProvider = { ...provider, extra_params: updatedExtraParams }
  const newProviders = [...apiProviders.value]
  newProviders[index] = updatedProvider
  emit('update', 'api_providers', newProviders)
}

function updateModel(index: number, key: string, value: unknown) {
  const updatedModel = { ...models.value[index], [key]: value }
  const newModels = [...models.value]
  newModels[index] = updatedModel
  emit('update', 'models', newModels)
}

function selectPreset(preset: typeof providerPresets[0]) {
  selectedPreset.value = preset
  newProvider.value = {
    name: preset.name === '自定义' ? '' : preset.name,
    base_url: preset.base_url,
    api_key: [] as string[],
    client_type: preset.client_type,
    max_retry: newProvider.value.max_retry ?? 2,
    timeout: preset.client_type === 'bedrock' ? 60 : (newProvider.value.timeout ?? 30),
    retry_interval: newProvider.value.retry_interval ?? 10,
    // Bedrock 额外参数
    aws_secret_key: '',
    aws_region: 'us-east-1'
  }
  presetSearchQuery.value = ''
}

function confirmAddProvider() {
  // Bedrock 不需要 base_url，其他类型需要
  const isBedrock = newProvider.value.client_type === 'bedrock'
  if (!newProvider.value.name || (!isBedrock && !newProvider.value.base_url)) return
  
  // 构建提供商对象
  const providerData: Record<string, unknown> = {
    name: newProvider.value.name,
    base_url: newProvider.value.base_url,
    api_key: newProvider.value.api_key,
    client_type: newProvider.value.client_type,
    max_retry: newProvider.value.max_retry ?? 2,
    timeout: newProvider.value.timeout ?? 30,
    retry_interval: newProvider.value.retry_interval ?? 10
  }
  
  // 如果是 Bedrock，添加 extra_params
  if (isBedrock) {
    const extraParams: Record<string, unknown> = {
      region: newProvider.value.aws_region || 'us-east-1'
    }
    // 只有在提供了 secret key 时才添加
    if (newProvider.value.aws_secret_key) {
      extraParams.aws_secret_key = newProvider.value.aws_secret_key
    }
    providerData.extra_params = extraParams
  }
  
  const newProviders = [...apiProviders.value, providerData]
  
  emit('update', 'api_providers', newProviders)
  
  showAddProviderModal.value = false
  // 重置表单
  newProvider.value = { 
    name: '', 
    base_url: '', 
    api_key: [] as string[], 
    client_type: 'openai', 
    max_retry: 2, 
    timeout: 30, 
    retry_interval: 10,
    aws_secret_key: '',
    aws_region: 'us-east-1'
  }
  selectedPreset.value = null
  presetSearchQuery.value = ''
  showNewProviderAdvanced.value = false
  
  // 展开新添加的提供商
  selectedProvider.value = newProviders.length - 1
}

function removeProvider(index: number) {
  if (!confirm('确定要删除此提供商吗？')) return
  
  const newProviders = apiProviders.value.filter((_, i) => i !== index)
  emit('update', 'api_providers', newProviders)
  
  if (selectedProvider.value === index) {
    selectedProvider.value = null
  }
}

function confirmAddModel() {
  if (!newModel.value.model_identifier || !newModel.value.name) return
  
  // 构建新模型对象
  const modelData: Model = {
    model_identifier: newModel.value.model_identifier,
    name: newModel.value.name,
    api_provider: newModel.value.api_provider,
    price_in: newModel.value.price_in,
    price_out: newModel.value.price_out
  }
  
  // 添加高级参数到 extra_params
  const extraParams: Record<string, unknown> = {}
  if (newModel.value.max_tokens !== undefined && newModel.value.max_tokens > 0) {
    extraParams.max_tokens = newModel.value.max_tokens
  }
  if (newModel.value.temperature !== undefined && newModel.value.temperature >= 0) {
    extraParams.temperature = newModel.value.temperature
  }
  
  if (Object.keys(extraParams).length > 0) {
    modelData.extra_params = extraParams
  }
  
  // 添加反截断和内容混淆选项
  if (newModel.value.anti_truncation) {
    modelData.anti_truncation = true
  }
  if (newModel.value.enable_prompt_perturbation) {
    modelData.enable_prompt_perturbation = true
  }
  
  const newModels = [...models.value, modelData]
  
  emit('update', 'models', newModels)
  
  showAddModelModal.value = false
  showAddModelAdvanced.value = false
  availableModels.value = []
  fetchModelsError.value = null
  newModel.value = { 
    model_identifier: '', 
    name: '', 
    api_provider: '', 
    price_in: 0, 
    price_out: 0,
    max_tokens: undefined,
    temperature: undefined,
    anti_truncation: false,
    enable_prompt_perturbation: false,
    perturbation_strength: 'light',
    enable_semantic_variants: false
  }
  
  // 展开新添加的模型
  selectedModel.value = newModels.length - 1
}

function removeModel(index: number) {
  if (!confirm('确定要删除此模型吗？')) return
  
  const newModels = models.value.filter((_, i) => i !== index)
  emit('update', 'models', newModels)
  
  if (selectedModel.value === index) {
    selectedModel.value = null
  }
}

// 任务模型配置
function getTaskModel(taskKey: string): string[] {
  const key = `model_task_config.${taskKey}.model_list`
  if (props.editedValues && key in props.editedValues) {
    return props.editedValues[key] as string[]
  }

  const data = props.parsedData
  const taskConfig = data.model_task_config as Record<string, Record<string, unknown>> | undefined
  if (!taskConfig || !taskConfig[taskKey]) return []
  
  const modelList = taskConfig[taskKey].model_list as string[] | undefined
  return modelList || []
}

function updateTaskModel(taskKey: string, modelNames: string[]) {
  emit('update', `model_task_config.${taskKey}.model_list`, modelNames)
}

// 任务模型下拉框状态
const openTaskModelDropdown = ref<string | null>(null)

function toggleTaskModelDropdown(taskKey: string, event?: Event) {
  if (openTaskModelDropdown.value === taskKey) {
    openTaskModelDropdown.value = null
  } else {
    if (event) {
      updateDropdownPosition(event.currentTarget as HTMLElement)
    }
    openTaskModelDropdown.value = taskKey
  }
}

function toggleTaskModelSelection(taskKey: string, modelName: string) {
  const currentModels = getTaskModel(taskKey)
  const index = currentModels.indexOf(modelName)
  let newModels: string[]
  if (index >= 0) {
    newModels = currentModels.filter(m => m !== modelName)
  } else {
    newModels = [...currentModels, modelName]
  }
  updateTaskModel(taskKey, newModels)
}

// 获取任务温度
function getTaskTemperature(taskKey: string): number | undefined {
  const key = `model_task_config.${taskKey}.temperature`
  if (props.editedValues && key in props.editedValues) {
    return props.editedValues[key] as number | undefined
  }

  const data = props.parsedData
  const taskConfig = data.model_task_config as Record<string, Record<string, unknown>> | undefined
  if (!taskConfig || !taskConfig[taskKey]) return undefined
  return taskConfig[taskKey].temperature as number | undefined
}

// 更新任务温度
function updateTaskTemperature(taskKey: string, temp: number) {
  if (isNaN(temp)) return
  emit('update', `model_task_config.${taskKey}.temperature`, temp)
}

// 获取任务最大token
function getTaskMaxTokens(taskKey: string): number | undefined {
  const key = `model_task_config.${taskKey}.max_tokens`
  if (props.editedValues && key in props.editedValues) {
    return props.editedValues[key] as number | undefined
  }

  const data = props.parsedData
  const taskConfig = data.model_task_config as Record<string, Record<string, unknown>> | undefined
  if (!taskConfig || !taskConfig[taskKey]) return undefined
  return taskConfig[taskKey].max_tokens as number | undefined
}

// 更新任务最大token
function updateTaskMaxTokens(taskKey: string, tokens: number) {
  if (isNaN(tokens) || tokens < 1) return
  emit('update', `model_task_config.${taskKey}.max_tokens`, tokens)
}

// 获取任务并发数
function getTaskConcurrency(taskKey: string): number {
  const key = `model_task_config.${taskKey}.concurrency_count`
  if (props.editedValues && key in props.editedValues) {
    return (props.editedValues[key] as number | undefined) ?? 1
  }

  const data = props.parsedData
  const taskConfig = data.model_task_config as Record<string, Record<string, unknown>> | undefined
  if (!taskConfig || !taskConfig[taskKey]) return 1
  
  const concurrency = taskConfig[taskKey].concurrency_count as number | undefined
  return concurrency ?? 1
}

// 更新任务并发数
function updateTaskConcurrency(taskKey: string, count: number) {
  if (count < 1) count = 1
  if (count > 100) count = 100
  emit('update', `model_task_config.${taskKey}.concurrency_count`, count)
}

// 模型测试相关
const testingModels = ref<Record<string, boolean>>({})
const modelTestResults = ref<Record<string, {
  connected: boolean
  response_time?: number
  response_text?: string
  error?: string
}>>({})

// 获取模型列表相关
const fetchingModels = ref(false)
const availableModels = ref<Array<{ id: string; name: string }>>([])
const fetchModelsError = ref<string | null>(null)

// 测试模型连通性
async function testModelConnection(modelName: string) {
  console.log('🧪 测试模型连通性:', modelName)
  if (!modelName) {
    console.warn('⚠️ 模型名称为空')
    return
  }
  
  // 导入 API 函数
  const { testModelConnection: testAPI } = await import('@/api')
  
  // 标记为测试中
  testingModels.value[modelName] = true
  delete modelTestResults.value[modelName]
  console.log('📡 开始测试模型:', modelName)
  
  try {
    const response = await testAPI(modelName)
    console.log('✅ 测试响应:', response)
    
    if (response.success && response.data) {
      modelTestResults.value[modelName] = {
        connected: response.data.connected,
        response_time: response.data.response_time,
        response_text: response.data.response_text,
        error: response.data.error
      }
    } else {
      modelTestResults.value[modelName] = {
        connected: false,
        error: response.error || '测试失败'
      }
    }
  } catch (error: any) {
    console.error('❌ 测试出错:', error)
    modelTestResults.value[modelName] = {
      connected: false,
      error: error.message || '网络错误'
    }
  } finally {
    testingModels.value[modelName] = false
    console.log('🏁 测试完成:', modelName, modelTestResults.value[modelName])
  }
}

// 获取测试按钮标题
function getTestButtonTitle(modelName: string): string {
  if (!modelName) return '请先配置模型名称'
  if (testingModels.value[modelName]) return '测试中...'
  if (modelTestResults.value[modelName]?.connected === true) return '连接成功，点击重新测试'
  if (modelTestResults.value[modelName]?.connected === false) return '连接失败，点击重试'
  return '测试模型连通性'
}

// 获取测试按钮文本
function getTestButtonText(modelName: string): string {
  if (testingModels.value[modelName]) return '测试中'
  if (modelTestResults.value[modelName]) return '重新测试'
  return '测试连接'
}

// 获取可用模型列表
async function fetchAvailableModels() {
  
  // 检查是否在添加模型弹窗中选择了提供商
  let targetProviderName: string | null = null
  
  if (showAddModelModal.value && newModel.value.api_provider) {
    // 在添加模型弹窗中，使用 newModel.api_provider
    targetProviderName = newModel.value.api_provider
  } else if (selectedProvider.value !== null) {
    // 在提供商列表中，使用 selectedProvider.value
    const provider = apiProviders.value[selectedProvider.value]
    targetProviderName = provider?.name || null
  }
  
  if (!targetProviderName) {
    const errorMsg = '请先选择一个提供商'
    console.error('❌', errorMsg)
    fetchModelsError.value = errorMsg
    return
  }
  
  // 查找提供商配置
  const provider = apiProviders.value.find(p => p.name === targetProviderName)
  
  if (!provider || !provider.name || !provider.base_url) {
    const errorMsg = '提供商配置不完整（需要名称和地址）'
    fetchModelsError.value = errorMsg
    return
  }
  
  // 获取API密钥
  let apiKey = ''
  if (Array.isArray(provider.api_key)) {
    apiKey = provider.api_key[0] || ''
  } else {
    apiKey = String(provider.api_key || '')
  }
  
  if (!apiKey && provider.client_type !== 'ollama') {
    const errorMsg = '请先配置API密钥'
    console.warn('⚠️', errorMsg)
    fetchModelsError.value = errorMsg
    return
  }
  
  fetchingModels.value = true
  fetchModelsError.value = null
  availableModels.value = []
  
  try {
    const { getAvailableModels } = await import('@/api')
    
    const requestParams = {
      provider_name: provider.name,
      base_url: provider.base_url,
      api_key: apiKey,
      client_type: provider.client_type || 'openai'
    }
    console.log('📤 发送请求参数:', requestParams)
    
    const response = await getAvailableModels(requestParams)
    console.log('📥 收到响应:', response)
    
    if (response.success && response.data) {
      const modelsData = response.data
      
      if (modelsData.success && modelsData.models) {
        availableModels.value = modelsData.models.map((m: { id: string; name: string }) => ({
          id: m.id,
          name: m.name || m.id
        }))
        console.log(`✅ 成功获取 ${availableModels.value.length} 个模型:`, availableModels.value.slice(0, 5))
        
        // 如果正在添加新模型，自动填充第一个模型
        if (showAddModelModal.value && availableModels.value.length > 0 && !newModel.value.model_identifier) {
          const firstModel = availableModels.value[0]
          if (firstModel) {
            newModel.value.model_identifier = firstModel.id
            newModel.value.name = firstModel.name
            console.log('✨ 自动填充第一个模型:', firstModel)
          }
        }
      } else {
        fetchModelsError.value = modelsData.error || '获取模型列表失败'
        console.error('❌ 获取模型列表失败:', modelsData.error)
      }
    } else {
      fetchModelsError.value = response.error || '获取模型列表失败'
      console.error('❌ 获取模型列表失败:', response.error)
    }
  } catch (error: any) {
    fetchModelsError.value = `请求失败: ${error.message || String(error)}`
    console.error('❌ 获取模型列表异常:', error)
  } finally {
    fetchingModels.value = false
    console.log('🏁 获取模型列表完成')
  }
}

// 监听滚动和调整大小以关闭下拉框
function closeDropdowns(event?: Event) {
  // 如果滚动发生在下拉框内部（options-list），则不关闭
  if (event && event.target) {
    const target = event.target as HTMLElement
    if (target.classList?.contains('options-list') || 
        target.closest?.('.options-list') ||
        target.closest?.('.select-options')) {
      return
    }
  }
  activeDropdown.value = null
  openTaskModelDropdown.value = null
}

onMounted(() => {
  window.addEventListener('resize', closeDropdowns)
  window.addEventListener('scroll', closeDropdowns, true)
})

onUnmounted(() => {
  window.removeEventListener('resize', closeDropdowns)
  window.removeEventListener('scroll', closeDropdowns, true)
})

// 初始化
watch(() => props.parsedData, () => {
  // 如果有提供商，默认展开第一个
  if (apiProviders.value.length > 0 && selectedProvider.value === null) {
    selectedProvider.value = 0
  }
}, { immediate: true })
</script>

<style scoped>
.model-config-editor {
  /* Map MD3 variables to component variables */
  --bg-primary: var(--md-sys-color-surface);
  --bg-secondary: var(--md-sys-color-surface-container);
  --bg-tertiary: var(--md-sys-color-surface-container-high);
  --bg-hover: var(--md-sys-color-surface-container-highest);
  
  --text-primary: var(--md-sys-color-on-surface);
  --text-secondary: var(--md-sys-color-on-surface-variant);
  --text-tertiary: var(--md-sys-color-outline);
  
  --border-color: var(--md-sys-color-outline-variant);
  
  --primary: var(--md-sys-color-primary);
  --primary-bg: var(--md-sys-color-primary-container);
  
  --radius-sm: var(--md-sys-shape-corner-extra-small);
  --radius: var(--md-sys-shape-corner-medium);
  --radius-lg: var(--md-sys-shape-corner-large);
  
  --transition-fast: 0.2s ease;
  --warning: #f59e0b;
  --error: var(--md-sys-color-error);

  display: flex;
  flex-direction: column;
  height: 100%;
  background: var(--bg-primary);
  border-radius: var(--radius-lg);
}

/* 导航头部 */
.nav-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  gap: 16px;
  flex-wrap: wrap;
  background: var(--bg-secondary);
  border-radius: var(--radius-lg);
  margin: 12px;
  margin-bottom: 0;
}

.nav-tabs {
  display: flex;
  gap: 4px;
}

.nav-tab {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 16px;
  background: transparent;
  border: none;
  border-radius: 20px;
  color: var(--text-secondary);
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.15s ease;
}

.nav-tab:hover {
  background: var(--bg-hover);
  color: var(--text-primary);
}

.nav-tab.active {
  background: var(--primary);
  color: white;
}

.tab-badge {
  padding: 2px 6px;
  background: rgba(255, 255, 255, 0.2);
  border-radius: 10px;
  font-size: 11px;
  font-weight: 600;
}

.nav-tab:not(.active) .tab-badge {
  background: var(--bg-hover);
}

.nav-actions {
  display: flex;
  align-items: center;
  gap: 10px;
}

.search-box {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 16px;
  background: var(--bg-primary);
  border: 1px solid var(--border-color);
  border-radius: 20px;
  color: var(--text-tertiary);
  transition: all 0.2s;
}

.search-box:focus-within {
  border-color: var(--primary);
  box-shadow: 0 0 0 2px var(--primary-bg);
}

.search-input {
  width: 160px;
  border: none;
  background: transparent;
  color: var(--text-primary);
  font-size: 13px;
  outline: none;
}

.search-input::placeholder {
  color: var(--text-tertiary);
}

.clear-search {
  display: flex;
  padding: 2px;
  background: transparent;
  border: none;
  color: var(--text-tertiary);
  cursor: pointer;
}

.clear-search:hover {
  color: var(--text-primary);
}

.add-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 16px;
  background: var(--primary);
  border: none;
  border-radius: 20px;
  color: white;
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.15s ease;
}

.add-btn:hover {
  background: var(--primary-hover);
}

/* 面板 */
.tab-panel {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
  background: var(--bg-secondary);
  border-radius: var(--radius-lg);
  margin: 12px;
}

/* 空状态 */
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px 20px;
  text-align: center;
}

.empty-icon {
  width: 64px;
  height: 64px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--bg-secondary);
  border-radius: 50%;
  color: var(--text-tertiary);
  font-size: 28px;
  margin-bottom: 16px;
}

.empty-state h3 {
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0 0 8px 0;
}

.empty-state p {
  font-size: 13px;
  color: var(--text-tertiary);
  margin: 0 0 20px 0;
}

/* 列表项通用样式 */
.provider-list,
.model-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.provider-item,
.model-item {
  background: var(--bg-secondary);
  border: 1px solid var(--border-color);
  border-radius: var(--radius);
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
  position: relative;
}

.provider-item:hover,
.model-item:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 20px -4px rgba(0, 0, 0, 0.1);
  border-color: var(--primary);
  background: linear-gradient(to bottom right, var(--bg-secondary), var(--bg-primary));
  z-index: 10;
}

.provider-item.active,
.model-item.active {
  border-color: var(--primary);
  box-shadow: 0 0 0 2px var(--primary-bg);
  transform: translateY(-2px);
  z-index: 10;
}

.provider-row,
.model-row {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 16px 18px;
  cursor: pointer;
  transition: background 0.15s ease;
  border-radius: var(--radius);
}

.provider-item.active .provider-row,
.model-item.active .model-row {
  border-bottom-left-radius: 0;
  border-bottom-right-radius: 0;
}

.provider-row:hover,
.model-row:hover {
  background: var(--bg-hover);
}

.provider-icon,
.model-icon {
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, var(--primary), var(--tertiary));
  border-radius: var(--radius);
  color: var(--on-primary);
  font-size: 18px;
  flex-shrink: 0;
}

.model-icon {
  background: linear-gradient(135deg, var(--secondary), var(--tertiary));
  color: var(--on-secondary);
}

.provider-main,
.model-main {
  flex: 1;
  min-width: 0;
}

.provider-name,
.model-name {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 4px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.provider-meta,
.model-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.meta-tag {
  padding: 2px 10px;
  background: var(--bg-primary);
  border: 1px solid var(--border-color);
  border-radius: 12px;
  font-size: 11px;
  color: var(--text-tertiary);
  font-weight: 500;
}

.meta-tag.provider {
  color: var(--primary);
  background: var(--primary-bg);
  border-color: var(--primary);
}

.meta-tag.price {
  font-family: 'JetBrains Mono', monospace;
}

.meta-tag.feature {
  color: #10b981;
  background: rgba(16, 185, 129, 0.1);
}

.provider-actions-row,
.model-actions-row {
  display: flex;
  align-items: center;
  gap: 8px;
}

.icon-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  background: transparent;
  border: none;
  border-radius: 50%;
  color: var(--text-tertiary);
  cursor: pointer;
  transition: all 0.15s ease;
}

.icon-btn:hover {
  background: var(--bg-primary);
  color: #ef4444;
}

.expand-icon {
  color: var(--text-tertiary);
}

/* 详情面板 */
.provider-detail,
.model-detail {
  padding: 20px;
  background: var(--bg-primary);
  border-top: 1px dashed var(--border-color);
  border-bottom-left-radius: var(--radius);
  border-bottom-right-radius: var(--radius);
}

.detail-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 14px;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.form-group.full-width {
  grid-column: 1 / -1;
}

.form-group.half {
  grid-column: span 1;
}

.form-group label {
  font-size: 12px;
  font-weight: 500;
  color: var(--text-secondary);
}

.form-input {
  width: 100%;
  padding: 10px 12px;
  background: var(--bg-secondary);
  border: 1px solid var(--border-color);
  border-radius: var(--radius);
  color: var(--text-primary);
  font-size: 13px;
  outline: none;
  transition: all 0.2s;
}

.form-input:focus {
  border-color: var(--primary);
  background: var(--bg-primary);
  box-shadow: 0 0 0 2px var(--primary-bg);
}

.form-input::placeholder {
  color: var(--text-tertiary);
}

select.form-input {
  cursor: pointer;
  appearance: none;
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='12' viewBox='0 0 24 24' fill='none' stroke='%236b7280' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpolyline points='6 9 12 15 18 9'%3E%3C/polyline%3E%3C/svg%3E");
  background-repeat: no-repeat;
  background-position: right 10px center;
  padding-right: 30px;
}

.input-with-action {
  position: relative;
  display: flex;
}

.input-with-action .form-input {
  padding-right: 38px;
}

.input-action {
  position: absolute;
  right: 6px;
  top: 50%;
  transform: translateY(-50%);
  display: flex;
  align-items: center;
  justify-content: center;
  width: 26px;
  height: 26px;
  background: transparent;
  border: none;
  border-radius: var(--radius-sm);
  color: var(--text-tertiary);
  cursor: pointer;
}

.input-action:hover {
  background: var(--bg-hover);
  color: var(--text-primary);
}

/* 高级选项 */
.advanced-section {
  margin-top: 16px;
  background: var(--bg-secondary);
  border-radius: var(--radius);
}

.advanced-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  cursor: pointer;
  font-size: 13px;
  font-weight: 500;
  color: var(--text-secondary);
  transition: background 0.15s ease;
}

.advanced-header:hover {
  background: var(--bg-hover);
}

.advanced-content {
  padding: 16px;
  border-top: 1px dashed var(--border-color);
}

.toggle-group {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.toggle-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  background: var(--bg-primary);
  border: 1px solid var(--border-color);
  border-radius: var(--radius);
  cursor: pointer;
  transition: all 0.2s ease;
}

.toggle-item:hover {
  border-color: var(--primary);
  transform: translateY(-1px);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
}

.toggle-item.compact {
  padding: 8px 12px;
}

.toggle-info {
  display: flex;
  align-items: center;
  gap: 10px;
}

.toggle-info > svg {
  color: var(--text-tertiary);
  font-size: 18px;
}

.toggle-label {
  font-size: 13px;
  font-weight: 500;
  color: var(--text-primary);
}

.toggle-hint {
  font-size: 11px;
  color: var(--text-tertiary);
}

.perturbation-options {
  display: flex;
  gap: 12px;
  padding: 12px;
  background: var(--bg-secondary);
  border-radius: var(--radius);
  margin-top: 8px;
}

.perturbation-options .form-group {
  flex: 1;
}

.perturbation-options .toggle-item {
  flex: 1;
  background: var(--bg-primary);
}

/* Switch 开关 */
.switch {
  position: relative;
  width: 40px;
  height: 22px;
  flex-shrink: 0;
}

.switch input {
  opacity: 0;
  width: 0;
  height: 0;
}

.slider {
  position: absolute;
  cursor: pointer;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: var(--bg-hover);
  border-radius: 11px;
  transition: 0.2s;
}

.slider::before {
  position: absolute;
  content: "";
  height: 18px;
  width: 18px;
  left: 2px;
  bottom: 2px;
  background: white;
  border-radius: 50%;
  transition: 0.2s;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.2);
}

.switch input:checked + .slider {
  background: var(--primary);
}

.switch input:checked + .slider::before {
  transform: translateX(18px);
}

.switch.small {
  width: 34px;
  height: 18px;
}

.switch.small .slider {
  border-radius: 9px;
}

.switch.small .slider::before {
  height: 14px;
  width: 14px;
}

.switch.small input:checked + .slider::before {
  transform: translateX(16px);
}

/* 任务配置 */
.task-categories {
  display: flex;
  gap: 6px;
  padding-bottom: 16px;
  border-bottom: 1px solid var(--border-color);
  margin-bottom: 16px;
  overflow-x: auto;
}

.category-btn {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 16px;
  background: transparent;
  border: 1px solid transparent;
  border-radius: 20px;
  color: var(--text-secondary);
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  white-space: nowrap;
  transition: all 0.2s ease;
}

.category-btn:hover {
  background: var(--bg-hover);
  color: var(--text-primary);
}

.category-btn.active {
  background: var(--primary);
  border-color: var(--primary);
  color: white;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
}

.task-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.task-item {
  padding: 18px;
  background: var(--bg-secondary);
  border: 1px solid var(--border-color);
  border-radius: var(--radius);
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
  position: relative;
}

.task-item:hover,
.task-item:has(.custom-select.open) {
  transform: translateY(-2px);
  box-shadow: 0 8px 20px -4px rgba(0, 0, 0, 0.1);
  border-color: var(--primary);
  background: linear-gradient(to bottom right, var(--bg-secondary), var(--bg-primary));
  z-index: 10;
}

.task-header {
  margin-bottom: 16px;
  padding-bottom: 12px;
  border-bottom: 1px dashed var(--border-color);
}

.task-name {
  font-size: 13px;
  font-weight: 600;
  color: var(--text-primary);
}

.task-desc {
  display: block;
  font-size: 12px;
  color: var(--text-tertiary);
  margin-top: 2px;
}

.task-controls {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.control-row {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}

.control-group {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.control-group.model-select {
  flex: 1;
  min-width: 150px;
}

.control-group.small {
  width: 80px;
}

.control-group.tiny {
  width: 60px;
}

.control-group label {
  font-size: 12px;
  font-weight: 500;
  color: var(--text-secondary);
  margin-bottom: 2px;
}

.control-group .form-input {
  padding: 8px 10px;
  font-size: 13px;
  background: var(--bg-primary);
  border: 1px solid var(--border-color);
  border-radius: var(--radius);
  transition: all 0.2s;
}

.control-group .form-input:focus {
  border-color: var(--primary);
  background: var(--bg-secondary);
  box-shadow: 0 0 0 2px var(--primary-bg);
}

/* 模型测试区域 */
.model-test-section {
  margin-top: 16px;
  padding-top: 16px;
  border-top: 1px solid var(--border-color);
  display: flex;
  flex-direction: column;
  gap: 12px;
}

/* 测试按钮 */
.test-model-btn {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 16px;
  background: var(--bg-secondary);
  border: 1px solid var(--border-color);
  border-radius: var(--radius);
  font-size: 13px;
  font-weight: 500;
  color: var(--text-primary);
  cursor: pointer;
  transition: all 0.15s ease;
  white-space: nowrap;
  align-self: flex-start;
}

.test-model-btn:hover:not(:disabled) {
  background: var(--bg-hover);
  border-color: var(--primary);
}

.test-model-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.test-model-btn.testing {
  border-color: var(--primary);
  color: var(--primary);
}

.test-model-btn.success {
  background: rgba(34, 197, 94, 0.1);
  border-color: #22c55e;
  color: #22c55e;
}

.test-model-btn.error {
  background: rgba(239, 68, 68, 0.1);
  border-color: #ef4444;
  color: #ef4444;
}

.test-model-btn .spinning {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

/* 测试结果 */
.test-result {
  font-size: 12px;
}

.test-success {
  display: flex;
  flex-direction: column;
  gap: 6px;
  background: rgba(34, 197, 94, 0.1);
  color: #22c55e;
  padding: 10px 12px;
  border-radius: var(--radius);
}

.test-success > span:first-child {
  display: flex;
  align-items: center;
  gap: 8px;
}

.test-success .response-preview {
  color: var(--text-secondary);
  font-size: 12px;
  line-height: 1.5;
  font-style: italic;
}

.test-error {
  display: flex;
  align-items: center;
  gap: 8px;
  background: rgba(239, 68, 68, 0.1);
  color: #ef4444;
  padding: 10px 12px;
  border-radius: var(--radius);
}

/* 过渡动画 */
.slide-enter-active,
.slide-leave-active {
  transition: all 0.2s ease;
  overflow: hidden;
}

.slide-enter-from,
.slide-leave-to {
  opacity: 0;
  max-height: 0;
}

.slide-enter-to,
.slide-leave-from {
  opacity: 1;
  max-height: 500px;
}

/* 按钮 */
.btn {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  padding: 10px 18px;
  border: none;
  border-radius: var(--radius);
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.15s ease;
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
  border: 1px solid var(--border-color);
}

.btn-secondary:hover:not(:disabled) {
  background: var(--bg-hover);
}

/* 弹窗 */
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
  max-width: 420px;
  max-height: 85vh;
  display: flex;
  flex-direction: column;
  animation: modalIn 0.2s ease;
  overflow: hidden;
}

@keyframes modalIn {
  from {
    opacity: 0;
    transform: scale(0.95);
  }
  to {
    opacity: 1;
    transform: scale(1);
  }
}

.modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  border-bottom: 1px solid var(--border-color);
}

.modal-header h3 {
  display: flex;
  align-items: center;
  gap: 8px;
  margin: 0;
  font-size: 15px;
  font-weight: 600;
  color: var(--text-primary);
}

.modal-header h3 svg {
  color: var(--primary);
}

.close-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  background: transparent;
  border: none;
  border-radius: var(--radius);
  color: var(--text-tertiary);
  cursor: pointer;
}

.close-btn:hover {
  background: var(--bg-secondary);
  color: var(--text-primary);
}

.modal-body {
  padding: 16px;
  overflow-y: auto;
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  padding: 12px 16px;
  border-top: 1px solid var(--border-color);
  background: var(--bg-secondary);
}

/* 带搜索的下拉选择器 */
.searchable-select {
  position: relative;
}

.select-trigger-with-search {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 12px;
  background: var(--bg-primary);
  border: 1px solid var(--border-color);
  border-radius: var(--radius);
  cursor: pointer;
  transition: all 0.15s ease;
}

.select-trigger-with-search:hover {
  border-color: var(--primary);
}

.searchable-select.open .select-trigger-with-search {
  border-color: var(--primary);
  box-shadow: 0 0 0 3px var(--primary-bg);
}

.select-trigger-with-search .preset-icon {
  font-size: 18px;
  color: var(--primary);
}

.select-trigger-with-search span {
  flex: 1;
  font-size: 13px;
  color: var(--text-primary);
}

.select-trigger-with-search .preset-hint {
  font-size: 11px;
  color: var(--text-tertiary);
  margin-left: auto;
  margin-right: 8px;
}

.select-options.searchable {
  max-height: 320px;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  z-index: 9999;
}

.search-in-dropdown {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 12px;
  border-bottom: 1px solid var(--border-color);
  background: var(--bg-primary);
  position: sticky;
  top: 0;
  flex-shrink: 0;
  z-index: 1;
}

.search-in-dropdown svg {
  font-size: 16px;
  color: var(--text-tertiary);
}

.dropdown-search-input {
  flex: 1;
  background: transparent;
  border: none;
  outline: none;
  font-size: 13px;
  color: var(--text-primary);
}

.dropdown-search-input::placeholder {
  color: var(--text-tertiary);
}

.options-list {
  overflow-y: auto;
  max-height: 260px;
  overscroll-behavior: contain;
  flex: 1;
}

.select-option.with-icon {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 12px;
}

.select-option.with-icon .option-icon {
  font-size: 18px;
  color: var(--text-secondary);
}

.select-option.with-icon:hover .option-icon,
.select-option.with-icon.selected .option-icon {
  color: var(--primary);
}

.select-option .option-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.select-option .option-name {
  font-size: 13px;
  font-weight: 500;
  color: var(--text-primary);
}

.select-option .option-desc {
  font-size: 11px;
  color: var(--text-tertiary);
}

.select-option .check-icon {
  font-size: 16px;
  color: var(--primary);
}

.select-option.selected {
  background: var(--primary-bg);
}

.no-results {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  padding: 24px;
  color: var(--text-tertiary);
}

.no-results svg {
  font-size: 24px;
  opacity: 0.5;
}

.no-results span {
  font-size: 12px;
}

.field-tip {
  font-size: 11px;
  color: var(--text-tertiary);
  margin: 4px 0 0 0;
}

.field-lock {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-size: 11px;
  color: var(--warning);
  font-weight: 400;
  margin-left: 8px;
}

.field-lock svg {
  font-size: 12px;
}

.input.disabled,
.select-trigger.disabled,
.custom-select.disabled .select-trigger {
  background: var(--bg-secondary);
  cursor: not-allowed;
  opacity: 0.7;
}

/* 高级设置区域 */
.advanced-settings-section {
  margin-top: 8px;
  border: 1px solid var(--border-color);
  border-radius: var(--radius);
  overflow: hidden;
}

.advanced-toggle {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 12px;
  background: var(--bg-secondary);
  cursor: pointer;
  transition: all 0.15s ease;
}

.advanced-toggle:hover {
  background: var(--bg-hover);
}

.advanced-toggle svg {
  font-size: 16px;
  color: var(--text-secondary);
}

.advanced-toggle span {
  font-size: 12px;
  font-weight: 500;
  color: var(--text-secondary);
}

.advanced-fields {
  padding: 14px;
  display: flex;
  flex-direction: column;
  gap: 14px;
  background: var(--bg-primary);
}

.config-field-row {
  display: flex;
  gap: 12px;
}

.config-field.half {
  flex: 1;
}

.config-field .field-hint {
  font-size: 10px;
  color: var(--text-tertiary);
  margin: 4px 0 0 0;
}

/* 预设模板（保留兼容性） */
.preset-providers h4 {
  font-size: 12px;
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
  gap: 6px;
  padding: 12px 8px;
  background: var(--bg-secondary);
  border: 2px solid var(--border-color);
  border-radius: var(--radius);
  cursor: pointer;
  transition: all 0.15s ease;
}

.preset-btn:hover {
  border-color: var(--primary);
}

.preset-btn.active {
  border-color: var(--primary);
  background: var(--primary-bg);
}

.preset-btn svg {
  font-size: 20px;
  color: var(--text-secondary);
}

.preset-btn.active svg,
.preset-btn:hover svg {
  color: var(--primary);
}

.preset-btn span {
  font-size: 11px;
  font-weight: 500;
  color: var(--text-primary);
}

.preset-btn small {
  font-size: 10px;
  color: var(--text-tertiary);
  text-align: center;
}

.divider {
  display: flex;
  align-items: center;
  gap: 12px;
  margin: 8px 0;
}

.divider::before,
.divider::after {
  content: '';
  flex: 1;
  height: 1px;
  background: var(--border-color);
}

.divider span {
  font-size: 11px;
  color: var(--text-tertiary);
}

.manual-config {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

/* 高级参数区域 */
.advanced-params-section {
  background: var(--bg-secondary);
  border-radius: var(--radius);
}

.slider-with-input {
  display: flex;
  align-items: center;
  gap: 10px;
}

.temp-slider {
  flex: 1;
  height: 4px;
  -webkit-appearance: none;
  appearance: none;
  background: var(--bg-hover);
  border-radius: 2px;
  outline: none;
}

.temp-slider::-webkit-slider-thumb {
  -webkit-appearance: none;
  appearance: none;
  width: 16px;
  height: 16px;
  background: var(--primary);
  border-radius: 50%;
  cursor: pointer;
}

.temp-slider::-moz-range-thumb {
  width: 16px;
  height: 16px;
  background: var(--primary);
  border-radius: 50%;
  cursor: pointer;
  border: none;
}

.temp-input {
  width: 60px !important;
  text-align: center;
}

.feature-toggles {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.feature-toggle {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 12px;
  background: var(--bg-primary);
  border: 1px solid var(--border-color);
  border-radius: var(--radius);
  cursor: pointer;
  transition: all 0.15s ease;
}

.feature-toggle:hover {
  border-color: var(--primary);
}

.feature-toggle-info {
  display: flex;
  align-items: center;
  gap: 10px;
}

.feature-toggle-icon {
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--bg-secondary);
  border-radius: var(--radius);
  color: var(--text-tertiary);
}

.feature-toggle-icon.active {
  background: var(--primary-bg);
  color: var(--primary);
}

.feature-toggle-text {
  display: flex;
  flex-direction: column;
  gap: 1px;
}

.feature-name {
  font-size: 13px;
  font-weight: 500;
  color: var(--text-primary);
}

.feature-hint {
  font-size: 11px;
  color: var(--text-tertiary);
}

.config-field {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.config-field label {
  font-size: 12px;
  font-weight: 500;
  color: var(--text-secondary);
}

.field-hint {
  font-size: 11px;
  font-weight: 400;
  color: var(--text-tertiary);
}

.input {
  width: 100%;
  padding: 8px 12px;
  border: 1px solid var(--border-color);
  border-radius: var(--radius);
  background: var(--bg-secondary);
  color: var(--text-primary);
  font-size: 13px;
  outline: none;
  transition: all 0.15s ease;
}

.input:focus {
  border-color: var(--primary);
  box-shadow: 0 0 0 2px var(--primary-bg);
}

.input::placeholder {
  color: var(--text-tertiary);
}

select.input {
  cursor: pointer;
  appearance: none;
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='12' viewBox='0 0 24 24' fill='none' stroke='%236b7280' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpolyline points='6 9 12 15 18 9'%3E%3C/polyline%3E%3C/svg%3E");
  background-repeat: no-repeat;
  background-position: right 10px center;
  padding-right: 30px;
}

.config-field-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
}

/* 响应式 */
@media (max-width: 640px) {
  .nav-header {
    flex-direction: column;
    align-items: stretch;
  }

  .nav-tabs {
    overflow-x: auto;
  }

  .nav-actions {
    justify-content: space-between;
  }

  .search-input {
    width: 100px;
  }

  .detail-grid {
    grid-template-columns: 1fr;
  }

  .control-row {
    flex-direction: column;
  }

  .control-group.model-select,
  .control-group.small,
  .control-group.tiny {
    width: 100%;
  }

  .preset-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

/* 模型列表区域 */
.models-section {
  background: var(--bg-secondary);
  border: 1px solid var(--border-color);
  border-radius: var(--radius);
  padding: 12px;
  margin-top: 8px;
}

.loading-models {
  display: flex;
  align-items: center;
  gap: 10px;
  justify-content: center;
  padding: 16px;
  color: var(--text-secondary);
  font-size: 13px;
}

.loading-models .spinning {
  animation: spin 1s linear infinite;
}

.fetch-error {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px;
  background: rgba(239, 68, 68, 0.1);
  border-radius: var(--radius);
  color: #ef4444;
  font-size: 12px;
}

.btn-retry {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-left: auto;
  padding: 6px 12px;
  background: white;
  border: 1px solid #ef4444;
  border-radius: var(--radius-sm);
  color: #ef4444;
  font-size: 12px;
  cursor: pointer;
  transition: all 0.15s ease;
}

.btn-retry:hover {
  background: #fef2f2;
}

.available-models {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.models-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding-bottom: 8px;
  border-bottom: 1px solid var(--border-color);
  font-size: 12px;
  font-weight: 500;
  color: var(--text-secondary);
}

.btn-refresh {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 24px;
  height: 24px;
  padding: 0;
  background: transparent;
  border: none;
  border-radius: var(--radius-sm);
  color: var(--text-tertiary);
  cursor: pointer;
  transition: all 0.15s ease;
}

.btn-refresh:hover {
  background: var(--bg-hover);
  color: var(--primary);
}

.models-list {
  display: flex;
  flex-direction: column;
  gap: 6px;
  max-height: 240px;
  overflow-y: auto;
}

.model-option {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 12px;
  background: var(--bg-primary);
  border: 1px solid var(--border-color);
  border-radius: var(--radius);
  color: var(--text-primary);
  font-size: 13px;
  text-align: left;
  cursor: pointer;
  transition: all 0.15s ease;
}

.model-option:hover {
  border-color: var(--primary);
  background: var(--bg-hover);
}

.model-option.active {
  border-color: var(--primary);
  background: var(--primary-bg);
}

.model-info {
  display: flex;
  flex-direction: column;
  gap: 2px;
  flex: 1;
  min-width: 0;
}

.model-id {
  font-weight: 500;
  color: var(--text-primary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.model-name {
  font-size: 11px;
  color: var(--text-tertiary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.check-icon {
  color: var(--primary);
  font-size: 16px;
  flex-shrink: 0;
}

/* 自定义多选下拉框 */
.custom-select {
  position: relative;
  width: 100%;
}

.select-trigger {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 9.5px 12px;
  background: var(--bg-secondary);
  border: 1px solid var(--border-color);
  border-radius: var(--radius);
  cursor: pointer;
  font-size: 13px;
  min-height: 38px;
  transition: all 0.2s;
}

.select-trigger:hover {
  border-color: var(--text-tertiary);
  background: var(--bg-hover);
}

.custom-select.open .select-trigger {
  border-color: var(--primary);
  box-shadow: 0 0 0 2px var(--primary-bg);
  background: var(--bg-primary);
}

.selected-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
  flex: 1;
  margin-right: 8px;
  overflow: hidden;
}

.selected-tag {
  background: var(--primary-bg);
  border: 1px solid var(--primary);
  color: var(--primary);
  padding: 2px 10px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 500;
  line-height: 1.5;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 100%;
  display: flex;
  align-items: center;
  gap: 4px;
}

.placeholder {
  color: var(--text-tertiary);
}

.chevron {
  color: var(--text-tertiary);
  width: 14px;
  height: 14px;
  flex-shrink: 0;
  transition: transform 0.2s ease;
}

.chevron.rotated {
  transform: rotate(180deg);
}

.select-options {
  position: absolute;
  top: 100%;
  left: 0;
  right: 0;
  margin-top: 4px;
  background: var(--bg-secondary);
  border: 1px solid var(--border-color);
  border-radius: var(--radius);
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.2);
  z-index: 100;
  max-height: 240px;
  overflow-y: auto;
  padding: 4px;
}

/* 下拉框动画 */
.dropdown-fade-enter-active,
.dropdown-fade-leave-active {
  transition: all 0.2s ease;
}

.dropdown-fade-enter-from,
.dropdown-fade-leave-to {
  opacity: 0;
  transform: translateY(-5px);
}

.select-option {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 8px;
  cursor: pointer;
  border-radius: var(--radius-sm);
  font-size: 12px;
  color: var(--text-primary);
}

.select-option:hover {
  background: var(--bg-hover);
}

.checkbox {
  width: 14px;
  height: 14px;
  border: 1px solid var(--border-input);
  border-radius: 3px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--bg-input);
}

.checkbox.checked {
  background: var(--primary);
  border-color: var(--primary);
  color: white;
}

.checkbox svg {
  width: 10px;
  height: 10px;
}

.dropdown-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  z-index: 9998;
  cursor: default;
}

/* Number Input Styling */
.number-input-wrapper {
  display: flex;
  align-items: center;
  border: 1px solid var(--border-color);
  border-radius: var(--radius);
  background: var(--bg-secondary);
  padding: 2px;
  transition: all 0.2s;
}

.number-input-wrapper:focus-within {
  border-color: var(--primary);
  background: var(--bg-primary);
}

.number-input-wrapper .form-input {
  border: none;
  background: transparent;
  padding: 0;
  text-align: center;
  height: 32px;
  width: 100%;
  -moz-appearance: textfield;
  appearance: textfield;
}

.number-input-wrapper .form-input:focus {
  box-shadow: none;
  background: transparent;
}

.number-input-wrapper .form-input::-webkit-outer-spin-button,
.number-input-wrapper .form-input::-webkit-inner-spin-button {
  -webkit-appearance: none;
  margin: 0;
}

.number-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  border: none;
  background: transparent;
  color: var(--text-secondary);
  cursor: pointer;
  border-radius: var(--radius-sm);
  transition: all 0.2s;
  flex-shrink: 0;
}

.number-btn:hover:not(:disabled) {
  background: var(--bg-hover);
  color: var(--text-primary);
}

.number-btn:disabled {
  opacity: 0.3;
  cursor: not-allowed;
}

/* Perturbation Options Styling */
.perturbation-options,
.perturbation-sub-options {
  margin-top: 8px;
  padding: 12px;
  background: var(--bg-secondary);
  border: 1px solid var(--border-color);
  border-radius: var(--radius);
  display: flex;
  align-items: flex-end;
  gap: 16px;
  animation: slideDown 0.2s ease-out;
}

.perturbation-options .form-group,
.perturbation-sub-options .config-field {
  flex: 1;
  margin-bottom: 0;
}

.perturbation-options .toggle-item.compact,
.perturbation-sub-options .feature-toggle.compact {
  flex: 1;
  margin-bottom: 0;
  background: var(--bg-primary);
  border: 1px solid var(--border-color);
  border-radius: var(--radius);
  padding: 8px 12px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: 40px; /* Match input height roughly */
}

.perturbation-options .toggle-item.compact .toggle-info,
.perturbation-sub-options .feature-toggle.compact .feature-toggle-info {
  display: flex;
  align-items: center;
  gap: 8px;
}

.perturbation-options .toggle-item.compact .toggle-label,
.perturbation-sub-options .feature-toggle.compact .feature-name {
  font-size: 13px;
  font-weight: 500;
  color: var(--text-primary);
}

@keyframes slideDown {
  from {
    opacity: 0;
    transform: translateY(-10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}
</style>
