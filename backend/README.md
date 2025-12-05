# WebUI Auth Plugin

WebUI 前端认证插件，提供固定端口的发现服务和带验证的 API 接口。

## 功能概述

本插件实现了以下功能：

1. **发现服务器** - 在固定端口（12138）启动 uvicorn + FastAPI 服务器
2. **服务发现** - 前端通过发现服务器获取主程序的 IP 和端口
3. **登录验证** - 提供带有 API Key 验证的登录接口
4. **数据接口** - 提供仪表盘统计、插件列表等受保护的 API 接口

## 工作流程

```text
前端 → 发现服务器(固定端口12138) → 返回主程序端口和IP 
    → 通过主程序的端口和IP访问插件系统定义的API接口
```

### 详细流程

1. **前端启动时**：
   - 前端访问 `http://<hostname>:12138/server-info` 获取主程序 IP 和端口
   - 发现服务器返回 `{ host: "127.0.0.1", port: 8000 }`

2. **用户登录**：
   - 前端根据返回的 IP 和端口自行拼接登录 URL
   - 向 `http://{host}:{port}/plugin-api/webui_auth/auth/login` 发送 GET 请求
   - 在请求头 `X-API-Key` 中携带用户输入的密钥
   - 主程序的 `VerifiedDep` 自动验证密钥
   - 验证成功返回登录成功响应，失败返回 401/403

3. **访问受保护接口**：
   - 前端使用用户输入的密钥作为 API Key
   - 在请求头中添加 `X-API-Key: <用户输入的密钥>`
   - 访问 `http://{host}:{port}/plugin-api/webui_auth/auth/<endpoint>` 获取数据

## 文件结构

```text
webui_auth_plugin/
├── __init__.py              # 模块入口
├── _manifest.json           # 插件清单文件
├── plugin.py                # 主插件类
├── discovery_server.py      # 发现服务器模块
├── handlers/
│   ├── __init__.py
│   ├── startup_handler.py   # 启动事件处理器
│   └── shutdown_handler.py  # 关闭事件处理器
└── routers/
    ├── __init__.py
    └── auth_router.py       # 认证路由组件
```

## API 端点

### 发现服务器端点 (端口 12138)

| 方法 | 路径 | 描述 | 是否需要认证 |
|------|------|------|-------------|
| GET | `/` | 服务状态检查 | 否 |
| GET | `/server-info` | 获取主程序服务器信息和登录URL | 否 |

### 主程序 API 端点

基础路径: `/plugin-api/webui_auth/auth`

| 方法 | 路径 | 描述 | 是否需要认证 |
|------|------|------|-------------|
| GET | `/health` | 健康检查 | 否 |
| GET | `/login` | 登录验证（请求头携带密钥） | 是 |
| POST | `/verify-token` | 验证 Token 是否有效 | 否 |
| GET | `/user-info` | 获取用户信息 | 是 |
| GET | `/dashboard/stats` | 获取仪表盘统计 | 是 |
| GET | `/plugins` | 获取插件列表 | 是 |
| GET | `/config` | 获取配置信息 | 是 |

## 配置说明

插件会自动生成 `config.toml` 配置文件：

```toml
# 插件基本配置
[plugin]
# 是否启用插件
enable = true

# 发现服务器配置
[discovery]
# 发现服务器端口（固定端口，供前端发现主程序）
port = 12138
# 发现服务器绑定地址
host = "0.0.0.0"

# 认证配置
[auth]
# 有效的API Key列表，用于验证前端请求
api_keys = ["mofox-default-key"]
# 会话超时时间（分钟），默认24小时
session_timeout_minutes = 1440

# 主程序服务器配置
[main_server]
# 主程序HTTP服务器地址
host = "127.0.0.1"
# 主程序HTTP服务器端口
port = 8000
```

## 前端使用示例

### 1. 获取服务器信息

```typescript
// 获取主程序 IP 和端口
const response = await fetch('http://localhost:12138/server-info')
const { host, port } = await response.json()
// 返回: { host: "127.0.0.1", port: 8000 }

// 前端自行拼接各种 URL
const apiBaseUrl = `http://${host}:${port}`
const loginUrl = `${apiBaseUrl}/plugin-api/webui_auth/auth/login`
const pluginApiUrl = `${apiBaseUrl}/plugin-api/webui_auth/auth`
```

### 2. 登录验证

```typescript
// 根据返回的 IP 和端口拼接登录 URL
const loginUrl = `http://${host}:${port}/plugin-api/webui_auth/auth/login`

// 用户输入的密钥直接作为 X-API-Key 发送
const response = await fetch(loginUrl, {
  method: 'GET',
  headers: {
    'X-API-Key': userInputPassword  // 用户输入的密钥
  }
})

if (response.ok) {
  const { success } = await response.json()
  if (success) {
    // 保存用户输入的密钥用于后续请求
    localStorage.setItem('api_key', userInputPassword)
  }
} else if (response.status === 401 || response.status === 403) {
  // 密钥验证失败
  console.error('密码错误')
}
```

### 3. 访问受保护接口

```typescript
const apiKey = localStorage.getItem('api_key')

// 根据 IP 和端口拼接 API URL
const statsUrl = `http://${host}:${port}/plugin-api/webui_auth/auth/dashboard/stats`

const response = await fetch(statsUrl, {
  headers: {
    'X-API-Key': apiKey
  }
})

const stats = await response.json()
```

## 安全注意事项

1. **更改默认 API Key**：
   - 生产环境中务必修改 `config.toml` 中的默认 API Key
   - 使用强密码作为 API Key

2. **网络配置**：
   - 如果只需本地访问，将 `discovery.host` 设置为 `127.0.0.1`
   - 生产环境建议配置反向代理和 HTTPS

3. **API Key 保管**：
   - API Key 列表存储在配置文件中
   - 确保配置文件的访问权限正确设置

## 依赖项

- `uvicorn` - ASGI 服务器
- `fastapi` - Web 框架
- `psutil` - 系统信息获取

这些依赖会在插件加载时自动检查和安装。

## 故障排除

### 发现服务器无法启动

1. 检查端口 12138 是否被占用
2. 检查防火墙设置

### 登录失败

1. 检查 API Key 是否正确配置
2. 查看日志中的错误信息

### 无法访问受保护接口

1. 确保在请求头中正确设置了 `X-API-Key`
2. 验证 API Key 是否在有效列表中
