"""
异步数据库管理模块
使用连接池提供非阻塞的数据库操作
"""
import aiosqlite
import json
from datetime import datetime
from typing import List, Dict, Optional
from core.config import add_log
from core.db_pool import get_db

DB_FILE = "data.db"


async def init_db():
    """初始化数据库表结构（异步）"""
    try:
        async with get_db() as db:
            # 热点话题表 - 精选后的最终热点
            await db.execute('''
                CREATE TABLE IF NOT EXISTS hot_topics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    link TEXT NOT NULL,
                    source TEXT NOT NULL,
                    ai_score DECIMAL(3,2),
                    ai_comment TEXT,
                    category_id INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (category_id) REFERENCES categories(id)
                )
            ''')

            # 用户表
            await db.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    email TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    is_admin INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            # 用户文章表
            await db.execute('''
                CREATE TABLE IF NOT EXISTS user_articles (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    topic_id INTEGER,
                    topic_title TEXT NOT NULL,
                    topic_link TEXT,
                    topic_source TEXT,
                    title TEXT NOT NULL,
                    content TEXT NOT NULL,
                    platform TEXT NOT NULL,
                    share_token TEXT UNIQUE NOT NULL,
                    is_public INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
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
            await db.execute('''
                CREATE INDEX IF NOT EXISTS idx_users_username
                ON users(username)
            ''')
            await db.execute('''
                CREATE INDEX IF NOT EXISTS idx_users_email
                ON users(email)
            ''')
            await db.execute('''
                CREATE INDEX IF NOT EXISTS idx_user_articles_user_id
                ON user_articles(user_id)
            ''')
            await db.execute('''
                CREATE INDEX IF NOT EXISTS idx_user_articles_share_token
                ON user_articles(share_token)
            ''')
            await db.execute('''
                CREATE INDEX IF NOT EXISTS idx_user_articles_created_at
                ON user_articles(created_at DESC)
            ''')

            # 创建更新时间触发器
            await db.execute('''
                CREATE TRIGGER IF NOT EXISTS update_users_timestamp
                AFTER UPDATE ON users
                BEGIN
                    UPDATE users SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
                END
            ''')
            await db.execute('''
                CREATE TRIGGER IF NOT EXISTS update_user_articles_timestamp
                AFTER UPDATE ON user_articles
                BEGIN
                    UPDATE user_articles SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
                END
            ''')

            # 微信公众号账号配置表
            await db.execute('''
                CREATE TABLE IF NOT EXISTS wechat_accounts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    app_id TEXT NOT NULL,
                    secret TEXT NOT NULL,
                    account_name TEXT,
                    nickname TEXT,
                    avatar_url TEXT,
                    access_token TEXT,
                    token_expires_at INTEGER,
                    is_active INTEGER DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                )
            ''')

            # 微信发布记录表
            await db.execute('''
                CREATE TABLE IF NOT EXISTS wechat_publish_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    article_id INTEGER NOT NULL,
                    wechat_account_id INTEGER NOT NULL,
                    publish_type TEXT NOT NULL,
                    media_id TEXT,
                    publish_status TEXT DEFAULT 'pending',
                    publish_id TEXT,
                    published_at TIMESTAMP,
                    error_message TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                    FOREIGN KEY (article_id) REFERENCES user_articles(id) ON DELETE CASCADE,
                    FOREIGN KEY (wechat_account_id) REFERENCES wechat_accounts(id) ON DELETE CASCADE
                )
            ''')

            # 微信账号表索引
            await db.execute('''
                CREATE INDEX IF NOT EXISTS idx_wechat_accounts_user_id
                ON wechat_accounts(user_id)
            ''')
            await db.execute('''
                CREATE INDEX IF NOT EXISTS idx_wechat_accounts_is_active
                ON wechat_accounts(is_active)
            ''')

            # 发布记录表索引
            await db.execute('''
                CREATE INDEX IF NOT EXISTS idx_wechat_publish_log_user_id
                ON wechat_publish_log(user_id)
            ''')
            await db.execute('''
                CREATE INDEX IF NOT EXISTS idx_wechat_publish_log_article_id
                ON wechat_publish_log(article_id)
            ''')
            await db.execute('''
                CREATE INDEX IF NOT EXISTS idx_wechat_publish_log_created_at
                ON wechat_publish_log(created_at DESC)
            ''')

            # 创建微信账号表更新时间触发器
            await db.execute('''
                CREATE TRIGGER IF NOT EXISTS update_wechat_accounts_timestamp
                AFTER UPDATE ON wechat_accounts
                BEGIN
                    UPDATE wechat_accounts SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
                END
            ''')

            # ========== 分类相关表 ==========

            # 分类表
            await db.execute('''
                CREATE TABLE IF NOT EXISTS categories (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE NOT NULL,
                    slug TEXT UNIQUE NOT NULL,
                    description TEXT,
                    icon TEXT,
                    color TEXT,
                    is_active INTEGER DEFAULT 1,
                    sort_order INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            # 关键词表
            await db.execute('''
                CREATE TABLE IF NOT EXISTS category_keywords (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    category_id INTEGER NOT NULL,
                    keyword TEXT NOT NULL,
                    weight INTEGER DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (category_id) REFERENCES categories(id) ON DELETE CASCADE
                )
            ''')

            # 平台分类配置表
            await db.execute('''
                CREATE TABLE IF NOT EXISTS category_platforms (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    category_id INTEGER NOT NULL,
                    platform TEXT NOT NULL,
                    is_enabled INTEGER DEFAULT 1,
                    FOREIGN KEY (category_id) REFERENCES categories(id) ON DELETE CASCADE
                )
            ''')

            # 分类相关索引
            await db.execute('''
                CREATE INDEX IF NOT EXISTS idx_category_keywords_category_id
                ON category_keywords(category_id)
            ''')
            await db.execute('''
                CREATE INDEX IF NOT EXISTS idx_category_keywords_keyword
                ON category_keywords(keyword)
            ''')
            await db.execute('''
                CREATE INDEX IF NOT EXISTS idx_category_platforms_category_id
                ON category_platforms(category_id)
            ''')
            await db.execute('''
                CREATE INDEX IF NOT EXISTS idx_categories_is_active
                ON categories(is_active)
            ''')

            # 创建分类表更新时间触发器
            await db.execute('''
                CREATE TRIGGER IF NOT EXISTS update_categories_timestamp
                AFTER UPDATE ON categories
                BEGIN
                    UPDATE categories SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
                END
            ''')

            # ========== 原始新闻表（raw_news）用于爬虫存储 ==========
            await db.execute('''
                CREATE TABLE IF NOT EXISTS raw_news (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    link TEXT UNIQUE NOT NULL,
                    source TEXT NOT NULL,
                    category_id INTEGER,
                    analyzed BOOLEAN DEFAULT 0,
                    analyze_fail_count INTEGER DEFAULT 0,
                    skip_reason TEXT,
                    ai_score DECIMAL(3,2),
                    ai_comment TEXT,
                    last_analyzed_at TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (category_id) REFERENCES categories(id)
                )
            ''')

            # raw_news 索引
            await db.execute('''
                CREATE INDEX IF NOT EXISTS idx_raw_news_link ON raw_news(link)
            ''')
            await db.execute('''
                CREATE INDEX IF NOT EXISTS idx_raw_news_source ON raw_news(source)
            ''')
            await db.execute('''
                CREATE INDEX IF NOT EXISTS idx_raw_news_analyzed ON raw_news(analyzed)
            ''')
            await db.execute('''
                CREATE INDEX IF NOT EXISTS idx_raw_news_created_at ON raw_news(created_at DESC)
            ''')
            await db.execute('''
                CREATE INDEX IF NOT EXISTS idx_raw_news_ai_score ON raw_news(ai_score DESC)
            ''')
            await db.execute('''
                CREATE INDEX IF NOT EXISTS idx_raw_news_category_id ON raw_news(category_id)
            ''')

            await db.commit()

            # 数据库迁移：为已存在的 users 表添加 is_admin 字段
            try:
                await db.execute('ALTER TABLE users ADD COLUMN is_admin INTEGER DEFAULT 0')
                await db.commit()
                add_log('info', '数据库迁移完成：已添加 is_admin 字段')
            except Exception as migrate_error:
                # 字段已存在，忽略错误
                if 'duplicate column' not in str(migrate_error).lower():
                    pass

            # 数据库迁移：为已存在的 user_articles 表添加微信相关字段
            try:
                await db.execute('ALTER TABLE user_articles ADD COLUMN wechat_draft_id TEXT')
                await db.execute('ALTER TABLE user_articles ADD COLUMN wechat_publish_status TEXT DEFAULT "draft"')
                await db.commit()
                add_log('info', '数据库迁移完成：已添加微信相关字段')
            except Exception as migrate_error:
                # 字段已存在，忽略错误
                if 'duplicate column' not in str(migrate_error).lower():
                    pass

            # 数据库迁移：为 hot_topics 表添加分类相关字段
            try:
                await db.execute('ALTER TABLE hot_topics ADD COLUMN category_id INTEGER')
                await db.execute('ALTER TABLE hot_topics ADD COLUMN matched_keyword TEXT')
                await db.execute('CREATE INDEX IF NOT EXISTS idx_hot_topics_category_id ON hot_topics(category_id)')
                await db.commit()
                add_log('info', '数据库迁移完成：已添加分类相关字段')
            except Exception as migrate_error:
                # 字段已存在，忽略错误
                if 'duplicate column' not in str(migrate_error).lower():
                    pass

        add_log('info', '数据库初始化检查完成')
    except Exception as e:
        add_log('error', f'数据库初始化失败: {e}')


async def save_topics_to_db(topics: List[Dict]) -> int:
    """
    保存一批热点数据（异步）

    Args:
        topics: 热点话题列表，支持扩展字段 category_id 和 matched_keyword

    Returns:
        保存的记录数
    """
    if not topics:
        return 0

    try:
        async with get_db() as db:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            count = 0

            # 使用事务批量插入
            async with db.execute('BEGIN') as _:
                for topic in topics:
                    tags_json = json.dumps(topic.get('tags', []), ensure_ascii=False)

                    await db.execute('''
                        INSERT INTO hot_topics (title, link, source, heat, tags, comment, created_at, category_id, matched_keyword)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        topic.get('title'),
                        topic.get('link'),
                        topic.get('source'),
                        topic.get('heat', 0),
                        tags_json,
                        topic.get('comment', ''),
                        timestamp,
                        topic.get('category_id'),
                        topic.get('matched_keyword')
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
        async with get_db() as db:

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
        async with get_db() as db:

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
        async with get_db() as db:
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
        async with get_db() as db:
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
        async with get_db() as db:

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
        async with get_db() as db:
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


# ============ 分类相关函数 ============

# 预定义分类数据
DEFAULT_CATEGORIES = [
    {
        "name": "AI科技",
        "slug": "ai-tech",
        "description": "人工智能、前沿科技",
        "icon": "🤖",
        "color": "#6366f1",
        "keywords": ["AI", "ChatGPT", "人工智能", "大模型", "芯片", "半导体", "5G", "区块链"]
    },
    {
        "name": "财经投资",
        "slug": "finance",
        "description": "金融、投资、股市",
        "icon": "💰",
        "color": "#10b981",
        "keywords": ["股票", "基金", "理财", "A股", "港股", "美股", "比特币", "金融"]
    },
    {
        "name": "职场成长",
        "slug": "career",
        "description": "职业发展、技能提升",
        "icon": "💼",
        "color": "#f59e0b",
        "keywords": ["职场", "面试", "薪资", "裁员", "跳槽", "考证", "副业", "创业"]
    },
    {
        "name": "健康养生",
        "slug": "health",
        "description": "健康、医疗、养生",
        "icon": "🏥",
        "color": "#ef4444",
        "keywords": ["健康", "医疗", "养生", "减肥", "健身", "疫苗", "医保", "疫情"]
    },
    {
        "name": "教育育儿",
        "slug": "education",
        "description": "教育、育儿、学习",
        "icon": "📚",
        "color": "#8b5cf6",
        "keywords": ["教育", "高考", "考研", "留学", "育儿", "双减", "培训", "幼升小"]
    },
    {
        "name": "数码评测",
        "slug": "digital",
        "description": "数码产品、评测",
        "icon": "📱",
        "color": "#3b82f6",
        "keywords": ["手机", "电脑", "平板", "耳机", "相机", "测评", "发布会", "新品"]
    },
    {
        "name": "美食生活",
        "slug": "food",
        "description": "美食、生活方式",
        "icon": "🍜",
        "color": "#f97316",
        "keywords": ["美食", "菜谱", "餐厅", "探店", "外卖", "咖啡", "奶茶", "零食"]
    },
    {
        "name": "影视娱乐",
        "slug": "entertainment",
        "description": "影视、综艺、娱乐",
        "icon": "🎬",
        "color": "#ec4899",
        "keywords": ["电影", "电视剧", "综艺", "明星", "娱乐圈", "票房", "剧集", "档期"]
    },
    {
        "name": "旅游出行",
        "slug": "travel",
        "description": "旅游、交通、出行",
        "icon": "✈️",
        "color": "#06b6d4",
        "keywords": ["旅游", "机票", "酒店", "景点", "自驾", "假期", "交通", "出行"]
    },
    {
        "name": "情感心理",
        "slug": "emotion",
        "description": "情感、心理、人际关系",
        "icon": "💕",
        "color": "#d946ef",
        "keywords": ["恋爱", "婚姻", "情感", "心理", "抑郁", "焦虑", "社交", "人际关系"]
    }
]


async def get_categories(include_inactive: bool = False) -> List[Dict]:
    """
    获取所有分类

    Args:
        include_inactive: 是否包含未激活的分类

    Returns:
        分类列表
    """
    categories = []
    try:
        async with get_db() as db:
            

            where_clause = "" if include_inactive else "WHERE is_active = 1"

            async with db.execute(f'''
                SELECT id, name, slug, description, icon, color, is_active, sort_order, created_at, updated_at
                FROM categories
                {where_clause}
                ORDER BY sort_order ASC, id ASC
            ''') as cursor:
                rows = await cursor.fetchall()

            for r in rows:
                categories.append({
                    "id": r['id'],
                    "name": r['name'],
                    "slug": r['slug'],
                    "description": r['description'],
                    "icon": r['icon'],
                    "color": r['color'],
                    "is_active": bool(r['is_active']),
                    "sort_order": r['sort_order'],
                    "created_at": r['created_at'],
                    "updated_at": r['updated_at']
                })

    except Exception as e:
        add_log('error', f'获取分类列表失败: {e}')

    return categories


async def get_category_by_id(category_id: int) -> Optional[Dict]:
    """
    获取分类详情（含关键词和平台配置）

    Args:
        category_id: 分类ID

    Returns:
        分类详情，包含关键词列表和平台配置
    """
    try:
        async with get_db() as db:
            

            # 获取分类基本信息
            async with db.execute('''
                SELECT id, name, slug, description, icon, color, is_active, sort_order, created_at, updated_at
                FROM categories
                WHERE id = ?
            ''', (category_id,)) as cursor:
                row = await cursor.fetchone()

            if not row:
                return None

            category = {
                "id": row['id'],
                "name": row['name'],
                "slug": row['slug'],
                "description": row['description'],
                "icon": row['icon'],
                "color": row['color'],
                "is_active": bool(row['is_active']),
                "sort_order": row['sort_order'],
                "created_at": row['created_at'],
                "updated_at": row['updated_at'],
                "keywords": [],
                "platforms": []
            }

            # 获取关键词
            async with db.execute('''
                SELECT keyword, weight
                FROM category_keywords
                WHERE category_id = ?
                ORDER BY weight DESC, id ASC
            ''', (category_id,)) as cursor:
                keyword_rows = await cursor.fetchall()
                for kr in keyword_rows:
                    category["keywords"].append({
                        "keyword": kr['keyword'],
                        "weight": kr['weight']
                    })

            # 获取平台配置
            async with db.execute('''
                SELECT platform, is_enabled
                FROM category_platforms
                WHERE category_id = ?
            ''', (category_id,)) as cursor:
                platform_rows = await cursor.fetchall()
                for pr in platform_rows:
                    category["platforms"].append({
                        "platform": pr['platform'],
                        "is_enabled": bool(pr['is_enabled'])
                    })

            return category

    except Exception as e:
        add_log('error', f'获取分类详情失败: {e}')
        return None


async def get_categories_with_keywords() -> List[Dict]:
    """
    获取所有分类及其关键词（用于抓取任务）

    Returns:
        分类列表，每个分类包含关键词
    """
    categories = []
    try:
        async with get_db() as db:
            

            async with db.execute('''
                SELECT id, name, slug, is_active
                FROM categories
                WHERE is_active = 1
                ORDER BY sort_order ASC, id ASC
            ''') as cursor:
                rows = await cursor.fetchall()

            for r in rows:
                category = {
                    "id": r['id'],
                    "name": r['name'],
                    "slug": r['slug'],
                    "keywords": []
                }

                # 获取关键词
                async with db.execute('''
                    SELECT keyword
                    FROM category_keywords
                    WHERE category_id = ?
                    ORDER BY weight DESC, id ASC
                ''', (r['id'],)) as keyword_cursor:
                    keyword_rows = await keyword_cursor.fetchall()
                    category["keywords"] = [kr['keyword'] for kr in keyword_rows]

                categories.append(category)

    except Exception as e:
        add_log('error', f'获取分类和关键词失败: {e}')

    return categories


async def create_category(data: Dict) -> int:
    """
    创建分类

    Args:
        data: 分类数据，包含 name, slug, description, icon, color, keywords, platforms

    Returns:
        新创建的分类ID
    """
    try:
        async with get_db() as db:
            # 插入分类
            await db.execute('''
                INSERT INTO categories (name, slug, description, icon, color, is_active, sort_order)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                data.get('name'),
                data.get('slug'),
                data.get('description'),
                data.get('icon'),
                data.get('color'),
                data.get('is_active', True),
                data.get('sort_order', 0)
            ))

            # 获取新插入的ID
            async with db.execute("SELECT last_insert_rowid() as id") as cursor:
                row = await cursor.fetchone()
                category_id = row["id"]

            # 插入关键词
            if data.get('keywords'):
                for keyword in data['keywords']:
                    await db.execute('''
                        INSERT INTO category_keywords (category_id, keyword, weight)
                        VALUES (?, ?, ?)
                    ''', (category_id, keyword, 1))

            # 插入平台配置
            if data.get('platforms'):
                for platform in data['platforms']:
                    await db.execute('''
                        INSERT INTO category_platforms (category_id, platform, is_enabled)
                        VALUES (?, ?, ?)
                    ''', (category_id, platform, 1))

            await db.commit()
            add_log('success', f'创建分类成功: {data.get("name")}')
            return category_id

    except Exception as e:
        add_log('error', f'创建分类失败: {e}')
        raise


