<!--
  @file ModelStatsView.vue
  @description 模型统计页面
  
  功能说明：
  1. 查看 AI 模型使用情况
  2. 成本分析和效率指标
  3. 按模型/提供商/模块分类统计
  4. 图表可视化分析
  
  统计总览：
  - 总调用次数
  - 总 Token 消耗
  - Token 效率（输出/输入比）
  - 总成本
  - 平均单次 Token
  
  页面选项卡：
  - models: 按模型统计
  - providers: 按提供商分析
  - modules: 按模块使用情况
  - charts: 图表分析
  
  时间范围：
  - 支持选择不同时间段的统计数据
-->
<template>
  <div class="model-stats-view">
    <div class="view-header">
      <div class="header-content">
        <h2>模型统计</h2>
        <p class="subtitle">查看模型使用情况、成本分析和性能指标</p>
      </div>
      <div class="header-actions">
        <div class="time-range-selector">
          <button 
            v-for="range in timeRanges" 
            :key="range.value"
            class="time-range-button"
            :class="{ active: selectedTimeRange === range.value }"
            @click="selectTimeRange(range.value)"
          >
            {{ range.label }}
          </button>
        </div>
        <button class="m3-button filled" @click="fetchData" :disabled="loading">
          <span class="material-symbols-rounded" :class="{ spinning: loading }">refresh</span>
          刷新数据
        </button>
      </div>
    </div>

    <!-- 统计总览卡片 -->
    <div class="overview-section" v-if="statsData && Object.keys(statsData).length > 0">
      <div class="overview-grid">
        <div class="overview-card">
          <div class="card-icon" style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);">
            <span class="material-symbols-rounded">api</span>
          </div>
          <div class="card-content">
            <div class="label">总调用次数</div>
            <div class="value primary">{{ formatNumber(totalStats.totalCalls) }}</div>
            <div class="description">模型接口总调用</div>
          </div>
        </div>
        <div class="overview-card">
          <div class="card-icon" style="background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);">
            <span class="material-symbols-rounded">token</span>
          </div>
          <div class="card-content">
            <div class="label">总Token消耗</div>
            <div class="value secondary">{{ formatNumber(totalStats.totalTokens) }}</div>
            <div class="description">累计处理Token数</div>
          </div>
        </div>
        <div class="overview-card">
          <div class="card-icon" style="background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);">
            <span class="material-symbols-rounded">insights</span>
          </div>
          <div class="card-content">
            <div class="label">Token效率</div>
            <div class="value tertiary">{{ totalStats.tokenEfficiency }}</div>
            <div class="description">输出/输入比率</div>
          </div>
        </div>
        <div class="overview-card">
          <div class="card-icon" style="background: linear-gradient(135deg, #fa709a 0%, #fee140 100%);">
            <span class="material-symbols-rounded">payments</span>
          </div>
          <div class="card-content">
            <div class="label">总成本</div>
            <div class="value error">${{ totalStats.totalCost.toFixed(4) }}</div>
            <div class="description">累计消费金额</div>
          </div>
        </div>
        <div class="overview-card">
          <div class="card-icon" style="background: linear-gradient(135deg, #a8edea 0%, #fed6e3 100%);">
            <span class="material-symbols-rounded">analytics</span>
          </div>
          <div class="card-content">
            <div class="label">平均单次Token</div>
            <div class="value">{{ totalStats.avgTokensPerCall }}</div>
            <div class="description">每次调用平均消耗</div>
          </div>
        </div>
      </div>
    </div>

    <!-- 标签页导航 -->
    <div class="tabs-container" v-if="statsData && Object.keys(statsData).length > 0">
      <div class="tabs">
        <button 
          class="tab" 
          :class="{ active: activeTab === 'models' }"
          @click="activeTab = 'models'"
        >
          <span class="material-symbols-rounded">model_training</span>
          模型统计
        </button>
        <button 
          class="tab" 
          :class="{ active: activeTab === 'providers' }"
          @click="activeTab = 'providers'"
        >
          <span class="material-symbols-rounded">cloud</span>
          提供商分析
        </button>
        <button 
          class="tab" 
          :class="{ active: activeTab === 'modules' }"
          @click="activeTab = 'modules'"
        >
          <span class="material-symbols-rounded">extension</span>
          模块使用
        </button>
        <button 
          class="tab" 
          :class="{ active: activeTab === 'charts' }"
          @click="activeTab = 'charts'"
        >
          <span class="material-symbols-rounded">bar_chart</span>
          图表分析
        </button>
      </div>
    </div>

    <div class="stats-content">
      <div v-if="loading && !statsData" class="loading-state">
        <span class="material-symbols-rounded spinning" style="font-size: 48px;">progress_activity</span>
        <p>加载统计数据中...</p>
      </div>
      
      <!-- 模型统计标签页 -->
      <div v-else-if="statsData && Object.keys(statsData).length > 0 && activeTab === 'models'" class="tab-content">
        <div class="stats-grid">
          <div 
            v-for="[model, stats] in Object.entries(statsData)" 
            :key="model" 
            class="model-card"
            @click="openDetail(model, stats)"
          >
            <div class="card-header">
              <div class="model-info">
                <span class="material-symbols-rounded model-icon">smart_toy</span>
                <h3 class="model-name">{{ model }}</h3>
              </div>
            </div>
            <div class="card-body">
              <div class="stat-row">
                <div class="stat-item">
                  <span class="label">调用次数</span>
                  <span class="value">{{ stats.total_calls ? formatNumber(stats.total_calls) : 'N/A' }}</span>
                </div>
                <div class="stat-item">
                  <span class="label">平均Token</span>
                  <span class="value">{{ getAvgTokens(stats) }}</span>
                </div>
              </div>
              <div class="stat-divider"></div>
              <div class="stat-row">
                <div class="stat-item">
                  <span class="label">输入Token</span>
                  <span class="value">{{ stats.prompt_tokens ? formatNumber(stats.prompt_tokens) : 'N/A' }}</span>
                </div>
                <div class="stat-item">
                  <span class="label">输出Token</span>
                  <span class="value">{{ stats.completion_tokens ? formatNumber(stats.completion_tokens) : 'N/A' }}</span>
                </div>
              </div>
              <div class="stat-divider"></div>
              <div class="stat-row total-row">
                <div class="stat-item">
                  <span class="label">总Token</span>
                  <span class="value highlight">{{ stats.total_tokens ? formatNumber(stats.total_tokens) : 'N/A' }}</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 提供商统计标签页 -->
      <div v-else-if="activeTab === 'providers'" class="tab-content">
        <div class="provider-grid">
          <div 
            v-for="[provider, stats] in Object.entries(providerStats)" 
            :key="provider" 
            class="provider-card"
          >
            <div class="card-header">
              <div class="provider-info">
                <span class="material-symbols-rounded provider-icon">cloud_circle</span>
                <h3 class="provider-name">{{ provider }}</h3>
              </div>
            </div>
            <div class="card-body">
              <div class="stat-grid-2col">
                <div class="stat-item-card">
                  <span class="label">总调用</span>
                  <span class="value">{{ stats.total_calls ? formatNumber(stats.total_calls) : 'N/A' }}</span>
                </div>
                <div class="stat-item-card">
                  <span class="label">总Token</span>
                  <span class="value">{{ stats.total_tokens ? formatNumber(stats.total_tokens) : 'N/A' }}</span>
                </div>
                <div class="stat-item-card">
                  <span class="label">总成本</span>
                  <span class="value">${{ stats.total_cost.toFixed(4) }}</span>
                </div>
                <div class="stat-item-card">
                  <span class="label">平均响应</span>
                  <span class="value">{{ stats.avg_time.toFixed(2) }}s</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 模块统计标签页 -->
      <div v-else-if="activeTab === 'modules'" class="tab-content">
        <div class="module-grid">
          <div 
            v-for="[module, stats] in Object.entries(moduleStats)" 
            :key="module" 
            class="module-card"
          >
            <div class="card-header">
              <div class="module-info">
                <span class="material-symbols-rounded module-icon">widgets</span>
                <h3 class="module-name">{{ module }}</h3>
              </div>
            </div>
            <div class="card-body">
              <div class="stat-grid-2col">
                <div class="stat-item-card">
                  <span class="label">调用次数</span>
                  <span class="value">{{ formatNumber(stats.total_calls) }}</span>
                </div>
                <div class="stat-item-card">
                  <span class="label">Token消耗</span>
                  <span class="value">{{ formatNumber(stats.total_tokens) }}</span>
                </div>
                <div class="stat-item-card">
                  <span class="label">总成本</span>
                  <span class="value">${{ stats.total_cost.toFixed(4) }}</span>
                </div>
                <div class="stat-item-card">
                  <span class="label">平均时间</span>
                  <span class="value">{{ stats.avg_time.toFixed(2) }}s</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 图表分析标签页 -->
      <div v-else-if="activeTab === 'charts'" class="tab-content">
        <div class="charts-container">
          <div class="chart-card">
            <div class="chart-header">
              <h3>成本分布 (按提供商)</h3>
              <span class="chart-subtitle">Pie Chart</span>
            </div>
            <div class="chart-body" ref="costByProviderChart"></div>
          </div>
          <div class="chart-card">
            <div class="chart-header">
              <h3>请求分布 (按提供商)</h3>
              <span class="chart-subtitle">Doughnut Chart</span>
            </div>
            <div class="chart-body" ref="reqByProviderChart"></div>
          </div>
          <div class="chart-card wide">
            <div class="chart-header">
              <h3>模型成本对比</h3>
              <span class="chart-subtitle">Bar Chart</span>
            </div>
            <div class="chart-body" ref="costByModelChart"></div>
          </div>
          <div class="chart-card wide">
            <div class="chart-header">
              <h3>平均响应时间</h3>
              <span class="chart-subtitle">Bar Chart</span>
            </div>
            <div class="chart-body" ref="avgResponseTimeChart"></div>
          </div>
        </div>
      </div>
      
      <div v-else class="empty-state">
        <span class="material-symbols-rounded empty-icon">inbox</span>
        <p>暂无统计数据</p>
        <button class="m3-button filled" @click="fetchData">立即获取</button>
      </div>
    </div>

    <!-- 详情弹窗 -->
    <div class="m3-dialog-overlay" v-if="selectedModel" @click="closeDetail">
      <div class="m3-dialog" :class="{ 'has-tasks': getTasksForModel(selectedModel.name).length > 0 }" @click.stop>
        <div class="dialog-header">
          <h3>模型详情</h3>
          <button class="m3-icon-button" @click="closeDetail">
            <span class="material-symbols-rounded">close</span>
          </button>
        </div>
        <div class="dialog-content">
          <div class="detail-body-layout">
            <div class="stats-section">
              <div class="detail-header">
                <span class="material-symbols-rounded detail-icon">smart_toy</span>
                <div class="detail-title">
                  <div class="detail-name">{{ selectedModel.name }}</div>
                  <div class="detail-badges">
                    <span class="detail-badge">{{ selectedModel.stats.total_calls ? formatNumber(selectedModel.stats.total_calls) : 'N/A' }} 次调用</span>
                  </div>
                </div>
              </div>
              <div class="section-title">统计数据</div>
              <div class="detail-grid">
                <div class="detail-card filled">
                  <span class="detail-label">总Token消耗</span>
                  <span class="detail-value">{{ selectedModel.stats.total_tokens ? formatNumber(selectedModel.stats.total_tokens) : 'N/A' }}</span>
                </div>
                <div class="detail-card">
                  <span class="detail-label">输入Token</span>
                  <span class="detail-value">{{ selectedModel.stats.prompt_tokens ? formatNumber(selectedModel.stats.prompt_tokens) : 'N/A' }}</span>
                </div>
                <div class="detail-card">
                  <span class="detail-label">输出Token</span>
                  <span class="detail-value">{{ selectedModel.stats.completion_tokens ? formatNumber(selectedModel.stats.completion_tokens) : 'N/A' }}</span>
                </div>
                <div class="detail-card">
                  <span class="detail-label">平均Token</span>
                  <span class="detail-value">{{ getAvgTokens(selectedModel.stats) }}</span>
                </div>
              </div>
            </div>
            <div class="tasks-section" v-if="getTasksForModel(selectedModel.name).length > 0">
              <div class="section-title">使用场景</div>
              <div class="tasks-grid">
                <div class="task-card" v-for="task in getTasksForModel(selectedModel.name)" :key="task">
                  <span class="material-symbols-rounded task-icon">check_circle</span>
                  <span class="task-name">{{ task }}</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, nextTick, watch } from 'vue'
