# TOML 错误翻译系统

## 📋 概述

TOML Linter 使用智能翻译系统，将 `toml@3.0.0` (PEG 解析器) 的英文错误信息翻译成友好的中文提示。

## 🎯 翻译策略

由于 `toml@3.0.0` 使用 PEG 解析器，其错误格式为 "Expected X but Y found"，我们采用**智能条件匹配**而非简单的映射表：

### 支持的错误类型

1. **键重复错误** - 提取并显示重复的键名
2. **数组类型不匹配** - 翻译类型名称（String→字符串, Integer→整数等）
3. **Unicode 错误** - 保留并显示错误的 Unicode 码
4. **未闭合的字符串** - 区分单/双引号、普通/多行字符串
5. **日期时间格式错误** - 具体说明错误原因
6. **内联表换行** - 提示必须在同一行
7. **值后意外字符** - 提示应该是注释或换行
8. **输入结束错误** - 根据上下文提供具体提示

## 📂 文件说明

### `collect-toml-errors.cjs`

**用途**：收集测试错误信息，用于文档和调试

```bash
node scripts/collect-toml-errors.cjs
```

**输出**：
- `docs/toml-errors/collected-errors.json` - 详细错误信息
- `docs/toml-errors/unique-errors.json` - 唯一错误列表
- `docs/toml-errors/error-patterns.json` - 错误模式分析

**用途**：
- 测试覆盖率验证
- 文档生成
- 调试新增的 TOML 语法检查

### `generate-translations.cjs` (可选)

生成翻译文档（供参考）。

### `update-linter.cjs` (已废弃)

**注意**：由于采用智能翻译，不再需要自动更新翻译映射表。

## 🔧 如何添加新的翻译

直接编辑 `src/utils/toml-linter.ts` 中的 `translateTOMLError` 函数：

```typescript
function translateTOMLError(errorMessage: string): string {
  const msg = errorMessage.trim()

  // 添加你的翻译逻辑
  if (msg.includes('你的错误模式')) {
    return '你的中文翻译'
  }

  // ... 其他翻译 ...
}
```

### 翻译最佳实践

1. **具体优于通用** - 优先匹配具体的错误模式
2. **提取关键信息** - 从错误中提取键名、类型等有用信息
3. **友好的提示** - 提供可操作的修复建议
4. **保持简洁** - 中文提示应简洁明了

示例：

```typescript
// ❌ 不好
if (msg.includes('error')) {
  return '错误'
}

// ✅ 更好
if (msg.includes('Cannot redefine existing key')) {
  const match = msg.match(/Cannot redefine existing key '([^']+)'/)
  if (match) {
    return `不能重新定义已存在的键 '${match[1]}'`
  }
  return '不能重新定义已存在的键'
}
```

## 📚 测试用例

`collect-toml-errors.cjs` 包含 90+ 个测试用例，覆盖：

- ✅ 字符串错误（未闭合、转义序列等）
- ✅ 键重复错误
- ✅ 数字格式错误
- ✅ 日期时间错误
- ✅ 数组类型混合
- ✅ 内联表错误
- ✅ 表/节定义错误
- ✅ Unicode 错误

运行测试查看覆盖情况：

```bash
node scripts/collect-toml-errors.cjs
```

## 🐛 调试

### 查看实际错误信息

如果遇到未翻译的错误：

1. 在浏览器控制台查看原始错误
2. 在 `translateTOMLError` 函数中添加断点或 console.log
3. 添加新的匹配条件

### 测试特定的 TOML 内容

编辑 `collect-toml-errors.cjs` 添加测试用例：

```javascript
const testCases = [
  // ... 现有用例 ...
  
  { name: '我的测试', content: 'key = invalid toml' },
]
```

## 📖 参考资源

