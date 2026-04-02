/**
 * @file main.ts
 * @description 应用程序入口文件
 * 
 * 该文件负责：
 * 1. 创建 Vue 应用实例
 * 2. 配置和安装 Pinia 状态管理
 * 3. 配置和安装 Vue Router 路由
 * 4. 导入全局样式
 * 5. 挂载应用到 DOM
 */

// ==================== 依赖导入 ====================
import { createApp } from 'vue'      // Vue 3 核心方法，用于创建应用实例
import { createPinia } from 'pinia'  // Pinia 状态管理库
import router from './router'         // 路由配置
import App from './App.vue'           // 根组件
import './style.css'                  // 全局样式表
import 'material-symbols/rounded.css' // Material Symbols 图标字体（本地）

// ==================== 应用初始化 ====================

// 创建 Vue 应用实例，传入根组件
const app = createApp(App)

// 创建 Pinia 实例，用于全局状态管理
const pinia = createPinia()

// ==================== 插件安装 ====================

// 安装 Pinia 插件，启用状态管理功能
app.use(pinia)

// 安装路由插件，启用页面导航功能
app.use(router)

// ==================== 挂载应用 ====================

// 将应用挂载到 index.html 中 id 为 "app" 的元素上
app.mount('#app')
