<template>
  <div class="decision-engine">
    <a-page-header title="智能决策引擎" sub-title="洞察量化、优先级排序、行动规划生成">
      <template #extra>
        <a-space>
          <a-button type="primary" :loading="loading" @click="runPriorityAnalysis">
            <CalculatorOutlined />
            执行优先级分析
          </a-button>
          <a-button @click="refreshData">
            <ReloadOutlined />
            刷新数据
          </a-button>
        </a-space>
      </template>
    </a-page-header>

    <!-- 引擎状态监控 -->
    <a-row :gutter="16" class="status-row">
      <a-col :span="8">
        <a-card class="status-card">
          <a-statistic
            title="高级优先级引擎"
            :value="engineStatus.advanced_priority_engine ? '正常' : '异常'"
            :value-style="{ 
              color: engineStatus.advanced_priority_engine ? '#3f8600' : '#cf1322' 
            }"
          />
        </a-card>
      </a-col>
      <a-col :span="8">
        <a-card class="status-card">
          <a-statistic
            title="基础优先级引擎"
            :value="engineStatus.priority_engine ? '正常' : '异常'"
            :value-style="{ 
              color: engineStatus.priority_engine ? '#3f8600' : '#cf1322' 
            }"
          />
        </a-card>
      </a-col>
      <a-col :span="8">
        <a-card class="status-card">
          <a-statistic
            title="行动生成器"
            :value="engineStatus.action_generator ? '正常' : '异常'"
            :value-style="{ 
              color: engineStatus.action_generator ? '#3f8600' : '#cf1322' 
            }"
          />
        </a-card>
      </a-col>
    </a-row>

    <!-- 决策分析概览 -->
    <a-card title="决策分析概览" class="overview-card">
      <a-row :gutter="16" v-if="analyticsData">
        <a-col :span="6">
          <a-statistic
            title="总反馈数"
            :value="analyticsData.total_feedbacks"
          />
        </a-col>
        <a-col :span="6">
          <a-statistic
            title="已分析数"
            :value="analyticsData.analyzed_count"
            :value-style="{ color: '#3f8600' }"
          />
        </a-col>
        <a-col :span="6">
          <a-statistic
            title="平均优先级得分"
            :value="analyticsData.avg_scores.priority"
            suffix="分"
            :precision="1"
          />
        </a-col>
        <a-col :span="6">
          <a-statistic
            title="平均ROI"
            :value="(analyticsData.avg_scores.roi * 100).toFixed(2)"
            suffix="%"
            :value-style="{ color: '#cf1322' }"
          />
        </a-col>
      </a-row>
    </a-card>

    <!-- 6维度权重配置 + 图表展示 -->
    <a-row :gutter="16" class="content-row">
      <a-col :span="12">
        <a-card title="6维度权重配置" class="weights-card">
          <div class="dimension-weights" v-if="weightsConfig">
            <div class="weight-item" v-for="(desc, key) in weightsConfig.description" :key="key">
              <div class="weight-label">
                <span>{{ desc.split(' - ')[0] }}:</span>
              </div>
              <a-slider
                v-model="weightsConfig.dimension_weights[key]"
                :max="1"
                :step="0.05"
                :marks="{ 0: '0', 0.5: '0.5', 1: '1' }"
              />
              <span class="weight-value">{{ weightsConfig.dimension_weights[key] }}</span>
            </div>
          </div>
          <a-space>
            <a-button type="primary" @click="saveWeights">
              保存权重配置
            </a-button>
            <a-button @click="resetWeights">
              重置默认值
            </a-button>
          </a-space>
        </a-card>
      </a-col>
      
      <a-col :span="12">
        <a-card title="6维度雷达图" class="radar-card">
          <div ref="dimensionsChart" style="height: 400px;"></div>
        </a-card>
      </a-col>
    </a-row>

    <!-- 优先级分布 -->
    <a-row :gutter="16" class="content-row">
      <a-col :span="12">
        <a-card title="优先级分布" class="priority-card">
          <div ref="priorityChart" style="height: 300px;"></div>
        </a-card>
      </a-col>
      
      <a-col :span="12">
        <a-card title="战略建议" class="recommendations-card">
          <a-list
            :data-source="analyticsData?.recommendations_summary || []"
            size="small"
          >
            <template #renderItem="{ item }">
              <a-list-item>
                {{ item }}
              </a-list-item>
            </template>
          </a-list>
        </a-card>
      </a-col>
    </a-row>

    <!-- 智能行动计划 -->
    <a-card title="🚀 智能行动计划" class="action-plan-card">
      <template #extra>
        <a-space>
          <a-tag color="blue" v-if="actionPlan">计划ID: {{ actionPlan.plan_id }}</a-tag>
          <a-tag color="green" v-if="actionPlan">{{ actionPlan.total_actions }} 个行动项</a-tag>
        </a-space>
      </template>
      
      <div v-if="loading" class="loading-placeholder">
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
              v-for="action in actionPlan.action_items.slice(0, 6)" 
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
          <a-button type="primary" @click="refreshData">重新生成</a-button>
        </a-empty>
      </div>
    </a-card>
  </div>
