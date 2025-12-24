<template>
  <div class="min-h-screen bg-gradient-to-br from-indigo-100 via-purple-50 to-pink-100 flex items-center justify-center p-4">
    <div class="bg-white rounded-2xl shadow-xl w-full max-w-md p-8">
      <!-- Logo 和标题 -->
      <div class="text-center mb-8">
        <el-icon class="text-5xl text-indigo-600 mb-4"><Data-Analysis /></el-icon>
        <h1 class="text-2xl font-bold text-gray-900">HotSpotAI</h1>
        <p class="text-gray-500 mt-2">{{ isLogin ? '登录您的账户' : '创建新账户' }}</p>
      </div>

      <!-- 表单 -->
      <el-form
        ref="formRef"
        :model="form"
        :rules="rules"
        @submit.prevent="handleSubmit"
        label-position="top"
      >
        <el-form-item prop="username">
          <el-input
            v-model="form.username"
            placeholder="用户名"
            :prefix-icon="User"
            size="large"
          />
        </el-form-item>

        <el-form-item prop="email" v-if="!isLogin">
          <el-input
            v-model="form.email"
            placeholder="邮箱"
            :prefix-icon="Message"
            size="large"
          />
        </el-form-item>

        <el-form-item prop="password">
          <el-input
            v-model="form.password"
            type="password"
            placeholder="密码"
            :prefix-icon="Lock"
            size="large"
            show-password
          />
        </el-form-item>

        <el-form-item v-if="!isLogin" prop="confirmPassword">
          <el-input
            v-model="form.confirmPassword"
            type="password"
            placeholder="确认密码"
            :prefix-icon="Lock"
            size="large"
            show-password
          />
        </el-form-item>

        <el-form-item>
          <el-button
            type="primary"
            native-type="submit"
            size="large"
            :loading="loading"
            class="w-full"
          >
            {{ isLogin ? '登录' : '注册' }}
          </el-button>
        </el-form-item>
      </el-form>

      <!-- 切换登录/注册 -->
      <div class="text-center mt-6">
        <span class="text-gray-500">
          {{ isLogin ? '还没有账户？' : '已有账户？' }}
        </span>
        <el-button type="text" @click="toggleMode">
          {{ isLogin ? '立即注册' : '立即登录' }}
        </el-button>
      </div>

      <!-- 返回首页 -->
      <div class="text-center mt-4">
        <el-button type="text" @click="goHome" class="text-gray-400">
          <el-icon><Back /></el-icon>
          返回首页
        </el-button>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { User, Message, Lock, DataAnalysis, Back } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { useAuth } from '@/composables/useAuth'
import { auth } from '@/api'

export default {
  name: 'Login',
  components: { User, Message, Lock, DataAnalysis, Back },
  setup() {
    const router = useRouter()
    const { login } = useAuth()

    const isLogin = ref(true)
    const formRef = ref(null)
    const loading = ref(false)

    const form = reactive({
      username: '',
      email: '',
      password: '',
      confirmPassword: ''
    })

    // 验证确认密码
    const validateConfirmPassword = (rule, value, callback) => {
      if (!isLogin.value && value !== form.password) {
        callback(new Error('两次输入的密码不一致'))
      } else {
        callback()
      }
    }

    // 表单验证规则
    const rules = {
      username: [
        { required: true, message: '请输入用户名', trigger: 'blur' },
        { min: 3, max: 20, message: '用户名长度应为3-20个字符', trigger: 'blur' }
      ],
      email: [
        { required: true, message: '请输入邮箱', trigger: 'blur' },
        { type: 'email', message: '请输入有效的邮箱地址', trigger: 'blur' }
      ],
      password: [
        { required: true, message: '请输入密码', trigger: 'blur' },
        { min: 6, message: '密码长度至少为6个字符', trigger: 'blur' }
      ],
      confirmPassword: [
        { required: true, message: '请确认密码', trigger: 'blur' },
        { validator: validateConfirmPassword, trigger: 'blur' }
      ]
    }

    // 切换登录/注册模式
    const toggleMode = () => {
      isLogin.value = !isLogin.value
      formRef.value?.clearValidate()
      // 清空表单
      form.username = ''
      form.email = ''
      form.password = ''
      form.confirmPassword = ''
    }

    // 提交表单
    const handleSubmit = async () => {
      try {
        await formRef.value.validate()
        loading.value = true

        if (isLogin.value) {
          await login({ username: form.username, password: form.password })
        } else {
          await auth.register(form.username, form.email, form.password)
        }

        router.push('/')
      } catch (e) {
        // 验证或 API 错误已处理
      } finally {
        loading.value = false
      }
    }

    // 返回首页
    const goHome = () => {
      router.push('/')
    }

    return {
      isLogin,
      form,
      formRef,
      rules,
      loading,
      toggleMode,
      handleSubmit,
      goHome
    }
  }
}
</script>
