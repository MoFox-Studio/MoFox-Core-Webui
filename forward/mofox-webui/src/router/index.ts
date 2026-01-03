import { createRouter, createWebHistory, type RouteRecordRaw } from 'vue-router'

// ==================== 路由懒加载 ====================
// 使用动态 import 实现代码分割，优化首屏加载速度

// 核心页面（首屏需要，保持同步加载）
import Login from '@/views/Login.vue'
import Dashboard from '@/views/Dashboard.vue'

// 仪表盘子页面（懒加载）
const DashboardHome = () => import('@/views/DashboardHome.vue')
const BotConfigView = () => import('@/views/BotConfigView.vue')
const ModelConfigView = () => import('@/views/ModelConfigView.vue')
const ModelStatsView = () => import('@/views/ModelStatsView.vue')
const ThemeConfigView = () => import('@/views/ThemeConfigView.vue')

// 插件相关页面（懒加载）
const PluginConfigList = () => import('@/views/PluginConfigList.vue')
const PluginConfigView = () => import('@/views/PluginConfigView.vue')
const PluginManageView = () => import('@/views/PluginManageView.vue')
const PluginDetailView = () => import('@/views/PluginDetailView.vue')
const PluginMarketplace = () => import('@/views/PluginMarketplace.vue')
const PluginMarketplaceDetail = () => import('@/views/PluginMarketplaceDetail.vue')

// 功能页面（懒加载）
const ExpressionView = () => import('@/views/ExpressionView.vue')
const RelationshipView = () => import('@/views/RelationshipView.vue')
const EmojiManager = () => import('@/components/emoji/EmojiManager.vue')
const ChatroomView = () => import('@/views/ChatroomView.vue')
const LiveChatView = () => import('@/views/LiveChatView.vue')

// 系统页面（懒加载）
const GitUpdateView = () => import('@/views/GitUpdateView.vue')
const GitHubView = () => import('@/views/GitHubView.vue')
const LogViewerView = () => import('@/views/LogViewerView.vue')
const LiveLogView = () => import('@/views/LiveLogView.vue')
const InitializationView = () => import('@/views/InitializationView.vue')

const routes: Array<RouteRecordRaw> = [
  {
    path: '/',
    redirect: '/login'
  },
  {
    path: '/login',
    name: 'Login',
    component: Login,
    meta: { requiresAuth: false }
  },
  {
    path: '/initialization',
    name: 'Initialization',
    component: InitializationView,
    meta: { requiresAuth: true, skipInitCheck: true }
  },
  {
    path: '/dashboard',
    component: Dashboard,
    meta: { requiresAuth: true },
    children: [
      {
        path: '',
        name: 'DashboardHome',
        component: DashboardHome
      },
      {
        path: 'model-stats',
        name: 'ModelStats',
        component: ModelStatsView
      },
      {
        path: 'theme',
        name: 'ThemeConfig',
        component: ThemeConfigView
      },
      {
        path: 'bot-config',
        name: 'BotConfig',
        component: BotConfigView
      },
      {
        path: 'model-config',
        name: 'ModelConfig',
        component: ModelConfigView
      },
      {
        path: 'plugin-config',
        name: 'PluginConfigList',
        component: PluginConfigList
      },
      {
        path: 'plugin-config/:path(.*)',
        name: 'PluginConfigView',
        component: PluginConfigView,
        props: true
      },
      {
        path: 'plugin-manage',
        name: 'PluginManage',
        component: PluginManageView
      },
      {
        path: 'plugin-manage/:pluginName',
        name: 'PluginDetail',
        component: PluginDetailView,
        props: true
      },
      {
        path: 'marketplace',
        name: 'PluginMarketplace',
        component: PluginMarketplace
      },
      {
        path: 'marketplace/:pluginId',
        name: 'PluginMarketplaceDetail',
        component: PluginMarketplaceDetail,
        props: true
      },
      {
        path: 'expression',
        name: 'Expression',
        component: ExpressionView
      },
      {
        path: 'relationship',
        name: 'Relationship',
        component: RelationshipView
      },
      {
        path: 'emoji-manager',
        name: 'EmojiManager',
        component: EmojiManager
      },
      {
        path: 'chatroom',
        name: 'Chatroom',
        component: ChatroomView
      },
      {
        path: 'live-chat',
        name: 'LiveChat',
        component: LiveChatView
      },
      {
        path: 'git-update',
        name: 'GitUpdate',
        component: GitUpdateView
      },
      {
        path: 'github',
        name: 'GitHub',
        component: GitHubView
      },
      {
        path: 'log-viewer',
        name: 'LogViewer',
        component: LogViewerView
      },
      {
        path: 'live-log',
        name: 'LiveLog',
        component: LiveLogView
      }
    ]
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// ==================== 初始化状态缓存 ====================
// 缓存初始化状态，供组件使用
let initStatusCache: { isInitialized: boolean; timestamp: number } | null = null
const CACHE_DURATION = 60000 // 缓存1分钟

/**
 * 获取初始化状态（带缓存）
 * 供组件调用，非阻塞式
 */
export async function checkInitStatus(): Promise<boolean> {
  const now = Date.now()
  
  // 如果有有效缓存，直接返回
  if (initStatusCache && (now - initStatusCache.timestamp) < CACHE_DURATION) {
    return initStatusCache.isInitialized
  }
  
  try {
    // 动态导入避免循环依赖
    const { getInitStatus } = await import('@/api/initialization')
    const result = await getInitStatus()
    if (result.success && result.data) {
      initStatusCache = {
        isInitialized: result.data.is_initialized,
        timestamp: now
      }
      return result.data.is_initialized
    }
  } catch (error) {
    console.error('检查初始化状态失败:', error)
  }
  
  // 出错时返回 true，允许继续访问（避免阻塞）
  return true
}

/**
 * 清除初始化状态缓存（用于初始化完成后）
 */
export function clearInitStatusCache() {
  initStatusCache = null
}

// ==================== 路由守卫 ====================
// 轻量级守卫，只做认证检查，初始化状态检查移到 Dashboard 组件内
router.beforeEach((to, _from, next) => {
  const isAuthenticated = localStorage.getItem('mofox_token')
  
  // 检查是否需要认证
  if (to.meta.requiresAuth && !isAuthenticated) {
    next('/login')
    return
  }
  
  // 登录页逻辑：已登录则跳转到仪表盘
  if (to.path === '/login' && isAuthenticated) {
    next('/dashboard')
    return
  }
  
  next()
})

export default router
