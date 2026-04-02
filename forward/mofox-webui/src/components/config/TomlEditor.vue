<!--
  @file TomlEditor.vue
  @description 统一的 TOML 源码编辑器组件
  
  基于 CodeMirror 6 实现，提供：
  - TOML 语法高亮
  - 实时语法检查（500ms 防抖）
  - 中文错误提示
  - 代码格式化
  - 深色/浅色主题自适应
  - 行号、代码折叠、搜索功能
-->
<template>
  <div class="toml-editor-wrapper">
    <!-- 工具栏 -->
    <div class="editor-toolbar">
      <div class="toolbar-left">
        <span class="material-symbols-rounded">description</span>
        <span class="file-path">{{ filePath }}</span>
      </div>
    </div>

    <!-- 编辑器容器 -->
    <div ref="editorRef" class="editor-container"></div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, watch, shallowRef } from 'vue'
import { EditorView, basicSetup } from 'codemirror'
import { Decoration, WidgetType } from '@codemirror/view'
import { EditorState, Compartment, StateField } from '@codemirror/state'
import { StreamLanguage } from '@codemirror/language'
import { toml } from '@codemirror/legacy-modes/mode/toml'
import { linter, forEachDiagnostic } from '@codemirror/lint'
import { syntaxHighlighting, HighlightStyle } from '@codemirror/language'
import { tags as t } from '@lezer/highlight'
import { useThemeStore } from '@/stores/theme'
import { lintTOML } from '@/utils/toml-linter'

// 开发模式下的调试标志
const DEBUG = import.meta.env.DEV

// ═══ 行尾诊断信息显示（类似 Error Lens）═══
/**
 * 创建诊断信息小部件
 */
class DiagnosticWidget extends WidgetType {
  message: string
  severity: string

  constructor(message: string, severity: string) {
    super()
    this.message = message
    this.severity = severity
  }

  toDOM() {
    const span = document.createElement('span')
    span.className = `cm-inline-diagnostic cm-inline-diagnostic-${this.severity}`

    // 移动端使用更短的消息（30字符），桌面端稍长（50字符）
    const isMobile = window.innerWidth < 768
    const maxLength = isMobile ? 30 : 50
    const shortMessage =
      this.message.length > maxLength
        ? this.message.substring(0, maxLength - 3) + '...'
        : this.message

    // 移动端只显示图标+简短消息，去掉多余信息
    const displayMessage = isMobile
      ? `⚠ ${shortMessage.split('(')[0]?.trim() || shortMessage}` // 移除括号内的详细位置信息
      : `⚠ ${shortMessage}`

    span.textContent = ` ${displayMessage}`
    span.title = this.message // 完整消息作为 tooltip
    return span
  }

  eq(other: DiagnosticWidget) {
    return other.message === this.message && other.severity === this.severity
  }

  ignoreEvent() {
    return true
  }
}

/**
 * 构建诊断装饰器
 */
function buildDiagnosticDecorations(state: EditorState) {
  const diagnostics: Array<{
    from: number
    to: number
    message: string
    severity: string
  }> = []

  // 收集所有诊断信息
  forEachDiagnostic(state, (diagnostic, from, to) => {
    diagnostics.push({
      from,
      to,
      message: diagnostic.message,
      severity: diagnostic.severity,
    })
  })

  if (DEBUG && diagnostics.length > 0) {
    console.log('[TomlEditor] 检测到诊断信息:', diagnostics.length, '个')
  }

  // 按行分组诊断信息（每行只显示第一个错误）
  const lineMap = new Map<number, { message: string; severity: string }>()
  diagnostics.forEach(({ from, message, severity }) => {
    const line = state.doc.lineAt(from).number
    if (!lineMap.has(line)) {
      // 只保留每行的第一个错误
      lineMap.set(line, { message, severity })
    }
  })

  // 创建装饰器
  const decorationArray: any[] = []
  lineMap.forEach((diag, lineNumber) => {
    const line = state.doc.line(lineNumber)
    const lineEnd = line.to

    // 在行尾添加 widget
    const widget = Decoration.widget({
      widget: new DiagnosticWidget(diag.message, diag.severity),
      side: 1,
    })

    decorationArray.push(widget.range(lineEnd))
  })

  if (DEBUG && decorationArray.length > 0) {
    console.log('[TomlEditor] 创建装饰器:', decorationArray.length, '个')
  }

  return Decoration.set(decorationArray, true)
}

