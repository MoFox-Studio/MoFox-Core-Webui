import { MOCK_DATA } from './mock'

/**
 * API 请求模块
 * 统一管理所有 API 请求，提供类型安全的 API 调用接口
 * 
 * 🌟 核心特性：
 * - 统一的请求/响应处理
 * - 自动 Token 管理（从 localStorage 读取并自动添加到请求头）
 * - Demo 模式支持（使用 Mock 数据，无需后端）
 * - 完整的类型定义
 * 
 * 🔄 代理模式说明：
 * - 生产环境：静态文件由发现服务器托管（端口 12138），API 请求通过相对路径自动发送到同一服务器，发现服务器代理到主程序
 * - 开发环境：前端独立运行（npm run dev），通过 Vite 代理将 API 请求转发到发现服务器
 * - Demo 环境：完全本地运行，使用 Mock 数据，不发送实际请求
 * 
 * 📡 请求流程：
 * 1. 前端发起请求 → /plugins/webui_backend/xxx
 * 2. 发现服务器接收 → 转发到主程序的 webui_backend 插件
 * 3. 插件处理请求 → 返回响应
 * 4. 发现服务器 → 返回给前端
 */

// ==================== 配置常量 ====================

/**
 * 发现服务器端口号
 * 固定端口，用于前端获取主程序信息和代理 API 请求
 */
const DISCOVERY_SERVER_PORT = 12138

/**
 * 发现服务器完整 URL
 * 自动使用当前页面的 hostname，适配不同部署环境
 */
const DISCOVERY_SERVER_URL = `http://${window.location.hostname}:${DISCOVERY_SERVER_PORT}`

/**
 * 插件 API 基础路径
 * 所有 API 请求都会加上这个前缀
 */
const PLUGIN_BASE_PATH = '/plugins/webui_backend'

/**
 * 缓存的服务器信息
 * 用于避免重复请求发现服务器（虽然在代理模式下已不常用）
 */
let cachedServerInfo: { host: string; port: number } | null = null

// ==================== 服务器信息接口 ====================

/**
 * 服务器信息接口
 * 定义主程序服务器的连接信息
 */
interface ServerInfo {
  /** 服务器主机地址 */
  host: string
  /** 服务器端口号 */
  port: number
}

// ==================== 服务器信息获取 ====================

/**
 * 从发现服务器获取主程序信息
 * 
 * ⚠️ 注意：在代理模式下，此函数已不常用，保留用于调试
 * 
 * @returns Promise<ServerInfo> 服务器连接信息
 * @throws 当无法连接到发现服务器时抛出错误
 */
export async function getServerInfo(): Promise<ServerInfo> {
  // Demo 模式下直接返回模拟数据
  if (import.meta.env.MODE === 'demo') {
    return { host: 'localhost', port: 8080 }
  }

  // 如果有缓存，直接返回
  if (cachedServerInfo) {
    return cachedServerInfo
  }

  try {
    const response = await fetch(`${DISCOVERY_SERVER_URL}/api/server-info`)
    if (!response.ok) {
      throw new Error(`发现服务器请求失败: ${response.status}`)
    }
    const data = await response.json()
    cachedServerInfo = { host: data.host, port: data.port }
    return cachedServerInfo
  } catch (error) {
    console.error('无法连接到发现服务器:', error)
    throw error
  }
}

/**
 * 清除服务器信息缓存
 * 
 * 用于强制重新获取服务器信息，例如：
 * - 服务器地址发生变化
 * - 需要重新连接
 * - 调试时需要刷新缓存
 */
export function clearServerInfoCache() {
  cachedServerInfo = null
}

/**
 * 获取 API 基础 URL
 * 
 * 🌟 代理模式核心函数：
 * - 生产环境和开发环境都返回空字符串
 * - 使用相对路径，让浏览器自动使用当前页面的地址
 * - 静态文件托管在发现服务器（12138），请求自动发送到该服务器
 * - 发现服务器接收请求后代理到主程序
 * 
 * 工作原理：
 * 1. 前端访问：http://hostname:12138/
 * 2. API 请求：/plugins/webui_backend/xxx（相对路径）
 * 3. 实际请求：http://hostname:12138/plugins/webui_backend/xxx
 * 4. 发现服务器代理到主程序的 webui_backend 插件
 * 
 * @returns Promise<string> 空字符串（使用相对路径）
 */
export async function getApiBaseUrl(): Promise<string> {
  // Demo 模式：返回空字符串，Mock 数据会在 ApiClient.request 中拦截
  if (import.meta.env.MODE === 'demo') {
    return ''
  }
  
  // 🌟 代理模式：返回空字符串，使用相对路径
  return ''
}

/**
 * 获取插件 API 基础 URL
 * 
 * 返回插件 API 的路径前缀，配合 getApiBaseUrl 使用
 * 
 * @returns Promise<string> 插件 API 路径前缀
 */
export async function getPluginBaseUrl(): Promise<string> {
  // Demo 模式：直接返回路径
  if (import.meta.env.MODE === 'demo') {
    return PLUGIN_BASE_PATH
  }
  
  // 🌟 代理模式：直接返回相对路径
  return PLUGIN_BASE_PATH
}

// ==================== API 请求客户端 ====================

/**
 * API 请求客户端类
 * 
 * 核心功能：
 * - 统一的 HTTP 请求封装（GET/POST/PUT/PATCH/DELETE）
 * - 自动 Token 管理（读取、存储、添加到请求头）
 * - Demo 模式支持（Mock 数据拦截）
 * - 错误处理和日志记录
 * - 类型安全的响应处理
 * 
 * 使用示例：
 * ```typescript
 * const api = new ApiClient()
 * api.setToken('your-token')
 * const result = await api.get<DataType>('endpoint')
 * if (result.success) {
 *   console.log(result.data)
 * }
 * ```
 */
class ApiClient {
  /** 认证 Token，用于 API 请求鉴权 */
  private token: string | null = null

