/**
 * UI 更新 API
 * 管理 WebUI 静态文件的更新检查、下载和回滚
 */
import { api } from './index'

// ==================== 类型定义 ====================

/**
 * UI 状态响应（合并了版本信息和更新检查）
 */
export interface UIStatusResult {
  success: boolean
  // 是否有更新
  has_update: boolean
  // 当前版本
  current_version?: string
  current_commit?: string
  // 远程版本
  latest_version?: string
  latest_commit?: string
  // 更新日志
  changelog: string[]
  commits_behind?: number
  // 更新功能是否启用
  update_enabled?: boolean
  // 当前分支
  current_branch?: string
  // 提示信息
  message?: string
  // 错误信息
  error?: string
}

export interface UIUpdateResult {
  success: boolean
  message: string
  version?: string
  backup_commit?: string  // 更新前的提交 hash（用于回滚）
  commit?: string  // 当前提交 hash
  commit_short?: string  // 当前提交简短 hash
  error?: string
}

export interface UIBackupInfo {
  commit: string  // 完整 commit hash
  commit_short: string  // 简短 commit hash
  version?: string  // 版本号
  message: string  // 提交消息
  timestamp: string  // 提交时间
  is_current: boolean  // 是否是当前版本
}

// ==================== API 函数 ====================

/**
 * 获取 UI 状态（包含版本信息和更新检查）
 */
export function getUIStatus() {
  return api.get<UIStatusResult>('ui_update/status')
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
 * 回滚 UI 版本到指定提交
 */
export function rollbackUI(commitHash: string) {
  return api.post<UIUpdateResult>('ui_update/rollback', {
    commit_hash: commitHash
  })
}

/**
 * 回滚到上一次更新前的状态
 */
export function rollbackUILast() {
  return api.post<UIUpdateResult>('ui_update/rollback-last')
}
