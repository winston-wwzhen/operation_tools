"""
原始新闻 (raw_news) 数据库操作模块
用于爬虫存储原始数据
"""
from typing import List, Dict
from core.db_pool import get_db
from core.config import add_log


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
