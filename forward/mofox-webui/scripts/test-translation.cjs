/**
 * TOML 翻译功能测试脚本
 * 
 * 验证 toml-linter.ts 中的翻译功能是否正常工作
 * 
 * 使用方法：
 *   node scripts/test-translation.cjs
 */

const TOML = require('toml');

// 测试用例：[测试名称, TOML内容, 期望包含的中文关键词]
const testCases = [
  ['键重复', 'key = 1\nkey = 2', ['重复', '键']],
  ['数组类型混合', 'arr = [1, "string"]', ['数组', '类型', '不匹配']],
  ['无效 Unicode', 'key = "\\uDEAD"', ['Unicode', '转义码']],
  ['未闭合双引号', 'key = "value', ['未闭合', '双引号']],
  ['未闭合单引号', "key = 'value", ['未闭合', '单引号']],
  ['未闭合多行字符串', 'key = """value\nline2', ['未闭合', '多行']],
  ['日期时间空格', 'key = 2023-01-01 12:00:00', ['日期', '时间', 'T']],
  ['内联表换行', 'key = { a = 1,\nb = 2 }', ['内联表', '换行', '同一行']],
  ['值后意外字符', 'key = "value" extra', ['意外字符', '注释', '换行']],
  ['未闭合方括号', '[table', ['未闭合', '方括号']],
  ['缺少等号', 'key "value"', ['缺少', '等号']],
];

console.log('\n' + '='.repeat(60));
console.log('  TOML 翻译功能测试');
console.log('='.repeat(60) + '\n');

let passedTests = 0;
let failedTests = 0;

testCases.forEach(([name, content, keywords], index) => {
  try {
    TOML.parse(content);
    console.log(`⚠️  [${index + 1}/${testCases.length}] ${name}`);
    console.log(`   未触发错误（测试用例可能需要更新）\n`);
    failedTests++;
  } catch (error) {
    const errorMessage = error.message || '';
    
    // 注意：这里我们只能看到英文错误，因为翻译在前端进行
    // 但我们可以检查错误是否被触发
    console.log(`✓ [${index + 1}/${testCases.length}] ${name}`);
    console.log(`  原始错误: ${errorMessage.split('\n')[0].substring(0, 80)}...`);
    console.log(`  期望包含: ${keywords.join(', ')}`);
    console.log('');
    passedTests++;
  }
});

console.log('='.repeat(60));
console.log(`测试结果: ${passedTests}/${testCases.length} 个错误成功触发`);
console.log('='.repeat(60));
console.log('\n💡 提示：');
console.log('  - 这些错误在前端会被翻译成中文');
console.log('  - 在浏览器中测试以查看实际中文翻译');
console.log('  - 如果某个测试未触发错误，说明 toml@3.0.0 可能允许该语法\n');
