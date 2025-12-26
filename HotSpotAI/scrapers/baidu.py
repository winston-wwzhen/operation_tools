"""
百度热搜爬虫模块
使用 HTTPScraper 基类实现
"""
from bs4 import BeautifulSoup
from .base import HTTPScraper
from .factory import register_scraper
from utils import http_retry


@register_scraper("baidu")
class BaiduScraper(HTTPScraper):
    """百度热搜爬虫"""

    def get_platform_name(self) -> str:
        return "百度"

    @http_retry
    async def fetch_page(self) -> str:
        """获取百度热搜页面（带重试）"""
        url = "https://top.baidu.com/board?tab=realtime"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        return await self.fetch(url, headers)

    async def scrape(self, limit: int = 10) -> list:
        """抓取百度热搜"""
        self.log_start(limit)

        try:
            html = await self.fetch_page()
            soup = BeautifulSoup(html, 'html.parser')
            rows = soup.select('.c-single-text-ellipsis')

            self.log_warning(f"原始条目数量: {len(rows)}")

            items = []
            for t in rows:
                if len(items) >= limit:
                    break

                title = t.get_text().strip()
                if not title:
                    continue

                # 简单去重
                if any(x['title'] == title for x in items):
                    continue

                items.append(self.format_result(
                    title,
                    f"https://www.baidu.com/s?wd={title}"
                ))

            self.log_success(len(items))
            return items

        except Exception as e:
            self.log_error(str(e))
            return []


# 兼容旧代码的函数式接口
_scraper_instance = None


async def scrape_baidu(limit: int = 10) -> list:
    """
    兼容旧代码的函数接口

    Args:
        limit: 最大抓取数量

    Returns:
        热点话题列表
    """
    global _scraper_instance
    if _scraper_instance is None:
        _scraper_instance = BaiduScraper()
    return await _scraper_instance.scrape(limit)
