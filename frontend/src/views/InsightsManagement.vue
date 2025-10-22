<template>
  <div class="insights-platform">
    <!-- 页面标题栏 -->
    <div class="page-header">
      <div class="header-content">
        <div class="header-left">
          <h1 class="page-title">
            <BulbOutlined class="title-icon" />
            智能洞察分析平台
          </h1>
          <p class="page-subtitle">数据驱动的用户反馈洞察分析与智能决策支持</p>
        </div>
        <div class="header-actions">
          <a-button 
            type="primary" 
            size="large"
            @click="generateInsights" 
            :loading="isGenerating"
            class="generate-btn"
          >
            <PlayCircleOutlined />
            {{ isGenerating ? '生成中...' : '生成洞察' }}
          </a-button>

          <a-button size="large" @click="getDemo" class="demo-btn">
            <EyeOutlined />
            演示数据
          </a-button>
          <a-button size="large" @click="refreshFeedbackData" class="refresh-btn">
            <ReloadOutlined />
            刷新数据
          </a-button>
        </div>
      </div>
    </div>

    <!-- 数据源选择区域 -->
    <div class="data-source-section">
      <a-card title="数据源配置" class="data-source-card">
        <template #extra>
          <a-space>
            <a-button type="link" @click="refreshFeedbackData" :loading="isGenerating">
              <ReloadOutlined />
              刷新数据
            </a-button>
            <a-button type="link" @click="showDataConfig = true">
              <SettingOutlined />
              高级配置
            </a-button>
          </a-space>
        </template>
        
        <!-- 数据概览 -->
        <div class="data-overview">
          <a-row :gutter="24">
            <a-col :span="6">
              <div class="data-metric">
                <div class="metric-value">{{ feedbackStats.total_feedback || 0 }}</div>
                <div class="metric-label">总反馈数</div>
                <div class="metric-status active"></div>
              </div>
            </a-col>
            <a-col :span="6">
              <div class="data-metric">
                <div class="metric-value">{{ feedbackStats.high_priority_count || 0 }}</div>
                <div class="metric-label">高优先级</div>
                <div class="metric-status warning"></div>
              </div>
            </a-col>
            <a-col :span="6">
              <div class="data-metric">
                <div class="metric-value">{{ getSentimentPercentage('positive') }}%</div>
                <div class="metric-label">正面情感</div>
                <div class="metric-status positive"></div>
              </div>
            </a-col>
            <a-col :span="6">
              <div class="data-metric">
                <div class="metric-value">{{ formatTime(insightsStats.last_generation_time) }}</div>
                <div class="metric-label">最后更新</div>
                <div class="metric-status"></div>
              </div>
            </a-col>
          </a-row>
        </div>

        <!-- 数据筛选 -->
        <div class="data-filters">
          <a-row :gutter="16">
            <a-col :span="8">
              <div class="filter-group">
                <label class="filter-label">时间范围</label>
                <a-range-picker v-model="dataConfig.date_range" style="width: 100%" />
              </div>
            </a-col>
            <a-col :span="8">
              <div class="filter-group">
                <label class="filter-label">情感类型</label>
                <a-select
                  v-model="dataConfig.sentiment_filter"
                  mode="multiple"
                  placeholder="选择情感类型"
                  style="width: 100%"
                >
                  <a-select-option value="positive">正面</a-select-option>
                  <a-select-option value="negative">负面</a-select-option>
                  <a-select-option value="neutral">中性</a-select-option>
                </a-select>
              </div>
            </a-col>
            <a-col :span="8">
              <div class="filter-group">
                <label class="filter-label">数据量限制</label>
                <a-input-number
                  v-model="dataConfig.feedback_limit"
                  :min="10"
                  :max="1000"
                  style="width: 100%"
                  placeholder="数据量"
                />
              </div>
            </a-col>
          </a-row>
        </div>
      </a-card>
    </div>

    <!-- 洞察分析区域 -->
    <div class="insights-analysis-section">
      <a-row :gutter="24">
        <!-- 洞察详情列表 - 拉宽到100% -->
        <a-col :span="24">
          <a-card class="insights-detail-card">
            <template #title>
              <div class="insights-header">
                <span class="insights-title">智能洞察详情</span>
                <a-tabs v-model="selectedInsightType" size="small" class="insight-filter-tabs">
                  <a-tab-pane key="all">
                    <template #tab>
                      <span class="tab-with-count">
                        全部洞察
                        <a-badge v-if="allInsights.length > 0" :count="allInsights.length" />
                      </span>
                    </template>
                  </a-tab-pane>
                  <a-tab-pane key="trend">
                    <template #tab>
                      <span class="tab-with-count">
                        趋势分析
                        <a-badge v-if="getInsightCountByType('trend') > 0" :count="getInsightCountByType('trend')" />
                      </span>
                    </template>
                  </a-tab-pane>
                  <a-tab-pane key="pattern">
                    <template #tab>
                      <span class="tab-with-count">
                        模式识别
                        <a-badge v-if="getInsightCountByType('pattern') > 0" :count="getInsightCountByType('pattern')" />
                      </span>
                    </template>
                  </a-tab-pane>
                  <a-tab-pane key="opportunity">
                    <template #tab>
                      <span class="tab-with-count">
                        机会发现
                        <a-badge v-if="getInsightCountByType('opportunity') > 0" :count="getInsightCountByType('opportunity')" />
                      </span>
                    </template>
                  </a-tab-pane>
                  <a-tab-pane key="risk">
                    <template #tab>
                      <span class="tab-with-count">
                        风险预警
                        <a-badge v-if="getInsightCountByType('risk') > 0" :count="getInsightCountByType('risk')" />
                      </span>
                    </template>
                  </a-tab-pane>
                </a-tabs>
              </div>
            </template>

            <div class="insights-content">
              <InsightsPanel :filtered-type="selectedInsightType" />
            </div>
          </a-card>
        </a-col>
      </a-row>
    </div>

    <!-- 行动计划区域 -->
    <div class="action-plans-section">
      <a-card title="智能行动建议" class="action-plans-card">
        <template #extra>
          <a-space>
            <span class="plans-count">{{ filteredActionPlans.length }} 个计划</span>
                         <a-select v-model="selectedPriority" placeholder="优先级" style="width: 120px" size="small">
               <a-select-option value="">全部优先级</a-select-option>
               <a-select-option value="P0">P0 - 紧急</a-select-option>
               <a-select-option value="P1">P1 - 高</a-select-option>
               <a-select-option value="P2">P2 - 中</a-select-option>
               <a-select-option value="P3">P3 - 低</a-select-option>
             </a-select>
          </a-space>
        </template>

        <div class="action-plans-grid">
          <div 
            v-for="plan in filteredActionPlans" 
            :key="plan.plan_id"
            class="action-plan-item"
            :class="`priority-${plan.priority}`"
          >
            <div class="plan-header">
              <a-tag :color="getPriorityColor(plan.priority)" class="priority-tag">
                {{ plan.priority }}
              </a-tag>
              <span class="plan-timeline">{{ plan.timeline }}</span>
            </div>
            
            <h3 class="plan-title">{{ plan.title }}</h3>
            <p class="plan-description">{{ plan.summary }}</p>
            
            <div class="plan-details">
              <div class="plan-effort">
                <ClockCircleOutlined />
                预估工作量：{{ plan.estimated_effort }}
              </div>
              <div class="plan-team">
                <TeamOutlined />
                负责团队：{{ plan.owner_team }}
              </div>
            </div>

            <!-- 洞察来源 -->
            <div class="insight-source" v-if="plan.insight_source">
              <div class="source-label">
                <BulbOutlined />
                基于洞察
              </div>
              <div class="source-tags">
                <a-tag 
                  size="small"
                  :color="getInsightTypeColor(plan.insight_source.type)"
                >
                  {{ getInsightTypeText(plan.insight_source.type) }}
                </a-tag>
              </div>
            </div>
          </div>
        </div>

        <!-- 空状态 -->
        <div v-if="filteredActionPlans.length === 0" class="empty-state">
          <ExclamationCircleOutlined class="empty-icon" />
          <p class="empty-text">暂无行动计划</p>
          <p class="empty-hint">请先生成洞察分析</p>
        </div>
      </a-card>
    </div>

    <!-- 配置弹窗 -->
    <a-modal
      v-model="showDataConfig"
      title="数据源配置"
      width="600px"
      @ok="updateDataConfig"
    >
      <a-form
        :model="dataConfig"
        :label-col="{ span: 6 }"
        :wrapper-col="{ span: 18 }"
      >
        <a-form-item label="反馈数量限制">
          <a-input-number
            v-model="dataConfig.feedback_limit"
            :min="10"
            :max="1000"
            style="width: 100%"
          />
        </a-form-item>
        <a-form-item label="包含行动计划">
          <a-switch v-model="dataConfig.include_action_plans" />
        </a-form-item>
        <a-form-item label="时间范围">
          <a-range-picker v-model="dataConfig.date_range" />
        </a-form-item>
        <a-form-item label="情感过滤">
          <a-select
            v-model="dataConfig.sentiment_filter"
            mode="multiple"
            placeholder="选择情感类型"
            style="width: 100%"
          >
            <a-select-option value="positive">正面</a-select-option>
            <a-select-option value="negative">负面</a-select-option>
            <a-select-option value="neutral">中性</a-select-option>
          </a-select>
        </a-form-item>
      </a-form>
    </a-modal>
  </div>
