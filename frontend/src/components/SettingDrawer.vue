<template>
  <a-drawer
    title="系统设置"
    placement="right"
    :width="320"
    :visible="visible"
    @close="handleClose"
    :body-style="{ padding: '16px' }"
  >
    <div class="setting-drawer">
      <!-- 主题设置 -->
      <a-divider orientation="left">
        <template #orientationMargin>
          <BgColorsOutlined />
          <span style="margin-left: 8px;">主题设置</span>
        </template>
      </a-divider>

      <!-- 主题模式 -->
      <div class="setting-item">
        <div class="setting-item-title">主题模式</div>
        <div class="setting-item-control">
          <a-segmented
            v-model:value="themeStore.mode"
            :options="[
              { label: '亮色', value: 'light', icon: h(SunOutlined) },
              { label: '暗色', value: 'dark', icon: h(MoonOutlined) }
            ]"
            @change="themeStore.setTheme"
          />
        </div>
      </div>

      <!-- 主题色 -->
      <div class="setting-item">
        <div class="setting-item-title">主题色</div>
        <div class="setting-item-control">
          <div class="theme-color-picker">
            <div 
              v-for="color in presetColors" 
              :key="color"
              class="color-block"
              :class="{ active: themeStore.primaryColor === color }"
              :style="{ backgroundColor: color }"
              @click="themeStore.setPrimaryColor(color)"
            />
            <a-color-picker
              v-model:value="themeStore.primaryColor"
              @change="themeStore.setPrimaryColor"
              size="small"
            />
          </div>
        </div>
      </div>

      <!-- 侧边栏主题 -->
      <div class="setting-item">
        <div class="setting-item-title">侧边栏主题</div>
        <div class="setting-item-control">
          <a-segmented
            v-model:value="themeStore.sidebarTheme"
            :options="[
              { label: '亮色', value: 'light' },
              { label: '暗色', value: 'dark' }
            ]"
            @change="themeStore.setSidebarTheme"
          />
        </div>
      </div>

      <!-- 布局设置 -->
      <a-divider orientation="left">
        <template #orientationMargin>
          <LayoutOutlined />
          <span style="margin-left: 8px;">布局设置</span>
        </template>
      </a-divider>

      <!-- 布局模式 -->
      <div class="setting-item">
        <div class="setting-item-title">导航模式</div>
        <div class="setting-item-control">
          <div class="layout-picker">
            <div 
              v-for="layout in layoutOptions"
              :key="layout.value"
              class="layout-item"
              :class="{ active: themeStore.layout === layout.value }"
              @click="themeStore.setLayout(layout.value)"
            >
              <div class="layout-preview">
                <div 
                  v-for="block in layout.preview" 
                  :key="block.name"
                  :class="['layout-block', block.name]"
                />
              </div>
              <div class="layout-name">{{ layout.label }}</div>
            </div>
          </div>
        </div>
      </div>

      <!-- 内容区域宽度 -->
      <div class="setting-item">
        <div class="setting-item-title">内容区域</div>
        <div class="setting-item-control">
          <a-segmented
            v-model:value="themeStore.contentWidth"
            :options="[
              { label: '流式', value: 'fluid' },
              { label: '定宽', value: 'fixed' }
            ]"
            @change="themeStore.setContentWidth"
          />
        </div>
      </div>

      <!-- 功能设置 -->
      <a-divider orientation="left">
        <template #orientationMargin>
          <ControlOutlined />
          <span style="margin-left: 8px;">功能设置</span>
        </template>
      </a-divider>

      <!-- 固定设置 -->
      <div class="setting-item">
        <div class="setting-item-title">
          固定Header
          <a-tooltip title="固定顶部导航栏">
            <QuestionCircleOutlined style="margin-left: 4px; color: #999;" />
          </a-tooltip>
        </div>
        <div class="setting-item-control">
          <a-switch 
            v-model:checked="themeStore.fixedHeader"
            @change="themeStore.toggleFixedHeader"
          />
        </div>
      </div>

      <div class="setting-item">
        <div class="setting-item-title">
          固定侧边栏
          <a-tooltip title="固定左侧导航菜单">
            <QuestionCircleOutlined style="margin-left: 4px; color: #999;" />
          </a-tooltip>
        </div>
        <div class="setting-item-control">
          <a-switch 
            v-model:checked="themeStore.fixedSidebar"
            @change="themeStore.toggleFixedSidebar"
          />
        </div>
      </div>

      <!-- 界面设置 -->
      <div class="setting-item">
        <div class="setting-item-title">
          显示面包屑
          <a-tooltip title="显示页面路径导航">
            <QuestionCircleOutlined style="margin-left: 4px; color: #999;" />
          </a-tooltip>
        </div>
        <div class="setting-item-control">
          <a-switch 
            v-model:checked="themeStore.showBreadcrumb"
            @change="themeStore.toggleBreadcrumb"
          />
        </div>
      </div>

      <div class="setting-item">
        <div class="setting-item-title">
          显示标签页
          <a-tooltip title="显示多页面标签切换">
            <QuestionCircleOutlined style="margin-left: 4px; color: #999;" />
          </a-tooltip>
        </div>
        <div class="setting-item-control">
          <a-switch 
            v-model:checked="themeStore.showTags"
            @change="themeStore.toggleTags"
          />
        </div>
      </div>

      <div class="setting-item">
        <div class="setting-item-title">
          多标签页模式
          <a-tooltip title="启用多标签页缓存">
            <QuestionCircleOutlined style="margin-left: 4px; color: #999;" />
          </a-tooltip>
        </div>
        <div class="setting-item-control">
          <a-switch 
            v-model:checked="themeStore.multiTab"
            @change="themeStore.toggleMultiTab"
          />
        </div>
      </div>

      <!-- 辅助功能 -->
      <a-divider orientation="left">
        <template #orientationMargin>
          <EyeOutlined />
          <span style="margin-left: 8px;">辅助功能</span>
        </template>
      </a-divider>

      <div class="setting-item">
        <div class="setting-item-title">
          色弱模式
          <a-tooltip title="开启色彩辅助模式">
            <QuestionCircleOutlined style="margin-left: 4px; color: #999;" />
          </a-tooltip>
        </div>
        <div class="setting-item-control">
          <a-switch 
            v-model:checked="themeStore.colorWeak"
            @change="themeStore.toggleColorWeak"
          />
        </div>
      </div>

      <!-- 操作按钮 -->
      <a-divider />
      <div class="setting-actions">
        <a-space direction="vertical" style="width: 100%;">
          <a-button 
            type="primary" 
            block 
            @click="copySettings"
          >
            <CopyOutlined />
            复制设置
          </a-button>
          <a-button 
            block 
            @click="resetSettings"
          >
            <ReloadOutlined />
            重置设置
          </a-button>
        </a-space>
      </div>

      <!-- 预设主题 -->
      <a-divider orientation="left">
        <template #orientationMargin>
          <HighlightOutlined />
          <span style="margin-left: 8px;">预设主题</span>
        </template>
      </a-divider>

      <div class="preset-themes">
        <div 
          v-for="preset in presetThemes"
          :key="preset.name"
          class="preset-theme-item"
          @click="applyPreset(preset)"
        >
          <div class="preset-preview">
            <div class="preset-header" :style="{ backgroundColor: preset.colors.header }" />
            <div class="preset-sidebar" :style="{ backgroundColor: preset.colors.sidebar }" />
            <div class="preset-content" :style="{ backgroundColor: preset.colors.content }" />
          </div>
          <div class="preset-name">{{ preset.name }}</div>
        </div>
      </div>
    </div>
  </a-drawer>
