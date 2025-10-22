<template>
  <div class="issue-management">
    <a-page-header title="问题管理" sub-title="管理和跟踪系统问题">
      <template #extra>
        <a-button type="primary" @click="showCreateDialog = true">
          <PlusOutlined />
          创建问题
        </a-button>
      </template>
    </a-page-header>

    <!-- 统计卡片 -->
    <a-row :gutter="16" class="stats-row">
      <a-col :span="6">
        <a-card class="stats-card">
          <a-statistic
            title="总问题数"
            :value="issueStats.total"
            :value-style="{ color: '#3f8600' }"
          />
        </a-card>
      </a-col>
      <a-col :span="6">
        <a-card class="stats-card">
          <a-statistic
            title="待解决"
            :value="issueStats.open"
            :value-style="{ color: '#cf1322' }"
          />
        </a-card>
      </a-col>
      <a-col :span="6">
        <a-card class="stats-card">
          <a-statistic
            title="处理中"
            :value="issueStats.in_progress"
            :value-style="{ color: '#1890ff' }"
          />
        </a-card>
      </a-col>
      <a-col :span="6">
        <a-card class="stats-card">
          <a-statistic
            title="已解决"
            :value="issueStats.resolved"
            :value-style="{ color: '#52c41a' }"
          />
        </a-card>
      </a-col>
    </a-row>

    <!-- 过滤器 -->
    <a-card class="filter-card">
      <a-row :gutter="16">
        <a-col :span="6">
          <a-input
            v-model:value="searchQuery"
            placeholder="搜索问题..."
            @input="handleSearch"
            allowClear
          >
            <template #prefix>
              <SearchOutlined />
            </template>
          </a-input>
        </a-col>
        <a-col :span="4">
          <a-select 
            v-model:value="statusFilter" 
            placeholder="选择状态" 
            @change="loadIssues" 
            allowClear
            style="width: 100%"
          >
            <a-select-option value="open">待解决</a-select-option>
            <a-select-option value="in_progress">处理中</a-select-option>
            <a-select-option value="resolved">已解决</a-select-option>
            <a-select-option value="closed">已关闭</a-select-option>
          </a-select>
        </a-col>
        <a-col :span="4">
          <a-select 
            v-model:value="severityFilter" 
            placeholder="选择严重程度" 
            @change="loadIssues" 
            allowClear
            style="width: 100%"
          >
            <a-select-option value="low">低</a-select-option>
            <a-select-option value="medium">中</a-select-option>
            <a-select-option value="high">高</a-select-option>
            <a-select-option value="critical">紧急</a-select-option>
          </a-select>
        </a-col>
        <a-col :span="4">
          <a-select 
            v-model:value="categoryFilter" 
            placeholder="选择分类" 
            @change="loadIssues" 
            allowClear
            style="width: 100%"
          >
            <a-select-option value="bug">功能缺陷</a-select-option>
            <a-select-option value="performance">性能问题</a-select-option>
            <a-select-option value="ux">用户体验</a-select-option>
            <a-select-option value="security">安全问题</a-select-option>
            <a-select-option value="other">其他</a-select-option>
          </a-select>
        </a-col>
        <a-col :span="6">
          <a-space>
            <a-button type="primary" @click="loadIssues">搜索</a-button>
            <a-button @click="resetFilters">重置</a-button>
          </a-space>
        </a-col>
      </a-row>
    </a-card>

    <!-- 问题列表 -->
    <a-card class="table-card">
      <a-table 
        :columns="issueColumns" 
        :data-source="issueList" 
        :loading="loading"
        :pagination="pagination"
        @change="handleTableChange"
      >
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'severity'">
            <a-tag :color="getSeverityColor(record.severity)">
              {{ getSeverityText(record.severity) }}
            </a-tag>
          </template>
          <template v-if="column.key === 'status'">
            <a-tag :color="getStatusColor(record.status)">
              {{ getStatusText(record.status) }}
            </a-tag>
          </template>
          <template v-if="column.key === 'action'">
            <a-space>
              <a-button type="link" size="small" @click="viewIssue(record)">
                详情
              </a-button>
              <a-button type="link" size="small" @click="editIssue(record)">
                编辑
              </a-button>
            </a-space>
          </template>
        </template>
      </a-table>
    </a-card>

    <!-- 创建问题对话框 -->
    <a-modal
      v-model:visible="showCreateDialog"
      title="创建问题"
      @ok="createIssue"
      @cancel="showCreateDialog = false"
    >
      <a-form
        :model="issueForm"
        :label-col="{ span: 6 }"
        :wrapper-col="{ span: 18 }"
      >
        <a-form-item label="问题标题">
          <a-input v-model:value="issueForm.title" placeholder="请输入问题标题" />
        </a-form-item>
        <a-form-item label="问题描述">
          <a-textarea
            v-model:value="issueForm.description"
            :rows="4"
            placeholder="请详细描述问题..."
          />
        </a-form-item>
        <a-form-item label="分类">
          <a-select v-model:value="issueForm.category" placeholder="选择分类">
            <a-select-option value="bug">功能缺陷</a-select-option>
            <a-select-option value="performance">性能问题</a-select-option>
            <a-select-option value="ux">用户体验</a-select-option>
            <a-select-option value="security">安全问题</a-select-option>
            <a-select-option value="other">其他</a-select-option>
          </a-select>
        </a-form-item>
        <a-form-item label="严重程度">
          <a-select v-model:value="issueForm.severity" placeholder="选择严重程度">
            <a-select-option value="low">低</a-select-option>
            <a-select-option value="medium">中</a-select-option>
            <a-select-option value="high">高</a-select-option>
            <a-select-option value="critical">紧急</a-select-option>
          </a-select>
        </a-form-item>
      </a-form>
    </a-modal>
  </div>