</template>

<script>
import { computed, ref, reactive, onMounted } from 'vue'
import { message } from 'ant-design-vue'
import { useInsightsStore } from '@/stores/insights'
import InsightsPanel from '@/components/InsightsPanel.vue'
import { feedbackAPI } from '@/utils/api'
import {
  BulbOutlined,
  PlayCircleOutlined,
  ReloadOutlined,
  EyeOutlined,
  ExclamationCircleOutlined,
  ClockCircleOutlined,
  SettingOutlined,
  LineChartOutlined,
  TrophyOutlined,
  TeamOutlined
} from '@ant-design/icons-vue'

export default {
  name: 'InsightsManagement',
  components: {
    InsightsPanel,
    BulbOutlined,
    PlayCircleOutlined,
    ReloadOutlined,
    EyeOutlined,
    ExclamationCircleOutlined,
    ClockCircleOutlined,
    SettingOutlined,
    LineChartOutlined,
    TrophyOutlined,
    TeamOutlined
  },
  setup() {
    const insightsStore = useInsightsStore()
    
    // 响应式数据
    const showDataConfig = ref(false)
    const selectedInsightType = ref('all')
    const selectedPriority = ref('')

    
    // 数据配置 - 默认获取最近一个月数据
    const now = new Date()
    const oneMonthAgo = new Date()
    oneMonthAgo.setMonth(now.getMonth() - 1)
    
    const dataConfig = reactive({
      feedback_limit: 350,  // 增加默认数据量到350
      include_action_plans: true,
      date_range: [oneMonthAgo, now],  // 正确的最近一个月时间范围
      sentiment_filter: []
    })
    
    // 反馈数据统计
    const feedbackStats = reactive({
      total_feedback: 0,
      high_priority_count: 0,
      sentiment_distribution: {
        positive: 0,
        negative: 0,
        neutral: 0
      }
    })
    
    // 计算属性
    const isGenerating = computed(() => insightsStore.isGenerating)
    const allInsights = computed(() => insightsStore.allInsights)
    const allActionPlans = computed(() => insightsStore.allActionPlans)
    const insightsByType = computed(() => insightsStore.insightsByType)
    const insightsStats = computed(() => insightsStore.insightsStats)
    
    // 过滤后的执行计划
    const filteredActionPlans = computed(() => {
      if (!selectedPriority.value) return allActionPlans.value
      return allActionPlans.value.filter(plan => plan.priority === selectedPriority.value)
    })
    
    // 模拟反馈数据
    const feedbacks = ref([])
    
    // 方法
    const generateInsights = async () => {
      try {
        // 构建生成参数，包含时间范围
        const params = {
          feedback_limit: dataConfig.feedback_limit || 350,
          include_action_plans: dataConfig.include_action_plans,
          filters: {}
        }
        
        // 添加时间范围
        if (dataConfig.date_range && dataConfig.date_range.length === 2) {
          params.filters.date_range = [
            dataConfig.date_range[0].toISOString(),
            dataConfig.date_range[1].toISOString()
          ]
        }
        
        // 添加情感过滤
        if (dataConfig.sentiment_filter && dataConfig.sentiment_filter.length > 0) {
          params.filters.sentiment = dataConfig.sentiment_filter
        }
        
        // 更新配置并生成洞察
        insightsStore.updateGenerationConfig(params)
        message.info('🚀 开始生成常规洞察（月度数据）和全文洞察（历史数据），请稍候...')
        const result = await insightsStore.generateInsights()
        
        if (result && result.generation_type === 'combined') {
          const { standard_insights = 0, full_text_insights = 0 } = insightsStore.stats
          message.success(`🎯 洞察生成成功！总计生成 ${result.total_insights} 个洞察（常规洞察：${standard_insights}个 + 全文洞察：${full_text_insights}个）`)
        } else {
          message.success('洞察生成成功')
        }
        updateFeedbackStats()
      } catch (error) {
        message.error('洞察生成失败')
      }
    }
    
    const getDemo = async () => {
      try {
        await insightsStore.getInsightsDemo()
        message.success('演示数据加载成功')
        updateFeedbackStats()
      } catch (error) {
        message.error('演示数据加载失败')
      }
    }


    
    const refreshFeedbackData = async () => {
      try {
        // 构建API参数，获取更多数据
        const params = {
          limit: dataConfig.feedback_limit || 350,  // 使用配置的数据量或默认350
          // status: 'completed'  // 暂时移除状态过滤，获取所有数据
        }
        
        // 如果有时间范围过滤
        if (dataConfig.date_range && dataConfig.date_range.length === 2) {
          const startDate = new Date(dataConfig.date_range[0])
          const endDate = new Date(dataConfig.date_range[1])
          
          // 确保时间格式正确（YYYY-MM-DD）
          params.start_date = startDate.getFullYear() + '-' + 
            String(startDate.getMonth() + 1).padStart(2, '0') + '-' + 
            String(startDate.getDate()).padStart(2, '0')
          params.end_date = endDate.getFullYear() + '-' + 
            String(endDate.getMonth() + 1).padStart(2, '0') + '-' + 
            String(endDate.getDate()).padStart(2, '0')
          
          console.log('时间范围参数:', { start_date: params.start_date, end_date: params.end_date })
        }
        
        // 如果有情感过滤
        if (dataConfig.sentiment_filter && dataConfig.sentiment_filter.length > 0) {
          params.sentiment = dataConfig.sentiment_filter.join(',')
        }
        
        console.log('正在获取反馈数据，参数:', params)
        const response = await feedbackAPI.getFeedbacks(params)
        
        if (response.data && response.data.data) {
          feedbacks.value = response.data.data.map(item => ({
            id: item.id,
            text: item.original_text || item.processed_text || '内容缺失',
            sentiment: item.sentiment || 'neutral',
            category: item.category || 'general',
            created_at: item.created_at || new Date().toISOString(),
            source: item.source || 'unknown',
            priority: item.priority || 'normal',
            analysis_result: item.analysis_result
          }))
          console.log(`✅ 从数据库获取到 ${feedbacks.value.length} 条反馈数据`)
        } else {
          feedbacks.value = generateMockFeedbacks()
          console.log('📊 API返回空数据，使用演示数据')
        }
        
        updateFeedbackStats()
        message.success(`反馈数据已更新 (${feedbacks.value.length}条)`)
      } catch (error) {
        console.error('获取反馈数据失败:', error)
        feedbacks.value = generateMockFeedbacks()
        updateFeedbackStats()
        message.warning('使用演示数据，请检查网络连接')
      }
    }
    
    const updateDataConfig = () => {
      insightsStore.updateGenerationConfig({
        feedback_limit: dataConfig.feedback_limit,
        include_action_plans: dataConfig.include_action_plans,
        filters: {
          date_range: dataConfig.date_range,
          sentiment: dataConfig.sentiment_filter
        }
      })
      showDataConfig.value = false
      message.success('数据配置已更新')
    }
    
    // 辅助函数
    const getInsightIcon = (type) => {
      const icons = {
        trend: LineChartOutlined,
        pattern: BulbOutlined,
        opportunity: TrophyOutlined,
        risk: ExclamationCircleOutlined
      }
      return icons[type] || BulbOutlined
    }
    
    const getInsightTypeText = (type) => {
      const texts = {
        trend: '趋势分析',
        pattern: '模式识别',
        opportunity: '机会发现',
        risk: '风险预警'
      }
      return texts[type] || '其他洞察'
    }
    
    const getInsightTypeColor = (type) => {
      const colors = {
        trend: '#1890ff',
        pattern: '#722ed1',
        opportunity: '#52c41a',
        risk: '#f5222d'
      }
      return colors[type] || '#666'
    }
    
    const getPriorityColor = (priority) => {
      const colors = {
        P0: 'red',
        P1: 'orange',
        P2: 'blue',
        P3: 'green'
      }
      return colors[priority] || 'default'
    }
    
    const getSentimentPercentage = (sentiment) => {
      const distribution = feedbackStats.sentiment_distribution
      const total = distribution.positive + distribution.negative + distribution.neutral
      if (total === 0) return 0
      return Math.round((distribution[sentiment] / total) * 100)
    }
    
    const getTypePercentage = (count) => {
      const total = allInsights.value.length
      if (total === 0) return 0
      return Math.round((count / total) * 100)
    }
    
    const getInsightCountByType = (type) => {
      if (type === 'all') return allInsights.value.length
      return insightsByType.value[type]?.length || 0
    }
    
    const formatTime = (time) => {
      if (!time) return '暂无'
      return new Date(time).toLocaleString()
    }
    
    const generateMockFeedbacks = () => {
      // 生成覆盖最近一个月的模拟数据
      const feedbackTemplates = [
        '用户界面设计需要优化，当前的导航不够直观',
        '应用启动速度慢，希望能提升性能',
        '功能很实用，但希望增加更多自定义选项',
        '客服响应及时，服务质量很好',
        '支付流程复杂，建议简化操作步骤',
        '新功能很棒，使用体验有明显提升',
        '登录经常超时，影响正常使用',
        '希望增加深色模式支持',
        '数据同步有延迟，需要优化',
        '整体满意，推荐朋友使用',
        '移动端页面显示异常，需要修复',
        '搜索功能反应慢，希望优化',
        '新增的功能非常实用，体验很好',
        '价格有点贵，希望能有更多优惠',
        '界面美观，操作简单，很满意',
        '客服态度很好，解决问题很及时',
        '希望能增加更多个性化设置',
        '数据加载速度需要提升',
        '总体体验不错，会推荐朋友使用',
        '部分功能还需要完善和优化'
      ]
      
      // 生成基于最近一个月的数据，平均每天10-15条
      const currentDate = new Date()
      const oneMonthAgo = new Date()
      oneMonthAgo.setMonth(currentDate.getMonth() - 1)
      
      const totalFeedbacks = 350 // 平均每天约12条
      
      return Array.from({ length: totalFeedbacks }, (_, i) => {
        // 在最近一个月内随机分布时间
        const timeDiff = currentDate.getTime() - oneMonthAgo.getTime()
        const randomTime = oneMonthAgo.getTime() + Math.random() * timeDiff
        
        const feedbackDate = new Date(randomTime)
        const dateString = feedbackDate.getFullYear() + '-' + 
          String(feedbackDate.getMonth() + 1).padStart(2, '0') + '-' + 
          String(feedbackDate.getDate()).padStart(2, '0')
        
        return {
          id: `feedback_${i + 1}`,
          text: feedbackTemplates[i % feedbackTemplates.length] + `（反馈 #${i + 1}）`,
          sentiment: ['positive', 'negative', 'neutral'][i % 3],
          category: ['bug', 'feature', 'performance', 'ui_ux', 'general'][i % 5],
          created_at: dateString,
          source: ['web', 'mobile', 'email', 'phone'][i % 4],
          priority: ['normal', 'high', 'low'][i % 3]
        }
      }).sort((a, b) => new Date(b.created_at) - new Date(a.created_at)) // 按时间倒序排列
    }
    
    const updateFeedbackStats = () => {
      feedbackStats.total_feedback = feedbacks.value.length
      feedbackStats.high_priority_count = Math.floor(feedbacks.value.length * 0.3)
      feedbackStats.sentiment_distribution = {
        positive: feedbacks.value.filter(f => f.sentiment === 'positive').length,
        negative: feedbacks.value.filter(f => f.sentiment === 'negative').length,
        neutral: feedbacks.value.filter(f => f.sentiment === 'neutral').length
      }
    }
    
    // 组件挂载
    onMounted(async () => {
      // 首先尝试加载最新的洞察会话
      try {
        const latestSession = await insightsStore.loadLatestInsights()
        if (latestSession) {
          message.success(`已加载最新洞察会话：${latestSession.title}`)
          console.log('加载了最新洞察会话:', latestSession)
        } else {
          console.log('没有找到历史洞察会话，显示空状态')
        }
      } catch (error) {
        console.warn('加载最新洞察会话失败:', error)
      }
      
      // 然后刷新反馈数据
      refreshFeedbackData()
    })
    
    return {
      isGenerating,
      allInsights,
      allActionPlans,
      insightsByType,
      insightsStats,
      feedbackStats,
      showDataConfig,
      selectedInsightType,
      selectedPriority,
      filteredActionPlans,
      dataConfig,
      generateInsights,
      getDemo,
      refreshFeedbackData,
      updateDataConfig,
      getInsightIcon,
      getInsightTypeText,
      getInsightTypeColor,
      getPriorityColor,
      getSentimentPercentage,
      getTypePercentage,
      getInsightCountByType,
      formatTime
    }
  }
}
</script>

