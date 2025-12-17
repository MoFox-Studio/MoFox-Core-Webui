# MoFox-Bot WebUI

MoFox-Bot 的 Web 管理控制台，提供可视化的机器人管理界面。

## ✨ 功能特性

### 前端功能
- 📊 **实时数据监控**: 消息统计、插件状态、系统资源监控
- 🔌 **插件管理**: 查看、启用/禁用插件，查看插件配置
- 🛒 **插件市场**: 浏览、搜索、安装社区插件
- ⚙️ **配置管理**: 可视化编辑插件配置
- 📱 **响应式设计**: 支持桌面和移动端访问
- � **安全认证**: 基于 API Key 的访问控制

### 后端功能
- � **服务发现**: 自动发现主程序的 IP 和端口
- 🔑 **身份验证**: API Key 验证机制
- 📡 **RESTful API**: 提供完整的数据接口
- 🔌 **插件系统集成**: 直接调用 MoFox-Bot 插件系统 API

## 📦 安装步骤

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

### 构建前端

```bash
cd forward/mofox-webui
npm run build
```

构建完成后，静态文件将生成在 `forward/mofox-webui/dist` 目录。

### 部署前端

可以使用任何静态文件服务器部署，例如：

- **Nginx**
- **Apache**
- **Caddy**
- 或直接使用 `serve` 包：
  ```bash
  npm install -g serve
  serve -s dist -l 11451
  ```

## 🔧 工作原理

```
┌─────────────┐       ┌──────────────────┐       ┌─────────────┐
│   前端 UI   │──1──▶ │ 发现服务器:12138 │──2──▶ │  返回信息   │
│ localhost:  │       │  (固定端口)      │       │ host + port │
│   11451     │       └──────────────────┘       └─────────────┘
└──────┬──────┘                                          │
       │                                                 │
       └────────────────3. 使用返回的地址访问─────────────┘
                              ▼
                    ┌──────────────────┐
                    │   主程序 API     │
                    │ plugins/         │
                    │ webui_backend/*  │
                    └──────────────────┘
```

1. 前端访问固定端口 12138 获取主程序地址
2. 发现服务器返回主程序的 IP 和端口
3. 前端使用获取的地址 + API Key 访问受保护的接口

## 📂 项目结构

```
MoFox-Core-Webui/
├── backend/                    # 后端插件（需要复制到 Bot 插件目录）
│   ├── plugin.py              # 主插件类
│   ├── discovery_server.py    # 服务发现服务器（端口 12138）
│   ├── handlers/              # 生命周期处理器
│   │   ├── startup_handler.py
│   │   └── shutdown_handler.py
│   └── routers/               # API 路由
│       ├── auth.py           # 认证接口
│       ├── stats.py          # 统计数据接口
│       ├── plugin_mgmt.py    # 插件管理接口
│       ├── config_mgmt.py    # 配置管理接口
│       └── marketplace.py    # 插件市场接口
│
└── forward/                   # 前端项目
    └── mofox-webui/
        ├── src/
        │   ├── components/   # Vue 组件
        │   ├── views/        # 页面视图
        │   ├── router/       # 路由配置
        │   └── stores/       # 状态管理
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
- [ ] 实时日志查看
- [ ] 消息历史查看
- [ ] 定时任务管理

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📄 许可证

本项目采用 GPL3 许可证。详见 [LICENSE](LICENSE) 文件。
