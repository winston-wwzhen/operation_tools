"""
历史数据查询 API
"""
from fastapi import APIRouter, Query
from typing import Optional
from pydantic import BaseModel

from core.database import get_historical_topics, get_distinct_dates, get_stats

router = APIRouter(tags=["history"])


class HistoryResponse(BaseModel):
    """历史数据响应模型"""
    topics: list
    total: int
    offset: int
    limit: int


class StatsResponse(BaseModel):
    """统计信息响应模型"""
    total_topics: int
    by_source: dict
    latest_update: Optional[str]


@router.get("/history/topics", response_model=HistoryResponse, summary="获取历史热点数据")
async def get_history(
    start_date: Optional[str] = Query(None, description="起始日期 (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="结束日期 (YYYY-MM-DD)"),
    source: Optional[str] = Query(None, description="数据源筛选 (weibo/baidu/zhihu/douyin/xiaohongshu/toutiao)"),
    offset: int = Query(0, ge=0, description="偏移量（用于分页）"),
    limit: int = Query(50, ge=1, le=200, description="每页数量")
):
    """
    获取历史热点数据，支持按日期范围和数据源筛选

    **参数说明：**
    - start_date: 起始日期，如 "2024-01-01"
    - end_date: 结束日期，如 "2024-01-31"
    - source: 数据源，可选值：weibo, baidu, zhihu, douyin, xiaohongshu, toutiao
    - offset: 分页偏移量，默认 0
    - limit: 每页数量，默认 50，最大 200

    **返回示例：**
    ```json
    {
        "topics": [
            {
                "id": 1,
                "title": "热点标题",
                "link": "https://...",
                "source": "weibo",
                "heat": 85,
                "tags": ["标签1", "标签2"],
                "comment": "AI点评",
                "created_at": "2024-01-15 10:30:00"
            }
        ],
        "total": 150,
        "offset": 0,
        "limit": 50
    }
    ```
    """
    return await get_historical_topics(
        start_date=start_date,
        end_date=end_date,
        source=source,
        offset=offset,
        limit=limit
    )


@router.get("/history/dates", summary="获取所有可用日期")
async def get_dates():
    """
    获取数据库中所有有数据的日期列表

    **返回示例：**
    ```json
    {
        "dates": ["2024-01-15", "2024-01-14", "2024-01-13"]
    }
    ```
    """
    dates = await get_distinct_dates()
    return {"dates": dates}


@router.get("/history/stats", response_model=StatsResponse, summary="获取数据库统计信息")
async def get_history_stats():
    """
    获取数据库统计信息

    **返回示例：**
    ```json
    {
        "total_topics": 1500,
        "by_source": {
            "weibo": 300,
            "baidu": 250,
            "zhihu": 200
        },
        "latest_update": "2024-01-15 10:30:00"
    }
    ```
    """
    return await get_stats()
