/**
 * API 请求配置
 * 基于 axios 创建统一的请求实例
 */
import axios from 'axios'
import { ElMessage } from 'element-plus'

// 导出 API 模块
import * as status from './modules/status'
import * as content from './modules/content'
import history from './modules/history'
import * as auth from './modules/auth'
import * as articles from './modules/articles'

// 创建 axios 实例
const request = axios.create({
  // 开发环境使用 localhost:3000，生产环境使用相对路径 /api（通过 Nginx 反向代理）
  baseURL: process.env.VUE_APP_API_BASE_URL || 'http://localhost:3000',
  timeout: 600000,  // 10分钟，适配 glm-4.7 等较慢的模型
  headers: {
    'Content-Type': 'application/json'
  }
})

// 请求拦截器
request.interceptors.request.use(
  config => {
    // 添加 token 到请求头
    const token = localStorage.getItem('hotspotai_token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  error => {
    console.error('请求错误:', error)
    return Promise.reject(error)
  }
)

// 响应拦截器
request.interceptors.response.use(
  response => {
    const res = response.data
    return res
  },
  error => {
    console.error('响应错误:', error)
    let message = '请求失败'

    if (error.response) {
      // 服务器返回错误状态码
      const status = error.response.status
      switch (status) {
        case 400:
          message = error.response.data?.detail || '请求参数错误'
          break
        case 401:
          // 优先使用后端返回的具体错误信息（如"用户名或密码错误"）
          message = error.response.data?.detail || '登录已过期，请重新登录'
          // 如果是登录过期（不是登录失败），清除 token 并跳转
          if (message === '登录已过期，请重新登录' || message.includes('Invalid')) {
            localStorage.removeItem('hotspotai_token')
            localStorage.removeItem('hotspotai_user')
            if (window.location.pathname !== '/login') {
              window.location.href = '/login'
            }
          }
          break
        case 500:
          message = '服务器内部错误'
          break
        default:
          message = error.response.data?.detail || `请求失败 (${status})`
      }
    } else if (error.request) {
      // 请求已发出但没有收到响应
      message = '网络连接失败，请检查后端服务是否启动'
    } else {
      // 请求配置出错
      message = error.message
    }

    ElMessage.error(message)
    return Promise.reject(error)
  }
)

// 默认导出 request (供 import request from '../index' 使用)
export default request

// 命名导出 (供 import { request, status, content, history, auth, articles } from '@/api' 使用)
export { request, status, content, history, auth, articles }