import { getConfigList, getConfigContent, type ConfigFileInfo } from '@/api'
import { getModelUsageStats,getProviderStats, getModuleStats, getChartData, } from '@/api/model_stats'
import { showError } from '@/utils/dialog'
import * as echarts from 'echarts'

// 定义时间范围类型
type TimeRange = '1h' | '24h' | '7d' | '30d' | 'all'

const loading = ref(false)
const statsData = ref<Record<string, Record<string, number>> | null>(null)
const providerStats = ref<Record<string, Record<string, any>>>({})
const moduleStats = ref<Record<string, Record<string, any>>>({})
const chartData = ref<Record<string, any>>({})
const selectedModel = ref<{ name: string; stats: any } | null>(null)
const modelTasks = ref<Record<string, string[]>>({})
const activeTab = ref<'models' | 'providers' | 'modules' | 'charts'>('models')
const selectedTimeRange = ref<TimeRange>('24h')

// 时间范围选项
const timeRanges: Array<{ value: TimeRange; label: string }> = [
  { value: '1h', label: '1小时' },
  { value: '24h', label: '24小时' },
  { value: '7d', label: '7天' },
  { value: '30d', label: '30天' },
  { value: 'all', label: '全部' }
]

// Chart refs
const costByProviderChart = ref<HTMLElement | null>(null)
const reqByProviderChart = ref<HTMLElement | null>(null)
const costByModelChart = ref<HTMLElement | null>(null)
const avgResponseTimeChart = ref<HTMLElement | null>(null)

