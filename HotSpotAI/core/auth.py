"""
JWT 认证和密码管理模块
提供 token 生成、验证和密码哈希功能
"""
import secrets
from jose import jwt
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from passlib.context import CryptContext
from pydantic import BaseModel, EmailStr


# FastAPI security (imported here for get_current_user dependency)
try:
    from fastapi import HTTPException, Depends, status
    from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
    from core.users import get_user_by_id
    FASTAPI_AVAILABLE = True
except ImportError:
    FASTAPI_AVAILABLE = False
    HTTPBearer = None
    HTTPAuthorizationCredentials = None


# JWT 配置
SECRET_KEY = secrets.token_urlsafe(32)
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 7 天

# 密码哈希上下文
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class Token(BaseModel):
    """Token 响应模型"""
    access_token: str
    token_type: str


class TokenData(BaseModel):
    """Token 数据模型"""
    username: Optional[str] = None
    user_id: Optional[int] = None


class UserCreate(BaseModel):
    """用户注册模型"""
    username: str
    email: EmailStr
    password: str


class UserLogin(BaseModel):
    """用户登录模型"""
    username: str
    password: str


class UserResponse(BaseModel):
    """用户响应模型"""
    id: int
    username: str
    email: str
    is_admin: bool = False
    created_at: str


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    验证密码

    Args:
        plain_password: 明文密码
        hashed_password: 哈希密码

    Returns:
        密码是否匹配
    """
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """
    生成密码哈希

    Args:
        password: 明文密码

    Returns:
        哈希后的密码
    """
    return pwd_context.hash(password)


def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """
    创建 JWT 访问令牌

    Args:
        data: 要编码到 token 中的数据
        expires_delta: 过期时间增量

    Returns:
        JWT token 字符串
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def decode_access_token(token: str) -> Optional[TokenData]:
    """
    解码并验证 JWT token

    Args:
        token: JWT token 字符串

    Returns:
        TokenData 对象，验证失败返回 None
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        user_id: int = payload.get("user_id")
        return TokenData(username=username, user_id=user_id)
    except Exception:
        return None


# FastAPI security and dependency (only if FastAPI is available)
if FASTAPI_AVAILABLE:
    security = HTTPBearer()

    async def get_current_user(
        credentials: HTTPAuthorizationCredentials = Depends(security)
    ) -> dict:
        """
        获取当前登录用户的依赖注入

        Args:
            credentials: HTTP Bearer Token

        Returns:
            用户信息字典

        Raises:
            HTTPException: 认证失败时抛出 401 错误
        """
        token = credentials.credentials
        token_data = decode_access_token(token)

        if token_data is None or token_data.user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="无效的认证凭据",
                headers={"WWW-Authenticate": "Bearer"},
            )

        user = await get_user_by_id(token_data.user_id)
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="用户不存在",
            )

        return user
else:
    security = None

    async def get_current_user():
        raise NotImplementedError("FastAPI is not installed")


# Optional authentication - returns None if no token provided
if FASTAPI_AVAILABLE:
    from fastapi.security.utils import get_authorization_scheme_param

    async def get_current_user_optional(
        credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False))
    ) -> Optional[dict]:
        """
        可选的用户认证依赖

        如果提供了 token 则验证并返回用户信息，否则返回 None

        Returns:
            用户信息字典，未认证返回 None
        """
        if credentials is None:
            return None

        token = credentials.credentials
        token_data = decode_access_token(token)

        if token_data is None or token_data.user_id is None:
            return None

        user = await get_user_by_id(token_data.user_id)
        return user
else:
    async def get_current_user_optional():
        raise NotImplementedError("FastAPI is not installed")
