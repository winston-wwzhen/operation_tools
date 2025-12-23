import sys
import asyncio
import subprocess

# === Windows 异步循环修复 (必须在最前面) ===
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from playwright.async_api import async_playwright

# 导入核心模块
from core import (
    add_log,
    runtime_state,
    get_settings,
    start_scheduler,
    init_db,
    load_latest_topics_from_db,
    setup_file_logging,
    get_logger,
)
from api import api_router

# 加载配置
settings = get_settings()

# === 初始化日志系统 ===
# 配置文件日志
setup_file_logging(
    level=settings.log_level,
    max_bytes=10 * 1024 * 1024,  # 10MB
    backup_count=5,
    use_time_rotation=True  # 按天轮转
)

# 获取应用日志器
logger = get_logger(__name__)

# === 初始化 App ===
app = FastAPI(
    title="HotSpotAI API",
    description="全网热点聚合与 AI 内容生成 API",
    version="1.0.0"
)

# CORS 配置 - 从环境变量读取
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.parse_cors_origins(settings.cors_origins),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册 API 路由
app.include_router(api_router)


# === 启动事件 ===
@app.on_event("startup")
async def startup_event():
    logger.info("=" * 50)
    logger.info("HotSpotAI API 启动中...")
    logger.info(f"日志级别: {settings.log_level}")
    logger.info("=" * 50)

    # 1. 初始化数据库 (异步)
    logger.info("正在初始化数据库...")
    await init_db()
    logger.info("数据库初始化完成")

    # 2. 从数据库恢复历史数据 (避免重启后页面空白)
    add_log('info', '正在尝试从数据库恢复历史热点数据...')
    saved_topics = await load_latest_topics_from_db()
    if saved_topics:
        runtime_state["hot_topics"] = saved_topics
        logger.info(f"从数据库恢复了 {len(saved_topics)} 条热点数据")

    # 3. 启动定时任务
    logger.info("正在启动定时任务调度器...")
    start_scheduler()

    # 4. 检查浏览器环境
    logger.info("正在检查 Playwright 浏览器环境...")
    add_log('info', '正在检查 Playwright 浏览器环境...')
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=settings.playwright_headless)
            await browser.close()
            logger.info("Playwright 浏览器环境正常")
            add_log('info', 'Playwright 浏览器环境正常')
    except Exception as e:
        if "Executable doesn't exist" in str(e) or "playwright install" in str(e):
            logger.warning("浏览器未安装，正在自动安装...")
            add_log('warning', '正在自动安装浏览器 (playwright install chromium)...')
            try:
                subprocess.run([sys.executable, "-m", "playwright", "install", "chromium"], check=True)
                logger.info("浏览器安装成功")
                add_log('success', '浏览器安装成功！')
            except Exception as install_e:
                logger.error(f"浏览器安装失败: {install_e}")
                add_log('error', f'自动安装失败: {install_e}')
        else:
            logger.warning(f"浏览器环境检查异常: {str(e)}")
            add_log('warning', f'浏览器环境检查异常: {str(e)}')

    logger.info(f"API 服务启动成功！监听: {settings.host}:{settings.port}")
    add_log('info', f'API 服务启动成功！监听: {settings.host}:{settings.port}')


# === 根路径健康检查 ===
@app.get("/")
async def root():
    return {
        "message": "HotSpotAI API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health"
    }


@app.get("/health")
async def health_check():
    """健康检查接口"""
    return {"status": "ok", "service": "hotspotai-api"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host=settings.host, port=settings.port, reload=settings.debug)
