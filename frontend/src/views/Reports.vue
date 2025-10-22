<template>
  <div class="reports">
    <a-page-header title="分析报告" sub-title="查看和管理系统分析报告">
      <template #extra>
        <a-button type="primary" @click="showGenerateDialog = true">
          <FileTextOutlined />
          生成新报告
        </a-button>
      </template>
    </a-page-header>

    <!-- 报告统计 -->
    <a-row :gutter="16" class="stats-row">
      <a-col :span="6">
        <a-card class="stats-card">
          <a-statistic
            title="总报告数"
            :value="reportStats.total"
            :value-style="{ color: '#3f8600' }"
          />
        </a-card>
      </a-col>
      <a-col :span="6">
        <a-card class="stats-card">
          <a-statistic
            title="本周生成"
            :value="reportStats.thisWeek"
            :value-style="{ color: '#1890ff' }"
          />
        </a-card>
      </a-col>
      <a-col :span="6">
        <a-card class="stats-card">
          <a-statistic
            title="自动生成"
            :value="reportStats.automated"
            :value-style="{ color: '#722ed1' }"
          />
        </a-card>
      </a-col>
      <a-col :span="6">
        <a-card class="stats-card">
          <a-statistic
            title="已下载"
            :value="reportStats.downloaded"
            :value-style="{ color: '#52c41a' }"
          />
        </a-card>
      </a-col>
    </a-row>

    <!-- 快速报告模板 -->
    <a-card title="快速报告模板" class="templates-card">
      <a-row :gutter="16">
        <a-col :span="6" v-for="template in reportTemplates" :key="template.id">
          <a-card
            class="template-card"
            :hoverable="true"
            @click="generateFromTemplate(template)"
          >
            <div class="template-content">
              <div class="template-icon">
                <component :is="template.icon" :style="{ color: template.color, fontSize: '32px' }" />
              </div>
              <div class="template-title">{{ template.title }}</div>
              <div class="template-description">{{ template.description }}</div>
            </div>
          </a-card>
        </a-col>
      </a-row>
    </a-card>

    <!-- 报告列表 -->
    <a-card title="报告列表" class="reports-list">
      <template #extra>
        <a-space>
          <a-select
            v-model:value="typeFilter"
            placeholder="报告类型"
            allowClear
            @change="loadReports"
            style="width: 120px"
          >
            <a-select-option value="weekly">周报</a-select-option>
            <a-select-option value="monthly">月报</a-select-option>
            <a-select-option value="custom">自定义</a-select-option>
            <a-select-option value="realtime">实时</a-select-option>
          </a-select>
          <a-select
            v-model:value="statusFilter"
            placeholder="状态"
            allowClear
            @change="loadReports"
            style="width: 120px"
          >
            <a-select-option value="generating">生成中</a-select-option>
            <a-select-option value="completed">已完成</a-select-option>
            <a-select-option value="failed">失败</a-select-option>
          </a-select>
        </a-space>
      </template>

      <a-table
        :columns="reportColumns"
        :data-source="reportList"
        :loading="loading"
        :pagination="pagination"
        @change="handleTableChange"
      >
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'type'">
            <a-tag :color="getTypeColor(record.type)">
              {{ getTypeLabel(record.type) }}
            </a-tag>
          </template>
          <template v-if="column.key === 'status'">
            <a-tag :color="getStatusColor(record.status)">
              {{ getStatusLabel(record.status) }}
            </a-tag>
          </template>
          <template v-if="column.key === 'action'">
            <a-space>
              <a-button type="link" size="small" @click="viewReport(record)">
                预览
              </a-button>
              <a-button
                type="link"
                size="small"
                @click="downloadReport(record)"
                v-if="record.status === 'completed'"
              >
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

    <!-- 报告预览抽屉 -->
    <a-drawer
      v-model:visible="showPreviewDrawer"
      title="报告预览"
      placement="right"
      width="800"
    >
      <div v-if="selectedReport">
        <a-descriptions :column="2" bordered>
          <a-descriptions-item label="报告标题" :span="2">
            {{ selectedReport.title }}
          </a-descriptions-item>
          <a-descriptions-item label="报告类型">
            <a-tag :color="getTypeColor(selectedReport.type)">
              {{ getTypeLabel(selectedReport.type) }}
            </a-tag>
          </a-descriptions-item>
          <a-descriptions-item label="生成时间">
            {{ selectedReport.created_at }}
          </a-descriptions-item>
          <a-descriptions-item label="文件大小" :span="2">
            {{ selectedReport.size }}
          </a-descriptions-item>
        </a-descriptions>

        <a-divider />

        <div class="report-preview">
          <h3>报告内容预览</h3>
          <div class="report-content">
            <p>{{ selectedReport.summary || '暂无预览内容' }}</p>
          </div>
        </div>
      </div>
    </a-drawer>

    <!-- 生成报告对话框 -->
    <a-modal
      v-model:visible="showGenerateDialog"
      title="生成新报告"
      @ok="confirmGenerate"
      @cancel="showGenerateDialog = false"
      width="600px"
    >
      <a-form
        :model="reportForm"
        :label-col="{ span: 6 }"
        :wrapper-col="{ span: 18 }"
      >
        <a-form-item label="报告标题">
          <a-input v-model:value="reportForm.title" placeholder="请输入报告标题" />
        </a-form-item>
        <a-form-item label="报告类型">
          <a-select v-model:value="reportForm.type" placeholder="请选择报告类型">
            <a-select-option value="weekly">周报</a-select-option>
            <a-select-option value="monthly">月报</a-select-option>
            <a-select-option value="custom">自定义</a-select-option>
            <a-select-option value="realtime">实时</a-select-option>
          </a-select>
        </a-form-item>
        <a-form-item label="时间范围">
          <a-range-picker
            v-model:value="reportForm.dateRange"
            format="YYYY-MM-DD"
          />
        </a-form-item>
        <a-form-item label="包含模块">
          <a-checkbox-group v-model:value="reportForm.modules">
            <a-checkbox value="feedback">反馈分析</a-checkbox>
            <a-checkbox value="issues">问题统计</a-checkbox>
            <a-checkbox value="trends">趋势分析</a-checkbox>
            <a-checkbox value="recommendations">建议汇总</a-checkbox>
          </a-checkbox-group>
        </a-form-item>
      </a-form>
    </a-modal>
  </div>
