/**
 * 消息提示的组合式函数
 */
import { ElMessage, ElMessageBox, ElNotification } from 'element-plus'
import { MESSAGE_TYPES } from '@/constants'

export function useMessage() {
  /**
   * 显示消息
   */
  const show = (message, type = MESSAGE_TYPES.INFO) => {
    ElMessage({
      message,
      type,
      duration: 3000
    })
  }

  /**
   * 成功消息
   */
  const success = (message) => {
    show(message, MESSAGE_TYPES.SUCCESS)
  }

  /**
   * 警告消息
   */
  const warning = (message) => {
    show(message, MESSAGE_TYPES.WARNING)
  }

  /**
   * 错误消息
   */
  const error = (message) => {
    show(message, MESSAGE_TYPES.ERROR)
  }

  /**
   * 信息消息
   */
  const info = (message) => {
    show(message, MESSAGE_TYPES.INFO)
  }

  /**
   * 确认对话框
   */
  const confirm = async (message, title = '提示') => {
    try {
      await ElMessageBox.confirm(message, title, {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      })
      return true
    } catch {
      return false
    }
  }

  /**
   * 显示通知
   */
  const notify = (options) => {
    ElNotification({
      title: options.title || '通知',
      message: options.message,
      type: options.type || MESSAGE_TYPES.INFO,
      duration: options.duration || 3000
    })
  }

  return {
    show,
    success,
    warning,
    error,
    info,
    confirm,
    notify
  }
}
