<template>
  <a-config-provider 
    :theme="themeStore.themeConfig"
    :locale="zhCN"
  >
    <div id="app" :class="appClass">
      <a-layout class="app-layout">
        <!-- 移动端遮罩 -->
        <div 
          v-show="!collapsed && isMobile" 
          class="mobile-mask"
          @click="collapsed = true"
        ></div>
        
        <!-- 侧边栏 -->
        <a-layout-sider
          v-model:collapsed="collapsed"
          :theme="themeStore.sidebarTheme"
          :trigger="null"
          collapsible
          :width="256"
          :collapsed-width="80"
          class="app-sider"
          :class="{ 'fixed-sider': themeStore.fixedSidebar }"
        >
          <!-- Logo -->
          <div class="logo-wrapper">
            <div class="logo">
              <img src="@/static/images/logo.png" alt="言值" v-if="!collapsed">
              <img src="@/static/images/logo.png" alt="言值" v-else class="logo-mini">
              <h1 v-if="!collapsed" class="logo-title">言值</h1>
            </div>
          </div>

          <!-- 导航菜单 -->
          <a-menu
            v-model:selectedKeys="selectedKeys"
            v-model:openKeys="openKeys"
            :theme="themeStore.sidebarTheme"
            mode="inline"
            :inline-collapsed="collapsed"
            class="app-menu"
            @click="handleMenuClick"
          >
            <a-menu-item key="dashboard">
              <template #icon>
                <DashboardOutlined />
              </template>
              <span>仪表板</span>
            </a-menu-item>

            <a-sub-menu key="feedback">
              <template #icon>
                <MessageOutlined />
              </template>
              <template #title>反馈管理</template>
              <a-menu-item key="feedback-list">反馈列表</a-menu-item>
              <a-menu-item key="feedback-import">批量导入</a-menu-item>
            </a-sub-menu>

            <a-sub-menu key="analysis">
              <template #icon>
                <BarChartOutlined />
              </template>
              <template #title>智能分析</template>
              <a-menu-item key="analysis-engine">分析引擎</a-menu-item>
              <a-menu-item key="analysis-reports">分析报告</a-menu-item>
              <a-menu-item key="insights">智能洞察</a-menu-item>
            </a-sub-menu>

            <a-menu-item key="decision-engine">
              <template #icon>
                <BranchesOutlined />
              </template>
              <span>决策引擎</span>
            </a-menu-item>

            <a-menu-item key="spider">
              <template #icon>
                <BugOutlined />
              </template>
              <span>爬虫管理</span>
            </a-menu-item>

            <a-menu-item key="issues">
              <template #icon>
                <ExclamationCircleOutlined />
              </template>
              <span>问题管理</span>
            </a-menu-item>

            <a-menu-item key="reports">
              <template #icon>
                <FileTextOutlined />
              </template>
              <span>报告中心</span>
            </a-menu-item>

            <a-menu-item key="settings">
              <template #icon>
                <SettingOutlined />
              </template>
              <span>系统设置</span>
            </a-menu-item>
          </a-menu>
        </a-layout-sider>

        <!-- 主内容区域 -->
        <a-layout class="app-main" :class="{ 'collapsed-main': collapsed }">
          <!-- 头部 -->
          <a-layout-header 
            class="app-header"
            :class="{ 'fixed-header': themeStore.fixedHeader }"
          >
            <div class="header-left">
              <!-- 折叠触发器 -->
              <a-button
                type="text"
                class="trigger"
                @click="collapsed = !collapsed"
              >
                <template #icon>
                  <MenuUnfoldOutlined v-if="collapsed" />
                  <MenuFoldOutlined v-else />
                </template>
              </a-button>

              <!-- 面包屑 -->
              <a-breadcrumb v-if="themeStore.showBreadcrumb" class="breadcrumb">
                <a-breadcrumb-item>
                  <HomeOutlined />
                  <span>首页</span>
                </a-breadcrumb-item>
                <a-breadcrumb-item v-for="item in breadcrumbList" :key="item.path">
                  {{ item.title }}
                </a-breadcrumb-item>
              </a-breadcrumb>
            </div>

            <div class="header-right">
              <!-- 全屏切换 -->
              <a-tooltip title="全屏">
                <a-button 
                  type="text" 
                  class="header-action"
                  @click="toggleFullscreen"
                >
                  <template #icon>
                    <FullscreenOutlined v-if="!isFullscreen" />
                    <FullscreenExitOutlined v-else />
                  </template>
                </a-button>
              </a-tooltip>

              <!-- 主题切换 -->
              <a-tooltip :title="themeStore.isDarkMode ? '切换到亮色主题' : '切换到暗色主题'">
                <a-button 
                  type="text" 
                  class="header-action"
                  @click="themeStore.toggleTheme()"
                >
                  <template #icon>
                    <SunFilled v-if="themeStore.isDarkMode" />
                    <MoonFilled v-else />
                  </template>
                </a-button>
              </a-tooltip>

              <!-- 设置 -->
              <a-tooltip title="系统设置">
                <a-button 
                  type="text" 
                  class="header-action"
                  @click="showSettingDrawer = true"
                >
                  <template #icon>
                    <SettingOutlined />
                  </template>
                </a-button>
              </a-tooltip>

              <!-- 用户信息 -->
              <a-dropdown>
                <a-button type="text" class="user-info">
                  <a-avatar size="small" src="/avatar.png">
                    <template #icon>
                      <UserOutlined />
                    </template>
                  </a-avatar>
                  <span class="user-name">管理员</span>
                  <DownOutlined class="user-arrow" />
                </a-button>
                <template #overlay>
                  <a-menu>
                    <a-menu-item key="profile">
                      <UserOutlined />
                      个人中心
                    </a-menu-item>
                    <a-menu-item key="logout">
                      <LogoutOutlined />
                      退出登录
                    </a-menu-item>
                  </a-menu>
                </template>
              </a-dropdown>
            </div>
          </a-layout-header>

          <!-- 标签页 -->
          <div 
            v-if="themeStore.showTags" 
            class="app-tabs"
            :class="{ 'fixed-tabs': themeStore.fixedHeader }"
          >
            <a-tabs
              v-model:activeKey="activeTab"
              type="editable-card"
              :hide-add="true"
              @edit="onTabEdit"
              @change="onTabChange"
            >
              <a-tab-pane
                v-for="tab in tabs"
                :key="tab.key"
                :tab="tab.title"
                :closable="tab.closable"
              />
            </a-tabs>
          </div>

          <!-- 内容区域 -->
          <a-layout-content 
            class="app-content"
            :class="{ 
              'fixed-content': themeStore.fixedHeader,
              'tabs-content': themeStore.showTags
            }"
          >
            <div class="content-wrapper" :class="{ 'fixed-width': themeStore.contentWidth === 'fixed' }">
              <router-view v-slot="{ Component }">
                <transition name="fade-slide" mode="out-in">
                  <keep-alive :include="cachedViews">
                    <component :is="Component" />
                  </keep-alive>
                </transition>
              </router-view>
            </div>
          </a-layout-content>

          <!-- 页脚 -->
          <a-layout-footer :class="footerClass">
            <div class="footer-content">
              <span>© 2025 言值 v0.0.1</span>
              <a-divider type="vertical" />
              <span>让每个字都成为决策神经元</span>
            </div>
          </a-layout-footer>
        </a-layout>
      </a-layout>

      <!-- 设置抽屉 -->
      <SettingDrawer 
        v-model:visible="showSettingDrawer"
        @update:visible="showSettingDrawer = $event"
      />
    </div>
  </a-config-provider>
