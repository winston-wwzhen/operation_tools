import asyncio
from playwright.async_api import async_playwright
from config_manager import add_log

async def scrape_xiaohongshu(limit=10):
    """
    抓取小红书热点
    策略：小红书网页版反爬极严（强制登录/验证码），因此采用聚合平台(今日热榜)抓取。
    """
    platform = "[小红书]"
    items = []

    # 今日热榜上的小红书节点
    target_url = "https://tophub.today/n/rYqoXQ8vOa"

    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True, args=['--disable-blink-features=AutomationControlled'])
            context = await browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )
            page = await context.new_page()

            add_log('info', f'{platform} 正在连接聚合平台: {target_url}')
            await page.goto(target_url, timeout=30000, wait_until="domcontentloaded")

            # 等待表格加载
            try:
                await page.wait_for_selector('table.table', timeout=8000)
            except:
                add_log('warning', f'{platform} 聚合平台表格加载超时')
                await browser.close()
                return []

            # 解析表格数据
            rows = await page.locator('table.table tbody tr').all()
            add_log('info', f'{platform} 获取到表格行数: {len(rows)}')

            for row in rows:
                if len(items) >= limit: break

                # 标题通常在 td.al a 中
                link_el = row.locator('td.al a')
                if await link_el.count() > 0:
                    title = await link_el.text_content()
                    href = await link_el.get_attribute('href')

                    if title:
                        clean_title = title.strip()
                        # 排除可能的置顶/广告
                        if not clean_title: continue

                        # 聚合平台的链接通常是跳转链接，我们需要保留它或清理它
                        # 这里直接使用聚合链接，它会自动跳到小红书
                        full_link = href if href.startswith('http') else f"https://tophub.today{href}"

                        items.append({
                            "title": clean_title,
                            "link": full_link,
                            "source": "小红书"
                        })

            await browser.close()

            if items:
                add_log('success', f'{platform} 抓取成功，有效数据: {len(items)} 条')
            else:
                add_log('warning', f'{platform} 未提取到有效数据')

            return items

    except Exception as e:
        add_log('error', f"{platform} 抓取流程异常: {e}")
        return []