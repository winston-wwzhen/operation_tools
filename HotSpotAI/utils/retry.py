"""
重试机制工具模块
使用 tenacity 实现指数退避重试策略
"""
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    before_sleep_log,
)
import logging
from typing import Callable, Any, Type
from functools import wraps

logger = logging.getLogger(__name__)


def with_retry(
    max_attempts: int = 3,
    min_wait: float = 1.0,
    max_wait: float = 10.0,
    exception_types: tuple = (Exception,),
):
    """
    通用重试装饰器

    Args:
        max_attempts: 最大重试次数
        min_wait: 最小等待时间(秒)
        max_wait: 最大等待时间(秒)
        exception_types: 需要重试的异常类型

    Returns:
        装饰器函数
    """

    def decorator(func: Callable) -> Callable:
        @retry(
            stop=stop_after_attempt(max_attempts),
            wait=wait_exponential(multiplier=1, min=min_wait, max=max_wait),
            retry=retry_if_exception_type(exception_types),
            before_sleep=before_sleep_log(logger, logging.WARNING),
            reraise=True,  # 重试次数用尽后重新抛出异常
        )
        @wraps(func)
        async def async_wrapper(*args, **kwargs) -> Any:
            return await func(*args, **kwargs)

        @wraps(func)
        def sync_wrapper(*args, **kwargs) -> Any:
            return func(*args, **kwargs)

        # 根据函数类型返回对应的包装器
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator


class RetryPolicy:
    """重试策略配置类"""

    # 网络请求重试策略
    HTTP_RETRY = {
        "max_attempts": 3,
        "min_wait": 1.0,
        "max_wait": 5.0,
        "exception_types": (
            ConnectionError,
            TimeoutError,
            OSError,
        ),
    }

    # Playwright 浏览器操作重试策略
    BROWSER_RETRY = {
        "max_attempts": 2,
        "min_wait": 2.0,
        "max_wait": 5.0,
        "exception_types": (
            TimeoutError,
            Exception,  # Playwright 异常类型较多
        ),
    }

    # LLM API 调用重试策略
    LLM_RETRY = {
        "max_attempts": 3,
        "min_wait": 2.0,
        "max_wait": 10.0,
        "exception_types": (
            ConnectionError,
            TimeoutError,
        ),
    }


def http_retry(func: Callable) -> Callable:
    """HTTP 请求重试装饰器"""
    return with_retry(**RetryPolicy.HTTP_RETRY)(func)


def browser_retry(func: Callable) -> Callable:
    """浏览器操作重试装饰器"""
    return with_retry(**RetryPolicy.BROWSER_RETRY)(func)


def llm_retry(func: Callable) -> Callable:
    """LLM API 调用重试装饰器"""
    return with_retry(**RetryPolicy.LLM_RETRY)(func)


# 使用示例
if __name__ == "__main__":
    import httpx

    @http_retry
    async def fetch_url(url: str):
        async with httpx.AsyncClient() as client:
            response = await client.get(url, timeout=5.0)
            response.raise_for_status()
            return response.text

    # 测试
    import asyncio

    async def test():
        try:
            result = await fetch_url("https://httpbin.org/get")
            print("Success:", len(result))
        except Exception as e:
            print("Failed after retries:", e)

    # asyncio.run(test())