  /**
   * 构造函数
   * 自动从 localStorage 读取保存的 Token
   */
  constructor() {
    this.token = localStorage.getItem('mofox_token')
  }

  /**
   * 设置 API Token
   * 
   * Token 会被：
   * 1. 保存到实例变量
   * 2. 持久化到 localStorage
   * 3. 在每次请求时自动添加到 X-API-Key 请求头
   * 
   * @param token - API 令牌，null 表示清除 Token
   */
  setToken(token: string | null) {
    this.token = token
    if (token) {
      localStorage.setItem('mofox_token', token)
    } else {
      localStorage.removeItem('mofox_token')
    }
  }

  /**
   * 获取当前 Token
   * @returns 当前的 API Token，未设置则返回 null
   */
  getToken(): string | null {
    return this.token
  }

  /**
   * 构建完整的 API URL
   * 
   * 组装规则：baseUrl + PLUGIN_BASE_PATH + endpoint
   * 例如：'' + '/plugins/webui_backend' + '/' + 'auth/login'
   * 结果：/plugins/webui_backend/auth/login
   * 
   * @param endpoint - API 端点路径，如 'auth/login'、'/config/list' 等
   * @returns Promise<string> 完整的 API URL（相对路径或绝对路径）
   */
  private async buildUrl(endpoint: string): Promise<string> {
    const baseUrl = await getApiBaseUrl()
    // 标准化端点路径：移除开头的斜杠（如果有）
    const cleanEndpoint = endpoint.startsWith('/') ? endpoint.slice(1) : endpoint
    return `${baseUrl}${PLUGIN_BASE_PATH}/${cleanEndpoint}`
  }