/**
 * 行尾诊断信息扩展
 */
function inlineDiagnostics() {
  const inlineDiagnosticField = StateField.define({
    create(state) {
      if (DEBUG) console.log('[TomlEditor] 初始化诊断装饰器')
      return buildDiagnosticDecorations(state)
    },

    update(decorations, tr) {
      // 如果文档有更改，或者有任何效果（包括 linter 更新），重新构建装饰器
      if (tr.docChanged || tr.effects.length > 0 || tr.selection) {
        return buildDiagnosticDecorations(tr.state)
      }
      // 否则映射现有的装饰器
      return decorations.map(tr.changes)
    },

    provide: (f) => EditorView.decorations.from(f),
  })

  return [
    inlineDiagnosticField,
    EditorView.theme({
      '.cm-inline-diagnostic': {
        display: 'inline',
        whiteSpace: 'nowrap',
        marginLeft: '0.5em',
        fontSize: '0.75em',
        opacity: '0.7',
        fontStyle: 'italic',
        pointerEvents: 'none',
        userSelect: 'none',
        maxWidth: '40vw',
        overflow: 'hidden',
        textOverflow: 'ellipsis',
      },
      '.cm-inline-diagnostic-error': {
        color: '#ef4444',
      },
      '.cm-inline-diagnostic-warning': {
        color: '#ff9800',
      },
      '.cm-inline-diagnostic-info': {
        color: '#3b82f6',
      },
      // 移动端特殊样式
      '@media (max-width: 768px)': {
        '.cm-inline-diagnostic': {
          fontSize: '0.7em',
          marginLeft: '0.3em',
          maxWidth: '30vw',
        },
      },
    }),
  ]
}

// Props
interface Props {
  modelValue: string
  filePath?: string
  readonly?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  filePath: 'config.toml',
  readonly: false,
})

// Emits
const emit = defineEmits<{
  'update:modelValue': [value: string]
}>()

// Refs
const editorRef = ref<HTMLElement | null>(null)
const editorView = shallowRef<EditorView | null>(null)

// Theme
const themeStore = useThemeStore()
const themeCompartment = new Compartment()
const readonlyCompartment = new Compartment()

/**
 * 创建自定义 M3 主题扩展
 * 使语法高亮颜色跟随 Material Design 3 主题
 */
function createM3Theme() {
  // 打印所有使用的 CSS 变量值（仅在开发模式）
  if (DEBUG) {
    const cssVars = [
      '--md-sys-color-on-surface',
      '--md-sys-color-surface',
      '--md-sys-color-primary',
      '--md-sys-color-primary-container',
      '--md-sys-color-surface-container',
      '--md-sys-color-on-surface-variant',
      '--md-sys-color-surface-container-highest',
      '--md-sys-color-surface-container-low',
      '--md-sys-color-secondary-container',
      '--md-sys-color-secondary',
      '--md-sys-color-outline-variant',
      '--md-sys-color-outline',
    ]
    
    const computedStyles = getComputedStyle(document.documentElement)
    console.group('[TomlEditor] M3 主题 CSS 变量值')
    console.log('isDark:', themeStore.isDark)
    cssVars.forEach(varName => {
      const value = computedStyles.getPropertyValue(varName).trim()
      console.log(`${varName}: ${value}`)
    })
    console.groupEnd()
  }

  return EditorView.theme(
    {
      // 编辑器整体样式
      '&': {
        color: 'var(--md-sys-color-on-surface)',
        backgroundColor: 'var(--md-sys-color-surface)',
      },
      // 内容区域
      '.cm-content': {
        caretColor: 'var(--md-sys-color-primary)',
      },
      // 光标和选择
      '.cm-cursor, .cm-dropCursor': {
        borderLeftColor: 'var(--md-sys-color-primary)',
      },
      '&.cm-focused > .cm-scroller > .cm-selectionLayer .cm-selectionBackground, .cm-selectionBackground, .cm-content ::selection':
        {
          backgroundColor: 'var(--md-sys-color-primary-container)',
        },
      // 行号栏
      '.cm-gutters': {
        backgroundColor: 'var(--md-sys-color-surface-container)',
        color: 'var(--md-sys-color-on-surface-variant)',
        border: 'none',
      },
      '.cm-activeLineGutter': {
        backgroundColor: 'var(--md-sys-color-surface-container-highest)',
        color: 'var(--md-sys-color-on-surface)',
      },
      // 当前行高亮
      '.cm-activeLine': {
        backgroundColor: 'var(--md-sys-color-surface-container-low)',
      },
      // 匹配括号
      '&.cm-focused .cm-matchingBracket, &.cm-focused .cm-nonmatchingBracket': {
        backgroundColor: 'var(--md-sys-color-secondary-container)',
        outline: '1px solid var(--md-sys-color-secondary)',
      },
    },
    { dark: themeStore.isDark }
  )
}

