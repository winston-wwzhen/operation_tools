/**
 * 应用全局状态管理 Store
 */
import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useAppStore = defineStore('app', () => {
  // 侧边栏状态
  const sidebarCollapsed = ref(false)

  // 主题
  const theme = ref(localStorage.getItem('hotspotai_theme') || 'light')

  // 加载状态
  const globalLoading = ref(false)

  /**
   * 切换侧边栏
   */
  const toggleSidebar = () => {
    sidebarCollapsed.value = !sidebarCollapsed.value
  }

  /**
   * 设置主题
   */
  const setTheme = (newTheme) => {
    theme.value = newTheme
    localStorage.setItem('hotspotai_theme', newTheme)
    document.documentElement.setAttribute('data-theme', newTheme)
  }

  /**
   * 设置全局加载状态
   */
  const setGlobalLoading = (loading) => {
    globalLoading.value = loading
  }

  return {
    // 状态
    sidebarCollapsed,
    theme,
    globalLoading,
    // 方法
    toggleSidebar,
    setTheme,
    setGlobalLoading
  }
})
