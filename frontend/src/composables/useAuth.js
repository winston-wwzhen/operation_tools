/**
 * 认证状态管理 Composable
 * 提供响应式的认证状态和认证方法
 */
import { reactive, computed } from 'vue'
import { ElMessage } from 'element-plus'
import * as auth from '@/api/modules/auth'

// 全局认证状态
const state = reactive({
  user: null,
  token: null,
  loading: false
})

// 本地存储 key
const TOKEN_KEY = 'hotspotai_token'
const USER_KEY = 'hotspotai_user'

let initialized = false

export function useAuth() {
  const isAuthenticated = computed(() => !!state.token)
  const username = computed(() => state.user?.username || '')
  const isAdmin = computed(() => state.user?.is_admin || false)

  // 从 localStorage 加载认证状态
  function loadAuth() {
    try {
      const token = localStorage.getItem(TOKEN_KEY)
      const userStr = localStorage.getItem(USER_KEY)

      if (token) {
        state.token = token
        if (userStr) {
          try {
            state.user = JSON.parse(userStr)
          } catch (e) {
            console.error('Failed to parse user data:', e)
            localStorage.removeItem(USER_KEY)
          }
        }
      }
    } catch (e) {
      console.error('Failed to load auth state:', e)
    }
  }

  // 保存认证状态到 localStorage
  function saveAuth(token, user) {
    localStorage.setItem(TOKEN_KEY, token)
    localStorage.setItem(USER_KEY, JSON.stringify(user))
    state.token = token
    state.user = user
  }

  // 清除认证状态
  function clearAuth() {
    localStorage.removeItem(TOKEN_KEY)
    localStorage.removeItem(USER_KEY)
    state.token = null
    state.user = null
  }

  // 注册
  async function register(username, email, password) {
    state.loading = true
    try {
      const res = await auth.register({ username, email, password })
      saveAuth(res.access_token, res.user)
      ElMessage.success('注册成功！')
      return res
    } catch (e) {
      // 错误消息由 axios 拦截器统一处理，这里不再重复显示
      throw e
    } finally {
      state.loading = false
    }
  }

  // 登录
  async function login(username, password) {
    state.loading = true
    try {
      const res = await auth.login({ username, password })
      saveAuth(res.access_token, res.user)
      ElMessage.success('登录成功！')
      return res
    } catch (e) {
      // 错误消息由 axios 拦截器统一处理，这里不再重复显示
      throw e
    } finally {
      state.loading = false
    }
  }

  // 登出
  async function logout() {
    try {
      await auth.logout()
    } catch (e) {
      console.error('Logout error:', e)
    } finally {
      clearAuth()
      ElMessage.success('已退出登录')
    }
  }

  // 获取当前用户信息
  async function fetchUser() {
    if (!state.token) return null

    try {
      const user = await auth.getMe()
      state.user = user
      localStorage.setItem(USER_KEY, JSON.stringify(user))
      return user
    } catch (e) {
      // Token 可能已过期
      clearAuth()
      return null
    }
  }

  // 初始化（仅第一次调用时执行）
  if (!initialized) {
    loadAuth()
    initialized = true
  }

  return {
    state,
    isAuthenticated,
    isAdmin,
    username,
    register,
    login,
    logout,
    fetchUser,
    clearAuth
  }
}
