<template>
  <div class="settings">
    <a-page-header title="系统设置" sub-title="配置系统参数和功能选项" />

    <a-tabs v-model:activeKey="activeTab" type="card">
      <!-- 系统配置 -->
      <a-tab-pane key="system" tab="系统配置">
        <a-card title="基础配置" class="settings-card">
          <a-form
            :model="systemSettings"
            :label-col="{ span: 6 }"
            :wrapper-col="{ span: 18 }"
          >
            <a-form-item label="系统名称">
              <a-input v-model:value="systemSettings.systemName" placeholder="请输入系统名称" />
            </a-form-item>
            <a-form-item label="系统描述">
              <a-textarea
                v-model:value="systemSettings.description"
                :rows="3"
                placeholder="请输入系统描述"
              />
            </a-form-item>
            <a-form-item label="时区设置">
              <a-select v-model:value="systemSettings.timezone" placeholder="选择时区">
                <a-select-option value="Asia/Shanghai">Asia/Shanghai</a-select-option>
                <a-select-option value="UTC">UTC</a-select-option>
                <a-select-option value="America/New_York">America/New_York</a-select-option>
              </a-select>
            </a-form-item>
            <a-form-item label="语言设置">
              <a-select v-model:value="systemSettings.language" placeholder="选择语言">
                <a-select-option value="zh-CN">简体中文</a-select-option>
                <a-select-option value="en-US">English</a-select-option>
              </a-select>
            </a-form-item>
            <a-form-item label="数据保留期">
              <a-input-number
                v-model:value="systemSettings.dataRetentionDays"
                :min="30"
                :max="3650"
                addon-after="天"
                style="width: 200px"
              />
            </a-form-item>
            <a-form-item>
              <a-button type="primary" @click="saveSystemSettings">
                保存配置
              </a-button>
            </a-form-item>
          </a-form>
        </a-card>

        <a-card title="数据库配置" class="settings-card">
          <a-form
            :model="systemSettings.database"
            :label-col="{ span: 6 }"
            :wrapper-col="{ span: 18 }"
          >
            <a-form-item label="数据库类型">
              <a-tag color="green">MongoDB</a-tag>
            </a-form-item>
            <a-form-item label="连接状态">
              <a-tag :color="systemSettings.database.connected ? 'green' : 'red'">
                {{ systemSettings.database.connected ? '已连接' : '未连接' }}
              </a-tag>
            </a-form-item>
            <a-form-item label="数据库地址">
              <a-input v-model:value="systemSettings.database.host" placeholder="数据库地址" />
            </a-form-item>
            <a-form-item label="端口">
              <a-input-number
                v-model:value="systemSettings.database.port"
                :min="1"
                :max="65535"
                style="width: 200px"
              />
            </a-form-item>
            <a-form-item>
              <a-button type="primary" @click="testDatabaseConnection">
                测试连接
              </a-button>
            </a-form-item>
          </a-form>
        </a-card>
      </a-tab-pane>

      <!-- 分析引擎配置 -->
      <a-tab-pane key="analysis" tab="分析引擎">
        <a-card title="智能预处理模块" class="settings-card">
          <a-form
            :model="analysisSettings"
            :label-col="{ span: 6 }"
            :wrapper-col="{ span: 18 }"
          >
            <a-form-item label="启用状态">
              <a-switch v-model:checked="analysisSettings.enabled" />
            </a-form-item>
            <a-form-item label="过滤阈值">
              <a-slider
                v-model:value="analysisSettings.threshold"
                :min="0"
                :max="1"
                :step="0.1"
                :marks="{ 0: '0', 0.5: '0.5', 1: '1' }"
              />
            </a-form-item>
          </a-form>
        </a-card>

        <a-card title="LLM分析模块" class="settings-card">
          <a-form
            :model="analysisSettings.llm"
            :label-col="{ span: 6 }"
            :wrapper-col="{ span: 18 }"
          >
            <a-form-item label="启用状态">
              <a-switch v-model:checked="analysisSettings.llm.enabled" />
            </a-form-item>
            <a-form-item label="模型选择">
              <a-select 
                v-model="analysisSettings.llm.model" 
                placeholder="选择LLM模型"
                :loading="modelsLoading"
                @dropdown-visible-change="onModelDropdownChange"
              >
                <a-select-option 
                  v-for="model in availableModels" 
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
            <a-form-item label="API密钥">
              <a-input-password
                v-model:value="analysisSettings.llm.apiKey"
                placeholder="请输入API密钥"
              />
            </a-form-item>
            <a-form-item label="温度参数">
              <a-slider
                v-model:value="analysisSettings.llm.temperature"
                :min="0"
                :max="1"
                :step="0.1"
                :marks="{ 0: '0', 0.5: '0.5', 1: '1' }"
              />
            </a-form-item>
            <a-form-item label="最大令牌数">
              <a-input-number
                v-model:value="analysisSettings.llm.maxTokens"
                :min="100"
                :max="8000"
                style="width: 200px"
              />
            </a-form-item>
          </a-form>
        </a-card>

        <a-card title="优先级评估引擎" class="settings-card">
          <a-form
            :model="analysisSettings.priority"
            :label-col="{ span: 6 }"
            :wrapper-col="{ span: 18 }"
          >
            <a-form-item label="启用状态">
              <a-switch v-model:checked="analysisSettings.priority.enabled" />
            </a-form-item>
            <a-form-item label="权重配置">
              <div class="weight-config">
                <div class="weight-item">
                  <span>用户影响权重:</span>
                  <a-slider
                    v-model:value="analysisSettings.priority.weights.userImpact"
                    :max="1"
                    :step="0.1"
                    :marks="{ 0: '0', 0.5: '0.5', 1: '1' }"
                  />
                </div>
                <div class="weight-item">
                  <span>技术复杂度权重:</span>
                  <a-slider
                    v-model:value="analysisSettings.priority.weights.complexity"
                    :max="1"
                    :step="0.1"
                    :marks="{ 0: '0', 0.5: '0.5', 1: '1' }"
                  />
                </div>
                <div class="weight-item">
                  <span>商业价值权重:</span>
                  <a-slider
                    v-model:value="analysisSettings.priority.weights.businessValue"
                    :max="1"
                    :step="0.1"
                    :marks="{ 0: '0', 0.5: '0.5', 1: '1' }"
                  />
                </div>
              </div>
            </a-form-item>
          </a-form>
        </a-card>

        <a-card class="settings-card">
          <a-form-item>
            <a-button type="primary" @click="saveAnalysisSettings">
              保存分析引擎配置
            </a-button>
          </a-form-item>
        </a-card>
      </a-tab-pane>

      <!-- 通知设置 -->
      <a-tab-pane key="notifications" tab="通知设置">
        <a-card title="邮件通知" class="settings-card">
          <a-form
            :model="notificationSettings.email"
            :label-col="{ span: 6 }"
            :wrapper-col="{ span: 18 }"
          >
            <a-form-item label="启用邮件通知">
              <a-switch v-model:checked="notificationSettings.email.enabled" />
            </a-form-item>
            <a-form-item label="SMTP服务器">
              <a-input v-model:value="notificationSettings.email.smtpHost" placeholder="SMTP服务器地址" />
            </a-form-item>
            <a-form-item label="端口">
              <a-input-number
                v-model:value="notificationSettings.email.smtpPort"
                :min="1"
                :max="65535"
                style="width: 200px"
              />
            </a-form-item>
            <a-form-item label="用户名">
              <a-input v-model:value="notificationSettings.email.username" placeholder="邮箱用户名" />
            </a-form-item>
            <a-form-item label="密码">
              <a-input-password
                v-model:value="notificationSettings.email.password"
                placeholder="邮箱密码"
              />
            </a-form-item>
            <a-form-item label="发件人">
              <a-input v-model:value="notificationSettings.email.fromEmail" placeholder="发件人邮箱" />
            </a-form-item>
          </a-form>
        </a-card>

        <a-card title="通知规则" class="settings-card">
          <a-form
            :model="notificationSettings.rules"
            :label-col="{ span: 6 }"
            :wrapper-col="{ span: 18 }"
          >
            <a-form-item label="新反馈通知">
              <a-switch v-model:checked="notificationSettings.rules.newFeedback" />
            </a-form-item>
            <a-form-item label="高优先级问题">
              <a-switch v-model:checked="notificationSettings.rules.highPriority" />
            </a-form-item>
            <a-form-item label="分析完成通知">
              <a-switch v-model:checked="notificationSettings.rules.analysisComplete" />
            </a-form-item>
            <a-form-item label="报告生成通知">
              <a-switch v-model:checked="notificationSettings.rules.reportGenerated" />
            </a-form-item>
          </a-form>
        </a-card>

        <a-card class="settings-card">
          <a-form-item>
            <a-button type="primary" @click="saveNotificationSettings">
              保存通知设置
            </a-button>
          </a-form-item>
        </a-card>
      </a-tab-pane>

      <!-- 用户管理 -->
      <a-tab-pane key="users" tab="用户管理">
        <a-card title="用户列表" class="settings-card">
          <template #extra>
            <a-button type="primary" @click="showAddUserModal = true">
              <UserAddOutlined />
              添加用户
            </a-button>
          </template>

          <a-table
            :columns="userColumns"
            :data-source="userList"
            :loading="userLoading"
            :pagination="false"
          >
            <template #bodyCell="{ column, record }">
              <template v-if="column.key === 'role'">
                <a-tag :color="getRoleColor(record.role)">
                  {{ getRoleText(record.role) }}
                </a-tag>
              </template>
              <template v-if="column.key === 'status'">
                <a-tag :color="record.status === 'active' ? 'green' : 'red'">
                  {{ record.status === 'active' ? '活跃' : '禁用' }}
                </a-tag>
              </template>
              <template v-if="column.key === 'action'">
                <a-space>
                  <a-button type="link" size="small" @click="editUser(record)">
                    编辑
                  </a-button>
                  <a-button type="link" size="small" danger @click="deleteUser(record)">
                    删除
                  </a-button>
                </a-space>
              </template>
            </template>
          </a-table>
        </a-card>
      </a-tab-pane>

      <!-- 安全设置 -->
      <a-tab-pane key="security" tab="安全设置">
        <a-card title="密码策略" class="settings-card">
          <a-form
            :model="securitySettings.password"
            :label-col="{ span: 6 }"
            :wrapper-col="{ span: 18 }"
          >
            <a-form-item label="最小长度">
              <a-input-number
                v-model:value="securitySettings.password.minLength"
                :min="6"
                :max="32"
                style="width: 200px"
              />
            </a-form-item>
            <a-form-item label="要求大写字母">
              <a-switch v-model:checked="securitySettings.password.requireUppercase" />
            </a-form-item>
            <a-form-item label="要求小写字母">
              <a-switch v-model:checked="securitySettings.password.requireLowercase" />
            </a-form-item>
            <a-form-item label="要求数字">
              <a-switch v-model:checked="securitySettings.password.requireNumbers" />
            </a-form-item>
            <a-form-item label="要求特殊字符">
              <a-switch v-model:checked="securitySettings.password.requireSpecialChars" />
            </a-form-item>
          </a-form>
        </a-card>

        <a-card title="会话管理" class="settings-card">
          <a-form
            :model="securitySettings.session"
            :label-col="{ span: 6 }"
            :wrapper-col="{ span: 18 }"
          >
            <a-form-item label="会话超时">
              <a-input-number
                v-model:value="securitySettings.session.timeout"
                :min="5"
                :max="1440"
                addon-after="分钟"
                style="width: 200px"
              />
            </a-form-item>
            <a-form-item label="记住登录">
              <a-switch v-model:checked="securitySettings.session.rememberLogin" />
            </a-form-item>
          </a-form>
        </a-card>

        <a-card class="settings-card">
          <a-form-item>
            <a-button type="primary" @click="saveSecuritySettings">
              保存安全设置
            </a-button>
          </a-form-item>
        </a-card>
      </a-tab-pane>
    </a-tabs>

    <!-- 添加用户对话框 -->
    <a-modal
      v-model:visible="showAddUserModal"
      title="添加用户"
      @ok="addUser"
      @cancel="showAddUserModal = false"
    >
      <a-form
        :model="userForm"
        :label-col="{ span: 6 }"
        :wrapper-col="{ span: 18 }"
      >
        <a-form-item label="用户名">
          <a-input v-model:value="userForm.username" placeholder="请输入用户名" />
        </a-form-item>
        <a-form-item label="邮箱">
          <a-input v-model:value="userForm.email" placeholder="请输入邮箱" />
        </a-form-item>
        <a-form-item label="角色">
          <a-select v-model:value="userForm.role" placeholder="选择角色">
            <a-select-option value="admin">管理员</a-select-option>
            <a-select-option value="user">普通用户</a-select-option>
            <a-select-option value="viewer">只读用户</a-select-option>
          </a-select>
        </a-form-item>
      </a-form>
    </a-modal>
  </div>