<style scoped>
/* 基础布局 */
.insights-platform {
  padding: 0;
  min-height: 100vh;
  background: linear-gradient(135deg, #e3f2fd 0%, #f3e5f5 50%, #fff3e0 100%);
}

/* 暗黑模式 - 使用正确的选择器 */
.app-dark .insights-platform,
[data-theme="dark"] .insights-platform {
  background: linear-gradient(135deg, #1a1a1a 0%, #2d2d2d 50%, #3a3a3a 100%) !important;
}

.app-dark .data-metric,
[data-theme="dark"] .data-metric {
  background: rgba(40, 40, 40, 0.8) !important;
  border: 1px solid rgba(255, 255, 255, 0.1) !important;
}

.app-dark .metric-value,
[data-theme="dark"] .metric-value {
  color: #40a9ff !important;
}

.app-dark .metric-label,
[data-theme="dark"] .metric-label {
  color: rgba(255, 255, 255, 0.65) !important;
}

.app-dark .filter-label,
[data-theme="dark"] .filter-label {
  color: rgba(255, 255, 255, 0.65) !important;
}

.app-dark .data-filters,
[data-theme="dark"] .data-filters {
  border-top-color: rgba(255, 255, 255, 0.1) !important;
}

.app-dark .data-source-card,
.app-dark .insights-detail-card,
[data-theme="dark"] .data-source-card,
[data-theme="dark"] .insights-detail-card {
  background: rgba(40, 40, 40, 0.8) !important;
  border: 1px solid rgba(255, 255, 255, 0.1) !important;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.3) !important;
}

/* 页面标题栏 */
.page-header {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  padding: 24px 32px;
  margin-bottom: 24px;
}

.header-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
  max-width: 1400px;
  margin: 0 auto;
}

