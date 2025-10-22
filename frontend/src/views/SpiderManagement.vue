<template>
  <div class="spider-management">
    <!-- 页面头部 -->
    <div class="page-header">
      <div class="header-content">
        <h1 class="page-title">
          <a-icon type="spider" />
          爬虫管理
        </h1>
        <p class="page-description">管理和监控爬虫任务，自动化采集用户反馈数据</p>
      </div>
      <div class="header-actions">
        <a-button type="primary" @click="showCreateTaskModal" :loading="loading">
          <template #icon><PlusOutlined /></template>
          创建爬虫任务
        </a-button>
        <a-button @click="refreshTaskList" :loading="refreshing">
          <template #icon><ReloadOutlined /></template>
          刷新
        </a-button>
      </div>
    </div>

    <!-- 统计卡片 -->
    <div class="stats-cards">
      <a-spin :spinning="statisticsLoading">
        <a-row :gutter="16">
          <a-col :span="6">
            <a-card>
              <a-statistic
                title="总任务数"
                :value="statistics.total_tasks"
                :value-style="{ color: '#1890ff' }"
              >
                <template #prefix><DatabaseOutlined /></template>
              </a-statistic>
            </a-card>
          </a-col>
          <a-col :span="6">
            <a-card>
              <a-statistic
                title="运行中"
                :value="statistics.running_tasks"
                :value-style="{ color: '#52c41a' }"
              >
                <template #prefix><PlayCircleOutlined /></template>
              </a-statistic>
            </a-card>
          </a-col>
          <a-col :span="6">
            <a-card>
              <a-statistic
                title="已完成"
                :value="statistics.completed_tasks"
                :value-style="{ color: '#13c2c2' }"
              >
                <template #prefix><CheckCircleOutlined /></template>
              </a-statistic>
            </a-card>
          </a-col>
          <a-col :span="6">
            <a-card>
              <a-statistic
                title="失败数"
                :value="statistics.failed_tasks"
                :value-style="{ color: '#ff4d4f' }"
              >
                <template #prefix><CloseCircleOutlined /></template>
              </a-statistic>
            </a-card>
          </a-col>
        </a-row>
      </a-spin>
    </div>

    <!-- 任务列表 -->
    <div class="task-list">
      <a-card title="爬虫任务列表" :bordered="false">
        <template #extra>
          <a-space>
            <a-select v-model:value="statusFilter" placeholder="筛选状态" style="width: 120px" allow-clear>
              <a-select-option value="idle">空闲</a-select-option>
              <a-select-option value="running">运行中</a-select-option>
              <a-select-option value="completed">已完成</a-select-option>
              <a-select-option value="error">失败</a-select-option>
              <a-select-option value="paused">暂停</a-select-option>
            </a-select>
            <a-button @click="cleanupTasks" type="text" danger>
              <template #icon><DeleteOutlined /></template>
              清理过期任务
            </a-button>
          </a-space>
        </template>

        <a-table 
          :columns="taskColumns" 
          :data-source="filteredTasks" 
          :loading="tasksLoading"
          :pagination="{ pageSize: 10, showSizeChanger: true, showQuickJumper: true }"
          row-key="task_id"
        >
          <template #bodyCell="{ column, record }">
            <template v-if="column.key === 'status'">
              <a-tag :color="getStatusColor(record.status)">
                {{ getStatusText(record.status) }}
              </a-tag>
            </template>

            <template v-if="column.key === 'duration'">
              {{ formatDuration(record.duration) }}
            </template>

            <template v-if="column.key === 'progress'">
              <div v-if="record.status === 'running' && record.spider_status">
                <a-progress 
                  :percent="getTaskProgress(record)" 
                  size="small" 
                  :status="record.status === 'error' ? 'exception' : 'active'"
                />
                <div class="progress-info">
                  <span>{{ record.spider_status.metrics?.total_items || 0 }} 条数据</span>
                  <span>{{ (record.spider_status.metrics?.items_per_second || 0).toFixed(1) }} 条/秒</span>
                </div>
              </div>
              <div v-else-if="record.result_summary">
                <a-tag color="success">{{ record.result_summary.data_count }} 条数据</a-tag>
              </div>
            </template>

            <template v-if="column.key === 'actions'">
              <a-space>
                <a-tooltip title="查看详情">
                  <a-button type="text" @click="showTaskDetail(record)" size="small">
                    <template #icon><EyeOutlined /></template>
                  </a-button>
                </a-tooltip>

                <a-tooltip title="运行任务" v-if="record.status === 'idle'">
                  <a-button type="text" @click="runTask(record.task_id)" size="small">
                    <template #icon><PlayCircleOutlined /></template>
                  </a-button>
                </a-tooltip>

                <a-tooltip title="暂停任务" v-if="record.status === 'running'">
                  <a-button type="text" @click="pauseTask(record.task_id)" size="small">
                    <template #icon><PauseCircleOutlined /></template>
                  </a-button>
                </a-tooltip>

                <a-tooltip title="恢复任务" v-if="record.status === 'paused'">
                  <a-button type="text" @click="resumeTask(record.task_id)" size="small">
                    <template #icon><PlayCircleOutlined /></template>
                  </a-button>
                </a-tooltip>

                <a-tooltip title="停止任务" v-if="['running', 'paused'].includes(record.status)">
                  <a-button type="text" danger @click="stopTask(record.task_id)" size="small">
                    <template #icon><StopOutlined /></template>
                  </a-button>
                </a-tooltip>

                <a-tooltip title="预览数据" v-if="record.status === 'completed'">
                  <a-button type="text" @click="previewTaskData(record.task_id)" size="small">
                    <template #icon><FileSearchOutlined /></template>
                  </a-button>
                </a-tooltip>

                <a-tooltip title="导入数据" v-if="record.status === 'completed'">
                  <a-button type="text" @click="importData(record.task_id)" size="small">
                    <template #icon><ImportOutlined /></template>
                  </a-button>
                </a-tooltip>
              </a-space>
            </template>
          </template>
        </a-table>
      </a-card>
    </div>

    <!-- 创建任务Modal -->
    <a-modal
      v-model:open="createTaskModalVisible"
      title="创建爬虫任务"
      @ok="createTask"
      @cancel="resetCreateForm"
      :confirm-loading="createTaskLoading"
      width="600px"
    >
      <a-form
        ref="createFormRef"
        :model="createForm"
        :rules="createFormRules"
        layout="vertical"
      >
        <!-- 平台选择 -->
        <a-form-item label="抓取平台" name="platform">
          <a-radio-group v-model:value="createForm.platform" @change="onPlatformChange">
            <a-radio value="ios">iOS App Store</a-radio>
            <a-radio value="android">Android应用市场</a-radio>
          </a-radio-group>
        </a-form-item>

        <!-- iOS配置 -->
        <div v-if="createForm.platform === 'ios'">
          <a-row :gutter="16">
            <a-col :span="12">
              <a-form-item label="应用ID" name="appid">
                <a-input 
                  v-model:value="createForm.appid" 
                  placeholder="输入App Store应用ID"
                  :maxlength="20"
                />
              </a-form-item>
            </a-col>
            <a-col :span="12">
              <a-form-item label="国家/地区" name="country">
                <a-select v-model:value="createForm.country" placeholder="选择国家">
                  <a-select-option value="cn">中国</a-select-option>
                  <a-select-option value="us">美国</a-select-option>
                  <a-select-option value="jp">日本</a-select-option>
                  <a-select-option value="kr">韩国</a-select-option>
                  <a-select-option value="uk">英国</a-select-option>
                </a-select>
              </a-form-item>
            </a-col>
          </a-row>

          <a-form-item label="回溯天数" name="days_back">
            <a-input-number 
              v-model:value="createForm.days_back" 
              :min="1" 
              :max="3650"
              placeholder="回溯天数"
              style="width: 100%"
            />
          </a-form-item>
        </div>

        <!-- Android配置 -->
        <div v-if="createForm.platform === 'android'">
          <a-form-item label="应用市场" name="market">
            <a-select v-model:value="createForm.market" placeholder="选择应用市场">
              <a-select-option value="4">小米应用市场</a-select-option>
              <a-select-option value="6">华为应用市场</a-select-option>
              <a-select-option value="7">魅族应用市场</a-select-option>
              <a-select-option value="8">vivo应用市场</a-select-option>
              <a-select-option value="9">oppo应用市场</a-select-option>
            </a-select>
          </a-form-item>
        </div>

        <!-- 通用配置 -->
        <a-form-item label="最大页数" name="max_pages">
          <a-input-number 
            v-model:value="createForm.max_pages" 
            :min="1" 
            :max="1000"
            placeholder="最大抓取页数"
            style="width: 100%"
          />
        </a-form-item>

        <a-form-item label="任务名称" name="task_name">
          <a-input 
            v-model:value="createForm.task_name" 
            placeholder="可选，不填写将自动生成"
            :maxlength="50"
          />
        </a-form-item>

        <a-form-item label="执行方式" name="execution_mode">
          <a-radio-group v-model:value="createForm.execution_mode">
            <a-radio value="async">后台执行</a-radio>
            <a-radio value="sync">立即执行</a-radio>
          </a-radio-group>
        </a-form-item>
      </a-form>
    </a-modal>

    <!-- 任务详情Modal -->
    <a-modal
      v-model:open="taskDetailModalVisible"
      :title="`任务详情 - ${selectedTask?.task_id}`"
      :footer="null"
      width="800px"
    >
      <div v-if="selectedTask">
        <a-descriptions :column="2" bordered>
          <a-descriptions-item label="任务ID">{{ selectedTask.task_id }}</a-descriptions-item>
          <a-descriptions-item label="状态">
            <a-tag :color="getStatusColor(selectedTask.status)">
              {{ getStatusText(selectedTask.status) }}
            </a-tag>
          </a-descriptions-item>
          <a-descriptions-item label="创建时间">{{ formatTime(selectedTask.created_at) }}</a-descriptions-item>
          <a-descriptions-item label="开始时间">{{ formatTime(selectedTask.started_at) }}</a-descriptions-item>
          <a-descriptions-item label="完成时间">{{ formatTime(selectedTask.completed_at) }}</a-descriptions-item>
          <a-descriptions-item label="执行时长">{{ formatDuration(selectedTask.duration) }}</a-descriptions-item>
        </a-descriptions>

        <a-divider>任务参数</a-divider>
        <a-descriptions :column="2" bordered>
          <a-descriptions-item label="平台">{{ getTaskPlatformName(selectedTask.task_params) }}</a-descriptions-item>
          <a-descriptions-item v-if="selectedTask.task_params?.appid" label="应用ID">{{ selectedTask.task_params.appid }}</a-descriptions-item>
          <a-descriptions-item v-if="selectedTask.task_params?.country" label="国家">{{ selectedTask.task_params.country }}</a-descriptions-item>
          <a-descriptions-item v-if="selectedTask.task_params?.days_back" label="回溯天数">{{ selectedTask.task_params.days_back }}</a-descriptions-item>
          <a-descriptions-item v-if="selectedTask.task_params?.market" label="应用市场">{{ selectedTask.task_params.market_name || `市场${selectedTask.task_params.market}` }}</a-descriptions-item>
          <a-descriptions-item label="最大页数">{{ selectedTask.task_params?.max_pages }}</a-descriptions-item>
        </a-descriptions>

        <a-divider v-if="selectedTask.spider_status">执行指标</a-divider>
        <a-descriptions v-if="selectedTask.spider_status" :column="2" bordered>
          <a-descriptions-item label="总请求数">{{ selectedTask.spider_status.metrics?.total_requests || 0 }}</a-descriptions-item>
          <a-descriptions-item label="成功请求">{{ selectedTask.spider_status.metrics?.successful_requests || 0 }}</a-descriptions-item>
          <a-descriptions-item label="失败请求">{{ selectedTask.spider_status.metrics?.failed_requests || 0 }}</a-descriptions-item>
          <a-descriptions-item label="成功率">{{ ((selectedTask.spider_status.metrics?.success_rate || 0) * 100).toFixed(1) }}%</a-descriptions-item>
          <a-descriptions-item label="抓取条目">{{ selectedTask.spider_status.metrics?.total_items || 0 }}</a-descriptions-item>
          <a-descriptions-item label="有效条目">{{ selectedTask.spider_status.metrics?.valid_items || 0 }}</a-descriptions-item>
          <a-descriptions-item label="处理速度">{{ (selectedTask.spider_status.metrics?.items_per_second || 0).toFixed(2) }} 条/秒</a-descriptions-item>
        </a-descriptions>

        <div v-if="selectedTask.error" style="margin-top: 16px;">
          <a-alert
            type="error"
            :message="selectedTask.error"
            show-icon
          />
        </div>
      </div>
    </a-modal>

    <!-- 数据预览Modal -->
    <a-modal
      v-model:open="previewModalVisible"
      title="数据预览"
      :footer="null"
      width="1000px"
    >
      <div v-if="previewData">
        <a-descriptions :column="3" bordered style="margin-bottom: 16px;">
          <a-descriptions-item label="总数据量">{{ previewData.total_count }}</a-descriptions-item>
          <a-descriptions-item label="预览数量">{{ previewData.preview_count }}</a-descriptions-item>
          <a-descriptions-item label="任务状态">{{ previewData.task_info?.status }}</a-descriptions-item>
        </a-descriptions>

        <a-table
          :columns="previewColumns"
          :data-source="previewData.preview_data"
          :pagination="false"
          size="small"
          :scroll="{ x: 1200 }"
        >
          <template #bodyCell="{ column, record }">
            <template v-if="column.key === 'sentiment'">
              <a-tag :color="getSentimentColor(record.sentiment)">
                {{ getSentimentText(record.sentiment) }}
              </a-tag>
            </template>
            
            <template v-if="column.key === 'priority'">
              <a-tag :color="getPriorityColor(record.priority)">
                {{ record.priority }}
              </a-tag>
            </template>
            
            <template v-if="column.key === 'content'">
              <div style="max-width: 300px; overflow: hidden; text-overflow: ellipsis;">
                {{ record.content }}
              </div>
            </template>
          </template>
        </a-table>
      </div>
    </a-modal>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, onUnmounted } from 'vue'
