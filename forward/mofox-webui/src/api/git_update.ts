/**
 * Git 更新 API
 */
import { api } from './index'

export interface GitStatus {
  git_available: boolean
  git_version?: string
  git_path?: string
  git_source: 'custom' | 'portable' | 'system' | 'unknown'
  is_portable: boolean
  system_os: string
  is_git_repo: boolean
  current_branch?: string
  available_branches: string[]
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
  dependencies_installed?: boolean
  dependencies_message?: string
  venv_type?: string
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

/**
 * 切换分支
 */
export function switchBranch(branch: string) {
  return api.post<{
    success: boolean
    message: string
    current_branch?: string
    error?: string
    dependencies_installed?: boolean
    dependencies_message?: string
    venv_type?: string
  }>('git_update/switch-branch', {
    branch
  })
}

/**
 * 设置自定义 Git 路径
 */
export function setGitPath(path: string) {
  return api.post<{
    success: boolean
    message: string
    git_path?: string
    git_version?: string
    error?: string
  }>('git_update/set-path', {
    path
  })
}

/**
 * 清除自定义 Git 路径
 */
export function clearGitPath() {
  return api.delete<{
    success: boolean
    message: string
    error?: string
  }>('git_update/clear-path')
}
