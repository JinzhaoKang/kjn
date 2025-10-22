import { defineStore } from 'pinia'
import { insightsAPI } from '@/utils/api'

export const useInsightsStore = defineStore('insights', {
  state: () => ({
    // 洞察生成状态
    insightsStatus: 'idle', // idle, generating, completed, error
    insights: [],
    
    // 执行计划状态
    actionPlans: [],
    
    // 生成配置
    generationConfig: {
      feedback_limit: 50,
      include_action_plans: true,
      filters: {}
    },
    
    // 统计信息
    stats: {
      total_insights: 0,
      insights_by_type: {},
      action_plans_by_priority: {},
      last_generation_time: null
    },
    
    // 错误信息
    error: null
  }),
  
  getters: {
    // 洞察状态
    isGenerating: (state) => state.insightsStatus === 'generating',
    isCompleted: (state) => state.insightsStatus === 'completed',
    hasError: (state) => state.insightsStatus === 'error',
    
    // 洞察数据
    allInsights: (state) => state.insights,
    allActionPlans: (state) => state.actionPlans,
    
    // 按类型分组的洞察
    insightsByType: (state) => {
      const grouped = {}
      state.insights.forEach(insight => {
        const type = insight.insight_type || 'general'
        if (!grouped[type]) {
          grouped[type] = []
        }
        grouped[type].push(insight)
      })
      return grouped
    },
    
    // 按优先级分组的执行计划
    actionPlansByPriority: (state) => {
      const grouped = {}
      state.actionPlans.forEach(plan => {
        const priority = plan.priority || 'P3'
        if (!grouped[priority]) {
          grouped[priority] = []
        }
        grouped[priority].push(plan)
      })
      return grouped
    },
    
    // 高优先级洞察
    highPriorityInsights: (state) => {
      return state.insights.filter(insight => 
        insight.impact_level === 'high' || insight.confidence_score > 0.8
      )
    },
    
    // 紧急执行计划
    urgentActionPlans: (state) => {
      return state.actionPlans.filter(plan => 
        plan.priority === 'P0' || plan.priority === 'P1'
      )
    },
    
    // 统计信息
    insightsStats: (state) => state.stats,
    
    // 错误信息
    lastError: (state) => state.error
  },
  
  actions: {
    // 生成洞察和执行计划（同时生成常规洞察和全文洞察）
    async generateInsights() {
      this.insightsStatus = 'generating'
      this.error = null
      
      try {
        console.log('🚀 开始生成常规洞察和全文洞察...')
        
        // 同时调用常规洞察和全文洞察
        const [standardResponse, fullTextResponse] = await Promise.allSettled([
          insightsAPI.generateInsights({
            feedback_limit: this.generationConfig.feedback_limit || 50,
            include_action_plans: this.generationConfig.include_action_plans || true,
            filters: this.generationConfig.filters || {}
          }),
          insightsAPI.generateFullTextInsights({
            feedback_limit: this.generationConfig.feedback_limit || 350,
            filters: this.generationConfig.filters || {},
            analysis_focus: 'comprehensive'
          })
        ])
        
        // 处理智能洞察结果
        let standardInsights = []
        let standardActionPlans = []
        if (standardResponse.status === 'fulfilled') {
          const { insights, action_plans } = standardResponse.value.data
          standardInsights = insights || []
          standardActionPlans = action_plans || []
          console.log(`✅ 智能洞察生成成功: ${standardInsights.length}个洞察`)
        } else {
          console.warn('⚠️ 智能洞察生成失败:', standardResponse.reason)
        }
        
        // 处理全文洞察结果
        let fullTextInsights = []
        let executiveSummary = {}
        if (fullTextResponse.status === 'fulfilled') {
          const { insights, executive_summary } = fullTextResponse.value.data
          fullTextInsights = (insights || []).map(insight => ({
            ...insight,
            is_full_text: true,
            analysis_type: 'full_text'
          }))
          executiveSummary = executive_summary || {}
          console.log(`✅ 全文洞察生成成功: ${fullTextInsights.length}个洞察`)
        } else {
          console.warn('⚠️ 全文洞察生成失败:', fullTextResponse.reason)
        }
        
        // 合并所有洞察
        const allInsights = [...standardInsights, ...fullTextInsights]
        
        // 更新状态
        this.insights = allInsights
        this.actionPlans = standardActionPlans
        this.stats = {
          ...this.stats,
          total_insights: allInsights.length,
          standard_insights: standardInsights.length,
          full_text_insights: fullTextInsights.length,
          last_generation_time: new Date().toISOString(),
          executive_summary: executiveSummary,
          generation_type: 'combined'
        }
        this.insightsStatus = 'completed'
        
        console.log(`🎯 洞察生成完成: 总计${allInsights.length}个洞察 (智能:${standardInsights.length} + 全文:${fullTextInsights.length})`)
        
        return {
          insights: allInsights,
          action_plans: standardActionPlans,
          executive_summary: executiveSummary,
          total_insights: allInsights.length,
          generation_type: 'combined'
        }
      } catch (error) {
        console.error('生成洞察失败:', error)
        this.error = error.response?.data?.detail || error.message
        this.insightsStatus = 'error'
        throw error
      }
    },
    
    // 手动生成洞察
    async generateManualInsights(feedbackIds) {
      this.insightsStatus = 'generating'
      this.error = null
      
      try {
        const response = await insightsAPI.generateManualInsights({
          feedback_ids: feedbackIds,
          focus_areas: ['用户体验', '产品功能', '性能优化'],
          business_context: '基于用户反馈的产品改进分析'
        })
        const { insights, action_plans } = response.data
        
        this.insights = insights || []
        this.actionPlans = action_plans || []
        this.insightsStatus = 'completed'
        
        return response.data
      } catch (error) {
        console.error('手动生成洞察失败:', error)
        this.error = error.response?.data?.detail || error.message
        this.insightsStatus = 'error'
        throw error
      }
    },
    
    // 获取洞察演示
    async getInsightsDemo() {
      this.insightsStatus = 'generating'
      this.error = null
      
      try {
        const response = await insightsAPI.getInsightsDemo()
        const { insights, action_plans } = response.data
        
        this.insights = insights || []
        this.actionPlans = action_plans || []
        this.insightsStatus = 'completed'
        
        return response.data
      } catch (error) {
        this.error = error.response?.data?.detail || error.message
        this.insightsStatus = 'error'
        throw error
      }
    },
    
    // 更新生成配置
    updateGenerationConfig(config) {
      this.generationConfig = { ...this.generationConfig, ...config }
    },
    
    // 清空洞察
    clearInsights() {
      this.insights = []
      this.actionPlans = []
      this.insightsStatus = 'idle'
      this.error = null
    },
    
    // 检查服务健康状态
    async checkInsightsHealth() {
      try {
        const response = await insightsAPI.checkInsightsHealth()
        return response.data
      } catch (error) {
        this.error = error.response?.data?.detail || error.message
        throw error
      }
    },
    
    // 添加洞察
    addInsight(insight) {
      this.insights.push(insight)
    },
    
    // 更新洞察
    updateInsight(index, insight) {
      if (index >= 0 && index < this.insights.length) {
        this.insights[index] = insight
      }
    },
    
    // 删除洞察
    removeInsight(index) {
      if (index >= 0 && index < this.insights.length) {
        this.insights.splice(index, 1)
      }
    },
    
    // 添加执行计划
    addActionPlan(plan) {
      this.actionPlans.push(plan)
    },
    
    // 更新执行计划
    updateActionPlan(index, plan) {
      if (index >= 0 && index < this.actionPlans.length) {
        this.actionPlans[index] = plan
      }
    },
    
    // 删除执行计划
    removeActionPlan(index) {
      if (index >= 0 && index < this.actionPlans.length) {
        this.actionPlans.splice(index, 1)
      }
    },

    // 合并全文洞察结果（兼容旧版本调用）
    mergeFullTextInsights(insights, executiveSummary) {
      // 为全文洞察添加特殊标记
      const enhancedInsights = insights.map(insight => ({
        ...insight,
        is_full_text: true,
        analysis_type: 'full_text'
      }))
      
      // 合并到现有洞察中
      this.insights = [...this.insights, ...enhancedInsights]
      
      // 更新统计信息
      this.stats = {
        ...this.stats,
        total_insights: this.insights.length,
        last_generation_time: new Date().toISOString(),
        executive_summary: executiveSummary || {}
      }
    },

    // 加载最新的洞察会话
    async loadLatestInsights() {
      this.insightsStatus = 'generating'
      this.error = null
      
      try {
        const response = await insightsAPI.getLatestInsightSession()
        const sessionData = response.data
        
        // 设置洞察和执行计划
        this.insights = sessionData.insights || []
        this.actionPlans = sessionData.action_plans || []
        
        // 设置统计信息
        this.stats = {
          total_insights: sessionData.total_insights || 0,
          insights_by_type: sessionData.insights_by_type || {},
          last_generation_time: sessionData.created_at,
          executive_summary: sessionData.executive_summary || {},
          session_id: sessionData.session_id,
          session_title: sessionData.title,
          generation_type: sessionData.generation_type
        }
        
        // 更新生成配置
        this.generationConfig = {
          feedback_limit: sessionData.feedback_limit,
          include_action_plans: true,
          filters: sessionData.filters || {}
        }
        
        this.insightsStatus = 'completed'
        
        return sessionData
      } catch (error) {
        // 如果没有找到洞察会话，不算错误
        if (error.response?.status === 404) {
          this.insightsStatus = 'idle'
          return null
        }
        
        console.error('加载最新洞察会话失败:', error)
        this.error = error.response?.data?.detail || error.message
        this.insightsStatus = 'error'
        throw error
      }
    },

    // 保存当前洞察会话
    async saveCurrentInsights({ title, tags = [] }) {
      try {
        const saveData = {
          title: title || `洞察分析 - ${new Date().toLocaleDateString()}`,
          generation_type: this.stats.generation_type || 'standard',
          feedback_limit: this.generationConfig.feedback_limit,
          feedback_analyzed: this.stats.feedback_analyzed || 0,
          filters: this.generationConfig.filters || {},
          insights: this.insights,
          action_plans: this.actionPlans,
          executive_summary: this.stats.executive_summary || {},
          generation_time: 0,
          tags: tags
        }
        
        const response = await insightsAPI.saveInsightSession(saveData)
        
        // 更新统计信息中的会话ID
        this.stats = {
          ...this.stats,
          session_id: response.data.session_id,
          session_title: saveData.title
        }
        
        return response.data
      } catch (error) {
        console.error('保存洞察会话失败:', error)
        this.error = error.response?.data?.detail || error.message
        throw error
      }
    },

    // 获取洞察会话列表
    async getInsightSessions(params = {}) {
      try {
        const response = await insightsAPI.getInsightSessions(params)
        return response.data
      } catch (error) {
        console.error('获取洞察会话列表失败:', error)
        this.error = error.response?.data?.detail || error.message
        throw error
      }
    },

    // 加载指定的洞察会话
    async loadInsightSession(sessionId) {
      this.insightsStatus = 'generating'
      this.error = null
      
      try {
        const response = await insightsAPI.getInsightSession(sessionId)
        const sessionData = response.data
        
        // 设置洞察和执行计划
        this.insights = sessionData.insights || []
        this.actionPlans = sessionData.action_plans || []
        
        // 设置统计信息
        this.stats = {
          total_insights: sessionData.total_insights || 0,
          insights_by_type: sessionData.insights_by_type || {},
          last_generation_time: sessionData.created_at,
          executive_summary: sessionData.executive_summary || {},
          session_id: sessionData.session_id,
          session_title: sessionData.title,
          generation_type: sessionData.generation_type
        }
        
        // 更新生成配置
        this.generationConfig = {
          feedback_limit: sessionData.feedback_limit,
          include_action_plans: true,
          filters: sessionData.filters || {}
        }
        
        this.insightsStatus = 'completed'
        
        return sessionData
      } catch (error) {
        console.error('加载洞察会话失败:', error)
        this.error = error.response?.data?.detail || error.message
        this.insightsStatus = 'error'
        throw error
      }
    }
  }
}) 