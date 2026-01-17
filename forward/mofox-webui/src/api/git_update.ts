/**
 * Git 更新 API
 */
import { api } from './index'

export interface RepoStatus {
  is_git_repo: boolean
  current_branch?: string
  available_branches: string[]
  error?: string
}

export interface UpdateCheck {
  success: boolean
  has_update: boolean
  current_commit?: string
  remote_commit?: string
  commits_behind: number
  update_logs: string[]
  branch?: string
  error?: string
}

export interface UpdateResult {
  success: boolean
  message: string
  updated_files?: string[]
  backup_commit?: string
  error?: string
}

/**
 * 获取主程序仓库状态
 */
export function getRepoStatus() {
  return api.get<RepoStatus>('git_update/status')
}

/**
 * 刷新远程分支列表（需要网络，可能较慢）
 */
export function refreshBranches() {
  return api.post<RepoStatus>('git_update/refresh-branches')
}

/**
 * 检查更新
 */
export function checkUpdates() {
  return api.get<UpdateCheck>('git_update/check')
}

/**
 * 执行更新
 */
export function updateMainProgram(force = false, createBackup = true) {
  return api.post<UpdateResult>('git_update/update', {
    force,
    create_backup: createBackup
  })
}

/**
 * 回滚版本
 */
export function rollbackVersion(commitHash: string) {
  return api.post<UpdateResult>('git_update/rollback', {
    commit_hash: commitHash
  })
}

/**
 * 切换分支
 */
export function switchBranch(branch: string) {
  return api.post<{
    success: boolean
    message: string
    current_branch?: string
    error?: string
  }>('git_update/switch-branch', {
    branch
  })
}

// ==================== 历史版本管理 ====================

/**
 * 主程序历史版本信息
 */
export interface MainBackupInfo {
  commit: string  // 完整 commit hash
  commit_short: string  // 简短 commit hash
  message: string  // 提交消息
  timestamp: string  // 提交时间
  is_current: boolean  // 是否是当前版本
}

/**
 * 主程序提交详情
 */
export interface MainCommitDetail {
  success: boolean
  commit?: string
  commit_short?: string
  message?: string
  body?: string
  author?: string
  timestamp?: string
  files_changed?: { status: string; path: string }[]
  stats?: string
  error?: string
}

/**
 * 获取主程序历史版本列表
 */
export function getMainBackups() {
  return api.get<{ success: boolean; data: MainBackupInfo[]; error?: string }>('git_update/backups')
}

/**
 * 获取主程序提交详情
 */
export function getMainCommitDetail(commitHash: string) {
  return api.get<MainCommitDetail>(`git_update/commits/${commitHash}`)
}
