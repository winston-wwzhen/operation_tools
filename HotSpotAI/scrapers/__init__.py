"""
爬虫模块
支持函数式接口和工厂模式
"""
# 函数式接口（兼容旧代码）
from .baidu import scrape_baidu
from .douyin import scrape_douyin_playwright
from .toutiao import scrape_toutiao
from .weibo import scrape_weibo
from .xiaohongshu import scrape_xiaohongshu
from .zhihu import scrape_zhihu_playwright

# 工厂模式（新代码）
from .factory import ScraperFactory, register_scraper
from .base import BaseScraper, HTTPScraper, PlaywrightScraper

__all__ = [
    # 函数式接口
    'scrape_weibo',
    'scrape_baidu',
    'scrape_zhihu_playwright',
    'scrape_douyin_playwright',
    'scrape_xiaohongshu',
    'scrape_toutiao',
    # 工厂模式
    'ScraperFactory',
    'register_scraper',
    'BaseScraper',
    'HTTPScraper',
    'PlaywrightScraper',
]
