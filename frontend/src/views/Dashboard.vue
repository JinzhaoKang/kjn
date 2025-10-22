<template>
  <div class="dashboard-container">


    <!-- 统计卡片区域 -->
    <div class="stats-section">
      <a-row :gutter="[24, 24]">
        <a-col :xs="24" :sm="12" :lg="6" v-for="stat in statistics" :key="stat.key">
          <div class="stat-card" :class="`stat-${stat.type}`">
            <div class="stat-content">
              <div class="stat-icon">
                <component :is="stat.icon" />
              </div>
              <div class="stat-info">
                <div class="stat-number">{{ stat.value }}</div>
                <div class="stat-label">{{ stat.label }}</div>
              </div>
            </div>
            <div class="stat-trend" :class="stat.trend > 0 ? 'positive' : 'negative'">
              <span class="trend-icon">
                <ArrowUpOutlined v-if="stat.trend > 0" />
                <ArrowDownOutlined v-else />
              </span>
              <span class="trend-value">{{ Math.abs(stat.trend) }}%</span>
              <span class="trend-label">较上月</span>
          </div>
          </div>
        </a-col>
      </a-row>
    </div>
    
    <!-- 热词分析区域 -->
    <div class="hotwords-section">
      <a-card title="热词分析" class="hotwords-card">
        <template #extra>
          <a-space>
            <a-select v-model="hotwordsPeriod" size="small" style="width: 120px" @change="updateHotwords">
              <a-select-option value="today">今日</a-select-option>
              <a-select-option value="week">本周</a-select-option>
              <a-select-option value="month">本月</a-select-option>
            </a-select>
            <a-button type="link" size="small">
              查看更多
            </a-button>
          </a-space>
        </template>
        
        <a-row :gutter="[24, 24]">
          <!-- 正面热词TOP100 -->
          <a-col :xs="24" :sm="8" :lg="6">
            <div class="hotwords-panel">
              <div class="panel-header">
                <h3 class="panel-title">
                  <span class="title-icon positive">
                    <SmileOutlined />
                  </span>
                  TOP100正面热词
                </h3>
              </div>
              <div class="hotwords-list">
                <div 
                  v-for="(word, index) in positiveHotwords" 
                  :key="word.text"
                  class="hotword-item"
                  :class="{ 'top-word': index < 3 }"
                >
                  <div class="word-rank">{{ index + 1 }}</div>
                  <div class="word-content">
                    <div class="word-text">{{ word.text }}</div>
                    <div class="word-bar">
                      <div 
                        class="word-progress positive" 
                        :style="{ width: `${(word.value / positiveHotwords[0].value) * 100}%` }"
                      ></div>
                    </div>
                  </div>
                  <div class="word-count">{{ word.value.toLocaleString() }}</div>
                </div>
              </div>
            </div>
          </a-col>

          <!-- 词云图 -->
          <a-col :xs="24" :sm="8" :lg="12">
            <div class="wordcloud-container">
              <div class="wordcloud-header">
                <h3 class="wordcloud-title">热门短语词云图</h3>
                <div class="wordcloud-stats">
                  <span class="stat-item positive">
                    <span class="stat-dot positive"></span>
                    正面反馈
                  </span>
                  <span class="stat-item negative">
                    <span class="stat-dot negative"></span>
                    负面反馈
                  </span>
                  <span class="stat-item neutral">
                    <span class="stat-dot neutral"></span>
                    中性反馈
                  </span>
                </div>
              </div>
              <canvas class="wordcloud-chart" ref="wordCloudRef"></canvas>
            </div>
          </a-col>

          <!-- 负面热词TOP100 -->
          <a-col :xs="24" :sm="8" :lg="6">
            <div class="hotwords-panel">
              <div class="panel-header">
                <h3 class="panel-title">
                  <span class="title-icon negative">
                    <FrownOutlined />
                  </span>
                  TOP100负面热词
                </h3>
              </div>
              <div class="hotwords-list">
                <div 
                  v-for="(word, index) in negativeHotwords" 
                  :key="word.text"
                  class="hotword-item"
                  :class="{ 'top-word': index < 3 }"
                >
                  <div class="word-rank">{{ index + 1 }}</div>
                  <div class="word-content">
                    <div class="word-text">{{ word.text }}</div>
                    <div class="word-bar">
                      <div 
                        class="word-progress negative" 
                        :style="{ width: `${(word.value / negativeHotwords[0].value) * 100}%` }"
                      ></div>
                    </div>
                  </div>
                  <div class="word-count">{{ word.value.toLocaleString() }}</div>
                </div>
              </div>
            </div>
          </a-col>
        </a-row>
      </a-card>
    </div>
    
    <!-- 图表区域 -->
    <div class="charts-section">
      <a-row :gutter="[24, 24]">
        <!-- 反馈趋势图 -->
        <a-col :xs="24" :lg="12">
          <a-card title="反馈趋势分析" class="chart-card">
            <template #extra>
              <a-radio-group v-model="trendPeriod" size="small" @change="updateTrendChart">
                <a-radio-button value="7d">7天</a-radio-button>
                <a-radio-button value="30d">30天</a-radio-button>
                <a-radio-button value="90d">90天</a-radio-button>
              </a-radio-group>
            </template>
            <div class="chart-container" ref="trendChartRef"></div>
          </a-card>
        </a-col>

        <!-- 情感分析饼图 -->
        <a-col :xs="24" :lg="12">
          <a-card title="情感分析分布" class="chart-card">
            <template #extra>
              <a-tooltip title="基于AI智能情感分析">
                <InfoCircleOutlined style="color: #999;" />
              </a-tooltip>
            </template>
            <div class="chart-container" ref="sentimentChartRef"></div>
          </a-card>
        </a-col>

        <!-- 分类统计柱状图 -->
        <a-col :xs="24" :lg="16">
          <a-card title="反馈分类统计" class="chart-card">
            <template #extra>
              <a-select v-model="categoryPeriod" size="small" style="width: 120px" @change="updateCategoryChart">
                <a-select-option value="today">今日</a-select-option>
                <a-select-option value="week">本周</a-select-option>
                <a-select-option value="month">本月</a-select-option>
              </a-select>
            </template>
            <div class="chart-container large" ref="categoryChartRef"></div>
          </a-card>
        </a-col>

        <!-- 热门问题排行 -->
        <a-col :xs="24" :lg="8">
          <a-card title="热门问题排行" class="chart-card">
            <template #extra>
              <a href="#" class="view-more">查看更多</a>
            </template>
            <div class="hot-issues-list">
              <div 
                v-for="(issue, index) in hotIssues" 
                :key="issue.id"
                class="issue-item"
                :class="{ 'top-issue': index < 3 }"
              >
                <div class="issue-rank">{{ index + 1 }}</div>
                <div class="issue-content">
                  <div class="issue-title">{{ issue.title }}</div>
                  <div class="issue-meta">
                    <a-tag :color="getIssueTypeColor(issue.type)" size="small">
                      {{ issue.type }}
                    </a-tag>
                    <span class="issue-count">{{ issue.count }}次反馈</span>
                  </div>
                </div>
                <div class="issue-trend">
                  <div class="trend-indicator" :class="issue.trend > 0 ? 'rising' : 'falling'">
                    <CaretUpOutlined v-if="issue.trend > 0" />
                    <CaretDownOutlined v-else />
                  </div>
                </div>
              </div>
          </div>
          </a-card>
        </a-col>
      </a-row>
          </div>

    <!-- 智能行动计划区域 -->
    <div class="action-plan-section">
      <a-card title="🚀 智能行动计划" class="action-plan-card">
        <template #extra>
          <a-space>
            <a-tag color="blue" v-if="actionPlan">计划ID: {{ actionPlan.plan_id }}</a-tag>
            <a-tag color="green" v-if="actionPlan">{{ actionPlan.total_actions }} 个行动项</a-tag>
            <a-button type="link" size="small" @click="$router.push('/decision-engine')">
              查看详情
            </a-button>
          </a-space>
        </template>
        
        <div v-if="actionPlanLoading" class="loading-placeholder">
          <a-spin size="large">
            <template #tip>正在生成智能行动计划...</template>
          </a-spin>
        </div>
        
        <div v-else-if="actionPlan" class="action-plan-content">
          <!-- 计划概览 -->
          <a-row :gutter="16" class="plan-overview">
            <a-col :span="6">
              <div class="metric-item priority-p0">
                <div class="metric-value">{{ actionPlan.p0_actions }}</div>
                <div class="metric-label">P0 紧急</div>
              </div>
            </a-col>
            <a-col :span="6">
              <div class="metric-item priority-p1">
                <div class="metric-value">{{ actionPlan.p1_actions }}</div>
                <div class="metric-label">P1 重要</div>
              </div>
            </a-col>
            <a-col :span="6">
              <div class="metric-item priority-p2">
                <div class="metric-value">{{ actionPlan.p2_actions }}</div>
                <div class="metric-label">P2 正常</div>
              </div>
            </a-col>
            <a-col :span="6">
              <div class="metric-item priority-p3">
                <div class="metric-value">{{ actionPlan.p3_actions }}</div>
                <div class="metric-label">P3 次要</div>
              </div>
            </a-col>
          </a-row>

          <!-- 关键信息 -->
          <a-row :gutter="16" class="plan-info">
            <a-col :span="12">
              <div class="info-card timeline-info">
                <div class="info-header">⏰ 预估时间线</div>
                <div class="info-content">{{ actionPlan.estimated_timeline }}</div>
              </div>
            </a-col>
            <a-col :span="12">
              <div class="info-card effort-info">
                <div class="info-header">👥 工作量估算</div>
                <div class="info-content">{{ actionPlan.total_effort_estimate }}</div>
              </div>
            </a-col>
          </a-row>

          <!-- 关键洞察 -->
          <div v-if="actionPlan.key_insights && actionPlan.key_insights.length > 0" class="insights-section">
            <div class="section-title">💡 关键洞察</div>
            <div class="insights-grid">
              <div 
                v-for="(insight, index) in actionPlan.key_insights" 
                :key="index"
                class="insight-item"
              >
                <div class="insight-content">{{ insight }}</div>
              </div>
            </div>
          </div>

          <!-- 核心行动项 -->
          <div v-if="actionPlan.action_items && actionPlan.action_items.length > 0" class="actions-section">
            <div class="section-title">🎯 核心行动项</div>
            <div class="actions-grid">
              <div 
                v-for="action in actionPlan.action_items.slice(0, 4)" 
                :key="action.id"
                class="action-card"
                :class="`priority-${action.priority.toLowerCase()}`"
              >
                <div class="action-header">
                  <div class="action-title">{{ action.title }}</div>
                  <a-tag :color="getPriorityColor(action.priority)" size="small">
                    {{ action.priority }}
                  </a-tag>
                </div>
                <div class="action-description">{{ action.description }}</div>
                <div class="action-footer">
                  <a-space>
                    <span class="action-team">👥 {{ action.owner_team }}</span>
                    <span class="action-effort">⏳ {{ action.estimated_effort }}</span>
                  </a-space>
                </div>
              </div>
            </div>
          </div>
        </div>

        <div v-else class="empty-placeholder">
          <a-empty description="暂无行动计划数据">
            <a-button type="primary" @click="loadActionPlan">生成计划</a-button>
          </a-empty>
        </div>
      </a-card>
    </div>

    <!-- 最新动态 -->
    <div class="activity-section">
      <a-row :gutter="[24, 24]">
        <a-col :xs="24" :lg="12">
          <a-card title="最新反馈" class="activity-card">
            <template #extra>
              <a-button type="link" size="small" @click="$router.push('/feedback')">
                查看全部
              </a-button>
            </template>
            <a-list :data-source="recentFeedback" :loading="loading">
              <template #renderItem="{ item }">
                <a-list-item>
                  <a-list-item-meta>
                    <template #avatar>
                      <a-avatar>{{ item.user?.charAt(0) || 'U' }}</a-avatar>
                    </template>
                    <template #title>
                      <span class="feedback-title">{{ item.title }}</span>
                      <a-tag :color="getSentimentColor(item.sentiment)" size="small" style="margin-left: 8px;">
                        {{ getSentimentLabel(item.sentiment) }}
                      </a-tag>
                    </template>
                    <template #description>
                      <div class="feedback-content">{{ item.content.substring(0, 80) }}...</div>
                      <div class="feedback-meta">
                        <span class="meta-item">
                          <ClockCircleOutlined />
                          {{ formatTime(item.createdAt) }}
                        </span>
                        <span class="meta-item">
                          <UserOutlined />
                          {{ item.user }}
                        </span>
          </div>
                    </template>
                  </a-list-item-meta>
                </a-list-item>
              </template>
            </a-list>
          </a-card>
        </a-col>

        <a-col :xs="24" :lg="12">
          <a-card title="系统通知" class="activity-card">
            <template #extra>
              <a-badge :count="notifications.filter(n => !n.read).length">
                <a-button type="link" size="small">管理通知</a-button>
              </a-badge>
            </template>
            <a-list :data-source="notifications" :loading="loading">
              <template #renderItem="{ item }">
                <a-list-item :class="{ 'unread': !item.read }">
                  <a-list-item-meta>
                    <template #avatar>
                      <a-badge dot v-if="!item.read">
                        <div class="notification-icon" :class="`type-${item.type}`">
                          <component :is="getNotificationIcon(item.type)" />
                        </div>
                      </a-badge>
                      <div v-else class="notification-icon" :class="`type-${item.type}`">
                        <component :is="getNotificationIcon(item.type)" />
                      </div>
                    </template>
                    <template #title>
                      <span class="notification-title">{{ item.title }}</span>
                    </template>
                    <template #description>
                      <div class="notification-content">{{ item.content }}</div>
                      <div class="notification-time">
                        {{ formatTime(item.createdAt) }}
          </div>
                    </template>
                  </a-list-item-meta>
                </a-list-item>
              </template>
            </a-list>
          </a-card>
        </a-col>
      </a-row>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, nextTick } from 'vue'
