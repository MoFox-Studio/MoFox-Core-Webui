/**
 * TOML 错误收集脚本
 * 用于收集 toml@3.0.0 解析器的所有错误信息
 * 
 * 使用方法：
 * 1. npm install (确保 toml 已安装)
 * 2. node scripts/collect-toml-errors.js
 * 3. 查看生成的 JSON 文件
 */

const TOML = require('toml');
const fs = require('fs');
const path = require('path');

/**
 * 测试用例集合 - 覆盖所有可能的 TOML 错误
 */
const testCases = [
  // ========== 字符串相关错误 ==========
  { name: '未闭合的双引号', content: 'key = "value' },
  { name: '未闭合的单引号', content: "key = 'value" },
  { name: '未闭合的三引号字符串', content: 'key = """value' },
  { name: '未闭合的多行字符串', content: 'key = """value\nline2' },
  { name: '未闭合的单引号多行字符串', content: "key = '''value\nline2" },
  { name: '无效的转义序列 - \\x', content: 'key = "\\x41"' },
  { name: '无效的转义序列 - \\v', content: 'key = "\\v"' },
  { name: '未知的转义字符', content: 'key = "\\q"' },
  { name: '字符串中的无效 Unicode', content: 'key = "\\uDEAD"' },
  { name: '字符串中的无效 Unicode (保留范围)', content: 'key = "\\uD800"' },
  
  // ========== 键重复错误 ==========
  { name: '顶层重复键', content: 'key = "value1"\nkey = "value2"' },
  { name: '表中重复键', content: '[table]\nkey = 1\nkey = 2' },
  { name: '重复定义表', content: '[table]\nkey = 1\n[table]\nkey = 2' },
  { name: '深层嵌套表重复', content: '[a.b.c]\nkey = 1\n[a.b.c]\nkey = 2' },
  { name: '表与表数组冲突', content: '[array]\nkey = 1\n[[array]]\nkey = 2' },
  { name: '表数组与普通表冲突', content: '[[array]]\nkey = 1\n[array]\nkey = 2' },
  
  // ========== 数字错误 ==========
  { name: '无效的数字格式 - 多个小数点', content: 'key = 12.34.56' },
  { name: '无效的数字格式 - 前导零', content: 'key = 012' },
  { name: '无效的十六进制', content: 'key = 0xGHI' },
  { name: '无效的八进制', content: 'key = 0o99' },
  { name: '无效的二进制', content: 'key = 0b123' },
  { name: '数字中多个下划线', content: 'key = 1__000' },
  { name: '数字开头的下划线', content: 'key = _1000' },
  { name: '数字结尾的下划线', content: 'key = 1000_' },
  { name: '无效的指数', content: 'key = 1e' },
  { name: '无效的正负号位置', content: 'key = 1e+' },
  
  // ========== 日期时间错误 ==========
  { name: '无效的日期 - 月份', content: 'key = 2023-13-01' },
  { name: '无效的日期 - 日期', content: 'key = 2023-01-32' },
  { name: '无效的时间 - 小时', content: 'key = 25:00:00' },
  { name: '无效的时间 - 分钟', content: 'key = 12:60:00' },
  { name: '无效的时间 - 秒', content: 'key = 12:00:60' },
  { name: '无效的日期时间格式', content: 'key = 2023/01/01' },
  { name: '无效的时区偏移', content: 'key = 2023-01-01T12:00:00+99:00' },
  { name: '日期时间缺少 T', content: 'key = 2023-01-01 12:00:00' },
  { name: '年份解析错误', content: 'key = 20XX-01-01' },
  
  // ========== 数组错误 ==========
  { name: '数组类型混合 - 数字和字符串', content: 'key = [1, "string"]' },
  { name: '数组类型混合 - 数字和布尔', content: 'key = [1, true]' },
  { name: '数组类型混合 - 多种类型', content: 'key = [1, "string", true]' },
  { name: '数组未闭合', content: 'key = [1, 2, 3' },
  { name: '数组多余的逗号', content: 'key = [1, 2, 3,]' },
  { name: '数组中意外字符', content: 'key = [1, 2 @ 3]' },
  { name: '数组缺少逗号', content: 'key = [1 2 3]' },
  { name: '嵌套数组类型混合', content: 'key = [[1, 2], ["a", "b"]]' },
  
  // ========== 内联表错误 ==========
  { name: '内联表未闭合', content: 'key = { a = 1, b = 2' },
  { name: '内联表中换行', content: 'key = { a = 1,\nb = 2 }' },
  { name: '内联表缺少逗号', content: 'key = { a = 1 b = 2 }' },
  { name: '内联表多余逗号', content: 'key = { a = 1, b = 2, }' },
  { name: '内联表重复键', content: 'key = { a = 1, a = 2 }' },
  
  // ========== 键值对错误 ==========
  { name: '缺少等号', content: 'key "value"' },
  { name: '缺少值', content: 'key =' },
  { name: '缺少值（仅空白）', content: 'key =   ' },
  { name: '多个等号', content: 'key = = "value"' },
  { name: '键后有意外字符', content: 'key @ = "value"' },
  { name: '等号后意外字符', content: 'key = @ "value"' },
  { name: '值后有多余内容', content: 'key = "value" extra' },
  { name: '值后意外字符', content: 'key = "value" @' },
  
  // ========== 表/节错误 ==========
  { name: '未闭合的表名', content: '[table' },
  { name: '多余的闭括号', content: 'table]' },
  { name: '空表名', content: '[]' },
  { name: '表名中有空格（未引用）', content: '[my table]' },
  { name: '表名后有多余内容', content: '[table] extra' },
  { name: '表名中无效字符', content: '[table@name]' },
  { name: '嵌套表名格式错误', content: '[a..b]' },
  { name: '点开头的表名', content: '[.table]' },
  { name: '点结尾的表名', content: '[table.]' },
  
  // ========== 表数组错误 ==========
  { name: '表数组未闭合 - 缺少一个]', content: '[[array]' },
  { name: '表数组多余闭括号', content: '[[array]]]' },
  { name: '空表数组名', content: '[[]]' },
  { name: '表数组名后有内容', content: '[[array]] extra' },
  
  // ========== 意外字符 ==========
  { name: '行首意外字符 @', content: '@ invalid' },
  { name: '行首意外字符 $', content: '$ invalid' },
  { name: '行首意外字符 %', content: '% invalid' },
  { name: '孤立的右括号', content: ']' },
  { name: '孤立的右花括号', content: '}' },
  { name: '孤立的逗号', content: ',' },
  
  // ========== 布尔值错误 ==========
  { name: '大写 True', content: 'key = True' },
  { name: '大写 False', content: 'key = False' },
  { name: '全大写 TRUE', content: 'key = TRUE' },
  { name: '全大写 FALSE', content: 'key = FALSE' },
  { name: '拼写错误的布尔值', content: 'key = ture' },
  
  // ========== 空键相关 ==========
  { name: '空键（空字符串）', content: '"" = "value"' },
  { name: '仅空白的键', content: '"  " = "value"' },
  { name: '键名缺失', content: '= "value"' },
  
  // ========== 注释相关（应该通过） ==========
  { name: '正常注释', content: '# This is a comment\nkey = "value"' },
  { name: '行内注释', content: 'key = "value" # inline comment' },
  
  // ========== 其他边界情况 ==========
  { name: '仅空白行', content: '   \n\n   ' },
  { name: '文件以值开头', content: '"value"' },
  { name: '裸值（无键）', content: 'true' },
  { name: '多行中间的错误', content: 'key1 = "value1"\nkey2 = @\nkey3 = "value3"' },
  { name: '表后紧跟值', content: '[table]\n"value"' },
];

