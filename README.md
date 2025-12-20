# MoFox-Bot WebUI

MoFox-Bot 的 Web 管理控制台，提供可视化的机器人管理界面。

## ✨ 功能特性

### 前端功能
- 📊 **实时数据监控**: 消息统计、插件状态、系统资源监控
- 🔌 **插件管理**: 查看、启用/禁用插件，查看插件配置
- 🛒 **插件市场**: 浏览、搜索、安装社区插件
- ⚙️ **配置管理**: 可视化编辑插件配置
- 📱 **响应式设计**: 支持桌面和移动端访问
- 🔐 **安全认证**: 基于 API Key 的访问控制

### 后端功能
- 🔍 **服务发现**: 自动发现主程序的 IP 和端口
- �️ **静态文件托管**: 自动托管编译好的前端文件
- �🔑 **身份验证**: API Key 验证机制
- 📡 **RESTful API**: 提供完整的数据接口
- 🔌 **插件系统集成**: 直接调用 MoFox-Bot 插件系统 API
- 🤖 **自动构建**: GitHub Actions 每日自动构建并发布前端

## 📦 安装步骤

### 方式一：使用预编译版本（推荐）

**适合不想自己编译前端的用户**

1. **从 Release 下载完整后端插件包**

   访问 [Releases](https://github.com/ikun-11451/MoFox-Core-Webui/releases) 页面，下载最新的 `mofox-webui-backend.zip`

2. **解压到插件目录**

   将下载的 ZIP 文件解压到 MoFox-Bot 的插件目录，并重命名为 `webui_backend`：
   ```
   <MoFox-Bot安装目录>/
   └── plugins/
       └── webui_backend/           # ← 解压并重命名
           ├── __init__.py
           ├── plugin.py
           ├── discovery_server.py
           ├── static/              # 编译好的前端文件
           │   ├── index.html
           │   └── assets/
           ├── handlers/
           └── routers/
   ```

3. **配置 API Key**

   打开 MoFox-Bot 的配置文件 `bot_config.toml`，配置 API 密钥：
   ```toml
   plugin_api_valid_keys = ["your-secret-api-key-here"]
   ```

4. **启动并访问**

   重启 MoFox-Bot，然后访问 http://localhost:12138 即可使用 WebUI！
   
   > **说明**: Release 包已包含完整的后端代码和编译好的前端，开箱即用。

### 方式二：本地开发（开发者使用）

**适合需要修改前端或进行开发的用户**

### 第一步：安装后端插件

1. **复制后端文件到插件目录**

   将 `backend` 文件夹复制到 MoFox-Bot 的插件目录：
   ```
   <MoFox-Bot安装目录>/plugins/
   ```

   完整路径示例：
   ```
   MoFox-Bot/
   └── plugins/
       └── webui_backend/         # ← 将 backend 文件夹重命名为 webui_backend
           ├── __init__.py
           ├── plugin.py
           ├── discovery_server.py
           ├── handlers/
           └── routers/
   ```

2. **配置 API Key**

   打开 MoFox-Bot 的配置文件 `bot_config.toml`（通常在 config 目录下），找到 `plugin_api_valid_keys` 配置项：

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

3. **重启 MoFox-Bot**

   保存配置后重启 Bot，插件会自动加载，并在固定端口 **12138** 启动发现服务器。

### 第二步：启动前端

1. **进入前端目录**
   ```bash
   cd forward/mofox-webui
   ```

2. **安装依赖**
   ```bash
   npm install
   # 或使用 pnpm
   pnpm install
   ```

3. **启动开发服务器**
   ```bash
   npm run dev
   ```

4. **访问 WebUI**
   
   打开浏览器访问：http://localhost:11451

5. **登录**
   
   使用您在 `bot_config.toml` 中配置的 API Key 登录（即 `plugin_api_valid_keys` 中的任意一个密钥）

## 🚀 生产部署

### 自动构建发布

本项目配置了 GitHub Actions 自动构建：
- **构建时间**: 每天 UTC 00:00（北京时间 08:00）
- **发布内容**: 完整的后端插件包（包含所有 Python 代码和编译好的前端）打包为 `mofox-webui-backend.zip`
- **保留策略**: 保留最近 7 个版本
- **智能构建**: 只有在有新提交时才会构建，避免重复构建
- **手动触发**: 支持在 GitHub Actions 页面手动触发构建

### 手动构建前端

如果需要自己构建前端：

```bash
cd forward/mofox-webui
npm install
npm run build
```

构建完成后，将 `dist/` 目录的内容复制到 `backend/static/`：

```bash
# Linux/Mac
cp -r forward/mofox-webui/dist/* backend/static/

# Windows PowerShell
Copy-Item -Path forward\mofox-webui\dist\* -Destination backend\static\ -Recurse
```

### 使用独立静态服务器

如果不想使用集成的静态文件托管，可以使用独立服务器部署前端：

**使用 Nginx**
```nginx
server {
    listen 80;
    server_name your-domain.com;
    
    root /path/to/mofox-webui/dist;
    index index.html;
    
    location / {
        try_files $uri $uri/ /index.html;
    }
}
```

**使用 Caddy**
```
your-domain.com {
    root * /path/to/mofox-webui/dist
    file_server
    try_files {path} /index.html
}
```

**使用 serve (快速测试)**
```bash
npm install -g serve
serve -s dist -l 11451
```

## 🔧 工作原理

### 架构图

```
┌─────────────┐                                      ┌─────────────┐
│  前端开发   │                                      │  前端生产   │
│  模式       │                                      │  模式       │
│ localhost:  │                                      │             │
│   11451     │                                      │             │
└──────┬──────┘                                      └──────┬──────┘
       │                                                    │
       │ 1. 发现服务器地址                                   │ 1. 访问静态文件
       ▼                                                    ▼
┌──────────────────────────────────────────────────────────────────┐
│                    发现服务器 (端口 12138)                         │
│                                                                  │
│  • GET /api/server-info   ← 返回主程序地址信息                    │
│  • GET /api/health        ← 服务健康检查                          │
│  • GET /                  ← 托管静态文件 (backend/static/)        │
│                             (如果存在编译好的前端)                  │
└──────────────────────┬───────────────────────────────────────────┘
                       │ 2. 返回主程序地址
                       │    {host, port}
                       ▼
       ┌───────────────────────────────────────┐
       │ 3. 使用返回的地址 + API Key 访问       │
       ▼                                       │
┌──────────────────┐                          │
│   主程序 API     │◄─────────────────────────┘
│ 插件系统路由      │
│ /plugin-api/*    │
└──────────────────┘
```

### 工作流程

1. **开发模式**: 
   - 前端运行在 `localhost:11451`
   - 通过发现服务器获取后端地址
   - 使用 Vite 开发服务器的热重载功能
   
2. **生产模式**: 
   - 前端编译后放在 `backend/static/`
   - 用户直接访问 `localhost:12138`
   - 发现服务器直接返回静态文件
   - API 请求通过 `/api/server-info` 获取后端地址

## 📂 项目结构

```
MoFox-Core-Webui/
├── .github/
│   └── workflows/
│       └── build-and-release.yml   # 自动构建发布工作流
│
├── backend/                        # 后端插件（需要复制到 Bot 插件目录）
│   ├── plugin.py                  # 主插件类
│   ├── discovery_server.py        # 服务发现服务器（端口 12138）+ 静态文件托管
│   ├── static/                    # 编译好的前端静态文件（由 CI 构建或手动构建）
│   │   ├── index.html            # 前端入口
│   │   ├── assets/               # 静态资源
│   │   └── BUILD_INFO.txt        # 构建信息
│   ├── handlers/                  # 生命周期处理器
│   │   ├── startup_handler.py
│   │   └── shutdown_handler.py
│   └── routers/                   # API 路由
│       ├── auth.py               # 认证接口
│       ├── stats.py              # 统计数据接口
│       ├── plugin_mgmt.py        # 插件管理接口
│       ├── config_mgmt.py        # 配置管理接口
│       └── marketplace.py        # 插件市场接口
│
└── forward/                       # 前端开发项目
    └── mofox-webui/
        ├── src/
        │   ├── components/       # Vue 组件
        │   ├── views/            # 页面视图
        │   ├── router/           # 路由配置
        │   └── stores/           # 状态管理
        ├── dist/                 # 构建产物（npm run build 后生成）
        ├── package.json
        └── vite.config.ts
```

## ⚙️ 配置说明

### 后端配置
后端主要通过 MoFox-Bot 的 `config.toml` 进行配置，详细解释见[MoFox-Core Docs](https://docs.mofox-sama.com/docs/development/plugins/configuration-guide.html)。

### 前端配置

如果需要修改发现服务器地址，编辑 `forward/mofox-webui/src/api/config.ts`：

```typescript
export const DISCOVERY_SERVER_URL = 'http://localhost:12138'
```

## 🔐 安全性

- **API Key 验证**: 所有接口都需要在请求头中携带 `X-API-Key`
- **固定发现端口**: 仅发现服务使用固定端口，主要 API 使用动态端口
- **CORS 配置**: 后端已配置 CORS，支持跨域访问

## 🛠️ 技术栈

### 前端
- **Vue 3** - 渐进式 JavaScript 框架
- **TypeScript** - 类型安全
- **Vite** - 下一代前端构建工具
- **Vue Router** - 官方路由管理器
- **Pinia** - 轻量级状态管理
- **ECharts** - 数据可视化
- **Marked** - Markdown 渲染

### 后端
- **FastAPI** - 现代 Python Web 框架
- **Uvicorn** - ASGI 服务器
- **MoFox Plugin System** - 插件系统集成

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
- [x] 自动构建发布
- [ ] 实时日志查看
- [ ] 消息历史查看
- [ ] 定时任务管理

## 🔄 自动构建说明

本项目使用 GitHub Actions 实现自动构建和发布：

- **触发时间**: 每天 UTC 00:00（北京时间 08:00）
- **构建内容**: 
  1. 安装前端依赖
  2. 编译前端项目
  3. 复制编译产物到 `backend/static/`
  4. 打包为 `mofox-webui-static.zip`
  5. 创建 GitHub Release 并上传
- **版本格式**: `v年.月日.时分` (例如: `v2025.1213.0800`)
- **保留策略**: 自动保留最近 7 个版本，删除旧版本
- **手动触发**: 可以在 Actions 页面手动触发构建

### 使用自动构建的版本

1. 访问 [Releases](https://github.com/ikun-11451/MoFox-Core-Webui/releases) 页面
2. 下载最新的 `mofox-webui-static.zip`
3. 解压到 `backend/` 目录
4. 重启后端服务即可

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📄 许可证

本项目采用 GPL3 许可证。详见 [LICENSE](LICENSE) 文件。