import { message } from 'ant-design-vue'
import * as echarts from 'echarts'
import WordCloud from 'wordcloud'
import { decisionEngineAPI, feedbackAPI } from '@/utils/api'
import {
  ArrowUpOutlined,
  ArrowDownOutlined,
  InfoCircleOutlined,
  CaretUpOutlined,
  CaretDownOutlined,
  ClockCircleOutlined,
  UserOutlined,
  MessageOutlined,
  BellOutlined,
  WarningOutlined,
  CheckCircleOutlined,
  SmileOutlined,
  FrownOutlined
} from '@ant-design/icons-vue'

// 响应式数据
const loading = ref(false)
const actionPlanLoading = ref(false)
const actionPlan = ref(null)
const trendPeriod = ref('30d')
const categoryPeriod = ref('week')
const hotwordsPeriod = ref('week')

// 图表引用
const trendChartRef = ref(null)
const sentimentChartRef = ref(null)
const categoryChartRef = ref(null)
const wordCloudRef = ref(null)

// 统计数据
const statistics = ref([
  {
    key: 'total',
    type: 'primary',
    icon: MessageOutlined,
    label: '总反馈数',
    value: '12,436',
    trend: 12.5
  },
  {
    key: 'processed',
    type: 'success',
    icon: CheckCircleOutlined,
    label: '已处理',
    value: '8,952',
    trend: 8.2
  },
  {
    key: 'pending',
    type: 'warning',
    icon: ClockCircleOutlined,
    label: '待处理',
    value: '2,184',
    trend: -5.1
  },
  {
    key: 'critical',
    type: 'danger',
    icon: WarningOutlined,
    label: '紧急问题',
    value: '89',
    trend: -15.3
  }
])

