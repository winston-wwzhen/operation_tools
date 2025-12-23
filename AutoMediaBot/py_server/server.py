import os
import sys
import json
import asyncio
import re
import subprocess
from datetime import datetime
from typing import List, Optional, Dict, Any

# === 关键修复：强制 Windows 使用 ProactorEventLoop ===
# 必须放在所有 asyncio 引用之前，且在 Windows 下生效
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

from fastapi import FastAPI, Request, BackgroundTasks, HTTPException
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

import httpx
from bs4 import BeautifulSoup
from openai import AsyncOpenAI
from playwright.async_api import async_playwright
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

# === 配置与全局状态 ===

CONFIG_FILE = "config.json"
LOG_LIMIT = 100

# 默认配置
default_config = {
    "llmApiKey": "", 
    "llmBaseUrl": "https://open.bigmodel.cn/api/paas/v4/", 
    "llmModel": "glm-4", 
    "wechatAppId": "",
    "wechatSecret": "",
    "topicLimit": 10,
    "scheduleCron": "0 */2 * * *", 
    "autoRun": False
}

# 运行时状态
runtime_state = {
    "isRunning": False,
    "lastRunTime": None,
    "nextRunTime": None,
    "logs": [],
    "hot_topics": [] 
}

# 全局变量
app_config = default_config.copy()
scheduler = AsyncIOScheduler()

# === 工具函数 ===

def load_config():
    global app_config
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                saved = json.load(f)
                app_config.update(saved)
        except Exception as e:
            print(f"Error loading config: {e}")

def save_config():
    with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump(app_config, f, indent=2, ensure_ascii=False)

def add_log(level: str, message: str):
    timestamp = datetime.now().strftime("%H:%M:%S")
    log_entry = {
        "id": int(datetime.now().timestamp() * 1000),
        "time": timestamp,
        "level": level,
        "message": message
    }
    # 保持日志长度
    runtime_state["logs"].insert(0, log_entry)
    if len(runtime_state["logs"]) > LOG_LIMIT:
        runtime_state["logs"].pop()
    print(f"[{level.upper()}] {message}")

# === 多平台抓取模块 ===

async def scrape_weibo(limit=10):
    """抓取微博热搜 (使用 httpx)"""
    add_log('info', '正在抓取 [微博] 热搜...')
    url = "https://s.weibo.com/top/summary"
    headers = { 
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Cookie": "SUB=_2AkMT_Mrzf8NxqwJRmP0SzGvhZYt1zw_EieKkjJ2ZJRMxHRl-yT9jqkUstRB6PaaZ-xT_r0Y0-v7_s-x_x_x_;", 
        "Referer": "https://s.weibo.com/"
    }
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(url, headers=headers)
            add_log('info', f'微博请求状态码: {resp.status_code}')
            if resp.status_code != 200:
                add_log('warning', f'微博返回状态码: {resp.status_code}')
                return []
                
        soup = BeautifulSoup(resp.text, 'html.parser')
        items = []
        rows = soup.select('td.td-02 a')
        add_log('info', f'微博解析到 {len(rows)} 行数据')
        
        for tr in rows:
            if len(items) >= limit: break
            title = tr.get_text().strip()
            href = tr.get('href', '')
            
            if "javascript" in href or not href.startswith("/"):
                continue
                
            link = f"https://s.weibo.com{href}"
            items.append({"title": title, "link": link, "source": "微博"})
            
        if not items:
            add_log('warning', f'微博抓取内容为空，HTML预览: {str(soup)[:100]}...')
        return items
    except Exception as e:
        add_log('error', f"微博抓取失败: {e}")
        return []