</template>

<script>
import { ref, reactive, onMounted } from 'vue'
import { message } from 'ant-design-vue'
import { PlusOutlined, SearchOutlined } from '@ant-design/icons-vue'

export default {
  name: 'IssueManagement',
  components: {
    PlusOutlined,
    SearchOutlined,
  },
  setup() {
    const loading = ref(false)
    const showCreateDialog = ref(false)
    const issueList = ref([])
    const searchQuery = ref('')
    const statusFilter = ref(undefined)
    const severityFilter = ref(undefined)
    const categoryFilter = ref(undefined)
    
    const issueStats = ref({
      total: 25,
      open: 8,
      in_progress: 5,
      resolved: 12
    })

    const pagination = ref({
      current: 1,
      pageSize: 10,
      total: 0,
      showSizeChanger: true,
      showQuickJumper: true,
    })

    const issueForm = reactive({
      title: '',
      description: '',
      category: undefined,
      severity: undefined,
    })

    const issueColumns = [
      { title: 'ID', dataIndex: 'id', key: 'id', width: 80 },
      { title: '标题', dataIndex: 'title', key: 'title', ellipsis: true },
      { title: '分类', dataIndex: 'category', key: 'category', width: 120 },
      { title: '严重程度', dataIndex: 'severity', key: 'severity', width: 120 },
      { title: '状态', dataIndex: 'status', key: 'status', width: 100 },
      { title: '创建时间', dataIndex: 'created_at', key: 'created_at', width: 150 },
      { title: '操作', key: 'action', width: 150, fixed: 'right' },
    ]

    const getSeverityColor = (severity) => {
      const colors = {
        low: 'green',
        medium: 'blue',
        high: 'orange',
        critical: 'red'
      }
      return colors[severity] || 'default'
    }

    const getSeverityText = (severity) => {
      const texts = {
        low: '低',
        medium: '中',
        high: '高',
        critical: '紧急'
      }
      return texts[severity] || severity
    }

    const getStatusColor = (status) => {
      const colors = {
        open: 'red',
        in_progress: 'blue',
        resolved: 'green',
        closed: 'default'
      }
      return colors[status] || 'default'
    }

    const getStatusText = (status) => {
      const texts = {
        open: '待解决',
        in_progress: '处理中',
        resolved: '已解决',
        closed: '已关闭'
      }
      return texts[status] || status
    }

    const loadIssues = () => {
      loading.value = true
      // 模拟数据
      setTimeout(() => {
        issueList.value = [
          {
            id: 1,
            title: '登录页面加载缓慢',
            category: 'performance',
            severity: 'high',
            status: 'open',
            created_at: '2024-01-01 10:30:00'
          },
          {
            id: 2,
            title: '用户头像上传失败',
            category: 'bug',
            severity: 'medium',
            status: 'in_progress',
            created_at: '2024-01-02 14:20:00'
          }
        ]
        pagination.value.total = issueList.value.length
        loading.value = false
      }, 1000)
    }

    const handleSearch = () => {
      // 搜索逻辑
      loadIssues()
    }

    const resetFilters = () => {
      searchQuery.value = ''
      statusFilter.value = undefined
      severityFilter.value = undefined
      categoryFilter.value = undefined
      loadIssues()
    }

    const handleTableChange = (pag) => {
      pagination.value = pag
      loadIssues()
    }

    const viewIssue = (record) => {
      message.info(`查看问题: ${record.title}`)
    }

    const editIssue = (record) => {
      message.info(`编辑问题: ${record.title}`)
    }

    const createIssue = () => {
      message.success('问题创建成功')
      showCreateDialog.value = false
      loadIssues()
    }

    onMounted(() => {
      loadIssues()
    })

    return {
      loading,
      showCreateDialog,
      issueList,
      issueStats,
      searchQuery,
      statusFilter,
      severityFilter,
      categoryFilter,
      pagination,
      issueForm,
      issueColumns,
      getSeverityColor,
      getSeverityText,
      getStatusColor,
      getStatusText,
      loadIssues,
      handleSearch,
      resetFilters,
      handleTableChange,
      viewIssue,
      editIssue,
      createIssue,
    }
  },
}
</script>

<style scoped>
.issue-management {
  padding: 24px;
}

.stats-row {
  margin-bottom: 24px;
}

.stats-card {
  text-align: center;
}

.filter-card {
  margin-bottom: 24px;
}

.table-card {
  margin-top: 16px;
}
</style> 