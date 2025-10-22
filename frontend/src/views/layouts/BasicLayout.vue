<template>
  <a-layout style="min-height: 100vh">
    <a-layout-sider v-model="collapsed" :trigger="null" collapsible>
      <div class="logo" />
      <a-menu
        theme="dark"
        mode="inline"
        v-model="selectedKeys"
        :open-keys="openKeys"
        @click="handleMenuClick"
      >
        <a-menu-item key="dashboard">
          <DashboardOutlined />
          <span>仪表板</span>
        </a-menu-item>
        <a-menu-item key="feedback">
          <MessageOutlined />
          <span>反馈管理</span>
        </a-menu-item>
        <a-menu-item key="analysis">
          <BarChartOutlined />
          <span>分析引擎</span>
        </a-menu-item>
        <a-menu-item key="insights">
          <BulbOutlined />
          <span>智能洞察</span>
        </a-menu-item>
        <a-menu-item key="decision-engine">
          <BranchesOutlined />
          <span>决策引擎</span>
        </a-menu-item>
        <a-menu-item key="spider">
          <BugOutlined />
          <span>爬虫管理</span>
        </a-menu-item>
        <a-menu-item key="issues">
          <ExclamationCircleOutlined />
          <span>问题管理</span>
        </a-menu-item>
        <a-menu-item key="reports">
          <FileTextOutlined />
          <span>报告中心</span>
        </a-menu-item>
        <a-menu-item key="settings">
          <SettingOutlined />
          <span>系统设置</span>
        </a-menu-item>
      </a-menu>
    </a-layout-sider>
    <a-layout>
      <a-layout-header style="background: #fff; padding: 0">
        <MenuUnfoldOutlined
          v-if="collapsed"
          class="trigger"
          @click="() => (collapsed = !collapsed)"
        />
        <MenuFoldOutlined
          v-else
          class="trigger"
          @click="() => (collapsed = !collapsed)"
        />
      </a-layout-header>
      <a-layout-content style="margin: 24px 16px; padding: 24px; background: #fff; min-height: 280px">
        <router-view />
      </a-layout-content>
    </a-layout>
  </a-layout>
</template>

<script>
import { ref, computed, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import {
  MenuUnfoldOutlined,
  MenuFoldOutlined,
  DashboardOutlined,
  MessageOutlined,
  BarChartOutlined,
  BranchesOutlined,
  BugOutlined,
  ExclamationCircleOutlined,
  FileTextOutlined,
  SettingOutlined,
  BulbOutlined,
} from '@ant-design/icons-vue'

export default {
  name: 'BasicLayout',
  components: {
    MenuUnfoldOutlined,
    MenuFoldOutlined,
    DashboardOutlined,
    MessageOutlined,
    BarChartOutlined,
    BranchesOutlined,
    BugOutlined,
    ExclamationCircleOutlined,
    FileTextOutlined,
    SettingOutlined,
    BulbOutlined,
  },
  setup() {
    const router = useRouter()
    const route = useRoute()
    
    const collapsed = ref(false)
    const openKeys = ref(['sub1'])

    // 菜单路由映射
    const menuRouteMap = {
      dashboard: '/dashboard',
      feedback: '/feedback',
      analysis: '/analysis',
      insights: '/insights',
      'decision-engine': '/decision-engine',
      spider: '/spider',
      issues: '/issues',
      reports: '/reports',
      settings: '/settings'
    }

    // 路由菜单映射（反向）
    const routeMenuMap = Object.fromEntries(
      Object.entries(menuRouteMap).map(([key, value]) => [value, key])
    )

    // 根据当前路由计算选中的菜单
    const selectedKeys = computed(() => {
      const currentPath = route.path
      const menuKey = routeMenuMap[currentPath]
      return menuKey ? [menuKey] : ['dashboard']
    })

    // 处理菜单点击
    const handleMenuClick = ({ key }) => {
      const targetRoute = menuRouteMap[key]
      if (targetRoute && targetRoute !== route.path) {
        router.push(targetRoute)
      }
    }

    return {
      collapsed,
      selectedKeys,
      openKeys,
      handleMenuClick,
    }
  },
}
</script>

<style scoped>
.trigger {
  font-size: 18px;
  line-height: 64px;
  padding: 0 24px;
  cursor: pointer;
  transition: color 0.3s;
}

.trigger:hover {
  color: #1890ff;
}

.logo {
  height: 32px;
  background: rgba(255, 255, 255, 0.3);
  margin: 16px;
}
</style> 