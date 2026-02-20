/**
 * Git 环境 API
 * 管理 Git 环境检测、安装和路径配置
 */
import { api } from './index'

// ==================== 类型定义 ====================

export interface GitEnvStatus {
  git_available: boolean
  git_version?: string
  git_path?: string
  git_source: 'custom' | 'portable' | 'system' | 'unknown'
  is_portable: boolean
  system_os: string
}

export interface GitInstallResult {
  success: boolean
  message: string
  install_path?: string
  error?: string
}

export interface GitSetPathResult {
  success: boolean
  message: string
  git_path?: string
  git_version?: string
  error?: string
}

export interface GitInstallGuide {
  platform: string
  method: string
  description: string
  manual_url?: string
  manual_commands?: Record<string, string>
}

// ==================== API 函数 ====================

/**
 * 获取 Git 环境状态
 */
export function getGitEnvStatus() {
  return api.get<GitEnvStatus>('git_env/status')
}

/**
 * 安装 Git
 */
export function installGit() {
  return api.post<GitInstallResult>('git_env/install')
}

/**
 * 设置自定义 Git 路径
 */
export function setGitPath(path: string) {
  return api.post<GitSetPathResult>('git_env/set-path', { path })
}

/**
 * 自动检测 Git
 * 清除当前配置并重新自动检测系统中的 Git
 */
export function autoDetectGit() {
  return api.post<GitSetPathResult>('git_env/auto-detect')
}

/**
 * 获取安装指南
 */
export function getGitInstallGuide() {
  return api.get<{ success: boolean; data: GitInstallGuide; error?: string }>('git_env/install-guide')
}
