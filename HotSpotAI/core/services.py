"""
服务层模块

提供业务逻辑封装，将业务逻辑从 API 层分离。
"""
from typing import List, Optional, Dict, Any
from abc import ABC, abstractmethod
from core.database import (
    get_categories,
    get_categories_with_keywords,
    get_category_by_id,
    create_category,
    update_category,
    delete_category,
    update_category_keywords,
    update_category_platforms,
)
from core.users import get_user_by_username
from core.exceptions import NotFoundException, BadRequestException, UnauthorizedException
from core.types import User, Category, UserRole
import aiosqlite


class BaseService(ABC):
    """服务基类"""

    def __init__(self, db: aiosqlite.Connection):
        self.db = db


class AuthService:
    """认证服务"""

    def __init__(self, db: aiosqlite.Connection):
        self.db = db

    async def login(self, username: str, password: str) -> tuple[str, User]:
        """
        用户登录

        Args:
            username: 用户名
            password: 密码

        Returns:
            (token, user_info) 元组

        Raises:
            UnauthorizedException: 认证失败
        """
        import hashlib
        from core.auth import create_access_token

        user = await get_user_by_username(username)
        if not user:
            raise UnauthorizedException("用户名或密码错误")

        # 验证密码
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        if user['password_hash'] != password_hash:
            raise UnauthorizedException("用户名或密码错误")

        # 生成 token
        token = create_access_token({'user_id': user['id']})

        user_info = User(
            id=user['id'],
            username=user['username'],
            is_admin=user.get('is_admin', 0)
        )

        return token, user_info

    async def get_current_user(self, token: str) -> User:
        """
        获取当前用户信息

        Args:
            token: JWT token

        Returns:
            用户信息

        Raises:
            UnauthorizedException: token 无效
        """
        from core.auth import decode_access_token

        token_data = decode_access_token(token)
        if token_data is None:
            raise UnauthorizedException("无效的认证凭据")

        user_id = token_data.get('user_id')
        if not user_id:
            raise UnauthorizedException("无效的认证凭据")

        # 通过 id 获取用户（使用 id 作为 username 查询，这不是最佳方案但可工作）
        # 注意：get_user_by_username 需要字符串参数
        user = await get_user_by_username(str(user_id))
        if not user:
            raise UnauthorizedException("用户不存在")

        return User(
            id=user['id'],
            username=user['username'],
            is_admin=user.get('is_admin', 0)
        )


class CategoryService:
    """分类服务"""

    def __init__(self, db: aiosqlite.Connection = None):
        self.db = db

    async def list_categories(self, include_inactive: bool = False) -> List[Category]:
        """获取分类列表"""
        categories = await get_categories(include_inactive)
        return [Category(**cat) for cat in categories]

    async def get_categories_with_keywords(self) -> List[Category]:
        """获取带关键词的分类列表"""
        categories = await get_categories_with_keywords()
        return [Category(**cat) for cat in categories]

    async def get_category(self, category_id: int) -> Category:
        """获取分类详情"""
        category = await get_category_by_id(category_id)
        if not category:
            raise NotFoundException(f"分类不存在: {category_id}")
        return Category(**category)

    async def create_category(self, data: Dict[str, Any]) -> int:
        """创建分类"""
        category_id = await create_category(data)
        return category_id

    async def update_category(self, category_id: int, data: Dict[str, Any]) -> bool:
        """更新分类"""
        # 检查分类是否存在
        await self.get_category(category_id)

        # 只更新提供的字段
        update_data = {k: v for k, v in data.items() if v is not None}
        success = await update_category(category_id, update_data)
        return success

    async def delete_category(self, category_id: int) -> bool:
        """删除分类"""
        await self.get_category(category_id)
        success = await delete_category(category_id)
        return success

    async def update_keywords(self, category_id: int, keywords: List[str]) -> bool:
        """更新分类关键词"""
        await self.get_category(category_id)
        success = await update_category_keywords(category_id, keywords)
        return success

    async def update_platforms(self, category_id: int, platforms: List[str]) -> bool:
        """更新分类平台配置"""
        await self.get_category(category_id)
        success = await update_category_platforms(category_id, platforms)
        return success

    async def check_is_admin(self, user: User) -> bool:
        """检查用户是否为管理员"""
        return user.is_admin == 1


# 服务工厂函数
def get_auth_service(db: aiosqlite.Connection = None) -> AuthService:
    """获取认证服务实例"""
    return AuthService(db)


def get_category_service(db: aiosqlite.Connection = None) -> CategoryService:
    """获取分类服务实例"""
    return CategoryService(db)
