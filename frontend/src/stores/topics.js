/**
 * 热点话题状态管理 Store
 */
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { status } from '@/api'

export const useTopicsStore = defineStore('topics', () => {
  // 状态
  const topics = ref([])
  const runtimeState = ref({
    isRunning: false,
    lastRunTime: null,
    nextRunTime: null
  })
  const selectedCategory = ref(null)
  const selectedSource = ref(null)
  const selectedTag = ref(null)

  // 计算属性
  const filteredTopics = computed(() => {
    return topics.value.filter(topic => {
      // 分类筛选
      if (selectedCategory.value && topic.category_id !== selectedCategory.value) {
        return false
      }
      // 来源筛选
      if (selectedSource.value && topic.source !== selectedSource.value) {
        return false
      }
      // 标签筛选
      if (selectedTag.value && (!topic.tags || !topic.tags.includes(selectedTag.value))) {
        return false
      }
      return true
    })
  })

  const availableTags = computed(() => {
    const tags = new Set()
    topics.value.forEach(topic => {
      if (topic.tags) {
        topic.tags.forEach(tag => tags.add(tag))
      }
    })
    return Array.from(tags)
  })

  /**
   * 获取热点数据
   */
  const fetchTopics = async () => {
    try {
      const data = await status.getStatus()
      topics.value = data.hot_topics || []
      runtimeState.value = {
        isRunning: data.state?.isRunning || false,
        lastRunTime: data.state?.lastRunTime || null,
        nextRunTime: data.state?.nextRunTime || null
      }
      return data
    } catch (error) {
      console.error('获取热点数据失败:', error)
      throw error
    }
  }

  /**
   * 刷新热点
   */
  const refreshTopics = async () => {
    try {
      const data = await status.refresh()
      await fetchTopics()
      return data
    } catch (error) {
      console.error('刷新热点失败:', error)
      throw error
    }
  }

  /**
   * 设置分类筛选
   */
  const setCategoryFilter = (categoryId) => {
    selectedCategory.value = categoryId
  }

  /**
   * 设置来源筛选
   */
  const setSourceFilter = (source) => {
    selectedSource.value = source
  }

  /**
   * 设置标签筛选
   */
  const setTagFilter = (tag) => {
    selectedTag.value = tag
  }

  /**
   * 清除所有筛选
   */
  const clearFilters = () => {
    selectedCategory.value = null
    selectedSource.value = null
    selectedTag.value = null
  }

  return {
    // 状态
    topics,
    runtimeState,
    selectedCategory,
    selectedSource,
    selectedTag,
    // 计算属性
    filteredTopics,
    availableTags,
    // 方法
    fetchTopics,
    refreshTopics,
    setCategoryFilter,
    setSourceFilter,
    setTagFilter,
    clearFilters
  }
})