/**
 * 执行测试并收集错误信息
 */
function collectErrors() {
  console.log('\n' + '='.repeat(60));
  console.log('  TOML 错误收集工具 - toml@3.0.0');
  console.log('='.repeat(60) + '\n');

  const errors = [];
  const uniqueErrorMessages = new Set();
  let passedTests = 0;

  testCases.forEach((testCase, index) => {
    try {
      TOML.parse(testCase.content);
      passedTests++;
      console.log(`✓ [${index + 1}/${testCases.length}] ${testCase.name} - 通过（未触发错误）`);
    } catch (error) {
      const errorMessage = error.message || error.toString();
      const mainError = errorMessage.split('\n')[0]; // 只取第一行
      
      console.log(`✗ [${index + 1}/${testCases.length}] ${testCase.name}`);
      console.log(`  └─ ${mainError}`);

      errors.push({
        testName: testCase.name,
        content: testCase.content,
        errorMessage: errorMessage,
        mainError: mainError,
        line: error.line,
        column: error.column,
      });

      uniqueErrorMessages.add(mainError);
    }
  });

  console.log('\n' + '='.repeat(60));
  console.log(`测试统计:`);
  console.log(`  总用例: ${testCases.length}`);
  console.log(`  触发错误: ${errors.length}`);
  console.log(`  通过测试: ${passedTests}`);
  console.log(`  唯一错误: ${uniqueErrorMessages.size}`);
  console.log('='.repeat(60) + '\n');

  return {
    errors,
    uniqueErrorMessages: Array.from(uniqueErrorMessages).sort(),
  };
}

