"""
Prompt 模块单元测试
"""
import pytest
from core.prompts import (
    get_platform_prompt,
    get_analysis_prompt,
    get_analysis_retry_prompt,
    list_supported_platforms,
    get_platform_temperature,
    get_platform_description,
    PLATFORM_PROMPTS
)


class TestPlatformPrompts:
    """测试平台 Prompt"""

    def test_get_platform_prompt_existing(self):
        """测试获取已存在的平台配置"""
        prompt = get_platform_prompt("wechat")
        assert prompt.name == "微信公众号"
        assert prompt.temperature == 0.8

    def test_get_platform_prompt_default(self):
        """测试获取默认平台配置"""
        prompt = get_platform_prompt("unknown")
        assert prompt.name == "通用"

    def test_all_platforms_have_required_fields(self):
        """测试所有平台都有必需的字段"""
        for platform, config in PLATFORM_PROMPTS.items():
            assert config.name
            assert config.system_prompt
            assert config.temperature >= 0
            assert config.temperature <= 1

    def test_list_supported_platforms(self):
        """测试列出支持的平台"""
        platforms = list_supported_platforms()
        assert isinstance(platforms, dict)
        assert "wechat" in platforms
        assert "xiaohongshu" in platforms

    def test_get_platform_temperature(self):
        """测试获取平台 temperature"""
        wechat_temp = get_platform_temperature("wechat")
        assert wechat_temp == 0.8

        zhihu_temp = get_platform_temperature("zhihu")
        assert zhihu_temp < wechat_temp  # 知乎应该更理性

    def test_get_platform_description(self):
        """测试获取平台描述"""
        desc = get_platform_description("wechat")
        assert "HTML" in desc

        desc = get_platform_description("xiaohongshu")
        assert "Emoji" in desc


class TestAnalysisPrompts:
    """测试分析 Prompt"""

    def test_get_analysis_prompt(self):
        """测试获取分析 Prompt"""
        prompt = get_analysis_prompt()
        assert "全网舆情分析师" in prompt
        assert "去重" in prompt

    def test_get_analysis_retry_prompt(self):
        """测试获取重试 Prompt"""
        prompt = get_analysis_retry_prompt()
        assert "去重" in prompt
        assert "评分" in prompt
