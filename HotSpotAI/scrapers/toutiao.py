"""
今日头条热榜爬虫模块
支持 API 拦截 (优先) + DOM 抓取 (兜底)
"""
import asyncio
from playwright.async_api import async_playwright
from .base import PlaywrightScraper
from .factory import register_scraper
from utils import browser_retry


@register_scraper("toutiao")
class ToutiaoScraper(PlaywrightScraper):
    """今日头条热榜爬虫"""

    def get_platform_name(self) -> str:
        return "今日头条"

    @browser_retry
    async def scrape(self, limit: int = 10) -> list:
        """抓取今日头条热榜"""
        self.log_start(limit)

        captured_data = {'list': []}

        # API 拦截回调
        async def handle_response(response):
            if "hot-event/hot-board" in response.url and response.status == 200:
                try:
                    json_body = await response.json()
                    data = json_body.get('data', [])
                    if isinstance(data, list):
                        captured_data['list'].extend(data)
                        self.log_warning(f'拦截 API 数据: {len(data)} 条')
                    elif isinstance(data, dict):
                        raw_list = data.get('data', [])
                        if raw_list:
                            captured_data['list'].extend(raw_list)
                            self.log_warning(f'拦截 API 数据 (嵌套): {len(raw_list)} 条')
                except Exception:
                    pass

        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(
                    headless=self.get_headless(),
                    args=['--disable-blink-features=AutomationControlled']
                )

                context = await browser.new_context(
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                    viewport={'width': 1920, 'height': 1080}
                )

                page = await context.new_page()
                page.on("response", handle_response)

                target_url = "https://www.toutiao.com/"
                self.log_warning(f'正在加载页面: {target_url}')

                await page.goto(target_url, timeout=30000, wait_until="networkidle")

                # 等待 API 响应
                for _ in range(10):
                    if captured_data['list']:
                        break
                    await asyncio.sleep(0.5)

                # 处理数据
                items = []
                if captured_data['list']:
                    seen = set()
                    for item in captured_data['list']:
                        if len(items) >= limit:
                            break

                        title = item.get('Title', '')
                        url = item.get('Url', '')

                        if title and title not in seen:
                            full_url = url if url.startswith('http') else f"https://www.toutiao.com{url}"
                            items.append(self.format_result(title, full_url))
                            seen.add(title)
                else:
                    # DOM 兜底
                    self.log_warning('未拦截到 API，尝试解析 DOM...')
                    elements = await page.locator('div[class*="hot-board"] a').all()

                    if not elements:
                        elements = await page.locator('a[href*="toutiao.com/trending"]').all()

                    self.log_warning(f'DOM 找到元素: {len(elements)} 个')

                    for el in elements[:limit * 2]:
                        if len(items) >= limit:
                            break

                        text = await el.text_content()
                        href = await el.get_attribute('href')

                        if text and len(text.strip()) > 4:
                            full_link = href if href.startswith('http') else f"https://www.toutiao.com{href}"
                            items.append(self.format_result(text.strip(), full_link))

                await browser.close()
                self.log_success(len(items))
                return items

        except Exception as e:
            self.log_error(str(e))
            return []


# 兼容旧代码的函数式接口
_scraper_instance = None


async def scrape_toutiao(limit: int = 10) -> list:
    """兼容旧代码的函数接口"""
    global _scraper_instance
    if _scraper_instance is None:
        _scraper_instance = ToutiaoScraper()
    return await _scraper_instance.scrape(limit)
