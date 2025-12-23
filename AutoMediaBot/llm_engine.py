import json
import re
from typing import List, Dict
from openai import AsyncOpenAI
from config_manager import add_log, get_config

async def analyze_hot_topics(raw_topics: List[Dict]):
    """
    使用 GLM-4 分析热点列表
    功能：去重聚合、评分、打标签、生成简短点评
    包含重试机制，防止模型返回空内容
    """
    if not raw_topics: return []
    
    api_key = get_config("llmApiKey")
    if not api_key:
        add_log('warning', '未配置 API Key，跳过智能分析')
        return raw_topics

    add_log('info', f'正在调用 GLM-4 分析 {len(raw_topics)} 条原始数据 (进行去重聚合与点评)...')
    
    # 1. 构建输入数据
    prompt_items = [f"{idx}. [{t['source']}] {t['title']}" for idx, t in enumerate(raw_topics)]
    prompt_text = "\n".join(prompt_items)
    
    add_log('info', f"Prompt 构建完成，输入长度: {len(prompt_text)} 字符")

    client = AsyncOpenAI(api_key=api_key, base_url=get_config("llmBaseUrl"))
    model_name = get_config("llmModel", "glm-4")

    # 定义请求包装函数
    async def request_llm(sys_prompt, temp):
        try:
            resp = await client.chat.completions.create(
                model=model_name,
                messages=[
                    {"role": "system", "content": sys_prompt},
                    {"role": "user", "content": f"以下是原始标题列表：\n{prompt_text}"}
                ],
                temperature=temp,
                max_tokens=2500
            )
            return resp.choices[0].message.content
        except Exception as e:
            add_log('warning', f'LLM 请求发生异常: {e}')
            return ""

    # === 尝试 1: 标准 Prompt ===
    system_prompt_v1 = (
        "你是一个专业的全网舆情分析师。请对以下新闻标题列表进行去重和深度分析。\n"
        "任务：\n"
        "1. 合并重复或内容相近的事件。\n"
        "2. 从原始列表中选择一个代表性 ID。\n"
        "3. 评分 (heat 0-100) 并打标签 (tags)。\n"
        "4. 写一句简短犀利的点评 (comment, 50字内)。\n"
        "\n"
        "请返回 JSON 数组格式，不要包含 Markdown 标记。格式示例：\n"
        "[{ \"id\": 0, \"title\": \"...\", \"heat\": 80, \"tags\": [\"...\"], \"comment\": \"...\" }]"
    )
    
    content = await request_llm(system_prompt_v1, 0.4) # 稍微提高温度

    # === 尝试 2: 降级重试 (如果第一次为空) ===
    if not content or not content.strip():
        add_log('warning', 'LLM 第一次返回为空，尝试使用简化 Prompt 进行重试...')
        system_prompt_simple = "请对以下新闻标题进行去重、评分和点评。请直接返回 JSON 数组，包含 id, title, heat, tags, comment 字段。"
        content = await request_llm(system_prompt_simple, 0.7) # 进一步提高温度以打破死循环

    # === 结果检查 ===
    if not content or not content.strip():
        add_log('error', 'LLM 重试后依然返回空内容，将展示原始数据。')
        return raw_topics

    # [Log] 记录原始内容
    add_log('info', f"LLM 返回内容预览: {content[:100].replace(chr(10), ' ')}...")

    # 3. 清洗与解析
    analysis_list = []
    clean_content = content.replace("```json", "").replace("```", "").strip()
    
    try:
        # 策略 A: 直接解析
        analysis_list = json.loads(clean_content)
    except json.JSONDecodeError:
        add_log('warning', f'标准 JSON 解析失败，尝试截取数组部分...')
        try:
            # 策略 B: 寻找 []
            start_idx = clean_content.find('[')
            end_idx = clean_content.rfind(']')
            if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
                json_candidate = clean_content[start_idx : end_idx + 1]
                analysis_list = json.loads(json_candidate)
                add_log('success', '通过截取 [] 成功恢复 JSON 数据')
            else:
                add_log('error', '无法找到有效的 JSON 数组标记 []')
                return raw_topics
        except Exception as e:
             add_log('error', f'JSON 解析最终失败: {e}')
             return raw_topics

    # 4. 结构校验与提取
    if not isinstance(analysis_list, list):
        if isinstance(analysis_list, dict):
            # 尝试提取字典中的列表
            for key in analysis_list:
                if isinstance(analysis_list[key], list):
                    analysis_list = analysis_list[key]
                    break
        if not isinstance(analysis_list, list):
            add_log('error', '解析出的数据类型不正确 (期望 List)')
            return raw_topics

    # 5. 重组数据
    final_list = []
    try:
        for item in analysis_list:
            original_idx = item.get('id')
            if isinstance(original_idx, (int, str)) and str(original_idx).isdigit():
                original_idx = int(original_idx)
                if 0 <= original_idx < len(raw_topics):
                    original_data = raw_topics[original_idx]
                    new_topic = {
                        "title": item.get('title', original_data['title']),
                        "link": original_data['link'],
                        "source": original_data['source'],
                        "heat": item.get('heat', 50),
                        "tags": item.get('tags', []),
                        "comment": item.get('comment', '')
                    }
                    final_list.append(new_topic)
    except Exception as e:
        add_log('error', f'数据重组过程出错: {e}')
        return raw_topics
        
    final_list.sort(key=lambda x: x['heat'], reverse=True)
    add_log('success', f'分析完成！聚合后剩余 {len(final_list)} 条热点')
    return final_list

async def generate_article_for_topic(topic: Dict, platform: str):
    """针对单个 Topic 生成文章 (保持不变)"""
    api_key = get_config("llmApiKey")
    if not api_key: return None

    add_log('info', f"正在生成 [{platform}] 文案: {topic['title']}")
    
    try:
        client = AsyncOpenAI(api_key=api_key, base_url=get_config("llmBaseUrl"))
        
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