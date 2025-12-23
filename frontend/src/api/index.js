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

// 创建 axios 实例
const request = axios.create({
  baseURL: process.env.VUE_APP_API_BASE_URL || 'http://localhost:3000',
  timeout: 60000,
  headers: {
    'Content-Type': 'application/json'
  }
})

// 请求拦截器
request.interceptors.request.use(
  config => {
    // 可以在这里添加 token 等认证信息
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
      switch (error.response.status) {
        case 400:
          message = error.response.data?.message || '请求参数错误'
          break
        case 500:
          message = '服务器内部错误'
          break
        default:
          message = error.response.data?.message || `请求失败 (${error.response.status})`
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

// 命名导出 (供 import { request, status, content, history } from '@/api' 使用)
export { request, status, content, history }