async def scrape_baidu(limit=10):
    """抓取百度热搜 (使用 httpx)"""
    add_log('info', '正在抓取 [百度] 热搜...')
    url = "https://top.baidu.com/board?tab=realtime"
    headers = { "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36" }
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(url, headers=headers)
            add_log('info', f'百度请求状态码: {resp.status_code}')
            
        soup = BeautifulSoup(resp.text, 'html.parser')
        items = []
        titles = soup.select('.c-single-text-ellipsis')
        add_log('info', f'百度解析到 {len(titles)} 个标题元素')
        
        for t in titles:
            if len(items) >= limit: break
            title = t.get_text().strip()
            if not title: continue
            if any(x['title'] == title for x in items): continue
            
            items.append({
                "title": title,
                "link": f"https://www.baidu.com/s?wd={title}",
                "source": "百度"
            })
        return items
    except Exception as e:
        add_log('error', f"百度抓取失败: {e}")
        return []

async def scrape_zhihu_playwright(limit=10):
    """
    抓取知乎热榜 (Playwright)
    策略：直接访问 /hot 页面，并从 window.initialState 中提取数据。
    """
    add_log('info', '正在抓取 [知乎] 热榜 (Playwright - JSON数据源)...')
    items = []
    try:
        async with async_playwright() as p:
            # 升级 UA，增加真实性
            browser = await p.chromium.launch(headless=True, args=['--disable-blink-features=AutomationControlled'])
            context = await browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
                viewport={'width': 1920, 'height': 1080},
                extra_http_headers={
                    'Accept-Language': 'zh-CN,zh;q=0.9',
                    'Referer': 'https://www.zhihu.com/'
                }
            )
            await context.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            page = await context.new_page()
            
            add_log('info', '正在跳转知乎热榜页面...')
            try:
                await page.goto("https://www.zhihu.com/hot", timeout=30000, wait_until="domcontentloaded")
                # 增加一点等待，确保内容渲染
                await asyncio.sleep(3)
                title = await page.title()
                add_log('info', f'知乎页面加载完成，标题: {title}')
                if "验证" in title or not title:
                     add_log('warning', '知乎可能触发了验证码页面或加载不完整')
            except Exception as e:
                add_log('warning', f'知乎页面加载超时或部分失败: {e}')

            # 方法 A: JSON
            try:
                script_el = await page.wait_for_selector('#js-initialData', state="attached", timeout=5000)
                if script_el:
                    add_log('info', '知乎找到 #js-initialData 元素')
                    raw_data = await page.evaluate("document.getElementById('js-initialData').innerHTML")
                    
                    if raw_data:
                        add_log('info', f'知乎获取到 JSON 数据，长度: {len(raw_data)}')
                        data = json.loads(raw_data)
                        
                        initial_state = data.get('initialState', {})
                        if not initial_state:
                            add_log('warning', '知乎 JSON 中缺少 initialState')
                        else:
                            # 尝试多个可能的路径
                            hot_list = initial_state.get('topstory', {}).get('hotList', [])
                            
                            # 如果 hotList 为空，打印一下 keys 方便调试
                            if not hot_list:
                                add_log('warning', f"知乎 hotList 为空，initialState keys: {list(initial_state.keys())}")
                                if 'topstory' in initial_state:
                                    add_log('warning', f"topstory keys: {list(initial_state['topstory'].keys())}")
                            
                            add_log('info', f'知乎解析出 hotList 长度: {len(hot_list)}')
                            
                            for item in hot_list[:limit]:
                                target = item.get('target', {})
                                title = target.get('titleArea', {}).get('text', '')
                                link_url = target.get('link', {}).get('url', '')
                                
                                if title:
                                    full_link = link_url if link_url.startswith('http') else f"https://www.zhihu.com{link_url}"
                                    items.append({"title": title, "link": full_link, "source": "知乎"})
                else:
                    add_log('warning', '知乎未找到 #js-initialData 元素')
            except Exception as e:
                add_log('warning', f'知乎 JSON 提取异常: {str(e)}')

            # 方法 B: DOM 兜底
            if not items:
                add_log('info', '知乎尝试 DOM 兜底抓取...')
                try:
                    # 尝试多种选择器，因为知乎类名可能变化
                    # .HotItem 是热榜常见的，.HotList-item 是 Billboard 常见的
                    selector = '.HotItem, .HotList-item, section[class*="HotItem"]'
                    try:
                         await page.wait_for_selector(selector, timeout=8000)
                    except:
                         add_log('error', '知乎 DOM 元素等待超时')

                    elements = await page.locator(selector).all()
                    add_log('info', f'知乎找到 {len(elements)} 个热榜元素')
                    
                    for el in elements[:limit]:
                        # 尝试多种标题选择器
                        title_el = el.locator('.HotItem-title, .HotList-itemTitle, h2')
                        link_el = el.locator('.HotItem-content a, .HotList-itemBody, a[href*="/question/"]')
                        
                        if await title_el.count() > 0:
                            # 获取第一个匹配的
                            title = await title_el.first.text_content()
                            href = ""
                            if await link_el.count() > 0:
                                href = await link_el.first.get_attribute('href')
                            
                            if title:
                                items.append({
                                    "title": title.strip(),
                                    "link": href if href.startswith('http') else f"https://www.zhihu.com{href}",
                                    "source": "知乎"
                                })
                except Exception as e:
                     add_log('error', f'知乎 DOM 抓取也失败: {str(e)}')

            await browser.close()
            return items
    except Exception as e:
        add_log('error', f"知乎抓取整体失败: {str(e)}")
        return []

