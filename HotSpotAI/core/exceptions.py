"""
统一异常处理模块

提供自定义异常类和全局异常处理器。
"""
from typing import Any, Optional
from fastapi import HTTPException, Request, status
from fastapi.responses import JSONResponse
from core.responses import ApiResponse


class AppException(Exception):
    """
    应用基础异常类

    所有自定义异常的基类。
    """

    def __init__(
        self,
        message: str,
        code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        data: Any = None
    ):
        self.message = message
        self.code = code
        self.data = data
        super().__init__(message)


class NotFoundException(AppException):
    """资源未找到异常"""

    def __init__(self, message: str = "资源不存在", data: Any = None):
        super().__init__(message, status.HTTP_404_NOT_FOUND, data)


class BadRequestException(AppException):
    """错误请求异常"""

    def __init__(self, message: str = "请求参数错误", data: Any = None):
        super().__init__(message, status.HTTP_400_BAD_REQUEST, data)


class UnauthorizedException(AppException):
    """未授权异常"""

    def __init__(self, message: str = "未授权访问", data: Any = None):
        super().__init__(message, status.HTTP_401_UNAUTHORIZED, data)


class ForbiddenException(AppException):
    """禁止访问异常"""

    def __init__(self, message: str = "无权访问", data: Any = None):
        super().__init__(message, status.HTTP_403_FORBIDDEN, data)


class ConflictException(AppException):
    """冲突异常"""

    def __init__(self, message: str = "资源冲突", data: Any = None):
        super().__init__(message, status.HTTP_409_CONFLICT, data)


class ValidationException(AppException):
    """验证失败异常"""

    def __init__(self, message: str = "数据验证失败", data: Any = None):
        super().__init__(message, status.HTTP_422_UNPROCESSABLE_ENTITY, data)


class InternalServerException(AppException):
    """服务器内部错误异常"""

    def __init__(self, message: str = "服务器内部错误", data: Any = None):
        super().__init__(message, status.HTTP_500_INTERNAL_SERVER_ERROR, data)


async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
    """
    自定义异常处理器

    Args:
        request: 请求对象
        exc: 异常对象

    Returns:
        JSON 响应
    """
    return JSONResponse(
        status_code=exc.code,
        content=ApiResponse(
            success=False,
            message=exc.message,
            data=exc.data
        ).dict()
    )


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """
    HTTP 异常处理器

    Args:
        request: 请求对象
        exc: HTTP 异常对象

    Returns:
        JSON 响应
    """
    from json import loads

    response = ApiResponse(
        success=False,
        message=exc.detail,
        data=None
    )

    # Use .json() to properly serialize datetime, then parse back to dict
    return JSONResponse(
        status_code=exc.status_code,
        content=loads(response.json())
    )


async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    通用异常处理器

    Args:
        request: 请求对象
        exc: 异常对象

    Returns:
        JSON 响应
    """
    from core.config import add_log
    import traceback
    from json import loads

    # 记录错误日志
    add_log("ERROR", f"未处理的异常: {str(exc)}")
    add_log("ERROR", f"堆栈跟踪:\n{traceback.format_exc()}")

    response = ApiResponse(
        success=False,
        message="服务器内部错误",
        data=str(exc) if add_log else None
    )

    # Use .json() to properly serialize datetime, then parse back to dict
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=loads(response.json())
    )
