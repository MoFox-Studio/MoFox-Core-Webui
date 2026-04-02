/**
 * 测试错误是否显示在行尾（内联提示）
 */

const TOML = require('toml')
const { Text } = require('@codemirror/state')

// 模拟 lintTOML 函数的关键部分
function testInlineErrors() {
  console.log('\n' + '='.repeat(60))
  console.log('  测试错误显示在行尾（内联提示）')
  console.log('='.repeat(60) + '\n')

  const testCases = [
    {
      name: '重复键错误',
      content: 'key = "value1"\nkey = "value2"',
      expectedLine: 2,
    },
    {
      name: '未闭合引号',
      content: 'key = "value',
      expectedLine: 1,
    },
    {
      name: '数组类型混合',
      content: 'arr = [1, "string"]',
      expectedLine: 1,
    },
    {
      name: '未闭合方括号（基础检查）',
      content: '[table',
      expectedLine: 1,
    },
  ]

  testCases.forEach((testCase, index) => {
    console.log(`\n测试 ${index + 1}: ${testCase.name}`)
    console.log(`内容: ${testCase.content.replace(/\n/g, '\\n')}`)

    try {
      TOML.parse(testCase.content)
      console.log('  ✗ 未触发错误（预期应该有错误）')
    } catch (error) {
      const line = error.line
      const column = error.column
      const message = error.message.split('\n')[0]

      console.log(`  错误行: ${line}`)
      console.log(`  错误列: ${column}`)
      console.log(`  错误信息: ${message}`)

      // 模拟 CodeMirror 的行尾定位
      const lines = testCase.content.split('\n')
      if (line && line > 0 && line <= lines.length) {
        const targetLine = lines[line - 1]
        const lineStartPos = lines.slice(0, line - 1).join('\n').length + (line > 1 ? 1 : 0)
        const lineEndPos = lineStartPos + targetLine.length

        console.log(`  行内容: "${targetLine}"`)
        console.log(`  行起始位置: ${lineStartPos}`)
        console.log(`  行结束位置: ${lineEndPos}`)
        console.log(`  ✓ 错误将显示在位置 ${lineEndPos}（行尾）`)

        if (line === testCase.expectedLine) {
          console.log(`  ✓ 行号匹配预期`)
        } else {
          console.log(`  ✗ 行号不匹配（预期: ${testCase.expectedLine}, 实际: ${line}）`)
        }
      } else {
        console.log(`  ✗ 无效的行号: ${line}`)
      }
    }
  })

  console.log('\n' + '='.repeat(60))
  console.log('💡 说明：')
  console.log('  - from = lineEnd, to = lineEnd 会让 CodeMirror 在行尾显示内联提示')
  console.log('  - 这比高亮整行或部分文本更加简洁明了')
  console.log('  - 用户可以在行尾看到错误图标和消息')
  console.log('='.repeat(60) + '\n')
}

// 运行测试
testInlineErrors()
