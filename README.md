# MoFox-Bot WebUI

这是一个基于 Vue 3 + TypeScript + Vite 构建的 MoFox-Bot 管理控制台前端项目。

## 项目特性

- 🎨 **像素风格 UI**: 采用 Press Start 2P 字体和复古配色
- 📱 **响应式设计**: 适配桌面和移动端设备
- 📊 **数据可视化**: 集成 ECharts 展示统计数据
- 🔐 **状态管理**: 使用 Pinia 管理用户状态
- ⚡ **极速开发**: 基于 Vite 的快速构建工具

## 目录结构

```
mofox-webui/
├── public/              # 静态资源
├── src/
│   ├── components/      # 公共组件
│   ├── router/          # 路由配置
│   ├── stores/          # Pinia 状态管理
│   ├── views/           # 页面视图
│   ├── App.vue          # 根组件
│   ├── main.ts          # 入口文件
│   └── style.css        # 全局样式
├── index.html           # HTML 模板
├── package.json         # 项目依赖
├── tsconfig.json        # TypeScript 配置
└── vite.config.ts       # Vite 配置
```

## 快速开始

### 1. 安装依赖

```bash
npm install
```

### 2. 启动开发服务器

```bash
npm run dev
```

访问 http://localhost:3000 即可查看项目。

### 3. 构建生产版本

```bash
npm run build
```

## 开发进度

- [x] 项目初始化
- [x] 登录页面 (UI + 逻辑)
- [x] 仪表盘布局
- [x] 核心统计卡片
- [x] 系统状态展示
- [ ] 实时数据对接 (API)
- [ ] 更多图表组件
- [ ] 插件管理功能

## 注意事项

- 目前登录功能为模拟实现，任意用户名密码即可登录。
- 数据展示为静态 Mock 数据，后续需要对接后端 API。
