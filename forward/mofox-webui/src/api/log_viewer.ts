/**
 * 日志查看器 API
 */
import { api } from './index'

export interface LogFile {
  name: string
  size: number
  size_human: string
  mtime: number
  mtime_human: string
  compressed: boolean
}

export interface LogEntry {
  timestamp: string
  level: string
  logger_name: string
  alias?: string // Logger 别名/显示名称
  logger_color?: string // Logger 颜色
  event: string
  line_number: number
  file_name: string
}

export interface LoggerInfo {
  display: string // 显示名称
  name?: string // 内部名称
  color?: string // 颜色
}

export interface LogStats {
  success: boolean
  total: number
  by_level: Record<string, number>
  by_logger: Record<string, number>
}

export interface LogFilesResponse {
  success: boolean
  files: LogFile[]
}

export interface LogSearchResponse {
  success: boolean
  entries: LogEntry[]
  total: number
  offset: number
  limit: number
}

export interface LogLoggersResponse {
  success: boolean
  loggers: LoggerInfo[]
}

/**
 * 获取日志文件列表
 */
export function getLogFiles() {
  return api.get<LogFilesResponse>('log_viewer/files')
}

/**
 * 搜索日志
 */
export function searchLogs(params: {
  filename: string
  query?: string
  level?: string
  logger_name?: string
  start_time?: string
  end_time?: string
  limit?: number
  offset?: number
  regex?: boolean
}) {
  const searchParams = new URLSearchParams()
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== '') {
      searchParams.append(key, value.toString())
    }
  })
  return api.get<LogSearchResponse>(`log_viewer/search?${searchParams.toString()}`)
}

/**
 * 获取日志文件的 logger 列表
 */
export function getLoggers(filename: string) {
  return api.get<LogLoggersResponse>(`log_viewer/loggers?filename=${encodeURIComponent(filename)}`)
}

/**
 * 获取日志统计信息
 */
export function getLogStats(filename: string) {
  return api.get<LogStats>(`log_viewer/stats?filename=${encodeURIComponent(filename)}`)
}
