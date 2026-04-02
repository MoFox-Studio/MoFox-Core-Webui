/**
 * 测试行尾诊断信息显示功能
 * 用于调试 TomlEditor.vue 中的 Error Lens 效果
 */

const { EditorState, StateField } = require('@codemirror/state');
const { EditorView, Decoration } = require('@codemirror/view');
const { linter, forEachDiagnostic } = require('@codemirror/lint');

// 简单的 TOML linter（模拟）
function simpleTOMLLinter(view) {
  const diagnostics = [];
  const doc = view.state.doc.toString();
  const lines = doc.split('\n');

  lines.forEach((line, index) => {
    const lineStart = view.state.doc.line(index + 1).from;
    const lineEnd = view.state.doc.line(index + 1).to;

    // 检查未闭合的引号
    const trimmed = line.trim();
    if (trimmed && !trimmed.startsWith('#')) {
      const doubleQuotes = (trimmed.match(/"/g) || []).length;
      if (doubleQuotes % 2 !== 0) {
        diagnostics.push({
          from: lineEnd,
          to: lineEnd,
          severity: 'error',
          message: '未闭合的双引号字符串（缺少 "）',
        });
      }
    }
  });

  return diagnostics;
}

// 测试装饰器构建
function testDiagnosticDecorations() {
  console.log('=== 测试诊断装饰器构建 ===\n');

  const testDoc = `[section]
key = "value
another_key = "complete"`;

  const state = EditorState.create({
    doc: testDoc,
    extensions: [
      linter(simpleTOMLLinter),
    ],
  });

  console.log('文档内容:');
  console.log(testDoc);
  console.log('\n检测到的诊断信息:');

  let count = 0;
  forEachDiagnostic(state, (diagnostic, from, to) => {
    count++;
    const line = state.doc.lineAt(from).number;
    console.log(`  [${count}] 行 ${line}: ${diagnostic.message} (严重级别: ${diagnostic.severity})`);
  });

  if (count === 0) {
    console.log('  ⚠️ 没有检测到任何诊断信息！');
    console.log('  可能原因: linter 需要在 EditorView 中运行，而不是单独的 State');
  } else {
    console.log(`\n✅ 成功检测到 ${count} 个诊断信息`);
  }
}

// 测试完整的编辑器
function testFullEditor() {
  console.log('\n\n=== 测试完整编辑器（需要 DOM 环境）===\n');

  // 检查是否在浏览器环境
  if (typeof document === 'undefined') {
    console.log('⚠️ 此测试需要在浏览器环境中运行');
    console.log('建议: 将此逻辑添加到 Vue 组件的开发模式中进行调试');
    return;
  }

  const container = document.createElement('div');
  const view = new EditorView({
    state: EditorState.create({
      doc: '[section]\nkey = "value\n',
      extensions: [linter(simpleTOMLLinter)],
    }),
    parent: container,
  });

  setTimeout(() => {
    console.log('延迟检查诊断信息:');
    forEachDiagnostic(view.state, (diagnostic, from, to) => {
      console.log(`  - ${diagnostic.message}`);
    });
    view.destroy();
  }, 100);
}

// 运行测试
console.log('CodeMirror 诊断系统测试\n');
console.log('='.repeat(50));
testDiagnosticDecorations();
testFullEditor();

console.log('\n' + '='.repeat(50));
console.log('\n📌 调试建议:');
console.log('1. 确保 linter 扩展在 EditorView 创建后正确运行');
console.log('2. 检查 StateField 是否正确订阅了 linter 状态变化');
console.log('3. 在 buildDiagnosticDecorations 中添加 console.log 查看是否被调用');
console.log('4. 验证 forEachDiagnostic 是否真的遍历到了诊断信息');
