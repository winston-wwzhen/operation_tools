"""
微信公众号发布管理器

提供微信公众号文章发布的核心业务逻辑：
- 保存文章为草稿
- 自动发布文章
- 发布频率限制检查
- 发布记录管理
"""
import aiosqlite
import time
from typing import Any, Dict, List, Optional
from datetime import datetime, timedelta

from .logger import add_log
from .wechat_client import WeChatClient, WeChatAPIError
from .config import get_settings

# 数据库文件路径
DB_FILE = "data.db"


class WeChatPublisher:
    """微信公众号发布管理器"""

    def __init__(self, db: aiosqlite.Connection):
        """
        初始化发布管理器

        Args:
            db: 数据库连接
        """
        self.db = db
        self.settings = get_settings()
        self._client_cache: Dict[int, WeChatClient] = {}

    async def _get_client(self, account_id: int) -> WeChatClient:
        """
        获取微信客户端（带缓存）

        Args:
            account_id: 公众号账号 ID

        Returns:
            WeChatClient 实例

        Raises:
            ValueError: 账号不存在或未激活
        """
        if account_id in self._client_cache:
            return self._client_cache[account_id]

        # 从数据库获取账号信息
        self.db.row_factory = aiosqlite.Row
        async with self.db.execute(
            "SELECT * FROM wechat_accounts WHERE id = ? AND is_active = 1",
            (account_id,)
        ) as cursor:
            account = await cursor.fetchone()

        if not account:
            raise ValueError(f"公众号账号不存在或未激活: {account_id}")

        # 创建客户端
        token_cache_time = getattr(self.settings, 'wechat_token_cache_time', 6600)
        client = WeChatClient(
            app_id=account['app_id'],
            secret=account['secret'],
            token_cache_time=token_cache_time
        )

        self._client_cache[account_id] = client
        return client

    async def check_publish_limits(
        self,
        user_id: int,
        wechat_account_id: int
    ) -> Dict[str, Any]:
        """
        检查发布频率限制

        Args:
            user_id: 用户 ID
            wechat_account_id: 公众号账号 ID

        Returns:
            {
                "can_publish": bool,  # 是否可以发布
                "reason": str,       # 不能发布的原因
                "next_publish_time": str  # 下次可发布时间
            }
        """
        # 获取发布间隔配置
        publish_interval = getattr(self.settings, 'wechat_publish_interval', 1800)
        daily_limit = getattr(self.settings, 'wechat_daily_limit', 1)

        current_time = datetime.now()

        # 1. 检查发布间隔
        self.db.row_factory = aiosqlite.Row
        async with self.db.execute('''
            SELECT published_at FROM wechat_publish_log
            WHERE wechat_account_id = ? AND publish_status = 'success'
            ORDER BY published_at DESC LIMIT 1
        ''', (wechat_account_id,)) as cursor:
            last_publish = await cursor.fetchone()

        if last_publish and last_publish['published_at']:
            last_time = datetime.fromisoformat(last_publish['published_at'])
            elapsed = (current_time - last_time).total_seconds()
            if elapsed < publish_interval:
                next_time = last_time + timedelta(seconds=publish_interval)
                return {
                    "can_publish": False,
                    "reason": f"发布间隔过短，距离上次发布仅 {int(elapsed)} 秒",
                    "next_publish_time": next_time.isoformat()
                }

        # 2. 检查每日发布次数
        today_start = current_time.replace(hour=0, minute=0, second=0, microsecond=0)
        async with self.db.execute('''
            SELECT COUNT(*) as count FROM wechat_publish_log
            WHERE wechat_account_id = ? AND publish_status = 'success'
            AND published_at >= ?
        ''', (wechat_account_id, today_start.isoformat())) as cursor:
            result = await cursor.fetchone()
            today_count = result['count'] if result else 0

        if today_count >= daily_limit:
            tomorrow = today_start + timedelta(days=1)
            return {
                "can_publish": False,
                "reason": f"今日发布次数已达上限 ({daily_limit})",
                "next_publish_time": tomorrow.isoformat()
            }

        return {
            "can_publish": True,
            "reason": "可以发布",
            "next_publish_time": None
        }

    async def save_draft(
        self,
        article_id: int,
        user_id: int,
        wechat_account_id: int
    ) -> Dict[str, Any]:
        """
        保存文章为草稿

        Args:
            article_id: 文章 ID
            user_id: 用户 ID
            wechat_account_id: 公众号账号 ID

        Returns:
            {
                "success": bool,
                "media_id": str,
                "create_time": int,
                "log_id": int
            }

        Raises:
            ValueError: 参数错误
            WeChatAPIError: API 调用失败
        """
        # 获取文章信息
        self.db.row_factory = aiosqlite.Row
        async with self.db.execute(
            "SELECT * FROM user_articles WHERE id = ? AND user_id = ?",
            (article_id, user_id)
        ) as cursor:
            article = await cursor.fetchone()

        if not article:
            raise ValueError(f"文章不存在: {article_id}")

        # 获取微信客户端
        client = await self._get_client(wechat_account_id)

        # 构建草稿数据
        # 从文章内容中提取摘要（如果没有）
        content = article['content']
        digest = content[:100].strip() if len(content) > 100 else content

        draft_articles = [{
            "title": article['title'],
            "author": "HotSpotAI",
            "digest": digest,
            "content": content,
            "need_open_comment": 1,
            "only_fans_can_comment": 0,
        }]

        # 调用 API 创建草稿
        try:
            result = await client.create_draft(draft_articles)

            # 更新文章表
            await self.db.execute('''
                UPDATE user_articles
                SET wechat_draft_id = ?, wechat_publish_status = 'draft'
                WHERE id = ?
            ''', (result['media_id'], article_id))

            # 创建发布记录
            await self.db.execute('''
                INSERT INTO wechat_publish_log (
                    user_id, article_id, wechat_account_id, publish_type,
                    media_id, publish_status
                ) VALUES (?, ?, ?, 'draft', ?, 'success')
            ''', (user_id, article_id, wechat_account_id, result['media_id']))

            await self.db.commit()

            # 获取日志 ID
            async with self.db.execute(
                "SELECT last_insert_rowid() as id"
            ) as cursor:
                log_row = await cursor.fetchone()
                log_id = log_row['id']

            add_log("INFO", f"文章 {article_id} 已保存为草稿: {result['media_id']}")

            return {
                "success": True,
                "media_id": result['media_id'],
                "create_time": result['create_time'],
                "log_id": log_id
            }

        except WeChatAPIError as e:
            # 记录失败日志
            await self.db.execute('''
                INSERT INTO wechat_publish_log (
                    user_id, article_id, wechat_account_id, publish_type,
                    publish_status, error_message
                ) VALUES (?, ?, ?, 'draft', 'failed', ?)
            ''', (user_id, article_id, wechat_account_id, str(e)))
            await self.db.commit()

            raise

    async def publish_article(
        self,
        article_id: int,
        user_id: int,
        wechat_account_id: int
    ) -> Dict[str, Any]:
        """
        自动发布文章

        Args:
            article_id: 文章 ID
            user_id: 用户 ID
            wechat_account_id: 公众号账号 ID

        Returns:
            {
                "success": bool,
                "publish_id": str,
                "published_at": str,
                "log_id": int
            }

        Raises:
            ValueError: 参数错误或发布限制
            WeChatAPIError: API 调用失败
        """
        # 检查发布限制
        limit_check = await self.check_publish_limits(user_id, wechat_account_id)
        if not limit_check['can_publish']:
            raise ValueError(limit_check['reason'])

        # 获取文章信息
        self.db.row_factory = aiosqlite.Row
        async with self.db.execute(
            "SELECT * FROM user_articles WHERE id = ? AND user_id = ?",
            (article_id, user_id)
        ) as cursor:
            article = await cursor.fetchone()

        if not article:
            raise ValueError(f"文章不存在: {article_id}")

        # 获取微信客户端
        client = await self._get_client(wechat_account_id)

        # 检查是否已有草稿
        media_id = article.get('wechat_draft_id')

        try:
            if not media_id:
                # 没有草稿，直接创建并发布
                content = article['content']
                digest = content[:100].strip() if len(content) > 100 else content

                draft_articles = [{
                    "title": article['title'],
                    "author": "HotSpotAI",
                    "digest": digest,
                    "content": content,
                    "need_open_comment": 1,
                    "only_fans_can_comment": 0,
                }]

                # 创建草稿
                draft_result = await client.create_draft(draft_articles)
                media_id = draft_result['media_id']

                # 更新文章表
                await self.db.execute('''
                    UPDATE user_articles
                    SET wechat_draft_id = ?
                    WHERE id = ?
                ''', (media_id, article_id))

            # 发布草稿
            publish_result = await client.publish_draft(media_id)

            # 更新文章表
            await self.db.execute('''
                UPDATE user_articles
                SET wechat_publish_status = 'published'
                WHERE id = ?
            ''', (article_id,))

            # 创建发布记录
            published_at = datetime.now().isoformat()
            await self.db.execute('''
                INSERT INTO wechat_publish_log (
                    user_id, article_id, wechat_account_id, publish_type,
                    media_id, publish_status, publish_id, published_at
                ) VALUES (?, ?, ?, 'auto', ?, 'success', ?, ?)
            ''', (
                user_id, article_id, wechat_account_id,
                media_id, publish_result['publish_id'], published_at
            ))

            await self.db.commit()

            # 获取日志 ID
            async with self.db.execute(
                "SELECT last_insert_rowid() as id"
            ) as cursor:
                log_row = await cursor.fetchone()
                log_id = log_row['id']

            add_log("INFO", f"文章 {article_id} 已自动发布: {publish_result['publish_id']}")

            return {
                "success": True,
                "publish_id": publish_result['publish_id'],
                "published_at": published_at,
                "log_id": log_id
            }

        except WeChatAPIError as e:
            # 更新文章状态
            await self.db.execute('''
                UPDATE user_articles
                SET wechat_publish_status = 'failed'
                WHERE id = ?
            ''', (article_id,))

            # 记录失败日志
            await self.db.execute('''
                INSERT INTO wechat_publish_log (
                    user_id, article_id, wechat_account_id, publish_type,
                    publish_status, error_message
                ) VALUES (?, ?, ?, 'auto', 'failed', ?)
            ''', (user_id, article_id, wechat_account_id, str(e)))
            await self.db.commit()

            raise

    async def get_publish_logs(
        self,
        user_id: int,
        offset: int = 0,
        limit: int = 20
    ) -> Dict[str, Any]:
        """
        获取发布记录

        Args:
            user_id: 用户 ID
            offset: 偏移量
            limit: 每页数量

        Returns:
            {
                "logs": [...],
                "total": int
            }
        """
        logs = []
        self.db.row_factory = aiosqlite.Row

        # 获取总数
        async with self.db.execute(
            "SELECT COUNT(*) as count FROM wechat_publish_log WHERE user_id = ?",
            (user_id,)
        ) as cursor:
            row = await cursor.fetchone()
            total = row['count']

        # 获取分页数据
        async with self.db.execute('''
            SELECT l.*, a.title as article_title, w.account_name, w.nickname
            FROM wechat_publish_log l
            LEFT JOIN user_articles a ON l.article_id = a.id
            LEFT JOIN wechat_accounts w ON l.wechat_account_id = w.id
            WHERE l.user_id = ?
            ORDER BY l.created_at DESC
            LIMIT ? OFFSET ?
        ''', (user_id, limit, offset)) as cursor:
            rows = await cursor.fetchall()

        for r in rows:
            logs.append({
                "id": r['id'],
                "article_id": r['article_id'],
                "article_title": r['article_title'],
                "wechat_account_id": r['wechat_account_id'],
                "account_name": r['account_name'] or r['nickname'],
                "publish_type": r['publish_type'],
                "publish_status": r['publish_status'],
                "publish_id": r['publish_id'],
                "published_at": r['published_at'],
                "error_message": r['error_message'],
                "created_at": r['created_at']
            })

        return {
            "logs": logs,
            "total": total
        }

    async def close(self):
        """关闭所有客户端连接"""
        for client in self._client_cache.values():
            await client.close()
        self._client_cache.clear()
