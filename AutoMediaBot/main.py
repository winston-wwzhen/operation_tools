import sys
import asyncio
import os
import subprocess
from typing import Optional, Dict

# === Windows 异步循环修复 (必须在最前面) ===
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

from fastapi import FastAPI, BackgroundTasks
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from playwright.async_api import async_playwright

# 导入拆分后的模块
from config_manager import load_config, save_config, add_log, app_config, runtime_state, update_app_config
from task_scheduler import start_scheduler, update_scheduler, run_task_logic
from llm_engine import generate_article_for_topic

# === Pydantic 模型 ===
class ConfigModel(BaseModel):
    llmApiKey: Optional[str] = None
    llmBaseUrl: Optional[str] = None
    llmModel: Optional[str] = None
    wechatAppId: Optional[str] = None
    wechatSecret: Optional[str] = None
    topicLimit: Optional[int] = None
    scheduleCron: Optional[str] = None
    autoRun: Optional[bool] = None

class GenerateRequest(BaseModel):
    topic: Dict
    platform: str

# === 初始化 App ===
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# === 启动事件 ===
@app.on_event("startup")
async def startup_event():
    # 1. 加载配置
    load_config()
    
    # 2. 启动定时任务
    start_scheduler()
    
    # 3. 检查浏览器环境
    add_log('info', '正在检查 Playwright 浏览器环境...')
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            await browser.close()
            add_log('info', 'Playwright 浏览器环境正常')
    except Exception as e:
        if "Executable doesn't exist" in str(e) or "playwright install" in str(e):
            add_log('warning', '正在自动安装浏览器 (playwright install chromium)...')
            try:
                subprocess.run([sys.executable, "-m", "playwright", "install", "chromium"], check=True)
                add_log('success', '浏览器安装成功！')
            except Exception as install_e:
                add_log('error', f'自动安装失败: {install_e}')
        else:
            add_log('warning', f'浏览器环境检查异常: {str(e)}')

    add_log('info', '服务启动成功。请访问 http://localhost:3000')

# === API 路由 ===

@app.get("/api/status")
async def get_status():
    return {
        "config": app_config,
        "state": runtime_state
    }

@app.post("/api/config")
async def update_config_api(config: ConfigModel):
    update_data = config.dict(exclude_unset=True)
    update_app_config(update_data)
    update_scheduler()
    return {"success": True}

@app.post("/api/refresh-topics")
async def refresh_topics(background_tasks: BackgroundTasks):
    # 使用 BackgroundTasks 避免阻塞 API 返回
    background_tasks.add_task(run_task_logic)
    return {"success": True, "message": "正在后台聚合全网热点..."}

@app.post("/api/generate-draft")
async def generate_draft(req: GenerateRequest):
    content = await generate_article_for_topic(req.topic, req.platform)
    return {"success": True, "content": content}

# 挂载静态文件 (必须放在 API 路由之后)
if os.path.exists("public"):
    app.mount("/", StaticFiles(directory="public", html=True), name="static")

if __name__ == "__main__":
    import uvicorn
    # 生产环境建议关闭 reload
    uvicorn.run("main:app", host="0.0.0.0", port=3000, reload=False)