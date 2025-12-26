"""
pytest 配置文件
提供测试 fixtures 和通用配置
"""
import pytest
import asyncio
import tempfile
import os
from pathlib import Path


@pytest.fixture(scope="session")
def event_loop():
    """创建事件循环"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def test_db():
    """创建测试数据库"""
    # 使用临时数据库
    original_db_url = os.getenv("DATABASE_URL")
    test_db_file = tempfile.NamedTemporaryFile(delete=False, suffix=".db")
    test_db_path = test_db_file.name
    test_db_file.close()

    os.environ["DATABASE_URL"] = f"sqlite:///{test_db_path}"

    # 导入并初始化数据库
    from core.database import init_db
    await init_db()

    yield test_db_path

    # 清理
    os.unlink(test_db_path)
    if original_db_url:
        os.environ["DATABASE_URL"] = original_db_url


@pytest.fixture(autouse=True)
async def clear_logs_between_tests():
    """每个测试后清空日志"""
    from core.log_utils import clear_logs
    yield
    clear_logs()


@pytest.fixture
def mock_settings(monkeypatch):
    """模拟环境变量配置"""
    monkeypatch.setenv("LLM_API_KEY", "test_key_12345")
    monkeypatch.setenv("LLM_MODEL", "glm-4")
    monkeypatch.setenv("DATABASE_URL", "sqlite:///:memory:")
    monkeypatch.setenv("JWT_SECRET_KEY", "test_secret_key_for_testing")
    return None


@pytest.fixture
def sample_topics():
    """示例热点数据"""
    return [
        {
            "title": "测试热点1",
            "link": "https://example.com/1",
            "source": "测试平台",
            "heat": 100,
            "tags": ["科技", "AI"],
            "comment": "这是一个测试热点"
        },
        {
            "title": "测试热点2",
            "link": "https://example.com/2",
            "source": "测试平台",
            "heat": 90,
            "tags": ["娱乐", "明星"],
            "comment": "这也是一个测试热点"
        }
    ]


@pytest.fixture
def sample_user():
    """示例用户数据"""
    return {
        "id": 1,
        "username": "testuser",
        "email": "test@example.com",
        "is_admin": False,
        "created_at": "2024-01-01 00:00:00"
    }
