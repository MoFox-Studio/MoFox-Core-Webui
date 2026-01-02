# MoFox-Bot WebUI

MoFox-Bot 的 Web 管理控制台，提供可视化的机器人管理界面。

## ✨ 功能特性

### 核心功能
- 📊 **实时数据监控**: 消息统计、插件状态、系统资源监控
- 🔌 **插件管理**: 查看、启用/禁用插件，可视化编辑配置
- 🛒 **插件市场**: 浏览、搜索、安装社区插件
- 🎭 **表情包管理**: 管理和组织表情包资源
- 👥 **人物关系管理**: 可视化管理角色关系
- 💬 **聊天室功能**: 实时聊天和消息广播
- 📝 **日志查看器**: 实时查看系统日志

### 自动更新功能 🔥
- 🔄 **一键更新 WebUI**: 在界面内直接检查和更新到最新版本
- 🔄 **一键更新主程序**: 通过 Git 自动更新 MoFox-Bot 主程序
- 📦 **自动安装依赖**: 更新后自动检测并安装新增依赖
- 🔙 **版本回滚**: 支持回滚到历史版本
- 🛡️ **备份保护**: 更新前自动备份，安全无忧

### 其他特性
- 📱 **响应式设计**: 支持桌面和移动端访问
- 🔐 **安全认证**: 基于 API Key 的访问控制
- 🔍 **服务发现**: 自动发现主程序的 IP 和端口
- 🤖 **每日自动构建**: GitHub Actions 每日自动构建最新版本

---

## 🚀 快速安装（推荐）

### 一行命令，支持自动更新！

这是最简单的安装方式，安装后可在 WebUI 界面内一键更新。

#### Windows PowerShell

```powershell
# 进入 MoFox-Bot 插件目录
cd <MoFox-Bot安装目录>/plugins

# 克隆 webui-dist 分支（预编译版本）
git clone -b webui-dist https://github.com/MoFox-Studio/MoFox-Core-Webui.git webui_backend
```

#### Linux / macOS

```bash
# 进入 MoFox-Bot 插件目录
cd <MoFox-Bot安装目录>/plugins

# 克隆 webui-dist 分支（预编译版本）
git clone -b webui-dist https://github.com/MoFox-Studio/MoFox-Core-Webui.git webui_backend
```

### 配置 API Key

编辑插件配置文件 `plugins/webui_backend/config/config.toml`：

   ```toml
   # --- 插件API密钥认证 ---
   # 用于访问需要认证的插件API的有效密钥列表
   # 如果列表为空，则所有需要认证的API都将无法访问
   # 例如: ["your-secret-key-1", "your-secret-key-2"]
   plugin_api_valid_keys = ["your-secret-api-key-here"]
   ```

   **重要说明**：
   - 请将 `your-secret-api-key-here` 替换为您自己的密钥（建议使用随机字符串）
   - 可以配置多个密钥，例如：`["key1", "key2", "key3"]`
   - 这个密钥将用于登录 WebUI，请妥善保管
   - 如果列表为空 `[]`，则无法登录 WebUI

### 启动并访问

1. 重启 MoFox-Bot
2. 打开浏览器访问：**http://localhost:12138**
3. 使用您配置的 API Key 登录

> ✅ **搞定！** 后续更新只需在 WebUI 设置页面点击「检查更新」即可。

---

## 🔄 自动更新使用说明

安装完成后，WebUI 自带自动更新功能，无需手动操作。

### WebUI 更新

1. 登录 WebUI
2. 进入 **设置** → **系统更新**
3. 点击 **检查更新**
4. 如有新版本，点击 **立即更新**

更新过程会自动：
- 从 GitHub 拉取最新代码
- 备份当前版本（支持回滚）
- 应用更新并刷新页面

### 主程序更新

WebUI 还支持更新 MoFox-Bot 主程序：

1. 进入 **设置** → **系统更新**
2. 在「主程序更新」部分点击 **检查更新**
3. 确认后点击 **执行更新**

更新后会自动：
- 检测 Python 虚拟环境类型（venv/conda）
- 安装新增的依赖包
- 提示重启主程序

---

## 📦 其他安装方式

### 方式二：手动下载 ZIP（不支持自动更新）

如果无法使用 Git，可以手动下载：

