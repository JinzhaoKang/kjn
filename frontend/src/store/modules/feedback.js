import { feedbackAPI } from '@/utils/api'

const state = {
  feedbacks: [],
  totalCount: 0,
  unprocessedCount: 0,
  currentFeedback: null,
  
  stats: {
    total_feedback: 0,
    processed_feedback: 0,
    unprocessed_feedback: 0,
    processing_rate: 0,
    source_distribution: {},
    recent_7days: 0
  },
  
  filters: {
    source: '',
    is_processed: null,
    date_range: []
  },
  
  pagination: {
    current_page: 1,
    page_size: 20,
    total: 0
  },
  
  loading: {
    list: false,
    create: false,
    delete: false,
    stats: false
  }
}

const mutations = {
  SET_FEEDBACKS(state, data) {
    state.feedbacks = data.feedbacks || []
    state.totalCount = data.total || 0
  },
  
  SET_CURRENT_FEEDBACK(state, feedback) {
    state.currentFeedback = feedback
  },
  
  ADD_FEEDBACK(state, feedback) {
    state.feedbacks.unshift(feedback)
    state.totalCount += 1
  },
  
  UPDATE_FEEDBACK(state, updatedFeedback) {
    const index = state.feedbacks.findIndex(f => f.id === updatedFeedback.id)
    if (index !== -1) {
      state.feedbacks.splice(index, 1, updatedFeedback)
    }
  },
  
  REMOVE_FEEDBACK(state, feedbackId) {
    const index = state.feedbacks.findIndex(f => f.id === feedbackId)
    if (index !== -1) {
      state.feedbacks.splice(index, 1)
      state.totalCount -= 1
    }
  },
  
  SET_STATS(state, stats) {
    state.stats = stats
    state.unprocessedCount = stats.unprocessed_feedback || 0
  },
  
  SET_FILTERS(state, filters) {
    state.filters = { ...state.filters, ...filters }
  },
  
  SET_PAGINATION(state, pagination) {
    state.pagination = { ...state.pagination, ...pagination }
  },
  
  SET_LOADING(state, { type, loading }) {
    state.loading[type] = loading
  }
}

const actions = {
  async fetchFeedbacks({ commit, state }, params = {}) {
    commit('SET_LOADING', { type: 'list', loading: true })
    
    try {
      const requestParams = {
        skip: (state.pagination.current_page - 1) * state.pagination.page_size,
        limit: state.pagination.page_size,
        ...state.filters,
        ...params
      }
      
      // 移除空值
      Object.keys(requestParams).forEach(key => {
        if (requestParams[key] === '' || requestParams[key] === null) {
          delete requestParams[key]
        }
      })
      
      const response = await feedbackAPI.getFeedbacks(requestParams)
      
      commit('SET_FEEDBACKS', {
        feedbacks: response.data,
        total: response.headers['x-total-count'] || response.data.length
      })
      
      return response.data
    } catch (error) {
      console.error('获取反馈列表失败:', error)
      throw error
    } finally {
      commit('SET_LOADING', { type: 'list', loading: false })
    }
  },
  
  async fetchFeedback({ commit }, feedbackId) {
    try {
      const response = await feedbackAPI.getFeedback(feedbackId)
      commit('SET_CURRENT_FEEDBACK', response.data)
      return response.data
    } catch (error) {
      console.error('获取反馈详情失败:', error)
      throw error
    }
  },
  
  async createFeedback({ commit }, feedbackData) {
    commit('SET_LOADING', { type: 'create', loading: true })
    
    try {
      const response = await feedbackAPI.createFeedback(feedbackData)
      commit('ADD_FEEDBACK', response.data)
      return response.data
    } catch (error) {
      console.error('创建反馈失败:', error)
      throw error
    } finally {
      commit('SET_LOADING', { type: 'create', loading: false })
    }
  },
  
  async createBatchFeedback({ dispatch }, feedbacksData) {
    commit('SET_LOADING', { type: 'create', loading: true })
    
    try {
      const response = await feedbackAPI.createBatchFeedback(feedbacksData)
      
      // 重新获取列表
      await dispatch('fetchFeedbacks')
      await dispatch('fetchStats')
      
      return response.data
    } catch (error) {
      console.error('批量创建反馈失败:', error)
      throw error
    } finally {
      commit('SET_LOADING', { type: 'create', loading: false })
    }
  },
  
  async deleteFeedback({ commit }, feedbackId) {
    commit('SET_LOADING', { type: 'delete', loading: true })
    
    try {
      await feedbackAPI.deleteFeedback(feedbackId)
      commit('REMOVE_FEEDBACK', feedbackId)
      return true
    } catch (error) {
      console.error('删除反馈失败:', error)
      throw error
    } finally {
      commit('SET_LOADING', { type: 'delete', loading: false })
    }
  },
  
  async fetchStats({ commit }) {
    commit('SET_LOADING', { type: 'stats', loading: true })
    
    try {
      const response = await feedbackAPI.getFeedbackStats()
      commit('SET_STATS', response.data)
      return response.data
    } catch (error) {
      console.error('获取反馈统计失败:', error)
      throw error
    } finally {
      commit('SET_LOADING', { type: 'stats', loading: false })
    }
  },
  
  updateFilters({ commit, dispatch }, filters) {
    commit('SET_FILTERS', filters)
    commit('SET_PAGINATION', { current_page: 1 }) // 重置到第一页
    return dispatch('fetchFeedbacks')
  },
  
  updatePagination({ commit, dispatch }, pagination) {
    commit('SET_PAGINATION', pagination)
    return dispatch('fetchFeedbacks')
  },
  
  clearCurrentFeedback({ commit }) {
    commit('SET_CURRENT_FEEDBACK', null)
  }
}

const getters = {
  feedbackList: state => state.feedbacks,
  currentFeedback: state => state.currentFeedback,
  feedbackStats: state => state.stats,
  unprocessedCount: state => state.unprocessedCount,
  totalCount: state => state.totalCount,
  
  filters: state => state.filters,
  pagination: state => state.pagination,
  
  isLoading: state => type => state.loading[type] || false,
  
  // 格式化的统计数据
  formattedStats: state => {
    const stats = state.stats
    return {
      total: stats.total_feedback,
      processed: stats.processed_feedback,
      unprocessed: stats.unprocessed_feedback,
      processingRate: stats.processing_rate,
      sourceDistribution: Object.entries(stats.source_distribution || {}).map(([source, count]) => ({
        source,
        count,
        percentage: stats.total_feedback > 0 ? ((count / stats.total_feedback) * 100).toFixed(1) : 0
      })),
      recentCount: stats.recent_7days
    }
  },
  
  // 分页信息
  paginationInfo: state => {
    const { current_page, page_size, total } = state.pagination
    const totalPages = Math.ceil(total / page_size)
    const start = (current_page - 1) * page_size + 1
    const end = Math.min(current_page * page_size, total)
    
    return {
      currentPage: current_page,
      pageSize: page_size,
      total,
      totalPages,
      start,
      end,
      hasNext: current_page < totalPages,
      hasPrev: current_page > 1
    }
  },
  
  // 筛选后的反馈列表
  filteredFeedbacks: state => {
    let filtered = [...state.feedbacks]
    
    // 按源筛选
    if (state.filters.source) {
      filtered = filtered.filter(f => f.source === state.filters.source)
    }
    
    // 按处理状态筛选
    if (state.filters.is_processed !== null) {
      filtered = filtered.filter(f => f.is_processed === state.filters.is_processed)
    }
    
    return filtered
  }
}

export default {
  namespaced: true,
  state,
  mutations,
  actions,
  getters
} 