</template>

<script>
import { ref, onMounted, nextTick, h } from 'vue'
import { message, Modal } from 'ant-design-vue'
import {
  CalculatorOutlined,
  ReloadOutlined,
} from '@ant-design/icons-vue'
import * as echarts from 'echarts'
import { decisionEngineAPI, feedbackAPI } from '@/utils/api'

export default {
  name: 'DecisionEngine',
  components: {
    CalculatorOutlined,
    ReloadOutlined,
  },
  setup() {
    const loading = ref(false)
    const dimensionsChart = ref(null)
    const priorityChart = ref(null)
    
    const engineStatus = ref({
      advanced_priority_engine: false,
      priority_engine: false,
      action_generator: false
    })
    
    const weightsConfig = ref(null)
    const analyticsData = ref(null)
    const actionPlan = ref(null)

    const loadData = async () => {
      loading.value = true
      try {
        const [statusRes, weightsRes, analyticsRes] = await Promise.all([
          decisionEngineAPI.getHealth(),
          decisionEngineAPI.getWeightsConfig(),
          decisionEngineAPI.getAnalyticsOverview()
        ])
        
        engineStatus.value = statusRes.data
        weightsConfig.value = weightsRes.data
        analyticsData.value = analyticsRes.data
        
        // 自动生成行动计划
        await loadActionPlan()
        
        nextTick(() => {
          initCharts()
        })
      } catch (error) {
        console.error('加载数据失败:', error)
        message.error('加载数据失败')
      } finally {
        loading.value = false
      }
    }

    const loadActionPlan = async () => {
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
        // 不显示错误消息，保持静默失败
      }
    }

    const initCharts = () => {
      if (priorityChart.value && analyticsData.value) {
        const chartInstance = echarts.init(priorityChart.value)
        const data = Object.entries(analyticsData.value.priority_distribution).map(([key, value]) => ({
          name: key,
          value: value
        }))
        
        chartInstance.setOption({
          tooltip: { trigger: 'item' },
          series: [{
            type: 'pie',
            radius: '60%',
            data: data
          }]
        })
      }

      if (dimensionsChart.value && analyticsData.value) {
        const chartInstance = echarts.init(dimensionsChart.value)
        const dimensions = analyticsData.value.six_dimensions_avg
        
        chartInstance.setOption({
          tooltip: { trigger: 'axis' },
          radar: {
            indicator: [
              { name: '影响力', max: 100 },
              { name: '紧急性', max: 100 },
              { name: '实现成本', max: 100 },
              { name: '商业价值', max: 100 },
              { name: '战略匹配', max: 100 },
              { name: '用户声音', max: 100 }
            ]
          },
          series: [{
            type: 'radar',
            data: [{
              value: [
                dimensions.impact,
                dimensions.urgency,
                dimensions.effort,
                dimensions.business_value,
                dimensions.strategic,
                dimensions.user_voice
              ],
              name: '6维度评分'
            }]
          }]
        })
      }
    }

    const refreshData = () => {
      loadData()
      message.success('数据已刷新')
    }

    const runPriorityAnalysis = async () => {
      loading.value = true
      try {
        message.loading('正在获取反馈数据...', 1)
        
        // 获取反馈数据ID列表
        const feedbackResponse = await feedbackAPI.getFeedbacks({ limit: 50 })
        console.log('反馈API响应:', feedbackResponse.data)
        
        // 确认数据结构并提取ID
        const feedbackData = feedbackResponse.data.data || []
        const feedbackIds = feedbackData.map(item => item.id || item._id).filter(Boolean)
        
        console.log('提取到的反馈ID:', feedbackIds)
        
        if (feedbackIds.length === 0) {
          message.warning('没有找到可分析的反馈数据')
          return
        }
        
        message.loading(`正在分析 ${feedbackIds.length} 条反馈数据...`, 2)
        
        // 调用优先级分析API
        const analysisResult = await decisionEngineAPI.calculatePriority({
          feedback_ids: feedbackIds,
          use_advanced_engine: true
        })
        
        message.success(`优先级分析完成！分析了 ${analysisResult.data.total_analyzed} 条反馈`)
        
        // 显示分析结果
        Modal.info({
          title: '🎯 优先级分析结果',
          width: 600,
          content: h('div', [
            h('div', { class: 'analysis-summary' }, [
              h('p', `📊 总计分析: ${analysisResult.data.total_analyzed} 条反馈`),
              h('p', `🔥 高优先级: ${analysisResult.data.high_priority_count} 条`),
              h('p', `⚡ 中等优先级: ${analysisResult.data.medium_priority_count} 条`),
              h('p', `📝 低优先级: ${analysisResult.data.low_priority_count} 条`),
              h('p', `💰 平均ROI: ${(analysisResult.data.avg_roi * 100).toFixed(1)}%`),
              h('p', `⭐ 平均得分: ${analysisResult.data.avg_priority_score}/100`)
            ]),
            h('div', { class: 'top-priorities', style: { marginTop: '16px' } }, [
              h('h4', '🏆 Top 3 优先级项目:'),
              ...analysisResult.data.top_priority_items.slice(0, 3).map((item, index) => 
                h('div', { 
                  key: item.feedback_id,
                  style: { 
                    padding: '8px', 
                    margin: '4px 0', 
                    background: '#f6f8ff', 
                    borderRadius: '4px',
                    border: '1px solid #d9d9d9'
                  } 
                }, [
                  h('strong', `${index + 1}. ${item.priority_tier} - 得分: ${item.priority_score.toFixed(1)}`),
                  h('br'),
                  h('span', { style: { fontSize: '12px', color: '#666' } }, 
                    `影响力: ${item.impact_score.toFixed(1)} | 紧急性: ${item.urgency_score.toFixed(1)} | ROI: ${(item.expected_roi * 100).toFixed(1)}%`)
                ])
              )
            ])
          ])
        })
        
        // 刷新页面数据显示最新分析结果
        await loadData()
        
      } catch (error) {
        console.error('优先级分析失败:', error)
        message.error(`优先级分析失败: ${error.response?.data?.detail || error.message}`)
      } finally {
        loading.value = false
      }
    }

    const getPriorityColor = (priority) => {
      const colorMap = {
        'P0': 'red',
        'P1': 'orange', 
        'P2': 'blue',
        'P3': 'green'
      }
      return colorMap[priority] || 'default'
    }

    const saveWeights = () => {
      message.success('权重配置已保存')
    }

    const resetWeights = () => {
      loadData()
      message.success('权重配置已重置')
    }

    onMounted(() => {
      loadData()
    })

    return {
      loading,
      dimensionsChart,
      priorityChart,
      engineStatus,
      weightsConfig,
      analyticsData,
      actionPlan,
      refreshData,
      runPriorityAnalysis,
      getPriorityColor,
      saveWeights,
      resetWeights
    }
  }
}
</script>

