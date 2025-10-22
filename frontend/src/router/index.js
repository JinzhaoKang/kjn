import { createRouter, createWebHistory } from 'vue-router'
import NProgress from 'nprogress'

// 布局组件
const BasicLayout = () => import('@/views/layouts/BasicLayout.vue')

// 页面组件 - 懒加载
const Dashboard = () => import('@/views/Dashboard.vue')
const FeedbackManagement = () => import('@/views/FeedbackManagement.vue')
const FeedbackImport = () => import('@/views/FeedbackImport.vue')
const AnalysisEngine = () => import('@/views/AnalysisEngine.vue')
const AnalysisReports = () => import('@/views/AnalysisReports.vue')
const DecisionEngine = () => import('@/views/DecisionEngine.vue')
const IssueManagement = () => import('@/views/IssueManagement.vue')
const Reports = () => import('@/views/Reports.vue')
const Settings = () => import('@/views/Settings.vue')
const SpiderManagement = () => import('@/views/SpiderManagement.vue')
const InsightsManagement = () => import('@/views/InsightsManagement.vue')

// 错误页面
const NotFound = () => import('@/views/error/NotFound.vue')
const Forbidden = () => import('@/views/error/Forbidden.vue')
const ServerError = () => import('@/views/error/ServerError.vue')

const routes = [
  {
    path: '/',
    redirect: '/dashboard'
  },
  {
    path: '/dashboard',
    name: 'Dashboard',
    component: Dashboard,
    meta: {
      title: '仪表板',
      menuKey: 'dashboard',
      icon: 'DashboardOutlined',
      requiresAuth: true,
      keepAlive: true
    }
  },
  {
    path: '/feedback',
    name: 'FeedbackManagement',
    component: FeedbackManagement,
    meta: {
      title: '反馈管理',
      menuKey: 'feedback-list',
      icon: 'MessageOutlined',
      requiresAuth: true,
      keepAlive: true
    }
  },
  {
    path: '/feedback/import',
    name: 'FeedbackImport',
    component: FeedbackImport,
    meta: {
      title: '批量导入',
      parentKey: 'feedback',
      menuKey: 'feedback-import',
      icon: 'UploadOutlined',
      requiresAuth: true,
      keepAlive: false
    }
  },
  {
    path: '/analysis',
    name: 'AnalysisEngine',
    component: AnalysisEngine,
    meta: {
      title: '分析引擎',
      menuKey: 'analysis-engine',
      icon: 'BarChartOutlined',
      requiresAuth: true,
      keepAlive: true
    }
  },
  {
    path: '/analysis/reports',
    name: 'AnalysisReports',
    component: AnalysisReports,
    meta: {
      title: '分析报告',
      parentKey: 'analysis',
      menuKey: 'analysis-reports',
      icon: 'FileTextOutlined',
      requiresAuth: true,
      keepAlive: true
    }
  },
  {
    path: '/decision-engine',
    name: 'DecisionEngine',
    component: DecisionEngine,
    meta: {
      title: '决策引擎',
      menuKey: 'decision-engine',
      icon: 'BranchesOutlined',
      requiresAuth: true,
      keepAlive: true
    }
  },
  {
    path: '/issues',
    name: 'IssueManagement',
    component: IssueManagement,
    meta: {
      title: '问题管理',
      menuKey: 'issues',
      icon: 'BugOutlined',
      requiresAuth: true,
      keepAlive: true
    }
  },
  {
    path: '/reports',
    name: 'Reports',
    component: Reports,
    meta: {
      title: '报告中心',
      menuKey: 'reports',
      icon: 'FileTextOutlined',
      requiresAuth: true,
      keepAlive: true
    }
  },
  {
    path: '/spider',
    name: 'SpiderManagement',
    component: SpiderManagement,
    meta: {
      title: '爬虫管理',
      menuKey: 'spider',
      icon: 'BugOutlined',
      requiresAuth: true,
      keepAlive: true
    }
  },
      {
      path: '/insights',
      name: 'InsightsManagement',
      component: InsightsManagement,
      meta: {
        title: '智能洞察',
        menuKey: 'insights',
        icon: 'BulbOutlined',
        requiresAuth: true,
        keepAlive: true
      }
    },
  {
    path: '/settings',
    name: 'Settings',
    component: Settings,
    meta: {
      title: '系统设置',
      menuKey: 'settings',
      icon: 'SettingOutlined',
      requiresAuth: true,
      keepAlive: false
    }
  },
  // 错误页面路由
  {
    path: '/403',
    name: 'Forbidden',
    component: Forbidden,
    meta: {
      title: '访问被拒绝',
      hideInMenu: true
    }
  },
  {
    path: '/500',
    name: 'ServerError',
    component: ServerError,
    meta: {
      title: '服务器错误',
      hideInMenu: true
    }
  },
  {
    path: '/:pathMatch(.*)*',
    name: 'NotFound',
    component: NotFound,
    meta: {
      title: '页面不存在',
      hideInMenu: true
    }
  }
]

const router = createRouter({
  history: createWebHistory(process.env.BASE_URL),
  routes,
  scrollBehavior(to, from, savedPosition) {
    if (savedPosition) {
      return savedPosition
    } else {
      return { top: 0 }
    }
  }
})

// 路由白名单
const whiteList = ['/login', '/register', '/403', '/404', '/500']

// 全局前置守卫
router.beforeEach(async (to, from, next) => {
  // 开始进度条
  NProgress.start()

  // 设置页面标题
  if (to.meta?.title) {
    document.title = `${to.meta.title} - 用户反馈分析系统`
  } else {
    document.title = '用户反馈分析系统'
  }

  // 权限验证
  if (to.meta?.requiresAuth) {
    // 这里可以添加用户认证逻辑
    // const token = localStorage.getItem('access_token')
    // if (!token) {
    //   next('/login')
    //   return
    // }
    
    // 验证用户权限
    // const hasPermission = await checkPermission(to.meta.permission)
    // if (!hasPermission) {
    //   next('/403')
    //   return
    // }
  }

  next()
})

// 全局后置守卫
router.afterEach((to, from) => {
  // 结束进度条
  NProgress.done()

  // 页面访问统计
  if (process.env.NODE_ENV === 'production') {
    // 可以在这里添加页面访问统计代码
    // trackPageView(to.path)
  }
})

// 路由错误处理
router.onError((error) => {
  console.error('路由错误:', error)
  NProgress.done()
})

export default router

// 导出路由工具函数
export const getRouteByName = (name) => {
  return routes.find(route => route.name === name)
}

export const getMenuRoutes = () => {
  return routes.filter(route => !route.meta?.hideInMenu && route.meta?.title)
}

export const getBreadcrumbList = (route) => {
  const matched = route.matched.filter(item => item.meta?.title)
  const breadcrumbs = []
  
  matched.forEach(item => {
    breadcrumbs.push({
      path: item.path,
      name: item.name,
      title: item.meta.title,
      icon: item.meta.icon
    })
  })
  
  return breadcrumbs
} 