// 热门问题
const hotIssues = ref([
  { id: 1, title: '登录页面加载缓慢', type: '性能问题', count: 156, trend: 23 },
  { id: 2, title: '支付流程异常', type: '功能问题', count: 142, trend: -8 },
  { id: 3, title: '移动端适配问题', type: 'UI问题', count: 98, trend: 15 },
  { id: 4, title: '数据同步延迟', type: '技术问题', count: 87, trend: 5 },
  { id: 5, title: '用户体验优化建议', type: '建议', count: 76, trend: -12 }
])

// 快速操作数据已移除，由智能行动计划取代

// 最新反馈
const recentFeedback = ref([
  {
    id: 1,
    title: '购买流程中遇到支付问题',
    content: '在使用微信支付时，页面一直显示加载中，无法完成支付操作，建议优化支付流程的稳定性...',
    user: '张三',
    sentiment: 'negative',
    createdAt: new Date(Date.now() - 2 * 60 * 1000)
  },
  {
    id: 2,
    title: '新功能使用体验很好',
    content: '最新更新的搜索功能非常好用，响应速度快，结果准确度高，希望能继续保持...',
    user: '李四',
    sentiment: 'positive',
    createdAt: new Date(Date.now() - 15 * 60 * 1000)
  },
  {
    id: 3,
    title: '建议增加深色模式',
    content: '希望应用能够支持深色模式，这样在夜间使用时会更加舒适，对眼睛也更好...',
    user: '王五',
    sentiment: 'neutral',
    createdAt: new Date(Date.now() - 30 * 60 * 1000)
  }
])

// 系统通知
const notifications = ref([
  {
    id: 1,
    type: 'warning',
    title: '系统维护通知',
    content: '系统将于今晚22:00-23:00进行维护升级',
    read: false,
    createdAt: new Date(Date.now() - 10 * 60 * 1000)
  },
  {
    id: 2,
    type: 'info',
    title: '新版本发布',
    content: 'v2.1.0版本已发布，新增AI智能分析功能',
    read: false,
    createdAt: new Date(Date.now() - 2 * 60 * 60 * 1000)
  },
  {
    id: 3,
    type: 'success',
    title: '数据备份完成',
    content: '今日数据备份已成功完成',
    read: true,
    createdAt: new Date(Date.now() - 6 * 60 * 60 * 1000)
  }
])

// 正面热词数据
const positiveHotwords = ref([
  { text: '安装', value: 18794 },
  { text: '响应', value: 13340 },
  { text: '清洁', value: 8911 },
  { text: '解放', value: 8556 },
  { text: '干净', value: 7805 },
  { text: '效果', value: 6695 },
  { text: '服务', value: 6546 },
  { text: '上门', value: 6244 },
  { text: '师傅专业', value: 5890 },
  { text: '物流很快', value: 5567 },
  { text: '清洁效果好', value: 5234 },
  { text: '师傅服务', value: 4892 },
  { text: '性价比高', value: 4556 },
  { text: '颜值高', value: 4234 },
  { text: '服务态度', value: 3987 }
])

// 负面热词数据
const negativeHotwords = ref([
  { text: '清理', value: 1294 },
  { text: '干净', value: 1051 },
  { text: '效果', value: 762 },
  { text: '能力', value: 693 },
  { text: '抱地', value: 668 },
  { text: '打扫', value: 565 },
  { text: '客服', value: 551 },
  { text: '解放', value: 506 },
  { text: '噪音大', value: 445 },
  { text: '清洁效果不理想', value: 398 },
  { text: '性价比低', value: 367 },
  { text: '师傅不专业', value: 334 },
  { text: '物流慢', value: 298 },
  { text: '服务态度差', value: 267 },
  { text: '故障频繁', value: 234 }
])

// 词云图数据
const wordCloudData = ref([
  { name: '清洁功能', value: 2340, sentiment: 'positive' },
  { name: '服务态度很好', value: 1890, sentiment: 'positive' },
  { name: '师傅服务', value: 1567, sentiment: 'positive' },
  { name: '颜值高', value: 1456, sentiment: 'positive' },
  { name: '颜值很高', value: 1234, sentiment: 'positive' },
  { name: '清洁效果', value: 1123, sentiment: 'positive' },
  { name: '物流很快', value: 998, sentiment: 'positive' },
  { name: '性价比高', value: 876, sentiment: 'positive' },
  { name: '师傅很专业', value: 756, sentiment: 'positive' },
  { name: '操作简单', value: 654, sentiment: 'positive' },
  { name: '智能避障', value: 543, sentiment: 'positive' },
  { name: '噪音控制', value: 432, sentiment: 'neutral' },
  { name: '清洁效果不理想', value: 398, sentiment: 'negative' },
  { name: '噪音大', value: 345, sentiment: 'negative' },
  { name: '故障频繁', value: 298, sentiment: 'negative' },
  { name: '性价比低', value: 267, sentiment: 'negative' },
  { name: '师傅不专业', value: 234, sentiment: 'negative' },
  { name: '清洁能力差', value: 198, sentiment: 'negative' },
  { name: '外观设计', value: 167, sentiment: 'neutral' },
  { name: '功能全面', value: 145, sentiment: 'positive' }
])

// 方法
const refreshData = async () => {
  loading.value = true
  try {
    // 模拟API调用
    await new Promise(resolve => setTimeout(resolve, 1000))
    message.success('数据刷新成功')
  } catch (error) {
    message.error('数据刷新失败')
  } finally {
    loading.value = false
  }
}

const exportReport = () => {
  message.info('报告导出功能开发中...')
}

// handleQuickAction方法已移除，由智能行动计划取代

const getIssueTypeColor = (type) => {
  const colorMap = {
    '性能问题': 'orange',
    '功能问题': 'red',
    'UI问题': 'blue',
    '技术问题': 'purple',
    '建议': 'green'
  }
  return colorMap[type] || 'default'
}