  /**
   * 通用请求方法（核心方法）
   * 
   * 所有 HTTP 请求的入口，处理：
   * 1. Demo 模式拦截（返回 Mock 数据）
   * 2. URL 构建
   * 3. 请求头设置（Token、Content-Type）
   * 4. 发送请求
   * 5. 响应解析
   * 6. 错误处理
   * 
   * 返回格式统一：
   * - success: boolean - 请求是否成功
   * - data?: T - 响应数据（成功时）
   * - error?: string - 错误消息（失败时）
   * - status: number - HTTP 状态码
   * 
   * @template T - 响应数据的类型
   * @param endpoint - API 端点路径，如 'auth/login'
   * @param options - fetch 请求选项（method、body、headers 等）
   * @returns Promise 包含 success、data、error、status 的响应对象
   */
  async request<T = unknown>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<{ success: boolean; data?: T; error?: string; status: number }> {
    // ==================== Demo 模式拦截 ====================
    // 在 Demo 模式下，不发送实际请求，而是返回 Mock 数据
    if (import.meta.env.MODE === 'demo') {
      console.log(`[Demo Mode] Request: ${endpoint}`, options)
      
      // 模拟网络延迟，让 Demo 模式更真实
      await new Promise(resolve => setTimeout(resolve, 500))

      // ==================== 登录请求特殊处理 ====================
      if (endpoint === 'auth/login') {
        // Login.vue 的认证流程：
        // 1. 用户输入密码
        // 2. api.setToken(loginForm.password) - 将密码作为 Token 设置
        // 3. api.get(API_ENDPOINTS.AUTH.LOGIN) - 发送 GET 请求
        // 4. Token 自动添加到 X-API-Key 请求头
        // 5. 后端验证 X-API-Key 是否正确
        
        const token = this.token
        // Demo 模式：密码固定为 'mofox'
        if (token === 'mofox') {
          return { success: true, data: MOCK_DATA.login.data as unknown as T, status: 200 }
        } else {
          return { success: false, error: '密钥错误 (Demo模式密码: mofox)', status: 401 }
        }
      }

      // 其他接口 Mock
      if (endpoint === 'dashboard/overview') return { success: true, data: MOCK_DATA.overview.data as unknown as T, status: 200 }
      if (endpoint === 'dashboard/schedule') return { success: true, data: MOCK_DATA.schedule.data as unknown as T, status: 200 }
      if (endpoint === 'dashboard/monthly_plans') return { success: true, data: MOCK_DATA.monthlyPlans.data as unknown as T, status: 200 }
      if (endpoint === 'stats/llm') return { success: true, data: MOCK_DATA.llmStats.data as unknown as T, status: 200 }
      if (endpoint === 'stats/messages') return { success: true, data: MOCK_DATA.messageStats.data as unknown as T, status: 200 }
      if (endpoint === 'plugins/list') return { success: true, data: MOCK_DATA.plugins.data as unknown as T, status: 200 }
      if (endpoint === 'components/list') return { success: true, data: MOCK_DATA.components.data as unknown as T, status: 200 }
      if (endpoint === 'logs/list') return { success: true, data: MOCK_DATA.logs.data as unknown as T, status: 200 }
      
      // ==================== 初始化相关 API Mock ====================
      // 初始化状态：Demo 模式下返回未初始化，让用户体验初始化配置界面
      if (endpoint === 'initialization/status') {
        // 检查 localStorage 中是否已完成初始化
        const demoInitialized = localStorage.getItem('demo_initialized') === 'true'
        return { success: true, data: { is_initialized: demoInitialized } as unknown as T, status: 200 }
      }
      
      // 获取机器人配置
      if (endpoint === 'initialization/bot-config') {
        return {
          success: true,
          data: {
            qq_account: 123456789,
            nickname: 'MoFox',
            alias_names: ['小狐狸', '狐狸'],
            personality_core: '友善、活泼、乐于助人',
            identity: '一只可爱的AI小狐狸',
            reply_style: '活泼可爱，偶尔卖萌',
            master_users: []
          } as unknown as T,
          status: 200
        }
      }
      
      // 保存机器人配置
      if (endpoint === 'initialization/bot-config' && options.method === 'POST') {
        return { success: true, data: { success: true, message: '配置保存成功' } as unknown as T, status: 200 }
      }
      
      // 获取模型配置
      if (endpoint === 'initialization/model-config') {
        return {
          success: true,
          data: {
            api_key: '',
            provider_name: 'siliconflow',
            base_url: 'https://api.siliconflow.cn/v1'
          } as unknown as T,
          status: 200
        }
      }
      
      // 保存模型配置
      if (endpoint === 'initialization/model-config' && options.method === 'POST') {
        return { success: true, data: { success: true, message: '模型配置保存成功' } as unknown as T, status: 200 }
      }
      
      // 获取 Git 配置
      if (endpoint === 'initialization/git-config') {
        return {
          success: true,
          data: {
            git_path: ''
          } as unknown as T,
          status: 200
        }
      }
      
      // 保存 Git 配置
      if (endpoint === 'initialization/git-config' && options.method === 'POST') {
        return { success: true, data: { success: true, message: 'Git配置保存成功' } as unknown as T, status: 200 }
      }
      
      // 验证 API 密钥
      if (endpoint === 'initialization/validate-api-key') {
        return { success: true, data: { valid: true, message: 'API密钥验证成功 (Demo模式)' } as unknown as T, status: 200 }
      }
      
      // 检测 Git 路径
      if (endpoint === 'initialization/detect-git') {
        return { success: true, data: { found: true, path: 'C:\\Program Files\\Git\\bin\\git.exe' } as unknown as T, status: 200 }
      }
      
      // 完成初始化
      if (endpoint === 'initialization/complete') {
        // 在 localStorage 中标记已完成初始化
        localStorage.setItem('demo_initialized', 'true')
        return { success: true, data: { success: true, message: '初始化完成！' } as unknown as T, status: 200 }
      }

      // 默认返回成功
      return { success: true, data: { success: true } as unknown as T, status: 200 }
    }

    const url = await this.buildUrl(endpoint)
    
    // 🐛 DEBUG: 打印请求详情
    console.log('[API Request]', {
      endpoint,
      url,
      method: options.method || 'GET',
      hasToken: !!this.token,
      timestamp: new Date().toISOString()
    })
    
    const headers = new Headers(options.headers)
    
    // 添加认证头
    if (this.token) {
      headers.set('X-API-Key', this.token)
    }
    
    // 设置默认 Content-Type（除非是 FormData，让浏览器自动设置）
    if (!headers.has('Content-Type') && options.body && !(options.body instanceof FormData)) {
      headers.set('Content-Type', 'application/json')
    }

    // 发送 HTTP 请求
    try {
      const response = await fetch(url, {
        ...options,
        headers
      })

      const status = response.status
      
      // 🐛 DEBUG: 打印响应状态
      console.log('[API Response]', {
        endpoint,
        status,
        ok: response.ok,
        statusText: response.statusText,
        headers: Object.fromEntries(response.headers.entries())
      })

      // 🐛 DEBUG: 读取原始响应文本
      const responseText = await response.text()
      console.log('[API Response Text]', {
        endpoint,
        text: responseText,
        length: responseText.length,
        preview: responseText.substring(0, 1000) // 只显示前1000字符
      })

      // 尝试解析 JSON 响应
      // 大多数 API 返回 JSON 格式，但也可能返回其他格式
      let data: T | undefined
      try {
        data = responseText ? JSON.parse(responseText) : undefined
        // 🐛 DEBUG: 打印响应数据
        console.log('[API Data]', {
          endpoint,
          data,
          dataType: typeof data,
          dataKeys: data && typeof data === 'object' ? Object.keys(data) : null
        })
      } catch (parseError) {
        // 响应不是 JSON 格式（如纯文本、HTML、或空响应）
        console.error('[API Parse Error]', {
          endpoint,
          error: parseError,
          contentType: response.headers.get('content-type'),
          responseText: responseText.substring(0, 1000) // 显示更多文本用于调试
        })
      }

      // 根据 HTTP 状态码判断请求是否成功
      if (response.ok) {
        // 2xx 状态码表示成功
        return { success: true, data, status }
      } else {
        // 非 2xx 状态码表示失败
        // 详细记录错误信息，便于调试
        console.error(`[API Error] 请求失败 ${options.method || 'GET'} ${endpoint}:`, {
          status,
          statusText: response.statusText,
          data,
          headers: Object.fromEntries(response.headers.entries())
        })
        
        // 返回错误响应
        // 优先使用服务器返回的错误消息，否则使用默认消息
        return { 
          success: false, 
          error: (data as Record<string, unknown>)?.error as string || `请求失败: ${status}`,
          status 
        }
      }
    } catch (error) {
      // 捕获网络错误（如断网、超时、CORS 错误等）
      console.error('[API Network Error]', {
        endpoint,
        url,
        error: error instanceof Error ? {
          name: error.name,
          message: error.message,
          stack: error.stack
        } : error
      })
      return { 
        success: false, 
        error: error instanceof Error ? error.message : '网络请求失败',
        status: 0  // 0 表示网络错误
      }
    }
  }

  // ==================== HTTP 方法封装 ====================

  /**
   * GET 请求
   * 
   * 用于获取资源，支持 query 参数
   * 
   * 使用示例：
   * ```typescript
   * // 不带参数
   * await api.get<UserData>('user/profile')
   * 
   * // 带 query 参数
   * await api.get<UserList>('users', { params: { page: 1, limit: 10 } })
   * // 实际请求：/plugins/webui_backend/users?page=1&limit=10
   * ```
   * 
   * @template T - 响应数据类型
   * @param endpoint - API 端点
   * @param options - 请求选项，可包含 params 对象用于 query 参数
   */
  async get<T = unknown>(endpoint: string, options: RequestInit & { params?: Record<string, any> } = {}) {
    // 处理 query 参数
    let finalEndpoint = endpoint
    if (options.params) {
      const searchParams = new URLSearchParams()
      Object.entries(options.params).forEach(([key, value]) => {
        // 只添加有效值（过滤 undefined 和 null）
        if (value !== undefined && value !== null) {
          searchParams.append(key, String(value))
        }
      })
      const queryString = searchParams.toString()
      if (queryString) {
        finalEndpoint = `${endpoint}?${queryString}`
      }
      // 移除 params 属性，避免传递给 fetch
      const { params, ...restOptions } = options
      return this.request<T>(finalEndpoint, { ...restOptions, method: 'GET' })
    }
    return this.request<T>(finalEndpoint, { ...options, method: 'GET' })
  }