- [TOML 规范](https://toml.io/)
- [toml@3.0.0 文档](https://www.npmjs.com/package/toml)
- [PEG 解析器](https://pegjs.org/)

## 🤝 贡献

发现翻译不准确？欢迎提交 PR！

1. 在 `src/utils/toml-linter.ts` 中改进翻译
2. 添加测试用例到 `collect-toml-errors.cjs`
3. 运行测试验证
4. 提交 PR

---

**当前版本**: 基于 toml@3.0.0 (PEG 解析器)  
**最后更新**: 2026-04-02

## 脚本说明

### 1. collect-toml-errors.js

**功能**：收集 TOML 解析器的所有错误信息

**输出文件**：
- `docs/toml-errors/collected-errors.json` - 详细错误信息
- `docs/toml-errors/unique-errors.json` - 唯一错误列表
- `docs/toml-errors/error-patterns.json` - 错误模式分析
- `docs/toml-errors/translation-template.json` - 翻译模板

**测试覆盖**：
- ✓ 字符串相关错误（未闭合、转义序列等）
- ✓ 键重复错误
- ✓ 数字格式错误
- ✓ 日期时间错误
- ✓ 数组类型混合
- ✓ 内联表错误
- ✓ 表/节定义错误
- ✓ 键值对错误
- ✓ Unicode 错误
- ✓ 意外字符

**示例输出**：

```
========================================
开始收集 TOML 解析错误信息
========================================

✗ [1/90] 未闭合的双引号
  └─ Expected a value at row 1, col 9, pos 8:
✓ [2/90] 正常注释 - 通过（未触发错误）

测试统计:
  总用例: 90
  触发错误: 85
  通过测试: 5
  唯一错误: 42
```

### 2. generate-translations.js

**功能**：生成完整的中英文翻译映射表

**输出文件**：
- `docs/toml-errors/translations.ts` - TypeScript 格式翻译
- `docs/toml-errors/translations.json` - JSON 格式翻译
- `docs/toml-errors/translations.md` - Markdown 文档

**翻译特点**：
- 按优先级排序（具体错误 > 通用错误）
- 包含 40+ 种错误模式
- 符合中文语境的翻译
- 保持技术准确性

**翻译示例**：

| 英文 | 中文 |
|------|------|
| Unterminated multi-line string | 未闭合的多行字符串 |
| Can't redefine an existing key | 不能重新定义已存在的键 |
| Invalid Unicode | 无效的 Unicode |
| Array mismatch | 数组类型不匹配 |

### 3. update-linter.js

**功能**：自动更新 `toml-linter.ts` 中的翻译数组

**操作步骤**：
1. 读取 `src/utils/toml-linter.ts`
2. 创建备份文件（`.backup`）
3. 替换 `TOML_ERROR_PATTERNS` 常量
4. 验证更新是否成功

**安全特性**：
- ✓ 自动创建备份
- ✓ 更新前验证文件存在
- ✓ 更新后验证翻译数量
- ✓ 检查关键翻译是否存在

**示例输出**：

```
========================================
  更新 toml-linter.ts
========================================

✓ 读取文件: src/utils/toml-linter.ts
✓ 创建备份: src/utils/toml-linter.ts.backup
✓ 更新文件: src/utils/toml-linter.ts
✓ 更新翻译数: 45 条

统计信息:
  原文件行数: 250
  新文件行数: 265
  行数变化: +15
```

### 4. update-all-translations.js

**功能**：一键执行所有更新步骤

**优点**：
- 自动化整个流程
- 实时显示进度
- 彩色输出（Windows 支持）
- 统计执行时间
- 汇总生成的文件

**示例输出**：

```
████████████████████████████████████████████████████████████
  TOML 错误翻译一键更新工具
████████████████████████████████████████████████████████████

步骤 1/3: 收集 TOML 错误信息
⚡ 执行 collect-toml-errors.js...
[... 收集过程输出 ...]
✓ collect-toml-errors.js 完成

步骤 2/3: 生成中英文翻译映射
⚡ 执行 generate-translations.js...
[... 生成过程输出 ...]
✓ generate-translations.js 完成

步骤 3/3: 更新 toml-linter.ts
⚡ 执行 update-linter.js...
[... 更新过程输出 ...]
✓ update-linter.js 完成

✅ 所有步骤完成！

📊 执行统计:
  总耗时: 2.34 秒
```

## 文件结构

```
mofox-webui/
├── scripts/
│   ├── collect-toml-errors.js     # 错误收集
│   ├── generate-translations.js   # 翻译生成
│   ├── update-linter.js          # Linter 更新
│   ├── update-all-translations.js # 一键更新
│   └── README.md                 # 本文档
├── docs/
│   └── toml-errors/              # 生成的文件
│       ├── collected-errors.json
│       ├── unique-errors.json
│       ├── error-patterns.json
│       ├── translation-template.json
│       ├── translations.ts
│       ├── translations.json
│       └── translations.md
└── src/
    └── utils/
        ├── toml-linter.ts        # 目标文件
        └── toml-linter.ts.backup # 自动备份
```

## 使用场景

### 场景 1: TOML 库升级

当 `toml` 库升级到新版本时：

```bash
# 重新收集错误信息
node scripts/collect-toml-errors.js

# 检查新增的错误类型
cat docs/toml-errors/unique-errors.json

# 如果有新错误，更新 generate-translations.js 中的 TRANSLATION_MAP

# 重新生成和更新
node scripts/generate-translations.js
node scripts/update-linter.js
```

### 场景 2: 改进翻译

如果发现某些翻译不准确：

1. 编辑 `scripts/generate-translations.js`
2. 修改 `TRANSLATION_MAP` 中的相应条目
3. 重新运行：
   ```bash
   node scripts/generate-translations.js
   node scripts/update-linter.js
   ```

### 场景 3: 添加新测试用例

在 `collect-toml-errors.js` 中添加新测试：

```javascript
const testCases = [
  // ... 现有测试用例 ...
  
  // 添加新测试
  { name: '你的测试名称', content: 'invalid = toml content' },
];
```

然后重新运行收集流程。

### 场景 4: 恢复备份

如果更新出错：

```bash
# Windows
copy src\utils\toml-linter.ts.backup src\utils\toml-linter.ts

# Linux/Mac
cp src/utils/toml-linter.ts.backup src/utils/toml-linter.ts
```

## 常见问题

### Q1: 脚本运行失败，提示找不到模块

**A**: 确保在项目根目录下运行，并且已安装依赖：

```bash
npm install
```

### Q2: 翻译没有生效

**A**: 检查以下几点：

1. 确认 `update-linter.js` 成功执行
2. 检查浏览器缓存是否清除
3. 重新构建前端项目：
   ```bash
   npm run build
   ```

### Q3: 如何添加自定义翻译

**A**: 编辑 `scripts/generate-translations.js`：

```javascript
const TRANSLATION_MAP = [
  // ... 现有翻译 ...
  
  // 添加你的翻译（格式：[英文, 中文, 优先级]）
  ['Your error pattern', '你的中文翻译', 150],
];
```

然后运行更新脚本。

### Q4: 翻译优先级如何确定

**A**: 优先级规则：

- 数字越小，优先级越高
- 具体错误（如 "Unterminated multi-line string"）应该比通用错误（如 "Unterminated string"）优先级高
- 建议范围：
  - 0-99: 非常具体的错误
  - 100-199: 常见错误
  - 200+: 通用错误

### Q5: 如何验证更新是否成功

**A**: 三种方式验证：

1. **控制台输出**：查看脚本的验证信息
2. **文件对比**：对比 `.backup` 文件和新文件
3. **浏览器测试**：在 WebUI 中测试 TOML 编辑器

### Q6: 翻译表太大了，如何优化

**A**: 可以考虑：

1. 合并相似的错误模式
2. 移除低频错误的翻译
3. 使用更通用的模式匹配

但建议保持完整性以提供更好的用户体验。

## 贡献

欢迎提交 Issue 或 Pull Request 来改进翻译质量！

### 提交新翻译

1. Fork 项目
2. 编辑 `scripts/generate-translations.js`
3. 运行测试：`node scripts/update-all-translations.js`
4. 提交 PR

### 报告翻译问题

如果发现翻译不准确，请提供：

- 原始英文错误信息
- 当前中文翻译
- 建议的改进翻译
- 触发该错误的 TOML 内容示例

## 许可

本工具遵循项目主许可证。
