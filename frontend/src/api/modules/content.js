import request from '../index'

/**
 * 刷新热点话题
 */
export function refreshTopics() {
  return request({
    url: '/api/refresh-topics',
    method: 'post'
  })
}

/**
 * 生成文章草稿
 */
export function generateDraft(data) {
  return request({
    url: '/api/generate-draft',
    method: 'post',
    data,
    timeout: 120000 // 2分钟超时
  })
}
