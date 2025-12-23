import httpx
from bs4 import BeautifulSoup
from config_manager import add_log

async def scrape_weibo(limit=10):
    """抓取微博热搜 (使用 httpx)"""
    platform = "[微博]"
    add_log('info', f'{platform} 开始抓取热搜数据...')
    
    url = "https://s.weibo.com/top/summary"
    headers = { 
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Cookie": "SUB=_2AkMT_Mrzf8NxqwJRmP0SzGvhZYt1zw_EieKkjJ2ZJRMxHRl-yT9jqkUstRB6PaaZ-xT_r0Y0-v7_s-x_x_x_;", 
        "Referer": "https://s.weibo.com/"
    }
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            add_log('info', f'{platform} 正在请求 URL: {url}')
            resp = await client.get(url, headers=headers)
            
            if resp.status_code != 200:
                add_log('warning', f'{platform} 请求失败，状态码: {resp.status_code}')
                return []
            
            add_log('info', f'{platform} 请求成功，开始解析 HTML...')
                
        soup = BeautifulSoup(resp.text, 'html.parser')
        items = []
        rows = soup.select('td.td-02 a')
        
        add_log('info', f'{platform} 原始条目数量: {len(rows)}')
        
        for index, tr in enumerate(rows):
            if len(items) >= limit: 
                break
                
            title = tr.get_text().strip()
            href = tr.get('href', '')
            
            # 过滤置顶广告和无效链接
            if "javascript" in href or not href.startswith("/"):
                # add_log('info', f'{platform} 跳过无效链接/广告: {title}')
                continue
                
            link = f"https://s.weibo.com{href}"
            items.append({"title": title, "link": link, "source": "微博"})
            
        add_log('success', f'{platform} 抓取完成，有效数据: {len(items)} 条')
        return items
        
    except httpx.RequestError as e:
        add_log('error', f"{platform} 网络请求异常: {e}")
        return []
    except Exception as e:
        add_log('error', f"{platform} 抓取发生未预期的错误: {e}")
        return []