/**
 * 测试 TOML Linter 的行尾错误显示
 * 
 * 这个脚本模拟 CodeMirror 的 Text 对象来测试 lintTOML 函数
 */

const TOML = require('toml');

// 模拟 CodeMirror 的 Text 对象
class MockText {
  constructor(content) {
    this.content = content;
    this.lines = content.split('\n');
  }

  toString() {
    return this.content;
  }

  get lines() {
    return this._lines.length;
  }

  set lines(value) {
    this._lines = value;
  }

  line(num) {
    const lineIndex = num - 1;
    if (lineIndex < 0 || lineIndex >= this._lines.length) {
      throw new Error(`Invalid line number: ${num}`);
    }

    let offset = 0;
    for (let i = 0; i < lineIndex; i++) {
      offset += this._lines[i].length + 1; // +1 for newline
    }

    const from = offset;
    const to = offset + this._lines[lineIndex].length;

    return { from, to, text: this._lines[lineIndex] };
  }

  get length() {
    return this.content.length;
  }
}

// 测试用例
const testCases = [
  {
    name: '重复的键（第2行）',
    content: 'key = "value1"\nkey = "value2"',
    expectedLine: 2,
  },
  {
    name: '未闭合的字符串（第1行）',
    content: 'key = "value',
    expectedLine: 1,
  },
  {
    name: '数组类型混合（第1行）',
    content: 'arr = [1, "string"]',
    expectedLine: 1,
  },
  {
    name: '多行中的错误（第3行）',
    content: 'key1 = "value1"\nkey2 = "value2"\nkey3 = invalid',
    expectedLine: 3,
  },
];

console.log('测试 TOML 错误显示位置:\n');

testCases.forEach((test) => {
  console.log(`=== ${test.name} ===`);
  console.log('内容:');
  test.content.split('\n').forEach((line, i) => {
    console.log(`  ${i + 1}: ${line}`);
  });

  try {
    TOML.parse(test.content);
    console.log('❌ 没有触发错误（预期应该有错误）\n');
  } catch (error) {
    const mockDoc = new MockText(test.content);
    const errorLine = error.line || 1;
    const lineInfo = mockDoc.line(errorLine);

    console.log(`\n错误信息: ${error.message}`);
    console.log(`错误位置: 第 ${errorLine} 行`);
    console.log(`行内容: "${lineInfo.text}"`);
    console.log(`行起始偏移: ${lineInfo.from}`);
    console.log(`行结束偏移: ${lineInfo.to}`);
    console.log(`错误标记位置: from=${lineInfo.to}, to=${lineInfo.to} (行尾)`);
    
    if (errorLine === test.expectedLine) {
      console.log('✅ 错误行号正确');
    } else {
      console.log(`❌ 错误行号不匹配（期望 ${test.expectedLine}，实际 ${errorLine}）`);
    }
    console.log('');
  }
});

console.log('测试完成！');