async def scrape_douyin_playwright(limit=10):
    """
    抓取抖音热榜 (Playwright)
    """
    add_log('info', '正在抓取 [抖音] 热榜 (Playwright - 混合模式)...')
    items = []
    
    captured_data = {'list': []}

    async def handle_response(response):
        if "web/hot/search/list" in response.url:
            add_log('info', f'抖音命中 API URL: {response.url}, Status: {response.status}')
            if response.status == 200:
                try:
                    json_body = await response.json()
                    data_list = json_body.get('data', {}).get('word_list', [])
                    if data_list:
                        captured_data['list'] = data_list
                        add_log('info', f'成功解析抖音 API，包含 {len(data_list)} 条数据')
                except Exception as e:
                    add_log('error', f'抖音 API 解析异常: {e}')

    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True, args=['--disable-blink-features=AutomationControlled'])
            # 修复：referer 不能作为直接参数，需放入 extra_http_headers
            context = await browser.new_context(
                 user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
                 extra_http_headers={
                     "Referer": "https://www.douyin.com/"
                 }
            )
            page = await context.new_page()
            
            page.on("response", handle_response)
            
            add_log('info', '正在跳转抖音热榜页面...')
            try:
                await page.goto("https://www.douyin.com/hot", timeout=30000, wait_until="domcontentloaded")
                add_log('info', f'抖音页面加载完成，标题: {await page.title()}')
                await asyncio.sleep(5)
            except Exception as e:
                add_log('warning', f'抖音页面加载异常: {str(e)[:50]}')

            # 1. API 数据
            if captured_data['list']:
                add_log('info', f"抖音使用 API 数据，共 {len(captured_data['list'])} 条")
                for item in captured_data['list'][:limit]:
                    word = item.get('word', '')
                    if word:
                        items.append({
                            "title": word,
                            "link": f"https://www.douyin.com/search/{word}?type=hot",
                            "source": "抖音"
                        })
                await browser.close()
                return items

            # 2. DOM 暴力搜索
            add_log('info', '抖音 API 拦截未命中，尝试 DOM 搜索...')
            try:
                links = await page.locator('a[href*="douyin.com/search"]').all()
                add_log('info', f'抖音 DOM 搜索找到 {len(links)} 个潜在链接')
                
                seen_titles = set()
                count = 0
                for link in links:
                    if count >= limit: break
                    href = await link.get_attribute('href')
                    text = await link.text_content()
                    
                    if text and len(text.strip()) > 2 and "type=hot" in str(href):
                        clean_title = text.strip()
                        if clean_title not in seen_titles:
                            items.append({
                                "title": clean_title,
                                "link": href,
                                "source": "抖音"
                            })
                            seen_titles.add(clean_title)
                            count += 1
                add_log('info', f'抖音 DOM 筛选出 {count} 条有效数据')
            except Exception as e:
                add_log('error', f'抖音 DOM 搜索失败: {str(e)}')

            await browser.close()
            return items
    except Exception as e:
        add_log('error', f"抖音抓取失败: {str(e)}")
        return []

