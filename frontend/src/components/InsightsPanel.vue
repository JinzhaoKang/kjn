<template>
  <div class="insights-panel">
    <!-- 洞察标题栏 -->
    <div class="insights-header">
      <h3 class="insights-title">
        <BulbOutlined class="title-icon" />
        智能洞察
      </h3>
      <div class="insights-actions">
        <a-button 
          type="primary" 
          size="small" 
          @click="generateInsights"
          :loading="isGenerating"
        >
          <RiseOutlined />
          生成洞察
        </a-button>
        <a-button 
          size="small" 
          @click="getDemo"
          :loading="isGenerating"
        >
          演示
        </a-button>
        <a-button 
          size="small" 
          @click="clearInsights"
          :disabled="!hasInsights"
        >
          清空
        </a-button>
      </div>
    </div>

    <!-- 错误提示 -->
    <div v-if="hasError" class="error-alert">
      <a-alert 
        :message="lastError" 
        type="error" 
        show-icon 
        closable 
        @close="clearError"
      />
    </div>

    <!-- 生成中状态 -->
    <div v-if="isGenerating" class="generating-state">
      <a-spin size="large">
        <template #indicator>
          <LoadingOutlined style="font-size: 24px; color: #1890ff" />
        </template>
      </a-spin>
      <div class="generating-text">正在生成洞察...</div>
    </div>

    <!-- 洞察内容 -->
    <div v-else-if="hasInsights" class="insights-content">
      <!-- 洞察列表 -->
      <div class="insights-section">
        <h4 class="section-title">
          <EyeOutlined />
          洞察分析
        </h4>
        <div class="insights-list">
          <div 
            v-for="(insight, index) in insights" 
            :key="index"
            class="insight-item"
            :class="[
              `insight-${insight.insight_type}`,
              { 'full-text-insight': insight.is_full_text }
            ]"
          >
            <!-- 洞察来源标记 -->
            <div v-if="insight.is_full_text" class="full-text-badge">
              <div class="badge-content">
                <span class="badge-icon">🧠</span>
                <span class="badge-text">全文洞察</span>
              </div>
              <div class="badge-description">基于所有历史数据·1M上下文分析</div>
            </div>
            <div v-else class="regular-insight-badge">
              <div class="badge-content">
                <span class="badge-icon">📊</span>
                <span class="badge-text">月度洞察</span>
              </div>
              <div class="badge-description">基于最近一个月数据</div>
            </div>
            
            <div class="insight-header">
              <div class="insight-type">
                <component :is="getInsightIcon(insight.insight_type)" />
                {{ getInsightTypeText(insight.insight_type) }}
              </div>
              <div class="insight-confidence">
                <a-progress 
                  :percent="Math.round(insight.confidence_score * 100)"
                  size="small"
                  :stroke-color="getConfidenceColor(insight.confidence_score)"
                />
              </div>
            </div>
            <div class="insight-title">{{ insight.title }}</div>
            <div class="insight-description">
              <vue-markdown-render :source="insight.description" />
            </div>
            <div class="insight-meta">
              <a-tag :color="getImpactColor(insight.impact_level)">
                {{ getImpactText(insight.impact_level) }}
              </a-tag>
              <span class="insight-segments">
                影响用户: {{ insight.affected_user_segments?.join(', ') || '所有用户' }}
              </span>
            </div>
          </div>
        </div>
      </div>

      <!-- 执行计划 -->
      <div class="action-plans-section">
        <h4 class="section-title">
          <CheckCircleOutlined />
          执行计划
        </h4>
        <div class="action-plans-list">
          <div 
            v-for="(plan, index) in actionPlans" 
            :key="index"
            class="action-plan-item"
            :class="`priority-${plan.priority}`"
          >
            <div class="plan-header">
              <div class="plan-priority">
                <a-tag :color="getPriorityColor(plan.priority)">
                  {{ plan.priority }}
                </a-tag>
              </div>
              <div class="plan-effort">
                <ClockCircleOutlined />
                {{ plan.estimated_effort }}
              </div>
            </div>
            <div class="plan-title">{{ plan.title }}</div>
            <div class="plan-summary">{{ plan.summary }}</div>
            <div class="plan-meta">
              <div class="plan-owner">
                <UserOutlined />
                {{ plan.owner_team }}
              </div>
              <div class="plan-timeline">
                <CalendarOutlined />
                {{ plan.timeline }}
              </div>
            </div>
            <div class="plan-metrics">
              <div class="metrics-title">成功指标:</div>
              <div class="metrics-list">
                <a-tag 
                  v-for="metric in plan.success_metrics" 
                  :key="metric"
                  color="blue"
                >
                  {{ metric }}
                </a-tag>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 空状态 -->
    <div v-else class="empty-state">
      <a-empty description="暂无洞察数据">
        <template #image>
          <BulbOutlined style="font-size: 48px; color: #d9d9d9" />
        </template>
        <a-button type="primary" @click="generateInsights">
          生成洞察
        </a-button>
      </a-empty>
    </div>
  </div>
