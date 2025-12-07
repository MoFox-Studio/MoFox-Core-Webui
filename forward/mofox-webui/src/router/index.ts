import { createRouter, createWebHistory, type RouteRecordRaw } from 'vue-router'
import Login from '@/views/Login.vue'
import Dashboard from '@/views/Dashboard.vue'
import DashboardHome from '@/views/DashboardHome.vue'
import BotConfigView from '@/views/BotConfigView.vue'
import ModelConfigView from '@/views/ModelConfigView.vue'
import PluginConfigList from '@/views/PluginConfigList.vue'
import PluginConfigView from '@/views/PluginConfigView.vue'
import PluginManageView from '@/views/PluginManageView.vue'
import PluginDetailView from '@/views/PluginDetailView.vue'
import PluginMarketplace from '@/views/PluginMarketplace.vue'
import PluginMarketplaceDetail from '@/views/PluginMarketplaceDetail.vue'
import GitUpdateView from '@/views/GitUpdateView.vue'
import LogViewerView from '@/views/LogViewerView.vue'

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
        path: 'plugin-config/:pluginPath',
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
        path: 'git-update',
        name: 'GitUpdate',
        component: GitUpdateView
      },
      {
        path: 'log-viewer',
        name: 'LogViewer',
        component: LogViewerView
      }
    ]
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// 路由守卫
router.beforeEach((to, _from, next) => {
  const isAuthenticated = localStorage.getItem('mofox_token')
  
  if (to.meta.requiresAuth && !isAuthenticated) {
    next('/login')
  } else if (to.path === '/login' && isAuthenticated) {
    next('/dashboard')
  } else {
    next()
  }
})

export default router