</template>

<script setup>
import { h } from 'vue'
import { message } from 'ant-design-vue'
import { useThemeStore } from '../stores/theme'
import {
  BgColorsOutlined,
  LayoutOutlined,
  ControlOutlined,
  EyeOutlined,
  SunOutlined,
  MoonOutlined,
  QuestionCircleOutlined,
  CopyOutlined,
  ReloadOutlined,
  HighlightOutlined
} from '@ant-design/icons-vue'

// Props & Emits
const props = defineProps({
  visible: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['update:visible'])

const themeStore = useThemeStore()

// 预设颜色
const presetColors = [
  '#1890ff', // 拂晓蓝
  '#722ed1', // 酱紫
  '#13c2c2', // 明青
  '#52c41a', // 极光绿
  '#fa8c16', // 日暮黄
  '#f5222d', // 薄暮红
  '#eb2f96', // 法式洋红
  '#faad14'  // 金盏花
]

// 布局选项
const layoutOptions = [
  {
    value: 'side',
    label: '侧边菜单',
    preview: [
      { name: 'sidebar' },
      { name: 'header' },
      { name: 'content' }
    ]
  },
  {
    value: 'top',
    label: '顶部菜单',
    preview: [
      { name: 'header-full' },
      { name: 'content-full' }
    ]
  },
  {
    value: 'mix',
    label: '混合菜单',
    preview: [
      { name: 'sidebar-mini' },
      { name: 'header' },
      { name: 'content' }
    ]
  }
]

// 预设主题
const presetThemes = [
  {
    name: '默认主题',
    colors: {
      header: '#ffffff',
      sidebar: '#001529',
      content: '#f0f2f5'
    },
    config: {
      mode: 'light',
      primaryColor: '#1890ff',
      sidebarTheme: 'dark'
    }
  },
  {
    name: '暗夜主题',
    colors: {
      header: '#141414',
      sidebar: '#000000',
      content: '#1f1f1f'
    },
    config: {
      mode: 'dark',
      primaryColor: '#1890ff',
      sidebarTheme: 'dark'
    }
  },
  {
    name: '科技蓝',
    colors: {
      header: '#ffffff',
      sidebar: '#001529',
      content: '#f0f2f5'
    },
    config: {
      mode: 'light',
      primaryColor: '#722ed1',
      sidebarTheme: 'dark'
    }
  },
  {
    name: '清新绿',
    colors: {
      header: '#ffffff',
      sidebar: '#ffffff',
      content: '#f0f2f5'
    },
    config: {
      mode: 'light',
      primaryColor: '#52c41a',
      sidebarTheme: 'light'
    }
  }
]

// 方法
const handleClose = () => {
  emit('update:visible', false)
}

const copySettings = () => {
  const settings = {
    mode: themeStore.mode,
    primaryColor: themeStore.primaryColor,
    sidebarTheme: themeStore.sidebarTheme,
    layout: themeStore.layout,
    fixedHeader: themeStore.fixedHeader,
    fixedSidebar: themeStore.fixedSidebar,
    showBreadcrumb: themeStore.showBreadcrumb,
    showTags: themeStore.showTags,
    multiTab: themeStore.multiTab,
    contentWidth: themeStore.contentWidth,
    colorWeak: themeStore.colorWeak
  }
  
  navigator.clipboard.writeText(JSON.stringify(settings, null, 2)).then(() => {
    message.success('设置已复制到剪贴板')
  }).catch(() => {
    message.error('复制失败，请手动复制')
  })
}

const resetSettings = () => {
  themeStore.resetConfig()
  message.success('设置已重置')
}

const applyPreset = (preset) => {
  Object.keys(preset.config).forEach(key => {
    if (key === 'mode') {
      themeStore.setTheme(preset.config[key])
    } else if (key === 'primaryColor') {
      themeStore.setPrimaryColor(preset.config[key])
    } else if (key === 'sidebarTheme') {
      themeStore.setSidebarTheme(preset.config[key])
    }
  })
  message.success(`已应用 ${preset.name}`)
}
</script>

<style lang="scss" scoped>
.setting-drawer {
  .setting-item {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 16px;
    
    .setting-item-title {
      font-size: 14px;
      display: flex;
      align-items: center;
    }
    
    .setting-item-control {
      min-width: 120px;
      text-align: right;
    }
  }
  
  .theme-color-picker {
    display: flex;
    align-items: center;
    gap: 8px;
    flex-wrap: wrap;
    
    .color-block {
      width: 20px;
      height: 20px;
      border-radius: 4px;
      cursor: pointer;
      border: 2px solid transparent;
      transition: all 0.2s;
      
      &:hover {
        transform: scale(1.1);
      }
      
      &.active {
        border-color: #fff;
        box-shadow: 0 0 0 1px #1890ff;
      }
    }
  }
  
  .layout-picker {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 8px;
    margin-top: 8px;
    
    .layout-item {
      cursor: pointer;
      border: 2px solid #d9d9d9;
      border-radius: 4px;
      padding: 4px;
      transition: all 0.2s;
      
      &:hover {
        border-color: #1890ff;
      }
      
      &.active {
        border-color: #1890ff;
        background-color: #e6f7ff;
      }
      
      .layout-preview {
        width: 48px;
        height: 36px;
        position: relative;
        background: #f0f0f0;
        border-radius: 2px;
        overflow: hidden;
        
        .layout-block {
          position: absolute;
          
          &.sidebar {
            width: 30%;
            height: 100%;
            left: 0;
            top: 0;
            background: #001529;
          }
          
          &.header {
            width: 70%;
            height: 25%;
            right: 0;
            top: 0;
            background: #fff;
            border: 1px solid #d9d9d9;
          }
          
          &.content {
            width: 70%;
            height: 75%;
            right: 0;
            bottom: 0;
            background: #fafafa;
          }
          
          &.header-full {
            width: 100%;
            height: 25%;
            top: 0;
            background: #fff;
            border-bottom: 1px solid #d9d9d9;
          }
          
          &.content-full {
            width: 100%;
            height: 75%;
            bottom: 0;
            background: #fafafa;
          }
          
          &.sidebar-mini {
            width: 15%;
            height: 100%;
            left: 0;
            top: 0;
            background: #001529;
          }
        }
      }
      
      .layout-name {
        font-size: 12px;
        text-align: center;
        margin-top: 4px;
        color: #666;
      }
    }
  }
  
  .setting-actions {
    margin: 16px 0;
  }
  
  .preset-themes {
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: 12px;
    
    .preset-theme-item {
      cursor: pointer;
      border: 1px solid #d9d9d9;
      border-radius: 6px;
      padding: 8px;
      transition: all 0.2s;
      
      &:hover {
        border-color: #1890ff;
        box-shadow: 0 2px 4px rgba(24, 144, 255, 0.2);
      }
      
      .preset-preview {
        width: 100%;
        height: 48px;
        position: relative;
        border-radius: 4px;
        overflow: hidden;
        
        .preset-header {
          height: 12px;
          width: 100%;
        }
        
        .preset-sidebar {
          width: 30%;
          height: 36px;
          position: absolute;
          left: 0;
          bottom: 0;
        }
        
        .preset-content {
          width: 70%;
          height: 36px;
          position: absolute;
          right: 0;
          bottom: 0;
        }
      }
      
      .preset-name {
        font-size: 12px;
        text-align: center;
        margin-top: 8px;
        color: #666;
        font-weight: 500;
      }
    }
  }
}
</style> 