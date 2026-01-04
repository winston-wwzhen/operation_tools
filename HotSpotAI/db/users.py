"""
用户 (users) 数据库操作模块
"""
from typing import Optional, Dict
from core.db_pool import get_db
from core.config import add_log


async def create_user(username: str, email: str, password_hash: str, is_admin: bool = False) -> Optional[int]:
    """
    创建用户

    Args:
        username: 用户名
        email: 邮箱
        password_hash: 密码哈希
        is_admin: 是否是管理员

    Returns:
        新用户ID，失败返回 None
    """
    try:
        async with get_db() as db:
            await db.execute('''
                INSERT INTO users (username, email, password_hash, is_admin)
                VALUES (?, ?, ?, ?)
            ''', (username, email, password_hash, 1 if is_admin else 0))

            await db.commit()

            async with db.execute("SELECT last_insert_rowid() as id") as cursor:
                row = await cursor.fetchone()
                user_id = row["id"]

            add_log('success', f'创建用户成功: {username}')
            return user_id

    except Exception as e:
        add_log('error', f'创建用户失败: {e}')
        return None


async def get_user_by_id(user_id: int) -> Optional[Dict]:
    """
    根据 ID 获取用户

    Args:
        user_id: 用户ID

    Returns:
        用户信息字典，不存在返回 None
    """
    try:
        async with get_db() as db:
            async with db.execute('''
                SELECT id, username, email, password_hash, is_admin, created_at, updated_at
                FROM users
                WHERE id = ?
            ''', (user_id,)) as cursor:
                row = await cursor.fetchone()

            if row:
                return {
                    "id": row['id'],
                    "username": row['username'],
                    "email": row['email'],
                    "password_hash": row['password_hash'],
                    "is_admin": bool(row['is_admin']),
                    "created_at": row['created_at'],
                    "updated_at": row['updated_at']
                }
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
        async with get_db() as db:
            async with db.execute('''
                SELECT id, username, email, password_hash, is_admin, created_at, updated_at
                FROM users
                WHERE email = ?
            ''', (email,)) as cursor:
                row = await cursor.fetchone()

            if row:
                return {
                    "id": row['id'],
                    "username": row['username'],
                    "email": row['email'],
                    "password_hash": row['password_hash'],
                    "is_admin": bool(row['is_admin']),
                    "created_at": row['created_at'],
                    "updated_at": row['updated_at']
                }
            return None

    except Exception as e:
        add_log('error', f'获取用户失败: {e}')
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
        async with get_db() as db:
            async with db.execute('''
                SELECT id, username, email, password_hash, is_admin, created_at, updated_at
                FROM users
                WHERE username = ?
            ''', (username,)) as cursor:
                row = await cursor.fetchone()

            if row:
                return {
                    "id": row['id'],
                    "username": row['username'],
                    "email": row['email'],
                    "password_hash": row['password_hash'],
                    "is_admin": bool(row['is_admin']),
                    "created_at": row['created_at'],
                    "updated_at": row['updated_at']
                }
            return None

    except Exception as e:
        add_log('error', f'获取用户失败: {e}')
        return None


async def update_user(user_id: int, **kwargs) -> bool:
    """
    更新用户信息

    Args:
        user_id: 用户ID
        **kwargs: 要更新的字段

    Returns:
        是否成功
    """
    try:
        async with get_db() as db:
            update_fields = []
            update_values = []

            for field in ['username', 'email', 'password_hash', 'is_admin']:
                if field in kwargs:
                    update_fields.append(f"{field} = ?")
                    value = kwargs[field]
                    if field == 'is_admin':
                        value = 1 if value else 0
                    update_values.append(value)

            if update_fields:
                update_values.append(user_id)
                await db.execute(f'''
                    UPDATE users
                    SET {', '.join(update_fields)}
                    WHERE id = ?
                ''', update_values)

                await db.commit()
                add_log('success', f'更新用户成功: {user_id}')
                return True

            return False

    except Exception as e:
        add_log('error', f'更新用户失败: {e}')
        return False
