<template>
  <div class="feedback-management">
    <a-page-header title="反馈管理" sub-title="管理和处理用户反馈">
      <template #extra>
        <a-space>
          <a-button 
            type="primary"
            :loading="analyzing"
            @click="triggerAnalyzeAll"
            style="background: #52c41a; border-color: #52c41a;"
          >
            🤖 一键AI分析
          </a-button>
          <a-button 
            type="primary"
            :loading="reanalyzing"
            @click="triggerForceReanalyze"
            style="background: #722ed1; border-color: #722ed1;"
          >
            🔄 优化重新分析
          </a-button>
        <a-button type="primary" @click="showCreateDialog = true">
          <PlusOutlined />
          添加反馈
        </a-button>
        </a-space>
      </template>
    </a-page-header>

    <!-- 搜索和过滤 -->
    <a-card class="filter-card">
      <a-row :gutter="16">
        <a-col :span="8">
          <a-input
            v-model:value="searchQuery"
            placeholder="搜索反馈内容..."
            @pressEnter="handleSearch"
            allowClear
          >
            <template #prefix>
              <SearchOutlined />
            </template>
          </a-input>
        </a-col>
        <a-col :span="5">
          <a-select 
            v-model:value="statusFilter" 
            placeholder="选择状态" 
            @change="loadFeedback" 
            allowClear
            style="width: 100%"
          >
            <a-select-option value="pending">待处理</a-select-option>
            <a-select-option value="processing">处理中</a-select-option>
            <a-select-option value="completed">已完成</a-select-option>
            <a-select-option value="rejected">已拒绝</a-select-option>
          </a-select>
        </a-col>
        <a-col :span="5">
          <a-select 
            v-model:value="categoryFilter" 
            placeholder="选择分类" 
            @change="loadFeedback" 
            allowClear
            style="width: 100%"
          >
            <a-select-option value="feature">功能建议</a-select-option>
            <a-select-option value="bug">问题报告</a-select-option>
            <a-select-option value="ux">用户体验</a-select-option>
            <a-select-option value="performance">性能优化</a-select-option>
            <a-select-option value="other">其他</a-select-option>
          </a-select>
        </a-col>
        <a-col :span="6">
          <a-space>
            <a-button type="primary" @click="loadFeedback">搜索</a-button>
            <a-button @click="resetFilters">重置</a-button>
          </a-space>
        </a-col>
      </a-row>
    </a-card>

    <!-- 反馈列表 -->
    <a-card class="table-card">
      <a-table
        :columns="feedbackColumns"
        :data-source="feedbackList"
        :loading="loading"
        :pagination="pagination"
        :row-selection="rowSelection"
        @change="handleTableChange"
        size="small"
      >
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'feedback_content'">
            <div class="feedback-wrapper">
              <div class="feedback-card">
                <div class="feedback-header" v-if="getFeedbackTitle(record)">
                  <span class="title-icon">💬</span>
                  <span class="feedback-title">{{ getFeedbackTitle(record) }}</span>
                </div>
                <div class="feedback-body">
                  <div class="feedback-content" :class="{ 'expanded': record.expanded }">
                    {{ getFeedbackContent(record) }}
                  </div>
                  
                  <!-- 关键词显示在内容下方 -->
                  <div v-if="record.keywords && record.keywords.length > 0" class="keywords-section">
                    <span class="keywords-label">🏷️ 关键词：</span>
                    <span class="keywords-text">{{ record.keywords.slice(0, 5).join(' · ') }}{{ record.keywords.length > 5 ? '...' : '' }}</span>
                  </div>
                  
                  <!-- 分析状态标识 -->
                  <div class="analysis-status" v-if="record.analysis_result || record.processing_status">
                    <span class="analysis-indicators">
                      <!-- AI分析状态 -->
                      <span 
                        v-if="(record.analysis_result && record.analysis_result.analysis_method === 'multi_model_ai') || 
                              (record.processing_status && record.processing_status.analysis_method === 'multi_model_ai')" 
                        class="analysis-check ai-analyzed"
                        title="已完成AI分析"
                      >
                        ✅ AI分析
                      </span>
                      <!-- 预筛选状态 -->
                      <span 
                        v-else-if="(record.analysis_result && record.analysis_result.analysis_method === 'intelligent_filter') || 
                                   (record.processing_status && record.processing_status.analysis_method === 'intelligent_filter')"
                        class="analysis-check pre-filtered"
                        title="已预筛选处理"
                      >
                        ⚡ 预筛选
                      </span>
                      <!-- 情感标识 -->
                      <span 
                        v-if="record.sentiment" 
                        :class="['sentiment-indicator', `sentiment-${record.sentiment}`]"
                        :title="`情感：${getSentimentLabel(record.sentiment)}`"
                      >
                        {{ getSentimentLabel(record.sentiment) }}
                      </span>
                      <!-- 置信度 -->
                      <span 
                        v-if="record.ai_confidence && record.ai_confidence > 0"
                        class="confidence-indicator"
                        :title="`AI分析置信度：${Math.round(record.ai_confidence * 100)}%`"
                      >
                        {{ Math.round(record.ai_confidence * 100) }}%
                      </span>
                    </span>
                  </div>
                  
                  <a-button 
                    v-if="needsExpansion(record)" 
                    type="link" 
                    size="small" 
                    class="expand-btn"
                    @click="toggleExpansion(record)"
                  >
                    <template #icon>
                      <component :is="record.expanded ? 'UpOutlined' : 'DownOutlined'" />
                    </template>
                    {{ record.expanded ? '收起' : '展开' }}
                  </a-button>
                </div>
              </div>
            </div>
          </template>
          
          <template v-if="column.key === 'source'">
            <a-tag :color="getSourceColor(record.source)" class="modern-source-tag">
              <component :is="getSourceIcon(record.source)" class="tag-icon" />
              <span>{{ getSourceLabel(record.source) }}</span>
            </a-tag>
          </template>
          
          <template v-if="column.key === 'category'">
            <a-tag :color="getCategoryColor(record.category)" class="category-main-tag">
              {{ getCategoryLabel(record.category) }}
            </a-tag>
          </template>
          
          <template v-if="column.key === 'status'">
            <div class="status-indicator">
              <span :class="['status-dot', getStatusClass(record.status)]"></span>
              <span class="status-text">{{ getStatusLabel(record.status) }}</span>
            </div>
          </template>
          
          <template v-if="column.key === 'priority'">
            <a-tag :color="getPriorityColor(record.priority)" class="priority-badge">
              {{ getPriorityText(record.priority) }}
            </a-tag>
          </template>
          
          <template v-if="column.key === 'created_at'">
            <div class="time-display">
              <div class="relative-time">{{ getRelativeTime(record.created_at) }}</div>
              <div class="absolute-time">{{ formatAbsoluteTime(record.created_at) }}</div>
            </div>
          </template>
        </template>
      </a-table>
    </a-card>

    <!-- 创建/编辑反馈对话框 -->
    <a-modal
      v-model:visible="showCreateDialog"
      :title="editingFeedback ? '编辑反馈' : '创建反馈'"
      @ok="saveFeedback"
      @cancel="cancelEdit"
      width="600px"
    >
      <a-form
        :model="feedbackForm"
        :label-col="{ span: 6 }"
        :wrapper-col="{ span: 18 }"
        ref="feedbackFormRef"
      >
        <a-form-item label="标题" name="title" :rules="[{ required: true, message: '请输入反馈标题' }]">
          <a-input v-model:value="feedbackForm.title" placeholder="请输入反馈标题" />
        </a-form-item>
        <a-form-item label="内容" name="content" :rules="[{ required: true, message: '请输入反馈内容' }]">
          <a-textarea
            v-model:value="feedbackForm.content"
            :rows="4"
            placeholder="请详细描述您的反馈..."
          />
        </a-form-item>
        <a-form-item label="分类" name="category" :rules="[{ required: true, message: '请选择反馈分类' }]">
          <a-select v-model:value="feedbackForm.category" placeholder="请选择分类">
            <a-select-option value="feature">功能建议</a-select-option>
            <a-select-option value="bug">问题报告</a-select-option>
            <a-select-option value="ux">用户体验</a-select-option>
            <a-select-option value="performance">性能优化</a-select-option>
            <a-select-option value="other">其他</a-select-option>
          </a-select>
        </a-form-item>
        <a-form-item label="优先级" name="priority">
          <a-select v-model:value="feedbackForm.priority" placeholder="请选择优先级">
            <a-select-option value="low">低</a-select-option>
            <a-select-option value="normal">普通</a-select-option>
            <a-select-option value="high">高</a-select-option>
            <a-select-option value="urgent">紧急</a-select-option>
          </a-select>
        </a-form-item>
        <a-form-item label="联系邮箱" name="email">
          <a-input v-model:value="feedbackForm.email" placeholder="请输入您的邮箱地址" />
        </a-form-item>
      </a-form>
    </a-modal>

    <!-- 查看反馈详情抽屉 -->
    <a-drawer
      v-model:visible="showViewDialog"
      title="反馈详情"
      placement="right"
      width="600"
    >
      <div v-if="selectedFeedback">
        <a-descriptions :column="2" bordered>
          <a-descriptions-item label="ID">
            {{ selectedFeedback.id }}
          </a-descriptions-item>
          <a-descriptions-item label="状态">
            <a-tag :color="getStatusColor(selectedFeedback.status)">
              {{ getStatusLabel(selectedFeedback.status) }}
            </a-tag>
          </a-descriptions-item>
          <a-descriptions-item label="标题" :span="2">
            {{ selectedFeedback.title }}
          </a-descriptions-item>
          <a-descriptions-item label="分类">
            <a-tag :color="getCategoryColor(selectedFeedback.category)">
              {{ getCategoryLabel(selectedFeedback.category) }}
            </a-tag>
          </a-descriptions-item>
          <a-descriptions-item label="优先级">
            <a-tag :color="getPriorityColor(selectedFeedback.priority)">
              {{ getPriorityText(selectedFeedback.priority) }}
            </a-tag>
          </a-descriptions-item>
          <a-descriptions-item label="创建时间" :span="2">
            {{ selectedFeedback.created_at }}
          </a-descriptions-item>
          <a-descriptions-item label="联系邮箱" :span="2">
            {{ selectedFeedback.email || '未提供' }}
          </a-descriptions-item>
          <a-descriptions-item label="反馈内容" :span="2">
            <div class="feedback-content">
              {{ selectedFeedback.content }}
            </div>
          </a-descriptions-item>
        </a-descriptions>
      </div>
    </a-drawer>
  </div>