// 计算总体统计数据
const totalStats = ref({
  totalCalls: 0,
  totalTokens: 0,
  totalCost: 0,
  tokenEfficiency: '0.00x',
  consumeRatio: '0.00',
  avgTokensPerCall: 0
})

const calculateTotalStats = () => {
  if (!statsData.value) return
  
  let calls = 0
  let tokens = 0
  let cost = 0
  let promptTokens = 0
  let completionTokens = 0
  
  Object.values(statsData.value).forEach(stats => {
    calls += stats.total_calls || 0
    tokens += stats.total_tokens || 0
    promptTokens += stats.prompt_tokens || 0
    completionTokens += stats.completion_tokens || 0
  })
  
  // 从提供商统计中获取总成本
  if (Object.keys(providerStats.value).length > 0) {
    Object.values(providerStats.value).forEach(stats => {
      cost += stats.total_cost || 0
    })
  }
  
  const efficiency = promptTokens > 0 ? (completionTokens / promptTokens).toFixed(3) + 'x' : '0.000x'
  const ratio = calls > 0 ? (tokens / calls / 1000).toFixed(2) : '0.00'
  const avgTokens = calls > 0 ? Math.round(tokens / calls) : 0
  
  totalStats.value = {
    totalCalls: calls,
    totalTokens: tokens,
    totalCost: cost,
    tokenEfficiency: efficiency,
    consumeRatio: ratio,
    avgTokensPerCall: avgTokens
  }
}

