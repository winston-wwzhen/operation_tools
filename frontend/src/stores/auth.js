/**
 * 认证状态管理 Store
 */
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { auth } from '@/api'
import { STORAGE_KEYS } from '@/constants'

export const useAuthStore = defineStore('auth', () => {
  // 状态
  const token = ref(localStorage.getItem(STORAGE_KEYS.TOKEN) || '')
  const userInfo = ref(JSON.parse(localStorage.getItem(STORAGE_KEYS.USER) || 'null'))

  // 计算属性
  const isAuthenticated = computed(() => !!token.value)
  const user = computed(() => userInfo.value)
  const isAdmin = computed(() => !!userInfo.value?.is_admin)
  const username = computed(() => userInfo.value?.username || '')

  /**
   * 登录
   */
  const login = async (credentials) => {
    const data = await auth.login(credentials)

    // 保存认证信息
    token.value = data.access_token
    userInfo.value = data.user

    localStorage.setItem(STORAGE_KEYS.TOKEN, data.access_token)
    localStorage.setItem(STORAGE_KEYS.USER, JSON.stringify(data.user))

    return data
  }

  /**
   * 登出
   */
  const logout = () => {
    token.value = ''
    userInfo.value = null

    localStorage.removeItem(STORAGE_KEYS.TOKEN)
    localStorage.removeItem(STORAGE_KEYS.USER)
  }

  /**
   * 更新用户信息
   */
  const updateUserInfo = (newUserInfo) => {
    userInfo.value = { ...userInfo.value, ...newUserInfo }
    localStorage.setItem(STORAGE_KEYS.USER, JSON.stringify(userInfo.value))
  }

  return {
    // 状态
    token,
    userInfo,
    // 计算属性
    isAuthenticated,
    user,
    isAdmin,
    username,
    // 方法
    login,
    logout,
    updateUserInfo
  }
})
