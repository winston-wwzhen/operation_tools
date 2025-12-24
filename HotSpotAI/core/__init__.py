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
    run_full_pipeline,
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

# 新增：类型定义
from .types import (
    SourceType,
    UserRole,
    TopicStatus,
    HotTopic,
    User,
    Category,
    Article,
    LoginRequest,
    LoginResponse,
    PageParams,
)

# 新增：响应格式
from .responses import (
    ApiResponse,
    PageResponse,
    success_response,
    error_response,
)

# 新增：异常处理
from .exceptions import (
    AppException,
    NotFoundException,
    BadRequestException,
    UnauthorizedException,
    ForbiddenException,
    ConflictException,
    ValidationException,
    InternalServerException,
    app_exception_handler,
    http_exception_handler,
    general_exception_handler,
)

# 新增：服务层
from .services import (
    AuthService,
    CategoryService,
    get_auth_service,
    get_category_service,
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
    "run_full_pipeline",
    "update_scheduler",
    "start_scheduler",
    # Logger
    "get_logger",
    "setup_file_logging",
    "set_frontend_callback",
    "enable_frontend_logging",
    "disable_frontend_logging",
    "add_log",
    # Types
    "SourceType",
    "UserRole",
    "TopicStatus",
    "HotTopic",
    "User",
    "Category",
    "Article",
    "LoginRequest",
    "LoginResponse",
    "PageParams",
    # Responses
    "ApiResponse",
    "PageResponse",
    "success_response",
    "error_response",
    # Exceptions
    "AppException",
    "NotFoundException",
    "BadRequestException",
    "UnauthorizedException",
    "ForbiddenException",
    "ConflictException",
    "ValidationException",
    "InternalServerException",
    "app_exception_handler",
    "http_exception_handler",
    "general_exception_handler",
    # Services
    "AuthService",
    "CategoryService",
    "get_auth_service",
    "get_category_service",
]