const formatNumber = (num: number) => {
  if (num >= 1000000) {
    return (num / 1000000).toFixed(2) + 'M'
  } else if (num >= 1000) {
    return (num / 1000).toFixed(2) + 'K'
  }
  return num.toString()
}

const getAvgTokens = (stats: any) => {
  if (!stats.total_calls || stats.total_calls === 0) return 0
  return Math.round(stats.total_tokens / stats.total_calls)
}

const fetchData = async () => {
  loading.value = true
  try {
    const [statsRes, configListRes, providerRes, moduleRes, chartRes] = await Promise.all([
      getModelUsageStats(selectedTimeRange.value),
      getConfigList(),
      getProviderStats(selectedTimeRange.value),
      getModuleStats(selectedTimeRange.value),
      getChartData(selectedTimeRange.value)
    ])

    if (statsRes.success && statsRes.data) {
      statsData.value = statsRes.data.stats
    } else {
      showError('获取模型数据失败: ' + (statsRes.error || '未知错误'))
    }

    if (providerRes.success && providerRes.data) {
      providerStats.value = providerRes.data.stats || {}
    }

    if (moduleRes.success && moduleRes.data) {
      moduleStats.value = moduleRes.data.stats || {}
    }

    if (chartRes.success && chartRes.data) {
      chartData.value = chartRes.data.chart_data || {}
    }

    calculateTotalStats() // 计算总体统计

    // 获取模型配置以分析用途
    if (configListRes.success && configListRes.data) {
      // 扫描主配置和模型配置
      const targetConfigs = configListRes.data.configs.filter((c: ConfigFileInfo) => 
        c.path === 'mofox_bot_config.yaml' || c.path.includes('model_config')
      )
      
      for (const config of targetConfigs) {
        const contentRes = await getConfigContent(config.path)
        if (contentRes.success && contentRes.data?.content) {
          analyzeModelTasks(contentRes.data.content)
        }
      }
    }

    // 等待DOM更新后渲染图表
    if (activeTab.value === 'charts') {
      await nextTick()
      renderCharts()
    }
  } catch (e) {
    showError('网络请求失败: ' + e)
  } finally {
    loading.value = false
  }
}