import { message, Modal } from 'ant-design-vue'
import {
  PlusOutlined,
  ReloadOutlined,
  DatabaseOutlined,
  LoadingOutlined,
  CheckCircleOutlined,
  CloseCircleOutlined,
  EyeOutlined,
  PlayCircleOutlined,
  PauseCircleOutlined,
  StopOutlined,
  FileSearchOutlined,
  ImportOutlined,
  DeleteOutlined
} from '@ant-design/icons-vue'
import api, { spiderAPI } from '@/utils/api'

// 响应式数据
const loading = ref(false)
const refreshing = ref(false)
const tasksLoading = ref(false)
const statisticsLoading = ref(false)
const createTaskLoading = ref(false)

// 统计数据
const statistics = reactive({
  total_tasks: 0,
  running_tasks: 0,
  completed_tasks: 0,
  failed_tasks: 0,
  idle_tasks: 0
})

// 任务列表
const tasks = ref([])
const statusFilter = ref('')

// Modal状态
const createTaskModalVisible = ref(false)
const taskDetailModalVisible = ref(false)
const previewModalVisible = ref(false)

// 选中的任务
const selectedTask = ref(null)
const previewData = ref(null)

// 创建任务表单
const createFormRef = ref()
const createForm = reactive({
  platform: 'ios',
  appid: '',
  country: 'cn',
  days_back: 30,
  market: '4',
  max_pages: 10,
  task_name: '',
  execution_mode: 'async'
})

