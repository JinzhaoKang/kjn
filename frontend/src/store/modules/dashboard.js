import api from '@/utils/api'

const state = {
  overview: {
    total_feedback: 0,
    processed_feedback: 0,
    processing_rate: 0,
    total_issues: 0,
    critical_issues: 0,
    recent_feedback_trend: [],
    sentiment_distribution: {},
    top_issues: [],
    last_updated: null
  },
  
  sentimentTrend: {
    trend_data: [],
    period: '',
    last_updated: null
  },
  
  topicDistribution: {
    distribution: [],
    total_feedbacks: 0,
    period: '',
    last_updated: null
  },
  
  priorityMatrix: {
    matrix_data: [],
    total_issues: 0,
    last_updated: null
  },
  
  sourceAnalysis: {
    source_analysis: [],
    total_feedback: 0,
    period: '',
    last_updated: null
  },
  
  processingPerformance: {
    avg_processing_time_seconds: 0,
    max_processing_time_seconds: 0,
    min_processing_time_seconds: 0,
    total_processed: 0,
    daily_processing: [],
    period: '',
    last_updated: null
  }
}

const mutations = {
  SET_OVERVIEW(state, overview) {
    state.overview = overview
  },
  
  SET_SENTIMENT_TREND(state, data) {
    state.sentimentTrend = data
  },
  
  SET_TOPIC_DISTRIBUTION(state, data) {
    state.topicDistribution = data
  },
  
  SET_PRIORITY_MATRIX(state, data) {
    state.priorityMatrix = data
  },
  
  SET_SOURCE_ANALYSIS(state, data) {
    state.sourceAnalysis = data
  },
  
  SET_PROCESSING_PERFORMANCE(state, data) {
    state.processingPerformance = data
  }
}

const actions = {
  async fetchOverview({ commit }, daysBack = 30) {
    try {
      const response = await api.get(`/dashboard/overview?days_back=${daysBack}`)
      commit('SET_OVERVIEW', response.data)
      return response.data
    } catch (error) {
      console.error('获取概览数据失败:', error)
      throw error
    }
  },
  
  async fetchSentimentTrend({ commit }, daysBack = 30) {
    try {
      const response = await api.get(`/dashboard/charts/sentiment-trend?days_back=${daysBack}`)
      commit('SET_SENTIMENT_TREND', response.data)
      return response.data
    } catch (error) {
      console.error('获取情感趋势失败:', error)
      throw error
    }
  },
  
  async fetchTopicDistribution({ commit }, params = {}) {
    try {
      const { daysBack = 30, limit = 10 } = params
      const response = await api.get(`/dashboard/charts/topic-distribution?days_back=${daysBack}&limit=${limit}`)
      commit('SET_TOPIC_DISTRIBUTION', response.data)
      return response.data
    } catch (error) {
      console.error('获取主题分布失败:', error)
      throw error
    }
  },
  
  async fetchPriorityMatrix({ commit }) {
    try {
      const response = await api.get('/dashboard/charts/priority-matrix')
      commit('SET_PRIORITY_MATRIX', response.data)
      return response.data
    } catch (error) {
      console.error('获取优先级矩阵失败:', error)
      throw error
    }
  },
  
  async fetchSourceAnalysis({ commit }, daysBack = 30) {
    try {
      const response = await api.get(`/dashboard/charts/source-analysis?days_back=${daysBack}`)
      commit('SET_SOURCE_ANALYSIS', response.data)
      return response.data
    } catch (error) {
      console.error('获取数据源分析失败:', error)
      throw error
    }
  },
  
  async fetchProcessingPerformance({ commit }, daysBack = 7) {
    try {
      const response = await api.get(`/dashboard/stats/processing-performance?days_back=${daysBack}`)
      commit('SET_PROCESSING_PERFORMANCE', response.data)
      return response.data
    } catch (error) {
      console.error('获取处理性能统计失败:', error)
      throw error
    }
  },
  
  async fetchAllDashboardData({ dispatch }, daysBack = 30) {
    try {
      await Promise.all([
        dispatch('fetchOverview', daysBack),
        dispatch('fetchSentimentTrend', daysBack),
        dispatch('fetchTopicDistribution', { daysBack }),
        dispatch('fetchPriorityMatrix'),
        dispatch('fetchSourceAnalysis', daysBack),
        dispatch('fetchProcessingPerformance', 7)
      ])
    } catch (error) {
      console.error('获取仪表板数据失败:', error)
      throw error
    }
  }
}

const getters = {
  overviewData: state => state.overview,
  sentimentTrendData: state => state.sentimentTrend,
  topicDistributionData: state => state.topicDistribution,
  priorityMatrixData: state => state.priorityMatrix,
  sourceAnalysisData: state => state.sourceAnalysis,
  processingPerformanceData: state => state.processingPerformance,
  
  // 计算属性
  processingRate: state => state.overview.processing_rate,
  criticalIssuesCount: state => state.overview.critical_issues,
  
  // 格式化的数据
  formattedSentimentTrend: state => {
    const data = state.sentimentTrend.trend_data
    if (!data || data.length === 0) return { dates: [], positive: [], negative: [], neutral: [] }
    
    return {
      dates: data.map(item => item.date),
      positive: data.map(item => item.Positive || 0),
      negative: data.map(item => item.Negative || 0),
      neutral: data.map(item => item.Neutral || 0)
    }
  },
  
  formattedTopicDistribution: state => {
    const data = state.topicDistribution.distribution
    if (!data || data.length === 0) return { topics: [], counts: [] }
    
    return {
      topics: data.map(item => item.topic),
      counts: data.map(item => item.count),
      percentages: data.map(item => item.percentage)
    }
  }
}

export default {
  namespaced: true,
  state,
  mutations,
  actions,
  getters
} 