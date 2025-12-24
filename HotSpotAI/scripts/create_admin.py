"""
创建管理员账户脚本
运行此脚本将在数据库中创建一个管理员账户
"""
import asyncio
import aiosqlite
from core.auth import get_password_hash

DB_FILE = "data.db"
ADMIN_USERNAME = "admin"
ADMIN_EMAIL = "admin@hotspotai.local"
ADMIN_PASSWORD = "aaaaaa"


async def create_admin_user():
    """创建管理员账户"""
    password_hash = get_password_hash(ADMIN_PASSWORD)

    try:
        async with aiosqlite.connect(DB_FILE) as db:
            # 检查管理员是否已存在
            db.row_factory = aiosqlite.Row
            async with db.execute(
                'SELECT * FROM users WHERE username = ?', (ADMIN_USERNAME,)
            ) as cursor:
                existing = await cursor.fetchone()

            if existing:
                # 更新现有账户为管理员
                await db.execute('''
                    UPDATE users
                    SET is_admin = 1
                    WHERE username = ?
                ''', (ADMIN_USERNAME,))
                await db.commit()
                print(f"用户 '{ADMIN_USERNAME}' 已存在，已更新为管理员")
            else:
                # 创建新的管理员账户
                await db.execute('''
                    INSERT INTO users (username, email, password_hash, is_admin)
                    VALUES (?, ?, ?, 1)
                ''', (ADMIN_USERNAME, ADMIN_EMAIL, password_hash))
                await db.commit()
                print(f"管理员账户创建成功！")
                print(f"用户名: {ADMIN_USERNAME}")
                print(f"密码: {ADMIN_PASSWORD}")
                print(f"邮箱: {ADMIN_EMAIL}")

    except Exception as e:
        print(f"创建管理员账户失败: {e}")


if __name__ == "__main__":
    asyncio.run(create_admin_user())