# === 智能分析模块 ===

async def analyze_hot_topics(raw_topics: List[Dict]):
    """使用 GLM-4 分析热点列表"""
    if not raw_topics: return []
    
    api_key = app_config.get("llmApiKey")
    if not api_key:
        add_log('warning', '未配置 API Key，仅返回原始数据')
        return raw_topics

    add_log('info', f'正在调用 GLM-4 分析 {len(raw_topics)} 条全网热点...')
    
    # 构建 Prompt
    prompt_items = [f"{idx+1}. [{t['source']}] {t['title']}" for idx, t in enumerate(raw_topics)]
    prompt_text = "\n".join(prompt_items)

    system_prompt = (
        "你是一个全网舆情分析师。请分析以下新闻标题。"
        "任务：1. 评分 (heat): 0-100，基于话题的社会影响力和讨论度。"
        "2. 标签 (tags): 为每个话题打1-2个标签，如：时事、娱乐、科技、民生、国际、体育等。"
        "请以 JSON 数组格式返回，包含 'index', 'heat', 'tags' 字段。不要输出任何 Markdown 格式，仅输出纯 JSON 字符串。"
    )

    try:
        client = AsyncOpenAI(api_key=api_key, base_url=app_config.get("llmBaseUrl"))
        
        response = await client.chat.completions.create(
            model=app_config.get("llmModel", "glm-4"),
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt_text}
            ],
            temperature=0.3
        )
        
        content = response.choices[0].message.content
        
        analysis_list = []
        try:
            clean_content = content.replace("```json", "").replace("```", "").strip()
            analysis_list = json.loads(clean_content)
        except json.JSONDecodeError:
            try:
                match = re.search(r'\[.*\]', content, re.DOTALL)
                if match:
                    analysis_list = json.loads(match.group(0))
                else:
                    raise ValueError("无法提取 JSON 数组")
            except Exception as parse_err:
                add_log('error', f'GLM 返回格式异常，无法解析 JSON。原始内容前50字符: {content[:50]}')
                return raw_topics

        analysis_map = {}
        for item in analysis_list:
            idx = item.get('index', 0) - 1
            analysis_map[idx] = item

        final_list = []
        for idx, topic in enumerate(raw_topics):
            meta = analysis_map.get(idx, {})
            topic['heat'] = meta.get('heat', 50)
            topic['tags'] = meta.get('tags', ['热点'])
            final_list.append(topic)
            
        final_list.sort(key=lambda x: x['heat'], reverse=True)
        return final_list

    except Exception as e:
        add_log('error', f"智能分析失败: {e}")
        return raw_topics

# === 核心任务逻辑 ===

async def run_task_logic():
    """执行：全网抓取 -> 智能分析"""
    if runtime_state["isRunning"]: return
    
    runtime_state["isRunning"] = True
    runtime_state["lastRunTime"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    add_log('info', '>>> 开始全网热点聚合任务')
    
    try:
        limit = int(app_config.get("topicLimit", 10))
        
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
                add_log('error', f"某个平台抓取发生异常: {res}")
            
        add_log('success', f"原始数据抓取完成，共 {len(all_topics)} 条，准备分析...")
        
        if all_topics:
            analyzed_topics = await analyze_hot_topics(all_topics)
            runtime_state["hot_topics"] = analyzed_topics
            add_log('success', f"全网热点分析完成！Top1: {analyzed_topics[0]['title']}")
        else:
            add_log('warning', "未抓取到任何数据，请检查网络或配置")
            
    except Exception as e:
        add_log('error', f"任务执行异常: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        runtime_state["isRunning"] = False
        add_log('info', '<<< 任务结束')
        
        if scheduler.get_jobs():
            job = scheduler.get_jobs()[0]
            if job.next_run_time:
                 runtime_state["nextRunTime"] = job.next_run_time.strftime("%Y-%m-%d %H:%M:%S")

# === 内容生成 (针对单个 Topic) ===

async def generate_article_for_topic(topic: Dict, platform: str):
    api_key = app_config.get("llmApiKey")
    if not api_key: return None

    add_log('info', f"正在生成 [{platform}] 文案: {topic['title']}")
    
    try:
        client = AsyncOpenAI(api_key=api_key, base_url=app_config.get("llmBaseUrl"))
        
        system_prompt = "你是一个专业自媒体编辑。"
        if platform == "wechat":
            system_prompt += "请写一篇深度公众号文章，HTML格式，包含标题、摘要、正文。"
        
        tools_config = [{
            "type": "web_search",
            "web_search": {
                "enable": True,
                "search_result": True
            }
        }]

        response = await client.chat.completions.create(
            model=app_config.get("llmModel", "glm-4"),
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"请针对热点“{topic['title']}”写一篇文章。请务必先使用联网搜索工具获取该事件的最新起因、经过、结果和各方观点，然后基于搜索结果进行创作。"}
            ],
            tools=tools_config
        )
        return response.choices[0].message.content
    except Exception as e:
        add_log('error', f"文案生成失败: {e}")
        return None

