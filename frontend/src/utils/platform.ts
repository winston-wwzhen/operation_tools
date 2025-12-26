/**
 * 平台相关工具函数
 */

/**
 * 平台配置接口
 */
export interface PlatformConfig {
  id: string
  name: string
  label: string
  color: string
  icon: string
  description: string
}

/**
 * 平台配置映射表
 */
export const PLATFORMS: Record<string, PlatformConfig> = {
  wechat: {
    id: 'wechat',
    name: 'wechat',
    label: '微信公众号',
    color: 'green',
    icon: 'wechat',
    description: '深度长文 / HTML排版'
  },
  xiaohongshu: {
    id: 'xiaohongshu',
    name: 'xiaohongshu',
    label: '小红书',
    color: 'pink',
    icon: 'xiaohongshu',
    description: 'Emoji / 种草 / 标签'
  },
  zhihu: {
    id: 'zhihu',
    name: 'zhihu',
    label: '知乎',
    color: 'blue',
    icon: 'zhihu',
    description: '理性客观 / Markdown'
  },
  toutiao: {
    id: 'toutiao',
    name: 'toutiao',
    label: '今日头条',
    color: 'red',
    icon: 'toutiao',
    description: '爆款标题 / 叙事强'
  }
}

/**
 * 获取平台标签名称
 * @param platform - 平台标识
 * @returns 平台标签名称
 */
export function getPlatformLabel(platform: string): string {
  return PLATFORMS[platform]?.label || platform
}

/**
 * 根据名称获取平台标识
 * @param name - 平台名称或标识
 * @returns 平台标识，未找到返回 null
 */
export function getPlatformByName(name: string): string | null {
  // 直接匹配
  if (PLATFORMS[name]) return name

  // 标签匹配
  for (const [key, config] of Object.entries(PLATFORMS)) {
    if (name.includes(config.label) || name.includes(key)) {
      return key
    }
  }

  // 中文匹配
  if (name.includes('微信')) return 'wechat'
  if (name.includes('小红书')) return 'xiaohongshu'
  if (name.includes('知乎')) return 'zhihu'
  if (name.includes('头条')) return 'toutiao'

  return null
}

/**
 * 获取平台对应的 CSS 类名
 * @param source - 来源名称
 * @returns CSS 类名字符串
 */
export function getSourceClass(source: string): string {
  const platform = getPlatformByName(source)
  if (platform) {
    const config = PLATFORMS[platform]
    return `source-${platform} bg-${config.color}-100 text-${config.color}-700`
  }
  return 'bg-gray-100 text-gray-600'
}

/**
 * 获取平台配置
 * @param platform - 平台标识
 * @returns 平台配置对象
 */
export function getPlatformConfig(platform: string): PlatformConfig | undefined {
  return PLATFORMS[platform]
}

/**
 * 获取所有支持的平台列表
 * @returns 平台配置数组
 */
export function getAllPlatforms(): PlatformConfig[] {
  return Object.values(PLATFORMS)
}

/**
 * 获取平台颜色
 * @param platform - 平台标识
 * @returns 颜色名称
 */
export function getPlatformColor(platform: string): string {
  return PLATFORMS[platform]?.color || 'gray'
}

/**
 * 检查平台是否支持
 * @param platform - 平台标识
 * @returns 是否支持该平台
 */
export function isPlatformSupported(platform: string): boolean {
  return platform in PLATFORMS
}

/**
 * 获取平台描述
 * @param platform - 平台标识
 * @returns 平台风格描述
 */
export function getPlatformDescription(platform: string): string {
  return PLATFORMS[platform]?.description || ''
}