/**
 * 提取错误模式（去除具体的位置信息）
 */
function extractErrorPattern(errorMessage) {
  return errorMessage
    .replace(/at row \d+, col \d+, pos \d+:/g, 'at row X, col Y, pos Z:')
    .replace(/at pos \d+/g, 'at pos X')
    .replace(/at row \d+/g, 'at row X')
    .replace(/at line \d+/g, 'at line X')
    .replace(/col \d+/g, 'col Y')
    .replace(/column \d+/g, 'column Y')
    .trim();
}

/**
 * 分析错误模式，生成翻译模板
 */
function analyzeAndGenerateTranslations(uniqueErrorMessages) {
  console.log('\n' + '='.repeat(60));
  console.log('  错误模式分析');
  console.log('='.repeat(60) + '\n');

  const patterns = new Map();

  uniqueErrorMessages.forEach((error) => {
    const pattern = extractErrorPattern(error);
    if (!patterns.has(pattern)) {
      patterns.set(pattern, []);
    }
    patterns.get(pattern).push(error);
  });

  console.log(`发现 ${patterns.size} 种错误模式：\n`);

  const translationTemplate = {};
  let index = 1;

  patterns.forEach((examples, pattern) => {
    console.log(`${index}. ${pattern}`);
    console.log(`   出现次数: ${examples.length}`);
    if (examples.length > 1) {
      console.log(`   示例: ${examples[0]}`);
    }
    console.log('');

    // 生成待翻译的条目
    translationTemplate[pattern] = `[待翻译 ${index}] ${pattern}`;
    index++;
  });

  return { patterns, translationTemplate };
}

/**
 * 保存结果到文件
 */
function saveResults(errors, uniqueErrorMessages, patterns, translationTemplate) {
  const outputDir = path.join(__dirname, '../docs/toml-errors');

  // 确保输出目录存在
  if (!fs.existsSync(outputDir)) {
    fs.mkdirSync(outputDir, { recursive: true });
  }

  // 1. 详细错误信息
  const errorsFile = path.join(outputDir, 'collected-errors.json');
  fs.writeFileSync(
    errorsFile,
    JSON.stringify(
      {
        generatedAt: new Date().toISOString(),
        library: 'toml@3.0.0',
        totalTests: testCases.length,
        totalErrors: errors.length,
        uniqueErrors: uniqueErrorMessages.length,
        errors: errors,
      },
      null,
      2
    ),
    'utf-8'
  );
  console.log(`✓ 详细错误信息: ${errorsFile}`);

  // 2. 唯一错误列表
  const uniqueFile = path.join(outputDir, 'unique-errors.json');
  fs.writeFileSync(uniqueFile, JSON.stringify(uniqueErrorMessages, null, 2), 'utf-8');
  console.log(`✓ 唯一错误列表: ${uniqueFile}`);

  // 3. 错误模式
  const patternsObj = {};
  patterns.forEach((examples, pattern) => {
    patternsObj[pattern] = examples;
  });
  const patternsFile = path.join(outputDir, 'error-patterns.json');
  fs.writeFileSync(patternsFile, JSON.stringify(patternsObj, null, 2), 'utf-8');
  console.log(`✓ 错误模式: ${patternsFile}`);

  // 4. 翻译模板
  const templateFile = path.join(outputDir, 'translation-template.json');
  fs.writeFileSync(templateFile, JSON.stringify(translationTemplate, null, 2), 'utf-8');
  console.log(`✓ 翻译模板: ${templateFile}`);

  console.log('');
}

/**
 * 主函数
 */
function main() {
  console.log('🚀 开始收集 TOML 错误信息...\n');

  const { errors, uniqueErrorMessages } = collectErrors();
  const { patterns, translationTemplate } = analyzeAndGenerateTranslations(uniqueErrorMessages);
  saveResults(errors, uniqueErrorMessages, patterns, translationTemplate);

  console.log('='.repeat(60));
  console.log('✅ 错误收集完成！');
  console.log('='.repeat(60));
  console.log('\n📝 下一步操作：');
  console.log('1. 查看 docs/toml-errors/unique-errors.json');
  console.log('2. 编辑 docs/toml-errors/translation-template.json 提供中文翻译');
  console.log('3. 运行 node scripts/generate-translations.js 生成最终翻译');
  console.log('4. 运行 node scripts/update-linter.js 更新 toml-linter.ts\n');
}

// 运行脚本
if (require.main === module) {
  main();
}

module.exports = {
  collectErrors,
  analyzeAndGenerateTranslations,
  extractErrorPattern,
};
