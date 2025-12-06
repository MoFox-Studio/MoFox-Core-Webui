/**
 * 插件市场 API
 */
import { api } from './index'

export interface PluginManifest {
  name: string
  description: string
  usage: string
  version: string
  author: string
  license: string
  repository_url: string
  keywords?: string[]
  categories?: string[]
  python_dependencies?: string[]
  extra?: string
}

export interface MarketplacePlugin {
  id: string
  manifest: PluginManifest
  createdAt: string
}

export interface MarketplaceListResponse {
  plugins: MarketplacePlugin[]
  installed_plugins: string[]
}

export interface PluginDetailResponse {
  plugin: MarketplacePlugin
  is_installed: boolean
  installed_version?: string
  readme?: string
}

export interface UpdateInfo {
  plugin_id: string
  plugin_name: string
  current_version: string
  latest_version: string
}

export interface CheckUpdatesResponse {
  updates: UpdateInfo[]
}

/**
 * 获取插件市场列表
 */
export function getMarketplacePlugins() {
  return api.get<MarketplaceListResponse>('marketplace/list')
}

/**
 * 获取插件详情
 */
export function getPluginDetail(pluginId: string) {
  return api.get<PluginDetailResponse>(`marketplace/detail/${encodeURIComponent(pluginId)}`)
}

/**
 * 安装插件（默认自动加载）
 */
export function installPlugin(pluginId: string, repositoryUrl: string, autoLoad: boolean = true) {
  return api.post<{ message: string; plugin_name: string; loaded: boolean }>('marketplace/install', {
    plugin_id: pluginId,
    repository_url: repositoryUrl,
    auto_load: autoLoad
  })
}

/**
 * 更新插件
 */
export function updatePlugin(pluginId: string) {
  return api.post<{ message: string }>(`marketplace/update/${encodeURIComponent(pluginId)}`)
}

/**
 * 检查插件更新
 */
export function checkPluginUpdates() {
  return api.get<CheckUpdatesResponse>('marketplace/check-updates')
}
