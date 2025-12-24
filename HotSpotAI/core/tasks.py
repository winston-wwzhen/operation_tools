"""
定时任务模块
包含三个独立的定时任务：
1. 爬虫任务 - 每小时执行（0-6点跳过）
2. AI 分析任务 - 每2小时执行
3. 热点精选任务 - 每小时执行
"""
import asyncio
from datetime import datetime
from typing import List, Dict
from core.config import add_log
from core.database import (
    save_raw_news_to_db,
    get_unanalyzed_news,
    update_news_analysis,
    get_top_scoring_news,
    save_hot_topics,
    get_raw_news_stats
)
from core.llm import analyze_news_batch, select_hot_topics


def is_night_hours() -> bool:
    """检查是否在夜间（0-6点）"""
    current_hour = datetime.now().hour
    return 0 <= current_hour < 6


def get_daytime_cron() -> str:
    """
    根据当前时间返回合适的 cron 表达式
    夜间（0-6点）：不执行
    白天（6-24点）：正常执行
    """
    current_hour = datetime.now().hour
    if 6 <= current_hour < 12:
        # 早上：每2小时
        return "0 */2 6-11 * *"
    elif 12 <= current_hour < 18:
        # 下午：每1小时
        return "0 */1 12-17 * *"
    else:
        # 晚上：每2小时
        return "0 */2 18-23 * *"


# ==================== 任务1: 爬虫任务 ====================

async def run_scraper_task(category_id: int = None) -> Dict:
    """
    爬虫定时任务
    - 每小时执行一次
    - 0-6点跳过
    - 爬取新闻并存储到 raw_news 表

    包含两种类型的新闻：
    1. 热榜新闻：直接抓取平台热榜（微博热搜、知乎热榜等），不使用关键词过滤
    2. 分类新闻：根据分类关键词进行定向抓取

    Args:
        category_id: 可选的分类ID（如果指定，则只爬取该分类的新闻）

    Returns:
        任务执行结果
    """
    result = {
        'success': False,
        'hot_ranking_count': 0,  # 热榜新闻数量
        'category_count': 0,      # 分类新闻数量
        'scraped_count': 0,       # 总数量
        'message': ''
    }

    try:
        # 夜间跳过
        if is_night_hours():
            result['message'] = '夜间时段，跳过爬虫任务'
            add_log('info', '夜间时段，跳过爬虫任务')
            return result

        add_log('info', f'开始执行爬虫任务 (分类ID: {category_id or "全部"})')

        from scrapers.factory import create_scraper, ScraperFactory

        total_scraped = 0

        # ========== 第一步：爬取热榜新闻（如果没有指定分类ID） ==========
        if category_id is None:
            add_log('info', '========== 开始爬取热榜新闻 ==========')
            hot_ranking_count = 0

            # 获取所有可用平台
            available_platforms = ScraperFactory.get_available_platforms()
            add_log('info', f'可用平台: {", ".join(available_platforms)}')

            for platform in available_platforms:
                try:
                    platform_scraper = create_scraper(platform)
                    if platform_scraper is None:
                        continue

                    # 直接抓取热榜（不使用关键词过滤）
                    add_log('info', f'正在爬取 [{platform}] 热榜...')
                    topics = await platform_scraper.scrape(limit=20)

                    if topics:
                        # 保存到 raw_news，category_id 为 NULL 表示热榜新闻
                        count = await save_raw_news_to_db(topics, category_id=None)
                        hot_ranking_count += count
                        add_log('success', f'[{platform}] 热榜爬取 {count} 条')

                except Exception as e:
                    add_log('warning', f'[{platform}] 热榜爬取失败: {e}')

            result['hot_ranking_count'] = hot_ranking_count
            total_scraped += hot_ranking_count
            add_log('success', f'========== 热榜新闻爬取完成，共 {hot_ranking_count}条 ==========')

        # ========== 第二步：爬取分类新闻 ==========
        add_log('info', '========== 开始爬取分类新闻 ==========')

        # 获取启用的分类（如果指定了分类ID则只爬取该分类）
        if category_id:
            from core.database import get_category_by_id
            category = await get_category_by_id(category_id)
            categories = [category] if category else []
        else:
            from core.database import get_categories_with_keywords
            categories = await get_categories_with_keywords()

        category_count = 0
        for cat in categories:
            try:
                cat_id = cat['id']
                cat_name = cat['name']
                keywords = [k['keyword'] for k in cat.get('keywords', [])]

                # 获取该分类配置的平台
                from core.database import get_category_platforms
                platforms = await get_category_platforms(cat_id)
                enabled_platforms = [p['platform'] for p in platforms if p.get('is_enabled')]

                add_log('info', f'爬取分类 [{cat_name}]，关键词: {", ".join(keywords[:3])}')

                # 对每个启用的平台进行爬取
                for platform in enabled_platforms or ['weibo', 'zhihu']:
                    try:
                        platform_scraper = create_scraper(platform)
                        # 使用关键词搜索
                        topics = await platform_scraper.scrape_by_keywords(keywords, limit=20)
                        # 保存到 raw_news
                        count = await save_raw_news_to_db(topics, cat_id)
                        category_count += count
                        add_log('success', f'[{platform}] 分类 [{cat_name}] 爬取 {count} 条')
                    except Exception as e:
                        add_log('warning', f'[{platform}] 分类 [{cat_name}] 爬取失败: {e}')

            except Exception as e:
                add_log('warning', f'分类 [{cat.get("name", "未知")}] 处理失败: {e}')

        result['category_count'] = category_count
        total_scraped += category_count
        add_log('success', f'========== 分类新闻爬取完成，共 {category_count}条 ==========')

        # 更新最终结果
        result['scraped_count'] = total_scraped
        result['success'] = True

        # 组合消息
        parts = []
        if result['hot_ranking_count'] > 0:
            parts.append(f'热榜 {result["hot_ranking_count"]}条')
        if result['category_count'] > 0:
            parts.append(f'分类 {result["category_count"]}条')
        result['message'] = f'爬虫任务完成，共 {total_scraped} 条新闻 ({", ".join(parts)})'
        add_log('success', result['message'])

    except Exception as e:
        result['message'] = f'爬虫任务失败: {e}'
        add_log('error', result['message'])

    return result


