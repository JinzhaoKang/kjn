<template>
  <div class="error-page">
    <a-result
      status="403"
      title="403"
      sub-title="抱歉，您没有权限访问此页面。"
    >
      <template #extra>
        <a-space>
          <a-button type="primary" @click="goHome">
            返回首页
          </a-button>
          <a-button @click="contactAdmin">
            联系管理员
          </a-button>
        </a-space>
      </template>
    </a-result>
  </div>
</template>

<script>
import { useRouter } from 'vue-router'
import { message } from 'ant-design-vue'

export default {
  name: 'Forbidden',
  setup() {
    const router = useRouter()
    
    const goHome = () => {
      router.push('/')
    }
    
    const contactAdmin = () => {
      message.info('请联系系统管理员获取相关权限')
    }
    
    return {
      goHome,
      contactAdmin,
    }
  },
}
</script>

<style scoped>
.error-page {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 100vh;
  background: #f0f2f5;
}
</style> 