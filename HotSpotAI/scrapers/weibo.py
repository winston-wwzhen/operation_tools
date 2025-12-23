"""
微博热搜爬虫模块
"""
from bs4 import BeautifulSoup
from .base import HTTPScraper
from .factory import register_scraper
from utils import http_retry


@register_scraper("weibo")
class WeiboScraper(HTTPScraper):
    """微博热搜爬虫"""

    def get_platform_name(self) -> str:
        return "微博"

    @http_retry
    async def fetch_page(self) -> str:
        """获取微博热搜页面（带重试）"""
        url = "https://s.weibo.com/top/summary"
        headers = {
            "Cookie": "SUB=_2AkMT_Mrzf8NxqwJRmP0SzGvhZYt1zw_EieKkjJ2ZJRMxHRl-yT9jqkUstRB6PaaZ-xT_r0Y0-v7_s-x_x_x_;",
            "Referer": "https://s.weibo.com/"
        }
        return await self.fetch(url, headers)

    async def scrape(self, limit: int = 10) -> list:
        """
        抓取微博热搜

        Args:
            limit: 最大抓取数量

        Returns:
            热点话题列表
        """
        self.log_start(limit)

        try:
            html = await self.fetch_page()
            soup = BeautifulSoup(html, 'html.parser')
            rows = soup.select('td.td-02 a')

            self.log_warning(f"原始条目数量: {len(rows)}")

            items = []
            for tr in rows:
                if len(items) >= limit:
                    break

                title = tr.get_text().strip()
                href = tr.get('href', '')

                # 过滤置顶广告和无效链接
                if "javascript" in href or not href.startswith("/"):
                    continue

                link = f"https://s.weibo.com{href}"
                items.append(self.format_result(title, link))

            self.log_success(len(items))
            return items

        except Exception as e:
            self.log_error(str(e))
            return []


# 兼容旧代码的函数式接口
_scraper_instance = None


async def scrape_weibo(limit: int = 10) -> list:
    """兼容旧代码的函数接口"""
    global _scraper_instance
    if _scraper_instance is None:
        _scraper_instance = WeiboScraper()
    return await _scraper_instance.scrape(limit)