const analyzeModelTasks = (config: Record<string, any>) => {
  const tasks: Record<string, string[]> = { ...modelTasks.value } // 保留已有的任务
  
  // 0. 建立 模型别名(name) -> 模型标识符(model_identifier) 的映射
  const nameToIdMap: Record<string, string> = {}
  if (Array.isArray(config.models)) {
    config.models.forEach((m: any) => {
      if (m.name && m.model_identifier) {
        nameToIdMap[m.name] = m.model_identifier
      }
    })
  }

  // 辅助函数：添加任务
  const addTask = (modelRef: string, taskName: string) => {
    // 尝试解析为真实ID，如果找不到则使用原名（可能是直接填写的ID）
    const realId = nameToIdMap[modelRef] || modelRef
    
    if (!tasks[realId]) tasks[realId] = []
    if (!tasks[realId].includes(taskName)) {
      tasks[realId].push(taskName)
    }
  }

  // 1. 处理 model_task_config (标准结构)
  if (config.model_task_config && typeof config.model_task_config === 'object') {
    const taskConfig = config.model_task_config as Record<string, any>
    
    // 任务名称映射表
    const taskNameMap: Record<string, string> = {
      'replyer': '主回复 (Replyer)',
      'planner': '规划 (Planner)',
      'emotion': '情感分析 (Emotion)',
      'mood': '心情 (Mood)',
      'maizone': 'MaiZone',
      'tool_use': '工具调用 (Tool Use)',
      'anti_injection': '反注入 (Anti-Injection)',
      'vlm': '视觉识别 (VLM)',
      'emoji_vlm': '表情包识别 (Emoji VLM)',
      'utils_video': '视频处理',
      'voice': '语音 (Voice)',
      'embedding': '向量 (Embedding)',
      'memory_short_term_builder': '短时记忆构建',
      'memory_short_term_decider': '短时记忆决策',
      'memory_long_term': '长时记忆',
      'summary': '总结 (Summary)',
      'translate': '翻译 (Translate)',
    }

    for (const [taskKey, taskSettings] of Object.entries(taskConfig)) {
      if (taskSettings && typeof taskSettings === 'object') {
        const modelRef = (taskSettings as any).model
        if (modelRef && typeof modelRef === 'string') {
          const taskDisplayName = taskNameMap[taskKey] || taskKey
          addTask(modelRef, taskDisplayName)
        }
      }
    }
  }

  // 2. 通用遍历逻辑 (兼容旧格式或其他配置)
  const traverse = (obj: any, path: string[]) => {
    if (typeof obj !== 'object' || obj === null) return
    
    // 跳过 model_task_config，因为上面已经处理过了
    if (path.length === 0 && obj === config.model_task_config) return 
    if (path.includes('model_task_config')) return
    // 跳过 models 定义列表
    if (path.length === 0 && obj === config.models) return

    for (const [key, value] of Object.entries(obj)) {
      if (key === 'model' && typeof value === 'string') {
        // 找到了一个模型引用，尝试构建任务名
        const taskName = path.length > 0 ? path[path.length - 1] : 'Unknown'
        if(taskName) { 
          addTask(value, taskName)
        }
      } else if (typeof value === 'object' && value !== null) {
        traverse(value, [...path, key])
      }
    }
  }
  
  traverse(config, [])
  console.log('[ModelStats] Analyzed tasks:', tasks)
  modelTasks.value = tasks
}

const openDetail = (model: string, stats: any) => {
  selectedModel.value = { name: model, stats }
}

const closeDetail = () => {
  selectedModel.value = null
}

const getTasksForModel = (modelName: string) => {
  if (!modelTasks.value) return []
  return modelTasks.value[modelName] || []
}

// 选择时间范围
const selectTimeRange = (range: TimeRange) => {
  selectedTimeRange.value = range
  fetchData()
}

// 图表渲染
const renderCharts = () => {
  renderCostByProviderChart()
  renderReqByProviderChart()
  renderCostByModelChart()
  renderAvgResponseTimeChart()
}

const renderCostByProviderChart = () => {
  if (!costByProviderChart.value || !chartData.value.pie_chart_cost_by_provider) return
  
  const chart = echarts.init(costByProviderChart.value)
  const data = chartData.value.pie_chart_cost_by_provider
  
  const option = {
    tooltip: {
      trigger: 'item',
      formatter: '{b}: ${c} ({d}%)'
    },
    legend: {
      orient: 'vertical',
      left: 'left'
    },
    series: [
      {
        name: '成本分布',
        type: 'pie',
        radius: '60%',
        data: data.labels ? data.labels.map((label: string, idx: number) => ({
          name: label,
          value: data.data[idx]
        })) : [],
        emphasis: {
          itemStyle: {
            shadowBlur: 10,
            shadowOffsetX: 0,
            shadowColor: 'rgba(0, 0, 0, 0.5)'
          }
        }
      }
    ]
  }
  
  chart.setOption(option)
}

const renderReqByProviderChart = () => {
  if (!reqByProviderChart.value || !chartData.value.pie_chart_req_by_provider) return
  
  const chart = echarts.init(reqByProviderChart.value)
  const data = chartData.value.pie_chart_req_by_provider
  
  const option = {
    tooltip: {
      trigger: 'item',
      formatter: '{b}: {c} 次 ({d}%)'
    },
    legend: {
      orient: 'vertical',
      left: 'left'
    },
    series: [
      {
        name: '请求分布',
        type: 'pie',
        radius: ['40%', '70%'],
        data: data.labels ? data.labels.map((label: string, idx: number) => ({
          name: label,
          value: data.data[idx]
        })) : [],
        emphasis: {
          itemStyle: {
            shadowBlur: 10,
            shadowOffsetX: 0,
            shadowColor: 'rgba(0, 0, 0, 0.5)'
          }
        }
      }
    ]
  }
  
  chart.setOption(option)
}