</template>

<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useThemeStore } from './stores/theme'
import { theme } from 'ant-design-vue'
import zhCN from 'ant-design-vue/es/locale/zh_CN'
import SettingDrawer from './components/SettingDrawer.vue'

// 图标引用
import {
  DashboardOutlined,
  MessageOutlined,
  BarChartOutlined,
  BranchesOutlined,
  BugOutlined,
  ExclamationCircleOutlined,
  FileTextOutlined,
  SettingOutlined,
  MenuUnfoldOutlined,
  MenuFoldOutlined,
  HomeOutlined,
  FullscreenOutlined,
  FullscreenExitOutlined,
  SunFilled,
  MoonFilled,
  UserOutlined,
  DownOutlined,
  LogoutOutlined
} from '@ant-design/icons-vue'

const router = useRouter()
const route = useRoute()
const themeStore = useThemeStore()

// 响应式数据
const collapsed = ref(false)
const selectedKeys = ref(['dashboard'])
const openKeys = ref(['feedback', 'analysis'])
const showSettingDrawer = ref(false)
const isFullscreen = ref(false)
const activeTab = ref('dashboard')
const isMobile = ref(false)

// 标签页管理
const tabs = ref([
  { key: 'dashboard', title: '仪表板', closable: false }
])

// 缓存的视图
const cachedViews = ref(['Dashboard'])

