"""
知乎热榜爬虫模块
使用聚合平台 (今日热榜) 抓取，知乎日报作为兜底方案
"""
from typing import List
from playwright.async_api import async_playwright
from .base import PlaywrightScraper
from .factory import register_scraper
from utils import browser_retry
from core.config import add_log


@register_scraper("zhihu")
class ZhihuScraper(PlaywrightScraper):
    """知乎热榜爬虫"""

    def get_platform_name(self) -> str:
        return "知乎"

    @browser_retry
    async def scrape(self, limit: int = 10) -> list:
        """
        抓取知乎热榜
        策略：由于知乎原站强制登录，改为抓取第三方聚合平台数据
        """
        self.log_start(limit)

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

                # 方案 A: 今日热榜 (知乎热榜镜像)
                items = await self._scrape_from_tophub(page, limit)

                # 方案 B: 知乎日报 (兜底)
                if not items:
                    self.log_warning('聚合方案失败，尝试知乎日报兜底...')
                    items = await self._scrape_from_daily(page, limit)

                await browser.close()
                self.log_success(len(items))
                return items

        except Exception as e:
            self.log_error(str(e))
            return []

    async def _scrape_from_tophub(self, page, limit: int) -> list:
        """从今日热榜抓取知乎数据"""
        target_url = "https://tophub.today/n/mproPpoq6O"
        self.log_warning(f'从聚合平台加载: {target_url}')

        await page.goto(target_url, timeout=30000, wait_until="domcontentloaded")

        try:
            await page.wait_for_selector('table.table', timeout=5000)
        except:
            self.log_warning('聚合平台表格未加载')
            return []

        rows = await page.locator('table.table tbody tr').all()
        items = []

        for row in rows[:limit]:
            link_el = row.locator('td.al a')
            if await link_el.count() > 0:
                title = await link_el.text_content()
                href = await link_el.get_attribute('href')

                if title:
                    full_link = href if href.startswith('http') else f"https://tophub.today{href}"
                    items.append(self.format_result(title.strip(), full_link))

        return items

    async def _scrape_from_daily(self, page, limit: int) -> list:
        """从知乎日报抓取数据（兜底方案）"""
        daily_url = "https://daily.zhihu.com/"
        self.log_warning(f'加载知乎日报: {daily_url}')

        await page.goto(daily_url, timeout=30000, wait_until="domcontentloaded")

        cards = await page.locator('.box a.link-button').all()
        items = []

        for card in cards[:limit]:
            title_el = card.locator('span.title')
            if await title_el.count() > 0:
                title = await title_el.text_content()
                href = await card.get_attribute('href')

                if title:
                    items.append(self.format_result(title.strip(), f"https://daily.zhihu.com{href}"))

        return items

    async def scrape_by_keywords(self, keywords: List[str], limit: int = 10) -> list:
        """
        根据关键词抓取知乎相关话题
        策略：由于知乎搜索需要登录/验证，改为从通用热榜中筛选包含关键词的内容

        Args:
            keywords: 关键词列表
            limit: 每个关键词最大抓取数量

        Returns:
            热点话题列表，包含 matched_keyword 字段
        """
        self.log_start(f"关键词搜索: {', '.join(keywords[:3])}...")

        # 先获取知乎热榜数据，然后筛选包含关键词的内容
        try:
            all_topics = await self.scrape(limit * 2)  # 获取更多数据用于筛选

            if not all_topics:
                self.log_warning("无法获取知乎热榜数据，关键词搜索返回空结果")
                return []

            # 筛选包含关键词的话题
            items = []
            for topic in all_topics:
                for keyword in keywords:
                    if keyword.lower() in topic.get('title', '').lower():
                        items.append({
                            **topic,
                            "matched_keyword": keyword
                        })
                        break

                if len(items) >= limit:
                    break

            self.log_success(f"从热榜中筛选到 {len(items)} 条相关内容")
            return items[:limit]

        except Exception as e:
            self.log_error(f"关键词搜索失败: {e}")
            return []


# 兼容旧代码的函数式接口
_scraper_instance = None


async def scrape_zhihu_playwright(limit: int = 10) -> list:
    """兼容旧代码的函数接口"""
    global _scraper_instance
    if _scraper_instance is None:
        _scraper_instance = ZhihuScraper()
    return await _scraper_instance.scrape(limit)
