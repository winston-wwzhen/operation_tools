"""
知乎热榜爬虫模块
"""
from typing import List
from playwright.async_api import async_playwright
from .base import PlaywrightScraper
from .factory import register_scraper
from core.config import add_log, get_config


@register_scraper("zhihu")
class ZhihuScraper(PlaywrightScraper):
    """知乎热榜爬虫"""

    def get_platform_name(self) -> str:
        return "知乎"

    async def scrape(self, limit: int = 10) -> list:
        """
        抓取知乎热榜
        策略：由于知乎原站(/hot)强制登录，改为抓取第三方聚合平台数据。
        1. 优先抓取 [今日热榜] 的知乎板块 (实时热榜)。
        2. 如果失败，兜底抓取 [知乎日报] (精选热点)。

        Args:
            limit: 最大抓取数量

        Returns:
            热点话题列表
        """
        self.log_start(limit)
        items = []

        try:
            async with async_playwright() as p:
                headless = get_config("playwright_headless", True)
                browser = await p.chromium.launch(headless=headless, args=['--disable-blink-features=AutomationControlled'])
                context = await browser.new_context(
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                    viewport={'width': 1920, 'height': 1080}
                )
                page = await context.new_page()

                # === 方案 A: 抓取今日热榜 (知乎热榜镜像) ===
                try:
                    target_url = "https://tophub.today/n/mproPpoq6O"
                    self.log_warning(f"(方案A) 正在从聚合平台加载知乎热榜: {target_url}")

                    await page.goto(target_url, timeout=30000, wait_until="domcontentloaded")

                    # 等待表格加载
                    try:
                        await page.wait_for_selector('table.table', timeout=5000)
                    except:
                        self.log_warning("聚合平台表格未加载，尝试方案B...")
                        raise Exception("Table not found")

                    # 解析数据
                    rows = await page.locator('table.table tbody tr').all()

                    for row in rows[:limit]:
                        # 标题通常在 td.al a 中
                        link_el = row.locator('td.al a')
                        if await link_el.count() > 0:
                            title = await link_el.text_content()
                            href = await link_el.get_attribute('href')

                            if title:
                                items.append({
                                    "title": title.strip(),
                                    "link": href if href.startswith('http') else f"https://tophub.today{href}",
                                    "source": self.get_platform_name()
                                })

                    if items:
                        self.log_success(f"从聚合平台成功获取 {len(items)} 条热榜数据")

                except Exception as e:
                    self.log_warning(f"方案A抓取失败 ({str(e)})，切换到方案B (知乎日报)...")
                    items = []  # 清空可能的不完整数据

                # === 方案 B: 抓取知乎日报 (兜底) ===
                if not items:
                    try:
                        daily_url = "https://daily.zhihu.com/"
                        self.log_warning(f"(方案B) 正在加载知乎日报: {daily_url}")
                        await page.goto(daily_url, timeout=30000, wait_until="domcontentloaded")

                        # 知乎日报结构: .box a.link-button
                        cards = await page.locator('.box a.link-button').all()

                        for card in cards[:limit]:
                            title_el = card.locator('span.title')
                            if await title_el.count() > 0:
                                title = await title_el.text_content()
                                href = await card.get_attribute('href')

                                if title:
                                    items.append({
                                        "title": title.strip(),
                                        "link": f"https://daily.zhihu.com{href}",
                                        "source": self.get_platform_name()
                                    })

                        if items:
                            self.log_success(f"从知乎日报兜底获取 {len(items)} 条数据")

                    except Exception as e:
                        self.log_error(f"方案B (知乎日报) 也失败了: {e}")

                await browser.close()

        except Exception as e:
            self.log_error(str(e))

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