// 计算属性
const appClass = computed(() => ({
  'app-dark': themeStore.isDarkMode,
  'app-light': !themeStore.isDarkMode,
  'color-weak': themeStore.colorWeak,
  'fixed-sidebar': themeStore.fixedSidebar,
  'fixed-header': themeStore.fixedHeader
}))

// Footer样式计算属性，与侧边栏主题保持一致
const footerClass = computed(() => ({
  'app-footer': true,
  'footer-dark': themeStore.sidebarTheme === 'dark',
  'footer-light': themeStore.sidebarTheme === 'light'
}))

// 面包屑
const breadcrumbList = computed(() => {
  const matched = route.matched.filter(item => item.meta?.title)
  return matched.map(item => ({
    path: item.path,
    title: item.meta.title
  }))
})

// 方法
const handleMenuClick = ({ key }) => {
  selectedKeys.value = [key]
  
  // 路由映射
  const routeMap = {
    'dashboard': '/dashboard',
    'feedback-list': '/feedback',
    'feedback-import': '/feedback/import',
    'analysis-engine': '/analysis',
    'analysis-reports': '/analysis/reports',
    'insights': '/insights',
    'decision-engine': '/decision-engine',
    'spider': '/spider',
    'issues': '/issues',
    'reports': '/reports',
    'settings': '/settings'
  }
  
  const path = routeMap[key]
  if (path && path !== route.path) {
    router.push(path)
    
    // 添加标签页
    if (themeStore.showTags && themeStore.multiTab) {
      addTab(key, getTabTitle(key))
    }
  }
}

const getTabTitle = (key) => {
  const titleMap = {
    'dashboard': '仪表板',
    'feedback-list': '反馈列表',
    'feedback-import': '批量导入',
    'analysis-engine': '分析引擎',
    'analysis-reports': '分析报告',
    'insights': '智能洞察',
    'decision-engine': '决策引擎',
    'spider': '爬虫管理',
    'issues': '问题管理',
    'reports': '报告中心',
    'settings': '系统设置'
  }
  return titleMap[key] || '未知页面'
}

const addTab = (key, title) => {
  const existingTab = tabs.value.find(tab => tab.key === key)
  if (!existingTab) {
    tabs.value.push({
      key,
      title,
      closable: key !== 'dashboard'
    })
  }
  activeTab.value = key
}

const onTabEdit = (targetKey, action) => {
  if (action === 'remove') {
    removeTab(targetKey)
  }
}

const removeTab = (targetKey) => {
  const targetIndex = tabs.value.findIndex(tab => tab.key === targetKey)
  if (targetIndex > -1) {
    tabs.value.splice(targetIndex, 1)
    
    // 如果删除的是当前活跃标签，切换到其他标签
    if (targetKey === activeTab.value) {
      const newActiveTab = tabs.value[targetIndex] || tabs.value[targetIndex - 1]
      if (newActiveTab) {
        activeTab.value = newActiveTab.key
        handleMenuClick({ key: newActiveTab.key })
      }
    }
  }
}

const onTabChange = (key) => {
  activeTab.value = key
  handleMenuClick({ key })
}

const toggleFullscreen = () => {
  if (!document.fullscreenElement) {
    document.documentElement.requestFullscreen()
    isFullscreen.value = true
  } else {
    document.exitFullscreen()
    isFullscreen.value = false
  }
}

// 监听路由变化
watch(route, (newRoute) => {
  // 更新面包屑和选中状态
  if (newRoute.meta?.menuKey) {
    selectedKeys.value = [newRoute.meta.menuKey]
  }
}, { immediate: true })

// 检测移动端
const checkMobile = () => {
  isMobile.value = window.innerWidth <= 768
  if (isMobile.value) {
    collapsed.value = true
  }
}

// 监听全屏变化和窗口大小变化
onMounted(() => {
  document.addEventListener('fullscreenchange', () => {
    isFullscreen.value = !!document.fullscreenElement
  })
  
  // 检测移动端
  checkMobile()
  window.addEventListener('resize', checkMobile)
})
</script>

<style lang="scss" scoped>
.app-layout {
  min-height: 100vh;
}

