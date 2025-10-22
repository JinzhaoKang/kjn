import { analysisAPI } from '@/utils/api'

const state = {
  clusteringStatus: 'idle', // idle, running, completed, error
  clusteringResult: null,
  
  priorityStatus: 'idle',
  priorityResult: null,
  
  stats: {
    total_issues: 0,
    status_distribution: {},
    recent_issues_7days: 0,
    avg_feedback_per_issue: 0
  }
}

const mutations = {
  SET_CLUSTERING_STATUS(state, status) {
    state.clusteringStatus = status
  },
  
  SET_CLUSTERING_RESULT(state, result) {
    state.clusteringResult = result
  },
  
  SET_PRIORITY_STATUS(state, status) {
    state.priorityStatus = status
  },
  
  SET_PRIORITY_RESULT(state, result) {
    state.priorityResult = result
  },
  
  SET_STATS(state, stats) {
    state.stats = stats
  }
}

const actions = {
  async triggerClustering({ commit }, params) {
    commit('SET_CLUSTERING_STATUS', 'running')
    
    try {
      const response = await analysisAPI.triggerClustering(params)
      commit('SET_CLUSTERING_RESULT', response.data)
      commit('SET_CLUSTERING_STATUS', 'completed')
      return response.data
    } catch (error) {
      commit('SET_CLUSTERING_STATUS', 'error')
      throw error
    }
  },
  
  async calculatePriority({ commit }, params) {
    commit('SET_PRIORITY_STATUS', 'running')
    
    try {
      const response = await analysisAPI.calculatePriority(params)
      commit('SET_PRIORITY_RESULT', response.data)
      commit('SET_PRIORITY_STATUS', 'completed')
      return response.data
    } catch (error) {
      commit('SET_PRIORITY_STATUS', 'error')
      throw error
    }
  },
  
  async fetchStats({ commit }) {
    try {
      const response = await analysisAPI.getClusteringStats()
      commit('SET_STATS', response.data)
      return response.data
    } catch (error) {
      console.error('获取分析统计失败:', error)
      throw error
    }
  }
}

const getters = {
  isClusteringRunning: state => state.clusteringStatus === 'running',
  isPriorityCalculating: state => state.priorityStatus === 'running',
  clusteringResult: state => state.clusteringResult,
  priorityResult: state => state.priorityResult,
  analysisStats: state => state.stats
}

export default {
  namespaced: true,
  state,
  mutations,
  actions,
  getters
} 