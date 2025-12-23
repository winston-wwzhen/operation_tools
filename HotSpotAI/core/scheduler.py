"""
定时任务调度模块
使用 APScheduler 管理定时任务
"""
import asyncio
import traceback
from datetime import datetime
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from core.config import add_log, runtime_state, get_config
# 引入所有爬虫（包括新增的小红书和头条）
from scrapers import (
    scrape_weibo,
    scrape_baidu,
    scrape_zhihu_playwright,
    scrape_douyin_playwright,
    scrape_xiaohongshu,
    scrape_toutiao
)
from core.llm import analyze_hot_topics
# 引入数据库保存功能
from core.database import save_topics_to_db

scheduler = AsyncIOScheduler()


async def run_task_logic():
    """执行核心任务：全网抓取 -> 智能分析 -> 数据库存储"""
    if runtime_state["isRunning"]:
        return

    runtime_state["isRunning"] = True
    runtime_state["lastRunTime"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    add_log('info', '>>> 开始全网热点聚合任务')

    try:
        limit = int(get_config("topicLimit", 10))

        # 并发执行所有平台的抓取
        results = await asyncio.gather(
            scrape_weibo(limit),
            scrape_baidu(limit),
            scrape_zhihu_playwright(limit),
            scrape_douyin_playwright(limit),
            scrape_xiaohongshu(limit),
            scrape_toutiao(limit),
            return_exceptions=True
        )

        all_topics = []
        for res in results:
            if isinstance(res, list):
                all_topics.extend(res)
            else:
                add_log('error', f"抓取异常: {res}")

        add_log('success', f"原始数据抓取完成，共 {len(all_topics)} 条，准备分析...")

        if all_topics:
            # 这里的 analyze_hot_topics 负责去重、评分和点评
            analyzed_topics = await analyze_hot_topics(all_topics)

            if analyzed_topics:
                # 1. 更新内存状态 (供当前 API 立即读取)
                runtime_state["hot_topics"] = analyzed_topics
                add_log('success', f"全网热点分析完成！Top1: {analyzed_topics[0]['title']}")

                # 2. 保存到数据库 (持久化，防止重启丢失)
                await save_topics_to_db(analyzed_topics)
            else:
                add_log('warning', "分析结果为空")
        else:
            add_log('warning', "未抓取到任何数据")

    except Exception as e:
        add_log('error', f"任务执行异常: {str(e)}")
        traceback.print_exc()
    finally:
        runtime_state["isRunning"] = False
        add_log('info', '<<< 任务结束')

        # 更新下次运行时间显示
        if scheduler.get_jobs():
            job = scheduler.get_jobs()[0]
            if job.next_run_time:
                runtime_state["nextRunTime"] = job.next_run_time.strftime("%Y-%m-%d %H:%M:%S")


def update_scheduler():
    """根据配置更新定时任务"""
    scheduler.remove_all_jobs()
    auto_run = get_config("autoRun")
    cron_exp = get_config("scheduleCron")

    if auto_run and cron_exp:
        try:
            scheduler.add_job(run_task_logic, CronTrigger.from_crontab(cron_exp), id="auto_task")
            add_log('info', f"定时任务已更新: {cron_exp}")
        except Exception as e:
            add_log('error', f"Cron 格式错误: {e}")


def start_scheduler():
    scheduler.start()
    update_scheduler()