.app-sider {
  box-shadow: 2px 0 8px rgba(0, 0, 0, 0.15);
  z-index: 100;
  
  &.fixed-sider {
    position: fixed;
    left: 0;
    top: 0;
    bottom: 0;
  }
}

.logo-wrapper {
  height: 64px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
  padding: 0 16px;
  
  .logo {
    display: flex;
    align-items: center;
    
    img {
      height: 32px;
      width: 32px;
      border-radius: 6px;
      object-fit: contain;
      transition: all 0.3s;
      
      &.logo-mini {
        height: 28px;
        width: 28px;
      }
    }
    
    .logo-title {
      margin: 0 0 0 12px;
      color: white;
      font-size: 16px;
      font-weight: 600;
      white-space: nowrap;
      overflow: hidden;
      transition: all 0.3s;
    }
  }
}

.app-menu {
  border-right: none;
}

.app-main {
  margin-left: var(--sidebar-width);
  transition: margin-left 0.2s;
  
  &.collapsed-main {
    margin-left: var(--sidebar-collapsed-width);
  }
}

.app-header {
  background: white;
  padding: 0 24px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  border-bottom: 1px solid #f0f0f0;
  box-shadow: 0 1px 4px rgba(0, 21, 41, 0.08);
  
  &.fixed-header {
    position: fixed;
    top: 0;
    right: 0;
    left: var(--sidebar-width);
    z-index: 99;
    transition: left 0.2s;
  }
}

.collapsed-main .app-header.fixed-header {
  left: var(--sidebar-collapsed-width);
}

.header-left {
  display: flex;
  align-items: center;
  
  .trigger {
    font-size: 18px;
    margin-right: 24px;
  }
  
  .breadcrumb {
    margin: 0;
  }
}

.header-right {
  display: flex;
  align-items: center;
  gap: 8px;
  
  .header-action {
    font-size: 16px;
  }
  
  .user-info {
    display: flex;
    align-items: center;
    gap: 8px;
    
    .user-name {
      margin: 0 4px 0 8px;
    }
    
    .user-arrow {
      font-size: 12px;
    }
  }
}

.app-tabs {
  background: var(--background-color);
  padding: 0 24px;
  min-height: 48px;
  display: flex;
  align-items: flex-end;
  position: relative;
  
  :deep(.ant-tabs) {
    height: 48px;
    width: 100%;
    
    .ant-tabs-nav {
      margin: 0;
      position: relative;
      height: 100%;
      
      &::before {
        content: '';
        position: absolute;
        bottom: 0;
        left: 0;
        right: 0;
        height: 1px;
        background: var(--border-color-split);
        z-index: 0;
      }
      
      .ant-tabs-nav-wrap {
        height: 100%;
        display: flex;
        align-items: flex-end;
        
        .ant-tabs-nav-list {
          height: 100%;
          display: flex;
          align-items: flex-end;
          
          .ant-tabs-tab {
            padding: 8px 16px;
            margin: 0 4px 0 0;
            background: transparent;
            border: 1px solid transparent;
            border-radius: 6px 6px 0 0;
            transition: all 0.3s;
            height: 36px;
            display: flex;
            align-items: center;
            margin-bottom: 0;
            position: relative;
            
            &:hover {
              background: var(--background-color-light);
              color: var(--primary-color);
            }
            
            &.ant-tabs-tab-active {
              background: var(--background-color);
              border-color: var(--border-color);
              border-bottom: 1px solid var(--background-color);
              color: var(--primary-color);
              font-weight: 500;
              z-index: 2;
              
              &::after {
                content: '';
                position: absolute;
                bottom: -1px;
                left: -1px;
                right: -1px;
                height: 1px;
                background: var(--background-color);
                z-index: 1;
              }
            }
            
            .ant-tabs-tab-btn {
              color: inherit;
            }
            
            .ant-tabs-tab-remove {
              margin-left: 8px;
              color: var(--text-color-secondary);
              
              &:hover {
                color: var(--error-color);
              }
            }
          }
        }
      }
    }
    
    .ant-tabs-content-holder {
      display: none;
    }
  }
  
  &.fixed-tabs {
    position: fixed;
    top: var(--header-height);
    right: 0;
    left: var(--sidebar-width);
    z-index: 98;
    transition: left 0.2s;
  }
}

.collapsed-main .app-tabs.fixed-tabs {
  left: var(--sidebar-collapsed-width);
}