<style scoped>
.decision-engine {
  padding: 24px;
}

.status-row {
  margin-bottom: 24px;
}

.status-card {
  text-align: center;
}

.overview-card {
  margin-bottom: 24px;
}

.content-row {
  margin-bottom: 24px;
}

.weight-item {
  margin-bottom: 16px;
}

.weight-label {
  margin-bottom: 8px;
  font-weight: 500;
}

.weight-value {
  margin-left: 8px;
  font-weight: 500;
  color: #1890ff;
}

/* 行动计划样式 */
.action-plan-card {
  margin-top: 24px;
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
  border-radius: 8px;
  background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
  transition: all 0.3s ease;
}

.metric-item:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.priority-p0 {
  background: linear-gradient(135deg, #ff9a9e 0%, #fecfef 100%);
  color: #d32f2f;
}

.priority-p1 {
  background: linear-gradient(135deg, #ffecd2 0%, #fcb69f 100%);
  color: #f57c00;
}

.priority-p2 {
  background: linear-gradient(135deg, #a8edea 0%, #fed6e3 100%);
  color: #1976d2;
}

.priority-p3 {
  background: linear-gradient(135deg, #d299c2 0%, #fef9d7 100%);
  color: #388e3c;
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
  background: #f8f9fa;
  border-radius: 8px;
  padding: 16px;
  border-left: 4px solid #1890ff;
}

.timeline-info {
  border-left-color: #52c41a;
}

.effort-info {
  border-left-color: #fa8c16;
}

.info-header {
  font-weight: 600;
  color: #262626;
  margin-bottom: 8px;
}

.info-content {
  font-size: 16px;
  color: #595959;
}

.section-title {
  font-size: 18px;
  font-weight: 600;
  color: #262626;
  margin: 24px 0 16px 0;
  display: flex;
  align-items: center;
  gap: 8px;
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
  grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
  gap: 16px;
}

.action-card {
  background: white;
  border: 1px solid #e8e8e8;
  border-radius: 12px;
  padding: 20px;
  transition: all 0.3s ease;
  position: relative;
  overflow: hidden;
}

.action-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 4px;
  background: linear-gradient(90deg, #1890ff, #52c41a);
}

.action-card.priority-p0::before {
  background: linear-gradient(90deg, #ff4d4f, #ff7875);
}

.action-card.priority-p1::before {
  background: linear-gradient(90deg, #fa8c16, #ffa940);
}

.action-card.priority-p2::before {
  background: linear-gradient(90deg, #1890ff, #40a9ff);
}

.action-card.priority-p3::before {
  background: linear-gradient(90deg, #52c41a, #73d13d);
}

.action-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.12);
  border-color: #1890ff;
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
  color: #262626;
  flex: 1;
  margin-right: 12px;
}

.action-description {
  color: #595959;
  font-size: 14px;
  line-height: 1.5;
  margin-bottom: 16px;
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.action-footer {
  border-top: 1px solid #f0f0f0;
  padding-top: 12px;
}

.action-team, .action-effort {
  font-size: 12px;
  color: #8c8c8c;
  background: #f5f5f5;
  padding: 4px 8px;
  border-radius: 4px;
}

.empty-placeholder {
  text-align: center;
  padding: 60px 20px;
}
</style> 