/**
 * 创建语法高亮样式扩展
 * 对颜色映射进行美化调优，保持 M3 语义但使其更舒适
 */
function createSyntaxHighlighting() {  // 打印语法高亮使用的 CSS 变量值（仅在开发模式）
  if (DEBUG) {
    const syntaxVars = [
      '--md-sys-color-primary',
      '--md-sys-color-secondary',
      '--md-sys-color-tertiary',
      '--md-sys-color-error',
      '--md-sys-color-outline',
      '--text-secondary',
    ]
    
    const computedStyles = getComputedStyle(document.documentElement)
    console.group('[TomlEditor] 语法高亮 CSS 变量值')
    syntaxVars.forEach(varName => {
      const value = computedStyles.getPropertyValue(varName).trim()
      console.log(`${varName}: ${value}`)
    })
    console.groupEnd()
  }

  // 使用 HighlightStyle 替代 EditorView.theme
  // 这样可以正确映射 Legacy Mode 的 token
  const myHighlightStyle = HighlightStyle.define([
    // 注释
    { tag: t.comment, color: 'var(--text-secondary)', fontStyle: 'italic', opacity: '0.8' },
    // 字符串值
    { tag: t.string, color: 'var(--md-sys-color-tertiary)' },
    // 数值
    { tag: t.number, color: 'var(--md-sys-color-primary)', fontWeight: '500' },
    // 布尔值
    { tag: t.bool, color: 'var(--md-sys-color-primary)', fontWeight: '500' },
    // 键名/属性名
    { tag: [t.propertyName, t.variableName, t.name], color: 'var(--md-sys-color-secondary)', fontWeight: '500' },
    // null
    { tag: t.null, color: 'var(--md-sys-color-outline)', fontStyle: 'italic' },
    // TOML 区块头 [table]
    { tag: t.heading, color: 'var(--md-sys-color-primary)', fontWeight: 'bold' },
    // 括号
    { tag: t.bracket, color: 'var(--md-sys-color-outline)', fontWeight: 'bold' },
    // 运算符（如 = ）
    { tag: t.operator, color: 'var(--md-sys-color-outline)' },
  ])

  return syntaxHighlighting(myHighlightStyle)
}

// 创建编辑器
onMounted(() => {
  if (!editorRef.value) return

  // 配置扩展
  const extensions = [
    basicSetup,
    StreamLanguage.define(toml),
    // 调试：点击时打印 token 类名
    DEBUG ? EditorView.domEventHandlers({
      click: (event, view) => {
        const pos = view.posAtCoords({ x: event.clientX, y: event.clientY })
        if (pos !== null) {
          const line = view.state.doc.lineAt(pos)
          const lineText = line.text
          const element = event.target as HTMLElement
          
          // 获取所有可能的类名
          let current: HTMLElement | null = element
          const allClasses: string[] = []
          while (current && !current.classList.contains('cm-editor')) {
            if (current.className) {
              allClasses.push(current.className)
            }
            current = current.parentElement
          }
          
          console.group('[TomlEditor] Token 详细信息')
          console.log('位置:', pos)
          console.log('行内容:', lineText)
          console.log('点击文本:', element.textContent)
          console.log('元素链类名:', allClasses)
          console.log('计算颜色:', window.getComputedStyle(element).color)
          console.groupEnd()
        }
        return false
      }
    }) : [],
    EditorView.updateListener.of((update) => {
      if (update.docChanged) {
        const newValue = update.state.doc.toString()
        emit('update:modelValue', newValue)
      }
    }),
    themeCompartment.of([createM3Theme(), createSyntaxHighlighting()]),
    readonlyCompartment.of(EditorState.readOnly.of(props.readonly)),
    // 实时语法检查（500ms 防抖）
    linter(
      (view) => {
        return lintTOML(view.state.doc)
      },
      { delay: 500 }
    ),
    // 行尾诊断信息显示（Error Lens 效果）
    inlineDiagnostics(),
  ]

  // 创建编辑器状态
  const state = EditorState.create({
    doc: props.modelValue,
    extensions,
  })

  // 创建编辑器视图
  editorView.value = new EditorView({
    state,
    parent: editorRef.value,
  })
})

