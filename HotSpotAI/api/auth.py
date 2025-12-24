"""
用户认证 API 路由
提供注册、登录、登出等功能
"""
from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel

from core.auth import (
    create_access_token, decode_access_token,
    get_password_hash, verify_password, get_current_user,
    Token, UserCreate, UserLogin, UserResponse
)
from core.users import create_user, get_user_by_username, get_user_by_id, get_user_by_email
from core.config import add_log

router = APIRouter(tags=["auth"], prefix="/auth")


class AuthResponse(BaseModel):
    """认证响应模型"""
    access_token: str
    token_type: str
    user: UserResponse


@router.post("/register", response_model=AuthResponse, summary="用户注册")
async def register(user_data: UserCreate):
    """
    用户注册

    - **username**: 用户名（唯一，3-20字符）
    - **email**: 邮箱（唯一）
    - **password**: 密码（至少6字符）
    """
    # 检查用户名是否已存在
    existing = await get_user_by_username(user_data.username)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="用户名已存在"
        )

    # 检查邮箱是否已存在
    existing_email = await get_user_by_email(user_data.email)
    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="邮箱已被注册"
        )

    # 创建用户
    password_hash = get_password_hash(user_data.password)
    user_id = await create_user(user_data.username, user_data.email, password_hash)

    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="创建用户失败"
        )

    # 获取用户数据
    user = await get_user_by_id(user_id)

    # 生成 token
    access_token = create_access_token(
        data={"sub": user["username"], "user_id": user["id"]}
    )

    add_log('success', f'新用户注册: {user_data.username}')

    return AuthResponse(
        access_token=access_token,
        token_type="bearer",
        user=UserResponse(
            id=user["id"],
            username=user["username"],
            email=user["email"],
            is_admin=bool(user.get("is_admin", 0)),
            created_at=user["created_at"]
        )
    )


@router.post("/login", response_model=AuthResponse, summary="用户登录")
async def login(login_data: UserLogin):
    """
    用户登录

    - **username**: 用户名
    - **password**: 密码
    """
    user = await get_user_by_username(login_data.username)

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误"
        )

    if not verify_password(login_data.password, user["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误"
        )

    access_token = create_access_token(
        data={"sub": user["username"], "user_id": user["id"]}
    )

    return AuthResponse(
        access_token=access_token,
        token_type="bearer",
        user=UserResponse(
            id=user["id"],
            username=user["username"],
            email=user["email"],
            is_admin=bool(user.get("is_admin", 0)),
            created_at=user["created_at"]
        )
    )


@router.get("/me", response_model=UserResponse, summary="获取当前用户信息")
async def get_me(current_user: dict = Depends(get_current_user)):
    """
    获取当前登录用户的信息
    """
    return UserResponse(**current_user)


@router.post("/logout", summary="用户登出")
async def logout():
    """
    用户登出（客户端应删除 token）
    """
    return {"message": "登出成功"}
