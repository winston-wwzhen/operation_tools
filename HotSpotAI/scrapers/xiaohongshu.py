"""
小红书热点爬虫模块
使用聚合平台 (今日热榜) 抓取
"""
from .base import PlaywrightScraper
from .factory import register_scraper
from utils import browser_retry
from core.config import get_config


@register_scraper("xiaohongshu")
class XiaohongshuScraper(PlaywrightScraper):
    """小红书热点爬虫"""

    def get_platform_name(self) -> str:
        return "小红书"

    def get_headless(self) -> bool:
        return get_config("playwright_headless", True)

    @browser_retry
    async def scrape(self, limit: int = 10) -> list:
        """
        抓取小红书热点
        策略：小红书网页版反爬极严（强制登录/验证码），因此采用聚合平台抓取
        """
        self.log_start(limit)

        # 今日热榜上的小红书节点
        target_url = "https://tophub.today/n/rYqoXQ8vOa"

        try:
            from playwright.async_api import async_playwright

            async with async_playwright() as p:
                browser = await p.chromium.launch(
                    headless=self.get_headless(),
                    args=['--disable-blink-features=AutomationControlled']
                )

                context = await browser.new_context(
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                )

                page = await context.new_page()
                self.log_warning(f'正在连接聚合平台: {target_url}')

                await page.goto(target_url, timeout=30000, wait_until="domcontentloaded")

                # 等待表格加载
                try:
                    await page.wait_for_selector('table.table', timeout=8000)
                except:
                    self.log_warning('聚合平台表格加载超时')
                    await browser.close()
                    return []

                # 解析表格数据
                rows = await page.locator('table.table tbody tr').all()
                self.log_warning(f'获取到表格行数: {len(rows)}')

                items = []
                for row in rows:
                    if len(items) >= limit:
                        break

                    link_el = row.locator('td.al a')
                    if await link_el.count() > 0:
                        title = await link_el.text_content()
                        href = await link_el.get_attribute('href')

                        if title:
                            clean_title = title.strip()
                            if not clean_title:
                                continue

                            full_link = href if href.startswith('http') else f"https://tophub.today{href}"
                            items.append(self.format_result(clean_title, full_link))

                await browser.close()
                self.log_success(len(items))
                return items

        except Exception as e:
            self.log_error(str(e))
            return []


# 兼容旧代码的函数式接口
_scraper_instance = None


async def scrape_xiaohongshu(limit: int = 10) -> list:
    """兼容旧代码的函数接口"""
    global _scraper_instance
    if _scraper_instance is None:
        _scraper_instance = XiaohongshuScraper()
    return await _scraper_instance.scrape(limit)