</template>

<script>
import { computed, onMounted } from 'vue'
import { message } from 'ant-design-vue'
import { useInsightsStore } from '@/stores/insights'
import {
  BulbOutlined,
  RiseOutlined,
  EyeOutlined,
  CheckCircleOutlined,
  LoadingOutlined,
  ClockCircleOutlined,
  UserOutlined,
  CalendarOutlined,
  TrophyOutlined,
  ExclamationCircleOutlined,
  LineChartOutlined,
  SearchOutlined
} from '@ant-design/icons-vue'
import VueMarkdownRender from 'vue-markdown-render'

export default {
  name: 'InsightsPanel',
  props: {
    filteredType: {
      type: String,
      default: 'all',
      description: '过滤的洞察类型'
    }
  },
  components: {
    BulbOutlined,
    RiseOutlined,
    EyeOutlined,
    CheckCircleOutlined,
    LoadingOutlined,
    ClockCircleOutlined,
    UserOutlined,
    CalendarOutlined,
    TrophyOutlined,
    ExclamationCircleOutlined,
    LineChartOutlined,
    SearchOutlined,
    VueMarkdownRender
  },
  setup(props) {
    const insightsStore = useInsightsStore()
    
    // 计算属性
    const isGenerating = computed(() => insightsStore.isGenerating)
    const hasError = computed(() => insightsStore.hasError)
    const lastError = computed(() => insightsStore.lastError)
    const actionPlans = computed(() => insightsStore.allActionPlans)
    
    // 过滤后的洞察
    const insights = computed(() => {
      const allInsights = insightsStore.allInsights
      if (props.filteredType === 'all') {
        return allInsights
      }
      return allInsights.filter(insight => insight.insight_type === props.filteredType)
    })
    
    // 是否有洞察（基于过滤后的结果）
    const hasInsights = computed(() => insights.value.length > 0)
    
    // 方法
    const generateInsights = async () => {
      try {
        await insightsStore.generateInsights()
        message.success('洞察生成成功')
      } catch (error) {
        message.error('洞察生成失败')
      }
    }
    
    const getDemo = async () => {
      try {
        await insightsStore.getInsightsDemo()
        message.success('演示数据加载成功')
      } catch (error) {
        message.error('演示数据加载失败')
      }
    }
    
    const clearInsights = () => {
      insightsStore.clearInsights()
      message.info('洞察已清空')
    }
    
    const clearError = () => {
      insightsStore.error = null
    }
    
    // 辅助函数
    const getInsightIcon = (type) => {
      const icons = {
        trend: LineChartOutlined,
        pattern: SearchOutlined,
        opportunity: TrophyOutlined,
        risk: ExclamationCircleOutlined
      }
      return icons[type] || EyeOutlined
    }
    
    const getInsightTypeText = (type) => {
      const texts = {
        trend: '趋势',
        pattern: '模式',
        opportunity: '机会',
        risk: '风险'
      }
      return texts[type] || '洞察'
    }
    
    const getConfidenceColor = (score) => {
      if (score >= 0.8) return '#52c41a'
      if (score >= 0.6) return '#faad14'
      return '#ff4d4f'
    }
    
    const getImpactColor = (level) => {
      const colors = {
        high: 'red',
        medium: 'orange',
        low: 'blue'
      }
      return colors[level] || 'default'
    }
    
    const getImpactText = (level) => {
      const texts = {
        high: '高影响',
        medium: '中影响',
        low: '低影响'
      }
      return texts[level] || level
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
    
    // 组件挂载时检查健康状态
    onMounted(async () => {
      try {
        await insightsStore.checkInsightsHealth()
      } catch (error) {
        console.warn('洞察服务健康检查失败:', error)
      }
    })
    
    return {
      isGenerating,
      hasInsights,
      hasError,
      lastError,
      insights,
      actionPlans,
      generateInsights,
      getDemo,
      clearInsights,
      clearError,
      getInsightIcon,
      getInsightTypeText,
      getConfidenceColor,
      getImpactColor,
      getImpactText,
      getPriorityColor
    }
  }
}
</script>

<style scoped>
.insights-panel {
  border-radius: 8px;
  overflow: hidden;
}

.insights-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
}