.header-left {
  color: white;
}

.page-title {
  margin: 0;
  font-size: 28px;
  font-weight: 700;
  display: flex;
  align-items: center;
  gap: 12px;
  color: white;
}

.title-icon {
  font-size: 32px;
}

.page-subtitle {
  margin: 8px 0 0 0;
  font-size: 16px;
  opacity: 0.9;
  color: white;
}

.header-actions {
  display: flex;
  gap: 12px;
}

.generate-btn {
  background: linear-gradient(135deg, #ff6b6b 0%, #ee5a52 100%);
  border: none;
  height: 40px;
  font-weight: 600;
}



.demo-btn,
.refresh-btn {
  background: rgba(255, 255, 255, 0.15);
  border: 1px solid rgba(255, 255, 255, 0.25);
  color: white;
  height: 40px;
}

/* 主内容区域 */
.data-source-section,
.insights-analysis-section,
.action-plans-section {
  max-width: 1400px;
  margin: 0 auto 24px auto;
  padding: 0 32px;
}

/* 数据源卡片 */
.data-source-card {
  border-radius: 12px;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.1);
}

.data-overview {
  margin-bottom: 24px;
}

.data-metric {
  text-align: center;
  padding: 20px;
  background: #fafafa;
  border-radius: 8px;
  position: relative;
}