</template>

<script>
import { ref, reactive, onMounted } from 'vue'
import { message, Modal } from 'ant-design-vue'
import {
  FileTextOutlined,
  BarChartOutlined,
  PieChartOutlined,
  LineChartOutlined,
  TrophyOutlined,
} from '@ant-design/icons-vue'

export default {
  name: 'Reports',
  components: {
    FileTextOutlined,
    BarChartOutlined,
    PieChartOutlined,
    LineChartOutlined,
    TrophyOutlined,
  },
  setup() {
    const loading = ref(false)
    const showPreviewDrawer = ref(false)
    const showGenerateDialog = ref(false)
    const reportList = ref([])
    const selectedReport = ref(null)
    const typeFilter = ref(undefined)
    const statusFilter = ref(undefined)

    const reportStats = ref({
      total: 42,
      thisWeek: 8,
      automated: 15,
      downloaded: 28
    })

    const pagination = ref({
      current: 1,
      pageSize: 10,
      total: 0,
      showSizeChanger: true,
      showQuickJumper: true,
    })

    const reportForm = reactive({
      title: '',
      type: undefined,
      dateRange: [],
      modules: [],
    })

    const reportTemplates = ref([
      {
        id: 1,
        title: '周度汇总',
        description: '生成本周反馈汇总报告',
        icon: 'BarChartOutlined',
        color: '#1890ff'
      },
      {
        id: 2,
        title: '月度分析',
        description: '生成月度深度分析报告',
        icon: 'PieChartOutlined',
        color: '#52c41a'
      },
      {
        id: 3,
        title: '趋势报告',
        description: '生成趋势分析报告',
        icon: 'LineChartOutlined',
        color: '#faad14'
      },
      {
        id: 4,
        title: '优先级报告',
        description: '生成问题优先级报告',
        icon: 'TrophyOutlined',
        color: '#f5222d'
      }
    ])

    const reportColumns = [
      { title: 'ID', dataIndex: 'id', key: 'id', width: 80 },
      { title: '报告标题', dataIndex: 'title', key: 'title', ellipsis: true },
      { title: '类型', dataIndex: 'type', key: 'type', width: 100 },
      { title: '状态', dataIndex: 'status', key: 'status', width: 100 },
      { title: '生成时间', dataIndex: 'created_at', key: 'created_at', width: 150 },
      { title: '文件大小', dataIndex: 'size', key: 'size', width: 100 },
      { title: '操作', key: 'action', width: 200, fixed: 'right' },
    ]

    const getTypeColor = (type) => {
      const colors = {
        weekly: 'blue',
        monthly: 'green',
        custom: 'orange',
        realtime: 'purple'
      }
      return colors[type] || 'default'
    }

    const getTypeLabel = (type) => {
      const labels = {
        weekly: '周报',
        monthly: '月报',
        custom: '自定义',
        realtime: '实时'
      }
      return labels[type] || type
    }

    const getStatusColor = (status) => {
      const colors = {
        generating: 'blue',
        completed: 'green',
        failed: 'red'
      }
      return colors[status] || 'default'
    }

    const getStatusLabel = (status) => {
      const labels = {
        generating: '生成中',
        completed: '已完成',
        failed: '失败'
      }
      return labels[status] || status
    }

    const loadReports = () => {
      loading.value = true
      // 模拟数据
      setTimeout(() => {
        reportList.value = [
          {
            id: 1,
            title: '用户反馈周报 - 2024年第1周',
            type: 'weekly',
            status: 'completed',
            created_at: '2024-01-01 10:30:00',
            size: '2.5MB',
            summary: '本周共收到用户反馈156条，其中功能建议占60%，问题报告占30%，其他占10%。'
          },
          {
            id: 2,
            title: '月度分析报告 - 2024年1月',
            type: 'monthly',
            status: 'completed',
            created_at: '2024-01-02 14:20:00',
            size: '5.2MB',
            summary: '本月反馈量同比增长15%，用户满意度提升8%。'
          }
        ]
        pagination.value.total = reportList.value.length
        loading.value = false
      }, 1000)
    }

    const handleTableChange = (pag) => {
      pagination.value = pag
      loadReports()
    }

    const generateFromTemplate = (template) => {
      message.success(`正在生成${template.title}...`)
      loadReports()
    }

    const viewReport = (record) => {
      selectedReport.value = record
      showPreviewDrawer.value = true
    }

    const downloadReport = (record) => {
      message.success(`开始下载报告: ${record.title}`)
    }

    const deleteReport = (record) => {
      Modal.confirm({
        title: '确认删除',
        content: `确定要删除报告"${record.title}"吗？`,
        onOk() {
          message.success('报告已删除')
          loadReports()
        },
      })
    }

    const confirmGenerate = () => {
      message.success('报告生成请求已提交')
      showGenerateDialog.value = false
      loadReports()
    }

    onMounted(() => {
      loadReports()
    })

    return {
      loading,
      showPreviewDrawer,
      showGenerateDialog,
      reportList,
      reportStats,
      selectedReport,
      typeFilter,
      statusFilter,
      pagination,
      reportForm,
      reportTemplates,
      reportColumns,
      getTypeColor,
      getTypeLabel,
      getStatusColor,
      getStatusLabel,
      loadReports,
      handleTableChange,
      generateFromTemplate,
      viewReport,
      downloadReport,
      deleteReport,
      confirmGenerate,
    }
  },
}
</script>

