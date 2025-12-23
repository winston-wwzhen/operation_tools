import asyncio
import traceback
from datetime import datetime
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from config_manager import add_log, runtime_state, get_config
from scrapers import scrape_weibo, scrape_baidu, scrape_zhihu_playwright, scrape_douyin_playwright
from llm_engine import analyze_hot_topics

scheduler = AsyncIOScheduler()

async def run_task_logic():
    """执行核心任务：全网抓取 -> 智能分析"""
    if runtime_state["isRunning"]: 
        return
    
    runtime_state["isRunning"] = True
    runtime_state["lastRunTime"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    add_log('info', '>>> 开始全网热点聚合任务')
    
    try:
        limit = int(get_config("topicLimit", 10))
        
        # 并发执行所有抓取
        results = await asyncio.gather(
            scrape_weibo(limit),
            scrape_baidu(limit),
            scrape_zhihu_playwright(limit),
            scrape_douyin_playwright(limit),
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
            analyzed_topics = await analyze_hot_topics(all_topics)
            runtime_state["hot_topics"] = analyzed_topics
            add_log('success', f"全网热点分析完成！Top1: {analyzed_topics[0]['title']}")
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