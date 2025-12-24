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

    add_log('info', f'正在初始化 LLM 客户端，模型: {get_config("llmModel", "glm-4")}')
    add_log('info', f'API 地址: {get_config("llmBaseUrl")}')
    add_log('info', f'超时设置: {get_config("llmTimeout")} 秒')

    client = AsyncOpenAI(
        api_key=api_key,
        base_url=get_config("llmBaseUrl"),
        timeout=get_config("llmTimeout", 600)
    )
    model_name = get_config("llmModel", "glm-4")

    # 内部请求函数
    @llm_retry
    async def request_llm(sys_prompt, temp):
        try:
            add_log('info', f'开始调用 LLM API (temperature={temp})...')
            resp = await client.chat.completions.create(
                model=model_name,
                messages=[
                    {"role": "system", "content": sys_prompt},
                    {"role": "user", "content": f"以下是原始标题列表：\n{prompt_text}"}
                ],
                temperature=temp,
                max_tokens=40960
            )
            add_log('info', f'LLM 响应成功，开始解析结果...')
            choice = resp.choices[0]
            content = choice.message.content
            add_log('info', f'LLM 返回内容长度: {len(content) if content else 0} 字符')
            return content if content else ""
        except Exception as e:
            add_log('error', f'LLM 请求发生异常: {type(e).__name__}: {e}')
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

    add_log('info', f"开始生成 [{platform}] 文案...")
    add_log('info', f"主题: {topic['title']}")
    add_log('info', f"来源: {topic.get('source', '网络')}")

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
        add_log('info', f'初始化 LLM 客户端 (超时: {get_config("llmTimeout", 600)}秒)...')
        client = AsyncOpenAI(
            api_key=api_key,
            base_url=get_config("llmBaseUrl"),
            timeout=get_config("llmTimeout", 600)
        )

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

        add_log('info', '调用 LLM API 进行文案生成 (联网搜索已启用)...')
        response = await client.chat.completions.create(
            model=get_config("llmModel", "glm-4"),
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            tools=tools_config
        )

        content = response.choices[0].message.content
        add_log('info', f'文案生成完成，内容长度: {len(content) if content else 0} 字符')
        return content

    except Exception as e:
        error_msg = f"文案生成失败: {type(e).__name__}: {e}"
        add_log('error', error_msg)
        return error_msg


# ==================== 新增：批量分析和精选功能 ====================

async def analyze_news_batch(news_list: List[Dict]) -> List[Dict]:
    """
    批量分析新闻（用于定时任务）
    对每条新闻进行评分和简短点评

    Args:
        news_list: 新闻列表，每条包含 id, title, content, source, tags 等

    Returns:
        分析结果列表，每项包含 success, score, comment
    """
    results = []

    if not news_list:
        return results

    api_key = get_config("llmApiKey")
    if not api_key:
        add_log('warning', '未配置 API Key，跳过批量分析')
        # 返回默认结果
        return [{'success': False, 'error': '未配置 API Key'} for _ in news_list]

    try:
        # 构建批量分析输入
        prompt_items = []
        for i, news in enumerate(news_list):
            title = news.get('title', '')[:100]  # 限制长度
            content = news.get('content', '')[:200]  # 取部分内容
            source = news.get('source', '')
            prompt_items.append(f"{i}. [{source}] {title}")

        prompt_text = "\n".join(prompt_items)

        system_prompt = (
            "你是一个专业的内容分析师。请对以上新闻列表进行评分和点评。\n"
            "评分标准 (0-10分):\n"
            "1. 时效性 (3分): 越新越高\n"
            "2. 热度 (3分): 越热门越高\n"
            "3. 价值性 (4分): 内容是否重要、有趣、有讨论价值\n\n"
            "点评要求: 简短精炼，20字以内，点出核心看点\n\n"
            "请返回 JSON 数组格式:\n"
            "[\n"
            "  {\"index\": 0, \"score\": 8.5, \"comment\": \"核心看点\"},\n"
            "  {\"index\": 1, \"score\": 7.0, \"comment\": \"核心看点\"},\n"
            "  ...\n"
            "]\n\n"
            "只返回 JSON，不要有其他内容。"
        )

        add_log('info', f'正在批量分析 {len(news_list)} 条新闻...')

        client = AsyncOpenAI(
            api_key=api_key,
            base_url=get_config("llmBaseUrl"),
            timeout=get_config("llmTimeout", 300)
        )

        @llm_retry
        async def request_llm():
            response = await client.chat.completions.create(
                model=get_config("llmModel", "glm-4"),
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt_text}
                ],
                temperature=0.3,
                max_tokens=8192
            )
            return response.choices[0].message.content

        content = await request_llm()

        # 解析结果
        clean_content = content.replace("```json", "").replace("```", "").strip()
        try:
            start = clean_content.find('[')
            end = clean_content.rfind(']')
            if start != -1 and end != -1:
                analysis_list = json.loads(clean_content[start:end+1])

                # 构建结果映射
                score_map = {}
                for item in analysis_list:
                    idx = item.get('index')
                    if isinstance(idx, int) and 0 <= idx < len(news_list):
                        score_map[idx] = {
                            'score': item.get('score', 5.0),
                            'comment': item.get('comment', ''),
                            'success': True
                        }

                # 按顺序生成结果
                for i in range(len(news_list)):
                    if i in score_map:
                        results.append(score_map[i])
                    else:
                        # LLM 漏掉的，给默认分
                        results.append({
                            'success': True,
                            'score': 5.0,
                            'comment': ''
                        })

                add_log('success', f'批量分析完成，成功 {len([r for r in results if r.get("success")])} 条')
            else:
                raise ValueError("无法解析 JSON 数组")

        except Exception as e:
            add_log('warning', f'批量分析解析失败: {e}，使用规则评分')
            # 失败时使用规则评分
            for news in news_list:
                heat = news.get('heat', 0)
                # 将热度转换为 0-10 分
                score = min(10.0, heat / 10.0)
                results.append({
                    'success': True,
                    'score': score,
                    'comment': ''
                })

    except Exception as e:
        add_log('error', f'批量分析失败: {e}')
        # 返回失败结果
        return [{'success': False, 'error': str(e)} for _ in news_list]

    return results


