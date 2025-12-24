"""
微博热搜爬虫模块
"""
from bs4 import BeautifulSoup
from .base import HTTPScraper
from .factory import register_scraper
from utils import http_retry
from typing import List


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

    async def scrape_by_keywords(self, keywords: List[str], limit: int = 10) -> list:
        """
        根据关键词抓取微博相关话题
        策略：由于微博搜索需要登录，改为从通用热搜中筛选包含关键词的内容

        Args:
            keywords: 关键词列表
            limit: 每个关键词最大抓取数量

        Returns:
            热点话题列表，包含 matched_keyword 字段
        """
        self.log_start(f"关键词搜索: {', '.join(keywords[:3])}...")

        # 先获取微博热搜数据，然后筛选包含关键词的内容
        try:
            all_topics = await self.scrape(limit * 2)  # 获取更多数据用于筛选

            if not all_topics:
                self.log_warning("无法获取微博热搜数据，关键词搜索返回空结果")
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

            self.log_success(f"从热搜中筛选到 {len(items)} 条相关内容")
            return items[:limit]

        except Exception as e:
            self.log_error(f"关键词搜索失败: {e}")
            return []


# 兼容旧代码的函数式接口
_scraper_instance = None


async def scrape_weibo(limit: int = 10) -> list:
    """兼容旧代码的函数接口"""
    global _scraper_instance
    if _scraper_instance is None:
        _scraper_instance = WeiboScraper()
    return await _scraper_instance.scrape(limit)