.metric-value {
  font-size: 24px;
  font-weight: 700;
  color: #1890ff;
  margin-bottom: 4px;
}

.metric-label {
  font-size: 14px;
  color: #666;
}

.metric-status {
  position: absolute;
  top: 12px;
  right: 12px;
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #d9d9d9;
}

.metric-status.active {
  background: #52c41a;
}

.metric-status.warning {
  background: #faad14;
}

.metric-status.positive {
  background: #52c41a;
}

.data-filters {
  padding-top: 16px;
  border-top: 1px solid #f0f0f0;
}

.filter-group {
  margin-bottom: 16px;
}

.filter-label {
  display: block;
  margin-bottom: 8px;
  font-weight: 500;
  color: #666;
}

/* 洞察分类统计卡片样式已移除 */

/* 洞察详情卡片 */
.insights-detail-card {
  border-radius: 12px;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.1);
  height: 100%;
}

.insights-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
}

.insights-title {
  font-size: 16px;
  font-weight: 600;
}

.insight-filter-tabs {
  margin: 0;
}

.tab-with-count {
  display: flex;
  align-items: center;
  gap: 8px;
}

.tab-with-count .ant-badge {
  font-size: 12px;
}

.tab-with-count .ant-badge-count {
  background: #1890ff;
  color: white;
  min-width: 20px;
  height: 18px;
  line-height: 18px;
  border-radius: 9px;
  font-size: 11px;
  padding: 0 6px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

/* 暗黑模式下的tab样式 */
[data-theme="dark"] .tab-with-count .ant-badge-count {
  background: #1890ff;
  color: white;
  box-shadow: 0 1px 3px rgba(255, 255, 255, 0.1);
}

/* 行动计划区域 */
.action-plans-card {
  border-radius: 12px;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.1);
}

