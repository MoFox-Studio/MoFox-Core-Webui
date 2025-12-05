import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

// 服务器信息接口
interface ServerInfo {
  host: string
  port: number
}

// 发现服务器的固定端口
const DISCOVERY_PORT = 12138

export const useUserStore = defineStore('user', () => {
  const token = ref<string | null>(localStorage.getItem('mofox_token'))
  const serverInfo = ref<ServerInfo | null>(
    JSON.parse(localStorage.getItem('mofox_server_info') || 'null')
  )

  // 计算API基础URL
  const apiBaseUrl = computed(() => {
    if (serverInfo.value) {
      return `http://${serverInfo.value.host}:${serverInfo.value.port}`
    }
    // 默认值
    return `http://${window.location.hostname}:8000`
  })

  // 计算插件API的完整URL
  const pluginApiUrl = computed(() => {
    return `${apiBaseUrl.value}/plugin-api/webui_auth/auth`
  })

  // 计算登录URL
  const loginUrl = computed(() => {
    return `${pluginApiUrl.value}/login`
  })

  function login(mmcToken: string) {
    token.value = mmcToken
    localStorage.setItem('mofox_token', mmcToken)
    return true
  }

  function logout() {
    token.value = null
    serverInfo.value = null
    localStorage.removeItem('mofox_token')
    localStorage.removeItem('mofox_server_info')
  }

  function isAuthenticated() {
    return !!token.value
  }

  function setServerInfo(info: ServerInfo) {
    serverInfo.value = info
    localStorage.setItem('mofox_server_info', JSON.stringify(info))
  }

  // 获取发现服务器URL
  function getDiscoveryUrl() {
    return `http://${window.location.hostname}:${DISCOVERY_PORT}`
  }

  // 创建带有认证头的fetch请求
  async function authFetch(endpoint: string, options: RequestInit = {}) {
    const headers = new Headers(options.headers)
    if (token.value) {
      headers.set('X-API-Key', token.value)
    }
    
    const url = `${pluginApiUrl.value}${endpoint}`
    return fetch(url, {
      ...options,
      headers
    })
  }

  return {
    token,
    serverInfo,
    apiBaseUrl,
    pluginApiUrl,
    loginUrl,
    login,
    logout,
    isAuthenticated,
    setServerInfo,
    getDiscoveryUrl,
    authFetch
  }
})