  /**
   * POST 请求
   * 
   * 用于创建资源或提交数据
   * 
   * 使用示例：
   * ```typescript
   * // JSON 数据
   * await api.post<CreateResult>('user/create', { name: 'Alice', age: 25 })
   * 
   * // FormData（文件上传）
   * const formData = new FormData()
   * formData.append('file', file)
   * await api.post<UploadResult>('upload', formData)
   * ```
   * 
   * @template T - 响应数据类型
   * @param endpoint - API 端点
   * @param body - 请求体（对象会被 JSON.stringify，FormData 直接传递）
   * @param options - 额外的请求选项
   */
  async post<T = unknown>(endpoint: string, body?: unknown, options: RequestInit = {}) {
    // 特殊处理：FormData 不需要 JSON.stringify，浏览器会自动处理
    const requestBody = body instanceof FormData ? body : (body ? JSON.stringify(body) : undefined)
    
    return this.request<T>(endpoint, {
      ...options,
      method: 'POST',
      body: requestBody
    })
  }

  /**
   * PUT 请求
   * 
   * 用于完整更新资源
   * 
   * @template T - 响应数据类型
   * @param endpoint - API 端点
   * @param body - 请求体（会被 JSON.stringify）
   * @param options - 额外的请求选项
   */
  async put<T = unknown>(endpoint: string, body?: unknown, options: RequestInit = {}) {
    return this.request<T>(endpoint, {
      ...options,
      method: 'PUT',
      body: body ? JSON.stringify(body) : undefined
    })
  }

  /**
   * PATCH 请求
   * 
   * 用于部分更新资源
   * 
   * @template T - 响应数据类型
   * @param endpoint - API 端点
   * @param body - 请求体（会被 JSON.stringify）
   * @param options - 额外的请求选项
   */
  async patch<T = unknown>(endpoint: string, body?: unknown, options: RequestInit = {}) {
    return this.request<T>(endpoint, {
      ...options,
      method: 'PATCH',
      body: body ? JSON.stringify(body) : undefined
    })
  }

  /**
   * DELETE 请求
   * 
   * 用于删除资源
   * 
   * @template T - 响应数据类型
   * @param endpoint - API 端点
   * @param options - 请求选项
   */
  async delete<T = unknown>(endpoint: string, options: RequestInit = {}) {
    return this.request<T>(endpoint, { ...options, method: 'DELETE' })
  }
}

// ==================== 导出 ====================

/**
 * API 客户端单例实例
 * 
 * 整个应用共享一个实例，统一管理 Token 和请求
 * 
 * 使用示例：
 * ```typescript
 * import { api, API_ENDPOINTS } from '@/api'
 * 
 * // 登录
 * api.setToken('your-token')
 * const result = await api.get(API_ENDPOINTS.AUTH.LOGIN)
 * 
 * // 获取数据
 * const data = await api.get<OverviewData>(API_ENDPOINTS.STATS.OVERVIEW)
 * ```
 */
export const api = new ApiClient()

/**
 * 导出 ApiClient 类
 * 如果需要创建独立的实例（如测试），可以使用此类
 */
export { ApiClient }

// ==================== API 端点常量 ====================

/**
 * API 端点路径常量
 * 
 * 集中管理所有 API 端点，避免硬编码字符串
 * 分类：
 * - AUTH: 认证相关
 * - STATS: 统计数据
 * - CONFIG: 配置管理
 * - MODEL: 模型相关
 * - PLUGIN: 插件管理
 * - EMOJI: 表情包管理
 */
