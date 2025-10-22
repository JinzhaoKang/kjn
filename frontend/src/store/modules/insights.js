import { insightsAPI } from '@/utils/api'

const state = {
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
}

const mutations = {
  SET_INSIGHTS_STATUS(state, status) {
    state.insightsStatus = status
  },
  
  SET_INSIGHTS(state, insights) {
    state.insights = insights
  },
  
  SET_ACTION_PLANS(state, actionPlans) {
    state.actionPlans = actionPlans
  },
  
  SET_GENERATION_CONFIG(state, config) {
    state.generationConfig = { ...state.generationConfig, ...config }
  },
  
  SET_STATS(state, stats) {
    state.stats = stats
  },
  
  SET_ERROR(state, error) {
    state.error = error
  },
  
  ADD_INSIGHT(state, insight) {
    state.insights.push(insight)
  },
  
  UPDATE_INSIGHT(state, { index, insight }) {
    if (index >= 0 && index < state.insights.length) {
      state.insights[index] = insight
    }
  },
  
  REMOVE_INSIGHT(state, index) {
    if (index >= 0 && index < state.insights.length) {
      state.insights.splice(index, 1)
    }
  },
  
  ADD_ACTION_PLAN(state, plan) {
    state.actionPlans.push(plan)
  },
  
  UPDATE_ACTION_PLAN(state, { index, plan }) {
    if (index >= 0 && index < state.actionPlans.length) {
      state.actionPlans[index] = plan
    }
  },
  
  REMOVE_ACTION_PLAN(state, index) {
    if (index >= 0 && index < state.actionPlans.length) {
      state.actionPlans.splice(index, 1)
    }
  }
}

