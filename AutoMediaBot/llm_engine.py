import json
import re
from typing import List, Dict
from openai import AsyncOpenAI
from config_manager import add_log, get_config

async def analyze_hot_topics(raw_topics: List[Dict]):
    """使用 大模型 分析热点列表，打分和打标签"""
    if not raw_topics: return []
    
    api_key = get_config("llmApiKey")
    if not api_key:
        add_log('warning', '未配置 API Key，跳过智能分析')
        return raw_topics

    add_log('info', f'正在调用 {get_config("llmModel")} 分析 {len(raw_topics)} 条全网热点...')
    
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
        client = AsyncOpenAI(api_key=api_key, base_url=get_config("llmBaseUrl"))
        
        response = await client.chat.completions.create(
            model=get_config("llmModel", "glm-4"),
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt_text}
            ],
            temperature=0.3
        )
        
        content = response.choices[0].message.content
        
        # 清洗 JSON
        analysis_list = []
        try:
            clean_content = content.replace("```json", "").replace("```", "").strip()
            analysis_list = json.loads(clean_content)
        except json.JSONDecodeError:
            match = re.search(r'\[.*\]', content, re.DOTALL)
            if match:
                analysis_list = json.loads(match.group(0))

        # 合并数据
        analysis_map = {item.get('index', 0)-1: item for item in analysis_list}

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

async def generate_article_for_topic(topic: Dict, platform: str):
    """针对单个 Topic 生成文章"""
    api_key = get_config("llmApiKey")
    if not api_key: return None

    add_log('info', f"正在生成 [{platform}] 文案: {topic['title']}")
    
    try:
        client = AsyncOpenAI(api_key=api_key, base_url=get_config("llmBaseUrl"))
        
        system_prompt = "你是一个专业自媒体编辑。"
        if platform == "wechat":
            system_prompt += "请写一篇深度公众号文章，HTML格式，包含标题、摘要、正文。"
        
        # 启用联网搜索
        tools_config = [{
            "type": "web_search",
            "web_search": {
                "enable": True,
                "search_result": True
            }
        }]

        response = await client.chat.completions.create(
            model=get_config("llmModel", "glm-4"),
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