export const API_ENDPOINTS = {
  AUTH: {
    LOGIN: 'auth/login',
    LOGOUT: 'auth/logout',
    VERIFY: 'auth/verify',
    HEALTH: 'auth/health'
  },
  STATS: {
    OVERVIEW: 'stats/overview',
    PLUGINS: 'stats/plugins',
    PLUGINS_BY_STATUS: 'stats/plugins-by-status',
    PLUGIN_DETAIL: (name: string) => `stats/plugins/${name}`,
    COMPONENTS_BY_TYPE: (type: string) => `stats/components-by-type/${type}`,
    SYSTEM: 'stats/system',
    SYSTEM_RESTART: 'stats/system/restart',
    SYSTEM_SHUTDOWN: 'stats/system/shutdown',
    SCHEDULE: 'stats/schedule',
    MONTHLY_PLANS: 'stats/monthly-plans',
    LLM_STATS: 'stats/llm-stats',
    MESSAGE_STATS: 'stats/message-stats',
    MODEL_USAGE: 'model_stats/model_usage',
    MODEL_OVERVIEW: 'model_stats/model_overview',
    MODEL_DETAIL: (modelName: string) => `model_stats/model_detail/${modelName}`,
    PROVIDER_STATS: 'model_stats/provider_stats',
    MODULE_STATS: 'model_stats/module_stats',
    CHART_DATA: 'model_stats/chart_data'
  },
  CONFIG: {
    LIST: 'config/list',
    CONTENT: (path: string) => `config/content/${path}`,
    SCHEMA: (path: string) => `config/schema/${path}`,
    SAVE: (path: string) => `config/save/${path}`,
    UPDATE: (path: string) => `config/update/${path}`,
    BACKUPS: (path: string) => `config/backups/${path}`,
    RESTORE: (path: string) => `config/restore/${path}`,
    VALIDATE: 'config/validate'
  },
  MODEL: {
    TEST_MODEL: 'model/test-model',
    GET_MODELS: 'model/get-models'
  },
  PLUGIN: {
    LIST: 'plugin_manager/plugins',
    DETAIL: (name: string) => `plugin_manager/plugins/${name}`,
    STATUS: (name: string) => `plugin_manager/plugins/${name}/status`,
    ENABLE: (name: string) => `plugin_manager/plugins/${name}/enable`,
    DISABLE: (name: string) => `plugin_manager/plugins/${name}/disable`,
    RELOAD: (name: string) => `plugin_manager/plugins/${name}/reload`,
    UNLOAD: (name: string) => `plugin_manager/plugins/${name}/unload`,
    DELETE: (name: string) => `plugin_manager/plugins/${name}/delete`,
    LOAD: (name: string) => `plugin_manager/plugins/${name}/load`,
    COMPONENTS: (name: string) => `plugin_manager/plugins/${name}/components`,
    COMPONENT_ENABLE: (pluginName: string, componentName: string, type: string) => 
      `plugin_manager/plugins/${pluginName}/components/${componentName}/enable?component_type=${type}`,
    COMPONENT_DISABLE: (pluginName: string, componentName: string, type: string) => 
      `plugin_manager/plugins/${pluginName}/components/${componentName}/disable?component_type=${type}`,
    SCAN: 'plugin_manager/plugins/scan',
    RELOAD_ALL: 'plugin_manager/plugins/reload-all',
    BATCH_ENABLE: 'plugin_manager/plugins/batch/enable',
    BATCH_DISABLE: 'plugin_manager/plugins/batch/disable',
    BATCH_RELOAD: 'plugin_manager/plugins/batch/reload'
  },
  EMOJI: {
    LIST: 'emoji/list',
    DETAIL: (hash: string) => `emoji/${hash}`,
    UPLOAD: 'emoji/upload',
    DELETE: (hash: string) => `emoji/${hash}`,
    UPDATE: (hash: string) => `emoji/${hash}`,
    BATCH: 'emoji/batch',
    STATS: 'emoji/stats'
  },
  // 插件配置管理（增强版，支持 Schema）
  PLUGIN_CONFIG: {
    LIST: 'plugin_config/list',
    SCHEMA: (pluginName: string) => `plugin_config/${pluginName}/schema`,
    CONTENT: (pluginName: string) => `plugin_config/${pluginName}/content`,
    SAVE: (pluginName: string) => `plugin_config/${pluginName}/save`,
    UPDATE: (pluginName: string) => `plugin_config/${pluginName}/update`,
    RESET: (pluginName: string) => `plugin_config/${pluginName}/reset`,
    BACKUPS: (pluginName: string) => `plugin_config/${pluginName}/backups`,
    RESTORE: (pluginName: string, backupName: string) => `plugin_config/${pluginName}/restore/${backupName}`,
    VALIDATE: (pluginName: string) => `plugin_config/${pluginName}/validate`
  }
} as const

// ==================== 类型定义 ====================
// 以下定义了所有 API 响应的 TypeScript 类型
// 提供完整的类型安全，IDE 可以自动补全和类型检查

/**
 * 插件统计信息
 * 用于仪表盘展示插件的各种状态数量
 */
export interface PluginStats {
  loaded: number
  registered: number
  failed: number
  enabled: number
  disabled: number
}

/**
 * 组件统计信息
 * 统计系统中各类组件的数量和状态
 */
export interface ComponentStats {
  /** 组件总数 */
  total: number
  /** 已启用的组件数 */
  enabled: number
  /** 已禁用的组件数 */
  disabled: number
  /** 按类型分组的组件统计（如：handler、decorator、scheduler 等） */
  by_type: Record<string, { total: number; enabled: number; disabled: number }>
}

/**
 * 聊天流统计信息
 * 统计各种聊天流的数量
 */
export interface ChatStats {
  /** 总聊天流数 */
  total_streams: number
  /** 群组聊天流数 */
  group_streams: number
  /** 私聊流数 */
  private_streams: number
  /** QQ 聊天流数 */
  qq_streams: number
}

/**
 * 系统统计信息
 * 系统运行状态的关键指标
 */
export interface SystemStats {
  /** 系统运行时间（秒） */
  uptime_seconds: number
  /** 内存使用量（MB） */
  memory_usage_mb: number
  /** CPU 使用率（百分比） */
  cpu_percent: number
}

/**
 * 仪表盘总览数据
 * 汇总所有关键统计信息
 */
export interface DashboardOverview {
  /** 插件统计 */
  plugins: PluginStats
  /** 组件统计 */
  components: ComponentStats
  /** 聊天流统计 */
  chats: ChatStats
  /** 系统统计 */
  system: SystemStats
}

/**
 * 插件详情信息
 * 单个插件的基本信息
 */
export interface PluginDetail {
  /** 插件名称（内部标识） */
  name: string
  /** 插件显示名称 */
  display_name: string
  /** 插件版本号 */
  version: string
  /** 插件作者 */
  author: string
  /** 是否已启用 */
  enabled: boolean
  /** 组件数量 */
  components_count: number
}

/**
 * 插件列表响应
 * 返回插件列表及总数
 */
export interface PluginListResponse {
  /** 插件列表 */
  plugins: PluginDetail[]
  /** 插件总数 */
  total: number
}

/**
 * 系统状态响应
 * 系统运行状态的详细信息
 */
export interface SystemStatusResponse {
  /** 运行时间（秒） */
  uptime_seconds: number
  /** 格式化的运行时间（如 "2天 3小时"） */
  uptime_formatted: string
  /** 内存使用量（MB） */
  memory_usage_mb: number
  /** 格式化的内存使用量（如 "128.5 MB"） */
  memory_usage_formatted: string
  /** CPU 使用率（百分比） */
  cpu_percent: number
  /** 线程数 */
  threads: number
}

/**
 * 日程活动项
 * 单个时间段的活动安排
 */
export interface ScheduleActivity {
  /** 时间范围（如 "09:00-10:00"） */
  time_range: string
  /** 活动内容描述 */
  activity: string
}

/**
 * 日程响应
 * 某一天的完整日程安排
 */