</template>

<script>
import { ref, reactive, onMounted } from 'vue'
import { message, Modal } from 'ant-design-vue'
import { 
  PlusOutlined, 
  SearchOutlined,
  AppleOutlined,
  AndroidOutlined,
  GlobalOutlined,
  TeamOutlined,
  CustomerServiceOutlined,
  SettingOutlined,
  UserOutlined,
  UpOutlined,
  DownOutlined
} from '@ant-design/icons-vue'
import { feedbackAPI } from '@/utils/api'

export default {
  name: 'FeedbackManagement',
  components: {
    PlusOutlined,
    SearchOutlined,
    AppleOutlined,
    AndroidOutlined,
    GlobalOutlined,
    TeamOutlined,
    CustomerServiceOutlined,
    SettingOutlined,
    UserOutlined,
    UpOutlined,
    DownOutlined,
  },
  setup() {
    const loading = ref(false)
    const analyzing = ref(false)
    const reanalyzing = ref(false)
    const feedbackList = ref([])
    const selectedFeedback = ref(null)
    const showCreateDialog = ref(false)
    const showViewDialog = ref(false)
    const editingFeedback = ref(null)
    const feedbackFormRef = ref(null)
    
    const searchQuery = ref('')
    const statusFilter = ref(undefined)
    const categoryFilter = ref(undefined)
    
    const pagination = ref({
      current: 1,
      pageSize: 50,
      total: 0,
      showSizeChanger: true,
      showQuickJumper: true,
      showTotal: (total, range) => `第 ${range[0]}-${range[1]} 条，共 ${total} 条`,
      pageSizeOptions: ['20', '50', '100', '200'],
    })

    const feedbackForm = reactive({
      title: '',
      content: '',
      category: undefined,
      priority: 'normal',
      email: ''
    })

    const feedbackColumns = [
      { 
        title: '反馈内容', 
        dataIndex: 'feedback_content', 
        key: 'feedback_content', 
        ellipsis: true,
        width: '55%'
      },
      { 
        title: '来源渠道', 
        dataIndex: 'source', 
        key: 'source', 
        width: '12%',
        align: 'center'
      },
      { 
        title: '问题分类', 
        dataIndex: 'category', 
        key: 'category', 
        width: '10%',
        align: 'center'
      },
      { 
        title: '处理状态', 
        dataIndex: 'status', 
        key: 'status', 
        width: '10%',
        align: 'center'
      },
      { 
        title: '优先级', 
        dataIndex: 'priority', 
        key: 'priority', 
        width: '8%',
        align: 'center'
      },
      { 
        title: '提交时间', 
        dataIndex: 'created_at', 
        key: 'created_at', 
        width: '10%',
        align: 'center'
      },
    ]

    const rowSelection = {
      onChange: (selectedRowKeys, selectedRows) => {
        console.log('选中的反馈:', selectedRows)
      },
    }

    const getStatusColor = (status) => {
      const colors = {
        pending: 'orange',
        processing: 'blue',
        completed: 'green',
        rejected: 'red'
      }
      return colors[status] || 'default'
    }

    const getStatusLabel = (status) => {
      const labels = {
        pending: '待处理',
        processing: '处理中',
        completed: '已完成',
        rejected: '已拒绝'
      }
      return labels[status] || status
    }

    const getCategoryColor = (category) => {
      const colors = {
        feature: 'blue',
        feature_request: 'blue',
        bug: 'red',
        bug_report: 'red',
        ux: 'green',
        ux_complaint: 'green',
        performance: 'orange',
        question: 'cyan',
        praise: 'green',
        general: 'default',
        other: 'default'
      }
      return colors[category] || 'default'
    }

    const getCategoryLabel = (category) => {
      const labels = {
        feature: '功能建议',
        feature_request: '功能需求',
        bug: '问题报告',
        bug_report: 'Bug报告',
        ux: '用户体验',
        ux_complaint: 'UX投诉',
        performance: '性能优化',
        question: '咨询问题',
        praise: '表扬反馈',
        general: '通用反馈',
        other: '其他'
      }
      return labels[category] || category
    }

    const getPriorityColor = (priority) => {
      const colors = {
        low: 'green',      // 低优先级 - 绿色
        medium: 'orange',  // 中等优先级 - 橙色
        normal: 'orange',  // 普通优先级 - 橙色
        high: 'red',       // 高优先级 - 红色
        urgent: 'volcano'  // 紧急优先级 - 深红色
      }
      return colors[priority] || 'orange'
    }

    const getPriorityText = (priority) => {
      const texts = {
        low: '低',
        medium: '中等',
        normal: '普通',
        high: '高',
        urgent: '紧急'
      }
      return texts[priority] || priority
    }

    // 获取反馈标题 - 优先获取独立标题字段
    const getFeedbackTitle = (record) => {
      // 优先使用title字段，如果没有则从内容提取前几个字作为标题
      if (record.title && record.title.trim()) {
        const cleanTitle = record.title.replace(/\s+/g, ' ').trim()
        return cleanTitle.length > 30 ? cleanTitle.substring(0, 30) + '...' : cleanTitle
      }
      
      // 如果没有独立标题，从内容中提取前20个字符作为标题
      const content = record.original_text || record.content || record.original_content || record.processed_text || ''
      if (content) {
        const cleanContent = content.replace(/\s+/g, ' ').trim()
        return cleanContent.length > 20 ? cleanContent.substring(0, 20) + '...' : cleanContent
      }
      
      return '无标题'
    }

    // 获取反馈内容 - 显示完整反馈内容
    const getFeedbackContent = (record) => {
      const content = record.original_text || record.content || record.original_content || record.processed_text || ''
      if (!content) return '暂无内容'
      
      // 保留换行符，只替换多余的空白
      const cleanContent = content.replace(/[ \t]+/g, ' ').trim()
      
      if (record.expanded) {
        return cleanContent
      }
      
      return cleanContent.length > 120 ? cleanContent.substring(0, 120) + '...' : cleanContent
    }

    // 判断是否需要展开
    const needsExpansion = (record) => {
      const content = record.original_text || record.content || record.original_content || record.processed_text || ''
      const cleanContent = content.replace(/[ \t]+/g, ' ').trim()
      return cleanContent.length > 120
    }

    // 切换展开状态
    const toggleExpansion = (record) => {
      // 使用Vue的响应式更新
      const index = feedbackList.value.findIndex(item => item._id === record._id)
      if (index !== -1) {
        feedbackList.value[index].expanded = !feedbackList.value[index].expanded
      }
    }

    // 来源配置 - 行业标准
    const getSourceIcon = (source) => {
      const icons = {
        app_store: 'AppleOutlined',
        google_play: 'AndroidOutlined', 
        social_media: 'GlobalOutlined',
        internal: 'TeamOutlined',
        zendesk: 'CustomerServiceOutlined',
        user_survey: 'SettingOutlined'
      }
      return icons[source] || 'SettingOutlined'
    }

    const getSourceLabel = (source) => {
      const labels = {
        app_store: 'App Store',
        ios_app_store: 'iOS App Store',
        android_app_store: 'Android应用市场',
        google_play: 'Google Play',
        huawei_app_store: '华为应用市场',
        xiaomi_app_store: '小米应用市场',
        vivo_app_store: 'vivo应用市场',
        oppo_app_store: 'OPPO应用市场',
        meizu_app_store: '魅族应用市场',
        social_media: '社交平台',
        internal: '内部系统',
        zendesk: '客服工单',
        user_survey: '用户调研'
      }
      return labels[source] || source || 'Unknown'
    }

    // 情感分析显示
    const getSentimentColor = (sentiment) => {
      const colors = {
        positive: 'green',
        negative: 'red',
        neutral: 'default'
      }
      return colors[sentiment] || 'default'
    }

    const getSentimentLabel = (sentiment) => {
      const labels = {
        positive: '正面',
        negative: '负面', 
        neutral: '中性'
      }
      return labels[sentiment] || sentiment
    }

    // 分析方法显示
    const getAnalysisMethodColor = (method) => {
      const colors = {
        'multi_model_ai': 'green',
        'intelligent_filter': 'orange',
        'content_empty': 'red',
        'manual': 'blue'
      }
      return colors[method] || 'default'
    }

    const getAnalysisMethodLabel = (method) => {
      const labels = {
        'multi_model_ai': 'AI分析',
        'intelligent_filter': '预筛选',
        'content_empty': '内容空',
        'manual': '手动'
      }
      return labels[method] || method
    }

    // 模型显示
    const getModelLabel = (model) => {
      if (!model || model === 'none') return ''
      
      // 提取模型简称
      if (model.includes('gemini')) {
        return 'Gemini'
      } else if (model.includes('gpt')) {
        return 'GPT'
      } else if (model.includes('claude')) {
        return 'Claude'
      } else if (model === 'default') {
        return '默认'
      } else if (model === 'intelligent_filter') {
        return '预筛选'
      }
      return model.substring(0, 10) // 限制长度
    }

    const getSourceColor = (source) => {
      const colors = {
        app_store: 'blue',
        google_play: 'green',
        social_media: 'purple',
        internal: 'orange',
        zendesk: 'cyan',
        user_survey: 'geekblue'
      }
      return colors[source] || 'default'
    }

    // 状态徽章 - 行业标准
    const getStatusBadge = (status) => {
      const badges = {
        pending: 'processing',
        in_progress: 'processing', 
        resolved: 'success',
        closed: 'default'
      }
      return badges[status] || 'default'
    }

    // 获取状态样式类
    const getStatusClass = (status) => {
      const classes = {
        pending: 'status-pending',
        in_progress: 'status-processing', 
        resolved: 'status-success',
        closed: 'status-default'
      }
      return classes[status] || 'status-default'
    }

    // 相对时间显示
    const getRelativeTime = (timeStr) => {
      if (!timeStr) return '--'
      
      try {
        const date = new Date(timeStr)
        const now = new Date()
        const diff = now.getTime() - date.getTime()
        
        const minutes = Math.floor(diff / (1000 * 60))
        const hours = Math.floor(diff / (1000 * 60 * 60))
        const days = Math.floor(diff / (1000 * 60 * 60 * 24))
        
        if (minutes < 1) return '刚刚'
        if (minutes < 60) return `${minutes}分钟前`
        if (hours < 24) return `${hours}小时前`
        if (days < 7) return `${days}天前`
        if (days < 30) return `${Math.floor(days / 7)}周前`
        return `${Math.floor(days / 30)}个月前`
      } catch (error) {
        return '--'
      }
    }

    // 绝对时间显示
    const formatAbsoluteTime = (timeStr) => {
      if (!timeStr) return '--'
      
      try {
        const date = new Date(timeStr)
        const month = (date.getMonth() + 1).toString().padStart(2, '0')
        const day = date.getDate().toString().padStart(2, '0')
        const hour = date.getHours().toString().padStart(2, '0')
        const minute = date.getMinutes().toString().padStart(2, '0')
        
        return `${month}-${day} ${hour}:${minute}`
      } catch (error) {
        return '--'
      }
    }

    const loadFeedback = async () => {
      loading.value = true
      try {
        // 构建查询参数
        const params = {
          skip: (pagination.value.current - 1) * pagination.value.pageSize,
          limit: pagination.value.pageSize
        }
        
        // 添加过滤条件
        if (statusFilter.value) {
          params.status = statusFilter.value
        }
        if (categoryFilter.value) {
          params.source = categoryFilter.value
        }
        
        // 调用真实API
        const response = await feedbackAPI.getFeedbacks(params)
        
        if (response.data) {
          feedbackList.value = (response.data.data || []).map(item => ({
            ...item,
            expanded: false // 初始化展开状态
          }))
          pagination.value.total = response.data.total || 0
          
          console.log('✅ 从数据库加载反馈数据:', {
            总数: pagination.value.total,
            当前页: feedbackList.value.length,
            页码: pagination.value.current
          })
        }
      } catch (error) {
        console.error('❌ 加载反馈数据失败:', error)
        message.error('加载反馈数据失败：' + (error.response?.data?.detail || error.message))
        
        // 出错时清空数据
        feedbackList.value = []
        pagination.value.total = 0
      } finally {
        loading.value = false
      }
    }

    const handleSearch = () => {
      pagination.value.current = 1
      loadFeedback()
    }

    const resetFilters = () => {
      searchQuery.value = ''
      statusFilter.value = undefined
      categoryFilter.value = undefined
      pagination.value.current = 1
      loadFeedback()
    }

    const handleTableChange = (pag, filters, sorter) => {
      pagination.value = pag
      loadFeedback()
    }

    const viewFeedback = (feedback) => {
      selectedFeedback.value = feedback
      showViewDialog.value = true
    }

    const editFeedback = (feedback) => {
      editingFeedback.value = feedback
      Object.assign(feedbackForm, {
        title: feedback.title,
        content: feedback.content,
        category: feedback.category,
        priority: feedback.priority,
        email: feedback.email
      })
      showCreateDialog.value = true
    }

    const analyzeFeedback = (feedback) => {
      Modal.confirm({
        title: '确认分析',
        content: '确定要对此反馈进行智能分析吗？',
        onOk() {
          message.success('分析任务已启动')
          loadFeedback()
        },
      })
    }

    const deleteFeedback = async (feedback) => {
      Modal.confirm({
        title: '确认删除',
        content: `确定要删除反馈"${feedback.title}"吗？此操作不可恢复。`,
        okType: 'danger',
        async onOk() {
          try {
            await feedbackAPI.deleteFeedback(feedback.id)
            message.success('反馈删除成功')
            loadFeedback()
          } catch (error) {
            message.error('删除失败：' + (error.response?.data?.detail || error.message))
          }
        },
      })
    }

    const saveFeedback = () => {
      feedbackFormRef.value
        .validate()
        .then(() => {
          if (editingFeedback.value) {
            message.success('反馈更新成功')
          } else {
            message.success('反馈创建成功')
          }
          showCreateDialog.value = false
          resetForm()
          loadFeedback()
        })
        .catch(() => {
          message.error('请检查表单内容')
        })
    }

    const cancelEdit = () => {
      showCreateDialog.value = false
      resetForm()
    }

    const resetForm = () => {
      Object.assign(feedbackForm, {
        title: '',
        content: '',
        category: undefined,
        priority: 'normal',
        email: ''
      })
      editingFeedback.value = null
      feedbackFormRef.value?.resetFields()
    }

    onMounted(() => {
      loadFeedback()
    })

    // 一键AI分析功能
    const triggerAnalyzeAll = async () => {
      analyzing.value = true
      try {
        const response = await feedbackAPI.analyzeAllUnprocessed()
        const data = response.data
        
        if (data.unanalyzed_count === 0) {
          message.success('🎉 所有反馈数据都已完成AI分析！')
        } else {
          message.success(`🚀 成功启动AI分析！正在处理 ${data.unanalyzed_count} 条反馈数据，预计需要 ${data.analysis_details.estimated_time}`)
          
          // 延迟刷新数据，给AI分析一些时间
          setTimeout(() => {
            loadFeedback()
          }, 3000)
        }
        
        console.log('✅ AI分析任务启动成功:', data)
      } catch (error) {
        console.error('❌ AI分析启动失败:', error)
        message.error('AI分析启动失败：' + (error.response?.data?.detail || error.message))
      } finally {
        analyzing.value = false
      }
    }

    // 强制重新分析功能（使用改进的AI prompt）
    const triggerForceReanalyze = async () => {
      reanalyzing.value = true
      try {
        const response = await feedbackAPI.forceReanalyzeAll()
        const data = response.data
        
        message.success(`🔄 ${data.message}`)
        
        // 延迟刷新数据，给AI重新分析一些时间
        setTimeout(() => {
          loadFeedback()
        }, 5000)
        
        console.log('✅ 强制重新分析启动成功:', data)
      } catch (error) {
        console.error('❌ 强制重新分析启动失败:', error)
        message.error('强制重新分析启动失败：' + (error.response?.data?.detail || error.message))
      } finally {
        reanalyzing.value = false
      }
    }

    return {
      loading,
      analyzing,
      reanalyzing,
      feedbackList,
      selectedFeedback,
      showCreateDialog,
      showViewDialog,
      editingFeedback,
      feedbackFormRef,
      searchQuery,
      statusFilter,
      categoryFilter,
      pagination,
      feedbackForm,
      feedbackColumns,
      rowSelection,
      getStatusColor,
      getStatusLabel,
      getCategoryColor,
      getCategoryLabel,
      getPriorityColor,
      getPriorityText,
      getFeedbackTitle,
      getFeedbackContent,
      needsExpansion,
      toggleExpansion,
      getSourceIcon,
      getSourceLabel,
      getSourceColor,
      getStatusClass,
      getRelativeTime,
      formatAbsoluteTime,
      getSentimentColor,
      getSentimentLabel,
      getAnalysisMethodColor,
      getAnalysisMethodLabel,
      getModelLabel,
      loadFeedback,
      handleSearch,
      resetFilters,
      handleTableChange,
      viewFeedback,
      editFeedback,
      analyzeFeedback,
      deleteFeedback,
      saveFeedback,
      cancelEdit,
      resetForm,
      triggerAnalyzeAll,
      triggerForceReanalyze,
    }
  },
}
</script>