const renderCostByModelChart = () => {
  if (!costByModelChart.value || !chartData.value.bar_chart_cost_by_model) return
  
  const chart = echarts.init(costByModelChart.value)
  const data = chartData.value.bar_chart_cost_by_model
  
  const option = {
    tooltip: {
      trigger: 'axis',
      axisPointer: {
        type: 'shadow'
      },
      formatter: '{b}: ${c}'
    },
    grid: {
      containLabel: true,
      left: '3%',
      right: '4%',
      bottom: '3%'
    },
    xAxis: {
      type: 'value',
      name: '成本 ($)'
    },
    yAxis: {
      type: 'category',
      data: data.labels || [],
      axisLabel: {
        interval: 0
      }
    },
    series: [
      {
        name: '成本',
        type: 'bar',
        data: data.data || [],
        itemStyle: {
          color: new echarts.graphic.LinearGradient(1, 0, 0, 0, [
            { offset: 0, color: '#83bff6' },
            { offset: 0.5, color: '#188df0' },
            { offset: 1, color: '#188df0' }
          ])
        }
      }
    ]
  }
  
  chart.setOption(option)
}

const renderAvgResponseTimeChart = () => {
  if (!avgResponseTimeChart.value || !chartData.value.bar_chart_avg_response_time) return
  
  const chart = echarts.init(avgResponseTimeChart.value)
  const data = chartData.value.bar_chart_avg_response_time
  
  const option = {
    tooltip: {
      trigger: 'axis',
      axisPointer: {
        type: 'shadow'
      },
      formatter: '{b}: {c}s'
    },
    grid: {
      containLabel: true,
      left: '3%',
      right: '4%',
      bottom: '3%'
    },
    xAxis: {
      type: 'value',
      name: '响应时间 (秒)'
    },
    yAxis: {
      type: 'category',
      data: data.labels || [],
      axisLabel: {
        interval: 0
      }
    },
    series: [
      {
        name: '平均响应时间',
        type: 'bar',
        data: data.data || [],
        itemStyle: {
          color: new echarts.graphic.LinearGradient(1, 0, 0, 0, [
            { offset: 0, color: '#f093fb' },
            { offset: 0.5, color: '#f5576c' },
            { offset: 1, color: '#f5576c' }
          ])
        }
      }
    ]
  }
  
  chart.setOption(option)
}

// 监听标签页切换
watch(activeTab, async (newTab) => {
  if (newTab === 'charts') {
    await nextTick()
    renderCharts()
  }
})

onMounted(() => {
  fetchData()
})
</script>

<style scoped>
.model-stats-view {
  padding: 24px;
  height: 100%;
  overflow-y: auto;
  box-sizing: border-box;
}

.view-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
  background: var(--md-sys-color-surface-container);
  padding: 24px;
  border-radius: 24px;
  box-shadow: var(--md-sys-elevation-1);
}

.header-content h2 {
  margin: 0;
  font-size: 28px;
  font-weight: 700;
  color: var(--md-sys-color-on-surface);
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 16px;
}

.subtitle {
  margin: 4px 0 0;
  color: var(--md-sys-color-on-surface-variant);
  font-size: 14px;
}

.m3-button {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 0 24px;
  height: 40px;
  border-radius: 20px;
  border: none;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.m3-button.filled {
  background: var(--md-sys-color-primary);
  color: var(--md-sys-color-on-primary);
}

.m3-button.filled:hover {
  box-shadow: var(--md-sys-elevation-1);
  background: var(--md-sys-color-primary-container);
  color: var(--md-sys-color-on-primary-container);
}

.m3-button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* 总览卡片部分 */
.overview-section {
  margin-bottom: 32px;
}

.overview-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 16px;
}

.overview-card {
  background: var(--md-sys-color-surface-container);
  border-radius: 20px;
  padding: 20px;
  display: flex;
  align-items: center;
  gap: 16px;
  transition: all 0.2s;
}

.overview-card:hover {
  transform: translateY(-2px);
  box-shadow: var(--md-sys-elevation-2);
}

.overview-card .card-icon {
  width: 48px;
  height: 48px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  color: white;
}

.overview-card .card-icon .material-symbols-rounded {
  font-size: 28px;
}

.overview-card .card-content {
  flex: 1;
  min-width: 0;
}

.overview-card .label {
  font-size: 12px;
  color: var(--md-sys-color-on-surface-variant);
  margin-bottom: 4px;
  font-weight: 500;
}

.overview-card .value {
  font-size: 28px;
  font-weight: 700;
  line-height: 1;
  margin-bottom: 4px;
  font-family: 'Noto Sans SC', 'SF Pro Display', -apple-system, sans-serif;
}

.overview-card .value.primary {
  color: var(--md-sys-color-primary);
}

.overview-card .value.secondary {
  color: var(--md-sys-color-secondary);
}

.overview-card .value.tertiary {
  color: var(--md-sys-color-tertiary);
}

.overview-card .value.error {
  color: var(--md-sys-color-error);
}

