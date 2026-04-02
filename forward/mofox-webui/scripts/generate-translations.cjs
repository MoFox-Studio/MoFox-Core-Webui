/**
 * TOML 错误翻译生成脚本
 * 
 * 基于收集到的错误信息，生成完整的中英文翻译映射表
 * 
 * 使用方法：
 * 1. 先运行 node scripts/collect-toml-errors.js
 * 2. 然后运行 node scripts/generate-translations.js
 */

const fs = require('fs');
const path = require('path');

/**
 * 完整的 TOML 错误翻译映射表
 * 基于 toml@3.0.0 (PEG 解析器) 的真实错误信息
 * 
 * 格式：[英文错误前缀或关键词, 中文翻译, 优先级]
 * 优先级：数字越小越优先匹配（用于处理包含关系）
 */
const TRANSLATION_MAP = [
  // ========== 键重复错误（高优先级）==========
  ['Cannot redefine existing key', '不能重新定义已存在的键', 10],
  ['Cannot add value of type', '数组类型不匹配', 11],
  
  // ========== Unicode 错误 ==========
  ['Invalid Unicode escape code:', '无效的 Unicode 转义码:', 20],
  
  // ========== 未闭合的字符串 ==========
  ['Expected "\\"\\"\\"", "\\\\", "\\\\U"', '未闭合的多行双引号字符串', 30],
  ["Expected \"'''\"", '未闭合的多行单引号字符串', 31],
  ['Expected "\\"", "\\\\U"', '未闭合的双引号字符串', 32],
  ["Expected \"'\"", '未闭合的单引号字符串', 33],
  
  // ========== 日期时间格式错误 ==========
  ['Expected "T" but " " found', '日期时间格式错误：缺少 T 分隔符', 40],
  ['Expected "T" but end of input found', '日期格式不完整：缺少时间部分', 41],
  
  // ========== 数组错误 ==========
  ['but end of input found', '意外的输入结束', 50],
  
  // ========== 期望特定字符 ==========
  ['Expected "=" or', '缺少等号', 60],
  ['Expected "]" but end of input found', '未闭合的方括号', 61],
  ['Expected "}", [ \\t] or [A-Za-z0-9_\\-] but "\\n" found', '内联表不能换行', 62],
  
  // ========== 通用 PEG 错误翻译辅助 ==========
  ['Expected "#", "\\n", "\\r" or [ \\t] but', '值后有意外字符', 70],
  ['Expected "\'"', '期望单引号', 80],
  ['Expected "\\""', '期望双引号', 81],
  ['Expected "="', '期望等号', 82],
  ['Expected "]"', '期望右方括号', 83],
  ['Expected "}"', '期望右花括号', 84],
  ['Expected ","', '期望逗号', 85],
  ['Expected "T"', '期望日期时间分隔符 T', 86],
  
  // ========== 值类型期望 ==========
  ['Expected "\'"', '期望字符串、数字或布尔值', 90],
  
  // ========== 兜底翻译 ==========
  ['but', '语法错误', 200],
];

/**
 * 生成用于 TypeScript 的翻译数组
 */
function generateTypeScriptTranslations() {
  // 按优先级排序
  const sorted = TRANSLATION_MAP.sort((a, b) => a[2] - b[2]);

  const tsArray = sorted.map(([english, chinese]) => {
    // 转义特殊字符
    const escapedEnglish = english.replace(/'/g, "\\'");
    const escapedChinese = chinese.replace(/'/g, "\\'");
    return `  ['${escapedEnglish}', '${escapedChinese}'],`;
  });

  return `/**
 * TOML 错误信息翻译映射表
 * 基于 toml@3.0.0 库的真实错误信息
 * 每个条目格式：[英文前缀, 中文翻译]
 * 顺序很重要：更具体的错误应该放在前面
 * 
 * 此文件由 scripts/generate-translations.js 自动生成
 * 生成时间: ${new Date().toISOString()}
 */
const TOML_ERROR_PATTERNS: Array<[string, string]> = [
${tsArray.join('\n')}
];`;
}

/**
 * 生成用于 JavaScript 的翻译对象
 */
function generateJavaScriptTranslations() {
  const sorted = TRANSLATION_MAP.sort((a, b) => a[2] - b[2]);

  const entries = {};
  sorted.forEach(([english, chinese]) => {
    entries[english] = chinese;
  });

  return JSON.stringify(entries, null, 2);
}

/**
 * 生成 Markdown 文档
 */
function generateMarkdownDoc() {
  const sorted = TRANSLATION_MAP.sort((a, b) => a[2] - b[2]);

  let md = `# TOML 错误信息翻译对照表

> 基于 toml@3.0.0 库
> 生成时间: ${new Date().toISOString()}

## 翻译列表

| 优先级 | 英文错误信息 | 中文翻译 |
|--------|-------------|---------|
`;

  sorted.forEach(([english, chinese, priority]) => {
    md += `| ${priority} | ${english} | ${chinese} |\n`;
  });

  md += `\n## 总计

- 总翻译条目: ${TRANSLATION_MAP.length}

## 使用说明

1. 错误匹配按优先级从小到大进行
2. 更具体的错误（如"Unterminated multi-line string"）应该比通用错误（如"Unterminated string"）优先级更高
3. 优先级相同时，按数组顺序匹配
`;

  return md;
}

/**
 * 主函数
 */
function main() {
  console.log('\n' + '='.repeat(60));
  console.log('  TOML 错误翻译生成工具');
  console.log('='.repeat(60) + '\n');

  const outputDir = path.join(__dirname, '../docs/toml-errors');

  // 确保输出目录存在
  if (!fs.existsSync(outputDir)) {
    fs.mkdirSync(outputDir, { recursive: true });
  }

  // 1. 生成 TypeScript 版本
  const tsContent = generateTypeScriptTranslations();
  const tsFile = path.join(outputDir, 'translations.ts');
  fs.writeFileSync(tsFile, tsContent, 'utf-8');
  console.log(`✓ TypeScript 翻译: ${tsFile}`);

  // 2. 生成 JavaScript 版本
  const jsContent = generateJavaScriptTranslations();
  const jsFile = path.join(outputDir, 'translations.json');
  fs.writeFileSync(jsFile, jsContent, 'utf-8');
  console.log(`✓ JSON 翻译: ${jsFile}`);

  // 3. 生成 Markdown 文档
  const mdContent = generateMarkdownDoc();
  const mdFile = path.join(outputDir, 'translations.md');
  fs.writeFileSync(mdFile, mdContent, 'utf-8');
  console.log(`✓ Markdown 文档: ${mdFile}`);

  console.log('\n' + '='.repeat(60));
  console.log(`✅ 翻译生成完成！共 ${TRANSLATION_MAP.length} 条翻译`);
  console.log('='.repeat(60));
  console.log('\n📝 下一步：运行 node scripts/update-linter.js 更新 toml-linter.ts\n');
}

// 运行脚本
if (require.main === module) {
  main();
}

module.exports = {
  TRANSLATION_MAP,
  generateTypeScriptTranslations,
  generateJavaScriptTranslations,
  generateMarkdownDoc,
};
