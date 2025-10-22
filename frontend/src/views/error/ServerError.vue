<template>
  <div class="error-page">
    <a-result
      status="500"
      title="500"
      sub-title="抱歉，服务器出现错误。"
    >
      <template #extra>
        <a-space>
          <a-button type="primary" @click="refresh">
            刷新页面
          </a-button>
          <a-button @click="goHome">
            返回首页
          </a-button>
        </a-space>
      </template>
    </a-result>
  </div>
</template>

<script>
import { useRouter } from 'vue-router'

export default {
  name: 'ServerError',
  setup() {
    const router = useRouter()
    
    const refresh = () => {
      window.location.reload()
    }
    
    const goHome = () => {
      router.push('/')
    }
    
    return {
      refresh,
      goHome,
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