<style scoped>
.reports {
  padding: 24px;
}

.stats-row {
  margin-bottom: 24px;
}

.stats-card {
  text-align: center;
}

.templates-card {
  margin-bottom: 24px;
}

.template-card {
  text-align: center;
  cursor: pointer;
}

.template-content {
  padding: 16px;
}

.template-icon {
  margin-bottom: 12px;
}

.template-title {
  font-size: 16px;
  font-weight: 500;
  margin-bottom: 8px;
}

.template-description {
  color: var(--text-color-secondary);
  font-size: 12px;
}

.reports-list {
  margin-top: 16px;
}

.report-preview {
  margin-top: 16px;
}

.report-content {
  background: var(--background-color-light);
  border: 1px solid var(--border-color-split);
  padding: 20px;
  border-radius: var(--border-radius-lg);
  margin-top: 16px;
  color: var(--text-color);
  font-size: 14px;
  line-height: 1.6;
  min-height: 200px;
  box-shadow: var(--box-shadow-card);
  transition: all var(--animation-duration-base);
  
  p {
    margin: 0;
    word-wrap: break-word;
    white-space: pre-wrap;
  }
  
  &:empty::after {
    content: '暂无预览内容';
    color: var(--text-color-disabled);
    font-style: italic;
    display: flex;
    align-items: center;
    justify-content: center;
    height: 100%;
  }
}

.report-preview {
  h3 {
    color: var(--text-color);
    font-size: 16px;
    font-weight: 600;
    margin-bottom: 12px;
    border-bottom: 2px solid var(--primary-color);
    padding-bottom: 8px;
    display: inline-block;
  }
}

/* 抽屉内容样式优化 */
:deep(.ant-drawer-body) {
  background: var(--background-color);
}

:deep(.ant-descriptions) {
  background: var(--background-color);
}

:deep(.ant-descriptions-item-label) {
  background: var(--background-color-light);
  color: var(--text-color);
  font-weight: 500;
}

:deep(.ant-descriptions-item-content) {
  background: var(--background-color);
  color: var(--text-color);
}

:deep(.ant-divider) {
  border-color: var(--border-color-split);
}
</style> 