# === FastAPI 应用 ===

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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

# === API 路由 ===

@app.on_event("startup")
async def startup_event():
    load_config()
    scheduler.start()
    if app_config.get("autoRun"):
        update_scheduler()
    
    # 自动检查并安装 Playwright 浏览器
    add_log('info', '正在检查 Playwright 浏览器环境...')
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            await browser.close()
            add_log('info', 'Playwright 浏览器环境正常')
    except Exception as e:
        if "Executable doesn't exist" in str(e) or "playwright install" in str(e):
            add_log('warning', '未检测到浏览器，正在自动执行安装 (playwright install chromium)...')
            try:
                # 使用 subprocess 同步执行安装，会阻塞启动，但这是必须的
                process = subprocess.run(
                    [sys.executable, "-m", "playwright", "install", "chromium"], 
                    capture_output=True, 
                    text=True
                )
                if process.returncode == 0:
                    add_log('success', '浏览器安装成功！')
                else:
                    add_log('error', f'自动安装失败: {process.stderr}')
            except Exception as install_e:
                add_log('error', f'执行安装命令出错: {install_e}')
        else:
            add_log('warning', f'浏览器环境检查异常 (非缺失错误): {str(e)}')

    add_log('info', '服务启动。请点击“聚合全网热点”获取最新数据。')

def update_scheduler():
    scheduler.remove_all_jobs()
    if app_config.get("autoRun") and app_config.get("scheduleCron"):
        try:
            scheduler.add_job(run_task_logic, CronTrigger.from_crontab(app_config["scheduleCron"]), id="auto_task")
            add_log('info', f"定时任务已更新: {app_config['scheduleCron']}")
        except:
            add_log('error', "Cron 格式错误")

@app.get("/api/status")
async def get_status():
    return {
        "config": app_config,
        "state": runtime_state
    }

@app.post("/api/config")
async def update_config(config: ConfigModel):
    update_data = config.dict(exclude_unset=True)
    app_config.update(update_data)
    save_config()
    update_scheduler()
    return {"success": True}

@app.post("/api/refresh-topics")
async def refresh_topics(background_tasks: BackgroundTasks):
    background_tasks.add_task(run_task_logic)
    return {"success": True, "message": "正在后台聚合全网热点..."}

@app.post("/api/generate-draft")
async def generate_draft(req: GenerateRequest):
    content = await generate_article_for_topic(req.topic, req.platform)
    return {"success": True, "content": content}

# 静态文件
if os.path.exists("public"):
    app.mount("/", StaticFiles(directory="public", html=True), name="static")

if __name__ == "__main__":
    import uvicorn
    # 注意：reload=True 在 Windows 下可能会导致 asyncio loop policy 设置失效或被重置
    # 如果遇到 loop 报错，请尝试去掉 reload=True
    # Windows下同时使用playwright和uvicorn必须关闭reload
    uvicorn.run("server:app", host="0.0.0.0", port=3000, reload=False)