const getSentimentColor = (sentiment) => {
  const colorMap = {
    'positive': 'green',
    'negative': 'red',
    'neutral': 'blue'
  }
  return colorMap[sentiment] || 'default'
}

const getSentimentLabel = (sentiment) => {
  const labelMap = {
    'positive': '积极',
    'negative': '消极',
    'neutral': '中性'
  }
  return labelMap[sentiment] || '未知'
}

const getNotificationIcon = (type) => {
  const iconMap = {
    'warning': WarningOutlined,
    'info': BellOutlined,
    'success': CheckCircleOutlined,
    'error': WarningOutlined
  }
  return iconMap[type] || BellOutlined
}

const formatTime = (date) => {
  const now = new Date()
  const diff = now - new Date(date)
  const minutes = Math.floor(diff / (1000 * 60))
  const hours = Math.floor(diff / (1000 * 60 * 60))
  const days = Math.floor(diff / (1000 * 60 * 60 * 24))
  
  if (minutes < 60) return `${minutes}分钟前`
  if (hours < 24) return `${hours}小时前`
  return `${days}天前`
}

// 加载行动计划
const loadActionPlan = async () => {
  actionPlanLoading.value = true
  try {
    // 获取反馈数据ID列表
    const feedbackResponse = await feedbackAPI.getFeedbacks({ limit: 30 })
    const feedbackData = feedbackResponse.data.data || []
    const feedbackIds = feedbackData.map(item => item.id || item._id).filter(Boolean)
    
    if (feedbackIds.length === 0) {
      console.warn('没有找到可分析的反馈数据')
      return
    }
    
    // 调用行动计划生成API
    const planResult = await decisionEngineAPI.generateActionPlan({
      feedback_ids: feedbackIds,
      priority_threshold: 0.4,
      include_low_priority: true
    })
    
    actionPlan.value = planResult.data
  } catch (error) {
    console.error('行动计划生成失败:', error)
    // 静默失败，不显示错误信息
  } finally {
    actionPlanLoading.value = false
  }
}

// 获取优先级颜色
const getPriorityColor = (priority) => {
  const colorMap = {
    'P0': 'red',
    'P1': 'orange', 
    'P2': 'blue',
    'P3': 'green'
  }
  return colorMap[priority] || 'default'
}

// 图表初始化
const initTrendChart = () => {
  const chart = echarts.init(trendChartRef.value)
  const option = {
      tooltip: {
        trigger: 'axis'
      },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '3%',
      containLabel: true
      },
      xAxis: {
        type: 'category',
      data: ['1月', '2月', '3月', '4月', '5月', '6月', '7月']
      },
      yAxis: {
        type: 'value'
      },
    series: [
      {
        name: '反馈数量',
        type: 'line',
        smooth: true,
        data: [820, 932, 901, 934, 1290, 1330, 1320],
        areaStyle: {
          opacity: 0.3
        }
      }
    ]
  }
  chart.setOption(option)
}

const initSentimentChart = () => {
  const chart = echarts.init(sentimentChartRef.value)
  const option = {
      tooltip: {
        trigger: 'item'
      },
      legend: {
      bottom: '0%',
      left: 'center'
      },
      series: [
        {
          type: 'pie',
        radius: ['40%', '70%'],
        avoidLabelOverlap: false,
        label: {
          show: false,
          position: 'center'
        },
          emphasis: {
          label: {
            show: true,
            fontSize: 20,
            fontWeight: 'bold'
          }
        },
        labelLine: {
          show: false
        },
        data: [
          { value: 1048, name: '积极', itemStyle: { color: '#52c41a' } },
          { value: 735, name: '中性', itemStyle: { color: '#1890ff' } },
          { value: 580, name: '消极', itemStyle: { color: '#f5222d' } }
        ]
        }
      ]
  }
  chart.setOption(option)
}

const initCategoryChart = () => {
  const chart = echarts.init(categoryChartRef.value)
  const option = {
    tooltip: {
      trigger: 'axis',
      axisPointer: {
        type: 'shadow'
      }
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '3%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      data: ['功能问题', '性能问题', 'UI问题', '技术问题', '建议', '其他']
    },
    yAxis: {
      type: 'value'
    },
    series: [
      {
        name: '反馈数量',
        type: 'bar',
        data: [320, 302, 301, 334, 390, 330],
        itemStyle: {
          color: '#1890ff',
          borderRadius: [4, 4, 0, 0]
        }
      }
    ]
  }
  chart.setOption(option)
}

const updateTrendChart = () => {
  // 根据时间周期更新图表数据
  message.info(`切换到${trendPeriod.value}数据`)
    }

const updateCategoryChart = () => {
  // 根据时间周期更新图表数据
  message.info(`切换到${categoryPeriod.value}数据`)
}

