"""
创建管理员账户脚本
运行此脚本将在数据库中创建一个管理员账户

管理员凭据从环境变量读取：
- ADMIN_USERNAME: 管理员用户名（默认: admin）
- ADMIN_PASSWORD: 管理员密码（默认: aaaaaa）
- ADMIN_EMAIL: 管理员邮箱（默认: admin@hotspotai.local）

需要在 .env 文件中配置这些变量。
"""
import asyncio
import aiosqlite
import os
import sys

# 获取脚本所在目录的父目录（HotSpotAI 目录）
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(SCRIPT_DIR)
DB_FILE = os.path.join(PROJECT_DIR, "data.db")

# 将 PROJECT_DIR 添加到 Python 路径，以便导入 core 模块
if PROJECT_DIR not in sys.path:
    sys.path.insert(0, PROJECT_DIR)

from core.auth import get_password_hash
from core.config import get_settings

# 加载环境变量
env_file = os.path.join(PROJECT_DIR, ".env")
if os.path.exists(env_file):
    with open(env_file, 'r') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                os.environ[key.strip()] = value.strip()

# 从环境变量读取管理员凭据，使用默认值
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "aaaaaa")
ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "admin@hotspotai.local")


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