.plans-count {
  font-size: 14px;
  color: #666;
}

.action-plans-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
  gap: 24px;
  margin-top: 16px;
}

.action-plan-item {
  background: #fafafa;
  border: 1px solid #e6f7ff;
  border-radius: 12px;
  padding: 20px;
  transition: all 0.3s ease;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
}

.action-plan-item:hover {
  border-color: #1890ff;
  background: #f6f8ff;
  transform: translateY(-4px);
  box-shadow: 0 8px 24px rgba(24, 144, 255, 0.15);
}

.plan-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.priority-tag {
  font-weight: 600;
}

.plan-timeline {
  font-size: 12px;
  color: #8c8c8c;
}

.plan-title {
  font-size: 16px;
  font-weight: 600;
  color: #262626;
  margin: 0 0 8px 0;
}

.plan-description {
  font-size: 14px;
  color: #595959;
  line-height: 1.4;
  margin: 0 0 16px 0;
}

.plan-details {
  display: flex;
  justify-content: space-between;
  margin-bottom: 16px;
  padding-top: 16px;
  border-top: 1px solid #f0f0f0;
}

.plan-effort,
.plan-team {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
  color: #8c8c8c;
}

.insight-source {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-top: 12px;
  border-top: 1px solid #f0f0f0;
}

