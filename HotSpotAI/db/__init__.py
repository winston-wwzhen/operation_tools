"""
数据库模块
提供数据库初始化、CRUD 操作和业务逻辑
"""
from .base import init_db
from .topics import (
    save_topics_to_db,
    load_latest_topics_from_db,
    get_topics_by_source,
    get_historical_topics,
    get_distinct_dates,
    clean_old_topics,
    get_stats,
    get_topics_by_category,
    save_hot_topics,
)
from .categories import (
    get_categories,
    get_category_by_id,
    get_categories_with_keywords,
    create_category,
    update_category,
    delete_category,
    update_category_keywords,
    update_category_platforms,
    get_category_platforms,
    init_default_categories,
)
from .raw_news import (
    save_raw_news_to_db,
    get_unanalyzed_news,
    update_news_analysis,
    get_top_scoring_news,
    get_raw_news_stats,
)
from .users import (
    create_user,
    get_user_by_id,
    get_user_by_email,
    get_user_by_username,
    update_user,
)

__all__ = [
    # 基础
    "init_db",
    # 热点话题
    "save_topics_to_db",
    "load_latest_topics_from_db",
    "get_topics_by_source",
    "get_historical_topics",
    "get_distinct_dates",
    "clean_old_topics",
    "get_stats",
    "get_topics_by_category",
    "save_hot_topics",
    # 分类
    "get_categories",
    "get_category_by_id",
    "get_categories_with_keywords",
    "create_category",
    "update_category",
    "delete_category",
    "update_category_keywords",
    "update_category_platforms",
    "get_category_platforms",
    "init_default_categories",
    # 原始新闻
    "save_raw_news_to_db",
    "get_unanalyzed_news",
    "update_news_analysis",
    "get_top_scoring_news",
    "get_raw_news_stats",
    # 用户
    "create_user",
    "get_user_by_id",
    "get_user_by_email",
    "get_user_by_username",
    "update_user",
]