export interface ScheduleResponse {
  /** 日期（YYYY-MM-DD） */
  date: string
  /** 活动列表 */
  activities: ScheduleActivity[]
  /** 当前正在进行的活动 */
  current_activity: ScheduleActivity | null
}

/**
 * 月度计划响应
 * 某个月的计划列表
 */
export interface MonthlyPlanResponse {
  /** 计划列表 */
  plans: string[]
  /** 计划总数 */
  total: number
  /** 月份（YYYY-MM） */
  month: string
}

/**
 * LLM 使用统计响应
 * 大语言模型的使用情况统计
 */
export interface LLMStatsResponse {
  /** 总请求次数 */
  total_requests: number
  /** 总花费（单位：元或美元） */
  total_cost: number
  /** 总令牌数 */
  total_tokens: number
  /** 输入令牌数 */
  input_tokens: number
  /** 输出令牌数 */
  output_tokens: number
}

/**
 * 消息统计数据点
 * 时间序列数据中的单个点
 */
export interface MessageStatsDataPoint {
  /** 时间戳（ISO 格式） */
  timestamp: string
  /** 收到的消息数 */
  received: number
  /** 发送的消息数 */
  sent: number
}

/**
 * 消息统计响应
 * 消息收发的时间序列统计
 */
export interface MessageStatsResponse {
  /** 数据点列表（时间序列） */
  data_points: MessageStatsDataPoint[]
  /** 总接收消息数 */
  total_received: number
  /** 总发送消息数 */
  total_sent: number
  /** 统计周期（如 "last_24_hours"） */
  period: string
}

/**
 * 插件列表项（带错误信息）
 * 用于按状态分组的插件列表，包含加载失败信息
 */
export interface PluginListItem {
  /** 插件名称 */
  name: string
  /** 显示名称 */
  display_name: string
  /** 版本号 */
  version: string
  /** 作者 */
  author: string
  /** 是否启用 */
  enabled: boolean
  /** 组件数量 */
  components_count: number
  /** 错误信息（加载失败时） */
  error?: string
}

/**
 * 按状态分组的插件列表
 * 将插件分为已加载和加载失败两组
 */
export interface PluginsByStatusResponse {
  /** 成功加载的插件 */
  loaded: PluginListItem[]
  /** 加载失败的插件 */
  failed: PluginListItem[]
}

/**
 * 组件项
 * 单个组件的详细信息
 */
export interface ComponentItem {
  /** 组件名称 */
  name: string
  /** 所属插件名称 */
  plugin_name: string
  /** 组件描述 */
  description: string
  /** 是否启用 */
  enabled: boolean
}

/**
 * 按类型分组的组件列表
 * 返回特定类型的所有组件
 */
export interface ComponentsByTypeResponse {
  /** 组件类型（如 "handler"、"decorator" 等） */
  component_type: string
  /** 组件列表 */
  components: ComponentItem[]
  /** 总数 */
  total: number
  /** 已启用数 */
  enabled: number
  /** 已禁用数 */
  disabled: number
}

// ==================== API 便捷方法 ====================
// 以下函数封装了常用的 API 调用，简化使用
// 优势：
// 1. 类型安全：自动推断响应类型
// 2. 参数验证：提供默认值和参数校验
// 3. 代码简洁：一行代码完成复杂调用

/**
 * 获取仪表盘总览数据
 * 
 * 包含：插件统计、组件统计、聊天流统计、系统统计
 * 
 * @returns Promise 包含总览数据的响应对象
 */
export async function getDashboardOverview() {
  return api.get<DashboardOverview>(API_ENDPOINTS.STATS.OVERVIEW)
}

/**
 * 获取插件列表（按状态分组，用于仪表盘）
 */
export async function getPluginsByStatus() {
  return api.get<PluginsByStatusResponse>(API_ENDPOINTS.STATS.PLUGINS_BY_STATUS)
}

/**
 * 获取插件详情（Stats API，用于仪表盘）
 */
export async function getPluginDetailForStats(pluginName: string) {
  return api.get<{ success: boolean; plugin?: Record<string, unknown>; error?: string }>(
    API_ENDPOINTS.STATS.PLUGIN_DETAIL(pluginName)
  )
}

/**
 * 获取系统状态
 */
export async function getSystemStatus() {
  return api.get<SystemStatusResponse>(API_ENDPOINTS.STATS.SYSTEM)
}

/**
 * 重启 Bot
 */
export async function restartBot() {
  return api.post<{ success: boolean; message?: string; error?: string }>(
    API_ENDPOINTS.STATS.SYSTEM_RESTART
  )
}

/**
 * 关闭 Bot
 */
export async function shutdownBot() {
  return api.post<{ success: boolean; message?: string; error?: string }>(
    API_ENDPOINTS.STATS.SYSTEM_SHUTDOWN
  )
}

/**
 * 获取今日日程
 */
export async function getTodaySchedule(date?: string) {
  const endpoint = date 
    ? `${API_ENDPOINTS.STATS.SCHEDULE}?date=${date}` 
    : API_ENDPOINTS.STATS.SCHEDULE
  return api.get<ScheduleResponse>(endpoint)
}

/**
 * 获取月度计划
 */
export async function getMonthlyPlans(month?: string, limit: number = 10) {
  let endpoint = API_ENDPOINTS.STATS.MONTHLY_PLANS
  const params = new URLSearchParams()
  if (month) params.append('month', month)
  if (limit) params.append('limit', limit.toString())
  const queryString = params.toString()
  if (queryString) endpoint += `?${queryString}`
  return api.get<MonthlyPlanResponse>(endpoint)
}

/**
 * 获取 LLM 使用统计
 */
export async function getLLMStats(period: 'last_hour' | 'last_24_hours' | 'last_7_days' | 'last_30_days' = 'last_24_hours') {
  const endpoint = `${API_ENDPOINTS.STATS.LLM_STATS}?period=${period}`
  return api.get<LLMStatsResponse>(endpoint)
}

/**
 * 获取消息收发统计
 */