# ==================== 任务2: AI 分析任务 ====================

async def run_analyzer_task(batch_size: int = 20) -> Dict:
    """
    AI 分析定时任务
    - 每2小时执行一次
    - 处理未分析的新闻
    - 批量处理以节省 token

    Args:
        batch_size: 每批处理的数量

    Returns:
        任务执行结果
    """
    result = {
        'success': False,
        'analyzed_count': 0,
        'failed_count': 0,
        'skipped_count': 0,
        'message': ''
    }

    try:
        # 夜间降低频率
        if is_night_hours():
            result['message'] = '夜间时段，跳过 AI 分析任务'
            add_log('info', '夜间时段，跳过 AI 分析任务')
            return result

        add_log('info', '开始执行 AI 分析任务')

        # 获取未分析的新闻（最多 50 条）
        unanalyzed = await get_unanalyzed_news(limit=50)

        if not unanalyzed:
            result['message'] = '没有待分析的新闻'
            add_log('info', result['message'])
            result['success'] = True
            return result

        add_log('info', f'获取到 {len(unanalyzed)} 条待分析新闻')

        # 分批处理（每批 20 条）
        analyzed_count = 0
        failed_count = 0
        skipped_count = 0

        for i in range(0, len(unanalyzed), batch_size):
            batch = unanalyzed[i:i + batch_size]
            add_log('info', f'正在分析第 {i // batch_size + 1} 批，共 {len(batch)} 条')

            try:
                # 批量分析
                analysis_results = await analyze_news_batch(batch)

                # 更新分析结果
                for news_id, analysis in zip([n['id'] for n in batch], analysis_results):
                    if analysis.get('success'):
                        await update_news_analysis(
                            news_id=news_id,
                            ai_score=analysis.get('score', 0),
                            ai_comment=analysis.get('comment', ''),
                            analyzed=True
                        )
                        analyzed_count += 1
                    else:
                        # 分析失败，记录原因
                        fail_reason = analysis.get('error', '分析失败')
                        # 如果失败次数超过 4 次，标记为跳过
                        news = next((n for n in batch if n['id'] == news_id), None)
                        if news and news.get('analyze_fail_count', 0) >= 4:
                            await update_news_analysis(
                                news_id=news_id,
                                analyzed=False,
                                skip_reason=f'失败次数过多: {fail_reason}'
                            )
                            skipped_count += 1
                        else:
                            await update_news_analysis(
                                news_id=news_id,
                                analyzed=False,
                                skip_reason=fail_reason
                            )
                            failed_count += 1

                add_log('success', f'第 {i // batch_size + 1} 批分析完成')

            except Exception as e:
                add_log('error', f'批次分析失败: {e}')
                # 整批失败，记录失败原因
                for news in batch:
                    await update_news_analysis(
                        news_id=news['id'],
                        analyzed=False,
                        skip_reason=f'批次处理失败: {e}'
                    )
                failed_count += len(batch)

        result['success'] = True
        result['analyzed_count'] = analyzed_count
        result['failed_count'] = failed_count
        result['skipped_count'] = skipped_count
        result['message'] = f'AI 分析完成: 成功 {analyzed_count}，失败 {failed_count}，跳过 {skipped_count}'
        add_log('success', result['message'])

    except Exception as e:
        result['message'] = f'AI 分析任务失败: {e}'
        add_log('error', result['message'])

    return result


