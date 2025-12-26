"""
配置模块单元测试
"""
import pytest
from core.config import (
    Settings,
    get_settings,
    get_config,
    reload_settings,
    runtime_state,
)
from core.log_utils import clear_logs


class TestSettings:
    """测试配置类"""

    def test_get_settings_singleton(self):
        """测试单例模式"""
        settings1 = get_settings()
        settings2 = get_settings()
        assert settings1 is settings2

    def test_default_values(self):
        """测试默认配置值"""
        settings = get_settings()
        assert settings.host == "0.0.0.0"
        assert settings.port == 3000
        assert settings.topic_limit == 10

    def test_cors_origins_parsing(self):
        """测试 CORS 配置解析"""
        settings = get_settings()
        origins = settings.parse_cors_origins("http://localhost:8080,http://127.0.0.1:8080")
        assert "http://localhost:8080" in origins
        assert "http://127.0.0.1:8080" in origins


class TestGetConfig:
    """测试 get_config 函数"""

    def test_get_existing_config(self):
        """测试获取存在的配置"""
        host = get_config("host")
        assert host == "0.0.0.0"

    def test_get_nested_config(self):
        """测试获取嵌套配置"""
        api_key = get_config("llm__api_key")
        # 应该返回字符串（可能为空）
        assert isinstance(api_key, str)

    def test_get_config_with_default(self):
        """测试使用默认值"""
        value = get_config("nonexistent", "default_value")
        assert value == "default_value"

    def test_camelcase_to_snake_case(self):
        """测试 camelCase 转换为 snake_case"""
        # llmApiKey -> llm_api_key
        value = get_config("llmApiKey", "")
        assert isinstance(value, str)


class TestRuntimeState:
    """测试运行时状态"""

    def test_runtime_state_structure(self):
        """测试运行时状态结构"""
        assert "isRunning" in runtime_state
        assert "lastRunTime" in runtime_state
        assert "logs" in runtime_state
        assert "hot_topics" in runtime_state

    def test_runtime_state_logs_is_buffer(self):
        """测试 logs 是共享缓冲区"""
        from core.log_utils import get_log_buffer
        assert runtime_state["logs"] is get_log_buffer()


class TestReloadSettings:
    """测试重新加载配置"""

    def test_reload_settings(self):
        """测试重新加载配置"""
        original_settings = get_settings()
        new_settings = reload_settings()
        assert new_settings is not None
        # 应该创建新实例
        # 注意：由于环境变量没变，值可能相同