// 表单验证规则
const createFormRules = computed(() => {
  const rules = {
    platform: [
      { required: true, message: '请选择抓取平台', trigger: 'change' }
    ],
    max_pages: [
      { required: true, message: '请输入最大页数', trigger: 'blur' },
      { type: 'number', min: 1, max: 1000, message: '最大页数必须在1-1000之间', trigger: 'blur' }
    ]
  }
  
  if (createForm.platform === 'ios') {
    rules.appid = [
      { required: true, message: '请输入应用ID', trigger: 'blur' },
      { pattern: /^\d+$/, message: '应用ID必须为数字', trigger: 'blur' }
    ]
    rules.country = [
      { required: true, message: '请选择国家', trigger: 'change' }
    ]
    rules.days_back = [
      { required: true, message: '请输入回溯天数', trigger: 'blur' },
      { type: 'number', min: 1, max: 3650, message: '回溯天数必须在1-3650之间', trigger: 'blur' }
    ]
  } else if (createForm.platform === 'android') {
    rules.market = [
      { required: true, message: '请选择应用市场', trigger: 'change' }
    ]
  }
  
  return rules
})

// 任务列表表格列配置
const taskColumns = [
  {
    title: '任务ID',
    dataIndex: 'task_id',
    key: 'task_id',
    width: 200,
    ellipsis: true
  },
  {
    title: '状态',
    dataIndex: 'status',
    key: 'status',
    width: 100
  },
  {
    title: '进度',
    dataIndex: 'progress',
    key: 'progress',
    width: 150
  },
  {
    title: '创建时间',
    dataIndex: 'created_at',
    key: 'created_at',
    width: 160,
    customRender: ({ text }) => formatTime(text)
  },
  {
    title: '执行时长',
    dataIndex: 'duration',
    key: 'duration',
    width: 100
  },
  {
    title: '操作',
    key: 'actions',
    width: 200
  }
]