export async function getMessageStats(period: 'last_hour' | 'last_24_hours' | 'last_7_days' | 'last_30_days' = 'last_24_hours') {
  const endpoint = `${API_ENDPOINTS.STATS.MESSAGE_STATS}?period=${period}`
  return api.get<MessageStatsResponse>(endpoint)
}

/**
 * 获取按类型分组的组件列表
 */
export async function getComponentsByType(componentType: string, enabledOnly: boolean = false) {
  const endpoint = `${API_ENDPOINTS.STATS.COMPONENTS_BY_TYPE(componentType)}?enabled_only=${enabledOnly}`
  return api.get<ComponentsByTypeResponse>(endpoint)
}

// ==================== 配置管理相关类型 ====================

/** 配置文件信息 */
export interface ConfigFileInfo {
  name: string
  display_name: string
  path: string
  type: 'main' | 'model' | 'plugin'
  plugin_name?: string
  description?: string
  last_modified?: string
}

/** 配置文件列表响应 */
export interface ConfigListResponse {
  configs: ConfigFileInfo[]
  total: number
}

/** 配置文件内容响应 */
export interface ConfigContentResponse {
  success: boolean
  path: string
  content?: string
  parsed?: Record<string, unknown>
  error?: string
}

/** 配置字段 */
export interface ConfigSchemaField {
  key: string
  full_key: string
  type: string
  value: unknown
  description?: string
  items_count?: number
  readonly?: boolean
}

/** 配置 Section */
export interface ConfigSection {
  name: string
  display_name: string
  fields: ConfigSchemaField[]
}

/** 配置模式响应 */
export interface ConfigSchemaResponse {
  success: boolean
  path: string
  sections: ConfigSection[]
  error?: string
}

/** 保存配置响应 */
export interface SaveConfigResponse {
  success: boolean
  message?: string
  backup_path?: string
  error?: string
}

/** 配置备份信息 */
export interface ConfigBackupInfo {
  name: string
  path: string
  created_at: string
  size: number
}

/** 配置备份列表响应 */
export interface ConfigBackupsResponse {
  success: boolean
  backups: ConfigBackupInfo[]
  error?: string
}

/** 验证 TOML 响应 */
export interface ValidateTomlResponse {
  success: boolean
  valid?: boolean
  message?: string
  line?: number
  col?: number
  error?: string
}

/**
 * 模型测试响应
 * 测试模型连通性的结果
 */
export interface ModelTestResponse {
  /** 是否成功 */
  success: boolean
  /** 模型名称 */
  model_name: string
  /** 是否连接成功 */
  connected: boolean
  /** 响应时间（毫秒） */
  response_time?: number
  /** 测试响应文本 */
  response_text?: string
  /** 错误信息 */
  error?: string
}

/**
 * 模型信息
 * LLM 模型的基本信息
 */
export interface ModelInfo {
  /** 模型 ID */
  id: string
  /** 模型名称 */
  name: string
  /** 创建时间戳 */
  created?: number
  /** 所有者（如 "openai"、"anthropic"） */
  owned_by?: string
}

/**
 * 获取模型列表请求
 * 用于从 API 提供商获取可用模型
 */
export interface GetModelsRequest {
  /** 提供商名称（如 "openai"、"anthropic"） */
  provider_name: string
  /** API 基础 URL */
  base_url: string
  /** API 密钥 */
  api_key: string
  /** 客户端类型（可选） */
  client_type?: string
}

/**
 * 获取模型列表响应
 * 返回可用的模型列表
 */
export interface GetModelsResponse {
  /** 是否成功 */
  success: boolean
  /** 模型列表 */
  models: ModelInfo[]
  /** 错误信息 */
  error?: string
}

// ==================== 配置管理 API 方法 ====================

/**
 * 获取配置文件列表
 */
export async function getConfigList() {
  return api.get<ConfigListResponse>(API_ENDPOINTS.CONFIG.LIST)
}

/**
 * 获取配置文件内容
 */
export async function getConfigContent(path: string) {
  return api.get<ConfigContentResponse>(API_ENDPOINTS.CONFIG.CONTENT(path))
}

/**
 * 获取配置文件结构（用于可视化编辑）
 */
export async function getConfigSchema(path: string) {
  return api.get<ConfigSchemaResponse>(API_ENDPOINTS.CONFIG.SCHEMA(path))
}

/**
 * 保存配置文件（原始 TOML）
 */
export async function saveConfig(path: string, content: string, createBackup: boolean = true) {
  return api.post<SaveConfigResponse>(API_ENDPOINTS.CONFIG.SAVE(path), {
    content,
    create_backup: createBackup
  })
}

/**
 * 更新配置文件（可视化编辑）
 */
export async function updateConfig(path: string, updates: Record<string, unknown>, createBackup: boolean = true) {
  return api.post<SaveConfigResponse>(API_ENDPOINTS.CONFIG.UPDATE(path), {
    updates,
    create_backup: createBackup
  })
}

// ==================== 插件管理类型定义 ====================

/** 插件项 */
export interface PluginItem {
  name: string
  display_name: string
  version: string
  author: string
  description?: string
  enabled: boolean
  loaded: boolean
  components_count: number
  last_updated?: string
  config_path?: string
  error?: string
  plugin_type?: string  // 插件类型: "system" 表示系统插件
}

/** 插件管理列表响应 */
export interface PluginManageListResponse {
  success: boolean
  plugins: PluginItem[]
  failed_plugins: PluginItem[]  // 加载失败的插件列表
  total: number
  loaded: number
  enabled: number
  failed: number
  error?: string
}

/** 组件项 */
export interface PluginComponent {
  name: string
  type: string
  description?: string
  enabled: boolean
  plugin_name: string
  details?: Record<string, unknown>
}

/** 组件列表响应 */
export interface ComponentsResponse {
  success: boolean
  plugin_name: string
  components: PluginComponent[]
  total: number
  enabled: number
  disabled: number
  error?: string
}

