import asyncio
from playwright.async_api import async_playwright
from core.config import add_log

async def scrape_toutiao(limit=10):
    """
    抓取今日头条热榜
    策略：Playwright 拦截 API (优先) + DOM 抓取 (兜底)
    """
    platform = "[今日头条]"
    add_log('info', f'{platform} 开始启动浏览器抓取...')

    items = []
    captured_data = {'list': []}

    # 1. 定义 API 拦截回调
    async def handle_response(response):
        # 拦截头条热榜接口: hot-event/hot-board
        if "hot-event/hot-board" in response.url and response.status == 200:
            try:
                json_body = await response.json()
                # 头条 API 结构通常为: data -> [] 或 data -> fixed_top_data / data
                # 这里做宽泛的解析
                data = json_body.get('data', [])
                if isinstance(data, list):
                    captured_data['list'].extend(data)
                    add_log('info', f'{platform} 成功拦截 API 数据: {len(data)} 条')
                elif isinstance(data, dict):
                    # 有时候会有置顶数据
                    raw_list = data.get('data', [])
                    if raw_list:
                        captured_data['list'].extend(raw_list)
                        add_log('info', f'{platform} 成功拦截 API 数据 (Nested): {len(raw_list)} 条')
            except Exception as e:
                add_log('warning', f'{platform} API JSON 解析失败: {e}')

    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True, args=['--disable-blink-features=AutomationControlled'])
            context = await browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                viewport={'width': 1920, 'height': 1080}
            )

            page = await context.new_page()

            # 开启监听
            page.on("response", handle_response)

            target_url = "https://www.toutiao.com/"
            add_log('info', f'{platform} 正在加载页面: {target_url}')

            try:
                await page.goto(target_url, timeout=30000, wait_until="networkidle")

                # 等待一会儿，确保 API 响应回来
                # 头条热榜通常在侧边栏，可能需要滚动或等待加载
                for _ in range(10):
                    if captured_data['list']: break
                    await asyncio.sleep(0.5)

            except Exception as e:
                add_log('warning', f'{platform} 页面加载等待期间出现轻微异常: {e}')

            # 2. 处理数据 (优先使用 API)
            if captured_data['list']:
                seen = set()
                for item in captured_data['list']:
                    if len(items) >= limit: break

                    title = item.get('Title', '')
                    url = item.get('Url', '')

                    if title and title not in seen:
                        items.append({
                            "title": title,
                            "link": url if url.startswith('http') else f"https://www.toutiao.com{url}",
                            "source": "今日头条"
                        })
                        seen.add(title)
            else:
                # 3. DOM 兜底 (如果 API 没拦截到)
                add_log('warning', f'{platform} 未拦截到 API，尝试解析 DOM...')
                try:
                    # 头条侧边栏热榜选择器，可能会变
                    # 查找包含 "热榜" 字样的区域，然后找下面的链接
                    elements = await page.locator('div[class*="hot-board"] a').all()

                    # 如果上面的选择器找不到，尝试更通用的
                    if not elements:
                        elements = await page.locator('a[href*="toutiao.com/trending"]').all()

                    add_log('info', f'{platform} DOM 找到潜在元素: {len(elements)} 个')

                    for el in elements[:limit*2]: # 多抓点防重
                        if len(items) >= limit: break

                        text = await el.text_content()
                        href = await el.get_attribute('href')

                        if text and len(text.strip()) > 4: # 标题通常较长
                            items.append({
                                "title": text.strip(),
                                "link": href if href.startswith('http') else f"https://www.toutiao.com{href}",
                                "source": "今日头条"
                            })
                except Exception as e:
                    add_log('error', f'{platform} DOM 兜底失败: {e}')

            await browser.close()

            if items:
                add_log('success', f'{platform} 抓取完成，有效数据: {len(items)} 条')
            return items

    except Exception as e:
        add_log('error', f"{platform} 抓取致命错误: {e}")
        return []