import json
import asyncio
from playwright.async_api import async_playwright
from config_manager import add_log

async def scrape_zhihu_playwright(limit=10):
    """抓取知乎热榜 (Playwright)"""
    platform = "[知乎]"
    add_log('info', f'{platform} 开始启动无头浏览器抓取...')
    items = []
    
    try:
        async with async_playwright() as p:
            add_log('info', f'{platform} 正在启动 Chromium...')
            browser = await p.chromium.launch(headless=True, args=['--disable-blink-features=AutomationControlled'])
            
            context = await browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
                viewport={'width': 1920, 'height': 1080}
            )
            # 注入脚本防止被检测
            await context.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            page = await context.new_page()
            try:
                add_log('info', f'{platform} 正在加载页面: https://www.zhihu.com/hot')
                await page.goto("https://www.zhihu.com/hot", timeout=30000, wait_until="domcontentloaded")
                await asyncio.sleep(2) # 等待动态内容渲染
            except Exception as e:
                add_log('warning', f'{platform} 页面加载超时或不完整: {e}')

            # 策略A: 尝试从 #js-initialData 数据中直接提取 JSON
            try:
                add_log('info', f'{platform} 尝试提取 hidden JSON 数据 (#js-initialData)...')
                script_el = await page.wait_for_selector('#js-initialData', state="attached", timeout=5000)
                
                if script_el:
                    raw_data = await page.evaluate("document.getElementById('js-initialData').innerHTML")
                    data = json.loads(raw_data)
                    initial_state = data.get('initialState', {})
                    hot_list = initial_state.get('topstory', {}).get('hotList', [])
                    
                    add_log('info', f'{platform} 成功提取到 JSON 数据列表，长度: {len(hot_list)}')
                    
                    for item in hot_list[:limit]:
                        target = item.get('target', {})
                        title = target.get('titleArea', {}).get('text', '')
                        link_url = target.get('link', {}).get('url', '')
                        if title:
                            full_link = link_url if link_url.startswith('http') else f"https://www.zhihu.com{link_url}"
                            items.append({"title": title, "link": full_link, "source": "知乎"})
            except Exception as e:
                add_log('warning', f'{platform} JSON 提取失败，准备切换到 DOM 解析: {e}')

            # 策略B: DOM 兜底 (如果策略A没有获取到数据)
            if not items:
                add_log('info', f'{platform} 正在进行 DOM 元素解析兜底...')
                try:
                    selector = '.HotItem, .HotList-item'
                    elements = await page.locator(selector).all()
                    add_log('info', f'{platform} 找到 DOM 元素数量: {len(elements)}')
                    
                    for el in elements[:limit]:
                        title_el = el.locator('.HotItem-title, .HotList-itemTitle, h2')
                        link_el = el.locator('a')
                        
                        if await title_el.count() > 0:
                            title = await title_el.first.text_content()
                            href = await link_el.first.get_attribute('href')
                            if title:
                                items.append({
                                    "title": title.strip(),
                                    "link": href if href.startswith('http') else f"https://www.zhihu.com{href}",
                                    "source": "知乎"
                                })
                except Exception as e:
                    add_log('error', f'{platform} DOM 抓取也失败了: {e}')

            await browser.close()
            
            if items:
                add_log('success', f'{platform} 抓取成功，获取数据: {len(items)} 条')
            else:
                add_log('warning', f'{platform} 抓取结束，但未获取到任何数据')
                
            return items
            
    except Exception as e:
        add_log('error', f"{platform} 抓取整体流程失败: {str(e)}")
        return []