// 数据预览表格列配置
const previewColumns = [
  {
    title: '内容',
    dataIndex: 'content',
    key: 'content',
    width: 300
  },
  {
    title: '评分',
    dataIndex: ['product_info', 'rating'],
    key: 'rating',
    width: 80
  },
  {
    title: '情感',
    dataIndex: 'sentiment',
    key: 'sentiment',
    width: 100
  },
  {
    title: '优先级',
    dataIndex: 'priority',
    key: 'priority',
    width: 100
  },
  {
    title: '用户',
    dataIndex: ['user_info', 'nickname'],
    key: 'user',
    width: 120
  },
  {
    title: '创建时间',
    dataIndex: 'created_at',
    key: 'created_at',
    width: 160,
    customRender: ({ text }) => formatTime(text)
  }
]

// 计算属性
const filteredTasks = computed(() => {
  if (!statusFilter.value) return tasks.value
  return tasks.value.filter(task => task.status === statusFilter.value)
})

// 定时刷新
let refreshTimer = null

// 生命周期
onMounted(() => {
  loadStatistics()
  loadTasks()
  
  // 设置定时刷新（每30秒）
  refreshTimer = setInterval(() => {
    loadStatistics()
    loadTasks()
  }, 30000)
})

onUnmounted(() => {
  if (refreshTimer) {
    clearInterval(refreshTimer)
  }
})