.insights-title {
  display: flex;
  align-items: center;
  margin: 0;
  font-size: 16px;
  font-weight: 600;
}

.title-icon {
  margin-right: 8px;
  font-size: 18px;
}

.insights-actions {
  display: flex;
  gap: 8px;
}

.error-alert {
  margin: 16px 20px;
}

.generating-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 40px 20px;
}

.generating-text {
  margin-top: 16px;
  color: var(--ant-color-text-secondary);
  font-size: 14px;
}

.insights-content {
  padding: 20px;
  background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
  min-height: calc(100vh - 200px);
  border-radius: 0 0 16px 16px;
}

.section-title {
  display: flex;
  align-items: center;
  margin: 0 0 16px 0;
  font-size: 14px;
  font-weight: 600;
  color: var(--ant-color-text);
}

.section-title .anticon {
  margin-right: 8px;
  color: var(--ant-color-primary);
}

.insights-list {
  /* 瀑布流布局 */
  columns: 2;
  column-gap: 16px;
  margin-bottom: 24px;
}

.insight-item {
  break-inside: avoid;
  margin-bottom: 16px;
  padding: 20px;
  border: 1px solid var(--ant-color-border);
  border-radius: 16px;
  background: var(--ant-color-bg-container);
  backdrop-filter: blur(10px);
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
  position: relative;
  overflow: hidden;
}

.insight-item::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: var(--ant-color-bg-container);
  opacity: 0.95;
  z-index: -1;
}

.insight-item:hover {
  box-shadow: 0 8px 30px rgba(0, 0, 0, 0.15);
  border-color: var(--ant-color-primary);
  transform: translateY(-4px) scale(1.02);
}

/* 全文洞察特殊样式 */
.full-text-insight {
  background: linear-gradient(135deg, rgba(34, 193, 195, 0.1) 0%, rgba(253, 187, 45, 0.1) 100%);
  border: 2px solid transparent;
  background-clip: padding-box;
  box-shadow: 0 6px 25px rgba(34, 193, 195, 0.2);
}

.full-text-insight::before {
  background: linear-gradient(135deg, rgba(34, 193, 195, 0.05) 0%, rgba(253, 187, 45, 0.05) 100%);
}