<style scoped>
.feedback-management {
  padding: 24px;
}

.filter-card {
  margin-bottom: 24px;
}

.table-card {
  margin-top: 16px;
}

.feedback-content {
  background: #f5f5f5;
  padding: 12px;
  border-radius: 4px;
  word-break: break-word;
}

/* 现代表格样式 */
:deep(.ant-table) {
  border-radius: 8px;
  border: 1px solid #f0f0f0;
  background: transparent;
}

:deep(.ant-table-thead > tr > th) {
  background: linear-gradient(135deg, #fafafa 0%, #f5f5f5 100%);
  border-bottom: 1px solid #e8e8e8;
  font-weight: 600;
  color: #262626;
  padding: 8px 12px;
  font-size: 13px;
}

:deep(.ant-table-tbody > tr) {
  transition: background-color 0.2s ease;
  border-bottom: 1px solid #f8f8f8;
}

:deep(.ant-table-tbody > tr:hover) {
  background: rgba(24, 144, 255, 0.02);
}

  :deep(.ant-table-tbody > tr > td) {
    padding: 8px 12px;
    border-bottom: 1px solid #f8f8f8;
    background: transparent;
    vertical-align: middle;
  }

/* 反馈内容包装器 */
.feedback-wrapper {
  width: 100%;
  padding: 4px 0;
}

  .feedback-card {
    background: transparent;
    border: 1px solid rgba(0, 0, 0, 0.08);
    border-radius: 4px;
    padding: 8px 10px;
    transition: all 0.2s ease;
  }
  
  .feedback-card:hover {
    background: rgba(24, 144, 255, 0.03);
    border-color: rgba(24, 144, 255, 0.15);
  }

/* 反馈标题区域 */
.feedback-header {
  display: flex;
  align-items: center;
  margin-bottom: 6px;
  gap: 6px;
}

.title-icon {
  font-size: 14px;
  opacity: 0.8;
}

  .feedback-title {
    font-weight: 600;
    color: #262626;
    font-size: 14px;
    line-height: 1.3;
    flex: 1;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
    max-width: 280px;
  }

/* 反馈内容区域 */
.feedback-body {
  position: relative;
}

  .feedback-content {
    color: #595959;
    font-size: 13px;
    line-height: 1.5;
    margin-bottom: 8px;
    max-height: 65px;
    overflow: hidden;
    transition: max-height 0.3s ease;
    word-break: break-word;
    word-wrap: break-word;
    white-space: pre-wrap;
    background: transparent;
  }

.feedback-content.expanded {
  max-height: none;
}

/* 关键词区域样式 */
.keywords-section {
  margin: 6px 0;
  padding: 4px 8px;
  background: rgba(24, 144, 255, 0.05);
  border-left: 3px solid #1890ff;
  border-radius: 3px;
}

.keywords-label {
  font-size: 12px;
  color: #1890ff;
  font-weight: 600;
  margin-right: 6px;
}

.keywords-text {
  font-size: 12px;
  color: #595959;
  font-weight: 500;
}

/* 分析状态区域 */
.analysis-status {
  margin: 6px 0 3px 0;
}

.analysis-indicators {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

/* 分析方法状态 */
.analysis-check {
  display: inline-flex;
  align-items: center;
  padding: 3px 8px;
  border-radius: 12px;
  font-size: 11px;
  font-weight: 600;
  border: 1px solid;
  background: transparent;
}

.analysis-check.ai-analyzed {
  color: #52c41a;
  border-color: #52c41a;
  background: rgba(82, 196, 26, 0.08);
}

.analysis-check.pre-filtered {
  color: #fa8c16;
  border-color: #fa8c16;
  background: rgba(250, 140, 22, 0.08);
}

/* 情感指示器 */
.sentiment-indicator {
  display: inline-flex;
  align-items: center;
  padding: 2px 6px;
  border-radius: 8px;
  font-size: 11px;
  font-weight: 500;
  border: 1px solid;
}

.sentiment-indicator.sentiment-positive {
  color: #52c41a;
  border-color: #52c41a;
  background: rgba(82, 196, 26, 0.1);
}

.sentiment-indicator.sentiment-negative {
  color: #ff4d4f;
  border-color: #ff4d4f;
  background: rgba(255, 77, 79, 0.1);
}

.sentiment-indicator.sentiment-neutral {
  color: #8c8c8c;
  border-color: #d9d9d9;
  background: rgba(140, 140, 140, 0.1);
}

/* 置信度指示器 */
.confidence-indicator {
  display: inline-flex;
  align-items: center;
  padding: 2px 6px;
  border-radius: 8px;
  font-size: 11px;
  font-weight: 600;
  color: #722ed1;
  border: 1px solid #722ed1;
  background: rgba(114, 46, 209, 0.08);
}

/* 分类主标签 */
.category-main-tag {
  font-weight: 600;
  font-size: 13px;
}

  .expand-btn {
    padding: 4px 8px;
    height: auto;
    font-size: 12px;
    color: #1890ff;
    background: transparent;
    border: 1px solid rgba(24, 144, 255, 0.3);
    border-radius: 4px;
    display: inline-flex;
    align-items: center;
    gap: 4px;
    transition: all 0.2s ease;
  }

  .expand-btn:hover {
    color: #40a9ff;
    background: rgba(24, 144, 255, 0.05);
    border-color: rgba(24, 144, 255, 0.4);
  }

/* 来源标签 */
.modern-source-tag {
  border-radius: 6px;
  border: 1px solid;
  font-size: 12px;
  font-weight: 500;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 4px;
  padding: 6px 10px;
  background: transparent;
}

.tag-icon {
  font-size: 12px;
}

/* 分类标签 */
.category-tag {
  border-radius: 6px;
  font-size: 12px;
  font-weight: 500;
  border: 1px solid;
  background: transparent;
  padding: 6px 10px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
}

/* 状态指示器 */
.status-indicator {
  display: flex;
  align-items: center;
  gap: 8px;
  justify-content: center;
}

.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  display: inline-block;
}

.status-pending {
  background: #faad14;
}

.status-processing {
  background: #1890ff;
}

.status-success {
  background: #52c41a;
}

.status-default {
  background: #d9d9d9;
}

.status-text {
  font-size: 13px;
  color: #595959;
  font-weight: 500;
}

/* 优先级徽章 */
.priority-badge {
  border-radius: 6px;
  font-size: 12px;
  font-weight: 500;
  border: 1px solid;
  background: transparent;
  padding: 6px 10px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
}

  /* 时间显示 */
  .time-display {
    text-align: center;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    height: 100%;
  }

.relative-time {
  font-size: 13px;
  color: #262626;
  font-weight: 500;
  line-height: 1.2;
}

.absolute-time {
  font-size: 12px;
  color: #8c8c8c;
  line-height: 1.1;
  margin-top: 3px;
}

/* 暗黑模式适配 */
@media (prefers-color-scheme: dark) {
  :deep(.ant-table) {
    background: transparent;
    border-color: #424242;
  }
  
  :deep(.ant-table-thead > tr > th) {
    background: linear-gradient(135deg, #2a2a2a 0%, #1f1f1f 100%);
    color: #ffffff;
    border-bottom: 1px solid #424242;
  }
  
  :deep(.ant-table-tbody > tr:hover) {
    background: rgba(255, 255, 255, 0.02);
  }
  
  :deep(.ant-table-tbody > tr > td) {
    border-bottom: 1px solid #424242;
    color: #ffffff;
  }
  
      .feedback-card {
      background: transparent;
      border-color: rgba(255, 255, 255, 0.1);
    }
    
    .feedback-card:hover {
      background: rgba(24, 144, 255, 0.05);
      border-color: rgba(24, 144, 255, 0.3);
    }
  
  .feedback-title {
    color: #ffffff;
  }
  
  .feedback-content {
    color: #cccccc;
  }
  
      .expand-btn {
      color: #91d5ff;
      background: transparent;
      border-color: rgba(145, 213, 255, 0.5);
    }
    
    .expand-btn:hover {
      color: #69c0ff;
      background: rgba(105, 192, 255, 0.08);
    }
    
    .modern-source-tag, .category-tag, .priority-badge {
      background: transparent;
    }
  
  .relative-time {
    color: #ffffff;
  }
  
  .absolute-time {
    color: #999999;
  }
  
  .status-text {
    color: #cccccc;
  }
}
</style> 