.overview-card .description {
  font-size: 11px;
  color: var(--md-sys-color-on-surface-variant);
  opacity: 0.7;
  line-height: 1.3;
}

/* 标签页 */
.tabs-container {
  margin-bottom: 24px;
  background: var(--md-sys-color-surface-container);
  border-radius: 24px;
  padding: 8px;
  box-shadow: var(--md-sys-elevation-1);
}

.tabs {
  display: flex;
  gap: 8px;
  overflow-x: auto;
}

.tab {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 24px;
  background: transparent;
  border: none;
  border-radius: 16px;
  color: var(--md-sys-color-on-surface-variant);
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
  white-space: nowrap;
}

.tab:hover {
  background: var(--md-sys-color-surface-container-high);
  color: var(--md-sys-color-on-surface);
}

.tab.active {
  background: var(--md-sys-color-primary-container);
  color: var(--md-sys-color-on-primary-container);
}

.tab .material-symbols-rounded {
  font-size: 20px;
}

.tab-content {
  animation: fadeIn 0.3s ease-in-out;
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 24px;
}

.model-card {
  background: var(--md-sys-color-surface-container);
  border-radius: 24px;
  overflow: hidden;
  transition: transform 0.2s, box-shadow 0.2s;
  cursor: pointer;
}

.model-card:hover {
  transform: translateY(-2px);
  box-shadow: var(--md-sys-elevation-2);
  background: var(--md-sys-color-surface-container-high);
}

.card-header {
  padding: 20px 24px 12px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.model-info, .provider-info, .module-info {
  display: flex;
  align-items: center;
  gap: 16px;
  overflow: hidden;
}

.model-icon, .provider-icon, .module-icon {
  color: var(--md-sys-color-on-secondary-container);
  background: var(--md-sys-color-secondary-container);
  padding: 12px;
  border-radius: 50%;
  font-size: 24px;
}

.model-name, .provider-name, .module-name {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: var(--md-sys-color-on-surface);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.card-body {
  padding: 0 24px 24px;
}

.stat-row {
  display: flex;
  justify-content: space-between;
  gap: 16px;
}

.stat-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.label {
  font-size: 12px;
  color: var(--md-sys-color-on-surface-variant);
}

.value {
  font-size: 18px;
  font-family: 'Noto Sans SC', sans-serif;
  color: var(--md-sys-color-on-surface);
  font-weight: 500;
}

.stat-divider {
  height: 1px;
  background: var(--md-sys-color-outline-variant);
  margin: 16px 0;
  opacity: 0.5;
}

.total-row .value.highlight {
  color: var(--md-sys-color-primary);
  font-weight: 700;
  font-size: 24px;
}

/* 提供商和模块网格 */
.provider-grid, .module-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
  gap: 24px;
}

.provider-card, .module-card {
  background: var(--md-sys-color-surface-container);
  border-radius: 24px;
  overflow: hidden;
  transition: transform 0.2s, box-shadow 0.2s;
}

.provider-card:hover, .module-card:hover {
  transform: translateY(-2px);
  box-shadow: var(--md-sys-elevation-2);
}

.stat-grid-2col {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 12px;
}

.stat-item-card {
  background: var(--md-sys-color-surface-container-low);
  padding: 16px;
  border-radius: 16px;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

/* 图表容器 */
.charts-container {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 24px;
}

.chart-card {
  background: var(--md-sys-color-surface-container);
  border-radius: 24px;
  overflow: hidden;
  padding: 24px;
}

.chart-card.wide {
  grid-column: span 2;
}

.chart-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.chart-header h3 {
  margin: 0;
  font-size: 18px;
  color: var(--md-sys-color-on-surface);
}

.chart-subtitle {
  font-size: 12px;
  color: var(--md-sys-color-on-surface-variant);
  padding: 4px 12px;
  background: var(--md-sys-color-surface-container-high);
  border-radius: 8px;
}

.chart-body {
  width: 100%;
  height: 300px;
}

.loading-state, .empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px;
  color: var(--md-sys-color-on-surface-variant);
  gap: 16px;
}

.spinning {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.empty-icon {
  font-size: 64px;
  opacity: 0.5;
}

/* Dialog Styles */
.m3-dialog-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  backdrop-filter: blur(4px);
}

.m3-dialog {
  background: var(--md-sys-color-surface-container);
  width: 90%;
  max-width: 500px;
  border-radius: 28px;
  display: flex;
  flex-direction: column;
  box-shadow: var(--md-sys-elevation-3);
  animation: dialogIn 0.3s cubic-bezier(0.2, 0, 0, 1);
  transition: max-width 0.3s cubic-bezier(0.2, 0, 0, 1);
}

.m3-dialog.has-tasks {
  max-width: 800px;
}

@keyframes dialogIn {
  from { opacity: 0; transform: scale(0.9); }
  to { opacity: 1; transform: scale(1); }
}

.dialog-header {
  padding: 24px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  border-bottom: 1px solid var(--md-sys-color-outline-variant);
}

.dialog-header h3 {
  margin: 0;
  font-size: 22px;
  color: var(--md-sys-color-on-surface);
}

.m3-icon-button {
  background: transparent;
  border: none;
  color: var(--md-sys-color-on-surface-variant);
  cursor: pointer;
  width: 40px;
  height: 40px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: background 0.2s;
}

.m3-icon-button:hover {
  background: var(--md-sys-color-surface-container-highest);
}

.dialog-content {
  padding: 24px;
}

.detail-header {
  display: flex;
  align-items: flex-start;
  gap: 16px;
  margin-bottom: 24px;
}

.detail-icon {
  font-size: 32px;
  color: var(--md-sys-color-primary);
  background: var(--md-sys-color-surface-container-high);
  padding: 12px;
  border-radius: 16px;
}

.detail-title {
  flex: 1;
}

.detail-name {
  font-size: 18px;
  font-weight: 600;
  color: var(--md-sys-color-on-surface);
  margin-bottom: 8px;
  word-break: break-all;
  line-height: 1.4;
}

.detail-badges {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  align-items: center;
}

.detail-badge {
  display: inline-block;
  padding: 4px 12px;
  background: var(--md-sys-color-secondary-container);
  color: var(--md-sys-color-on-secondary-container);
  border-radius: 8px;
  font-size: 12px;
  font-weight: 500;
}

.section-title {
  font-size: 14px;
  font-weight: 500;
  color: var(--md-sys-color-on-surface-variant);
  margin-bottom: 16px;
}

.detail-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
}

