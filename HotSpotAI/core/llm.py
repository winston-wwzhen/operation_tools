"""
LLM 引擎模块
处理与 GLM-4 等 AI 模型的交互
"""
import json
import re
from typing import List, Dict
from openai import AsyncOpenAI
from core.config import add_log, get_config
from utils import llm_retry


async def analyze_hot_topics(raw_topics: List[Dict]):
    """
    使用 GLM-4 分析热点列表
    优化：去重聚合、评分、打标签、生成简短点评
    修复：强制清洗标题中的 [来源] 前缀，移除与来源重复的标签
    """
    if not raw_topics:
        return []

    api_key = get_config("llmApiKey")
    if not api_key:
        add_log('warning', '未配置 API Key，跳过智能分析')
        return raw_topics

    # 1. 构建输入 (保留来源前缀供 AI 参考，但在 Output 中要求去除)
    prompt_items = [f"{idx}. [{t['source']}] {t['title']}" for idx, t in enumerate(raw_topics)]
    prompt_text = "\n".join(prompt_items)

    add_log('info', f"Prompt 构建完成，输入长度: {len(prompt_text)} 字符")

    client = AsyncOpenAI(api_key=api_key, base_url=get_config("llmBaseUrl"))
    model_name = get_config("llmModel", "glm-4")

    # 内部请求函数
    @llm_retry
    async def request_llm(sys_prompt, temp):
        try:
            resp = await client.chat.completions.create(
                model=model_name,
                messages=[
                    {"role": "system", "content": sys_prompt},
                    {"role": "user", "content": f"以下是原始标题列表：\n{prompt_text}"}
                ],
                temperature=temp,
                max_tokens=40960
            )
            choice = resp.choices[0]
            content = choice.message.content
            return content if content else ""
        except Exception as e:
            add_log('warning', f'LLM 请求发生异常: {e}')
            return ""

    # 2. 调用 LLM - 优化 Prompt 指令
    system_prompt_v1 = (
        "你是一个专业的全网舆情分析师。请对以下新闻标题列表进行去重和深度分析。\n"
        "任务：\n"
        "1. 合并重复或内容相近的事件。\n"
        "2. 从原始列表中选择一个代表性 ID。\n"
        "3. 评分 (heat 0-100) 并打标签 (tags)。\n"
        "4. 写一句简短犀利的点评 (comment, 50字内)。\n"
        "\n"
        "**严格的数据清洗规则：**\n"
        "1. **标题清洗**：生成的 title 字段**必须去除**开头的 [微博]、[百度] 等来源前缀。只保留纯文本标题。\n"
        "2. **标签清洗**：tags 数组中**禁止**包含平台名称（如：微博、百度、知乎、头条、热搜）。\n"
        "3. **禁止推理**：不要输出思考过程，直接返回 JSON 数组。\n"
        "\n"
        "格式示例：\n"
        "[{ \"id\": 0, \"title\": \"纯净的标题内容\", \"heat\": 80, \"tags\": [\"事件关键词\", \"核心人物\"], \"comment\": \"...\" }]"
    )

    content = await request_llm(system_prompt_v1, 0.2)

    # 简单的重试逻辑
    if not content or not content.strip():
        add_log('warning', 'LLM 返回为空，尝试重试...')
        content = await request_llm("请对新闻标题去重、评分，返回 JSON。注意：标题不要包含 [xx] 前缀。", 0.5)

    # 3. 解析与重组
    clean_content = content.replace("```json", "").replace("```", "").strip()
    analysis_list = []

    try:
        start = clean_content.find('[')
        end = clean_content.rfind(']')
        if start != -1 and end != -1:
            analysis_list = json.loads(clean_content[start:end+1])
    except Exception as e:
        add_log('error', f'JSON 解析失败: {e}')
        return raw_topics

    final_list = []
    if isinstance(analysis_list, list):
        for item in analysis_list:
            idx = item.get('id')
            if isinstance(idx, (int, str)) and str(idx).isdigit():
                idx = int(idx)
                if 0 <= idx < len(raw_topics):
                    orig = raw_topics[idx]

                    # === 数据强制清洗 (防止 LLM 不听话) ===

                    # 1. 清洗标题中的来源前缀 (如 "[微博] xxx" -> "xxx")
                    raw_title = item.get('title', orig['title']).strip()
                    source_name = orig['source']

                    # 定义需要剔除的脏字符模式
                    dirty_prefixes = [
                        f"[{source_name}]", f"【{source_name}】",
                        f"[{source_name}热搜]", f"【{source_name}热搜】",
                        "[]", "【】"
                    ]

                    clean_title = raw_title
                    for dirty in dirty_prefixes:
                        clean_title = clean_title.replace(dirty, "")
                    clean_title = clean_title.strip()

                    # 2. 清洗标签 (移除包含来源名的标签)
                    raw_tags = item.get('tags', [])
                    clean_tags = []
                    for tag in raw_tags:
                        # 如果标签不包含平台名，且长度适中，则保留
                        if source_name not in tag and len(tag) < 10:
                            clean_tags.append(tag)

                    final_list.append({
                        "title": clean_title,
                        "link": orig['link'],
                        "source": orig['source'],
                        "heat": item.get('heat', 50),
                        "tags": clean_tags,
                        "comment": item.get('comment', '')
                    })

    final_list.sort(key=lambda x: x['heat'], reverse=True)
    return final_list if final_list else raw_topics


