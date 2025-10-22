import { createStore } from 'vuex'
import dashboard from './modules/dashboard'
import feedback from './modules/feedback'
import analysis from './modules/analysis'
import issues from './modules/issues'
import insights from './modules/insights'

export default createStore({
  state: {
    loading: false,
    error: null,
    systemInfo: {
      name: '用户反馈分析系统',
      version: '1.0.0',
      apiUrl: process.env.VUE_APP_API_URL || 'http://localhost:8000/api/v1'
    }
  },
  
  mutations: {
    SET_LOADING(state, loading) {
      state.loading = loading
    },
    
    SET_ERROR(state, error) {
      state.error = error
    },
    
    CLEAR_ERROR(state) {
      state.error = null
    }
  },
  
  actions: {
    setLoading({ commit }, loading) {
      commit('SET_LOADING', loading)
    },
    
    setError({ commit }, error) {
      commit('SET_ERROR', error)
    },
    
    clearError({ commit }) {
      commit('CLEAR_ERROR')
    }
  },
  
  getters: {
    isLoading: state => state.loading,
    hasError: state => !!state.error,
    errorMessage: state => state.error,
    apiUrl: state => state.systemInfo.apiUrl
  },
  
  modules: {
    dashboard,
    feedback,
    analysis,
    issues,
    insights
  }
}) 