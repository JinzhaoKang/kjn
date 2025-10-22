<template>
  <div class="analysis-engine">
    <a-page-header title="智能分析引擎" sub-title="配置和管理AI分析模块">
      <template #extra>
        <a-space>
          <a-button type="primary" @click="runFullAnalysis">
            <PlayCircleOutlined />
            执行全量分析
          </a-button>
          <a-button @click="refreshStatus">
            <ReloadOutlined />
            刷新状态
          </a-button>
        </a-space>
      </template>
    </a-page-header>

    <!-- 引擎状态监控 -->
    <a-row :gutter="16" class="status-row">
      <a-col :span="6">
        <a-card class="status-card">
          <a-statistic
            title="预处理引擎"
            :value="engineStatus.preprocessing.status"
            :value-style="{ color: getStatusColor(engineStatus.preprocessing.status) }"
          >
            <template #suffix>
              <a-tag :color="getStatusColor(engineStatus.preprocessing.status)">
                {{ getStatusText(engineStatus.preprocessing.status) }}
              </a-tag>
            </template>
          </a-statistic>
        </a-card>
      </a-col>
      <a-col :span="6">
        <a-card class="status-card">
          <a-statistic
            title="LLM分析引擎"
            :value="engineStatus.llm.status"
            :value-style="{ color: getStatusColor(engineStatus.llm.status) }"
          >
            <template #suffix>
              <a-tag :color="getStatusColor(engineStatus.llm.status)">
                {{ getStatusText(engineStatus.llm.status) }}
              </a-tag>
            </template>
          </a-statistic>
        </a-card>
      </a-col>
      <a-col :span="6">
        <a-card class="status-card">
          <a-statistic
            title="优先级引擎"
            :value="engineStatus.priority.status"
            :value-style="{ color: getStatusColor(engineStatus.priority.status) }"
          >
            <template #suffix>
              <a-tag :color="getStatusColor(engineStatus.priority.status)">
                {{ getStatusText(engineStatus.priority.status) }}
              </a-tag>
            </template>
          </a-statistic>
        </a-card>
      </a-col>
      <a-col :span="6">
        <a-card class="status-card">
          <a-statistic
            title="情感分析引擎"
            :value="engineStatus.sentiment.status"
            :value-style="{ color: getStatusColor(engineStatus.sentiment.status) }"
          >
            <template #suffix>
              <a-tag :color="getStatusColor(engineStatus.sentiment.status)">
                {{ getStatusText(engineStatus.sentiment.status) }}
              </a-tag>
            </template>
          </a-statistic>
        </a-card>
      </a-col>
    </a-row>

    <!-- 分析任务队列 -->
    <a-card title="分析任务队列" class="task-queue-card">
      <template #extra>
        <a-space>
          <a-select v-model="taskFilter" placeholder="任务状态" allowClear @change="loadTasks">
            <a-select-option value="pending">等待中</a-select-option>
            <a-select-option value="running">运行中</a-select-option>
            <a-select-option value="completed">已完成</a-select-option>
            <a-select-option value="failed">失败</a-select-option>
          </a-select>
          <a-button @click="clearCompletedTasks">清理已完成</a-button>
        </a-space>
      </template>

      <a-table
        :columns="taskColumns"
        :data-source="taskList"
        :loading="taskLoading"
        :pagination="{ pageSize: 10 }"
      >
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'type'">
            <a-tag :color="getTaskTypeColor(record.type)">
              {{ getTaskTypeText(record.type) }}
            </a-tag>
          </template>
          <template v-if="column.key === 'status'">
            <a-tag :color="getTaskStatusColor(record.status)">
              {{ getTaskStatusText(record.status) }}
            </a-tag>
          </template>
          <template v-if="column.key === 'progress'">
            <a-progress :percent="record.progress" size="small" />
          </template>
          <template v-if="column.key === 'action'">
            <a-space>
              <a-button type="link" size="small" @click="viewTaskDetails(record)">
                详情
              </a-button>
              <a-button
                type="link"
                size="small"
                danger
                @click="cancelTask(record)"
                v-if="record.status === 'running' || record.status === 'pending'"
              >
                取消
              </a-button>
              <a-button
                type="link"
                size="small"
                @click="retryTask(record)"
                v-if="record.status === 'failed'"
              >
                重试
              </a-button>
            </a-space>
          </template>
          </template>
      </a-table>
    </a-card>

    <!-- 引擎性能监控 -->
    <a-row :gutter="16" class="performance-row">
      <a-col :span="12">
        <a-card title="CPU使用率" class="performance-card">
          <div ref="cpuChart" style="height: 300px;"></div>
        </a-card>
      </a-col>
      <a-col :span="12">
        <a-card title="内存使用率" class="performance-card">
          <div ref="memoryChart" style="height: 300px;"></div>
        </a-card>
      </a-col>
    </a-row>

    <!-- 分析配置 -->
    <a-card title="分析配置" class="config-card">
      <a-tabs v-model="configTab" type="card">
        <a-tab-pane key="preprocessing" tab="预处理配置">
          <a-form
            :model="analysisConfig.preprocessing"
            :label-col="{ span: 6 }"
            :wrapper-col="{ span: 18 }"
          >
            <a-form-item label="启用状态">
              <a-switch v-model:checked="analysisConfig.preprocessing.enabled" />
            </a-form-item>
            <a-form-item label="批处理大小">
              <a-input-number
                v-model:value="analysisConfig.preprocessing.batchSize"
                :min="1"
                :max="1000"
                style="width: 200px"
              />
            </a-form-item>
            <a-form-item label="过滤阈值">
              <a-slider
                v-model:value="analysisConfig.preprocessing.threshold"
                :min="0"
                :max="1"
                :step="0.1"
                :marks="{ 0: '0', 0.5: '0.5', 1: '1' }"
              />
            </a-form-item>
          </a-form>
        </a-tab-pane>

        <a-tab-pane key="llm" tab="LLM配置">
          <a-form
            :model="analysisConfig.llm"
            :label-col="{ span: 6 }"
            :wrapper-col="{ span: 18 }"
          >
            <a-form-item label="启用状态">
              <a-switch v-model:checked="analysisConfig.llm.enabled" />
            </a-form-item>
            <a-form-item label="模型选择">
              <a-select 
                v-model:value="analysisConfig.llm.model" 
                placeholder="选择模型"
                :loading="modelsLoading"
                @dropdown-visible-change="onModelDropdownChange"
              >
                <a-select-option 
                  v-for="model in sortedAvailableModels" 
                  :key="model.id" 
                  :value="model.id"
                >
                  {{ model.id }} {{ model.owned_by ? `(${model.owned_by})` : '' }}
                </a-select-option>
              </a-select>
              <div v-if="modelsError" style="color: red; font-size: 12px; margin-top: 4px;">
                {{ modelsError }}
              </div>
              <div v-if="modelsSource" style="color: #666; font-size: 12px; margin-top: 4px;">
                数据来源: {{ modelsSource }}
              </div>
            </a-form-item>
            <a-form-item label="温度参数">
              <a-slider
                v-model:value="analysisConfig.llm.temperature"
                :min="0"
                :max="1"
                :step="0.1"
                :marks="{ 0: '0', 0.5: '0.5', 1: '1' }"
              />
            </a-form-item>
            <a-form-item label="最大令牌数">
              <a-input-number
                v-model:value="analysisConfig.llm.maxTokens"
                :min="100"
                :max="8000"
                style="width: 200px"
              />
            </a-form-item>
          </a-form>
        </a-tab-pane>

        <a-tab-pane key="priority" tab="优先级配置">
          <a-form
            :model="analysisConfig.priority"
            :label-col="{ span: 6 }"
            :wrapper-col="{ span: 18 }"
          >
            <a-form-item label="启用状态">
              <a-switch v-model:checked="analysisConfig.priority.enabled" />
            </a-form-item>
            <a-form-item label="权重配置">
              <div class="weight-config">
                <div class="weight-item">
                  <span>用户影响权重:</span>
                  <a-slider
                    v-model:value="analysisConfig.priority.weights.userImpact"
                    :max="1"
                    :step="0.1"
                    :marks="{ 0: '0', 0.5: '0.5', 1: '1' }"
                  />
                </div>
                <div class="weight-item">
                  <span>技术复杂度权重:</span>
                  <a-slider
                    v-model:value="analysisConfig.priority.weights.complexity"
                    :max="1"
                    :step="0.1"
                    :marks="{ 0: '0', 0.5: '0.5', 1: '1' }"
                  />
                </div>
                <div class="weight-item">
                  <span>商业价值权重:</span>
                  <a-slider
                    v-model:value="analysisConfig.priority.weights.businessValue"
                    :max="1"
                    :step="0.1"
                    :marks="{ 0: '0', 0.5: '0.5', 1: '1' }"
                  />
                </div>
              </div>
            </a-form-item>
          </a-form>
        </a-tab-pane>

        <a-tab-pane key="decision" tab="决策引擎">
          <a-row :gutter="16">
            <a-col :span="12">
              <a-card title="6维度权重配置" size="small">
                <div class="dimension-weights" v-if="decisionEngineWeights">
                  <div class="weight-item" v-for="(desc, key) in decisionEngineWeights.description" :key="key">
                    <div class="weight-label">
                      <span>{{ desc.split(' - ')[0] }}:</span>
                      <a-tooltip :title="desc.split(' - ')[1]">
                        <InfoCircleOutlined style="margin-left: 4px; color: #666;" />
                      </a-tooltip>
                    </div>
                                         <a-slider
                       v-model="decisionEngineWeights.dimension_weights[key]"
                       :max="1"
                       :step="0.05"
                       :marks="{ 0: '0', 0.25: '0.25', 0.5: '0.5', 0.75: '0.75', 1: '1' }"
                     />
                    <span class="weight-value">{{ decisionEngineWeights.dimension_weights[key] }}</span>
                  </div>
                </div>
                <a-button type="primary" @click="saveDecisionWeights" style="margin-top: 16px;">
                  保存权重配置
                </a-button>
              </a-card>
            </a-col>
            <a-col :span="12">
              <a-card title="引擎状态" size="small">
                <a-descriptions :column="1" size="small">
                  <a-descriptions-item label="高级优先级引擎">
                    <a-tag color="green" v-if="decisionEngineStatus.advanced_priority_engine">正常</a-tag>
                    <a-tag color="red" v-else>异常</a-tag>
                  </a-descriptions-item>
                  <a-descriptions-item label="基础优先级引擎">
                    <a-tag color="green" v-if="decisionEngineStatus.priority_engine">正常</a-tag>
                    <a-tag color="red" v-else>异常</a-tag>
                  </a-descriptions-item>
                  <a-descriptions-item label="行动生成器">
                    <a-tag color="green" v-if="decisionEngineStatus.action_generator">正常</a-tag>
                    <a-tag color="red" v-else>异常</a-tag>
                  </a-descriptions-item>
                </a-descriptions>
                <a-button @click="checkDecisionEngineHealth" style="margin-top: 16px;">
                  检查状态
                </a-button>
              </a-card>
            </a-col>
          </a-row>

          <a-divider />

          <a-card title="决策引擎分析概览" class="decision-overview-card">
            <a-row :gutter="16" v-if="decisionAnalytics">
              <a-col :span="6">
                <a-statistic
                  title="总反馈数"
                  :value="decisionAnalytics.total_feedbacks"
                  prefix=""
                />
              </a-col>
              <a-col :span="6">
                <a-statistic
                  title="已分析数"
                  :value="decisionAnalytics.analyzed_count"
                  :value-style="{ color: '#3f8600' }"
                />
              </a-col>
              <a-col :span="6">
                <a-statistic
                  title="平均优先级得分"
                  :value="decisionAnalytics.avg_scores.priority"
                  suffix="分"
                  :precision="1"
                />
              </a-col>
              <a-col :span="6">
                <a-statistic
                  title="平均ROI"
                  :value="decisionAnalytics.avg_scores.roi"
                  suffix="%"
                  :precision="2"
                  :value-style="{ color: '#cf1322' }"
                />
              </a-col>
            </a-row>

            <a-divider />

            <a-row :gutter="16">
              <a-col :span="12">
                <h4>优先级分布</h4>
                <div ref="priorityChart" style="height: 200px;"></div>
              </a-col>
              <a-col :span="12">
                <h4>6维度平均得分</h4>
                <div ref="dimensionsChart" style="height: 200px;"></div>
              </a-col>
            </a-row>

            <a-divider />

            <h4>战略建议</h4>
            <a-list
              :data-source="decisionAnalytics.recommendations_summary"
              size="small"
            >
              <template #renderItem="{ item }">
                <a-list-item>
                  <BulbOutlined style="margin-right: 8px; color: #faad14;" />
                  {{ item }}
                </a-list-item>
              </template>
            </a-list>
          </a-card>
        </a-tab-pane>
      </a-tabs>

      <a-divider />
      
      <a-form-item>
        <a-space>
          <a-button type="primary" @click="saveConfig">
            保存配置
          </a-button>
          <a-button @click="resetConfig">
            重置配置
          </a-button>
          <a-button @click="testConfig">
            测试配置
          </a-button>
        </a-space>
      </a-form-item>
    </a-card>

    <!-- 任务详情抽屉 -->
    <a-drawer
      v-model:visible="showTaskDrawer"
      title="任务详情"
      placement="right"
      width="600"
    >
      <div v-if="selectedTask">
        <a-descriptions :column="2" bordered>
          <a-descriptions-item label="任务ID" :span="2">
            {{ selectedTask.id }}
          </a-descriptions-item>
          <a-descriptions-item label="任务类型">
            <a-tag :color="getTaskTypeColor(selectedTask.type)">
              {{ getTaskTypeText(selectedTask.type) }}
            </a-tag>
          </a-descriptions-item>
          <a-descriptions-item label="任务状态">
            <a-tag :color="getTaskStatusColor(selectedTask.status)">
              {{ getTaskStatusText(selectedTask.status) }}
            </a-tag>
          </a-descriptions-item>
          <a-descriptions-item label="开始时间">
            {{ selectedTask.startTime }}
          </a-descriptions-item>
          <a-descriptions-item label="完成时间">
            {{ selectedTask.endTime || '-' }}
          </a-descriptions-item>
          <a-descriptions-item label="处理时长">
            {{ selectedTask.duration || '-' }}
          </a-descriptions-item>
          <a-descriptions-item label="处理进度">
            <a-progress :percent="selectedTask.progress" />
          </a-descriptions-item>
        </a-descriptions>

        <a-divider />

        <div class="task-logs">
          <h4>执行日志</h4>
          <a-textarea
            :value="selectedTask.logs"
            :rows="10"
            readonly
            style="font-family: monospace;"
          />
        </div>
      </div>
    </a-drawer>
  </div>