.detail-card {
  background: var(--md-sys-color-surface-container-low);
  padding: 16px;
  border-radius: 16px;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.detail-card.filled {
  background: var(--md-sys-color-primary-container);
  color: var(--md-sys-color-on-primary-container);
  grid-column: span 2;
}

.detail-card.filled .detail-label {
  color: var(--md-sys-color-on-primary-container);
  opacity: 0.8;
}

.detail-card.filled .detail-value {
  color: var(--md-sys-color-on-primary-container);
}

.detail-label {
  font-size: 12px;
  color: var(--md-sys-color-on-surface-variant);
}

.detail-value {
  font-size: 20px;
  font-family: 'Noto Sans SC', sans-serif;
  font-weight: 600;
  color: var(--md-sys-color-on-surface);
}

.detail-body-layout {
  display: flex;
  gap: 24px;
}

.stats-section {
  flex: 1;
  min-width: 300px;
}

.tasks-section {
  flex: 1;
  min-width: 250px;
  border-left: 1px solid var(--md-sys-color-outline-variant);
  padding-left: 24px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.tasks-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(120px, 1fr));
  gap: 12px;
}

.task-card {
  background: var(--md-sys-color-secondary-container);
  color: var(--md-sys-color-on-secondary-container);
  padding: 12px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  font-weight: 500;
  transition: transform 0.2s;
}

.task-card:hover {
  transform: translateY(-2px);
}

.task-icon {
  font-size: 18px;
  opacity: 0.8;
}

.task-name {
  line-height: 1.2;
}

@media (max-width: 1200px) {
  .charts-container {
    grid-template-columns: 1fr;
  }
  
  .chart-card.wide {
    grid-column: span 1;
  }
}

/* 时间范围选择器 */
.time-range-selector {
  display: flex;
  gap: 8px;
  background: var(--md-sys-color-surface-container-high);
  padding: 4px;
  border-radius: 16px;
}

.time-range-button {
  padding: 8px 16px;
  border: none;
  background: transparent;
  color: var(--md-sys-color-on-surface-variant);
  font-size: 13px;
  font-weight: 500;
  border-radius: 12px;
  cursor: pointer;
  transition: all 0.2s;
  white-space: nowrap;
}

.time-range-button:hover {
  background: var(--md-sys-color-surface-container-highest);
  color: var(--md-sys-color-on-surface);
}

.time-range-button.active {
  background: var(--md-sys-color-primary);
  color: var(--md-sys-color-on-primary);
  box-shadow: var(--md-sys-elevation-1);
}

@media (max-width: 768px) {
  .view-header {
    flex-direction: column;
    gap: 16px;
  }
  
  .header-actions {
    width: 100%;
    flex-direction: column;
  }
  
  .time-range-selector {
    width: 100%;
    justify-content: space-between;
  }
  
  .detail-body-layout {
    flex-direction: column;
  }
  
  .tasks-section {
    border-left: none;
    border-top: 1px solid var(--md-sys-color-outline-variant);
    padding-left: 0;
    padding-top: 24px;
  }
}
</style>
