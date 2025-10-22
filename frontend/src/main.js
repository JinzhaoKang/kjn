import { createApp } from 'vue'
import { createPinia } from 'pinia'
import Antd from 'ant-design-vue'
import * as Icons from '@ant-design/icons-vue'
import App from './App.vue'
import router from './router'
import { useThemeStore } from './stores/theme'

// Ant Design Vue 样式
import 'ant-design-vue/dist/reset.css'

// 自定义样式
import './styles/index.scss'

// 进度条
import NProgress from 'nprogress'
import 'nprogress/nprogress.css'

// 创建应用实例
const app = createApp(App)

// 创建 Pinia 实例
const pinia = createPinia()
app.use(pinia)

// 使用路由
app.use(router)

// 使用 Ant Design Vue
app.use(Antd)

// 注册所有图标
Object.keys(Icons).forEach(key => {
  app.component(key, Icons[key])
})

// 配置 NProgress
NProgress.configure({
  showSpinner: false,
  trickleSpeed: 200,
  minimum: 0.3
})

// 路由守卫
router.beforeEach((to, from, next) => {
  NProgress.start()
  
  // 设置页面标题
  if (to.meta?.title) {
    document.title = `${to.meta.title} - 用户反馈分析系统`
  } else {
    document.title = '用户反馈分析系统'
  }
  
  next()
})

router.afterEach(() => {
  NProgress.done()
})

// 初始化主题
const themeStore = useThemeStore()
themeStore.initTheme()

// 挂载应用
app.mount('#app') 