// 初始化词云图
const initWordCloud = () => {
  console.log('开始初始化词云图')
  const canvas = wordCloudRef.value
  
  if (!canvas) {
    console.error('Canvas元素未找到')
    return
  }
  
  console.log('Canvas元素找到，尺寸:', canvas.width, 'x', canvas.height)
  console.log('词云数据:', wordCloudData.value)
  
  // 优化的颜色配置 - 参考图2的配色方案
  const getWordColor = (sentiment, weight) => {
    const colors = {
      'positive': [
        '#52c41a', '#73d13d', '#95de64', '#b7eb8f', '#d9f7be',  // 绿色系
        '#13c2c2', '#36cfc9', '#5cdbd3', '#87e8de', '#b5f5ec',  // 青色系
        '#1890ff', '#40a9ff', '#69c0ff', '#91d5ff', '#bae7ff'   // 蓝色系
      ],
      'negative': [
        '#ff4d4f', '#ff7875', '#ffa39e', '#ffccc7', '#ffd8d8',  // 红色系
        '#fa541c', '#ff7a45', '#ff9c6e', '#ffbb96', '#ffd6cc',  // 橙红色系
        '#eb2f96', '#f759ab', '#ff85c0', '#ffadd2', '#ffd6e7'   // 洋红色系
      ],
      'neutral': [
        '#1890ff', '#40a9ff', '#69c0ff', '#91d5ff', '#bae7ff',  // 蓝色系
        '#722ed1', '#9254de', '#b37feb', '#d3adf7', '#efdbff',  // 紫色系
        '#2f54eb', '#597ef7', '#85a5ff', '#adc6ff', '#d6e4ff'   // 深蓝色系
      ]
    }
    
    const sentimentColors = colors[sentiment] || colors['neutral']
    // 根据权重选择颜色深浅：权重高的用深色，权重低的用浅色
    const colorIndex = weight > 1000 ? Math.floor(Math.random() * 5) : 
                      weight > 500 ? Math.floor(Math.random() * 5) + 5 :
                      Math.floor(Math.random() * 5) + 10
    
    return sentimentColors[Math.min(colorIndex, sentimentColors.length - 1)]
  }
  
  // 准备词云数据，按权重排序
  const sortedData = [...wordCloudData.value].sort((a, b) => b.value - a.value)
  const list = sortedData.map(item => [item.name, item.value])
  console.log('处理后的列表数据:', list)
  
  // 创建颜色数组
  const colors = sortedData.map(item => getWordColor(item.sentiment, item.value))
  console.log('颜色数组:', colors)
  
  try {
    // 清空canvas
    const ctx = canvas.getContext('2d')
    ctx.clearRect(0, 0, canvas.width, canvas.height)
    
    // 优化的词云配置 - 参考图2的排版效果
    const options = {
      list: list,
      gridSize: 4,  // 减小网格大小，让词汇排列更紧密
      weightFactor: function(size) {
        // 优化权重计算，让大小层次更明显
        const maxWeight = Math.max(...list.map(item => item[1]))
        const minWeight = Math.min(...list.map(item => item[1]))
        const normalizedSize = (size - minWeight) / (maxWeight - minWeight)
        
        // 根据canvas大小动态调整字体大小
        const canvasSize = Math.min(canvas.width, canvas.height)
        const baseFontSize = canvasSize / 25
        
        return baseFontSize * (0.5 + normalizedSize * 2.5)  // 字体大小范围：0.5x到3x
      },
      fontFamily: 'Microsoft YaHei, PingFang SC, Hiragino Sans GB, Arial, sans-serif',
      fontWeight: function(word, weight, fontSize) {
        // 权重高的词汇使用加粗字体
        return weight > 1000 ? 'bold' : weight > 500 ? '600' : 'normal'
      },
      color: function(word, weight, fontSize, distance, theta) {
        const index = list.findIndex(item => item[0] === word)
        return colors[index] || '#1890ff'
      },
      backgroundColor: 'transparent',
      rotateRatio: 0.4,  // 增加旋转比例，让布局更灵活
      rotationSteps: 4,  // 增加旋转步数
      minSize: 12,       // 提高最小字体大小
      maxSize: 60,       // 设置最大字体大小
      ellipticity: 0.65, // 设置椭圆形状因子，让布局更紧凑
      shape: 'circle',
      drawOutOfBound: false,
      shrinkToFit: true,
      clearCanvas: true,
      hover: function(item, dimension, event) {
        console.log('悬停词汇:', item)
        if (item) {
          // 创建提示框
          let tooltip = document.getElementById('wordcloud-tooltip')
          if (!tooltip) {
            tooltip = document.createElement('div')
            tooltip.id = 'wordcloud-tooltip'
            tooltip.style.cssText = `
              position: fixed;
              background: rgba(0, 0, 0, 0.85);
              color: white;
              padding: 8px 12px;
              border-radius: 6px;
              font-size: 12px;
              pointer-events: none;
              z-index: 9999;
              white-space: nowrap;
              box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
              border: 1px solid rgba(255, 255, 255, 0.1);
            `
            document.body.appendChild(tooltip)
          }
          
          // 获取原始数据信息
          const originalData = sortedData.find(data => data.name === item[0])
          const sentiment = originalData?.sentiment || 'neutral'
          const sentimentText = sentiment === 'positive' ? '正面' : sentiment === 'negative' ? '负面' : '中性'
          const index = list.findIndex(listItem => listItem[0] === item[0])
          const color = colors[index] || '#1890ff'
          
          tooltip.innerHTML = `
            <div style="font-weight: bold; margin-bottom: 4px;">${item[0]}</div>
            <div style="color: ${color};">● ${sentimentText}反馈</div>
            <div>出现次数: <strong>${item[1].toLocaleString()}</strong></div>
          `
          tooltip.style.left = event.pageX + 10 + 'px'
          tooltip.style.top = event.pageY - 10 + 'px'
          tooltip.style.display = 'block'
        }
      },
      click: function(item, dimension, event) {
        if (item) {
          message.info(`点击了词汇：${item[0]} (${item[1]}次)`)
        }
      }
    }
    
    console.log('词云配置:', options)
    
    // 创建词云
    WordCloud(canvas, options)
    console.log('词云创建完成')
    
    // 鼠标离开时隐藏提示框
    canvas.addEventListener('mouseleave', () => {
      const tooltip = document.getElementById('wordcloud-tooltip')
      if (tooltip) {
        tooltip.style.display = 'none'
      }
    })
    
  } catch (error) {
    console.error('词云创建失败:', error)
    // 如果词云创建失败，显示文本提示
    const ctx = canvas.getContext('2d')
    ctx.fillStyle = '#666'
    ctx.font = '16px Arial'
    ctx.textAlign = 'center'
    ctx.fillText('词云图加载中...', canvas.width / 2, canvas.height / 2)
  }
}

// 更新热词数据
const updateHotwords = () => {
  message.info(`切换到${hotwordsPeriod.value}热词数据`)
  // 这里可以调用API更新数据
}

// 定义resize处理函数引用，便于添加和移除监听器
let resizeHandler = null
let resizeTimeout = null

// 防抖函数，防止 ResizeObserver 循环
const debounceResize = (func, delay = 100) => {
  return (...args) => {
    clearTimeout(resizeTimeout)
    resizeTimeout = setTimeout(() => func.apply(this, args), delay)
  }
}

// 生命周期
onMounted(async () => {
  await nextTick()
  
  // 初始化图表
  if (trendChartRef.value) initTrendChart()
  if (sentimentChartRef.value) initSentimentChart()
  if (categoryChartRef.value) initCategoryChart()
  
  // 设置canvas尺寸并初始化词云图
  if (wordCloudRef.value) {
    const canvas = wordCloudRef.value
    const container = canvas.parentElement
    const rect = container.getBoundingClientRect()
    
    console.log('容器尺寸:', rect.width, 'x', rect.height)
    
    // 设置较大的固定尺寸确保能够渲染
    const canvasWidth = Math.max(400, rect.width - 80)
    const canvasHeight = Math.max(300, rect.height - 120)
    
    canvas.width = canvasWidth
    canvas.height = canvasHeight
    canvas.style.width = canvasWidth + 'px'
    canvas.style.height = canvasHeight + 'px'
    canvas.style.margin = '10px auto'
    canvas.style.display = 'block'
    canvas.style.borderRadius = '8px'
    canvas.style.backgroundColor = 'transparent'
    // canvas.style.border = '1px solid #ddd' // 调试用边框（已移除）
    
    console.log('设置canvas尺寸:', canvasWidth, 'x', canvasHeight)
    
    // 延迟初始化词云图确保canvas完全准备好
    setTimeout(() => {
      initWordCloud()
    }, 100)
  }
  
  // 定义resize处理函数
  const originalResizeHandler = () => {
    try {
      if (trendChartRef.value) echarts.getInstanceByDom(trendChartRef.value)?.resize()
      if (sentimentChartRef.value) echarts.getInstanceByDom(sentimentChartRef.value)?.resize()
      if (categoryChartRef.value) echarts.getInstanceByDom(categoryChartRef.value)?.resize()
      
      // 重新设置词云图canvas尺寸并重新渲染
      if (wordCloudRef.value) {
        const canvas = wordCloudRef.value
        const container = canvas.parentElement
        if (container) {
          const rect = container.getBoundingClientRect()
          
          const canvasWidth = Math.max(400, rect.width - 80)
          const canvasHeight = Math.max(300, rect.height - 120)
          
          canvas.width = canvasWidth
          canvas.height = canvasHeight
          canvas.style.width = canvasWidth + 'px'
          canvas.style.height = canvasHeight + 'px'
          
          // 重新初始化词云图
          setTimeout(() => {
            initWordCloud()
          }, 100)
        }
      }
    } catch (error) {
      console.warn('Resize处理函数执行出错:', error)
    }
  }
  
  // 使用防抖函数包装resize处理函数
  resizeHandler = debounceResize(originalResizeHandler, 150)
  
  // 添加窗口大小改变监听器
  window.addEventListener('resize', resizeHandler)
  
  // 加载行动计划
  loadActionPlan()
})

