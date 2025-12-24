/**
 * 认证 API 模块
 */
import { request } from '../index'

export function register(data) {
  return request({
    url: '/api/auth/register',
    method: 'post',
    data
  })
}

export function login(data) {
  return request({
    url: '/api/auth/login',
    method: 'post',
    data
  })
}

export function logout() {
  return request({
    url: '/api/auth/logout',
    method: 'post'
  })
}

export function getMe() {
  return request({
    url: '/api/auth/me',
    method: 'get'
  })
}
