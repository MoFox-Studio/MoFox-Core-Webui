/**
 * 自动更新 toml-linter.ts 的翻译映射表
 * 
 * 使用方法：
 * 1. node scripts/collect-toml-errors.js（收集错误）
 * 2. node scripts/generate-translations.js（生成翻译）
 * 3. node scripts/update-linter.js（更新 linter 文件）
 */

const fs = require('fs');
const path = require('path');

// 导入翻译映射
const { TRANSLATION_MAP, generateTypeScriptTranslations } = require('./generate-translations.cjs');

/**
 * 更新 toml-linter.ts 文件
 */
function updateLinterFile() {
  const linterPath = path.join(__dirname, '../src/utils/toml-linter.ts');

  console.log('\n' + '='.repeat(60));
  console.log('  更新 toml-linter.ts');
  console.log('='.repeat(60) + '\n');

  // 检查文件是否存在
  if (!fs.existsSync(linterPath)) {
    console.error(`❌ 错误: 找不到文件 ${linterPath}`);
    process.exit(1);
  }

  // 读取原文件
  const originalContent = fs.readFileSync(linterPath, 'utf-8');
  console.log(`✓ 读取文件: ${linterPath}`);

  // 生成新的翻译数组内容
  const sorted = TRANSLATION_MAP.sort((a, b) => a[2] - b[2]);
  const translationLines = sorted.map(([english, chinese]) => {
    // 转义特殊字符
    const escapedEnglish = english.replace(/\\/g, '\\\\').replace(/'/g, "\\'");
    const escapedChinese = chinese.replace(/\\/g, '\\\\').replace(/'/g, "\\'");
    return `  ['${escapedEnglish}', '${escapedChinese}'],`;
  });

  const newTranslationBlock = `/**
 * TOML 错误信息翻译映射表
 * 基于 toml@3.0.0 库的真实错误信息
 * 每个条目格式：[英文前缀, 中文翻译]
 * 顺序很重要：更具体的错误应该放在前面
 * 
 * 此翻译表由 scripts/update-linter.js 自动更新
 * 更新时间: ${new Date().toISOString()}
 */
const TOML_ERROR_PATTERNS: Array<[string, string]> = [
${translationLines.join('\n')}
]`;

  // 使用正则表达式替换整个 TOML_ERROR_PATTERNS 常量
  // 匹配从注释开始到数组结束的整个块
  const pattern = /\/\*\*[\s\S]*?TOML 错误信息翻译映射表[\s\S]*?\*\/\s*const TOML_ERROR_PATTERNS:[\s\S]*?\] = \[[\s\S]*?\n\]/;

  if (!pattern.test(originalContent)) {
    console.error('❌ 错误: 无法在文件中找到 TOML_ERROR_PATTERNS 定义');
    console.error('   请确保文件格式正确');
    process.exit(1);
  }

  const updatedContent = originalContent.replace(pattern, newTranslationBlock);

  // 创建备份
  const backupPath = linterPath + '.backup';
  fs.writeFileSync(backupPath, originalContent, 'utf-8');
  console.log(`✓ 创建备份: ${backupPath}`);

  // 写入更新后的内容
  fs.writeFileSync(linterPath, updatedContent, 'utf-8');
  console.log(`✓ 更新文件: ${linterPath}`);
  console.log(`✓ 更新翻译数: ${TRANSLATION_MAP.length} 条`);

  // 统计信息
  const oldLines = originalContent.split('\n').length;
  const newLines = updatedContent.split('\n').length;
  const lineDiff = newLines - oldLines;

  console.log('\n统计信息:');
  console.log(`  原文件行数: ${oldLines}`);
  console.log(`  新文件行数: ${newLines}`);
  console.log(`  行数变化: ${lineDiff > 0 ? '+' : ''}${lineDiff}`);
}

/**
 * 验证更新后的文件
 */
function validateUpdate() {
  const linterPath = path.join(__dirname, '../src/utils/toml-linter.ts');
  const content = fs.readFileSync(linterPath, 'utf-8');

  console.log('\n' + '-'.repeat(60));
  console.log('验证更新:');

  // 检查是否包含预期的翻译数量
  const matches = content.match(/\['.+?', '.+?'\],/g);
  const actualCount = matches ? matches.length : 0;

  if (actualCount === TRANSLATION_MAP.length) {
    console.log(`✓ 翻译条目数正确: ${actualCount}`);
  } else {
    console.error(`❌ 翻译条目数不匹配: 期望 ${TRANSLATION_MAP.length}, 实际 ${actualCount}`);
    process.exit(1);
  }

  // 检查是否包含时间戳
  if (content.includes('更新时间:')) {
    console.log('✓ 包含更新时间戳');
  }

  // 检查是否包含关键翻译
  const keyTranslations = [
    '未闭合的字符串',
    '重复的键',
    '无效的数字',
    '意外的字符',
  ];

  let missingTranslations = [];
  keyTranslations.forEach((trans) => {
    if (!content.includes(trans)) {
      missingTranslations.push(trans);
    }
  });

  if (missingTranslations.length === 0) {
    console.log('✓ 关键翻译存在');
  } else {
    console.error(`❌ 缺少关键翻译: ${missingTranslations.join(', ')}`);
  }

  console.log('-'.repeat(60));
}

/**
 * 主函数
 */
function main() {
  try {
    updateLinterFile();
    validateUpdate();

    console.log('\n' + '='.repeat(60));
    console.log('✅ toml-linter.ts 更新成功！');
    console.log('='.repeat(60));
    console.log('\n💡 提示:');
    console.log('  - 备份文件保存在 src/utils/toml-linter.ts.backup');
    console.log('  - 如需恢复，可以使用备份文件');
    console.log('  - 建议在浏览器中测试更新后的 linter 功能\n');
  } catch (error) {
    console.error('\n❌ 更新失败:', error.message);
    console.error(error.stack);
    process.exit(1);
  }
}

// 运行脚本
if (require.main === module) {
  main();
}

module.exports = {
  updateLinterFile,
  validateUpdate,
};
