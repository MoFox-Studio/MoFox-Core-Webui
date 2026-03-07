/**
 * @file tagIconMapper.ts
 * @description Tag 到 Material Symbols 图标的映射工具
 * 
 * 根据后端定义的 16 个预设 tag 值，映射到对应的 Material Symbols 图标。
 * 
 * Tag 列表：
 * - general: 通用配置
 * - security: 安全与权限
 * - network: 网络与连接
 * - ai: AI/LLM 相关
 * - database: 数据库配置
 * - user: 用户与身份
 * - timer: 定时与调度
 * - performance: 性能优化
 * - text: 文本处理
 * - list: 列表配置
 * - advanced: 高级选项
 * - debug: 调试日志
 * - file: 文件路径
 * - color: 颜色外观
 * - notification: 通知提醒
 * - plugin: 插件相关
 */

export type ConfigTag =
  | 'general'
  | 'security'
  | 'network'
  | 'ai'
  | 'database'
  | 'user'
  | 'timer'
  | 'performance'
  | 'text'
  | 'list'
  | 'advanced'
  | 'debug'
  | 'file'
  | 'color'
  | 'notification'
  | 'plugin'

/**
 * Tag 到 Material Symbols 图标名称的映射表
 */
export const TAG_TO_ICON: Record<ConfigTag, string> = {
  general: 'settings',
  security: 'lock',
  network: 'lan',
  ai: 'psychology',
  database: 'database',
  user: 'person',
  timer: 'schedule',
  performance: 'speed',
  text: 'subject',
  list: 'view_list',
  advanced: 'tune',
  debug: 'bug_report',
  file: 'folder_open',
  color: 'palette',
  notification: 'notifications',
  plugin: 'extension',
}

/**
 * 根据 tag 获取对应的 Material Symbols 图标名称
 * 
 * @param tag - 配置标签（可以是预设值或 null/undefined）
 * @param fallback - 当 tag 无效时使用的默认图标（默认为 'settings'）
 * @returns Material Symbols 图标名称
 * 
 * @example
 * ```typescript
 * getIconByTag('ai')           // => 'psychology'
 * getIconByTag('security')     // => 'lock'
 * getIconByTag(null)           // => 'settings' (默认)
 * getIconByTag('unknown', 'help')  // => 'help' (自定义 fallback)
 * ```
 */
export function getIconByTag(
  tag: string | null | undefined,
  fallback: string = 'settings'
): string {
  if (!tag) return fallback
  
  const normalizedTag = tag.toLowerCase().trim()
  
  // 检查是否为预设 tag
  if (normalizedTag in TAG_TO_ICON) {
    return TAG_TO_ICON[normalizedTag as ConfigTag]
  }
  
  // 未知 tag，返回 fallback
  return fallback
}

/**
 * 根据 section key 智能推断图标（用于旧数据兼容）
 * 
 * 当 section 没有 tag 时，尝试根据 key 的关键词匹配合适的图标。
 * 这是一个兼容性函数，新代码应该使用显式的 tag。
 * 
 * @param sectionKey - section 的 key 值
 * @returns Material Symbols 图标名称
 * 
 * @example
 * ```typescript
 * inferIconFromKey('database_config')    // => 'database'
 * inferIconFromKey('api_settings')       // => 'lan'
 * inferIconFromKey('llm_config')         // => 'psychology'
 * inferIconFromKey('unknown_section')    // => 'folder'
 * ```
 */
export function inferIconFromKey(sectionKey: string): string {
  const key = sectionKey.toLowerCase()
  
  // 关键词到图标的映射规则（优先级从高到低）
  const keywordRules: Array<{ keywords: string[], icon: string }> = [
    // 数据库相关
    { keywords: ['database', 'db', 'sql', 'postgres', 'mysql', 'sqlite'], icon: 'database' },
    // AI/LLM 相关
    { keywords: ['ai', 'llm', 'model', 'chat', 'gpt', 'personality', '智能'], icon: 'psychology' },
    // 网络相关
    { keywords: ['api', 'network', 'http', 'websocket', 'connection', '网络'], icon: 'lan' },
    // 安全相关
    { keywords: ['permission', 'auth', 'security', 'password', 'token', '权限', '安全'], icon: 'lock' },
    // 用户相关
    { keywords: ['user', 'profile', 'account', '用户'], icon: 'person' },
    // 定时相关
    { keywords: ['schedule', 'timer', 'cron', 'task', '定时', '任务'], icon: 'schedule' },
    // 性能相关
    { keywords: ['performance', 'cache', 'optimize', '性能', '缓存'], icon: 'speed' },
    // 调试相关
    { keywords: ['debug', 'log', 'trace', '调试', '日志'], icon: 'bug_report' },
    // 文件相关
    { keywords: ['file', 'path', 'storage', 'upload', '文件', '路径'], icon: 'folder_open' },
    // 通知相关
    { keywords: ['notification', 'alert', 'message', '通知', '消息'], icon: 'notifications' },
    // 插件相关
    { keywords: ['plugin', 'extension', 'addon', '插件', '扩展'], icon: 'extension' },
    // 外观相关
    { keywords: ['ui', 'theme', 'color', 'appearance', 'style', '主题', '外观'], icon: 'palette' },
    // 功能相关
    { keywords: ['feature', 'toggle', 'switch', '功能', '开关'], icon: 'toggle_on' },
    // 系统相关
    { keywords: ['system', 'bot', 'core', '系统', '核心'], icon: 'settings' },
  ]
  
  // 按顺序匹配关键词
  for (const rule of keywordRules) {
    if (rule.keywords.some(keyword => key.includes(keyword))) {
      return rule.icon
    }
  }
  
  // 默认图标
  return 'folder'
}

/**
 * 获取 section 的图标（优先使用 tag，然后尝试推断）
 * 
 * @param section - section 对象（包含 tag 和 key）
 * @param fallback - 最终的默认图标
 * @returns Material Symbols 图标名称
 * 
 * @example
 * ```typescript
 * getSectionIcon({ tag: 'ai', key: 'llm_config' })        // => 'psychology' (使用 tag)
 * getSectionIcon({ tag: null, key: 'database_config' })   // => 'database' (推断)
 * getSectionIcon({ tag: null, key: 'unknown' })           // => 'folder' (默认)
 * ```
 */
export function getSectionIcon(
  section: { tag?: string | null; key: string },
  fallback: string = 'folder'
): string {
  // 1. 优先使用显式 tag
  if (section.tag) {
    const icon = getIconByTag(section.tag, null as any)
    if (icon !== null) return icon
  }
  
  // 2. 尝试从 key 推断
  const inferred = inferIconFromKey(section.key)
  if (inferred !== 'folder') return inferred
  
  // 3. 使用 fallback
  return fallback
}

/**
 * 获取字段的图标（field 级别的图标显示，可选）
 * 
 * @param field - 字段对象（包含 tag）
 * @param fallback - 默认图标
 * @returns Material Symbols 图标名称或 null（不显示图标）
 * 
 * @example
 * ```typescript
 * getFieldIcon({ tag: 'file' })      // => 'folder_open'
 * getFieldIcon({ tag: null })        // => null (不显示)
 * getFieldIcon({ tag: 'timer' })     // => 'schedule'
 * ```
 */
export function getFieldIcon(
  field: { tag?: string | null },
  fallback: string | null = null
): string | null {
  return field.tag ? getIconByTag(field.tag, fallback ?? 'help_outline') : fallback
}
