"""
类型定义模块

提供项目中使用的通用类型定义。
"""
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from datetime import datetime
from enum import Enum


class SourceType(str, Enum):
    """数据源类型枚举"""
    WEIBO = "weibo"
    ZHIHU = "zhihu"
    DOUYIN = "douyin"
    XIAOHONGSHU = "xiaohongshu"
    TOUTIAO = "toutiao"
    BAIDU = "baidu"


class UserRole(str, Enum):
    """用户角色枚举"""
    USER = "user"
    ADMIN = "admin"


class TopicStatus(str, Enum):
    """话题状态枚举"""
    DRAFT = "draft"
    PUBLISHED = "published"
    ARCHIVED = "archived"


# === 请求/响应模型 ===

class HotTopic(BaseModel):
    """热点话题模型"""
    title: str
    link: str
    source: str
    heat: Optional[int] = None
    tags: Optional[List[str]] = None
    comment: Optional[str] = None
    category_id: Optional[int] = None
    matched_keyword: Optional[str] = None
    created_at: Optional[datetime] = None
    id: Optional[int] = None


class User(BaseModel):
    """用户模型"""
    id: int
    username: str
    is_admin: int
    created_at: Optional[datetime] = None


class Category(BaseModel):
    """分类模型"""
    id: int
    name: str
    slug: str
    description: Optional[str] = None
    icon: Optional[str] = None
    color: Optional[str] = None
    is_active: bool = True
    sort_order: int = 0
    keywords: Optional[List[str]] = []
    platforms: Optional[List[str]] = []


class Article(BaseModel):
    """文章模型"""
    id: int
    title: str
    content: str
    source: str
    source_url: Optional[str] = None
    user_id: int
    status: str = "draft"
    share_token: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class LoginRequest(BaseModel):
    """登录请求模型"""
    username: str
    password: str


class LoginResponse(BaseModel):
    """登录响应模型"""
    access_token: str
    token_type: str = "bearer"
    user: User


class GenerateRequest(BaseModel):
    """文案生成请求模型"""
    topics: List[str]
    platform: str = "wechat"
    custom_prompt: Optional[str] = None


# === 分页参数 ===

class PageParams(BaseModel):
    """分页参数"""
    page: int = 1
    page_size: int = 10

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.page_size

    @property
    def limit(self) -> int:
        return self.page_size