async def select_hot_topics(news_list: List[Dict], count: int = 20) -> List[Dict]:
    """
    使用 AI 从候选新闻中精选热点话题

    Args:
        news_list: 候选新闻列表（已评分）
        count: 最终精选数量

    Returns:
        精选后的热点话题列表
    """
    if not news_list:
        return []

    if len(news_list) <= count:
        # 候选数量不足，直接返回（格式化字段）
        return [{
            'title': n.get('title', ''),
            'link': n.get('link', ''),
            'source': n.get('source', ''),
            'ai_score': n.get('ai_score'),
            'ai_comment': n.get('ai_comment', ''),
            'category_id': n.get('category_id')
        } for n in news_list]

    api_key = get_config("llmApiKey")
    if not api_key:
        add_log('warning', '未配置 API Key，使用规则排序')
        # 使用规则排序：按 ai_score 排序
        sorted_news = sorted(news_list, key=lambda x: x.get('ai_score', 0), reverse=True)
        return [{
            'title': n.get('title', ''),
            'link': n.get('link', ''),
            'source': n.get('source', ''),
            'ai_score': n.get('ai_score'),
            'ai_comment': n.get('ai_comment', ''),
            'category_id': n.get('category_id')
        } for n in sorted_news[:count]]

    try:
        # 构建输入，取前 50 条候选
        candidates = news_list[:50]
        prompt_items = []
        for i, news in enumerate(candidates):
            title = news.get('title', '')[:80]
            score = news.get('ai_score', 0)
            hours_ago = news.get('created_at', '')
            prompt_items.append(f"{i}. {title} (评分:{score}, 时间:{hours_ago})")

        prompt_text = "\n".join(prompt_items)

        system_prompt = (
            f"你是一个热点话题精选专家。请从以上候选新闻中精选出 {count} 条最具价值的热点。\n\n"
            "精选标准:\n"
            "1. 时效性：优先最新事件\n"
            "2. 热度：优先讨论度高的事件\n"
            "3. 价值性：优先有社会影响、公众关注的事件\n"
            "4. 多样性：避免选太多同类型新闻\n\n"
            f"请返回精选的 {count} 条新闻的索引号（0-{len(candidates)-1}），用逗号分隔。\n\n"
            "示例: 0, 3, 5, 7, 12, 15, 18, 22, 25, 28, 33, 37, 40, 42, 45, 47, 48, 49, 50"
        )

        add_log('info', f'正在使用 AI 从 {len(candidates)} 条候选中精选 {count} 条...')

        client = AsyncOpenAI(
            api_key=api_key,
            base_url=get_config("llmBaseUrl"),
            timeout=get_config("llmTimeout", 300)
        )

        response = await client.chat.completions.create(
            model=get_config("llmModel", "glm-4"),
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt_text}
            ],
            temperature=0.5,
            max_tokens=2048
        )

        content = response.choices[0].message.content.strip()

        # 解析索引
        import re
        indices = re.findall(r'\d+', content)
        selected_indices = [int(i) for i in indices if 0 <= int(i) < len(candidates)]

        if len(selected_indices) < count:
            # AI 选得不够，补充规则排序
            add_log('warning', f'AI 只选了 {len(selected_indices)} 条，补充规则排序')
            all_indices = set(range(len(candidates)))
            remaining = list(all_indices - set(selected_indices))
            # 按 ai_score 排序补充
            remaining.sort(
                key=lambda i: candidates[i].get('ai_score', 0),
                reverse=True
            )
            selected_indices.extend(remaining[:count - len(selected_indices)])

        # 构建最终结果
        selected = []
        for idx in selected_indices[:count]:
            news = candidates[idx]
            selected.append({
                'title': news.get('title', ''),
                'link': news.get('link', ''),
                'source': news.get('source', ''),
                'ai_score': news.get('ai_score'),
                'ai_comment': news.get('ai_comment', ''),
                'category_id': news.get('category_id')
            })

        add_log('success', f'AI 精选完成，共 {len(selected)} 条')
        return selected

    except Exception as e:
        add_log('warning', f'AI 精选失败: {e}，使用规则排序')
        # 失败时使用规则排序
        sorted_news = sorted(news_list, key=lambda x: x.get('ai_score', 0), reverse=True)
        return [{
            'title': n.get('title', ''),
            'link': n.get('link', ''),
            'source': n.get('source', ''),
            'ai_score': n.get('ai_score'),
            'ai_comment': n.get('ai_comment', ''),
            'category_id': n.get('category_id')
        } for n in sorted_news[:count]]

