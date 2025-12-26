/**
 * 日期格式化工具函数
 */

/**
 * 格式化日期字符串为友好的时间描述
 * @param dateStr - 日期字符串
 * @returns 格式化后的时间描述
 */
export function formatDate(dateStr: string | null | undefined): string {
  if (!dateStr) return '暂无更新'

  const date = new Date(dateStr)
  if (isNaN(date.getTime())) return '暂无更新'

  const now = new Date()
  const diff = now.getTime() - date.getTime()
  const minutes = Math.floor(diff / 60000)
  const hours = Math.floor(diff / 3600000)
  const days = Math.floor(diff / 86400000)

  if (minutes < 1) return '刚刚更新'
  if (minutes < 60) return `${minutes} 分钟前更新`
  if (hours < 24) return `${hours} 小时前更新`
  if (days < 7) return `${days} 天前更新`

  // 返回具体时间
  return date.toLocaleString('zh-CN', {
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}

/**
 * 格式化时间戳为本地时间字符串
 * @param timestamp - Unix 时间戳（毫秒）
 * @returns 格式化后的时间字符串
 */
export function formatTimestamp(timestamp: number): string {
  const date = new Date(timestamp)
  return date.toLocaleString('zh-CN', {
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}

/**
 * 格式化内容长度为可读字符串
 * @param length - 内容长度（字符数）
 * @returns 格式化后的长度字符串
 */
export function formatContentLength(length: number): string {
  if (length < 1000) return `${length} 字`
  return `${(length / 1000).toFixed(1)}k 字`
}

/**
 * 格式化完整日期时间
 * @param dateStr - 日期字符串
 * @returns 完整的日期时间字符串
 */
export function formatDateTime(dateStr: string | null | undefined): string {
  if (!dateStr) return ''
  const date = new Date(dateStr)
  if (isNaN(date.getTime())) return ''

  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit'
  })
}

/**
 * 格式化日期为 YYYY-MM-DD 格式
 * @param date - 日期对象或字符串
 * @returns YYYY-MM-DD 格式的日期字符串
 */
export function formatDateToISO(date: Date | string): string {
  const d = typeof date === 'string' ? new Date(date) : date
  if (isNaN(d.getTime())) return ''

  return d.toISOString().split('T')[0]
}

/**
 * 计算相对时间描述
 * @param dateStr - 日期字符串
 * @returns 相对时间描述（如"3天前"）
 */
export function getRelativeTime(dateStr: string | null | undefined): string {
  if (!dateStr) return ''
  const date = new Date(dateStr)
  if (isNaN(date.getTime())) return ''

  const now = new Date()
  const diff = now.getTime() - date.getTime()
  const seconds = Math.floor(diff / 1000)
  const minutes = Math.floor(seconds / 60)
  const hours = Math.floor(minutes / 60)
  const days = Math.floor(hours / 24)

  if (seconds < 60) return `${seconds}秒前`
  if (minutes < 60) return `${minutes}分钟前`
  if (hours < 24) return `${hours}小时前`
  if (days < 30) return `${days}天前`

  const months = Math.floor(days / 30)
  if (months < 12) return `${months}个月前`

  const years = Math.floor(days / 365)
  return `${years}年前`
}
