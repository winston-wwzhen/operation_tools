/**
 * 微信公众号 API 模块
 */
import { request } from '../index'

/**
 * 绑定微信公众号账号
 * @param {Object} data - 账号信息
 * @param {string} data.app_id - 微信 AppID
 * @param {string} data.secret - 微信 Secret
 * @param {string} [data.account_name] - 公众号名称（可选）
 */
export function bindWeChatAccount(data) {
  return request({
    url: '/wechat/accounts',
    method: 'post',
    data
  })
}

/**
 * 获取已绑定的公众号列表
 * @returns {Promise} 公众号列表
 */
export function getWeChatAccounts() {
  return request({
    url: '/wechat/accounts',
    method: 'get'
  })
}

/**
 * 解绑公众号账号
 * @param {number} accountId - 账号 ID
 */
export function unbindWeChatAccount(accountId) {
  return request({
    url: `/wechat/accounts/${accountId}`,
    method: 'delete'
  })
}

/**
 * 保存文章为草稿
 * @param {number} articleId - 文章 ID
 * @param {number} wechatAccountId - 公众号账号 ID
 * @returns {Promise} 草稿保存结果
 */
export function saveAsDraft(articleId, wechatAccountId) {
  return request({
    url: `/wechat/articles/${articleId}/draft`,
    method: 'post',
    data: { wechat_account_id: wechatAccountId }
  })
}

/**
 * 自动发布文章
 * @param {number} articleId - 文章 ID
 * @param {number} wechatAccountId - 公众号账号 ID
 * @returns {Promise} 发布结果
 */
export function publishToWeChat(articleId, wechatAccountId) {
  return request({
    url: `/wechat/articles/${articleId}/publish`,
    method: 'post',
    data: { wechat_account_id: wechatAccountId }
  })
}

/**
 * 检查发布限制
 * @param {number} articleId - 文章 ID
 * @param {number} wechatAccountId - 公众号账号 ID
 * @returns {Promise} 发布状态检查结果
 */
export function checkPublishStatus(articleId, wechatAccountId) {
  return request({
    url: `/wechat/articles/${articleId}/publish-status`,
    method: 'get',
    params: { wechat_account_id: wechatAccountId }
  })
}

/**
 * 获取发布记录
 * @param {Object} [params] - 查询参数
 * @param {number} [params.offset] - 偏移量
 * @param {number} [params.limit] - 每页数量
 * @returns {Promise} 发布记录列表
 */
export function getPublishLogs(params = {}) {
  return request({
    url: '/wechat/publish-logs',
    method: 'get',
    params
  })
}
