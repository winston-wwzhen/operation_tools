/**
 * 分类管理 API
 */
import { request } from '../index'

/**
 * 获取所有分类
 * @param {Object} params - 查询参数
 * @param {boolean} params.include_inactive - 是否包含未激活的分类
 * @returns {Promise} 分类列表
 */
export function getCategories(params = {}) {
  return request({
    url: '/categories',
    method: 'get',
    params
  })
}

/**
 * 获取所有分类及关键词（用于抓取任务）
 * @returns {Promise} 分类列表，包含关键词
 */
export function getCategoriesWithKeywords() {
  return request({
    url: '/categories/with-keywords',
    method: 'get'
  })
}

/**
 * 获取分类详情
 * @param {number} id - 分类ID
 * @returns {Promise} 分类详情，包含关键词和平台配置
 */
export function getCategory(id) {
  return request({
    url: `/categories/${id}`,
    method: 'get'
  })
}

/**
 * 创建分类
 * @param {Object} data - 分类数据
 * @param {string} data.name - 分类名称
 * @param {string} data.slug - URL标识
 * @param {string} data.description - 描述
 * @param {string} data.icon - 图标（emoji）
 * @param {string} data.color - 主题色
 * @param {boolean} data.is_active - 是否启用
 * @param {number} data.sort_order - 排序
 * @param {string[]} data.keywords - 关键词列表
 * @param {string[]} data.platforms - 启用的平台列表
 * @returns {Promise}
 */
export function createCategory(data) {
  return request({
    url: '/categories',
    method: 'post',
    data
  })
}

/**
 * 更新分类
 * @param {number} id - 分类ID
 * @param {Object} data - 要更新的数据
 * @returns {Promise}
 */
export function updateCategory(id, data) {
  return request({
    url: `/categories/${id}`,
    method: 'put',
    data
  })
}

/**
 * 删除分类
 * @param {number} id - 分类ID
 * @returns {Promise}
 */
export function deleteCategory(id) {
  return request({
    url: `/categories/${id}`,
    method: 'delete'
  })
}

/**
 * 初始化默认分类
 * @returns {Promise}
 */
export function initDefaultCategories() {
  return request({
    url: '/categories/init-defaults',
    method: 'post'
  })
}

/**
 * 更新分类关键词
 * @param {number} categoryId - 分类ID
 * @param {string[]} keywords - 关键词列表
 * @returns {Promise}
 */
export function updateKeywords(categoryId, keywords) {
  return request({
    url: `/categories/${categoryId}/keywords`,
    method: 'put',
    data: { keywords }
  })
}

/**
 * 更新分类平台配置
 * @param {number} categoryId - 分类ID
 * @param {string[]} platforms - 启用的平台列表
 * @returns {Promise}
 */
export function updatePlatformConfig(categoryId, platforms) {
  return request({
    url: `/categories/${categoryId}/platforms`,
    method: 'put',
    data: { platforms }
  })
}

/**
 * 按分类获取热点话题
 * @param {number} categoryId - 分类ID
 * @param {Object} params - 查询参数
 * @param {string} params.start_date - 起始日期 (YYYY-MM-DD)
 * @param {string} params.end_date - 结束日期 (YYYY-MM-DD)
 * @param {string} params.source - 数据源筛选
 * @param {number} params.offset - 偏移量
 * @param {number} params.limit - 每页数量
 * @returns {Promise}
 */
export function getCategoryTopics(categoryId, params = {}) {
  return request({
    url: `/categories/${categoryId}/topics`,
    method: 'get',
    params
  })
}

/**
 * 手动刷新分类热点（仅管理员）
 * @param {number[]} categoryIds - 要刷新的分类ID列表，不传则刷新所有
 * @returns {Promise}
 */
export function refreshCategoryTopics(categoryIds = null) {
  return request({
    url: '/categories/refresh',
    method: 'post',
    data: { category_ids: categoryIds }
  })
}

export default {
  getCategories,
  getCategoriesWithKeywords,
  getCategory,
  createCategory,
  updateCategory,
  deleteCategory,
  initDefaultCategories,
  updateKeywords,
  updatePlatformConfig,
  getCategoryTopics,
  refreshCategoryTopics
}
