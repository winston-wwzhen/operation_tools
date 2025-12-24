/**
 * 文章 API 模块
 */
import { request } from '../index'

export function generateAndSave(data) {
  return request({
    url: '/articles/generate-and-save',
    method: 'post',
    data,
    timeout: 120000
  })
}

export function getMyArticles(params = {}) {
  return request({
    url: '/articles/my-articles',
    method: 'get',
    params
  })
}

export function getArticle(id) {
  return request({
    url: `/articles/${id}`,
    method: 'get'
  })
}

export function setArticleVisibility(id, isPublic) {
  return request({
    url: `/articles/${id}/visibility`,
    method: 'patch',
    params: { is_public: isPublic }
  })
}

export function deleteArticle(id) {
  return request({
    url: `/articles/${id}`,
    method: 'delete'
  })
}

export function getSharedArticle(shareToken) {
  return request({
    url: `/articles/share/${shareToken}`,
    method: 'get'
  })
}
