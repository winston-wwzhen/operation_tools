"""
用户数据库操作模块
提供用户注册、查询等数据库操作
"""
import aiosqlite
from typing import Optional, Dict, List
from core.config import add_log

DB_FILE = "data.db"


async def create_user(username: str, email: str, password_hash: str) -> Optional[int]:
    """
    创建新用户

    Args:
        username: 用户名
        email: 邮箱
        password_hash: 密码哈希

    Returns:
        用户 ID，失败返回 None
    """
    try:
        async with aiosqlite.connect(DB_FILE) as db:
            cursor = await db.execute('''
                INSERT INTO users (username, email, password_hash)
                VALUES (?, ?, ?)
            ''', (username, email, password_hash))
            await db.commit()
            return cursor.lastrowid
    except aiosqlite.IntegrityError as e:
        add_log('warning', f'用户创建失败（用户名或邮箱已存在）: {e}')
        return None
    except Exception as e:
        add_log('error', f'用户创建失败: {e}')
        return None


async def get_user_by_username(username: str) -> Optional[Dict]:
    """
    根据用户名获取用户

    Args:
        username: 用户名

    Returns:
        用户信息字典，不存在返回 None
    """
    try:
        async with aiosqlite.connect(DB_FILE) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                'SELECT * FROM users WHERE username = ?', (username,)
            ) as cursor:
                row = await cursor.fetchone()
                if row:
                    return dict(row)
        return None
    except Exception as e:
        add_log('error', f'获取用户失败: {e}')
        return None


async def get_user_by_email(email: str) -> Optional[Dict]:
    """
    根据邮箱获取用户

    Args:
        email: 邮箱

    Returns:
        用户信息字典，不存在返回 None
    """
    try:
        async with aiosqlite.connect(DB_FILE) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                'SELECT * FROM users WHERE email = ?', (email,)
            ) as cursor:
                row = await cursor.fetchone()
                if row:
                    return dict(row)
        return None
    except Exception as e:
        add_log('error', f'获取用户失败: {e}')
        return None


async def get_user_by_id(user_id: int) -> Optional[Dict]:
    """
    根据 ID 获取用户（不包含密码）

    Args:
        user_id: 用户 ID

    Returns:
        用户信息字典，不存在返回 None
    """
    try:
        async with aiosqlite.connect(DB_FILE) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                'SELECT id, username, email, is_admin, created_at FROM users WHERE id = ?', (user_id,)
            ) as cursor:
                row = await cursor.fetchone()
                if row:
                    return dict(row)
        return None
    except Exception as e:
        add_log('error', f'获取用户失败: {e}')
        return None