// 方法
const loadStatistics = async () => {
  try {
    statisticsLoading.value = true
    const response = await spiderAPI.getStatistics()
    Object.assign(statistics, response.data)
  } catch (error) {
    console.error('加载统计数据失败:', error)
    message.error('加载统计数据失败')
  } finally {
    statisticsLoading.value = false
  }
}

const loadTasks = async () => {
  try {
    tasksLoading.value = true
    const response = await spiderAPI.getTaskList()
    tasks.value = response.data.tasks || []
  } catch (error) {
    message.error('加载任务列表失败')
    console.error('加载任务列表失败:', error)
  } finally {
    tasksLoading.value = false
  }
}

const refreshTaskList = async () => {
  refreshing.value = true
  await Promise.all([loadStatistics(), loadTasks()])
  refreshing.value = false
  message.success('刷新成功')
}

const showCreateTaskModal = () => {
  createTaskModalVisible.value = true
}

const onPlatformChange = () => {
  // 平台切换时重置相关字段
  if (createForm.platform === 'ios') {
    createForm.appid = ''
    createForm.country = 'cn'
    createForm.days_back = 30
  } else if (createForm.platform === 'android') {
    createForm.market = '4'
  }
}

const resetCreateForm = () => {
  createTaskModalVisible.value = false
  createFormRef.value?.resetFields()
  Object.assign(createForm, {
    platform: 'ios',
    appid: '',
    country: 'cn',
    days_back: 30,
    market: '4',
    max_pages: 10,
    task_name: '',
    execution_mode: 'async'
  })
}

