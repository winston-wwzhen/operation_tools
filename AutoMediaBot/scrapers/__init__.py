from .weibo import scrape_weibo
from .baidu import scrape_baidu
from .zhihu import scrape_zhihu_playwright
from .douyin import scrape_douyin_playwright

# 导出所有模块，方便外部调用
__all__ = [
    'scrape_weibo',
    'scrape_baidu',
    'scrape_zhihu_playwright',
    'scrape_douyin_playwright'
]