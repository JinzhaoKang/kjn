<template>
  <div class="feedback-import">
    <a-page-header title="反馈导入" sub-title="批量导入用户反馈数据" />
    
    <a-card title="导入反馈数据" class="import-card">
      <a-upload-dragger
        v-model:fileList="fileList"
        name="file"
        :multiple="false"
        :action="uploadUrl"
        @change="handleChange"
        :before-upload="beforeUpload"
        accept=".csv,.xlsx,.json"
      >
        <p class="ant-upload-drag-icon">
          <InboxOutlined />
        </p>
        <p class="ant-upload-text">点击或拖拽文件到此区域上传</p>
        <p class="ant-upload-hint">
          支持CSV、Excel、JSON格式文件，单次上传仅支持单个文件
        </p>
      </a-upload-dragger>
      
      <a-divider />
      
      <a-row :gutter="16">
        <a-col :span="8">
          <a-card size="small" title="文件格式要求">
            <p>CSV格式：包含title, content, category, email等字段</p>
            <p>Excel格式：第一行为标题行</p>
            <p>JSON格式：对象数组格式</p>
          </a-card>
        </a-col>
        <a-col :span="8">
          <a-card size="small" title="字段映射">
            <p>title: 反馈标题（必填）</p>
            <p>content: 反馈内容（必填）</p>
            <p>category: 分类（可选）</p>
            <p>email: 联系邮箱（可选）</p>
          </a-card>
        </a-col>
        <a-col :span="8">
          <a-card size="small" title="注意事项">
            <p>文件大小不超过10MB</p>
            <p>单次最多导入1000条记录</p>
            <p>重复数据将自动去重</p>
          </a-card>
        </a-col>
      </a-row>
    </a-card>
    
    <a-card title="导入历史" class="history-card" v-if="importHistory.length > 0">
      <a-table 
        :columns="historyColumns" 
        :data-source="importHistory"
        :pagination="false"
        size="small"
      >
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'status'">
            <a-tag :color="getStatusColor(record.status)">
              {{ getStatusText(record.status) }}
            </a-tag>
          </template>
          <template v-if="column.key === 'action'">
            <a-button type="link" size="small" @click="downloadReport(record)">
              下载报告
            </a-button>
          </template>
        </template>
      </a-table>
    </a-card>
  </div>
</template>

<script>
import { ref, onMounted } from 'vue'
import { message } from 'ant-design-vue'
import { InboxOutlined } from '@ant-design/icons-vue'

export default {
  name: 'FeedbackImport',
  components: {
    InboxOutlined,
  },
  setup() {
    const fileList = ref([])
    const importHistory = ref([])
    const uploadUrl = '/api/feedback/import'
    
    const historyColumns = [
      { title: '文件名', dataIndex: 'filename', key: 'filename' },
      { title: '导入数量', dataIndex: 'count', key: 'count' },
      { title: '状态', dataIndex: 'status', key: 'status' },
      { title: '导入时间', dataIndex: 'created_at', key: 'created_at' },
      { title: '操作', key: 'action' },
    ]
    
    const beforeUpload = (file) => {
      const isValidType = file.type === 'text/csv' || 
                         file.type === 'application/vnd.ms-excel' ||
                         file.type === 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' ||
                         file.type === 'application/json'
      if (!isValidType) {
        message.error('只支持CSV、Excel、JSON格式文件！')
        return false
      }
      const isLt10M = file.size / 1024 / 1024 < 10
      if (!isLt10M) {
        message.error('文件大小不能超过10MB！')
        return false
      }
      return true
    }
    
    const handleChange = (info) => {
      const { status } = info.file
      if (status === 'done') {
        message.success(`${info.file.name} 文件上传成功`)
        loadImportHistory()
      } else if (status === 'error') {
        message.error(`${info.file.name} 文件上传失败`)
      }
    }
    
    const getStatusColor = (status) => {
      const colors = {
        'success': 'green',
        'error': 'red',
        'processing': 'blue'
      }
      return colors[status] || 'default'
    }
    
    const getStatusText = (status) => {
      const texts = {
        'success': '成功',
        'error': '失败', 
        'processing': '处理中'
      }
      return texts[status] || '未知'
    }
    
    const downloadReport = (record) => {
      // 下载导入报告逻辑
      message.info('报告下载功能开发中...')
    }
    
    const loadImportHistory = () => {
      // 加载导入历史记录
      importHistory.value = [
        {
          id: 1,
          filename: 'feedback_data.csv',
          count: 156,
          status: 'success',
          created_at: '2024-01-01 10:30:00'
        }
      ]
    }
    
    onMounted(() => {
      loadImportHistory()
    })
    
    return {
      fileList,
      importHistory,
      uploadUrl,
      historyColumns,
      beforeUpload,
      handleChange,
      getStatusColor,
      getStatusText,
      downloadReport,
    }
  },
}
</script>

<style scoped>
.feedback-import {
  padding: 24px;
}

.import-card {
  margin-bottom: 24px;
}

.history-card {
  margin-top: 24px;
}
</style> 