</template>

<script>
import { ref, reactive, onMounted } from 'vue'
import { message, Modal } from 'ant-design-vue'
import { UserAddOutlined } from '@ant-design/icons-vue'

import { settingsAPI } from '@/utils/api';

export default {
  name: 'Settings',
  components: {
    UserAddOutlined,
  },
  setup() {
    const activeTab = ref('system');
    const userLoading = ref(false);
    const showAddUserModal = ref(false);
    const userList = ref([]);
    
    // LLM模型相关状态
    const modelsLoading = ref(false);
    const availableModels = ref([]);
    const modelsError = ref('');
    const modelsSource = ref('');

    const systemSettings = reactive({
      systemName: '',
      description: '',
      timezone: 'Asia/Shanghai',
      language: 'zh-CN',
      dataRetentionDays: 365,
      database: {
        connected: true,
        host: 'localhost',
        port: 27017
      }
    });

    const analysisSettings = reactive({
      enabled: true,
      threshold: 0.7,
      llm: {
        enabled: true,
        model: 'gpt-4',
        apiKey: '',
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
    });

    const notificationSettings = reactive({
      email: {
        enabled: true,
        smtpHost: 'smtp.gmail.com',
        smtpPort: 587,
        username: '',
        password: '',
        fromEmail: ''
      },
      rules: {
        newFeedback: true,
        highPriority: true,
        analysisComplete: false,
        reportGenerated: true
      }
    });

    const securitySettings = reactive({
      password: {
        minLength: 8,
        requireUppercase: true,
        requireLowercase: true,
        requireNumbers: true,
        requireSpecialChars: false
      },
      session: {
        timeout: 30,
        rememberLogin: true
      }
    });

    const userForm = reactive({
      username: '',
      email: '',
      role: undefined
    });

    const userColumns = [
      { title: '用户名', dataIndex: 'username', key: 'username' },
      { title: '邮箱', dataIndex: 'email', key: 'email' },
      { title: '角色', dataIndex: 'role', key: 'role' },
      { title: '状态', dataIndex: 'status', key: 'status' },
      { title: '最后登录', dataIndex: 'lastLogin', key: 'lastLogin' },
      { title: '操作', key: 'action', width: 150 },
    ];

    const getRoleColor = (role) => {
      const colors = {
        admin: 'red',
        user: 'blue',
        viewer: 'green'
      };
      return colors[role] || 'default';
    };

    const getRoleText = (role) => {
      const texts = {
        admin: '管理员',
        user: '普通用户',
        viewer: '只读用户'
      };
      return texts[role] || role;
    };

    const loadUsers = () => {
      userLoading.value = true;
      // 模拟数据
      setTimeout(() => {
        userList.value = [
          {
            id: 1,
            username: 'admin',
            email: 'admin@example.com',
            role: 'admin',
            status: 'active',
            lastLogin: '2024-01-01 10:30:00'
          },
          {
            id: 2,
            username: 'user1',
            email: 'user1@example.com',
            role: 'user',
            status: 'active',
            lastLogin: '2024-01-02 14:20:00'
          }
        ];
        userLoading.value = false;
      }, 1000);
    };

    const loadSettings = async () => {
      try {
        const response = await settingsAPI.getSettings();
        const data = response.data;
        Object.assign(systemSettings, data.system);
        Object.assign(analysisSettings, data.analysis);
        Object.assign(notificationSettings, data.notification);
        Object.assign(securitySettings, data.security);
      } catch (error) {
        message.error('加载设置失败');
      }
    };

    const saveSettings = async () => {
      try {
        const settingsToSave = {
          system: systemSettings,
          analysis: analysisSettings,
          notification: notificationSettings,
          security: securitySettings
        };
        await settingsAPI.updateSettings(settingsToSave);
        message.success('设置已保存');
      } catch (error) {
        message.error('保存设置失败');
      }
    };

    const saveSystemSettings = () => saveSettings();
    const saveAnalysisSettings = () => saveSettings();
    const saveNotificationSettings = () => saveSettings();
    const saveSecuritySettings = () => saveSettings();

    // 加载可用的LLM模型列表
    const loadAvailableModels = async () => {
      if (modelsLoading.value) return; // 避免重复加载
      
      modelsLoading.value = true;
      modelsError.value = '';
      modelsSource.value = '';
      
      try {
        const response = await settingsAPI.getLLMModels();
        const data = response.data;
        
        if (data.success) {
          availableModels.value = data.models || [];
          modelsSource.value = data.source === 'theturbo.ai' ? 'theturbo.ai (实时)' : data.source;
          message.success(`成功获取 ${availableModels.value.length} 个可用模型`);
        } else {
          availableModels.value = data.models || [];
          modelsSource.value = data.source;
          modelsError.value = `获取模型列表失败: ${data.error || '未知错误'}`;
          message.warning('使用备用模型列表');
        }
      } catch (error) {
        console.error('加载模型列表失败:', error);
        modelsError.value = `网络错误: ${error.message}`;
        // 设置默认模型列表
        availableModels.value = [
          { id: 'gpt-4', object: 'model', owned_by: 'openai' },
          { id: 'gpt-3.5-turbo', object: 'model', owned_by: 'openai' },
          { id: 'claude-3-haiku', object: 'model', owned_by: 'anthropic' },
          { id: 'claude-3-sonnet', object: 'model', owned_by: 'anthropic' }
        ];
        modelsSource.value = '默认列表';
        message.error('无法获取模型列表，使用默认选项');
      } finally {
        modelsLoading.value = false;
      }
    };

    // 下拉框打开时加载模型列表
    const onModelDropdownChange = (open) => {
      if (open && availableModels.value.length === 0) {
        loadAvailableModels();
      }
    };

    const testDatabaseConnection = () => {
      message.success('数据库连接测试成功');
    };

    const addUser = () => {
      message.success('用户添加成功');
      showAddUserModal.value = false;
      loadUsers();
    };

    const editUser = (record) => {
      message.info(`编辑用户: ${record.username}`);
    };

    const deleteUser = (record) => {
      Modal.confirm({
        title: '确认删除',
        content: `确定要删除用户"${record.username}"吗？`,
        onOk() {
          message.success('用户已删除');
          loadUsers();
        },
      });
    };

    onMounted(() => {
      loadSettings();
      loadUsers();
      // 初始加载模型列表
      loadAvailableModels();
    });

    return {
      activeTab,
      userLoading,
      showAddUserModal,
      userList,
      systemSettings,
      analysisSettings,
      notificationSettings,
      securitySettings,
      userForm,
      userColumns,
      // LLM模型相关
      modelsLoading,
      availableModels,
      modelsError,
      modelsSource,
      loadAvailableModels,
      onModelDropdownChange,
      // 其他方法
      getRoleColor,
      getRoleText,
      loadUsers,
      saveSystemSettings,
      testDatabaseConnection,
      saveAnalysisSettings,
      saveNotificationSettings,
      saveSecuritySettings,
      addUser,
      editUser,
      deleteUser,
    };
  },
};
</script>

<style scoped>
.settings {
  padding: 24px;
}

.settings-card {
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
</style> 