/** 插件详细信息 */
export interface PluginDetailInfo {
  name: string
  display_name: string
  version: string
  author: string
  description?: string
  enabled: boolean
  loaded: boolean
  components: PluginComponent[]
  components_count: number
  config: {
    path: string
    exists: boolean
  }
  metadata?: Record<string, unknown>
}

/** 插件详情响应 */
export interface PluginDetailResponse {
  success: boolean
  plugin?: PluginDetailInfo
  error?: string
}

/** 操作响应 */
export interface OperationResponse {
  success: boolean
  message?: string
  error?: string
}

/** 扫描结果响应 */
export interface ScanResultResponse {
  success: boolean
  registered: number
  loaded: number
  failed: number
  new_plugins: string[]
  error?: string
}

/** 批量操作响应 */
export interface BatchOperationResponse {
  success: boolean
  results: Record<string, { success: boolean; message?: string; error?: string }>
  total: number
  succeeded: number
  failed: number
}

// ==================== 插件管理 API 方法 ====================

/**
 * 获取所有插件列表
 */
export async function getPluginList() {
  return api.get<PluginManageListResponse>(API_ENDPOINTS.PLUGIN.LIST)
}

/**
 * 获取插件详情
 */
export async function getPluginDetail(pluginName: string) {
  return api.get<PluginDetailResponse>(API_ENDPOINTS.PLUGIN.DETAIL(pluginName))
}

/**
 * 获取插件状态
 */
export async function getPluginStatus(pluginName: string) {
  return api.get<{ success: boolean; plugin_name: string; loaded: boolean; enabled: boolean }>(
    API_ENDPOINTS.PLUGIN.STATUS(pluginName)
  )
}

/**
 * 启用插件
 */
export async function enablePlugin(pluginName: string) {
  return api.post<OperationResponse>(API_ENDPOINTS.PLUGIN.ENABLE(pluginName))
}

/**
 * 禁用插件
 */
export async function disablePlugin(pluginName: string) {
  return api.post<OperationResponse>(API_ENDPOINTS.PLUGIN.DISABLE(pluginName))
}

/**
 * 重载插件
 */
export async function reloadPlugin(pluginName: string) {
  return api.post<OperationResponse>(API_ENDPOINTS.PLUGIN.RELOAD(pluginName))
}

/**
 * 卸载插件
 */
export async function unloadPlugin(pluginName: string) {
  return api.post<OperationResponse>(API_ENDPOINTS.PLUGIN.UNLOAD(pluginName))
}

/**
 * 删除插件（删除文件夹）
 */
export async function deletePlugin(pluginName: string) {
  return api.delete<OperationResponse>(API_ENDPOINTS.PLUGIN.DELETE(pluginName))
}

/**
 * 加载插件
 */
export async function loadPlugin(pluginName: string) {
  return api.post<OperationResponse>(API_ENDPOINTS.PLUGIN.LOAD(pluginName))
}

/**
 * 获取插件的所有组件
 */
export async function getPluginComponents(pluginName: string) {
  return api.get<ComponentsResponse>(API_ENDPOINTS.PLUGIN.COMPONENTS(pluginName))
}

/**
 * 启用组件
 */
export async function enableComponent(pluginName: string, componentName: string, componentType: string) {
  return api.post<OperationResponse>(
    API_ENDPOINTS.PLUGIN.COMPONENT_ENABLE(pluginName, componentName, componentType)
  )
}

/**
 * 禁用组件
 */
export async function disableComponent(pluginName: string, componentName: string, componentType: string) {
  return api.post<OperationResponse>(
    API_ENDPOINTS.PLUGIN.COMPONENT_DISABLE(pluginName, componentName, componentType)
  )
}

/**
 * 扫描新插件
 */
export async function scanPlugins(loadAfterRegister: boolean = true) {
  return api.post<ScanResultResponse>(API_ENDPOINTS.PLUGIN.SCAN, {
    load_after_register: loadAfterRegister
  })
}

/**
 * 重载所有插件
 */
export async function reloadAllPlugins() {
  return api.post<OperationResponse>(API_ENDPOINTS.PLUGIN.RELOAD_ALL)
}

/**
 * 批量启用插件
 */
export async function batchEnablePlugins(pluginNames: string[]) {
  return api.post<BatchOperationResponse>(API_ENDPOINTS.PLUGIN.BATCH_ENABLE, {
    plugin_names: pluginNames
  })
}

/**
 * 批量禁用插件
 */
export async function batchDisablePlugins(pluginNames: string[]) {
  return api.post<BatchOperationResponse>(API_ENDPOINTS.PLUGIN.BATCH_DISABLE, {
    plugin_names: pluginNames
  })
}

/**
 * 批量重载插件
 */
export async function batchReloadPlugins(pluginNames: string[]) {
  return api.post<BatchOperationResponse>(API_ENDPOINTS.PLUGIN.BATCH_RELOAD, {
    plugin_names: pluginNames
  })
}

/**
 * 获取配置备份列表
 */
export async function getConfigBackups(path: string) {
  return api.get<ConfigBackupsResponse>(API_ENDPOINTS.CONFIG.BACKUPS(path))
}

/**
 * 从备份恢复配置
 */
export async function restoreConfigBackup(path: string, backupName: string) {
  return api.post<SaveConfigResponse>(`${API_ENDPOINTS.CONFIG.RESTORE(path)}?backup_name=${encodeURIComponent(backupName)}`)
}

/**
 * 测试模型连通性
 */
export async function testModelConnection(modelName: string) {
  return api.post<ModelTestResponse>(API_ENDPOINTS.MODEL.TEST_MODEL, {
    model_name: modelName
  })
}

/**
 * 获取可用模型列表
 */
export async function getAvailableModels(request: GetModelsRequest) {
  return api.post<GetModelsResponse>(API_ENDPOINTS.MODEL.GET_MODELS, request)
}

/**
 * 验证 TOML 内容
 */
export async function validateToml(content: string) {
  return api.post<ValidateTomlResponse>(API_ENDPOINTS.CONFIG.VALIDATE, content)
}