1. 访问 [webui-dist 分支](https://github.com/MoFox-Studio/MoFox-Core-Webui/tree/webui-dist)
2. 点击 **Code** → **Download ZIP**
3. 解压到 `plugins/webui_backend/`

> ⚠️ 此方式安装后无法使用 WebUI 内置的自动更新功能。

### 方式三：开发者模式

适合需要修改前端代码的开发者：

```bash
# 克隆完整仓库
git clone https://github.com/MoFox-Studio/MoFox-Core-Webui.git

# 后端：复制 backend 到插件目录
cp -r backend <MoFox-Bot>/plugins/webui_backend

# 前端：启动开发服务器
cd forward/mofox-webui
npm install
npm run dev

# 访问开发版：http://localhost:11451
```

---

## 🔧 工作原理

### 架构图

```
┌─────────────────────────────────────────────────────────────────┐
│                    用户浏览器                                    │
│                  http://localhost:12138                         │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                 发现服务器 (端口 12138)                          │
│  • 托管静态文件 (static/)                                        │
│  • GET /server-info → 返回主程序地址                             │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                    MoFox-Bot 主程序                              │
│                                                                  │
│  /plugin-api/webui_backend/                                     │
│    ├── /auth         认证接口                                    │
│    ├── /stats        统计数据                                    │
│    ├── /plugins      插件管理                                    │
│    ├── /config       配置管理                                    │
│    ├── /marketplace  插件市场                                    │
│    ├── /ui-update    WebUI 更新                                 │
│    ├── /git-update   主程序更新                                  │
│    └── ...                                                       │
└─────────────────────────────────────────────────────────────────┘
```

### 自动更新原理

WebUI 使用 Git 实现自动更新：

1. **检查更新**: `git fetch` 获取远程最新提交
2. **版本对比**: 比较本地和远程的 commit hash
3. **执行更新**: `git pull` 拉取最新代码
4. **备份回滚**: 记录更新前的 commit，支持 `git checkout` 回滚

---

## 📂 项目结构

```
webui_backend/                    # 插件目录（安装后的结构）
├── __init__.py                  # 模块入口
├── plugin.py                    # 主插件类
├── discovery_server.py          # 发现服务器 + 静态文件托管
├── static/                      # 编译好的前端静态文件
│   ├── index.html
│   └── assets/
├── adapters/                    # 适配器组件
├── apis/                        # 外部 API 集成
├── handlers/                    # 生命周期处理器
├── models/                      # 数据模型
├── plugins/                     # 子插件
├── routers/                     # API 路由
│   ├── auth_router.py          # 认证接口
│   ├── stats_router.py         # 统计数据
│   ├── plugin_router.py        # 插件管理
│   ├── config_router.py        # 配置管理
│   ├── marketplace_router.py   # 插件市场
│   ├── ui_update_router.py     # WebUI 更新
│   ├── git_update_router.py    # 主程序更新
│   ├── log_viewer_router.py    # 日志查看
│   ├── chatroom_router.py      # 聊天室
│   └── ...
├── storage/                     # 数据存储
└── utils/                       # 工具函数
    └── update/                  # 更新相关
        ├── git_detector.py      # Git 环境检测
        ├── git_installer.py     # Git 安装器
        ├── git_updater.py       # Git 更新器
        ├── ui_version_manager.py # UI 版本管理
        └── venv_utils.py        # 虚拟环境工具
```

---

## ⚙️ 配置说明

插件配置文件：`plugins/webui_backend/config/config.toml`

```toml
# 插件基本配置
[plugin]
enable = true                    # 是否启用插件

# 发现服务器配置
[discovery]
host = "0.0.0.0"                # 绑定地址
port = 12138                    # 固定端口

# 认证配置
[auth]
api_keys = ["your-api-key"]     # API 密钥列表
session_timeout_minutes = 1440   # 会话超时（分钟）

# 主程序服务器配置
[main_server]
host = "127.0.0.1"              # 主程序地址
port = 8000                     # 主程序端口
```

---

## 🔐 安全性

- **API Key 验证**: 所有接口都需要在请求头中携带 `X-API-Key`
- **固定发现端口**: 仅发现服务使用固定端口 12138
- **CORS 配置**: 支持跨域访问
- **会话管理**: 可配置会话超时时间

---

## 🛠️ 技术栈

### 前端
- **Vue 3** + **TypeScript** - 类型安全的渐进式框架
- **Vite** - 下一代前端构建工具
- **Vue Router** + **Pinia** - 路由和状态管理
- **ECharts** - 数据可视化

### 后端
- **FastAPI** + **Uvicorn** - 高性能 Python Web 框架
- **MoFox Plugin System** - 插件系统集成

---

## 📝 开发状态

- [x] 后端插件系统
- [x] 服务发现机制
- [x] 用户认证
- [x] 仪表盘统计
- [x] 插件管理
- [x] 插件市场
- [x] 配置编辑器
- [x] 响应式布局
- [x] 静态文件托管
- [x] WebUI 自动更新
- [x] 主程序自动更新
- [x] 依赖自动安装
- [x] 版本回滚
- [x] 实时日志查看
- [x] 聊天室功能
- [x] 表情包管理
- [x] 人物关系管理
- [ ] 消息历史查看
- [ ] 定时任务管理

---

## 🔄 自动构建说明

GitHub Actions 每日自动构建：

- **触发时间**: 每天 UTC 00:00（北京时间 08:00）
- **触发条件**: 代码变更时触发，无变更则跳过
- **发布分支**: `webui-dist`（预编译版本）
- **版本格式**: `Build: vYYYY.MMDD.HHMM`

手动触发：在 GitHub Actions 页面点击 "Run workflow"

---

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📄 许可证

本项目采用 GPL3 许可证。详见 [LICENSE](LICENSE) 文件。
