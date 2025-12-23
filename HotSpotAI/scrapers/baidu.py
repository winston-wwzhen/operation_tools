import httpx
from bs4 import BeautifulSoup
from core.config import add_log

async def scrape_baidu(limit=10):
    """抓取百度热搜 (使用 httpx)"""
    platform = "[百度]"
    add_log('info', f'{platform} 开始抓取热搜数据...')
    
    url = "https://top.baidu.com/board?tab=realtime"
    headers = { "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36" }
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            add_log('info', f'{platform} 正在请求 URL: {url}')
            resp = await client.get(url, headers=headers)
            
            if resp.status_code != 200:
                add_log('warning', f'{platform} 请求失败，状态码: {resp.status_code}')
                return []

        soup = BeautifulSoup(resp.text, 'html.parser')
        items = []
        titles = soup.select('.c-single-text-ellipsis')
        
        add_log('info', f'{platform} 页面解析获取到原始标题元素: {len(titles)} 个')
        
        for t in titles:
            if len(items) >= limit: break
            
            title = t.get_text().strip()
            if not title: 
                continue
                
            # 简单去重
            if any(x['title'] == title for x in items): 
                continue
            
            items.append({
                "title": title,
                "link": f"https://www.baidu.com/s?wd={title}",
                "source": "百度"
            })
            
        add_log('success', f'{platform} 抓取完成，有效数据: {len(items)} 条')
        return items
        
    except httpx.RequestError as e:
        add_log('error', f"{platform} 网络请求异常: {e}")
        return []
    except Exception as e:
        add_log('error', f"{platform} 抓取失败: {e}")
        return []