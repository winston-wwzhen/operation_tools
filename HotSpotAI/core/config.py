"""
核心配置与状态管理模块
合并了环境变量配置和运行时状态管理
"""
import os
from typing import Any, Dict, Optional
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# 日志函数从 logger 模块导入（避免循环导入）
def add_log(level: str, message: str):
    """临时占位函数，实际从 logger 模块导入"""
    from .logger import add_log as _add_log
    return _add_log(level, message)


# ============ 环境变量配置类 ============

class Settings(BaseSettings):
    """应用配置类（从环境变量读取）"""

    # LLM 配置
    llm_api_key: str = Field(default="", description="LLM API 密钥")
    llm_base_url: str = Field(
        default="https://open.bigmodel.cn/api/paas/v4/",
        description="LLM API 基础 URL"
    )
    llm_model: str = Field(default="glm-4", description="LLM 模型名称")
    llm_timeout: int = Field(default=600, description="LLM 请求超时时间(秒)")  # 增加到10分钟

    # 数据库配置
    database_url: str = Field(default="sqlite:///./data.db", description="数据库连接 URL")
    db_keep_days: int = Field(default=7, description="数据库保留天数")

    # 爬虫配置
    request_timeout: int = Field(default=30, description="HTTP 请求超时时间(秒)")
    max_retries: int = Field(default=3, description="最大重试次数")
    retry_delay: int = Field(default=2, description="重试延迟(秒)")
    topic_limit: int = Field(default=10, description="每个平台抓取话题数量")

    # 微信公众号配置
    wechat_app_id: str = Field(default="", description="微信 AppID")
    wechat_secret: str = Field(default="", description="微信 Secret")
    wechat_token_cache_time: int = Field(default=6600, description="AccessToken 缓存时间（秒），默认提前 5 分钟刷新")
    wechat_publish_interval: int = Field(default=1800, description="发布间隔限制（秒），默认 30 分钟")
    wechat_daily_limit: int = Field(default=1, description="每日最大发布次数，默认 1（订阅号限制）")
    wechat_enable_content_check: bool = Field(default=True, description="是否启用内容安全检测")

    # 定时任务配置
    schedule_cron: str = Field(default="0 */2 * * *", description="Cron 表达式")
    auto_run: bool = Field(default=False, description="是否自动运行定时任务")

    # 服务配置
    host: str = Field(default="0.0.0.0", description="服务监听地址")
    port: int = Field(default=3000, description="服务监听端口")
    debug: bool = Field(default=False, description="调试模式")
    log_level: str = Field(default="INFO", description="日志级别")

    # Playwright 配置
    playwright_headless: bool = Field(default=True, description="浏览器是否无头模式")
    playwright_timeout: int = Field(default=30000, description="浏览器操作超时(毫秒)")

    # CORS 配置
    cors_origins: str = Field(
        default="http://localhost:8080,http://127.0.0.1:8080,http://localhost:8081,http://127.0.0.1:8081,http://localhost:8082,http://127.0.0.1:8082,http://localhost:8083,http://127.0.0.1:8083",
        description="允许的 CORS 来源"
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_nested_delimiter="__",
        case_sensitive=False,
        extra="ignore"
    )

    @field_validator("cors_origins")
    @classmethod
    def parse_cors_origins(cls, v: str) -> list:
        """解析 CORS 来源字符串为列表"""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v

    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """验证日志级别"""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        v = v.upper()
        if v not in valid_levels:
            raise ValueError(f"log_level must be one of {valid_levels}")
        return v


# ============ 全局配置实例 ============

_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """获取全局配置实例（单例）"""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings


def reload_settings() -> Settings:
    """重新加载配置"""
    global _settings
    _settings = Settings()
    return _settings


# ============ 运行时状态管理 ============

LOG_LIMIT = 100

runtime_state = {
    "isRunning": False,
    "lastRunTime": None,
    "nextRunTime": None,
    "logs": [],
    "hot_topics": []
}


def get_config(key: str, default: Any = None) -> Any:
    """
    获取配置值（兼容旧代码）
    优先从环境变量读取，其次使用默认值

    Args:
        key: 配置键名，支持嵌套访问 (如 llm__api_key) 或 camelCase (如 llmApiKey)
        default: 默认值

    Returns:
        配置值
    """
    settings = get_settings()

    # 支持嵌套访问，如 llm__api_key -> settings.llm_api_key
    if "__" in key:
        parts = key.split("__")
        value = settings
        for part in parts:
            attr_name = part.lower()
            if hasattr(value, attr_name):
                value = getattr(value, attr_name)
            else:
                return default
        return value

    # 尝试直接获取属性（支持 camelCase 转换为 snake_case）
    # 先尝试直接作为属性名
    if hasattr(settings, key):
        return getattr(settings, key)

    # 将 camelCase 转换为 snake_case: llmApiKey -> llm_api_key
    import re
    attr_name = re.sub('([A-Z])', r'_\1', key).lower().lstrip('_')

    if hasattr(settings, attr_name):
        return getattr(settings, attr_name)

    return default


def get_app_config() -> Dict:
    """
    获取应用配置字典（供 API 返回）

    Returns:
        配置字典
    """
    settings = get_settings()
    return {
        "llmApiKey": settings.llm_api_key[:10] + "..." if settings.llm_api_key else "",
        "llmBaseUrl": settings.llm_base_url,
        "llmModel": settings.llm_model,
        "wechatAppId": settings.wechat_app_id,
        "wechatSecret": "***" if settings.wechat_secret else "",
        "topicLimit": settings.topic_limit,
        "scheduleCron": settings.schedule_cron,
        "autoRun": settings.auto_run,
    }
