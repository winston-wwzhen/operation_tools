"""
数据库初始化和基础配置模块
"""
from core.db_pool import get_db
from core.config import add_log


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
                    heat INTEGER DEFAULT 0,
                    tags TEXT,
                    comment TEXT,
                    category_id INTEGER,
                    matched_keyword TEXT,
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

            # 原始新闻表（raw_news）用于爬虫存储
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

            # 创建索引
            await _create_indexes(db)

            # 创建触发器
            await _create_triggers(db)

            # 数据库迁移
            await _run_migrations(db)

            await db.commit()

        add_log('info', '数据库初始化检查完成')
    except Exception as e:
        add_log('error', f'数据库初始化失败: {e}')


async def _create_indexes(db):
    """创建数据库索引"""
    indexes = [
        # hot_topics 索引
        ('idx_created_at', 'hot_topics', 'created_at DESC'),
        ('idx_source', 'hot_topics', 'source'),
        ('idx_hot_topics_category_id', 'hot_topics', 'category_id'),
        # users 索引
        ('idx_users_username', 'users', 'username'),
        ('idx_users_email', 'users', 'email'),
        # user_articles 索引
        ('idx_user_articles_user_id', 'user_articles', 'user_id'),
        ('idx_user_articles_share_token', 'user_articles', 'share_token'),
        ('idx_user_articles_created_at', 'user_articles', 'created_at DESC'),
        # wechat_accounts 索引
        ('idx_wechat_accounts_user_id', 'wechat_accounts', 'user_id'),
        ('idx_wechat_accounts_is_active', 'wechat_accounts', 'is_active'),
        # wechat_publish_log 索引
        ('idx_wechat_publish_log_user_id', 'wechat_publish_log', 'user_id'),
        ('idx_wechat_publish_log_article_id', 'wechat_publish_log', 'article_id'),
        ('idx_wechat_publish_log_created_at', 'wechat_publish_log', 'created_at DESC'),
        # categories 索引
        ('idx_category_keywords_category_id', 'category_keywords', 'category_id'),
        ('idx_category_keywords_keyword', 'category_keywords', 'keyword'),
        ('idx_category_platforms_category_id', 'category_platforms', 'category_id'),
        ('idx_categories_is_active', 'categories', 'is_active'),
        # raw_news 索引
        ('idx_raw_news_link', 'raw_news', 'link'),
        ('idx_raw_news_source', 'raw_news', 'source'),
        ('idx_raw_news_analyzed', 'raw_news', 'analyzed'),
        ('idx_raw_news_created_at', 'raw_news', 'created_at DESC'),
        ('idx_raw_news_ai_score', 'raw_news', 'ai_score DESC'),
        ('idx_raw_news_category_id', 'raw_news', 'category_id'),
    ]

    for name, table, columns in indexes:
        await db.execute(f'CREATE INDEX IF NOT EXISTS {name} ON {table}({columns})')


async def _create_triggers(db):
    """创建更新时间触发器"""
    triggers = [
        ('update_users_timestamp', 'users'),
        ('update_user_articles_timestamp', 'user_articles'),
        ('update_wechat_accounts_timestamp', 'wechat_accounts'),
        ('update_categories_timestamp', 'categories'),
    ]

    for name, table in triggers:
        await db.execute(f'''
            CREATE TRIGGER IF NOT EXISTS {name}
            AFTER UPDATE ON {table}
            BEGIN
                UPDATE {table} SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
            END
        ''')


async def _run_migrations(db):
    """运行数据库迁移"""
    # 为已存在的 users 表添加 is_admin 字段
    try:
        await db.execute('ALTER TABLE users ADD COLUMN is_admin INTEGER DEFAULT 0')
        await db.commit()
        add_log('info', '数据库迁移完成：已添加 is_admin 字段')
    except Exception as e:
        if 'duplicate column' not in str(e).lower():
            raise

    # 为已存在的 user_articles 表添加微信相关字段
    try:
        await db.execute('ALTER TABLE user_articles ADD COLUMN wechat_draft_id TEXT')
        await db.execute('ALTER TABLE user_articles ADD COLUMN wechat_publish_status TEXT DEFAULT "draft"')
        await db.commit()
        add_log('info', '数据库迁移完成：已添加微信相关字段')
    except Exception as e:
        if 'duplicate column' not in str(e).lower():
            raise

    # 为 hot_topics 表添加分类相关字段
    try:
        await db.execute('ALTER TABLE hot_topics ADD COLUMN category_id INTEGER')
        await db.execute('ALTER TABLE hot_topics ADD COLUMN matched_keyword TEXT')
        await db.commit()
        add_log('info', '数据库迁移完成：已添加分类相关字段')
    except Exception as e:
        if 'duplicate column' not in str(e).lower():
            raise
