/**
 * TOML 错误翻译一键更新脚本
 * 
 * 自动执行以下步骤：
 * 1. 收集所有 TOML 错误信息
 * 2. 生成中英文翻译映射
 * 3. 更新 toml-linter.ts 文件
 * 
 * 使用方法：
 *   node scripts/update-all-translations.js
 */

const { execSync } = require('child_process');
const path = require('path');
const fs = require('fs');

// ANSI 颜色代码
const colors = {
  reset: '\x1b[0m',
  bright: '\x1b[1m',
  green: '\x1b[32m',
  yellow: '\x1b[33m',
  blue: '\x1b[34m',
  red: '\x1b[31m',
};

/**
 * 打印带颜色的消息
 */
function log(message, color = colors.reset) {
  console.log(color + message + colors.reset);
}

/**
 * 打印步骤标题
 */
function printStep(step, total, title) {
  console.log('\n' + '='.repeat(60));
  log(`步骤 ${step}/${total}: ${title}`, colors.bright + colors.blue);
  console.log('='.repeat(60) + '\n');
}

/**
 * 执行脚本并捕获输出
 */
function runScript(scriptPath, scriptName) {
  try {
    log(`⚡ 执行 ${scriptName}...`, colors.yellow);
    
    const result = execSync(`node "${scriptPath}"`, {
      cwd: path.join(__dirname, '..'),
      encoding: 'utf-8',
      stdio: 'inherit', // 实时显示输出
    });

    log(`✓ ${scriptName} 完成`, colors.green);
    return true;
  } catch (error) {
    log(`✗ ${scriptName} 失败`, colors.red);
    console.error(error.message);
    return false;
  }
}

/**
 * 主函数
 */
function main() {
  const startTime = Date.now();

  log('\n' + '█'.repeat(60), colors.bright + colors.blue);
  log('  TOML 错误翻译一键更新工具', colors.bright);
  log('█'.repeat(60), colors.bright + colors.blue);

  // 步骤 1: 收集错误
  printStep(1, 3, '收集 TOML 错误信息');
  const step1Success = runScript(
    path.join(__dirname, 'collect-toml-errors.cjs'),
    'collect-toml-errors.cjs'
  );

  if (!step1Success) {
    log('\n❌ 错误收集失败，终止流程', colors.red);
    process.exit(1);
  }

  // 步骤 2: 生成翻译
  printStep(2, 3, '生成中英文翻译映射');
  const step2Success = runScript(
    path.join(__dirname, 'generate-translations.cjs'),
    'generate-translations.cjs'
  );

  if (!step2Success) {
    log('\n❌ 翻译生成失败，终止流程', colors.red);
    process.exit(1);
  }

  // 步骤 3: 更新 linter
  printStep(3, 3, '更新 toml-linter.ts');
  const step3Success = runScript(
    path.join(__dirname, 'update-linter.cjs'),
    'update-linter.cjs'
  );

  if (!step3Success) {
    log('\n❌ Linter 更新失败，终止流程', colors.red);
    process.exit(1);
  }

  // 完成统计
  const endTime = Date.now();
  const duration = ((endTime - startTime) / 1000).toFixed(2);

  console.log('\n' + '='.repeat(60));
  log('✅ 所有步骤完成！', colors.bright + colors.green);
  console.log('='.repeat(60));

  console.log('\n📊 执行统计:');
  console.log(`  总耗时: ${duration} 秒`);

  // 显示生成的文件
  console.log('\n📁 生成的文件:');
  const outputDir = path.join(__dirname, '../docs/toml-errors');
  if (fs.existsSync(outputDir)) {
    const files = fs.readdirSync(outputDir);
    files.forEach((file) => {
      console.log(`  ✓ docs/toml-errors/${file}`);
    });
  }

  // 显示备份文件
  const backupPath = path.join(__dirname, '../src/utils/toml-linter.ts.backup');
  if (fs.existsSync(backupPath)) {
    console.log(`  ✓ src/utils/toml-linter.ts.backup (备份)`);
  }

  console.log('\n💡 下一步操作:');
  console.log('  1. 查看 docs/toml-errors/ 下的文件');
  console.log('  2. 在浏览器中测试更新后的 TOML linter');
  console.log('  3. 如有问题，可以从 .backup 文件恢复');
  console.log('  4. 确认无误后，提交代码\n');
}

// 运行脚本
if (require.main === module) {
  main();
}
