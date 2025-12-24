"""
定时任务调度模块
使用 APScheduler 管理三个独立的定时任务：
1. 爬虫任务 - 每小时执行（0-6点跳过）
2. AI 分析任务 - 每2小时执行
3. 热点精选任务 - 每小时执行
"""
import asyncio
import traceback
from datetime import datetime
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from core.config import add_log, runtime_state, get_config
from core.tasks import run_scraper_task, run_analyzer_task, run_selector_task, get_tasks_stats

scheduler = AsyncIOScheduler()


async def run_scraper_job():
    """爬虫定时任务 - 每小时执行"""
    if runtime_state.get("scraper_running", False):
        add_log('warning', '爬虫任务运行中，跳过')
        return

    runtime_state["scraper_running"] = True
    runtime_state["lastRunTime"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    add_log('info', '>>> 开始爬虫任务')

    try:
        result = await run_scraper_task()
        if result.get('success'):
            runtime_state['last_scraper_count'] = result.get('scraped_count', 0)
            runtime_state['last_hot_ranking_count'] = result.get('hot_ranking_count', 0)
            runtime_state['last_category_count'] = result.get('category_count', 0)
            add_log('success', f"爬虫任务完成，新增 {result.get('scraped_count', 0)} 条")
        else:
            add_log('info', f"爬虫任务: {result.get('message', '')}")
    except Exception as e:
        add_log('error', f"爬虫任务异常: {str(e)}")
        traceback.print_exc()
    finally:
        runtime_state["scraper_running"] = False
        add_log('info', '<<< 爬虫任务结束')


async def run_analyzer_job():
    """AI 分析定时任务 - 每2小时执行"""
    if runtime_state.get("analyzer_running", False):
        add_log('warning', 'AI 分析任务运行中，跳过')
        return

    runtime_state["analyzer_running"] = True
    add_log('info', '>>> 开始 AI 分析任务')

    try:
        result = await run_analyzer_task()
        if result.get('success'):
            runtime_state['last_analyzer_count'] = result.get('analyzed_count', 0)
            add_log('success', f"AI 分析完成: 成功 {result.get('analyzed_count', 0)}，"
                          f"失败 {result.get('failed_count', 0)}，"
                          f"跳过 {result.get('skipped_count', 0)}")
        else:
            add_log('info', f"AI 分析任务: {result.get('message', '')}")
    except Exception as e:
        add_log('error', f"AI 分析任务异常: {str(e)}")
        traceback.print_exc()
    finally:
        runtime_state["analyzer_running"] = False
        add_log('info', '<<< AI 分析任务结束')


async def run_selector_job():
    """热点精选定时任务 - 每小时执行"""
    if runtime_state.get("selector_running", False):
        add_log('warning', '热点精选任务运行中，跳过')
        return

    runtime_state["selector_running"] = True
    add_log('info', '>>> 开始热点精选任务')

    try:
        result = await run_selector_task()
        if result.get('success'):
            runtime_state['last_selector_count'] = result.get('selected_count', 0)
            add_log('success', f"热点精选完成，共 {result.get('selected_count', 0)} 条")
        else:
            add_log('info', f"热点精选任务: {result.get('message', '')}")
    except Exception as e:
        add_log('error', f"热点精选任务异常: {str(e)}")
        traceback.print_exc()
    finally:
        runtime_state["selector_running"] = False
        add_log('info', '<<< 热点精选任务结束')


async def run_full_pipeline():
    """
    手动触发完整流程（用于立即刷新）
    依次执行：爬虫 -> AI 分析 -> 热点精选
    """
    if runtime_state.get("isRunning", False):
        add_log('warning', '任务运行中，跳过')
        return

    runtime_state["isRunning"] = True
    runtime_state["lastRunTime"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    add_log('info', '>>> 开始手动完整流程')

    try:
        # 1. 爬虫任务
        add_log('info', '步骤 1/3: 执行爬虫任务')
        scraper_result = await run_scraper_task()
        add_log('info', f"爬虫完成: {scraper_result.get('message', '')}")

        # 2. AI 分析任务
        add_log('info', '步骤 2/3: 执行 AI 分析任务')
        analyzer_result = await run_analyzer_task()
        add_log('info', f"分析完成: {analyzer_result.get('message', '')}")

        # 3. 热点精选任务
        add_log('info', '步骤 3/3: 执行热点精选任务')
        selector_result = await run_selector_task()
        add_log('info', f"精选完成: {selector_result.get('message', '')}")

        add_log('success', '完整流程执行完成')

    except Exception as e:
        add_log('error', f"完整流程异常: {str(e)}")
        traceback.print_exc()
    finally:
        runtime_state["isRunning"] = False
        add_log('info', '<<< 完整流程结束')

        # 更新下次运行时间
        jobs = scheduler.get_jobs()
        if jobs:
            job = jobs[0]
            if job.next_run_time:
                runtime_state["nextRunTime"] = job.next_run_time.strftime("%Y-%m-%d %H:%M:%S")


def update_scheduler():
    """根据配置更新定时任务"""
    # 获取统计信息
    try:
        stats = asyncio.get_event_loop().run_until_complete(get_tasks_stats())
        runtime_state['task_stats'] = stats
    except:
        runtime_state['task_stats'] = {}

    scheduler.remove_all_jobs()
    auto_run = get_config("autoRun", True)

    if not auto_run:
        add_log('info', '自动运行已禁用')
        return

    try:
        # 任务1: 爬虫任务 - 每小时执行（避开夜间 0-6 点）
        scheduler.add_job(
            run_scraper_job,
            CronTrigger.from_crontab("0 6-23 * * *"),  # 每小时的第0分钟，6-23点
            id="scraper_task"
        )
        add_log('info', "爬虫任务: 每小时执行 (6-23点)")

        # 任务2: AI 分析任务 - 每2小时执行
        scheduler.add_job(
            run_analyzer_job,
            CronTrigger.from_crontab("0 */2 * * *"),  # 每2小时的第0分钟
            id="analyzer_task"
        )
        add_log('info', "AI 分析任务: 每2小时执行")

        # 任务3: 热点精选任务 - 每小时执行（避开夜间 0-6 点）
        scheduler.add_job(
            run_selector_job,
            CronTrigger.from_crontab("30 6-23 * * *"),  # 每小时第30分钟，6-23点
            id="selector_task"
        )
        add_log('info', "热点精选任务: 每小时执行 (6-23点)")

        # 更新下次运行时间
        jobs = scheduler.get_jobs()
        if jobs:
            next_times = []
            for job in jobs:
                if job.next_run_time:
                    next_times.append(job.next_run_time.strftime("%H:%M"))
            if next_times:
                runtime_state["nextRunTime"] = f"今天 {', '.join(next_times)}"

    except Exception as e:
        add_log('error', f"定时任务配置错误: {e}")


def start_scheduler():
    """启动调度器"""
    scheduler.start()
    update_scheduler()
    add_log('info', '调度器已启动')
