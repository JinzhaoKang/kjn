<template>
  <div class="analysis-reports">
    <a-page-header title="分析报告" sub-title="查看和导出智能分析报告" />
    
    <a-row :gutter="16" class="filter-row">
      <a-col :span="6">
        <a-select
          v-model:value="reportType"
          placeholder="选择报告类型"
          style="width: 100%"
          @change="loadReports"
        >
          <a-select-option value="summary">汇总报告</a-select-option>
          <a-select-option value="sentiment">情感分析报告</a-select-option>
          <a-select-option value="priority">优先级分析报告</a-select-option>
          <a-select-option value="trend">趋势分析报告</a-select-option>
        </a-select>
      </a-col>
      <a-col :span="6">
        <a-range-picker
          v-model:value="dateRange"
          style="width: 100%"
          @change="loadReports"
        />
      </a-col>
      <a-col :span="6">
        <a-button type="primary" @click="generateReport" :loading="generating">
          <FileTextOutlined />
          生成新报告
        </a-button>
      </a-col>
      <a-col :span="6">
        <a-button @click="exportReport">
          <DownloadOutlined />
          导出报告
        </a-button>
      </a-col>
    </a-row>
    
    <a-card title="报告列表" class="reports-card">
      <a-table 
        :columns="reportColumns" 
        :data-source="reports"
        :loading="loading"
        :pagination="pagination"
        @change="handleTableChange"
      >
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'type'">
            <a-tag :color="getTypeColor(record.type)">
              {{ getTypeText(record.type) }}
            </a-tag>
          </template>
          <template v-if="column.key === 'status'">
            <a-tag :color="getStatusColor(record.status)">
              {{ getStatusText(record.status) }}
            </a-tag>
          </template>
          <template v-if="column.key === 'action'">
            <a-space>
              <a-button type="link" size="small" @click="viewReport(record)">
                查看
              </a-button>
              <a-button type="link" size="small" @click="downloadReport(record)">
                下载
              </a-button>
              <a-button type="link" size="small" danger @click="deleteReport(record)">
                删除
              </a-button>
            </a-space>
          </template>
        </template>
      </a-table>
    </a-card>
    
    <!-- 报告详情抽屉 -->
    <a-drawer
      v-model:visible="showReportDetail"
      title="报告详情"
      placement="right"
      width="800"
    >
      <div v-if="selectedReport">
        <a-descriptions :column="2" bordered>
          <a-descriptions-item label="报告名称" :span="2">
            {{ selectedReport.name }}
          </a-descriptions-item>
          <a-descriptions-item label="报告类型">
            <a-tag :color="getTypeColor(selectedReport.type)">
              {{ getTypeText(selectedReport.type) }}
            </a-tag>
          </a-descriptions-item>
          <a-descriptions-item label="生成时间">
            {{ selectedReport.created_at }}
          </a-descriptions-item>
          <a-descriptions-item label="数据范围" :span="2">
            {{ selectedReport.date_range }}
          </a-descriptions-item>
        </a-descriptions>
        
        <a-divider />
        
        <div class="report-content">
          <h3>报告内容</h3>
          <div v-html="selectedReport.content"></div>
        </div>
      </div>
    </a-drawer>
  </div>
</template>

<script>
import { ref, onMounted } from 'vue'
import { message, Modal } from 'ant-design-vue'
import { FileTextOutlined, DownloadOutlined } from '@ant-design/icons-vue'

export default {
  name: 'AnalysisReports',
  components: {
    FileTextOutlined,
    DownloadOutlined,
  },
  setup() {
    const loading = ref(false)
    const generating = ref(false)
    const reports = ref([])
    const reportType = ref(undefined)
    const dateRange = ref([])
    const showReportDetail = ref(false)
    const selectedReport = ref(null)
    
    const pagination = ref({
      current: 1,
      pageSize: 10,
      total: 0,
      showSizeChanger: true,
      showQuickJumper: true,
    })
    
    const reportColumns = [
      { title: '报告名称', dataIndex: 'name', key: 'name' },
      { title: '类型', dataIndex: 'type', key: 'type' },
      { title: '状态', dataIndex: 'status', key: 'status' },
      { title: '生成时间', dataIndex: 'created_at', key: 'created_at' },
      { title: '数据范围', dataIndex: 'date_range', key: 'date_range' },
      { title: '操作', key: 'action', width: 200 },
    ]
    
    const getTypeColor = (type) => {
      const colors = {
        'summary': 'blue',
        'sentiment': 'green',
        'priority': 'orange',
        'trend': 'purple'
      }
      return colors[type] || 'default'
    }
    
    const getTypeText = (type) => {
      const texts = {
        'summary': '汇总报告',
        'sentiment': '情感分析',
        'priority': '优先级分析',
        'trend': '趋势分析'
      }
      return texts[type] || type
    }
    
    const getStatusColor = (status) => {
      const colors = {
        'completed': 'green',
        'generating': 'blue',
        'failed': 'red'
      }
      return colors[status] || 'default'
    }
    
    const getStatusText = (status) => {
      const texts = {
        'completed': '已完成',
        'generating': '生成中',
        'failed': '失败'
      }
      return texts[status] || status
    }
    
    const loadReports = () => {
      loading.value = true
      // 模拟数据
      setTimeout(() => {
        reports.value = [
          {
            id: 1,
            name: '用户反馈汇总报告 - 2024年1月',
            type: 'summary',
            status: 'completed',
            created_at: '2024-01-01 10:30:00',
            date_range: '2024-01-01 至 2024-01-31',
            content: '<h4>反馈汇总</h4><p>本月共收到用户反馈156条...</p>'
          },
          {
            id: 2,
            name: '情感分析报告 - 2024年1月',
            type: 'sentiment',
            status: 'completed',
            created_at: '2024-01-02 14:20:00',
            date_range: '2024-01-01 至 2024-01-31',
            content: '<h4>情感分析结果</h4><p>正面情感占比65%...</p>'
          }
        ]
        pagination.value.total = reports.value.length
        loading.value = false
      }, 1000)
    }
    
    const generateReport = () => {
      generating.value = true
      setTimeout(() => {
        message.success('报告生成请求已提交，请稍后查看')
        generating.value = false
        loadReports()
      }, 2000)
    }
    
    const exportReport = () => {
      message.info('报告导出功能开发中...')
    }
    
    const viewReport = (record) => {
      selectedReport.value = record
      showReportDetail.value = true
    }
    
    const downloadReport = (record) => {
      message.info(`下载报告: ${record.name}`)
    }
    
    const deleteReport = (record) => {
      Modal.confirm({
        title: '确认删除',
        content: `确定要删除报告"${record.name}"吗？`,
        onOk() {
          message.success('报告已删除')
          loadReports()
        },
      })
    }
    
    const handleTableChange = (pag) => {
      pagination.value = pag
      loadReports()
    }
    
    onMounted(() => {
      loadReports()
    })
    
    return {
      loading,
      generating,
      reports,
      reportType,
      dateRange,
      showReportDetail,
      selectedReport,
      pagination,
      reportColumns,
      getTypeColor,
      getTypeText,
      getStatusColor,
      getStatusText,
      loadReports,
      generateReport,
      exportReport,
      viewReport,
      downloadReport,
      deleteReport,
      handleTableChange,
    }
  },
}
</script>

<style scoped>
.analysis-reports {
  padding: 24px;
}

.filter-row {
  margin-bottom: 24px;
}

.reports-card {
  margin-top: 16px;
}

.report-content {
  margin-top: 16px;
}
</style> 