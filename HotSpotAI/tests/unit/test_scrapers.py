"""
爬虫基类和工厂单元测试
"""
import pytest
from scrapers.base import BaseScraper, HTTPScraper, PlaywrightScraper
from scrapers.factory import ScraperFactory, register_scraper


# 测试爬虫类
class MockScraper(BaseScraper):
    """测试用爬虫"""

    def get_platform_name(self) -> str:
        return "测试平台"

    async def scrape(self, limit: int = 10) -> list:
        self.log_start(limit)
        self.log_success(5)
        return [
            {"title": f"测试{i}", "link": f"https://test.com/{i}", "source": "测试平台"}
            for i in range(5)
        ]


class TestBaseScraper:
    """测试爬虫基类"""

    def test_format_result(self):
        """测试结果格式化"""
        scraper = MockScraper()
        result = scraper.format_result("Test Title", "https://test.com")
        assert result["title"] == "Test Title"
        assert result["link"] == "https://test.com"
        assert result["source"] == "测试平台"

    def test_get_platform_name(self):
        """测试获取平台名称"""
        scraper = MockScraper()
        assert scraper.get_platform_name() == "测试平台"

    def test_log_methods(self):
        """测试日志方法"""
        scraper = MockScraper()
        # 这些方法不应该抛出异常
        scraper.log_start(10)
        scraper.log_success(5)
        scraper.log_error("Test error")
        scraper.log_warning("Test warning")


class TestScraperFactory:
    """测试爬虫工厂"""

    def setup_method(self):
        """清理已注册的爬虫"""
        ScraperFactory._scrapers.clear()

    def test_register_scraper(self):
        """测试注册爬虫"""
        @register_scraper("test")
        class TestScraper(BaseScraper):
            def get_platform_name(self) -> str:
                return "Test"

            async def scrape(self, limit: int = 10) -> list:
                return []

        assert "test" in ScraperFactory._scrapers

    def test_create_scraper(self):
        """测试创建爬虫实例"""
        @register_scraper("test")
        class TestScraper(BaseScraper):
            def get_platform_name(self) -> str:
                return "Test"

            async def scrape(self, limit: int = 10) -> list:
                return []

        scraper = ScraperFactory.create("test")
        assert scraper is not None
        assert isinstance(scraper, TestScraper)

    def test_create_nonexistent_scraper(self):
        """测试创建不存在的爬虫"""
        scraper = ScraperFactory.create("nonexistent")
        assert scraper is None

    def test_create_all_scrapers(self):
        """测试创建所有爬虫"""
        @register_scraper("test1")
        class TestScraper1(BaseScraper):
            def get_platform_name(self) -> str:
                return "Test1"

            async def scrape(self, limit: int = 10) -> list:
                return []

        @register_scraper("test2")
        class TestScraper2(BaseScraper):
            def get_platform_name(self) -> str:
                return "Test2"

            async def scrape(self, limit: int = 10) -> list:
                return []

        scrapers = ScraperFactory.create_all()
        assert len(scrapers) == 2
        assert "test1" in scrapers
        assert "test2" in scrapers

    def test_get_available_platforms(self):
        """测试获取可用平台列表"""
        @register_scraper("platform1")
        class Platform1(BaseScraper):
            def get_platform_name(self) -> str:
                return "Platform1"

            async def scrape(self, limit: int = 10) -> list:
                return []

        platforms = ScraperFactory.get_available_platforms()
        assert "platform1" in platforms

    def test_is_platform_available(self):
        """测试检查平台是否可用"""
        @register_scraper("available")
        class AvailableScraper(BaseScraper):
            def get_platform_name(self) -> str:
                return "Available"

            async def scrape(self, limit: int = 10) -> list:
                return []

        assert ScraperFactory.is_platform_available("available") is True
        assert ScraperFactory.is_platform_available("not_available") is False