// 销毁编辑器
onUnmounted(() => {
  if (editorView.value) {
    editorView.value.destroy()
    editorView.value = null
  }
})

// 监听主题变化
watch(
  () => themeStore.isDark,
  () => {
    if (editorView.value) {
      editorView.value.dispatch({
        effects: themeCompartment.reconfigure([createM3Theme(), createSyntaxHighlighting()]),
      })
    }
  }
)

// 监听只读状态变化
watch(
  () => props.readonly,
  (newReadonly) => {
    if (editorView.value) {
      editorView.value.dispatch({
        effects: readonlyCompartment.reconfigure(EditorState.readOnly.of(newReadonly)),
      })
    }
  }
)

// 监听外部值变化
watch(
  () => props.modelValue,
  (newValue) => {
    if (editorView.value && newValue !== editorView.value.state.doc.toString()) {
      editorView.value.dispatch({
        changes: {
          from: 0,
          to: editorView.value.state.doc.length,
          insert: newValue,
        },
      })
    }
  }
)
</script>

<style scoped>
.toml-editor-wrapper {
  display: flex;
  flex-direction: column;
  height: 100%;
  overflow: hidden;
}

.editor-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 16px;
  background: var(--md-sys-color-surface-container-high);
  border-bottom: 1px solid var(--md-sys-color-outline-variant);
  color: var(--md-sys-color-on-surface-variant);
  font-size: 13px;
  flex-shrink: 0;
}

.toolbar-left {
  display: flex;
  align-items: center;
  gap: 8px;
}

.file-path {
  font-family: 'Roboto Mono', 'Noto Sans SC', monospace;
}

.editor-container {
  flex: 1;
  overflow: auto;
  background: var(--md-sys-color-surface);
}

/* CodeMirror 样式覆盖 */
.editor-container :deep(.cm-editor) {
  height: 100%;
  font-family: 'Roboto Mono', 'Noto Sans SC', 'Microsoft YaHei', monospace;
  font-size: 15px;
  line-height: 1.6;
}

.editor-container :deep(.cm-scroller) {
  overflow: auto;
  font-family: inherit;
}

.editor-container :deep(.cm-content) {
  font-family: inherit;
  padding: 8px 0;
}

.editor-container :deep(.cm-line) {
  padding: 0 8px;
}

/* Lint 错误样式 */
.editor-container :deep(.cm-lintRange-error) {
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='6' height='3'%3E%3Cpath d='M0 3 L3 0 L6 3 Z' fill='%23f44336'/%3E%3C/svg%3E");
  background-repeat: repeat-x;
  background-position: left bottom;
}

.editor-container :deep(.cm-lintRange-warning) {
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='6' height='3'%3E%3Cpath d='M0 3 L3 0 L6 3 Z' fill='%23ff9800'/%3E%3C/svg%3E");
  background-repeat: repeat-x;
  background-position: left bottom;
}

.editor-container :deep(.cm-tooltip-lint) {
  background: var(--md-sys-color-surface-container-high);
  color: var(--md-sys-color-on-surface);
  border: 1px solid var(--md-sys-color-outline);
  border-radius: 8px;
  padding: 8px 12px;
  font-size: 13px;
  box-shadow: var(--md-sys-elevation-2);
}

.editor-container :deep(.cm-diagnostic-error) {
  border-left: 3px solid var(--md-sys-color-error);
  padding-left: 8px;
}

.editor-container :deep(.cm-diagnostic-warning) {
  border-left: 3px solid #ff9800;
  padding-left: 8px;
}
</style>