// 组件销毁时清理
onUnmounted(() => {
  try {
    // 移除resize事件监听器
    if (resizeHandler) {
      window.removeEventListener('resize', resizeHandler)
      resizeHandler = null
    }
    
    // 清理防抖timeout
    if (resizeTimeout) {
      clearTimeout(resizeTimeout)
      resizeTimeout = null
    }
    
    // 清理ECharts实例
    if (trendChartRef.value) {
      const chart = echarts.getInstanceByDom(trendChartRef.value)
      if (chart) {
        chart.dispose()
      }
    }
    
    if (sentimentChartRef.value) {
      const chart = echarts.getInstanceByDom(sentimentChartRef.value)
      if (chart) {
        chart.dispose()
      }
    }
    
    if (categoryChartRef.value) {
      const chart = echarts.getInstanceByDom(categoryChartRef.value)
      if (chart) {
        chart.dispose()
      }
    }
    
    // 清理词云图canvas事件监听器
    if (wordCloudRef.value) {
      const canvas = wordCloudRef.value
      const newCanvas = canvas.cloneNode(true)
      canvas.parentNode?.replaceChild(newCanvas, canvas)
    }
    
    // 清理词云图提示框
    const tooltip = document.getElementById('wordcloud-tooltip')
    if (tooltip && tooltip.parentNode) {
      tooltip.parentNode.removeChild(tooltip)
    }
  } catch (error) {
    console.warn('组件清理过程中出现错误:', error)
  }
})
</script>

<style lang="scss" scoped>
.dashboard-container {
  min-height: calc(100vh - var(--header-height) - var(--footer-height));
  overflow-y: auto;
}

// 行动计划区域样式
.action-plan-section {
  margin-bottom: 24px;
  
  .action-plan-card {
    border-radius: var(--border-radius-lg);
    
    :deep(.ant-card-body) {
      padding: 24px;
    }
  }
}

.loading-placeholder {
  text-align: center;
  padding: 40px;
}

.action-plan-content {
  padding: 16px 0;
}

.plan-overview {
  margin-bottom: 24px;
}

.metric-item {
  text-align: center;
  padding: 16px;
  border-radius: 12px;
  transition: all 0.3s ease;
  
  &:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  }
  
  // 暗黑模式兼容
  @media (prefers-color-scheme: dark) {
    &:hover {
      box-shadow: 0 4px 12px rgba(255, 255, 255, 0.1);
    }
  }
}

