/**
 * 插件管理状态管理
 */
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type {
  PluginItem,
  PluginDetailInfo,
  PluginComponent
} from '@/api'
import {
  getPluginList,
  getPluginDetail,
  enablePlugin,
  disablePlugin,
  reloadPlugin,
  unloadPlugin,
  deletePlugin,
  loadPlugin,
  getPluginComponents,
  enableComponent,
  disableComponent,
  scanPlugins,
  reloadAllPlugins,
  batchEnablePlugins,
  batchDisablePlugins,
  batchReloadPlugins
} from '@/api'

export const usePluginStore = defineStore('plugin', () => {
  // ==================== 状态 ====================
  
  /** 插件列表 */
  const plugins = ref<PluginItem[]>([])
  
  /** 加载失败的插件列表 */
  const failedPlugins = ref<PluginItem[]>([])
  
  /** 当前选中的插件详情 */
  const currentPlugin = ref<PluginDetailInfo | null>(null)
  
  /** 当前插件的组件列表 */
  const currentComponents = ref<PluginComponent[]>([])
  
  /** 加载状态 */
  const loading = ref(false)
  
  /** 详情加载状态 */
  const detailLoading = ref(false)
  
  /** 错误信息 */
  const error = ref<string | null>(null)
  
  /** 搜索关键词 */
  const searchKeyword = ref('')
  
  /** 状态筛选 */
  const statusFilter = ref<'all' | 'loaded' | 'enabled' | 'failed'>('all')
  
  // ==================== 计算属性 ====================
  
  /** 统计信息 */
  const stats = computed(() => {
    const total = plugins.value.length + failedPlugins.value.length
    const loaded = plugins.value.filter(p => p.loaded).length
    const enabled = plugins.value.filter(p => p.enabled).length
    const failed = failedPlugins.value.length
    
    return { total, loaded, enabled, failed }
  })
  
  /** 过滤后的插件列表 */
  const filteredPlugins = computed(() => {
    let result = plugins.value
    
    // 状态筛选
    if (statusFilter.value !== 'all') {
      switch (statusFilter.value) {
        case 'loaded':
          result = result.filter(p => p.loaded)
          break
        case 'enabled':
          result = result.filter(p => p.enabled)
          break
        case 'failed':
          result = result.filter(p => p.error)
          break
      }
    }
    
    // 搜索筛选
    if (searchKeyword.value.trim()) {
      const keyword = searchKeyword.value.toLowerCase()
      result = result.filter(p => 
        p.name.toLowerCase().includes(keyword) ||
        p.display_name.toLowerCase().includes(keyword) ||
        p.description?.toLowerCase().includes(keyword)
      )
    }
    
    return result
  })
  
  // ==================== 操作方法 ====================
  
  /**
   * 获取插件列表
   */
  async function fetchPlugins() {
    loading.value = true
    error.value = null
    
    try {
      const response = await getPluginList()
      
      if (response.success && response.data) {
        plugins.value = response.data.plugins
        failedPlugins.value = response.data.failed_plugins || []
        return true
      } else {
        error.value = response.data?.error || response.error || '获取插件列表失败'
        return false
      }
    } catch (err) {
      error.value = err instanceof Error ? err.message : '网络错误'
      return false
    } finally {
      loading.value = false
    }
  }
  
  /**
   * 获取插件详情
   */
  async function fetchPluginDetail(pluginName: string) {
    detailLoading.value = true
    error.value = null
    
    try {
      const response = await getPluginDetail(pluginName)
      
      if (response.success && response.data?.plugin) {
        currentPlugin.value = response.data.plugin
        currentComponents.value = response.data.plugin.components || []
        return true
      } else {
        error.value = response.data?.error || response.error || '获取插件详情失败'
        return false
      }
    } catch (err) {
      error.value = err instanceof Error ? err.message : '网络错误'
      return false
    } finally {
      detailLoading.value = false
    }
  }
  
  /**
   * 刷新当前插件详情
   */
  async function refreshCurrentPlugin() {
    if (currentPlugin.value) {
      return await fetchPluginDetail(currentPlugin.value.name)
    }
    return false
  }
  
  /**
   * 获取插件组件列表
   */
  async function fetchPluginComponents(pluginName: string) {
    try {
      const response = await getPluginComponents(pluginName)
      
      if (response.success && response.data) {
        currentComponents.value = response.data.components
        return true
      } else {
        error.value = response.data?.error || response.error || '获取组件列表失败'
        return false
      }
    } catch (err) {
      error.value = err instanceof Error ? err.message : '网络错误'
      return false
    }
  }
  
  /**
   * 启用插件
   */
  async function enablePluginAction(pluginName: string) {
    try {
      const response = await enablePlugin(pluginName)
      
      if (response.success) {
        // 更新本地状态
        const plugin = plugins.value.find(p => p.name === pluginName)
        if (plugin) {
          plugin.enabled = true
        }
        if (currentPlugin.value?.name === pluginName) {
          currentPlugin.value.enabled = true
        }
        return { success: true, message: response.data?.message }
      } else {
        return { success: false, error: response.data?.error || response.error }
      }
    } catch (err) {
      return { success: false, error: err instanceof Error ? err.message : '网络错误' }
    }
  }
  
  /**
   * 禁用插件
   */
  async function disablePluginAction(pluginName: string) {
    try {
      const response = await disablePlugin(pluginName)
      
      if (response.success) {
        // 更新本地状态
        const plugin = plugins.value.find(p => p.name === pluginName)
        if (plugin) {
          plugin.enabled = false
        }
        if (currentPlugin.value?.name === pluginName) {
          currentPlugin.value.enabled = false
        }
        return { success: true, message: response.data?.message }
      } else {
        return { success: false, error: response.data?.error || response.error }
      }
    } catch (err) {
      return { success: false, error: err instanceof Error ? err.message : '网络错误' }
    }
  }
  
  /**
   * 重载插件
   */
  async function reloadPluginAction(pluginName: string) {
    try {
      const response = await reloadPlugin(pluginName)
      
      if (response.success) {
        // 刷新插件列表和详情
        await fetchPlugins()
        if (currentPlugin.value?.name === pluginName) {
          await fetchPluginDetail(pluginName)
        }
        return { success: true, message: response.data?.message }
      } else {
        return { success: false, error: response.data?.error || response.error }
      }
    } catch (err) {
      return { success: false, error: err instanceof Error ? err.message : '网络错误' }
    }
  }
  
  /**
   * 卸载插件
   */
  async function unloadPluginAction(pluginName: string) {
    try {
      const response = await unloadPlugin(pluginName)
      
      if (response.success) {
        // 从列表中移除
        const index = plugins.value.findIndex(p => p.name === pluginName)
        if (index !== -1) {
          plugins.value.splice(index, 1)
        }
        if (currentPlugin.value?.name === pluginName) {
          currentPlugin.value = null
        }
        return { success: true, message: response.data?.message }
      } else {
        return { success: false, error: response.data?.error || response.error }
      }
    } catch (err) {
      return { success: false, error: err instanceof Error ? err.message : '网络错误' }
    }
  }
  
  /**
   * 删除插件（删除文件夹）
   */
  async function deletePluginAction(pluginName: string) {
    try {
      const response = await deletePlugin(pluginName)
      
      if (response.success) {
        // 从列表中移除
        const index = plugins.value.findIndex(p => p.name === pluginName)
        if (index !== -1) {
          plugins.value.splice(index, 1)
        }
        if (currentPlugin.value?.name === pluginName) {
          currentPlugin.value = null
        }
        return { success: true, message: response.data?.message }
      } else {
        return { success: false, error: response.data?.error || response.error }
      }
    } catch (err) {
      return { success: false, error: err instanceof Error ? err.message : '网络错误' }
    }
  }
  
  /**
   * 加载插件
   */
  async function loadPluginAction(pluginName: string) {
    try {
      const response = await loadPlugin(pluginName)
      
      if (response.success) {
        // 刷新插件列表
        await fetchPlugins()
        return { success: true, message: response.data?.message }
      } else {
        return { success: false, error: response.data?.error || response.error }
      }
    } catch (err) {
      return { success: false, error: err instanceof Error ? err.message : '网络错误' }
    }
  }
  
  /**
   * 启用组件
   */
  async function enableComponentAction(pluginName: string, componentName: string, componentType: string) {
    try {
      const response = await enableComponent(pluginName, componentName, componentType)
      
      if (response.success) {
        // 更新本地状态
        const component = currentComponents.value.find(c => c.name === componentName)
        if (component) {
          component.enabled = true
        }
        return { success: true, message: response.data?.message }
      } else {
        return { success: false, error: response.data?.error || response.error }
      }
    } catch (err) {
      return { success: false, error: err instanceof Error ? err.message : '网络错误' }
    }
  }
  
  /**
   * 禁用组件
   */
  async function disableComponentAction(pluginName: string, componentName: string, componentType: string) {
    try {
      const response = await disableComponent(pluginName, componentName, componentType)
      
      if (response.success) {
        // 更新本地状态
        const component = currentComponents.value.find(c => c.name === componentName)
        if (component) {
          component.enabled = false
        }
        return { success: true, message: response.data?.message }
      } else {
        return { success: false, error: response.data?.error || response.error }
      }
    } catch (err) {
      return { success: false, error: err instanceof Error ? err.message : '网络错误' }
    }
  }
  
  /**
   * 扫描新插件
   */
  async function scanForNewPlugins(loadAfterRegister: boolean = true) {
    loading.value = true
    
    try {
      const response = await scanPlugins(loadAfterRegister)
      
      if (response.success) {
        // 刷新插件列表
        await fetchPlugins()
        return { 
          success: true, 
          data: response.data 
        }
      } else {
        return { success: false, error: response.data?.error || response.error }
      }
    } catch (err) {
      return { success: false, error: err instanceof Error ? err.message : '网络错误' }
    } finally {
      loading.value = false
    }
  }
  
  /**
   * 重载所有插件
   */
  async function reloadAll() {
    loading.value = true
    
    try {
      const response = await reloadAllPlugins()
      
      if (response.success) {
        // 刷新插件列表
        await fetchPlugins()
        return { success: true, message: response.data?.message }
      } else {
        return { success: false, error: response.data?.error || response.error }
      }
    } catch (err) {
      return { success: false, error: err instanceof Error ? err.message : '网络错误' }
    } finally {
      loading.value = false
    }
  }
  
  /**
   * 批量启用插件
   */
  async function batchEnable(pluginNames: string[]) {
    try {
      const response = await batchEnablePlugins(pluginNames)
      
      if (response.data) {
        // 更新本地状态
        pluginNames.forEach(name => {
          const plugin = plugins.value.find(p => p.name === name)
          if (plugin && response.data?.results[name]?.success) {
            plugin.enabled = true
          }
        })
        return response.data
      }
      return { success: false, results: {}, total: 0, succeeded: 0, failed: pluginNames.length }
    } catch (err) {
      return { 
        success: false, 
        results: {}, 
        total: pluginNames.length, 
        succeeded: 0, 
        failed: pluginNames.length 
      }
    }
  }
  
  /**
   * 批量禁用插件
   */
  async function batchDisable(pluginNames: string[]) {
    try {
      const response = await batchDisablePlugins(pluginNames)
      
      if (response.data) {
        // 更新本地状态
        pluginNames.forEach(name => {
          const plugin = plugins.value.find(p => p.name === name)
          if (plugin && response.data?.results[name]?.success) {
            plugin.enabled = false
          }
        })
        return response.data
      }
      return { success: false, results: {}, total: 0, succeeded: 0, failed: pluginNames.length }
    } catch (err) {
      return { 
        success: false, 
        results: {}, 
        total: pluginNames.length, 
        succeeded: 0, 
        failed: pluginNames.length 
      }
    }
  }
  
  /**
   * 批量重载插件
   */
  async function batchReload(pluginNames: string[]) {
    try {
      const response = await batchReloadPlugins(pluginNames)
      
      if (response.data) {
        // 刷新插件列表
        await fetchPlugins()
        return response.data
      }
      return { success: false, results: {}, total: 0, succeeded: 0, failed: pluginNames.length }
    } catch (err) {
      return { 
        success: false, 
        results: {}, 
        total: pluginNames.length, 
        succeeded: 0, 
        failed: pluginNames.length 
      }
    }
  }
  
  /**
   * 清除当前插件
   */
  function clearCurrentPlugin() {
    currentPlugin.value = null
    currentComponents.value = []
  }
  
  /**
   * 设置搜索关键词
   */
  function setSearchKeyword(keyword: string) {
    searchKeyword.value = keyword
  }
  
  /**
   * 设置状态筛选
   */
  function setStatusFilter(status: 'all' | 'loaded' | 'enabled' | 'failed') {
    statusFilter.value = status
  }
  
  /**
   * 清除错误
   */
  function clearError() {
    error.value = null
  }
  
  return {
    // 状态
    plugins,
    failedPlugins,
    currentPlugin,
    currentComponents,
    loading,
    detailLoading,
    error,
    searchKeyword,
    statusFilter,
    
    // 计算属性
    stats,
    filteredPlugins,
    
    // 操作方法
    fetchPlugins,
    fetchPluginDetail,
    refreshCurrentPlugin,
    fetchPluginComponents,
    enablePluginAction,
    disablePluginAction,
    reloadPluginAction,
    unloadPluginAction,
    deletePluginAction,
    loadPluginAction,
    enableComponentAction,
    disableComponentAction,
    scanForNewPlugins,
    reloadAll,
    batchEnable,
    batchDisable,
    batchReload,
    clearCurrentPlugin,
    setSearchKeyword,
    setStatusFilter,
    clearError
  }
})