</template>

<script>
import { ref, reactive, onMounted, nextTick, computed } from 'vue'
import { message, Modal } from 'ant-design-vue'
import {
  PlayCircleOutlined,
  ReloadOutlined,
  InfoCircleOutlined,
  BulbOutlined,
} from '@ant-design/icons-vue'
import * as echarts from 'echarts'
import { settingsAPI, decisionEngineAPI } from '@/utils/api'

export default {
  name: 'AnalysisEngine',
  components: {
    PlayCircleOutlined,
    ReloadOutlined,
    InfoCircleOutlined,
    BulbOutlined,
  },
  setup() {
    const taskLoading = ref(false)
    const showTaskDrawer = ref(false)
    const taskFilter = ref(undefined)
    const configTab = ref('preprocessing')
    const taskList = ref([])
    const selectedTask = ref(null)
    const cpuChart = ref(null)
    const memoryChart = ref(null)
    const priorityChart = ref(null)
    const dimensionsChart = ref(null)
    
    // LLM模型相关状态
    const modelsLoading = ref(false)
    const availableModels = ref([])
    const modelsError = ref('')
    const modelsSource = ref('')

    // 决策引擎相关状态
    const decisionEngineStatus = ref({
      advanced_priority_engine: false,
      priority_engine: false,
      action_generator: false
    })
    const decisionEngineWeights = ref(null)
    const decisionAnalytics = ref(null)

    const engineStatus = ref({
      preprocessing: { status: 'running' },
      llm: { status: 'running' },
      priority: { status: 'idle' },
      sentiment: { status: 'running' }
    })

    const analysisConfig = reactive({
      preprocessing: {
        enabled: true,
        batchSize: 100,
        threshold: 0.7
      },
      llm: {
        enabled: true,
        model: 'gpt-4',
        temperature: 0.3,
        maxTokens: 2000
      },
      priority: {
        enabled: true,
        weights: {
          userImpact: 0.4,
          complexity: 0.3,
          businessValue: 0.3
        }
      }
    })

    // 排序后的模型列表计算属性
    const sortedAvailableModels = computed(() => {
      return [...availableModels.value].sort((a, b) => {
        // 按提供商分组排序：OpenAI -> Anthropic -> Google -> 其他
        const providerOrder = {
          'openai': 0,
          'anthropic': 1, 
          'google': 2,
          'zhipu': 3,
          'deepseek': 4,
          'grok': 5,
          'nova': 6,
          'bytedance': 7,
          'flux': 8,
          'stability': 9,
          'perplexity': 10,
          'baichuan': 11,
          'spark': 12,
          'ernie': 13
        }
        
        const orderA = providerOrder[a.owned_by?.toLowerCase()] ?? 999
        const orderB = providerOrder[b.owned_by?.toLowerCase()] ?? 999
        
        if (orderA !== orderB) {
          return orderA - orderB
        }
        
        // 同一提供商内按模型名称排序
        return a.id.localeCompare(b.id)
      })
    })

    // 加载可用的LLM模型列表
    const loadAvailableModels = async () => {
      if (modelsLoading.value) return
      
      modelsLoading.value = true
      modelsError.value = ''
      modelsSource.value = ''
      
      try {
        const response = await settingsAPI.getLLMModels()
        const data = response.data
        
        if (data.success) {
          availableModels.value = data.models || []
          modelsSource.value = data.source === 'theturbo.ai' ? 'theturbo.ai (实时)' : data.source
          message.success(`成功获取 ${availableModels.value.length} 个可用模型`)
        } else {
          availableModels.value = data.models || []
          modelsSource.value = data.source
          modelsError.value = `获取模型列表失败: ${data.error || '未知错误'}`
          message.warning('使用备用模型列表')
        }
      } catch (error) {
        console.error('加载模型列表失败:', error)
        modelsError.value = `网络错误: ${error.message}`
        // 设置默认模型列表
        availableModels.value = [
          { id: 'gpt-4', object: 'model', owned_by: 'openai' },
          { id: 'gpt-3.5-turbo', object: 'model', owned_by: 'openai' },
          { id: 'claude-3-haiku', object: 'model', owned_by: 'anthropic' },
          { id: 'claude-3-sonnet', object: 'model', owned_by: 'anthropic' }
        ]
        modelsSource.value = '默认列表'
        message.error('无法获取模型列表，使用默认选项')
      } finally {
        modelsLoading.value = false
      }
    }

    // 下拉框打开时加载模型列表
    const onModelDropdownChange = (open) => {
      if (open && availableModels.value.length === 0) {
        loadAvailableModels()
      }
    }

    const taskColumns = [
      { title: 'ID', dataIndex: 'id', key: 'id', width: 80 },
      { title: '任务类型', dataIndex: 'type', key: 'type', width: 120 },
      { title: '状态', dataIndex: 'status', key: 'status', width: 100 },
      { title: '进度', dataIndex: 'progress', key: 'progress', width: 120 },
      { title: '开始时间', dataIndex: 'startTime', key: 'startTime', width: 150 },
      { title: '预计完成', dataIndex: 'estimatedTime', key: 'estimatedTime', width: 150 },
      { title: '操作', key: 'action', width: 200, fixed: 'right' },
    ]

    const getStatusColor = (status) => {
      const colors = {
        running: '#52c41a',
        idle: '#1890ff',
        error: '#f5222d',
        stopped: '#faad14'
      }
      return colors[status] || '#d9d9d9'
    }

    const getStatusText = (status) => {
      const texts = {
        running: '运行中',
        idle: '空闲',
        error: '错误',
        stopped: '已停止'
      }
      return texts[status] || status
    }

    const getTaskTypeColor = (type) => {
      const colors = {
        preprocessing: 'blue',
        llm_analysis: 'green',
        priority_analysis: 'orange',
        sentiment_analysis: 'purple',
        full_analysis: 'red'
      }
      return colors[type] || 'default'
    }

    const getTaskTypeText = (type) => {
      const texts = {
        preprocessing: '预处理',
        llm_analysis: 'LLM分析',
        priority_analysis: '优先级分析',
        sentiment_analysis: '情感分析',
        full_analysis: '全量分析'
      }
      return texts[type] || type
    }

    const getTaskStatusColor = (status) => {
      const colors = {
        pending: 'blue',
        running: 'processing',
        completed: 'success',
        failed: 'error'
      }
      return colors[status] || 'default'
    }

    const getTaskStatusText = (status) => {
      const texts = {
        pending: '等待中',
        running: '运行中',
        completed: '已完成',
        failed: '失败'
      }
      return texts[status] || status
    }

    const loadTasks = () => {
      taskLoading.value = true
      // 模拟数据
      setTimeout(() => {
        taskList.value = [
          {
            id: 1,
            type: 'full_analysis',
            status: 'running',
            progress: 65,
            startTime: '2024-01-01 10:30:00',
            estimatedTime: '2024-01-01 11:00:00',
            logs: '正在执行全量分析...\n已处理65%的数据\n预计剩余时间: 15分钟'
          },
          {
            id: 2,
            type: 'llm_analysis',
            status: 'completed',
            progress: 100,
            startTime: '2024-01-01 09:15:00',
            estimatedTime: '2024-01-01 09:45:00',
            logs: 'LLM分析任务已完成\n处理了256条反馈\n生成了分析报告'
          }
        ]
        taskLoading.value = false
      }, 1000)
    }

    const refreshStatus = () => {
      message.success('状态已刷新')
      loadTasks()
    }

    const runFullAnalysis = () => {
      Modal.confirm({
        title: '确认执行',
        content: '确定要执行全量分析吗？这可能需要较长时间。',
        onOk() {
          message.success('全量分析任务已启动')
          loadTasks()
        },
      })
    }

    const clearCompletedTasks = () => {
      message.success('已清理完成的任务')
      loadTasks()
    }

    const viewTaskDetails = (record) => {
      selectedTask.value = record
      showTaskDrawer.value = true
    }

    const cancelTask = (record) => {
      Modal.confirm({
        title: '确认取消',
        content: `确定要取消任务"${record.id}"吗？`,
        onOk() {
          message.success('任务已取消')
          loadTasks()
        },
      })
    }

    const retryTask = (record) => {
      message.success('任务已重新启动')
      loadTasks()
    }

    // 加载配置
    const loadConfig = async () => {
      try {
        const response = await settingsAPI.getSettings()
        const data = response.data
        if (data.analysis) {
          Object.assign(analysisConfig, data.analysis)
        }
      } catch (error) {
        console.error('加载配置失败:', error)
        message.error('加载配置失败')
      }
    }

    const saveConfig = async () => {
      try {
        // 获取完整设置
        const response = await settingsAPI.getSettings()
        const currentSettings = response.data
        
        // 更新分析配置
        const settingsToSave = {
          ...currentSettings,
          analysis: analysisConfig
        }
        
        await settingsAPI.updateSettings(settingsToSave)
        message.success('配置已保存')
      } catch (error) {
        console.error('保存配置失败:', error)
        message.error('保存配置失败')
      }
    }

    const resetConfig = async () => {
      Modal.confirm({
        title: '确认重置',
        content: '确定要重置配置为默认值吗？',
        onOk: async () => {
          try {
            // 重置为默认配置
            Object.assign(analysisConfig, {
              preprocessing: {
                enabled: true,
                batchSize: 100,
                threshold: 0.7
              },
              llm: {
                enabled: true,
                model: 'gpt-4',
                temperature: 0.3,
                maxTokens: 2000
              },
              priority: {
                enabled: true,
                weights: {
                  userImpact: 0.4,
                  complexity: 0.3,
                  businessValue: 0.3
                }
              }
            })
            message.success('配置已重置')
          } catch (error) {
            message.error('重置配置失败')
          }
        }
      })
    }

    const testConfig = () => {
      message.success('配置测试通过')
    }

    // 决策引擎相关方法
    const checkDecisionEngineHealth = async () => {
      try {
        const response = await decisionEngineAPI.getHealth()
        decisionEngineStatus.value = response.data
        message.success('决策引擎状态检查完成')
      } catch (error) {
        console.error('检查决策引擎状态失败:', error)
        message.error('检查状态失败')
      }
    }

    const loadDecisionEngineData = async () => {
      try {
        // 加载权重配置
        const weightsResponse = await decisionEngineAPI.getWeightsConfig()
        decisionEngineWeights.value = weightsResponse.data

        // 加载分析概览
        const analyticsResponse = await decisionEngineAPI.getAnalyticsOverview()
        decisionAnalytics.value = analyticsResponse.data

        // 检查状态
        await checkDecisionEngineHealth()

        // 初始化图表
        nextTick(() => {
          initPriorityChart()
          initDimensionsChart()
        })
      } catch (error) {
        console.error('加载决策引擎数据失败:', error)
        message.error('加载决策引擎数据失败')
      }
    }

    const saveDecisionWeights = async () => {
      try {
        message.success('权重配置已保存')
      } catch (error) {
        console.error('保存权重配置失败:', error)
        message.error('保存权重配置失败')
      }
    }

    const initPriorityChart = () => {
      if (priorityChart.value && decisionAnalytics.value) {
        const chartInstance = echarts.init(priorityChart.value)
        const data = Object.entries(decisionAnalytics.value.priority_distribution).map(([key, value]) => ({
          name: key,
          value: value
        }))
        
        chartInstance.setOption({
          tooltip: { trigger: 'item' },
          series: [{
            type: 'pie',
            radius: '60%',
            data: data,
            emphasis: {
              itemStyle: {
                shadowBlur: 10,
                shadowOffsetX: 0,
                shadowColor: 'rgba(0, 0, 0, 0.5)'
              }
            }
          }]
        })
      }
    }

    const initDimensionsChart = () => {
      if (dimensionsChart.value && decisionAnalytics.value) {
        const chartInstance = echarts.init(dimensionsChart.value)
        const dimensions = decisionAnalytics.value.six_dimensions_avg
        
        chartInstance.setOption({
          tooltip: { trigger: 'axis' },
          radar: {
            indicator: [
              { name: '影响力', max: 100 },
              { name: '紧急性', max: 100 },
              { name: '实现成本', max: 100 },
              { name: '商业价值', max: 100 },
              { name: '战略匹配', max: 100 },
              { name: '用户声音', max: 100 }
            ]
          },
          series: [{
            type: 'radar',
            data: [{
              value: [
                dimensions.impact,
                dimensions.urgency,
                dimensions.effort,
                dimensions.business_value,
                dimensions.strategic,
                dimensions.user_voice
              ],
              name: '6维度评分'
            }]
          }]
        })
      }
    }

    const initCharts = () => {
      nextTick(() => {
        // CPU使用率图表
        if (cpuChart.value) {
          const cpuChartInstance = echarts.init(cpuChart.value)
          cpuChartInstance.setOption({
            tooltip: { trigger: 'axis' },
            xAxis: { type: 'category', data: ['00:00', '04:00', '08:00', '12:00', '16:00', '20:00'] },
            yAxis: { type: 'value', max: 100 },
            series: [{
              data: [20, 35, 45, 60, 55, 40],
              type: 'line',
              smooth: true,
              areaStyle: {}
            }]
          })
        }

        // 内存使用率图表
        if (memoryChart.value) {
          const memoryChartInstance = echarts.init(memoryChart.value)
          memoryChartInstance.setOption({
            tooltip: { trigger: 'axis' },
            xAxis: { type: 'category', data: ['00:00', '04:00', '08:00', '12:00', '16:00', '20:00'] },
            yAxis: { type: 'value', max: 100 },
            series: [{
              data: [30, 40, 50, 70, 65, 45],
              type: 'line',
              smooth: true,
              areaStyle: {}
            }]
          })
        }
      })
    }

    onMounted(() => {
      loadTasks()
      loadConfig() // 加载配置
      initCharts()
      // 初始加载模型列表
      loadAvailableModels()
      // 加载决策引擎数据
      loadDecisionEngineData()
    })

    return {
      taskLoading,
      showTaskDrawer,
      taskFilter,
      configTab,
      taskList,
      selectedTask,
      cpuChart,
      memoryChart,
      priorityChart,
      dimensionsChart,
      engineStatus,
      analysisConfig,
      taskColumns,
      // LLM模型相关
      modelsLoading,
      availableModels,
      sortedAvailableModels,
      modelsError,
      modelsSource,
      loadAvailableModels,
      onModelDropdownChange,
      // 决策引擎相关
      decisionEngineStatus,
      decisionEngineWeights,
      decisionAnalytics,
      checkDecisionEngineHealth,
      loadDecisionEngineData,
      saveDecisionWeights,
      // 其他方法
      getStatusColor,
      getStatusText,
      getTaskTypeColor,
      getTaskTypeText,
      getTaskStatusColor,
      getTaskStatusText,
      loadTasks,
      refreshStatus,
      runFullAnalysis,
      clearCompletedTasks,
      viewTaskDetails,
      cancelTask,
      retryTask,
      loadConfig,
      saveConfig,
      resetConfig,
      testConfig,
    }
  },
}
</script>

<style scoped>
.analysis-engine {
  padding: 24px;
}

.status-row {
  margin-bottom: 24px;
}

.status-card {
      text-align: center;
}

.task-queue-card {
  margin-bottom: 24px;
}

.performance-row {
  margin-bottom: 24px;
}

.performance-card {
  height: 400px;
}

.config-card {
  margin-bottom: 24px;
}

.weight-config {
  space-y: 16px;
}

.weight-item {
  margin-bottom: 16px;
}

.weight-item span {
  display: inline-block;
  width: 120px;
  font-weight: 500;
}

.task-logs {
  margin-top: 16px;
}
</style> 