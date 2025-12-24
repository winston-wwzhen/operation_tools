/**
 * 应用常量定义
 */

// === API 相关 ===
export const API_BASE_URL = process.env.VUE_APP_API_BASE_URL || 'http://localhost:3000'
export const API_TIMEOUT = 600000 // 10分钟

// === 存储 Key ===
export const STORAGE_KEYS = {
  TOKEN: 'hotspotai_token',
  USER: 'hotspotai_user',
  THEME: 'hotspotai_theme',
  LANGUAGE: 'hotspotai_language'
}

// === 平台配置 ===
export const PLATFORMS = [
  { id: 'weibo', name: '微博', icon: '📱', color: '#FF8200' },
  { id: 'zhihu', name: '知乎', icon: '🧠', color: '#0084FF' },
  { id: 'douyin', name: '抖音', icon: '🎵', color: '#000000' },
  { id: 'xiaohongshu', name: '小红书', icon: '📕', color: '#FF2442' },
  { id: 'toutiao', name: '今日头条', icon: '📰', color: '#F85959' },
  { id: 'baidu', name: '百度', icon: '🔍', color: '#2932E1' }
]

// === 默认分类 ===
export const DEFAULT_CATEGORIES = [
  { id: 1, name: 'AI科技', slug: 'ai-tech', icon: '🤖', color: '#6366f1' },
  { id: 2, name: '财经投资', slug: 'finance', icon: '💰', color: '#10b981' },
  { id: 3, name: '职场成长', slug: 'career', icon: '💼', color: '#f59e0b' },
  { id: 4, name: '健康养生', slug: 'health', icon: '🏥', color: '#ef4444' },
  { id: 5, name: '教育育儿', slug: 'education', icon: '📚', color: '#8b5cf6' },
  { id: 6, name: '数码评测', slug: 'digital', icon: '📱', color: '#3b82f6' },
  { id: 7, name: '美食生活', slug: 'food', icon: '🍜', color: '#f97316' },
  { id: 8, name: '影视娱乐', slug: 'entertainment', icon: '🎬', color: '#ec4899' },
  { id: 9, name: '旅游出行', slug: 'travel', icon: '✈️', color: '#06b6d4' },
  { id: 10, name: '情感心理', slug: 'emotion', icon: '💕', color: '#d946ef' }
]

// === 分页配置 ===
export const PAGINATION = {
  DEFAULT_PAGE_SIZE: 10,
  PAGE_SIZES: [10, 20, 50, 100]
}

// === 状态码 ===
export const HTTP_STATUS = {
  OK: 200,
  CREATED: 201,
  NO_CONTENT: 204,
  BAD_REQUEST: 400,
  UNAUTHORIZED: 401,
  FORBIDDEN: 403,
  NOT_FOUND: 404,
  CONFLICT: 409,
  UNPROCESSABLE_ENTITY: 422,
  INTERNAL_SERVER_ERROR: 500
}

// === 路由路径 ===
export const ROUTES = {
  HOME: '/',
  LOGIN: '/login',
  HISTORY: '/history',
  MY_ARTICLES: '/my-articles',
  ARTICLE_DETAIL: '/article/:id',
  SHARED_ARTICLE: '/shared/:token',
  CATEGORY_MANAGEMENT: '/categories'
}

// === 消息类型 ===
export const MESSAGE_TYPES = {
  SUCCESS: 'success',
  WARNING: 'warning',
  ERROR: 'error',
  INFO: 'info'
}

// === 微信平台配置 ===
export const WECHAT_PLATFORM = 'wechat'

// === 默认值 ===
export const DEFAULTS = {
  TOPIC_LIMIT: 10,
  AUTO_RUN: false,
  REFRESH_INTERVAL: 120000 // 2分钟
}
