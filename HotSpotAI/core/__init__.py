"""
核心业务模块
包含配置、数据库、LLM、定时任务、日志等核心功能
"""
from .config import (
    Settings,
    get_settings,
    reload_settings,
    get_config,
    get_app_config,
    runtime_state,
    LOG_LIMIT,
)

from .database import (
    init_db,
    save_topics_to_db,
    load_latest_topics_from_db,
    get_topics_by_source,
    clean_old_topics,
    get_stats,
)

from .llm import (
    analyze_hot_topics,
    generate_article_for_topic,
)

from .scheduler import (
    scheduler,
    run_task_logic,
    update_scheduler,
    start_scheduler,
)

from .logger import (
    get_logger,
    setup_file_logging,
    set_frontend_callback,
    enable_frontend_logging,
    disable_frontend_logging,
    add_log,  # 兼容旧代码
)

__all__ = [
    # Config
    "Settings",
    "get_settings",
    "reload_settings",
    "get_config",
    "get_app_config",
    "runtime_state",
    "LOG_LIMIT",
    # Database
    "init_db",
    "save_topics_to_db",
    "load_latest_topics_from_db",
    "get_topics_by_source",
    "clean_old_topics",
    "get_stats",
    # LLM
    "analyze_hot_topics",
    "generate_article_for_topic",
    # Scheduler
    "scheduler",
    "run_task_logic",
    "update_scheduler",
    "start_scheduler",
    # Logger
    "get_logger",
    "setup_file_logging",
    "set_frontend_callback",
    "enable_frontend_logging",
    "disable_frontend_logging",
    "add_log",
]