# ==================== 任务3: 热点精选任务 ====================

async def run_selector_task(hours: int = 48, top_count: int = 50, final_count: int = 20) -> Dict:
    """
    热点精选定时任务
    - 每小时执行一次
    - 从 48 小时内的新闻中选出 20 条热点

    Args:
        hours: 时间范围（小时）
        top_count: 候选数量
        final_count: 最终精选数量

    Returns:
        任务执行结果
    """
    result = {
        'success': False,
        'selected_count': 0,
        'message': ''
    }

    try:
        # 夜间跳过
        if is_night_hours():
            result['message'] = '夜间时段，跳过热点精选任务'
            add_log('info', '夜间时段，跳过热点精选任务')
            return result

        add_log('info', f'开始执行热点精选任务（{hours}小时内选{final_count}条）')

        # 获取高评分新闻（按规则排序）
        top_news = await get_top_scoring_news(hours=hours, limit=top_count, min_score=3.0)

        if not top_news:
            result['message'] = '没有足够的候选新闻'
            add_log('warning', result['message'])
            return result

        add_log('info', f'获取到 {len(top_news)} 条候选新闻')

        # 使用 AI 进行最终精选（考虑时效性和热度）
        selected = await select_hot_topics(top_news, final_count)

        if selected:
            # 保存到 hot_topics 表
            count = await save_hot_topics(selected)

            # 更新 runtime_state 中的 hot_topics
            from core import runtime_state
            runtime_state['hot_topics'] = selected

            result['success'] = True
            result['selected_count'] = count
            result['message'] = f'热点精选完成，共 {count} 条'
            add_log('success', result['message'])
        else:
            result['message'] = 'AI 精选失败，使用规则排序'
            add_log('warning', result['message'])

            # 失败时使用规则排序（取前 N 条）
            fallback_selected = top_news[:final_count]
            formatted_topics = []
            for news in fallback_selected:
                formatted_topics.append({
                    'title': news['title'],
                    'link': news['link'],
                    'source': news['source'],
                    'ai_score': news.get('ai_score', 0),
                    'ai_comment': news.get('ai_comment', ''),
                    'category_id': news.get('category_id')
                })

            count = await save_hot_topics(formatted_topics)

            from core import runtime_state
            runtime_state['hot_topics'] = formatted_topics

            result['success'] = True
            result['selected_count'] = count
            result['message'] = f'热点精选完成（规则排序），共 {count} 条'

    except Exception as e:
        result['message'] = f'热点精选任务失败: {e}'
        add_log('error', result['message'])

    return result


# ==================== 统计信息 ====================

async def get_tasks_stats() -> Dict:
    """
    获取任务统计信息

    Returns:
        统计数据
    """
    stats = await get_raw_news_stats()
    stats['is_night_hours'] = is_night_hours()
    stats['current_time'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    return stats
