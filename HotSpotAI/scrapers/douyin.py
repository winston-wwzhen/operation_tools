"""
抖音热榜爬虫模块
使用 PlaywrightScraper 基类实现，支持 API 拦截
"""
import asyncio
from playwright.async_api import async_playwright, Page
from .base import PlaywrightScraper
from .factory import register_scraper
from utils import browser_retry
from core.config import get_config


@register_scraper("douyin")
class DouyinScraper(PlaywrightScraper):
    """抖音热榜爬虫"""

    def get_platform_name(self) -> str:
        return "抖音"

    def get_headless(self) -> bool:
        """获取浏览器无头模式配置"""
        return get_config("playwright_headless", True)

    @browser_retry
    async def scrape(self, limit: int = 10) -> list:
        """抓取抖音热榜"""
        self.log_start(limit)

        captured_data = {'list': []}

        # 监听网络响应的回调
        async def handle_response(response):
            """处理 API 响应"""
            if "web/hot/search/list" in response.url and response.status == 200:
                try:
                    json_body = await response.json()
                    data_list = json_body.get('data', {}).get('word_list', [])
                    if data_list:
                        captured_data['list'] = data_list
                        self.log_warning(f'捕获到 {len(data_list)} 条 API 数据')
                except Exception as e:
                    self.log_warning(f'API 响应解析失败: {e}')

        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(
                    headless=self.get_headless(),
                    args=['--disable-blink-features=AutomationControlled']
                )

                context = await browser.new_context(
                    user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
                    viewport={'width': 1920, 'height': 1080},
                    device_scale_factor=1,
                    extra_http_headers={"Referer": "https://www.douyin.com/"}
                )

                # 防止 webdriver 检测
                await context.add_init_script(
                    "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
                )

                page = await context.new_page()
                page.on("response", handle_response)

                target_url = "https://www.douyin.com/hot"
                self.log_warning(f'正在加载页面: {target_url}')
                await page.goto(target_url, timeout=30000, wait_until="domcontentloaded")

                # 等待数据（最多 15 秒）
                self.log_warning('等待 API 数据回传...')
                for _ in range(30):
                    if captured_data['list']:
                        break
                    await asyncio.sleep(0.5)

                await browser.close()

                # 处理结果
                items = []
                if captured_data['list']:
                    for item in captured_data['list'][:limit]:
                        word = item.get('word', '')
                        if word:
                            items.append(self.format_result(
                                word,
                                f"https://www.douyin.com/search/{word}?type=hot"
                            ))
                else:
                    self.log_warning('未拦截到 API 数据')

                self.log_success(len(items))
                return items

        except Exception as e:
            self.log_error(str(e))
            return []


# 兼容旧代码的函数式接口
_scraper_instance = None


async def scrape_douyin_playwright(limit: int = 10) -> list:
    """
    兼容旧代码的函数接口

    Args:
        limit: 最大抓取数量

    Returns:
        热点话题列表
    """
    global _scraper_instance
    if _scraper_instance is None:
        _scraper_instance = DouyinScraper()
    return await _scraper_instance.scrape(limit)