.source-label {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
  color: #1890ff;
  font-weight: 500;
}

/* 空状态 */
.empty-state {
  text-align: center;
  padding: 60px 20px;
  color: #8c8c8c;
}

.empty-icon {
  font-size: 48px;
  margin-bottom: 16px;
}

.empty-text {
  font-size: 16px;
  font-weight: 500;
  margin: 0 0 8px 0;
}

.empty-hint {
  font-size: 14px;
  margin: 0;
}

/* 暗黑模式适配 */
[data-theme="dark"] .insights-platform {
  background: #141414;
}

[data-theme="dark"] .page-header {
  background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
}

[data-theme="dark"] .data-source-card,
[data-theme="dark"] .insights-detail-card,
[data-theme="dark"] .action-plans-card {
  background: #1f1f1f;
  border: 1px solid #333;
}

[data-theme="dark"] .data-metric {
  background: #262626;
}

[data-theme="dark"] .action-plan-item {
  background: #262626;
  border: 1px solid #333;
}

[data-theme="dark"] .action-plan-item:hover {
  background: #1890ff1a;
  border-color: #1890ff;
}

[data-theme="dark"] .insights-title,
[data-theme="dark"] .plan-title {
  color: #ffffff;
}

[data-theme="dark"] .plan-description {
  color: #bfbfbf;
}

[data-theme="dark"] .plan-timeline,
[data-theme="dark"] .plan-effort,
[data-theme="dark"] .plan-team {
  color: #8c8c8c;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .header-content {
    flex-direction: column;
    gap: 16px;
  }
  
  .header-actions {
    width: 100%;
    justify-content: center;
  }
  
  .data-source-section,
  .insights-analysis-section,
  .action-plans-section {
    padding: 0 16px;
  }
  
  .action-plans-grid {
    grid-template-columns: 1fr;
  }
}
</style> 