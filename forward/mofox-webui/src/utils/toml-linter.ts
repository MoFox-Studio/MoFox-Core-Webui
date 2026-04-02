/**
 * TOML 语法验证器（浏览器端）
 * 结合基础语法检查和 toml 库完整解析
 */

import type { Diagnostic } from '@codemirror/lint'
import type { Text } from '@codemirror/state'
import TOML from 'toml'

/**
 * TOML 语法检查（用于 CodeMirror Lint）
 * @param doc - CodeMirror 文档对象
 * @returns 诊断信息数组
 */
export function lintTOML(doc: Text): Diagnostic[] {
  const diagnostics: Diagnostic[] = []
  const text = doc.toString()

  try {
    // ═══ 阶段 1: 基础语法检查 ═══
    const lines = text.split('\n')

    lines.forEach((line, lineIndex) => {
      const trimmed = line.trim()
      const currentLine = doc.line(lineIndex + 1)
      const lineEnd = currentLine.to

      // 检查未闭合的方括号
      if (trimmed.startsWith('[') && !trimmed.includes(']')) {
        diagnostics.push({
          from: lineEnd,
          to: lineEnd,
          severity: 'error',
          message: '未闭合的方括号：缺少 ]',
        })
      }

      // 检查未闭合的引号
      const singleQuotes = (trimmed.match(/'/g) || []).length
      const doubleQuotes = (trimmed.match(/"/g) || []).length

      if (singleQuotes % 2 !== 0) {
        diagnostics.push({
          from: lineEnd,
          to: lineEnd,
          severity: 'error',
          message: "未闭合的单引号：缺少 '",
        })
      }

      if (doubleQuotes % 2 !== 0 && !trimmed.includes('"""')) {
        diagnostics.push({
          from: lineEnd,
          to: lineEnd,
          severity: 'error',
          message: '未闭合的双引号：缺少 "',
        })
      }

      // 检查重复的 = 号
      const equalCount = (trimmed.match(/=/g) || []).length
      if (equalCount > 1 && !trimmed.includes('==')) {
        diagnostics.push({
          from: lineEnd,
          to: lineEnd,
          severity: 'error',
          message: '一行中包含多个 = 符号',
        })
      }
    })

    // 检查括号匹配
    const bracketStack: Array<{ char: string; pos: number }> = []
    for (let i = 0; i < text.length; i++) {
      const char = text[i]
      if (char === '[') {
        bracketStack.push({ char, pos: i })
      } else if (char === ']') {
        if (bracketStack.length === 0) {
          diagnostics.push({
            from: i,
            to: i + 1,
            severity: 'error',
            message: '多余的 ] 括号，缺少对应的 [',
          })
        } else {
          bracketStack.pop()
        }
      }
    }

    // 未闭合的括号
    bracketStack.forEach((bracket) => {
      diagnostics.push({
        from: bracket.pos,
        to: bracket.pos + 1,
        severity: 'error',
        message: '未闭合的 [ 括号，缺少对应的 ]',
      })
    })

    // ═══ 阶段 2: 完整 TOML 解析验证 ═══
    // 只有在基础检查没有发现致命错误时才进行完整解析
    const hasCriticalErrors = diagnostics.some((d) => d.severity === 'error')

    if (!hasCriticalErrors) {
      try {
        TOML.parse(text)
      } catch (error: any) {
        // 解析失败，从错误对象直接获取行列信息
        const errorMessage = error.message || 'TOML 解析错误'
        const line = error.line
        // column 信息暂未使用，但保留以备将来更精确的错误定位
        // const column = error.column

        let from = doc.length
        let to = doc.length

        // 如果有行号，定位到该行的行尾
        if (line && line > 0 && line <= doc.lines) {
          try {
            const targetLine = doc.line(line)
            from = targetLine.to
            to = targetLine.to
          } catch (e) {
            // 行号无效，使用整个文档末尾
            console.warn(`无效的行号: ${line}`, e)
          }
        }

        // 翻译错误信息为中文
        const translatedError = translateTOMLError(errorMessage)

        diagnostics.push({
          from,
          to,
          severity: 'error',
          message: translatedError,
        })
      }
    }
  } catch (error: any) {
    // 如果检查过程中出错，显示在文档末尾
    diagnostics.push({
      from: doc.length,
      to: doc.length,
      severity: 'error',
      message: `语法检查异常: ${error.message}`,
    })
  }

  return diagnostics
}

/**
 * 翻译 TOML 错误信息为中文
 * 针对 toml@3.0.0 (PEG 解析器) 的错误格式优化
 * @param errorMessage - 原始英文错误信息
 * @returns 中文化的错误信息
 */
function translateTOMLError(errorMessage: string): string {
  const msg = errorMessage.trim()

  // 键重复错误
  if (msg.includes('Cannot redefine existing key')) {
    const match = msg.match(/Cannot redefine existing key '([^']+)'/)
    if (match) {
      return `不能重新定义已存在的键 '${match[1]}'`
    }
    return '不能重新定义已存在的键'
  }

  //数组类型不匹配
  if (msg.includes('Cannot add value of type')) {
    const match = msg.match(/Cannot add value of type (\w+) to array of type (\w+)/)
    if (match && match[1] && match[2]) {
      const typeMap: Record<string, string> = {
        'String': '字符串',
        'Integer': '整数',
        'Float': '浮点数',
        'Boolean': '布尔值',
        'Array': '数组',
        'Table': '表',
      }
      const fromType = typeMap[match[1]] || match[1]
      const toType = typeMap[match[2]] || match[2]
      return `数组类型不匹配：不能将 ${fromType} 添加到 ${toType} 数组中`
    }
    return '数组类型不匹配'
  }

  // Unicode 错误
  if (msg.includes('Invalid Unicode escape code')) {
    const match = msg.match(/Invalid Unicode escape code: ([A-F0-9]+)/)
    if (match) {
      return `无效的 Unicode 转义码: ${match[1]}`
    }
    return '无效的 Unicode 转义码'
  }

  // 未闭合的字符串
  if (msg.includes('Expected "\\"\\"\\"",')) {
    return '未闭合的多行双引号字符串（缺少 """）'
  }
  if (msg.includes("Expected \"'''\"")) {
    return "未闭合的多行单引号字符串（缺少 '''）"
  }
  if (msg.includes('Expected "\\"",') || msg.includes('Expected "\\"" or any character')) {
    return '未闭合的双引号字符串（缺少 "）'
  }
  if (msg.includes("Expected \"'\"") || msg.includes("Expected \"'\" or any character")) {
    return "未闭合的单引号字符串（缺少 '）"
  }

  // 日期时间格式错误
  if (msg.includes('Expected "T" but " " found')) {
    return '日期时间格式错误：应使用 T 而不是空格分隔日期和时间'
  }
  if (msg.includes('Expected "T" but end of input found')) {
    return '日期格式不完整：缺少时间部分（需要 T 和时间）'
  }

  // 内联表换行错误
  if (msg.includes('Expected "}", [ \\t] or [A-Za-z0-9_\\-] but "\\n" found')) {
    return '内联表不能跨越多行（所有内容必须在同一行）'
  }

  // 值后的意外字符
  if (msg.includes('Expected "#", "\\n", "\\r" or [ \\t] but')) {
    return '值后有意外字符（值之后应该是注释或换行）'
  }

  // 输入结束错误
  if (msg.includes('but end of input found')) {
    if (msg.includes('Expected "]"')) {
      return '未闭合的方括号（缺少 ]）'
    }
    if (msg.includes('Expected "}"')) {
      return '未闭合的花括号（缺少 }）'
    }
    if (msg.includes('Expected "="')) {
      return '缺少等号（键后应该跟 = 和值）'
    }
    return '意外的输入结束（TOML 内容不完整）'
  }

  // 缺少等号
  if (msg.includes('Expected "=" or [ \\t]')) {
    return '缺少等号（键和值之间需要 =）'
  }

  // 缺少值
  if (msg.includes("Expected \"'\", \"'''\", \"+\", \"-\", \"[\", \"\\\"\",")) {
    return '缺少值（= 后面应该有一个值）'
  }

  // 通用 PEG 格式错误
  if (msg.includes('Expected') && msg.includes('but') && msg.includes('found')) {
    return 'TOML 语法错误：格式不符合规范'
  }

  return 'TOML 解析错误'
}

/**
 * 格式化 TOML 内容
 * @param content - 原始 TOML 内容
 * @returns 格式化后的 TOML 内容
 */
export function formatTOML(content: string): string {
  try {
    // 解析并重新序列化
    const parsed = TOML.parse(content)
    return stringifyTOML(parsed)
  } catch (error) {
    // 如果解析失败，返回原内容
    throw new Error('无法格式化：TOML 内容包含语法错误')
  }
}

/**
 * 将对象序列化为 TOML 字符串
 * @param obj - 要序列化的对象
 * @param indent - 缩进级别
 * @returns TOML 字符串
 */
function stringifyTOML(obj: any, indent = 0): string {
  const lines: string[] = []
  const indentStr = '  '.repeat(indent)

  for (const [key, value] of Object.entries(obj)) {
    if (value === null || value === undefined) {
      continue
    }

    if (typeof value === 'object' && !Array.isArray(value) && !(value instanceof Date)) {
      // 嵌套对象，作为 section
      if (indent === 0) {
        lines.push(`[${key}]`)
        lines.push(stringifyTOML(value, indent + 1))
      } else {
        lines.push(`${indentStr}[${key}]`)
        lines.push(stringifyTOML(value, indent + 1))
      }
    } else {
      // 普通值
      lines.push(`${indentStr}${key} = ${tomlValueString(value)}`)
    }
  }

  return lines.join('\n')
}

/**
 * 将值转换为 TOML 字符串表示
 * @param value - 值
 * @returns TOML 字符串
 */
function tomlValueString(value: any): string {
  if (typeof value === 'string') {
    // 字符串需要引号
    return `"${value.replace(/\\/g, '\\\\').replace(/"/g, '\\"').replace(/\n/g, '\\n')}"`
  } else if (typeof value === 'boolean') {
    return value.toString()
  } else if (typeof value === 'number') {
    return value.toString()
  } else if (Array.isArray(value)) {
    // 数组
    const items = value.map((v) => tomlValueString(v)).join(', ')
    return `[${items}]`
  } else if (value instanceof Date) {
    return value.toISOString()
  } else if (typeof value === 'object') {
    // 内联表
    const pairs = Object.entries(value)
      .map(([k, v]) => `${k} = ${tomlValueString(v)}`)
      .join(', ')
    return `{ ${pairs} }`
  }
  return String(value)
}
