import json
import asyncio
from playwright.async_api import async_playwright
from config_manager import add_log

async def scrape_douyin_playwright(limit=10):
    """抓取抖音热榜 (Playwright)"""
    platform = "[抖音]"
    add_log('info', f'{platform} 开始启动浏览器抓取...')
    items = []
    captured_data = {'list': []}

    # 监听网络响应的回调
    async def handle_response(response):
        # 抖音热榜接口特征通常包含 web/hot/search/list
        if "web/hot/search/list" in response.url and response.status == 200:
            add_log('info', f'{platform} 捕获到热榜 API 响应: {response.url}')
            try:
                json_body = await response.json()
                data_list = json_body.get('data', {}).get('word_list', [])
                if data_list: 
                    captured_data['list'] = data_list
                    add_log('info', f'{platform} 成功从 API 拦截到 {len(data_list)} 条数据')
            except Exception as e:
                add_log('warning', f'{platform} API 响应解析 JSON 失败: {e}')

    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True, args=['--disable-blink-features=AutomationControlled'])
            context = await browser.new_context(
                 user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
                 extra_http_headers={"Referer": "https://www.douyin.com/"}
            )
            page = await context.new_page()
            
            # 注册监听
            page.on("response", handle_response)
            
            try:
                target_url = "https://www.douyin.com/hot"
                add_log('info', f'{platform} 正在加载页面: {target_url}')
                await page.goto(target_url, timeout=30000, wait_until="domcontentloaded")
                
                # 抖音是动态加载，必须等待
                add_log('info', f'{platform} 页面加载完成，等待数据渲染 (5秒)...')
                await asyncio.sleep(5)
            except Exception as e:
                add_log('warning', f'{platform} 页面加载异常: {e}')

            # 优先使用拦截到的 API 数据
            if captured_data['list']:
                add_log('info', f'{platform} 使用 API 拦截数据构造结果')
                for item in captured_data['list'][:limit]:
                    word = item.get('word', '')
                    if word:
                        items.append({
                            "title": word,
                            "link": f"https://www.douyin.com/search/{word}?type=hot",
                            "source": "抖音"
                        })
            else:
                # 如果没拦截到 API，尝试 DOM 兜底
                add_log('warning', f'{platform} 未拦截到 API 数据，尝试 DOM 抓取兜底...')
                try:
                    # 抖音热搜链接通常包含 douyin.com/search
                    links = await page.locator('a[href*="douyin.com/search"]').all()
                    add_log('info', f'{platform} 找到潜在热搜链接元素: {len(links)} 个')
                    
                    seen = set()
                    for link in links:
                        if len(items) >= limit: break
                        
                        text = await link.text_content()
                        href = await link.get_attribute('href')
                        
                        # 过滤无效文本
                        if text and len(text.strip()) > 2 and "type=hot" in str(href):
                            clean_text = text.strip()
                            if clean_text not in seen:
                                items.append({"title": clean_text, "link": href, "source": "抖音"})
                                seen.add(clean_text)
                except Exception as e:
                    add_log('error', f'{platform} DOM 兜底抓取失败: {e}')
            
            await browser.close()
            
            if items:
                add_log('success', f'{platform} 抓取成功，有效数据: {len(items)} 条')
            else:
                add_log('warning', f'{platform} 抓取结束，未获取到数据')
                
            return items
            
    except Exception as e:
        add_log('error', f"{platform} 抓取流程发生致命错误: {str(e)}")
        return []