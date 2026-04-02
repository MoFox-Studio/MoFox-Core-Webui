/**
 * 测试 toml@3.0.0 错误对象结构
 */

const TOML = require('toml');

const testCases = [
  { name: '重复键', content: 'key = 1\nkey = 2' },
  { name: '未闭合字符串', content: 'key = "value' },
  { name: '数组类型混合', content: 'arr = [1, "str"]' },
];

console.log('测试 TOML 错误对象结构:\n');

testCases.forEach((test) => {
  try {
    TOML.parse(test.content);
  } catch (error) {
    console.log(`=== ${test.name} ===`);
    console.log('错误对象属性:');
    console.log('  message:', error.message);
    console.log('  line:', error.line);
    console.log('  column:', error.column);
    console.log('  offset:', error.offset);
    console.log('  name:', error.name);
    console.log('  所有键:', Object.keys(error));
    console.log('');
  }
});
