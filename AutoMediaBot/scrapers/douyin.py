import asyncio

from playwright.async_api import async_playwright

from config_manager import add_log


async def scrape_douyin_playwright(limit=10):
    """抓取抖音热榜 (Playwright) - 优化等待逻辑"""
    platform = "[抖音]"
    add_log('info', f'{platform} 开始启动浏览器抓取...')
    items = []
    captured_data = {'list': []}

    # 监听网络响应的回调
    async def handle_response(response):
        # 抖音热榜接口特征
        if "web/hot/search/list" in response.url and response.status == 200:
            # add_log('info', f'{platform} 捕获到热榜 API 响应: {response.url}')
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
            # 使用更真实的 User-Agent
            browser = await p.chromium.launch(headless=True, args=['--disable-blink-features=AutomationControlled'])
            context = await browser.new_context(
                 user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                 viewport={'width': 1920, 'height': 1080},
                 device_scale_factor=1,
                 extra_http_headers={"Referer": "https://www.douyin.com/"}
            )
            # 注入脚本防止 webdriver 检测
            await context.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

            page = await context.new_page()
            
            # 注册监听
            page.on("response", handle_response)
            
            try:
                target_url = "https://www.douyin.com/hot"
                add_log('info', f'{platform} 正在加载页面: {target_url}')
                await page.goto(target_url, timeout=30000, wait_until="domcontentloaded")
                
                # === 优化等待逻辑 (轮询等待数据，最多等 15 秒) ===
                add_log('info', f'{platform} 页面加载完成，正在等待 API 数据回传...')
                max_retries = 30 # 30 * 0.5s = 15s
                for i in range(max_retries):
                    if captured_data['list']:
                        break
                    await asyncio.sleep(0.5)
                
            except Exception as e:
                add_log('warning', f'{platform} 页面加载或等待超时: {e}')

            # 优先使用拦截到的 API 数据
            if captured_data['list']:
                # add_log('info', f'{platform} 使用 API 拦截数据构造结果')
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
                    # 等待元素出现，确保 DOM 渲染
                    try:
                        await page.wait_for_selector('a[href*="douyin.com/search"]', timeout=5000)
                    except:
                        pass

                    links = await page.locator('a[href*="douyin.com/search"]').all()
                    add_log('info', f'{platform} 找到潜在热搜链接元素: {len(links)} 个')
                    
                    seen = set()
                    for link in links:
                        if len(items) >= limit: break
                        
                        text = await link.text_content()
                        href = await link.get_attribute('href')
                        
                        # 过滤无效文本
                        if text and len(text.strip()) > 1 and ("type=hot" in str(href) or "douyin.com/hot" in str(href)):
                            clean_text = text.strip()
                            # 过滤掉序号（如 "1 "）
                            if clean_text.isdigit(): continue
                            
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