.full-text-badge {
  position: absolute;
  top: -2px;
  right: -2px;
  background: linear-gradient(135deg, #22c1c3 0%, #fdbb2d 100%);
  color: white;
  padding: 8px 12px;
  border-radius: 0 14px 0 16px;
  font-size: 11px;
  font-weight: 600;
  text-align: center;
  box-shadow: 0 4px 12px rgba(34, 193, 195, 0.3);
  z-index: 10;
}

.badge-content {
  display: flex;
  align-items: center;
  gap: 4px;
  margin-bottom: 2px;
}

.badge-icon {
  font-size: 12px;
}

.badge-text {
  font-size: 10px;
  font-weight: 700;
  letter-spacing: 0.5px;
}

.badge-description {
  font-size: 8px;
  opacity: 0.9;
  font-weight: 500;
}

/* 常规洞察标记样式 */
.regular-insight-badge {
  position: absolute;
  top: -2px;
  right: -2px;
  background: linear-gradient(135deg, #1890ff 0%, #722ed1 100%);
  color: white;
  padding: 8px 12px;
  border-radius: 0 14px 0 16px;
  font-size: 11px;
  font-weight: 600;
  text-align: center;
  box-shadow: 0 4px 12px rgba(24, 144, 255, 0.3);
  z-index: 10;
}

.regular-insight-badge .badge-content {
  display: flex;
  align-items: center;
  gap: 4px;
  margin-bottom: 2px;
}

.regular-insight-badge .badge-icon {
  font-size: 12px;
}

.regular-insight-badge .badge-text {
  font-size: 10px;
  font-weight: 700;
  letter-spacing: 0.5px;
}

.regular-insight-badge .badge-description {
  font-size: 8px;
  opacity: 0.9;
  font-weight: 500;
}

/* 洞察类型颜色条 */
.insight-item.insight-risk {
  border-left: 5px solid #ff4d4f;
}

.insight-item.insight-opportunity {
  border-left: 5px solid #52c41a;
}

.insight-item.insight-trend {
  border-left: 5px solid #1890ff;
}

.insight-item.insight-pattern {
  border-left: 5px solid #722ed1;
}

.insight-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.insight-type {
  display: flex;
  align-items: center;
  font-size: 12px;
  color: var(--ant-color-text-secondary);
  font-weight: 500;
}

.insight-type .anticon {
  margin-right: 4px;
}

.insight-confidence {
  width: 60px;
}

.insight-title {
  font-size: 16px;
  font-weight: 600;
  color: var(--ant-color-text);
  margin-bottom: 8px;
}

.insight-description {
  color: var(--ant-color-text-secondary);
  font-size: 14px;
  line-height: 1.5;
  margin-bottom: 12px;
}

.insight-meta {
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: 12px;
  color: var(--ant-color-text-tertiary);
}

.insight-segments {
  color: var(--ant-color-text-secondary);
}

.action-plans-list {
  /* 瀑布流布局 */
  columns: 2;
  column-gap: 16px;
}

.action-plan-item {
  break-inside: avoid;
  margin-bottom: 16px;
  padding: 20px;
  border: 1px solid var(--ant-color-border);
  border-radius: 16px;
  background: var(--ant-color-bg-container);
  backdrop-filter: blur(10px);
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
  position: relative;
  overflow: hidden;
  min-height: 200px; /* 设置最小高度确保卡片美观 */
}

.action-plan-item::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: var(--ant-color-bg-container);
  opacity: 0.95;
  z-index: -1;
}

.action-plan-item:hover {
  box-shadow: 0 8px 30px rgba(0, 0, 0, 0.15);
  border-color: var(--ant-color-primary);
  transform: translateY(-4px) scale(1.02);
}

.action-plan-item.priority-P0 {
  border-left: 5px solid #ff4d4f;
}

.action-plan-item.priority-P1 {
  border-left: 5px solid #faad14;
}

.action-plan-item.priority-P2 {
  border-left: 5px solid #1890ff;
}

.action-plan-item.priority-P3 {
  border-left: 5px solid #52c41a;
}

.plan-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.plan-effort {
  display: flex;
  align-items: center;
  font-size: 12px;
  color: var(--ant-color-text-secondary);
}

.plan-effort .anticon {
  margin-right: 4px;
}

.plan-title {
  font-size: 16px;
  font-weight: 600;
  color: var(--ant-color-text);
  margin-bottom: 8px;
}

.plan-summary {
  color: var(--ant-color-text-secondary);
  font-size: 14px;
  line-height: 1.5;
  margin-bottom: 12px;
}

.plan-meta {
  display: flex;
  gap: 16px;
  margin-bottom: 12px;
  font-size: 12px;
  color: var(--ant-color-text-secondary);
}

.plan-owner,
.plan-timeline {
  display: flex;
  align-items: center;
}

.plan-owner .anticon,
.plan-timeline .anticon {
  margin-right: 4px;
}

.plan-metrics {
  margin-top: 12px;
}

.metrics-title {
  font-size: 12px;
  color: var(--ant-color-text-secondary);
  margin-bottom: 8px;
}

.metrics-list {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
}

.empty-state {
  padding: 40px 20px;
  text-align: center;
}

/* 暗黑模式特殊处理 - 使用正确的选择器 */
.app-dark .insights-content,
[data-theme="dark"] .insights-content {
  background: linear-gradient(135deg, #1f1f1f 0%, #2d2d2d 100%) !important;
}

.app-dark .insight-item,
.app-dark .action-plan-item,
[data-theme="dark"] .insight-item,
[data-theme="dark"] .action-plan-item {
  background: rgba(40, 40, 40, 0.95) !important;
  border-color: rgba(255, 255, 255, 0.15) !important;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.4) !important;
  color: rgba(255, 255, 255, 0.85) !important;
}

.app-dark .insight-item::before,
.app-dark .action-plan-item::before,
[data-theme="dark"] .insight-item::before,
[data-theme="dark"] .action-plan-item::before {
  background: rgba(40, 40, 40, 0.95) !important;
}

.app-dark .insight-item:hover,
.app-dark .action-plan-item:hover,
[data-theme="dark"] .insight-item:hover,
[data-theme="dark"] .action-plan-item:hover {
  background: rgba(50, 50, 50, 0.95) !important;
  box-shadow: 0 8px 30px rgba(255, 255, 255, 0.2) !important;
  border-color: rgba(255, 255, 255, 0.4) !important;
}

/* 暗黑模式全文洞察特殊样式 */
.app-dark .full-text-insight,
[data-theme="dark"] .full-text-insight {
  background: linear-gradient(135deg, rgba(34, 193, 195, 0.25) 0%, rgba(253, 187, 45, 0.25) 100%) !important;
  border-color: rgba(34, 193, 195, 0.6) !important;
  box-shadow: 0 6px 25px rgba(34, 193, 195, 0.3) !important;
}

.app-dark .full-text-insight::before,
[data-theme="dark"] .full-text-insight::before {
  background: linear-gradient(135deg, rgba(34, 193, 195, 0.15) 0%, rgba(253, 187, 45, 0.15) 100%) !important;
}

.app-dark .full-text-insight:hover,
[data-theme="dark"] .full-text-insight:hover {
  background: linear-gradient(135deg, rgba(34, 193, 195, 0.35) 0%, rgba(253, 187, 45, 0.35) 100%) !important;
  box-shadow: 0 8px 30px rgba(34, 193, 195, 0.4) !important;
  border-color: rgba(34, 193, 195, 0.8) !important;
}

/* 暗黑模式文字颜色调整 */
.app-dark .insight-title,
.app-dark .plan-title,
[data-theme="dark"] .insight-title,
[data-theme="dark"] .plan-title {
  color: rgba(255, 255, 255, 0.9) !important;
}

.app-dark .insight-description,
.app-dark .plan-summary,
[data-theme="dark"] .insight-description,
[data-theme="dark"] .plan-summary {
  color: rgba(255, 255, 255, 0.7) !important;
}

.app-dark .insight-type,
.app-dark .plan-effort,
[data-theme="dark"] .insight-type,
[data-theme="dark"] .plan-effort {
  color: rgba(255, 255, 255, 0.6) !important;
}

.app-dark .insight-meta,
.app-dark .plan-meta,
[data-theme="dark"] .insight-meta,
[data-theme="dark"] .plan-meta {
  color: rgba(255, 255, 255, 0.5) !important;
}

.app-dark .insight-segments,
[data-theme="dark"] .insight-segments {
  color: rgba(255, 255, 255, 0.6) !important;
}

.app-dark .metrics-title,
[data-theme="dark"] .metrics-title {
  color: rgba(255, 255, 255, 0.6) !important;
}

/* 响应式设计 */
@media (max-width: 1200px) {
  .insights-list,
  .action-plans-list {
    columns: 2;
  }
}

@media (max-width: 768px) {
  .insights-content {
    padding: 16px;
  }
  
  .insights-list,
  .action-plans-list {
    columns: 1;
    column-gap: 0;
  }
  
  .insight-item,
  .action-plan-item {
    padding: 16px;
    margin-bottom: 12px;
  }
  
  .plan-meta {
    flex-direction: column;
    gap: 8px;
  }
  
  .insight-header,
  .plan-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 8px;
  }
  
  .full-text-badge,
  .regular-insight-badge {
    padding: 6px 10px;
    font-size: 10px;
  }
  
  .full-text-badge .badge-text,
  .regular-insight-badge .badge-text {
    font-size: 9px;
  }
  
  .full-text-badge .badge-description,
  .regular-insight-badge .badge-description {
    font-size: 7px;
  }
}

/* 超大屏幕可以显示更多列 */
@media (min-width: 1400px) {
  .insights-list,
  .action-plans-list {
    columns: 3;
  }
}

@media (min-width: 1800px) {
  .insights-list,
  .action-plans-list {
    columns: 4;
  }
}
</style> 