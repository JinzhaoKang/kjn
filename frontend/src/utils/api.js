import axios from 'axios'
import { message } from 'ant-design-vue'

// 创建axios实例 - 不设置baseURL，使用Vue代理
const api = axios.create({
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json'
  }
})

// 请求拦截器
api.interceptors.request.use(
  config => {
    // 添加认证token（如果有）
    const token = localStorage.getItem('auth_token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    
    console.log('🚀 API请求:', config.method?.toUpperCase(), config.url, config.params)
    return config
  },
  error => {
    message.error('请求配置错误')
    return Promise.reject(error)
  }
)

// 响应拦截器
api.interceptors.response.use(
  response => {
    console.log('✅ API响应:', response.config.url, response.status)
    return response
  },
  error => {
    const { response } = error
    
    if (response) {
      const { status, data } = response
      console.error('❌ API错误:', response.config.url, status, data)
      
      switch (status) {
        case 400:
          message.error(data.detail || '请求参数错误')
          break
        case 401:
          message.error('未授权，请重新登录')
          break
        case 403:
          message.error('拒绝访问')
          break
        case 404:
          message.error(data.detail || '请求的资源不存在')
          break
        case 422:
          message.error(data.detail || '数据验证失败')
          break
        case 500:
          message.error(data.detail || '服务器内部错误')
          break
        default:
          message.error(data.detail || `请求失败 (${status})`)
      }
    } else {
      console.error('❌ 网络错误:', error.message)
      message.error('网络连接失败，请检查网络设置')
    }
    
    return Promise.reject(error)
  }
)

// 业务API封装
export const feedbackAPI = {
  // 获取反馈列表
  getFeedbacks(params = {}) {
    return api.get('/api/v1/feedback/', { params })
  },
  
  // 兼容旧的方法名
  getFeedback(params = {}) {
    return this.getFeedbacks(params)
  },
  
  // 获取单个反馈详情
  getFeedbackById(id) {
    return api.get(`/api/v1/feedback/${id}`)
  },
  
  // 添加反馈
  addFeedback(data) {
    return api.post('/api/v1/feedback', data)
  },
  
  // 更新反馈
  updateFeedback(id, data) {
    return api.put(`/api/v1/feedback/${id}`, data)
  },
  
  // 删除反馈
  deleteFeedback(id) {
    return api.delete(`/api/v1/feedback/${id}`)
  },
  
  // 批量操作
  batchUpdate(data) {
    return api.post('/api/v1/feedback/batch', data)
  },
  
  // 导出反馈
  exportFeedback(params = {}) {
    return api.get('/api/v1/feedback/export', { 
      params,
      responseType: 'blob'
    })
  },
  
  // 分析所有未处理的反馈
  analyzeAllUnprocessed() {
    return api.post('/api/v1/spider/analyze-all-unprocessed')
  },
  
  // 强制重新分析所有反馈（使用改进的AI prompt）
  forceReanalyzeAll() {
    return api.post('/api/v1/spider/force-reanalyze-all')
  },
  
  // 批量分析指定反馈
  batchAnalyze(feedbackIds, options = {}) {
    return api.post('/api/v1/spider/batch-ai-analysis', {
      feedback_ids: feedbackIds,
      ...options
    })
  },
  
  // 获取分析状态
  getAnalysisStatus() {
    return api.get('/api/v1/spider/processing-stats')
  }
}

export const analysisAPI = {
  // 触发聚类分析
  triggerClustering(data) {
    return api.post('/api/v1/analysis/clustering/trigger', data)
  },
  
  // 获取聚类结果
  getClusteringResults(params) {
    return api.get('/api/v1/analysis/clustering/results', { params })
  },
  
  // 获取混合分析结果
  getHybridAnalysis(params) {
    return api.get('/api/v1/analysis/hybrid', { params })
  },
  
  // 获取聚类统计
  getClusteringStats() {
    return api.get('/api/v1/analysis/clustering/stats')
  },
  
  // 计算优先级
  calculatePriority(data) {
    return api.post('/api/v1/analysis/priority/calculate', data)
  }
}

// 洞察生成API
export const insightsAPI = {
  // 生成常规洞察和执行计划（基于最近一个月数据）
  generateInsights(data) {
    const requestData = {
      feedback_limit: data?.feedback_limit || 50,
      include_action_plans: data?.include_action_plans !== false,
      filters: data?.filters || {},
      use_recent_data_only: true  // 常规洞察使用最近一个月数据
    }
    return api.post('/api/v1/insights/generate', requestData)
  },
  
  // 全文洞察生成 - 基于所有历史数据
  generateFullTextInsights(data) {
    const requestData = {
      feedback_limit: data?.feedback_limit || 350,
      filters: data?.filters || {},
      analysis_focus: data?.analysis_focus || 'comprehensive',
      use_all_history: true  // 全文洞察使用所有历史数据
    }
    return api.post('/api/v1/insights/generate-full-text', requestData)
  },
  
  // 手动生成洞察
  generateManualInsights(data) {
    return api.post('/api/v1/insights/generate-manual', data)
  },
  
  // 获取洞察演示
  getInsightsDemo() {
    return api.get('/api/v1/insights/demo')
  },
  
  // 健康检查
  checkInsightsHealth() {
    return api.get('/api/v1/insights/health')
  },

  // 新增洞察会话管理API
  saveInsightSession(data) {
    return api.post('/api/v1/insights/sessions/save', data)
  },
  
  getLatestInsightSession() {
    return api.get('/api/v1/insights/sessions/latest')
  },
  
  getInsightSessions(params = {}) {
    return api.get('/api/v1/insights/sessions', { params })
  },
  
  getInsightSession(sessionId) {
    return api.get(`/api/v1/insights/sessions/${sessionId}`)
  },
  
  deleteInsightSession(sessionId) {
    return api.delete(`/api/v1/insights/sessions/${sessionId}`)
  }
}

export const dashboardAPI = {
  // 获取总览数据
  getOverview(daysBack = 30) {
    return api.get('/api/v1/dashboard/overview', { params: { days_back: daysBack } })
  },
  
  // 获取情感趋势
  getSentimentTrend(daysBack = 30) {
    return api.get('/api/v1/dashboard/sentiment-trend', { params: { days_back: daysBack } })
  },
  
  // 获取话题分布
  getTopicDistribution(params) {
    return api.get('/api/v1/dashboard/topic-distribution', { params })
  },
  
  // 获取优先级矩阵
  getPriorityMatrix() {
    return api.get('/api/v1/dashboard/priority-matrix')
  },
  
  // 获取来源分析
  getSourceAnalysis(daysBack = 30) {
    return api.get('/api/v1/dashboard/source-analysis', { params: { days_back: daysBack } })
  }
}

// 决策引擎API
export const decisionEngineAPI = {
  // 健康检查
  getHealth() {
    return api.get('/api/v1/decision-engine/health')
  },
  
  // 获取权重配置
  getWeightsConfig() {
    return api.get('/api/v1/decision-engine/weights/config')
  },
  
  // 计算优先级得分
  calculatePriority(data) {
    return api.post('/api/v1/decision-engine/priority/calculate', data)
  },
  
  // 生成行动计划
  generateActionPlan(data) {
    return api.post('/api/v1/decision-engine/action-plan/generate', data)
  },
  
  // 获取分析概览
  getAnalyticsOverview() {
    return api.get('/api/v1/decision-engine/analytics/overview')
  },
  
  // 获取Top优先级洞察
  getTopPriorityInsights(limit = 10) {
    return api.get('/api/v1/decision-engine/insights/top-priorities', { params: { limit } })
  }
}

export const spiderAPI = {
  // 获取爬虫统计信息
  getStatistics() {
    return api.get('/api/v1/spider/statistics')
  },
  
  // 获取任务列表
  getTaskList() {
    return api.get('/api/v1/spider/task/list')
  },
  
  // 获取运行中的任务
  getRunningTasks() {
    return api.get('/api/v1/spider/task/running')
  },
  
  // 创建七麦iOS爬虫任务
  createQimaiTask(data) {
    return api.post('/api/v1/spider/qimai/create', data)
  },

  // 创建七麦Android爬虫任务
  createQimaiAndroidTask(data) {
    return api.post('/api/v1/spider/qimai-android/create', data)
  },
  
  // 运行任务
  runTask(taskId) {
    return api.post(`/api/v1/spider/task/${taskId}/run`)
  },
  
  // 暂停任务
  pauseTask(taskId) {
    return api.post(`/api/v1/spider/task/${taskId}/pause`)
  },

  // 恢复任务
  resumeTask(taskId) {
    return api.post(`/api/v1/spider/task/${taskId}/resume`)
  },
  
  // 停止任务
  stopTask(taskId) {
    return api.post(`/api/v1/spider/task/${taskId}/stop`)
  },
  
  // 获取任务状态
  getTaskStatus(taskId) {
    return api.get(`/api/v1/spider/task/${taskId}/status`)
  },

  // 预览任务数据
  previewTaskData(taskId, limit = 10) {
    return api.get(`/api/v1/spider/task/${taskId}/preview`, { params: { limit } })
  },

  // 导入任务数据
  importTaskData(taskId, enableAiAnalysis = true) {
    return api.post(`/api/v1/spider/task/${taskId}/import-data`, null, { 
      params: { enable_ai_analysis: enableAiAnalysis } 
    })
  },

  // 清理过期任务
  cleanupTasks() {
    return api.delete('/api/v1/spider/task/cleanup')
  }
}

export const settingsAPI = {
  // 获取设置
  getSettings() {
    return api.get('/api/v1/system/settings')
  },
  
  // 更新设置
  updateSettings(data) {
    return api.post('/api/v1/system/settings', data)
  },
  
  // 获取LLM模型列表
  getLLMModels() {
    return api.get('/api/v1/system/llm/models')
  }
}

// 健康检查
export const healthAPI = {
  checkHealth() {
    return api.get('/health')
  }
}

// 默认导出
export default api 