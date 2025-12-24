/**
 * 历史数据 API 模块
 */
import { request } from '../index'

export default {
  /**
   * 获取历史热点数据（支持分页和筛选）
   * @param {Object} params - 查询参数
   * @param {string} params.start_date - 起始日期 (YYYY-MM-DD)
   * @param {string} params.end_date - 结束日期 (YYYY-MM-DD)
   * @param {string} params.source - 数据源筛选
   * @param {number} params.offset - 偏移量
   * @param {number} params.limit - 每页数量
   */
  getHistory(params) {
    return request({
      url: '/history/topics',
      method: 'get',
      params
    })
  },

  /**
   * 获取所有可用日期列表
   */
  getDates() {
    return request({
      url: '/history/dates',
      method: 'get'
    })
  },

  /**
   * 获取数据库统计信息
   */
  getStats() {
    return request({
      url: '/history/stats',
      method: 'get'
    })
  }
}