const createTask = async () => {
  try {
    await createFormRef.value.validate()
    createTaskLoading.value = true

    let response
    if (createForm.platform === 'ios') {
      // 创建iOS任务
      response = await spiderAPI.createQimaiTask({
        appid: createForm.appid,
        country: createForm.country,
        days_back: createForm.days_back,
        max_pages: createForm.max_pages,
        task_name: createForm.task_name
      })
    } else if (createForm.platform === 'android') {
      // 创建Android任务
      response = await spiderAPI.createQimaiAndroidTask({
        market: createForm.market,
        max_pages: createForm.max_pages,
        task_name: createForm.task_name
      })
    }

    if (createForm.execution_mode === 'async') {
      // 立即运行任务
      await spiderAPI.runTask(response.data.task_id)
      message.success('爬虫任务创建成功，开始后台执行')
    } else {
      // 仅创建任务
      message.success('爬虫任务创建成功')
    }

    resetCreateForm()
    await loadTasks()
    await loadStatistics()
  } catch (error) {
    message.error('创建任务失败')
    console.error('创建任务失败:', error)
  } finally {
    createTaskLoading.value = false
  }
}

const runTask = async (taskId) => {
  try {
    await spiderAPI.runTask(taskId)
    message.success('任务开始执行')
    await loadTasks()
  } catch (error) {
    message.error('启动任务失败')
    console.error('启动任务失败:', error)
  }
}

const pauseTask = async (taskId) => {
  try {
    await spiderAPI.pauseTask(taskId)
    message.success('任务已暂停')
    await loadTasks()
  } catch (error) {
    message.error('暂停任务失败')
    console.error('暂停任务失败:', error)
  }
}

const resumeTask = async (taskId) => {
  try {
    await spiderAPI.resumeTask(taskId)
    message.success('任务已恢复')
    await loadTasks()
  } catch (error) {
    message.error('恢复任务失败')
    console.error('恢复任务失败:', error)
  }
}

const stopTask = async (taskId) => {
  Modal.confirm({
    title: '确认停止任务？',
    content: '停止后的任务无法恢复，确定要停止吗？',
    onOk: async () => {
      try {
        await spiderAPI.stopTask(taskId)
        message.success('任务已停止')
        await loadTasks()
      } catch (error) {
        message.error('停止任务失败')
        console.error('停止任务失败:', error)
      }
    }
  })
}

const showTaskDetail = async (task) => {
  selectedTask.value = task
  taskDetailModalVisible.value = true
}

const previewTaskData = async (taskId) => {
  try {
    const response = await spiderAPI.previewTaskData(taskId)
    previewData.value = response.data
    previewModalVisible.value = true
  } catch (error) {
    message.error('预览数据失败')
    console.error('预览数据失败:', error)
  }
}

