"""
爬虫基类模块
定义所有爬虫的统一接口
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Optional
from core.config import add_log, get_config


class BaseScraper(ABC):
    """爬虫基类"""

    def __init__(self):
        self.platform_name = self.__class__.__name__
        self.timeout = get_config("request_timeout", 30)
        self.max_retries = get_config("max_retries", 3)

    @abstractmethod
    async def scrape(self, limit: int = 10) -> List[Dict]:
        """
        抓取热点话题

        Args:
            limit: 最大抓取数量

        Returns:
            热点话题列表，格式: [{"title": str, "link": str, "source": str}, ...]
        """
        pass

    async def scrape_by_keywords(self, keywords: List[str], limit: int = 10) -> List[Dict]:
        """
        根据关键词抓取热点话题（可选实现）

        Args:
            keywords: 关键词列表
            limit: 每个关键词最大抓取数量

        Returns:
            热点话题列表，格式: [{"title": str, "link": str, "source": str, "matched_keyword": str}, ...]
        """
        # 默认实现：调用 scrape 方法，然后过滤包含关键词的结果
        all_topics = await self.scrape(limit * len(keywords))
        filtered = []
        for topic in all_topics:
            for keyword in keywords:
                if keyword.lower() in topic.get('title', '').lower():
                    filtered.append({
                        **topic,
                        "matched_keyword": keyword
                    })
                    break
            if len(filtered) >= limit:
                break
        return filtered

    @abstractmethod
    def get_platform_name(self) -> str:
        """获取平台名称"""
        pass

    async def health_check(self) -> bool:
        """
        健康检查

        Returns:
            True 如果爬虫工作正常
        """
        try:
            result = await self.scrape(limit=1)
            return len(result) >= 0
        except Exception as e:
            add_log('error', f'{self.get_platform_name()} 健康检查失败: {e}')
            return False

    def format_result(self, title: str, link: str) -> Dict:
        """
        格式化抓取结果

        Args:
            title: 标题
            link: 链接

        Returns:
            格式化后的结果字典
        """
        return {
            "title": title,
            "link": link,
            "source": self.get_platform_name()
        }

    def log_start(self, limit: int):
        """记录开始日志"""
        add_log('info', f'[{self.get_platform_name()}] 开始抓取热搜数据，目标数量: {limit}')

    def log_success(self, count: int):
        """记录成功日志"""
        add_log('success', f'[{self.get_platform_name()}] 抓取完成，有效数据: {count} 条')

    def log_error(self, error: str):
        """记录错误日志"""
        add_log('error', f'[{self.get_platform_name()}] 抓取失败: {error}')

    def log_warning(self, message: str):
        """记录警告日志"""
        add_log('warning', f'[{self.get_platform_name()}] {message}')


class HTTPScraper(BaseScraper):
    """HTTP 爬虫基类 (适用于使用 httpx 的爬虫)"""

    async def fetch(self, url: str, headers: Optional[Dict] = None) -> str:
        """
        获取页面内容（子类可重写）

        Args:
            url: 请求 URL
            headers: 请求头

        Returns:
            页面 HTML 内容
        """
        import httpx

        default_headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        if headers:
            default_headers.update(headers)

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(url, headers=default_headers)
            response.raise_for_status()
            return response.text


class PlaywrightScraper(BaseScraper):
    """Playwright 爬虫基类 (适用于需要渲染 JS 的爬虫)"""

    def get_headless(self) -> bool:
        """获取浏览器无头模式配置"""
        return get_config("playwright_headless", True)

    async def fetch(self, url: str) -> str:
        """
        使用 Playwright 获取页面内容

        Args:
            url: 请求 URL

        Returns:
            页面 HTML 内容
        """
        from playwright.async_api import async_playwright
        from core.config import get_config

        headless = get_config("playwright_headless", True)
        timeout = get_config("playwright_timeout", 30000)

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=headless)
            page = await browser.new_page()
            await page.goto(url, timeout=timeout)
            content = await page.content()
            await browser.close()

        return content
