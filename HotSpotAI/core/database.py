"""
异步数据库管理模块
使用 aiosqlite 实现非阻塞的数据库操作
"""
import aiosqlite
import json
from datetime import datetime
from typing import List, Dict, Optional
from core.config import add_log

DB_FILE = "data.db"


async def init_db():
    """初始化数据库表结构（异步）"""
    try:
        async with aiosqlite.connect(DB_FILE) as db:
            await db.execute('''
                CREATE TABLE IF NOT EXISTS hot_topics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT,
                    link TEXT,
                    source TEXT,
                    heat INTEGER,
                    tags TEXT,
                    comment TEXT,
                    created_at TIMESTAMP
                )
            ''')
            # 创建索引以提升查询性能
            await db.execute('''
                CREATE INDEX IF NOT EXISTS idx_created_at
                ON hot_topics(created_at DESC)
            ''')
            await db.execute('''
                CREATE INDEX IF NOT EXISTS idx_source
                ON hot_topics(source)
            ''')
            await db.commit()
        add_log('info', '数据库初始化检查完成')
    except Exception as e:
        add_log('error', f'数据库初始化失败: {e}')


async def save_topics_to_db(topics: List[Dict]) -> int:
    """
    保存一批热点数据（异步）

    Args:
        topics: 热点话题列表

    Returns:
        保存的记录数
    """
    if not topics:
        return 0

    try:
        async with aiosqlite.connect(DB_FILE) as db:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            count = 0

            # 使用事务批量插入
            async with db.execute('BEGIN') as _:
                for topic in topics:
                    tags_json = json.dumps(topic.get('tags', []), ensure_ascii=False)

                    await db.execute('''
                        INSERT INTO hot_topics (title, link, source, heat, tags, comment, created_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        topic.get('title'),
                        topic.get('link'),
                        topic.get('source'),
                        topic.get('heat', 0),
                        tags_json,
                        topic.get('comment', ''),
                        timestamp
                    ))
                    count += 1

                await db.commit()

        add_log('success', f'已将 {count} 条数据保存至数据库')
        return count

    except Exception as e:
        add_log('error', f'保存数据至数据库失败: {e}')
        return 0


async def load_latest_topics_from_db(limit: int = 50) -> List[Dict]:
    """
    加载最近一次抓取的数据（异步）

    Args:
        limit: 最大返回数量

    Returns:
        热点话题列表
    """
    topics = []
    try:
        async with aiosqlite.connect(DB_FILE) as db:
            db.row_factory = aiosqlite.Row

            # 查最近的时间点
            async with db.execute(
                "SELECT created_at FROM hot_topics ORDER BY id DESC LIMIT 1"
            ) as cursor:
                row = await cursor.fetchone()

            if row:
                latest_time = row['created_at']

                # 查该时间点的所有数据
                async with db.execute('''
                    SELECT * FROM hot_topics
                    WHERE created_at = ?
                    ORDER BY heat DESC
                    LIMIT ?
                ''', (latest_time, limit)) as cursor:
                    rows = await cursor.fetchall()

                for r in rows:
                    topics.append({
                        "title": r['title'],
                        "link": r['link'],
                        "source": r['source'],
                        "heat": r['heat'],
                        "tags": json.loads(r['tags']) if r['tags'] else [],
                        "comment": r['comment']
                    })

                add_log('info', f'从数据库恢复了 {len(topics)} 条历史记录 ({latest_time})')

    except Exception as e:
        add_log('error', f'读取数据库失败: {e}')

    return topics


async def get_topics_by_source(source: str, limit: int = 20) -> List[Dict]:
    """
    按来源获取热点话题（异步）

    Args:
        source: 数据源 (weibo, baidu, zhihu等)
        limit: 最大返回数量

    Returns:
        热点话题列表
    """
    topics = []
    try:
        async with aiosqlite.connect(DB_FILE) as db:
            db.row_factory = aiosqlite.Row

            async with db.execute('''
                SELECT * FROM hot_topics
                WHERE source = ?
                ORDER BY heat DESC
                LIMIT ?
            ''', (source, limit)) as cursor:
                rows = await cursor.fetchall()

            for r in rows:
                topics.append({
                    "title": r['title'],
                    "link": r['link'],
                    "source": r['source'],
                    "heat": r['heat'],
                    "tags": json.loads(r['tags']) if r['tags'] else [],
                    "comment": r['comment']
                })

    except Exception as e:
        add_log('error', f'按来源读取数据库失败: {e}')

    return topics


async def clean_old_topics(days: int = 7) -> int:
    """
    清理旧数据（异步）

    Args:
        days: 保留最近几天的数据

    Returns:
        删除的记录数
    """
    try:
        async with aiosqlite.connect(DB_FILE) as db:
            cursor = await db.execute('''
                DELETE FROM hot_topics
                WHERE created_at < datetime('now', '-' || ? || ' days')
            ''', (days,))
            await db.commit()

            deleted_count = cursor.rowcount
            if deleted_count > 0:
                add_log('info', f'已清理 {deleted_count} 条 {days} 天前的旧数据')

            return deleted_count

    except Exception as e:
        add_log('error', f'清理旧数据失败: {e}')
        return 0


async def get_stats() -> Dict:
    """
    获取数据库统计信息（异步）

    Returns:
        包含统计信息的字典
    """
    stats = {
        "total_topics": 0,
        "by_source": {},
        "latest_update": None
    }

    try:
        async with aiosqlite.connect(DB_FILE) as db:
            # 总数统计
            async with db.execute("SELECT COUNT(*) as count FROM hot_topics") as cursor:
                row = await cursor.fetchone()
                stats["total_topics"] = row["count"]

            # 按来源统计
            async with db.execute('''
                SELECT source, COUNT(*) as count
                FROM hot_topics
                GROUP BY source
            ''') as cursor:
                rows = await cursor.fetchall()
                for r in rows:
                    stats["by_source"][r["source"]] = r["count"]

            # 最新更新时间
            async with db.execute('''
                SELECT created_at FROM hot_topics
                ORDER BY id DESC LIMIT 1
            ''') as cursor:
                row = await cursor.fetchone()
                if row:
                    stats["latest_update"] = row["created_at"]

    except Exception as e:
        add_log('error', f'获取统计信息失败: {e}')

    return stats


async def get_historical_topics(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    source: Optional[str] = None,
    offset: int = 0,
    limit: int = 50
) -> Dict:
    """
    获取历史热点数据（支持分页和筛选）

    Args:
        start_date: 起始日期 (YYYY-MM-DD)
        end_date: 结束日期 (YYYY-MM-DD)
        source: 数据源筛选 (weibo, baidu, zhihu等)
        offset: 偏移量（用于分页）
        limit: 每页数量

    Returns:
        {
            "topics": [...],
            "total": 总数,
            "offset": 偏移量,
            "limit": 每页数量
        }
    """
    topics = []
    total = 0

    try:
        async with aiosqlite.connect(DB_FILE) as db:
            db.row_factory = aiosqlite.Row

            # 构建 WHERE 条件
            where_conditions = []
            params = []

            if start_date:
                where_conditions.append("DATE(created_at) >= ?")
                params.append(start_date)
            if end_date:
                where_conditions.append("DATE(created_at) <= ?")
                params.append(end_date)
            if source:
                where_conditions.append("source = ?")
                params.append(source)

            where_clause = ""
            if where_conditions:
                where_clause = "WHERE " + " AND ".join(where_conditions)

            # 获取总数
            count_params = params.copy()
            async with db.execute(
                f"SELECT COUNT(*) as count FROM hot_topics {where_clause}",
                count_params
            ) as cursor:
                row = await cursor.fetchone()
                total = row["count"]

            # 获取分页数据
            query_params = params.copy()
            query_params.extend([limit, offset])
            async with db.execute(f'''
                SELECT * FROM hot_topics
                {where_clause}
                ORDER BY created_at DESC, heat DESC
                LIMIT ? OFFSET ?
            ''', query_params) as cursor:
                rows = await cursor.fetchall()

            for r in rows:
                topics.append({
                    "id": r['id'],
                    "title": r['title'],
                    "link": r['link'],
                    "source": r['source'],
                    "heat": r['heat'],
                    "tags": json.loads(r['tags']) if r['tags'] else [],
                    "comment": r['comment'],
                    "created_at": r['created_at']
                })

    except Exception as e:
        add_log('error', f'获取历史数据失败: {e}')

    return {
        "topics": topics,
        "total": total,
        "offset": offset,
        "limit": limit
    }


async def get_distinct_dates() -> List[str]:
    """
    获取数据库中所有有数据的日期列表

    Returns:
        日期列表 (YYYY-MM-DD 格式，降序)
    """
    dates = []
    try:
        async with aiosqlite.connect(DB_FILE) as db:
            async with db.execute('''
                SELECT DISTINCT DATE(created_at) as date
                FROM hot_topics
                ORDER BY date DESC
            ''') as cursor:
                rows = await cursor.fetchall()
                for r in rows:
                    dates.append(r['date'])

    except Exception as e:
        add_log('error', f'获取日期列表失败: {e}')

    return dates
