import { analysisAPI } from '@/utils/api'

const state = {
  issues: [],
  currentIssue: null,
  totalCount: 0,
  
  filters: {
    status: '',
    priority_category: ''
  },
  
  pagination: {
    current_page: 1,
    page_size: 20,
    total: 0
  },
  
  priorityRanking: [],
  
  loading: {
    list: false,
    update: false
  }
}

const mutations = {
  SET_ISSUES(state, data) {
    state.issues = data.issues || []
    state.totalCount = data.total || 0
  },
  
  SET_CURRENT_ISSUE(state, issue) {
    state.currentIssue = issue
  },
  
  UPDATE_ISSUE(state, updatedIssue) {
    const index = state.issues.findIndex(i => i.issue_id === updatedIssue.issue_id)
    if (index !== -1) {
      state.issues.splice(index, 1, updatedIssue)
    }
  },
  
  SET_PRIORITY_RANKING(state, ranking) {
    state.priorityRanking = ranking
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
  async fetchIssues({ commit, state }, params = {}) {
    commit('SET_LOADING', { type: 'list', loading: true })
    
    try {
      const requestParams = {
        skip: (state.pagination.current_page - 1) * state.pagination.page_size,
        limit: state.pagination.page_size,
        ...state.filters,
        ...params
      }
      
      const response = await analysisAPI.getIssues(requestParams)
      
      commit('SET_ISSUES', {
        issues: response.data,
        total: response.headers['x-total-count'] || response.data.length
      })
      
      return response.data
    } catch (error) {
      console.error('获取问题列表失败:', error)
      throw error
    } finally {
      commit('SET_LOADING', { type: 'list', loading: false })
    }
  },
  
  async fetchIssue({ commit }, issueId) {
    try {
      const response = await analysisAPI.getIssue(issueId)
      commit('SET_CURRENT_ISSUE', response.data)
      return response.data
    } catch (error) {
      console.error('获取问题详情失败:', error)
      throw error
    }
  },
  
  async updateIssueStatus({ commit }, { issueId, status }) {
    commit('SET_LOADING', { type: 'update', loading: true })
    
    try {
      await analysisAPI.updateIssueStatus(issueId, status)
      
      // 更新本地状态
      const updatedIssue = { ...state.currentIssue, status }
      commit('UPDATE_ISSUE', updatedIssue)
      
      return true
    } catch (error) {
      console.error('更新问题状态失败:', error)
      throw error
    } finally {
      commit('SET_LOADING', { type: 'update', loading: false })
    }
  },
  
  async fetchPriorityRanking({ commit }, params = {}) {
    try {
      const response = await analysisAPI.getPriorityRanking(params)
      commit('SET_PRIORITY_RANKING', response.data.ranking || [])
      return response.data
    } catch (error) {
      console.error('获取优先级排序失败:', error)
      throw error
    }
  },
  
  updateFilters({ commit, dispatch }, filters) {
    commit('SET_FILTERS', filters)
    commit('SET_PAGINATION', { current_page: 1 })
    return dispatch('fetchIssues')
  },
  
  updatePagination({ commit, dispatch }, pagination) {
    commit('SET_PAGINATION', pagination)
    return dispatch('fetchIssues')
  }
}

const getters = {
  issueList: state => state.issues,
  currentIssue: state => state.currentIssue,
  priorityRanking: state => state.priorityRanking,
  totalCount: state => state.totalCount,
  
  filters: state => state.filters,
  pagination: state => state.pagination,
  
  isLoading: state => type => state.loading[type] || false,
  
  // 按状态分组的问题
  issuesByStatus: state => {
    const grouped = {}
    state.issues.forEach(issue => {
      const status = issue.status || 'Unknown'
      if (!grouped[status]) {
        grouped[status] = []
      }
      grouped[status].push(issue)
    })
    return grouped
  },
  
  // 高优先级问题
  criticalIssues: state => {
    return state.issues.filter(issue => issue.priority_score >= 8.0)
  }
}

export default {
  namespaced: true,
  state,
  mutations,
  actions,
  getters
} 