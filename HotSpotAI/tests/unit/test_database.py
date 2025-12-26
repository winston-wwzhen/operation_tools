"""
数据库模块单元测试
"""
import pytest
from core.database import (
    save_topics_to_db,
    load_latest_topics_from_db,
    get_topics_by_source,
    clean_old_topics,
    get_stats,
    get_historical_topics,
    get_distinct_dates
)


@pytest.mark.asyncio
async def test_save_topics(test_db, sample_topics):
    """测试保存热点数据"""
    count = await save_topics_to_db(sample_topics)
    assert count == len(sample_topics)


@pytest.mark.asyncio
async def test_save_empty_topics(test_db):
    """测试保存空列表"""
    count = await save_topics_to_db([])
    assert count == 0


@pytest.mark.asyncio
async def test_load_latest_topics(test_db, sample_topics):
    """测试加载最新热点"""
    await save_topics_to_db(sample_topics)

    topics = await load_latest_topics_from_db()
    assert len(topics) > 0
    assert topics[0]["title"] == sample_topics[0]["title"]


@pytest.mark.asyncio
async def test_get_topics_by_source(test_db, sample_topics):
    """测试按来源获取热点"""
    await save_topics_to_db(sample_topics)

    topics = await get_topics_by_source("测试平台")
    assert len(topics) > 0


@pytest.mark.asyncio
async def test_clean_old_topics(test_db, sample_topics):
    """测试清理旧数据"""
    await save_topics_to_db(sample_topics)

    deleted = await clean_old_topics(days=0)
    assert deleted >= 0


@pytest.mark.asyncio
async def test_get_stats(test_db, sample_topics):
    """测试获取统计信息"""
    await save_topics_to_db(sample_topics)

    stats = await get_stats()
    assert stats["total_topics"] > 0
    assert "测试平台" in stats["by_source"]


@pytest.mark.asyncio
async def test_get_historical_topics(test_db, sample_topics):
    """测试获取历史热点"""
    await save_topics_to_db(sample_topics)

    result = await get_historical_topics(limit=10)
    assert "topics" in result
    assert "total" in result
    assert result["total"] > 0


@pytest.mark.asyncio
async def test_get_distinct_dates(test_db, sample_topics):
    """测试获取可用日期列表"""
    await save_topics_to_db(sample_topics)

    dates = await get_distinct_dates()
    assert isinstance(dates, list)