async def update_category(category_id: int, data: Dict) -> bool:
    """
    更新分类

    Args:
        category_id: 分类ID
        data: 要更新的数据

    Returns:
        是否成功
    """
    try:
        async with get_db() as db:
            # 构建更新SQL
            update_fields = []
            update_values = []

            for field in ['name', 'slug', 'description', 'icon', 'color', 'is_active', 'sort_order']:
                if field in data:
                    update_fields.append(f"{field} = ?")
                    update_values.append(data[field])

            if update_fields:
                update_values.append(category_id)
                await db.execute(f'''
                    UPDATE categories
                    SET {', '.join(update_fields)}
                    WHERE id = ?
                ''', update_values)

            await db.commit()
            add_log('success', f'更新分类成功: {category_id}')
            return True

    except Exception as e:
        add_log('error', f'更新分类失败: {e}')
        return False


async def delete_category(category_id: int) -> bool:
    """
    删除分类

    Args:
        category_id: 分类ID

    Returns:
        是否成功
    """
    try:
        async with get_db() as db:
            # 删除关键词（级联删除）
            await db.execute('DELETE FROM category_keywords WHERE category_id = ?', (category_id,))

            # 删除平台配置（级联删除）
            await db.execute('DELETE FROM category_platforms WHERE category_id = ?', (category_id,))

            # 删除分类
            await db.execute('DELETE FROM categories WHERE id = ?', (category_id,))

            await db.commit()
            add_log('success', f'删除分类成功: {category_id}')
            return True

    except Exception as e:
        add_log('error', f'删除分类失败: {e}')
        return False