const actions = {
  // 生成洞察和执行计划
  async generateInsights({ commit, state }) {
    commit('SET_INSIGHTS_STATUS', 'generating')
    commit('SET_ERROR', null)
    
    try {
      const response = await insightsAPI.generateInsights(state.generationConfig)
      const { insights, action_plans, stats } = response.data
      
      commit('SET_INSIGHTS', insights || [])
      commit('SET_ACTION_PLANS', action_plans || [])
      commit('SET_STATS', {
        ...state.stats,
        total_insights: insights?.length || 0,
        last_generation_time: new Date().toISOString(),
        ...stats
      })
      commit('SET_INSIGHTS_STATUS', 'completed')
      
      return response.data
    } catch (error) {
      commit('SET_ERROR', error.response?.data?.detail || error.message)
      commit('SET_INSIGHTS_STATUS', 'error')
      throw error
    }
  },
  
  // 手动生成洞察
  async generateManualInsights({ commit }, feedbackIds) {
    commit('SET_INSIGHTS_STATUS', 'generating')
    commit('SET_ERROR', null)
    
    try {
      const response = await insightsAPI.generateManualInsights({
        feedback_ids: feedbackIds,
        include_action_plans: true
      })
      const { insights, action_plans } = response.data
      
      commit('SET_INSIGHTS', insights || [])
      commit('SET_ACTION_PLANS', action_plans || [])
      commit('SET_INSIGHTS_STATUS', 'completed')
      
      return response.data
    } catch (error) {
      commit('SET_ERROR', error.response?.data?.detail || error.message)
      commit('SET_INSIGHTS_STATUS', 'error')
      throw error
    }
  },
  
  // 获取洞察演示
  async getInsightsDemo({ commit }) {
    commit('SET_INSIGHTS_STATUS', 'generating')
    commit('SET_ERROR', null)
    
    try {
      const response = await insightsAPI.getInsightsDemo()
      const { insights, action_plans } = response.data
      
      commit('SET_INSIGHTS', insights || [])
      commit('SET_ACTION_PLANS', action_plans || [])
      commit('SET_INSIGHTS_STATUS', 'completed')
      
      return response.data
    } catch (error) {
      commit('SET_ERROR', error.response?.data?.detail || error.message)
      commit('SET_INSIGHTS_STATUS', 'error')
      throw error
    }
  },
  
  // 更新生成配置
  updateGenerationConfig({ commit }, config) {
    commit('SET_GENERATION_CONFIG', config)
  },
  
  // 清空洞察
  clearInsights({ commit }) {
    commit('SET_INSIGHTS', [])
    commit('SET_ACTION_PLANS', [])
    commit('SET_INSIGHTS_STATUS', 'idle')
    commit('SET_ERROR', null)
  },
  
  // 检查服务健康状态
  async checkInsightsHealth({ commit }) {
    try {
      const response = await insightsAPI.checkInsightsHealth()
      return response.data
    } catch (error) {
      commit('SET_ERROR', error.response?.data?.detail || error.message)
      throw error
    }
  },

  // 合并全文洞察结果
  mergeFullTextInsights({ commit, state }, insights, executiveSummary) {
    // 将全文洞察合并到现有洞察中
    const mergedInsights = [...state.insights]
    
    // 为全文洞察添加特殊标记
    insights.forEach(insight => {
      const enhancedInsight = {
        ...insight,
        is_full_text: true,
        analysis_type: 'full_text'
      }
      mergedInsights.push(enhancedInsight)
    })
    
    commit('SET_INSIGHTS', mergedInsights)
    
    // 更新统计信息
    commit('SET_STATS', {
      ...state.stats,
      total_insights: mergedInsights.length,
      last_generation_time: new Date().toISOString(),
      executive_summary: executiveSummary || {}
    })
  },

  // 新增：加载最新的洞察会话
  async loadLatestInsights({ commit }) {
    commit('SET_INSIGHTS_STATUS', 'generating')
    commit('SET_ERROR', null)
    
    try {
      const response = await insightsAPI.getLatestInsightSession()
      const sessionData = response.data
      
      // 设置洞察和执行计划
      commit('SET_INSIGHTS', sessionData.insights || [])
      commit('SET_ACTION_PLANS', sessionData.action_plans || [])
      
      // 设置统计信息
      commit('SET_STATS', {
        total_insights: sessionData.total_insights || 0,
        insights_by_type: sessionData.insights_by_type || {},
        last_generation_time: sessionData.created_at,
        executive_summary: sessionData.executive_summary || {},
        session_id: sessionData.session_id,
        session_title: sessionData.title,
        generation_type: sessionData.generation_type
      })
      
      // 更新生成配置
      commit('SET_GENERATION_CONFIG', {
        feedback_limit: sessionData.feedback_limit,
        include_action_plans: true,
        filters: sessionData.filters || {}
      })
      
      commit('SET_INSIGHTS_STATUS', 'completed')
      
      return sessionData
    } catch (error) {
      // 如果没有找到洞察会话，不算错误
      if (error.response?.status === 404) {
        commit('SET_INSIGHTS_STATUS', 'idle')
        return null
      }
      
      commit('SET_ERROR', error.response?.data?.detail || error.message)
      commit('SET_INSIGHTS_STATUS', 'error')
      throw error
    }
  },

  // 新增：保存当前洞察会话
  async saveCurrentInsights({ commit, state }, { title, tags = [] }) {
    try {
      const saveData = {
        title: title || `洞察分析 - ${new Date().toLocaleDateString()}`,
        generation_type: state.stats.generation_type || 'standard',
        feedback_limit: state.generationConfig.feedback_limit,
        feedback_analyzed: state.stats.feedback_analyzed || 0,
        filters: state.generationConfig.filters || {},
        insights: state.insights,
        action_plans: state.actionPlans,
        executive_summary: state.stats.executive_summary || {},
        generation_time: 0,
        tags: tags
      }
      
      const response = await insightsAPI.saveInsightSession(saveData)
      
      // 更新统计信息中的会话ID
      commit('SET_STATS', {
        ...state.stats,
        session_id: response.data.session_id,
        session_title: saveData.title
      })
      
      return response.data
    } catch (error) {
      commit('SET_ERROR', error.response?.data?.detail || error.message)
      throw error
    }
  },

  // 新增：获取洞察会话列表
  async getInsightSessions({ commit }, params = {}) {
    try {
      const response = await insightsAPI.getInsightSessions(params)
      return response.data
    } catch (error) {
      commit('SET_ERROR', error.response?.data?.detail || error.message)
      throw error
    }
  },

  // 新增：加载指定的洞察会话
  async loadInsightSession({ commit }, sessionId) {
    commit('SET_INSIGHTS_STATUS', 'generating')
    commit('SET_ERROR', null)
    
    try {
      const response = await insightsAPI.getInsightSession(sessionId)
      const sessionData = response.data
      
      // 设置洞察和执行计划
      commit('SET_INSIGHTS', sessionData.insights || [])
      commit('SET_ACTION_PLANS', sessionData.action_plans || [])
      
      // 设置统计信息
      commit('SET_STATS', {
        total_insights: sessionData.total_insights || 0,
        insights_by_type: sessionData.insights_by_type || {},
        last_generation_time: sessionData.created_at,
        executive_summary: sessionData.executive_summary || {},
        session_id: sessionData.session_id,
        session_title: sessionData.title,
        generation_type: sessionData.generation_type
      })
      
      // 更新生成配置
      commit('SET_GENERATION_CONFIG', {
        feedback_limit: sessionData.feedback_limit,
        include_action_plans: true,
        filters: sessionData.filters || {}
      })
      
      commit('SET_INSIGHTS_STATUS', 'completed')
      
      return sessionData
    } catch (error) {
      commit('SET_ERROR', error.response?.data?.detail || error.message)
      commit('SET_INSIGHTS_STATUS', 'error')
      throw error
    }
  }
}

const getters = {
  // 洞察状态
  isGenerating: state => state.insightsStatus === 'generating',
  isCompleted: state => state.insightsStatus === 'completed',
  hasError: state => state.insightsStatus === 'error',
  
  // 洞察数据
  allInsights: state => state.insights,
  allActionPlans: state => state.actionPlans,
  
  // 按类型分组的洞察
  insightsByType: state => {
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
  actionPlansByPriority: state => {
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
  highPriorityInsights: state => {
    return state.insights.filter(insight => 
      insight.impact_level === 'high' || insight.confidence_score > 0.8
    )
  },
  
  // 紧急执行计划
  urgentActionPlans: state => {
    return state.actionPlans.filter(plan => 
      plan.priority === 'P0' || plan.priority === 'P1'
    )
  },
  
  // 统计信息
  insightsStats: state => state.stats,
  
  // 错误信息
  lastError: state => state.error
}

export default {
  namespaced: true,
  state,
  mutations,
  actions,
  getters
} 