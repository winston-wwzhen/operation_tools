"""
统一响应格式模块

提供标准的 API 响应格式，确保所有 API 端点返回一致的数据结构。
"""
from typing import Any, Optional, Generic, TypeVar
from pydantic import BaseModel, Field
from datetime import datetime

# 泛型类型变量
T = TypeVar('T')


class ApiResponse(BaseModel, Generic[T]):
    """
    统一 API 响应格式

    Attributes:
        success: 请求是否成功
        message: 响应消息
        data: 响应数据（泛型）
        timestamp: 响应时间戳
    """
    success: bool = True
    message: str = "操作成功"
    data: Optional[T] = None
    timestamp: datetime = Field(default_factory=datetime.now)

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class PageResponse(BaseModel, Generic[T]):
    """
    分页响应格式

    Attributes:
        items: 数据列表
        total: 总数量
        page: 当前页码
        page_size: 每页数量
        pages: 总页数
    """
    items: list[T] = Field(default_factory=list)
    total: int = 0
    page: int = 1
    page_size: int = 10
    pages: int = 0

    @classmethod
    def create(cls, items: list, total: int, page: int = 1, page_size: int = 10):
        """创建分页响应"""
        pages = (total + page_size - 1) // page_size if page_size > 0 else 0
        return cls(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            pages=pages
        )


def success_response(data: Any = None, message: str = "操作成功") -> dict:
    """
    创建成功响应

    Args:
        data: 响应数据
        message: 响应消息

    Returns:
        标准响应字典
    """
    return ApiResponse(success=True, message=message, data=data).dict()


def error_response(message: str = "操作失败", data: Any = None) -> dict:
    """
    创建错误响应

    Args:
        message: 错误消息
        data: 错误数据

    Returns:
        标准错误响应字典
    """
    return ApiResponse(success=False, message=message, data=data).dict()