.app-content {
  padding: 0;
  overflow-y: auto;
  position: relative;
  
  &.fixed-content {
    margin-top: var(--header-height);
    height: calc(100vh - var(--header-height) - var(--footer-height));
  }
  
  &.tabs-content {
    margin-top: 48px;
    height: calc(100vh - 48px - var(--footer-height));
  }
  
  &.fixed-content.tabs-content {
    margin-top: calc(var(--header-height) + 48px);
    height: calc(100vh - var(--header-height) - 48px - var(--footer-height));
  }
  
  /* 默认状态（非固定头部，无标签页） */
  &:not(.fixed-content):not(.tabs-content) {
    min-height: calc(100vh - var(--footer-height));
  }
}

.content-wrapper {
  padding: 24px;
  min-height: 100%;
  
  &.fixed-width {
    max-width: 1200px;
    margin: 0 auto;
  }
}

.app-footer {
  text-align: center;
  
  .footer-content {
    font-size: 14px;
  }
  
  // 暗色侧边栏主题时的footer样式
  &.footer-dark {
    background: #001529;
    
    .footer-content {
      color: rgba(255, 255, 255, 0.85);
    }
  }
  
  // 亮色侧边栏主题时的footer样式  
  &.footer-light {
    background: #ffffff;
    border-top: 1px solid #f0f0f0;
    
    .footer-content {
      color: rgba(0, 0, 0, 0.65);
    }
  }
}

// 页面过渡动画
.fade-slide-enter-active,
.fade-slide-leave-active {
  transition: all 0.3s ease;
}

.fade-slide-enter-from {
  opacity: 0;
  transform: translateX(30px);
}

.fade-slide-leave-to {
  opacity: 0;
  transform: translateX(-30px);
}

// 暗黑主题样式
.app-dark {
  .app-header {
    background: var(--background-color);
    border-bottom-color: var(--border-color-split);
  }
  
  .app-tabs {
    background: var(--background-color);
    
    :deep(.ant-tabs) {
      .ant-tabs-nav {
        &::before {
          background: var(--border-color-split);
        }
        
        .ant-tabs-nav-wrap {
          .ant-tabs-nav-list {
            .ant-tabs-tab {
              color: var(--text-color-secondary);
              
              &:hover {
                background: var(--background-color-light);
                color: var(--primary-color);
              }
              
              &.ant-tabs-tab-active {
                background: var(--background-color);
                border-color: var(--border-color);
                border-bottom: 1px solid var(--background-color);
                color: var(--primary-color);
                z-index: 2;
                
                &::after {
                  background: var(--background-color);
                }
              }
            }
          }
        }
      }
    }
  }
  
  .app-footer {
    // 在暗黑模式下，根据侧边栏主题调整footer样式
    &.footer-dark {
      background: #001529; /* 保持和暗色侧边栏一致 */
      
      .footer-content {
        color: rgba(255, 255, 255, 0.65); /* 暗黑模式下调整透明度 */
      }
    }
    
    &.footer-light {
      background: #141414; /* 暗黑模式下的亮色侧边栏使用深色背景 */
      border-top: 1px solid #303030;
      
      .footer-content {
        color: rgba(255, 255, 255, 0.85);
      }
    }
  }
}

// 色弱模式
.color-weak {
  filter: invert(80%);
}

// 移动端遮罩
.mobile-mask {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(0, 0, 0, 0.45);
  z-index: 150;
  transition: opacity 0.3s;
}

// 响应式设计
@media (max-width: 768px) {
  .app-sider {
    position: fixed !important;
    z-index: 200;
    transform: translateX(-100%);
    transition: transform 0.3s;
    
    &:not(.ant-layout-sider-collapsed) {
      transform: translateX(0);
    }
  }
  
  .app-main {
    margin-left: 0 !important;
  }
  
  .app-header {
    padding: 0 16px;
    
    &.fixed-header {
      left: 0 !important;
    }
  }
  
  .app-tabs {
    padding: 0 16px;
    
    &.fixed-tabs {
      left: 0 !important;
    }
  }
  
  .app-content {
    padding: 16px;
  }
  
  .header-left .breadcrumb {
    display: none;
  }
  
  .collapsed-main .app-header.fixed-header,
  .collapsed-main .app-tabs.fixed-tabs {
    left: 0 !important;
  }
}
</style> 