.priority-p0 {
  background: linear-gradient(135deg, #ff9a9e 0%, #fecfef 100%);
  color: #d32f2f;
  
  // 暗黑模式
  @media (prefers-color-scheme: dark) {
    background: linear-gradient(135deg, #d32f2f 0%, #f44336 100%);
    color: #ffcdd2;
  }
}

.priority-p1 {
  background: linear-gradient(135deg, #ffecd2 0%, #fcb69f 100%);
  color: #f57c00;
  
  // 暗黑模式
  @media (prefers-color-scheme: dark) {
    background: linear-gradient(135deg, #f57c00 0%, #ff9800 100%);
    color: #ffe0b2;
  }
}

.priority-p2 {
  background: linear-gradient(135deg, #a8edea 0%, #fed6e3 100%);
  color: #1976d2;
  
  // 暗黑模式
  @media (prefers-color-scheme: dark) {
    background: linear-gradient(135deg, #1976d2 0%, #2196f3 100%);
    color: #bbdefb;
  }
}

.priority-p3 {
  background: linear-gradient(135deg, #d299c2 0%, #fef9d7 100%);
  color: #388e3c;
  
  // 暗黑模式
  @media (prefers-color-scheme: dark) {
    background: linear-gradient(135deg, #388e3c 0%, #4caf50 100%);
    color: #c8e6c9;
  }
}

.metric-value {
  font-size: 28px;
  font-weight: 700;
  margin-bottom: 4px;
}

.metric-label {
  font-size: 14px;
  font-weight: 500;
  opacity: 0.8;
}

.plan-info {
  margin-bottom: 24px;
}

.info-card {
  background: var(--background-color-light);
  border-radius: 8px;
  padding: 16px;
  border-left: 4px solid #1890ff;
  
  // 暗黑模式
  @media (prefers-color-scheme: dark) {
    background: rgba(255, 255, 255, 0.04);
    border-left-color: #40a9ff;
  }
}

.timeline-info {
  border-left-color: #52c41a;
  
  @media (prefers-color-scheme: dark) {
    border-left-color: #73d13d;
  }
}

.effort-info {
  border-left-color: #fa8c16;
  
  @media (prefers-color-scheme: dark) {
    border-left-color: #ffa940;
  }
}

.info-header {
  font-weight: 600;
  color: var(--heading-color);
  margin-bottom: 8px;
  
  @media (prefers-color-scheme: dark) {
    color: rgba(255, 255, 255, 0.85);
  }
}

.info-content {
  font-size: 16px;
  color: var(--text-color);
  
  @media (prefers-color-scheme: dark) {
    color: rgba(255, 255, 255, 0.65);
  }
}

.section-title {
  font-size: 18px;
  font-weight: 600;
  color: var(--heading-color);
  margin: 24px 0 16px 0;
  display: flex;
  align-items: center;
  gap: 8px;
  
  @media (prefers-color-scheme: dark) {
    color: rgba(255, 255, 255, 0.85);
  }
}

.insights-section {
  margin-bottom: 24px;
}

.insights-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 12px;
}

.insight-item {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  padding: 16px;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(102, 126, 234, 0.2);
  
  // 暗黑模式优化
  @media (prefers-color-scheme: dark) {
    background: linear-gradient(135deg, #4a5568 0%, #2d3748 100%);
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3);
  }
}

.insight-content {
  font-size: 14px;
  line-height: 1.5;
}

.actions-section {
  margin-top: 24px;
}

.actions-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 16px;
}

.action-card {
  background: var(--background-color);
  border: 1px solid var(--border-color-split);
  border-radius: 12px;
  padding: 20px;
  transition: all 0.3s ease;
  position: relative;
  overflow: hidden;
  
  // 暗黑模式
  @media (prefers-color-scheme: dark) {
    background: rgba(255, 255, 255, 0.04);
    border-color: rgba(255, 255, 255, 0.1);
  }
  
  &::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    height: 4px;
    background: linear-gradient(90deg, #1890ff, #52c41a);
  }
  
  &.priority-p0::before {
    background: linear-gradient(90deg, #ff4d4f, #ff7875);
  }
  
  &.priority-p1::before {
    background: linear-gradient(90deg, #fa8c16, #ffa940);
  }
  
  &.priority-p2::before {
    background: linear-gradient(90deg, #1890ff, #40a9ff);
  }
  
  &.priority-p3::before {
    background: linear-gradient(90deg, #52c41a, #73d13d);
  }
  
  &:hover {
    transform: translateY(-4px);
    box-shadow: 0 8px 24px rgba(0, 0, 0, 0.12);
    border-color: #1890ff;
    
    @media (prefers-color-scheme: dark) {
      box-shadow: 0 8px 24px rgba(255, 255, 255, 0.1);
      border-color: #40a9ff;
    }
  }
}

.action-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 12px;
}

.action-title {
  font-size: 16px;
  font-weight: 600;
  color: var(--heading-color);
  flex: 1;
  margin-right: 12px;
  
  @media (prefers-color-scheme: dark) {
    color: rgba(255, 255, 255, 0.85);
  }
}

.action-description {
  color: var(--text-color);
  font-size: 14px;
  line-height: 1.5;
  margin-bottom: 16px;
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
  overflow: hidden;
  
  @media (prefers-color-scheme: dark) {
    color: rgba(255, 255, 255, 0.65);
  }
}

.action-footer {
  border-top: 1px solid var(--border-color-split);
  padding-top: 12px;
  
  @media (prefers-color-scheme: dark) {
    border-top-color: rgba(255, 255, 255, 0.1);
  }
}

.action-team, .action-effort {
  font-size: 12px;
  color: var(--text-color-secondary);
  background: var(--background-color-light);
  padding: 4px 8px;
  border-radius: 4px;
  
  @media (prefers-color-scheme: dark) {
    color: rgba(255, 255, 255, 0.45);
    background: rgba(255, 255, 255, 0.04);
  }
}

.empty-placeholder {
  text-align: center;
  padding: 60px 20px;
}

// 热词分析区域样式
.hotwords-section {
  margin-bottom: 24px;
  
  .hotwords-card {
    :deep(.ant-card-body) {
      padding: 24px;
    }
  }
}

// 热词面板样式
.hotwords-panel {
  height: 500px;
  border: 1px solid var(--border-color-split);
  border-radius: var(--border-radius-base);
  overflow: hidden;
  
  .panel-header {
    background: var(--background-color-light);
    padding: 16px 20px;
    border-bottom: 1px solid var(--border-color-split);
    
    .panel-title {
      margin: 0;
      font-size: 16px;
      font-weight: 600;
      display: flex;
      align-items: center;
      
      .title-icon {
        width: 20px;
        height: 20px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        margin-right: 8px;
        font-size: 12px;
        
        &.positive {
          background: var(--success-color-bg);
          color: var(--success-color);
        }
        
        &.negative {
          background: var(--error-color-bg);
          color: var(--error-color);
        }
      }
    }
  }
  
  .hotwords-list {
    height: calc(100% - 56px);
    overflow-y: auto;
    padding: 0 20px;
    
    &::-webkit-scrollbar {
      width: 6px;
    }
    
    &::-webkit-scrollbar-track {
      background: var(--background-color-light);
      border-radius: 3px;
    }
    
    &::-webkit-scrollbar-thumb {
      background: var(--border-color);
      border-radius: 3px;
      
      &:hover {
        background: var(--border-color-base);
      }
    }
  }
  
  .hotword-item {
    display: flex;
    align-items: center;
    padding: 12px 0;
    border-bottom: 1px solid var(--border-color-split);
    transition: all var(--animation-duration-base);
    
    &:last-child {
      border-bottom: none;
    }
    
    &:hover {
      background: var(--background-color-light);
      margin: 0 -20px;
      padding-left: 20px;
      padding-right: 20px;
    }
    
    &.top-word {
      .word-rank {
        background: linear-gradient(135deg, var(--warning-color), #ffb347);
        color: white;
        font-weight: bold;
        box-shadow: 0 2px 8px rgba(250, 173, 20, 0.3);
      }
      
      .word-text {
        font-weight: 600;
        color: var(--heading-color);
      }
    }
  }
  
  .word-rank {
    width: 24px;
    height: 24px;
    border-radius: 50%;
    background: var(--background-color-light);
    border: 1px solid var(--border-color);
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 12px;
    font-weight: 600;
    margin-right: 12px;
    flex-shrink: 0;
  }
  
  .word-content {
    flex: 1;
    min-width: 0;
  }
  
  .word-text {
    font-size: 14px;
    margin-bottom: 4px;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }
  
  .word-bar {
    height: 4px;
    background: var(--background-color-light);
    border-radius: 2px;
    overflow: hidden;
    position: relative;
  }
  
  .word-progress {
    height: 100%;
    border-radius: 2px;
    transition: width 0.3s ease;
    
    &.positive {
      background: linear-gradient(90deg, var(--success-color), #87d068);
    }
    
    &.negative {
      background: linear-gradient(90deg, var(--error-color), #ff7875);
    }
  }
  
  .word-count {
    font-size: 13px;
    font-weight: 600;
    color: var(--text-color-secondary);
    margin-left: 12px;
    flex-shrink: 0;
  }
}

// 词云图容器样式
.wordcloud-container {
  height: 500px;
  border: 1px solid var(--border-color-split);
  border-radius: var(--border-radius-base);
  overflow: hidden;
  
  .wordcloud-header {
    background: var(--background-color-light);
    padding: 16px 20px;
    border-bottom: 1px solid var(--border-color-split);
    
    .wordcloud-title {
      margin: 0 0 12px 0;
      font-size: 16px;
      font-weight: 600;
    }
    
    .wordcloud-stats {
      display: flex;
      gap: 20px;
      
      .stat-item {
        display: flex;
        align-items: center;
        font-size: 12px;
        
        .stat-dot {
          width: 8px;
          height: 8px;
          border-radius: 50%;
          margin-right: 6px;
          
          &.positive {
            background: var(--success-color);
          }
          
          &.negative {
            background: var(--error-color);
          }
          
          &.neutral {
            background: var(--info-color);
          }
        }
      }
    }
  }
  
  .wordcloud-chart {
    height: calc(100% - 76px - 80px); // 减去上下边距
    width: calc(100% - 80px); // 减去左右边距
    margin: 40px auto;
    display: block;
    cursor: pointer;
    border-radius: 8px;
    background: transparent;
  }
}



.stats-section {
  margin: 24px 0 24px 0;
  
  .stat-card {
    background: var(--background-color);
    border-radius: var(--border-radius-lg);
    padding: 24px;
    box-shadow: var(--box-shadow-card);
    transition: all var(--animation-duration-base);
    border-left: 4px solid var(--border-color);
    border: 1px solid var(--border-color-split);
    
    &:hover {
      box-shadow: var(--box-shadow-base);
      transform: translateY(-2px);
    }
    
    &.stat-primary {
      border-left-color: var(--primary-color);
      
      .stat-icon {
        background: var(--info-color-bg);
        color: var(--primary-color);
      }
    }
    
    &.stat-success {
      border-left-color: var(--success-color);
      
      .stat-icon {
        background: var(--success-color-bg);
        color: var(--success-color);
      }
    }
    
    &.stat-warning {
      border-left-color: var(--warning-color);
      
      .stat-icon {
        background: var(--warning-color-bg);
        color: var(--warning-color);
      }
    }
    
    &.stat-danger {
      border-left-color: var(--error-color);
      
      .stat-icon {
        background: var(--error-color-bg);
        color: var(--error-color);
      }
    }
  }
  
  .stat-content {
    display: flex;
    align-items: center;
    margin-bottom: 16px;
  }
  
  .stat-icon {
    width: 48px;
    height: 48px;
    border-radius: 12px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 24px;
    margin-right: 16px;
  }
  
  .stat-info {
    flex: 1;
  }
  
  .stat-number {
    font-size: 32px;
    font-weight: 600;
    line-height: 1;
    margin-bottom: 4px;
  }
  
  .stat-label {
    font-size: 14px;
    color: var(--text-color-secondary);
  }
  
  .stat-trend {
    display: flex;
    align-items: center;
    font-size: 12px;
    
    &.positive {
      color: var(--success-color);
    }
    
    &.negative {
      color: var(--error-color);
    }
    
    .trend-icon {
      margin-right: 4px;
    }
    
    .trend-value {
      font-weight: 600;
      margin-right: 4px;
    }
  }
}

.charts-section {
  margin-bottom: 24px;
  
  .chart-card {
    height: 100%;
    
    :deep(.ant-card-body) {
      padding: 24px 24px 16px;
    }
  }
  
  .chart-container {
    height: 300px;
    
    &.large {
      height: 400px;
    }
  }
  
  .view-more {
    color: var(--primary-color);
    text-decoration: none;
    
    &:hover {
      text-decoration: underline;
    }
  }
}

.hot-issues-list {
  .issue-item {
    display: flex;
    align-items: center;
    padding: 12px 0;
    border-bottom: 1px solid var(--border-color-split);
    
    &:last-child {
      border-bottom: none;
    }
    
    &.top-issue .issue-rank {
      background: linear-gradient(135deg, var(--warning-color), #ffb347);
      color: white;
      font-weight: bold;
    }
  }
  
  .issue-rank {
    width: 24px;
    height: 24px;
    border-radius: 50%;
    background: var(--background-color-light);
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 12px;
    font-weight: 600;
    margin-right: 12px;
    flex-shrink: 0;
  }
  
  .issue-content {
    flex: 1;
    min-width: 0;
  }
  
  .issue-title {
    font-size: 14px;
    font-weight: 500;
    margin-bottom: 4px;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }
  
  .issue-meta {
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 12px;
    color: var(--text-color-secondary);
  }
  
  .issue-trend {
    margin-left: 8px;
    
    .trend-indicator {
      width: 20px;
      height: 20px;
      border-radius: 50%;
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 10px;
      
      &.rising {
        background: var(--success-color-bg);
        color: var(--success-color);
      }
      
      &.falling {
        background: var(--error-color-bg);
        color: var(--error-color);
      }
    }
  }
}

// 行动计划区域的CSS样式已经在前面定义了
  
.activity-section {
  .activity-card {
    height: 100%;
    
    :deep(.ant-card-body) {
      padding: 16px 24px;
    }
  }
  
  .feedback-title {
    font-weight: 500;
  }
  
  .feedback-content {
          margin-bottom: 8px;
    color: var(--text-color-secondary);
    line-height: 1.4;
  }
  
  .feedback-meta {
    display: flex;
    gap: 16px;
  }
  
  .meta-item {
    display: flex;
    align-items: center;
    gap: 4px;
    font-size: 12px;
    color: var(--text-color-disabled);
  }
  
  .notification-icon {
    width: 32px;
    height: 32px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 14px;
    
    &.type-warning {
      background: var(--warning-color-bg);
      color: var(--warning-color);
    }
    
    &.type-info {
      background: var(--info-color-bg);
      color: var(--info-color);
    }
    
    &.type-success {
      background: var(--success-color-bg);
      color: var(--success-color);
    }
    
    &.type-error {
      background: var(--error-color-bg);
      color: var(--error-color);
    }
  }
  
  .notification-title {
    font-weight: 500;
  }
  
  .notification-content {
    margin-bottom: 4px;
    color: var(--text-color-secondary);
        }
        
  .notification-time {
    font-size: 12px;
    color: var(--text-color-disabled);
  }
  
  :deep(.ant-list-item.unread) {
    background: var(--info-color-bg);
    border-radius: 6px;
    margin-bottom: 4px;
    border: 1px solid var(--info-color-outline);
  }
      }

// 响应式设计
@media (max-width: 768px) {
  
  .stat-card {
    text-align: center;
    
    .stat-content {
      flex-direction: column;
      text-align: center;
    }
    
    .stat-icon {
      margin-right: 0;
      margin-bottom: 12px;
    }
  }
  
  .chart-container {
    height: 250px !important;
    
    &.large {
      height: 300px !important;
    }
  }
  
  // 行动计划响应式样式
  .action-plan-section {
    .action-plan-content {
      padding: 8px 0;
    }
    
    .plan-overview {
      margin-bottom: 16px;
    }
    
    .metric-item {
      padding: 12px;
      
      .metric-value {
        font-size: 24px;
      }
      
      .metric-label {
        font-size: 12px;
      }
    }
    
    .plan-info {
      margin-bottom: 16px;
    }
    
    .info-card {
      padding: 12px;
      
      .info-header {
        font-size: 14px;
        margin-bottom: 6px;
      }
      
      .info-content {
        font-size: 14px;
      }
    }
    
    .section-title {
      font-size: 16px;
      margin: 16px 0 12px 0;
    }
    
    .insights-grid {
      grid-template-columns: 1fr;
      gap: 8px;
    }
    
    .insight-item {
      padding: 12px;
      
      .insight-content {
        font-size: 13px;
      }
    }
    
    .actions-grid {
      grid-template-columns: 1fr;
      gap: 12px;
    }
    
    .action-card {
      padding: 16px;
      
      .action-title {
        font-size: 15px;
      }
      
      .action-description {
        font-size: 13px;
        -webkit-line-clamp: 2;
      }
      
      .action-team, .action-effort {
        font-size: 11px;
        padding: 3px 6px;
      }
    }
  }
  
  // 热词分析响应式样式
  .hotwords-section {
    .hotwords-panel {
      height: 350px;
      
      .hotwords-list {
        padding: 0 12px;
      }
      
      .hotword-item {
        &:hover {
          margin: 0 -12px;
          padding-left: 12px;
          padding-right: 12px;
        }
      }
      
      .panel-header {
        padding: 12px 16px;
        
        .panel-title {
          font-size: 14px;
        }
      }
    }
    
    .wordcloud-container {
      height: 350px;
      margin-top: 16px;
      
      .wordcloud-header {
        padding: 12px 16px;
        
        .wordcloud-title {
          font-size: 14px;
          margin-bottom: 8px;
        }
        
        .wordcloud-stats {
          gap: 12px;
          
          .stat-item {
            font-size: 11px;
          }
        }
      }
      
      .wordcloud-chart {
        height: calc(100% - 76px - 40px); // 移动端减少边距
        width: calc(100% - 40px); // 移动端减少边距
        margin: 20px auto; // 移动端减少边距
      }
    }
  }
}

// 浮动动画
@keyframes float {
  0%, 100% {
    transform: translateY(0px) rotate(0deg);
  }
  33% {
    transform: translateY(-10px) rotate(1deg);
  }
  66% {
    transform: translateY(5px) rotate(-1deg);
  }
}
</style> 