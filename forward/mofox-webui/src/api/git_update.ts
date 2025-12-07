/**
 * Git 更新 API
 */
import { api } from './index'

export interface GitStatus {
  git_available: boolean
  git_version?: string
  git_path?: string
  is_portable: boolean
  system_os: string
  is_git_repo: boolean
  update_mode: 'git' | 'release' | 'unknown'
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
  update_mode: 'git' | 'release'
  current_version?: string
  latest_version?: string
  download_url?: string
}

export interface UpdateResult {
  success: boolean
  message: string
  updated_files?: string[]
  backup_commit?: string
  error?: string
}

/**
 * 获取 Git 状态
 */
export function getGitStatus() {
  return api.get<GitStatus>('git_update/status')
}

/**
 * 安装 Git
 */
export function installGit() {
  return api.post<{ success: boolean; message: string; install_path?: string }>('git_update/install')
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
export function updateMainProgram(force = false, stashLocal = true, createBackup = true) {
  return api.post<UpdateResult>('git_update/update', {
    force,
    stash_local: stashLocal,
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
