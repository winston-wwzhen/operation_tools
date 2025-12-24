import request from '../index'

/**
 * 获取公开状态（无需认证）
 */
export function getPublicStatus() {
  return request({
    url: '/status/public',
    method: 'get'
  })
}

/**
 * 获取系统状态（需要认证）
 * 管理员可以看到完整配置（敏感字段脱敏）和日志
 * 普通用户只能看到公开配置和热点话题
 */
export function getStatus() {
  return request({
    url: '/status',
    method: 'get'
  })
}

/**
 * 健康检查（无需认证）
 */
export function healthCheck() {
  return request({
    url: '/health',
    method: 'get'
  })
}
