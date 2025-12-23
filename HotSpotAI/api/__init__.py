"""
AutoMediaBot API 路由模块
"""
from fastapi import APIRouter
from .status import router as status_router
from .content import router as content_router
from .history import router as history_router

api_router = APIRouter(prefix="/api", tags=["api"])

# 注册子路由
api_router.include_router(status_router)
api_router.include_router(content_router)
api_router.include_router(history_router)

__all__ = ["api_router"]