const importData = async (taskId) => {
  Modal.confirm({
    title: '确认导入数据？',
    content: '确定要将此任务的数据导入到系统中吗？',
    onOk: async () => {
      try {
        loading.value = true
        const response = await spiderAPI.importTaskData(taskId)
        message.success(`数据导入成功，共导入 ${response.data.imported_count} 条数据`)
      } catch (error) {
        message.error('导入数据失败')
        console.error('导入数据失败:', error)
      } finally {
        loading.value = false
      }
    }
  })
}

const cleanupTasks = async () => {
  Modal.confirm({
    title: '确认清理过期任务？',
    content: '将清理7天前完成的任务，确定继续吗？',
    onOk: async () => {
      try {
        const response = await spiderAPI.cleanupTasks()
        message.success(`清理完成，删除了 ${response.data.cleaned_count} 个过期任务`)
        await loadTasks()
        await loadStatistics()
      } catch (error) {
        message.error('清理任务失败')
        console.error('清理任务失败:', error)
      }
    }
  })
}

// 工具函数
const getTaskPlatformName = (taskParams) => {
  if (!taskParams) return '未知'
  
  if (taskParams.platform === 'android') {
    return 'Android应用市场'
  } else if (taskParams.platform === 'ios' || taskParams.appid) {
    return 'iOS App Store'
  } else {
    return '未知平台'
  }
}

const getStatusColor = (status) => {
  const colors = {
    idle: 'default',
    running: 'processing',
    completed: 'success',
    error: 'error',
    paused: 'warning',
    stopped: 'default'
  }
  return colors[status] || 'default'
}

const getStatusText = (status) => {
  const texts = {
    idle: '空闲',
    running: '运行中',
    completed: '已完成',
    error: '失败',
    paused: '暂停',
    stopped: '已停止'
  }
  return texts[status] || status
}

const getSentimentColor = (sentiment) => {
  const colors = {
    positive: 'green',
    negative: 'red',
    neutral: 'blue'
  }
  return colors[sentiment] || 'default'
}

const getSentimentText = (sentiment) => {
  const texts = {
    positive: '正面',
    negative: '负面',
    neutral: '中性'
  }
  return texts[sentiment] || sentiment
}

const getPriorityColor = (priority) => {
  const colors = {
    high: 'red',
    medium: 'orange',
    low: 'green'
  }
  return colors[priority] || 'default'
}

const getTaskProgress = (task) => {
  if (task.spider_status?.metrics) {
    const metrics = task.spider_status.metrics
    if (metrics.total_requests > 0) {
      return Math.round((metrics.successful_requests / metrics.total_requests) * 100)
    }
  }
  return 0
}

const formatTime = (timeStr) => {
  if (!timeStr) return '-'
  return new Date(timeStr).toLocaleString('zh-CN')
}

const formatDuration = (seconds) => {
  if (!seconds || seconds < 0) return '-'
  
  const hours = Math.floor(seconds / 3600)
  const minutes = Math.floor((seconds % 3600) / 60)
  const secs = Math.floor(seconds % 60)
  
  if (hours > 0) {
    return `${hours}h ${minutes}m ${secs}s`
  } else if (minutes > 0) {
    return `${minutes}m ${secs}s`
  } else {
    return `${secs}s`
  }
}
</script>

<style scoped>
.spider-management {
  padding: 24px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 24px;
}

.header-content h1.page-title {
  margin: 0;
  font-size: 24px;
  font-weight: 600;
  display: flex;
  align-items: center;
  gap: 8px;
}

.header-content .page-description {
  margin: 8px 0 0 0;
  font-size: 14px;
  line-height: 1.5;
}

.header-actions {
  display: flex;
  gap: 8px;
}

.stats-cards {
  margin-bottom: 24px;
}

.task-list {
  margin-top: 16px;
}

.progress-info {
  display: flex;
  justify-content: space-between;
  font-size: 12px;
  margin-top: 4px;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .spider-management {
    padding: 16px;
  }
  
  .page-header {
    flex-direction: column;
    gap: 16px;
  }
  
  .header-actions {
    align-self: stretch;
  }
  
  .stats-cards .ant-col {
    margin-bottom: 16px;
  }
}
</style> 