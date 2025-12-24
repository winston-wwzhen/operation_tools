/**
 * 加载状态管理的组合式函数
 */
import { ref } from 'vue'

export function useLoading(initialState = false) {
  const isLoading = ref(initialState)
  const error = ref(null)
  const data = ref(null)

  /**
   * 开始加载
   */
  const startLoading = () => {
    isLoading.value = true
    error.value = null
  }

  /**
   * 结束加载
   */
  const stopLoading = () => {
    isLoading.value = false
  }

  /**
   * 设置错误
   */
  const setError = (err) => {
    error.value = err
    isLoading.value = false
  }

  /**
   * 设置数据
   */
  const setData = (newData) => {
    data.value = newData
    error.value = null
  }

  /**
   * 重置状态
   */
  const reset = () => {
    isLoading.value = false
    error.value = null
    data.value = null
  }

  /**
   * 执行异步操作
   */
  const execute = async (asyncFn) => {
    startLoading()
    try {
      const result = await asyncFn()
      setData(result)
      return result
    } catch (err) {
      setError(err)
      throw err
    } finally {
      stopLoading()
    }
  }

  return {
    isLoading,
    error,
    data,
    startLoading,
    stopLoading,
    setError,
    setData,
    reset,
    execute
  }
}
