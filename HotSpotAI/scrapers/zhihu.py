import asyncio
from playwright.async_api import async_playwright
from core.config import add_log

async def scrape_zhihu_playwright(limit=10):
    """
    抓取知乎数据
    策略：由于知乎原站(/hot)强制登录，改为抓取第三方聚合平台数据。
    1. 优先抓取 [今日热榜] 的知乎板块 (实时热榜)。
    2. 如果失败，兜底抓取 [知乎日报] (精选热点)。
    """
    platform = "[知乎]"
    items = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, args=['--disable-blink-features=AutomationControlled'])
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            viewport={'width': 1920, 'height': 1080}
        )
        page = await context.new_page()

        # === 方案 A: 抓取今日热榜 (知乎热榜镜像) ===
        try:
            target_url = "https://tophub.today/n/mproPpoq6O"
            add_log('info', f'{platform} (方案A) 正在从聚合平台加载知乎热榜: {target_url}')
            
            await page.goto(target_url, timeout=30000, wait_until="domcontentloaded")
            
            # 等待表格加载
            try:
                await page.wait_for_selector('table.table', timeout=5000)
            except:
                add_log('warning', f'{platform} 聚合平台表格未加载，尝试方案B...')
                raise Exception("Table not found")

            # 解析数据
            rows = await page.locator('table.table tbody tr').all()
            
            for row in rows[:limit]:
                # 标题通常在 td.al a 中
                link_el = row.locator('td.al a')
                if await link_el.count() > 0:
                    title = await link_el.text_content()
                    href = await link_el.get_attribute('href')
                    
                    if title:
                        items.append({
                            "title": title.strip(),
                            # 聚合平台的链接通常会跳转回知乎原站，这符合需求
                            "link": href if href.startswith('http') else f"https://tophub.today{href}",
                            "source": "知乎"
                        })
            
            if items:
                add_log('success', f'{platform} 从聚合平台成功获取 {len(items)} 条热榜数据')

        except Exception as e:
            add_log('warning', f'{platform} 方案A抓取失败 ({str(e)})，切换到方案B (知乎日报)...')
            items = [] # 清空可能的不完整数据

        # === 方案 B: 抓取知乎日报 (兜底) ===
        if not items:
            try:
                daily_url = "https://daily.zhihu.com/"
                add_log('info', f'{platform} (方案B) 正在加载知乎日报: {daily_url}')
                await page.goto(daily_url, timeout=30000, wait_until="domcontentloaded")
                
                # 知乎日报结构: .box a.link-button
                cards = await page.locator('.box a.link-button').all()
                
                for card in cards[:limit]:
                    title_el = card.locator('span.title')
                    if await title_el.count() > 0:
                        title = await title_el.text_content()
                        href = await card.get_attribute('href')
                        
                        if title:
                            items.append({
                                "title": title.strip(),
                                "link": f"https://daily.zhihu.com{href}",
                                "source": "知乎日报"
                            })
                
                if items:
                    add_log('success', f'{platform} 从知乎日报兜底获取 {len(items)} 条数据')
            
            except Exception as e:
                add_log('error', f'{platform} 方案B (知乎日报) 也失败了: {e}')

        await browser.close()
        return items