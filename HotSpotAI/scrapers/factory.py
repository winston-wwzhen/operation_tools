"""
爬虫工厂模块
使用工厂模式创建爬虫实例
"""
from typing import Dict, Type, Optional
from .base import BaseScraper


class ScraperFactory:
    """爬虫工厂类"""

    # 注册的爬虫类型
    _scrapers: Dict[str, Type[BaseScraper]] = {}

    @classmethod
    def register(cls, platform: str, scraper_class: Type[BaseScraper]):
        """
        注册爬虫

        Args:
            platform: 平台名称
            scraper_class: 爬虫类
        """
        cls._scrapers[platform.lower()] = scraper_class

    @classmethod
    def create(cls, platform: str) -> Optional[BaseScraper]:
        """
        创建爬虫实例

        Args:
            platform: 平台名称

        Returns:
            爬虫实例，如果平台不存在则返回 None
        """
        scraper_class = cls._scrapers.get(platform.lower())
        if scraper_class:
            return scraper_class()
        return None

    @classmethod
    def create_all(cls) -> Dict[str, BaseScraper]:
        """
        创建所有已注册的爬虫实例

        Returns:
            平台名称到爬虫实例的字典
        """
        return {
            platform: scraper_class()
            for platform, scraper_class in cls._scrapers.items()
        }

    @classmethod
    def get_available_platforms(cls) -> list:
        """获取所有可用平台列表"""
        return list(cls._scrapers.keys())

    @classmethod
    def is_platform_available(cls, platform: str) -> bool:
        """检查平台是否可用"""
        return platform.lower() in cls._scrapers


# 装饰器方式注册爬虫
def register_scraper(platform: str):
    """
    爬虫注册装饰器

    Usage:
        @register_scraper("weibo")
        class WeiboScraper(HTTPScraper):
            pass
    """
    def decorator(cls: Type[BaseScraper]):
        ScraperFactory.register(platform, cls)
        return cls
    return decorator