async def generate_article_for_topic(topic: Dict, platform: str):
    """
    针对单个 Topic 生成不同平台风格的文章
    支持：wechat (公众号), xiaohongshu (小红书), zhihu (知乎), toutiao (头条)
    """
    api_key = get_config("llmApiKey")
    if not api_key:
        return "请先配置 LLM API Key"

    add_log('info', f"正在生成 [{platform}] 文案: {topic['title']}")

    # === 定义不同平台的 Prompt ===
    prompts = {
        "wechat": (
            "你是一个资深微信公众号主笔，擅长撰写深度、引发共鸣的爆款文章。\n"
            "【写作要求】\n"
            "1. **标题**：起2-3个备选标题，风格要有吸引力、情绪感或悬念。\n"
            "2. **格式**：输出 HTML 格式（只输出<body>内容），使用 <h2>, <p>, <strong> 等标签排版。\n"
            "3. **结构**：摘要 -> 引入 -> 深度分析(分点) -> 升华结尾。\n"
            "4. **风格**：观点犀利，逻辑清晰，金句频出，语气既专业又有温度。"
        ),
        "xiaohongshu": (
            "你是一个小红书百万粉博主（KOC），擅长种草和分享热点。\n"
            "【写作要求】\n"
            "1. **标题**：二极管标题/悬念标题，必须包含关键词，吸引点击。\n"
            "2. **正文**：\n"
            "   - 大量使用 Emoji 表情 (✨🔥💡📌)。\n"
            "   - 语气亲切口语化（家人们、集美们、绝绝子）。\n"
            "   - 段落短小，便于手机阅读。\n"
            "   - 重点内容用符号标注 (✅ ❌)。\n"
            "3. **结尾**：必须添加 5-8 个热门话题标签 (#)。"
        ),
        "zhihu": (
            "你是一个知乎高赞答主，某个领域的资深专家。\n"
            "【写作要求】\n"
            "1. **风格**：理性、客观、硬核、逻辑严密。\n"
            "2. **格式**：使用 Markdown 格式。\n"
            "3. **开头**：直接抛出核心观点(如\"谢邀, 利益相关\"或\"直接说结论\")。\n"
            "4. **内容**：多维度拆解问题，引用数据或事实（基于搜索结果），进行深度剖析。\n"
            "5. **语气**：专业冷静，避免情绪化表达。"
        ),
        "toutiao": (
            "你是一个今日头条的资深时评人。\n"
            "【写作要求】\n"
            "1. **标题**：三段式标题，信息量大，悬念强。\n"
            "2. **风格**：通俗易懂，接地气，叙事性强，情绪饱满。\n"
            "3. **结构**：倒金字塔结构，开头即高潮，中间补充细节。"
        )
    }

    # 默认回退到通用 Prompt
    system_prompt = prompts.get(platform, "你是一个专业自媒体编辑。请写一篇关于该热点的文章。")

    try:
        client = AsyncOpenAI(api_key=api_key, base_url=get_config("llmBaseUrl"))

        # 启用联网搜索工具，确保内容时效性
        tools_config = [{
            "type": "web_search",
            "web_search": {
                "enable": True,
                "search_result": True
            }
        }]

        user_prompt = (
            f"热点事件：【{topic['title']}】\n"
            f"来源：{topic.get('source', '网络')}\n\n"
            "请先利用联网搜索工具查询该事件的最新起因、经过、结果和各方观点。\n"
            "然后基于搜索到的事实，严格按照 System Prompt 中的平台风格要求进行创作。"
        )

        response = await client.chat.completions.create(
            model=get_config("llmModel", "glm-4"),
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            tools=tools_config
        )

        return response.choices[0].message.content

    except Exception as e:
        error_msg = f"文案生成失败: {e}"
        add_log('error', error_msg)
        return error_msg
