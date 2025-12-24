"""
用户文章数据库操作模块
提供文章的创建、查询、更新、删除等数据库操作
"""
import aiosqlite
import secrets
from typing import Optional, Dict, List
from core.config import add_log

DB_FILE = "data.db"


async def create_article(
    user_id: int,
    topic_id: Optional[int],
    topic_title: str,
    topic_link: Optional[str],
    topic_source: Optional[str],
    title: str,
    content: str,
    platform: str
) -> Optional[int]:
    """
    创建新文章

    Args:
        user_id: 用户 ID
        topic_id: 关联的热点 ID（可选）
        topic_title: 热点标题
        topic_link: 热点链接（可选）
        topic_source: 热点来源（可选）
        title: 文章标题
        content: 文章内容
        platform: 目标平台

    Returns:
        文章 ID，失败返回 None
    """
    share_token = secrets.token_urlsafe(16)
    try:
        async with aiosqlite.connect(DB_FILE) as db:
            cursor = await db.execute('''
                INSERT INTO user_articles
                (user_id, topic_id, topic_title, topic_link, topic_source, title, content, platform, share_token)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (user_id, topic_id, topic_title, topic_link, topic_source, title, content, platform, share_token))
            await db.commit()
            return cursor.lastrowid
    except Exception as e:
        add_log('error', f'创建文章失败: {e}')
        return None


async def get_user_articles(
    user_id: int,
    offset: int = 0,
    limit: int = 20
) -> Dict:
    """
    获取用户的文章列表（分页）

    Args:
        user_id: 用户 ID
        offset: 偏移量
        limit: 每页数量

    Returns:
        包含文章列表和总数的字典
    """
    try:
        async with aiosqlite.connect(DB_FILE) as db:
            db.row_factory = aiosqlite.Row

            # 获取总数
            async with db.execute(
                'SELECT COUNT(*) as count FROM user_articles WHERE user_id = ?', (user_id,)
            ) as cursor:
                total = (await cursor.fetchone())['count']

            # 获取文章列表
            async with db.execute('''
                SELECT id, topic_title, topic_link, topic_source, title, platform, share_token, is_public, created_at
                FROM user_articles
                WHERE user_id = ?
                ORDER BY created_at DESC
                LIMIT ? OFFSET ?
            ''', (user_id, limit, offset)) as cursor:
                rows = await cursor.fetchall()

            articles = [dict(row) for row in rows]
            return {"articles": articles, "total": total, "offset": offset, "limit": limit}
    except Exception as e:
        add_log('error', f'获取用户文章失败: {e}')
        return {"articles": [], "total": 0, "offset": offset, "limit": limit}


async def get_article_by_share_token(share_token: str) -> Optional[Dict]:
    """
    根据分享 token 获取文章（公开访问）

    Args:
        share_token: 分享 token

    Returns:
        文章信息字典，不存在或非公开返回 None
    """
    try:
        async with aiosqlite.connect(DB_FILE) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute('''
                SELECT id, topic_title, topic_link, topic_source, title, content, platform, created_at
                FROM user_articles
                WHERE share_token = ? AND is_public = 1
            ''', (share_token,)) as cursor:
                row = await cursor.fetchone()
                if row:
                    return dict(row)
        return None
    except Exception as e:
        add_log('error', f'获取分享文章失败: {e}')
        return None


async def get_article_by_id(article_id: int, user_id: int) -> Optional[Dict]:
    """
    根据 ID 获取文章（所有者访问）

    Args:
        article_id: 文章 ID
        user_id: 用户 ID

    Returns:
        文章信息字典，不存在或无权限返回 None
    """
    try:
        async with aiosqlite.connect(DB_FILE) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute('''
                SELECT * FROM user_articles
                WHERE id = ? AND user_id = ?
            ''', (article_id, user_id)) as cursor:
                row = await cursor.fetchone()
                if row:
                    return dict(row)
        return None
    except Exception as e:
        add_log('error', f'获取文章失败: {e}')
        return None


async def update_article_public_status(article_id: int, user_id: int, is_public: bool) -> bool:
    """
    更新文章公开状态

    Args:
        article_id: 文章 ID
        user_id: 用户 ID
        is_public: 是否公开

    Returns:
        是否成功
    """
    try:
        async with aiosqlite.connect(DB_FILE) as db:
            await db.execute('''
                UPDATE user_articles
                SET is_public = ?
                WHERE id = ? AND user_id = ?
            ''', (1 if is_public else 0, article_id, user_id))
            await db.commit()
            return True
    except Exception as e:
        add_log('error', f'更新文章状态失败: {e}')
        return False


async def delete_article(article_id: int, user_id: int) -> bool:
    """
    删除文章

    Args:
        article_id: 文章 ID
        user_id: 用户 ID

    Returns:
        是否成功
    """
    try:
        async with aiosqlite.connect(DB_FILE) as db:
            await db.execute('''
                DELETE FROM user_articles
                WHERE id = ? AND user_id = ?
            ''', (article_id, user_id))
            await db.commit()
            return True
    except Exception as e:
        add_log('error', f'删除文章失败: {e}')
        return False
