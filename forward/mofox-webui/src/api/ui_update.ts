/**
 * UI 更新 API
 * 管理 WebUI 静态文件的更新检查、下载和回滚
 */
import { api } from './index'

// ==================== 类型定义 ====================

export interface UIVersionInfo {
  version: string
  build_time: string | null
  commit: string | null
  branch: string | null
  changelog: string[]
}

export interface UIUpdateCheckResult {
  success: boolean
  has_update: boolean
  current_version?: string
  latest_version?: string
  changelog: string[]
  download_size?: number
  error?: string
}

export interface UIUpdateResult {
  success: boolean
  message: string
  version?: string
  backup_name?: string
  error?: string
}

export interface UIBackupInfo {
  name: string
  version?: string
  timestamp: string
  size?: number
}

// ==================== API 函数 ====================

/**
 * 获取当前 UI 版本
 */
export function getUIVersion() {
  return api.get<{ success: boolean; data: UIVersionInfo; error?: string }>('ui_update/version')
}

/**
 * 检查 UI 更新
 */
export function checkUIUpdate() {
  return api.get<UIUpdateCheckResult>('ui_update/check')
}

/**
 * 执行 UI 更新
 */
export function updateUI() {
  return api.post<UIUpdateResult>('ui_update/update')
}

/**
 * 获取 UI 备份列表
 */
export function getUIBackups() {
  return api.get<{ success: boolean; data: UIBackupInfo[]; error?: string }>('ui_update/backups')
}

/**
 * 回滚 UI 版本
 */
export function rollbackUI(backupName: string) {
  return api.post<UIUpdateResult>('ui_update/rollback', {
    backup_name: backupName
  })
}
