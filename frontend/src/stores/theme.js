import { defineStore } from 'pinia'
import { theme } from 'ant-design-vue'

export const useThemeStore = defineStore('theme', {
  state: () => ({
    // 主题模式：'light' | 'dark'
    mode: 'light',
    // 主题色
    primaryColor: '#1890ff',
    // 侧边栏主题：'light' | 'dark'
    sidebarTheme: 'dark',
    // 布局模式：'side' | 'top' | 'mix'
    layout: 'side',
    // 是否固定头部
    fixedHeader: true,
    // 是否固定侧边栏
    fixedSidebar: true,
    // 是否显示面包屑
    showBreadcrumb: true,
    // 是否显示标签页
    showTags: true,
    // 是否开启多标签页
    multiTab: true,
    // 内容区域宽度
    contentWidth: 'fluid', // 'fluid' | 'fixed'
    // 色弱模式
    colorWeak: false
  }),

  getters: {
    // 当前主题配置
    themeConfig: (state) => {
      return {
        algorithm: state.mode === 'dark' ? theme.darkAlgorithm : theme.defaultAlgorithm,
        token: {
          colorPrimary: state.primaryColor,
          borderRadius: 6,
          wireframe: false
        },
        components: {
          Layout: {
            siderBg: state.sidebarTheme === 'dark' ? '#001529' : '#ffffff',
            headerBg: state.mode === 'dark' ? '#141414' : '#ffffff'
          },
          Menu: {
            darkItemBg: '#001529',
            darkSubMenuItemBg: '#000c17',
            darkItemSelectedBg: state.primaryColor
          }
        }
      }
    },

    // 是否为暗黑模式
    isDarkMode: (state) => state.mode === 'dark',

    // 布局配置
    layoutConfig: (state) => ({
      layout: state.layout,
      fixedHeader: state.fixedHeader,
      fixedSidebar: state.fixedSidebar,
      showBreadcrumb: state.showBreadcrumb,
      showTags: state.showTags,
      multiTab: state.multiTab,
      contentWidth: state.contentWidth
    })
  },

  actions: {
    // 切换主题模式
    toggleTheme() {
      this.mode = this.mode === 'light' ? 'dark' : 'light'
      this.applyTheme()
      this.saveToStorage()
    },

    // 设置主题模式
    setTheme(mode) {
      this.mode = mode
      this.applyTheme()
      this.saveToStorage()
    },

    // 设置主题色
    setPrimaryColor(color) {
      this.primaryColor = color
      this.applyTheme()
      this.saveToStorage()
    },

    // 设置侧边栏主题
    setSidebarTheme(theme) {
      this.sidebarTheme = theme
      this.saveToStorage()
    },

    // 设置布局模式
    setLayout(layout) {
      this.layout = layout
      this.saveToStorage()
    },

    // 切换固定头部
    toggleFixedHeader() {
      this.fixedHeader = !this.fixedHeader
      this.saveToStorage()
    },

    // 切换固定侧边栏
    toggleFixedSidebar() {
      this.fixedSidebar = !this.fixedSidebar
      this.saveToStorage()
    },

    // 切换面包屑显示
    toggleBreadcrumb() {
      this.showBreadcrumb = !this.showBreadcrumb
      this.saveToStorage()
    },

    // 切换标签页显示
    toggleTags() {
      this.showTags = !this.showTags
      this.saveToStorage()
    },

    // 切换多标签页
    toggleMultiTab() {
      this.multiTab = !this.multiTab
      this.saveToStorage()
    },

    // 设置内容宽度
    setContentWidth(width) {
      this.contentWidth = width
      this.saveToStorage()
    },

    // 切换色弱模式
    toggleColorWeak() {
      this.colorWeak = !this.colorWeak
      this.applyColorWeak()
      this.saveToStorage()
    },

    // 应用主题到DOM
    applyTheme() {
      const root = document.documentElement
      root.setAttribute('data-theme', this.mode)
      
      // 设置CSS变量
      root.style.setProperty('--primary-color', this.primaryColor)
      
      // 更新meta theme-color
      const metaThemeColor = document.querySelector('meta[name="theme-color"]')
      if (metaThemeColor) {
        metaThemeColor.setAttribute('content', this.mode === 'dark' ? '#141414' : '#ffffff')
      }
    },

    // 应用色弱模式
    applyColorWeak() {
      const root = document.documentElement
      if (this.colorWeak) {
        root.classList.add('color-weak')
      } else {
        root.classList.remove('color-weak')
      }
    },

    // 保存配置到本地存储
    saveToStorage() {
      const config = {
        mode: this.mode,
        primaryColor: this.primaryColor,
        sidebarTheme: this.sidebarTheme,
        layout: this.layout,
        fixedHeader: this.fixedHeader,
        fixedSidebar: this.fixedSidebar,
        showBreadcrumb: this.showBreadcrumb,
        showTags: this.showTags,
        multiTab: this.multiTab,
        contentWidth: this.contentWidth,
        colorWeak: this.colorWeak
      }
      localStorage.setItem('theme-config', JSON.stringify(config))
    },

    // 从本地存储加载配置
    loadFromStorage() {
      try {
        const stored = localStorage.getItem('theme-config')
        if (stored) {
          const config = JSON.parse(stored)
          Object.assign(this, config)
        }
      } catch (error) {
        console.warn('Failed to load theme config from localStorage:', error)
      }
    },

    // 初始化主题
    initTheme() {
      // 首先从本地存储加载配置
      this.loadFromStorage()
      
      // 检测系统主题偏好
      if (!localStorage.getItem('theme-config')) {
        const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches
        this.mode = prefersDark ? 'dark' : 'light'
      }
      
      // 应用主题
      this.applyTheme()
      this.applyColorWeak()
      
      // 监听系统主题变化
      window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', (e) => {
        if (!localStorage.getItem('theme-config')) {
          this.mode = e.matches ? 'dark' : 'light'
          this.applyTheme()
        }
      })
    },

    // 重置所有配置
    resetConfig() {
      this.$reset()
      localStorage.removeItem('theme-config')
      this.initTheme()
    }
  }
}) 