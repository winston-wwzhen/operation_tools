"""
日志工具模块单元测试
"""
import pytest
from core.log_utils import (
    add_log_to_buffer,
    get_logs,
    clear_logs,
    get_log_count,
    get_logs_by_level,
    get_recent_logs,
    LOG_LIMIT,
)


class TestLogBuffer:
    """测试日志缓冲区"""

    def setup_method(self):
        """每个测试前清空日志"""
        clear_logs()

    def test_add_log_to_buffer(self):
        """测试添加日志"""
        entry = add_log_to_buffer("info", "Test message")
        assert entry["level"] == "info"
        assert entry["message"] == "Test message"
        assert "id" in entry
        assert "time" in entry

    def test_log_limit(self):
        """测试日志数量限制"""
        # 添加超过限制的日志
        for i in range(LOG_LIMIT + 10):
            add_log_to_buffer("info", f"Message {i}")

        logs = get_logs()
        assert len(logs) <= LOG_LIMIT

    def test_get_logs_returns_copy(self):
        """测试 get_logs 返回副本"""
        add_log_to_buffer("info", "Test")
        logs1 = get_logs()
        logs2 = get_logs()

        # 修改副本不应影响原数据
        logs1.clear()
        assert len(get_logs()) > 0

    def test_clear_logs(self):
        """测试清空日志"""
        add_log_to_buffer("info", "Test 1")
        add_log_to_buffer("warning", "Test 2")
        assert get_log_count() == 2

        clear_logs()
        assert get_log_count() == 0

    def test_get_log_count(self):
        """测试获取日志数量"""
        assert get_log_count() == 0

        add_log_to_buffer("info", "Test 1")
        add_log_to_buffer("info", "Test 2")
        assert get_log_count() == 2

    def test_get_logs_by_level(self):
        """测试按级别筛选日志"""
        add_log_to_buffer("info", "Info message")
        add_log_to_buffer("error", "Error message")
        add_log_to_buffer("warning", "Warning message")

        info_logs = get_logs_by_level("info")
        error_logs = get_logs_by_level("error")

        assert len(info_logs) == 1
        assert len(error_logs) == 1
        assert info_logs[0]["message"] == "Info message"

    def test_get_recent_logs(self):
        """测试获取最近日志"""
        for i in range(20):
            add_log_to_buffer("info", f"Message {i}")

        recent = get_recent_logs(5)
        assert len(recent)) == 5
        # 应该是最新的 5 条
        assert recent[0]["message"] == "Message 19"

    def test_log_level_case_insensitive(self):
        """测试日志级别不区分大小写"""
        add_log_to_buffer("INFO", "Test")
        add_log_to_buffer("Error", "Test")

        logs = get_logs_by_level("info")
        assert len(logs) == 1

        logs = get_logs_by_level("error")
        assert len(logs) == 1
