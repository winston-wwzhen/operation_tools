import sqlite3
import json
from datetime import datetime
from config_manager import add_log

DB_FILE = "data.db"

def init_db():
    """初始化数据库表结构"""
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        # 创建热点表
        # tags 字段我们将存为 JSON 字符串
        cursor.execute('''
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
        conn.commit()
        conn.close()
        add_log('info', '数据库初始化检查完成')
    except Exception as e:
        add_log('error', f'数据库初始化失败: {e}')

def save_topics_to_db(topics):
    """保存一批热点数据"""
    if not topics:
        return

    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        count = 0

        for t in topics:
            # 将 list 类型的 tags 转换为 JSON 字符串存储
            tags_json = json.dumps(t.get('tags', []), ensure_ascii=False)

            cursor.execute('''
                INSERT INTO hot_topics (title, link, source, heat, tags, comment, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                t.get('title'),
                t.get('link'),
                t.get('source'),
                t.get('heat', 0),
                tags_json,
                t.get('comment', ''),
                timestamp
            ))
            count += 1

        conn.commit()
        conn.close()
        add_log('success', f'已将 {count} 条数据保存至数据库')
    except Exception as e:
        add_log('error', f'保存数据至数据库失败: {e}')

def load_latest_topics_from_db(limit=50):
    """
    加载最近一次抓取的数据
    策略：找到最近的一个 created_at 时间点，加载该时间点的所有数据
    """
    topics = []
    try:
        conn = sqlite3.connect(DB_FILE)
        conn.row_factory = sqlite3.Row # 让查询结果可以通过列名访问
        cursor = conn.cursor()

        # 1. 查最近的时间点
        cursor.execute("SELECT created_at FROM hot_topics ORDER BY id DESC LIMIT 1")
        row = cursor.fetchone()

        if row:
            latest_time = row['created_at']
            # 2. 查该时间点的所有数据
            cursor.execute('''
                SELECT * FROM hot_topics 
                WHERE created_at = ? 
                ORDER BY heat DESC
            ''', (latest_time,))

            rows = cursor.fetchall()
            for r in rows:
                topics.append({
                    "title": r['title'],
                    "link": r['link'],
                    "source": r['source'],
                    "heat": r['heat'],
                    "tags": json.loads(r['tags']), # 还原为 list
                    "comment": r['comment']
                })

            add_log('info', f'从数据库恢复了 {len(topics)} 条历史记录 ({latest_time})')

        conn.close()
    except Exception as e:
        add_log('error', f'读取数据库失败: {e}')

    return topics