async def update_category_keywords(category_id: int, keywords: List[str]) -> bool:
    """
    更新分类关键词

    Args:
        category_id: 分类ID
        keywords: 关键词列表

    Returns:
        是否成功
    """
    try:
        async with get_db() as db:
            # 删除旧关键词
            await db.execute('DELETE FROM category_keywords WHERE category_id = ?', (category_id,))

            # 插入新关键词
            for keyword in keywords:
                await db.execute('''
                    INSERT INTO category_keywords (category_id, keyword, weight)
                    VALUES (?, ?, ?)
                ''', (category_id, keyword, 1))

            await db.commit()
            add_log('success', f'更新分类关键词成功: {category_id}')
            return True

    except Exception as e:
        add_log('error', f'更新分类关键词失败: {e}')
        return False


async def update_category_platforms(category_id: int, platforms: List[str]) -> bool:
    """
    更新分类平台配置

    Args:
        category_id: 分类ID
        platforms: 启用的平台列表

    Returns:
        是否成功
    """
    try:
        async with get_db() as db:
            # 删除旧配置
            await db.execute('DELETE FROM category_platforms WHERE category_id = ?', (category_id,))

            # 插入新配置
            for platform in platforms:
                await db.execute('''
                    INSERT INTO category_platforms (category_id, platform, is_enabled)
                    VALUES (?, ?, ?)
                ''', (category_id, platform, 1))

            await db.commit()
            return True

    except Exception as e:
        add_log('error', f'更新分类平台失败: {e}')
        return False


