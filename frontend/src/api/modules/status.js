import request from '../index'

/**
 * 获取系统状态
 */
export function getStatus() {
  return request({
    url: '/api/status',
    method: 'get'
  })
}

/**
 * 健康检查
 */
export function healthCheck() {
  return request({
    url: '/health',
    method: 'get'
  })
}