async def get_category_platforms(category_id: int) -> List[Dict]:
    """
    获取分类的平台配置

    Args:
        category_id: 分类ID

    Returns:
        平台列表
    """
    platforms = []
    try:
        async with get_db() as db:
            
            async with db.execute('''
                SELECT platform, is_enabled FROM category_platforms
                WHERE category_id = ?
            ''', (category_id,)) as cursor:
                rows = await cursor.fetchall()
                platforms = [dict(r) for r in rows]

    except Exception as e:
        add_log('error', f'获取分类平台失败: {e}')

    return platforms


async def init_default_categories() -> int:
    """
    初始化默认分类

    Returns:
        创建的分类数量
    """
    try:
        async with get_db() as db:
            created_count = 0
            default_platforms = ['weibo', 'zhihu', 'douyin', 'xiaohongshu', 'toutiao']

            for cat_data in DEFAULT_CATEGORIES:
                # 检查是否已存在
                
                async with db.execute(
                    "SELECT id FROM categories WHERE slug = ?",
                    (cat_data['slug'],)
                ) as cursor:
                    existing = await cursor.fetchone()

                if existing:
                    continue

                # 插入分类
                await db.execute('''
                    INSERT INTO categories (name, slug, description, icon, color, is_active, sort_order)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    cat_data['name'],
                    cat_data['slug'],
                    cat_data['description'],
                    cat_data['icon'],
                    cat_data['color'],
                    1,
                    created_count
                ))

                # 获取新插入的ID
                async with db.execute("SELECT last_insert_rowid() as id") as cursor:
                    row = await cursor.fetchone()
                    category_id = row["id"]

                # 插入关键词
                for keyword in cat_data['keywords']:
                    await db.execute('''
                        INSERT INTO category_keywords (category_id, keyword, weight)
                        VALUES (?, ?, ?)
                    ''', (category_id, keyword, 1))

                # 插入平台配置
                for platform in default_platforms:
                    await db.execute('''
                        INSERT INTO category_platforms (category_id, platform, is_enabled)
                        VALUES (?, ?, ?)
                    ''', (category_id, platform, 1))

                created_count += 1

            await db.commit()

            if created_count > 0:
                add_log('success', f'初始化默认分类完成，共创建 {created_count} 个分类')
            else:
                add_log('info', '默认分类已存在，无需初始化')

            return created_count

    except Exception as e:
        add_log('error', f'初始化默认分类失败: {e}')
        return 0


async def get_topics_by_category(
    category_id: Optional[int] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    source: Optional[str] = None,
    offset: int = 0,
    limit: int = 50
) -> Dict:
    """
    按分类获取热点话题

    Args:
        category_id: 分类ID（可选）
        start_date: 起始日期 (YYYY-MM-DD)
        end_date: 结束日期 (YYYY-MM-DD)
        source: 数据源筛选
        offset: 偏移量
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
        async with get_db() as db:
            

            # 构建 WHERE 条件
            where_conditions = []
            params = []

            if category_id:
                where_conditions.append("category_id = ?")
                params.append(category_id)
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
                    "created_at": r['created_at'],
                    "category_id": r.get('category_id'),
                    "matched_keyword": r.get('matched_keyword')
                })

    except Exception as e:
        add_log('error', f'按分类获取热点失败: {e}')

    return {
        "topics": topics,
        "total": total,
        "offset": offset,
        "limit": limit
    }


# ==================== 原始新闻表 (raw_news) 操作 ====================

async def save_raw_news_to_db(news_list: List[Dict], category_id: int = None) -> int:
    """
    保存爬取的原始新闻到数据库（异步）
    使用 INSERT OR IGNORE 避免重复

    Args:
        news_list: 新闻列表，每个元素包含 title, link, source 等
        category_id: 可选的分类ID

    Returns:
        保存的记录数
    """
    count = 0
    try:
        async with get_db() as db:
            for news in news_list:
                try:
                    await db.execute('''
                        INSERT OR IGNORE INTO raw_news (
                            title, link, source, category_id, created_at
                        ) VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
                    ''', (
                        news.get('title', ''),
                        news.get('link', ''),
                        news.get('source', ''),
                        category_id
                    ))
                    if db.total_changes > 0:
                        count += 1
                except Exception as e:
                    add_log('warning', f'保存单条新闻失败: {e}')

            await db.commit()
            add_log('success', f'原始新闻保存完成，新增 {count} 条')

    except Exception as e:
        add_log('error', f'批量保存原始新闻失败: {e}')

    return count


async def get_unanalyzed_news(limit: int = 50, max_fail_count: int = 3) -> List[Dict]:
    """
    获取未分析的或可重试的新闻

    Args:
        limit: 获取数量限制
        max_fail_count: 最大失败次数限制

    Returns:
        未分析的新闻列表
    """
    news_list = []
    try:
        async with get_db() as db:
            
            async with db.execute('''
                SELECT * FROM raw_news
                WHERE analyzed = 0
                  AND (skip_reason IS NULL OR skip_reason = '')
                  AND analyze_fail_count <= ?
                  AND created_at > datetime('now', '-7 days')
                ORDER BY created_at DESC
                LIMIT ?
            ''', (max_fail_count, limit)) as cursor:
                rows = await cursor.fetchall()

                for r in rows:
                    news_list.append({
                        'id': r['id'],
                        'title': r['title'],
                        'link': r['link'],
                        'source': r['source'],
                        'category_id': r['category_id'],
                        'analyze_fail_count': r['analyze_fail_count']
                    })

    except Exception as e:
        add_log('error', f'获取未分析新闻失败: {e}')

    return news_list


async def update_news_analysis(news_id: int, ai_score: float, ai_comment: str,
                               analyzed: bool = True, skip_reason: str = None) -> bool:
    """
    更新新闻的分析结果

    Args:
        news_id: 新闻ID
        ai_score: AI评分 (0-10)
        ai_comment: AI评论
        analyzed: 是否分析完成
        skip_reason: 跳过原因（如果分析失败）

    Returns:
        是否更新成功
    """
    try:
        async with get_db() as db:
            if analyzed:
                await db.execute('''
                    UPDATE raw_news
                    SET analyzed = 1,
                        ai_score = ?,
                        ai_comment = ?,
                        last_analyzed_at = CURRENT_TIMESTAMP,
                        skip_reason = NULL
                    WHERE id = ?
                ''', (ai_score, ai_comment, news_id))
            else:
                # 增加失败计数
                await db.execute('''
                    UPDATE raw_news
                    SET analyze_fail_count = analyze_fail_count + 1,
                        skip_reason = ?,
                        last_analyzed_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                ''', (skip_reason, news_id))

            await db.commit()
            return True

    except Exception as e:
        add_log('error', f'更新新闻分析失败: {e}')
        return False


async def get_top_scoring_news(hours: int = 48, limit: int = 50,
                                 min_score: float = 0.0) -> List[Dict]:
    """
    获取指定时间内评分最高的新闻

    Args:
        hours: 时间范围（小时）
        limit: 返回数量限制
        min_score: 最低分数要求

    Returns:
        评分最高的新闻列表
    """
    news_list = []
    try:
        async with get_db() as db:
            
            async with db.execute('''
                SELECT id, title, link, source,
                       ai_score, ai_comment, category_id, created_at
                FROM raw_news
                WHERE analyzed = 1
                  AND ai_score >= ?
                  AND created_at > datetime('now', '-' || ? || ' hours')
                ORDER BY ai_score DESC, created_at DESC
                LIMIT ?
            ''', (min_score, hours, limit)) as cursor:
                rows = await cursor.fetchall()

                for r in rows:
                    news_list.append({
                        'id': r['id'],
                        'title': r['title'],
                        'link': r['link'],
                        'source': r['source'],
                        'ai_score': r['ai_score'],
                        'ai_comment': r['ai_comment'],
                        'category_id': r['category_id'],
                        'created_at': r['created_at']
                    })

    except Exception as e:
        add_log('error', f'获取高评分新闻失败: {e}')

    return news_list


async def save_hot_topics(topics: List[Dict]) -> int:
    """
    保存精选的热点新闻到 hot_topics 表
    先清空旧数据，再插入新数据

    Args:
        topics: 精选的热点话题列表，包含 ai_score, ai_comment 等字段

    Returns:
        保存的记录数
    """
    count = 0
    try:
        async with get_db() as db:
            # 清空旧的 hot_topics
            await db.execute('DELETE FROM hot_topics')

            # 插入新的热点话题
            for topic in topics:
                await db.execute('''
                    INSERT INTO hot_topics (
                        title, link, source, ai_score, ai_comment,
                        category_id, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                ''', (
                    topic.get('title', ''),
                    topic.get('link', ''),
                    topic.get('source', ''),
                    topic.get('ai_score'),
                    topic.get('ai_comment', ''),
                    topic.get('category_id')
                ))
                count += 1

            await db.commit()
            add_log('success', f'热点话题更新完成，共 {count} 条')

    except Exception as e:
        add_log('error', f'保存热点话题失败: {e}')

    return count


async def get_raw_news_stats() -> Dict:
    """
    获取原始新闻统计信息

    Returns:
        统计数据字典
    """
    stats = {
        'total': 0,
        'analyzed': 0,
        'unanalyzed': 0,
        'skipped': 0,
        'avg_score': 0.0
    }
    try:
        async with get_db() as db:
            async with db.execute('SELECT COUNT(*) as count FROM raw_news') as cursor:
                stats['total'] = (await cursor.fetchone())['count']

            async with db.execute('''
                SELECT COUNT(*) as count FROM raw_news WHERE analyzed = 1
            ''') as cursor:
                stats['analyzed'] = (await cursor.fetchone())['count']

            async with db.execute('''
                SELECT COUNT(*) as count FROM raw_news
                WHERE analyzed = 0 AND skip_reason IS NOT NULL AND skip_reason != ''
            ''') as cursor:
                stats['skipped'] = (await cursor.fetchone())['count']

            stats['unanalyzed'] = stats['total'] - stats['analyzed'] - stats['skipped']

            async with db.execute('''
                SELECT AVG(ai_score) as avg_score FROM raw_news
                WHERE analyzed = 1 AND ai_score IS NOT NULL
            ''') as cursor:
                row = await cursor.fetchone()
                stats['avg_score'] = row['avg_score'] if row['avg_score'] else 0.0

    except Exception as e:
        add_log('error', f'获取原始新闻统计失败: {e}')

    return stats

