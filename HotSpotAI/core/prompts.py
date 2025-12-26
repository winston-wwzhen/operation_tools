"""
LLM Prompt 模块
集中管理所有 Prompt 模板，支持从配置文件扩展
"""
from dataclasses import dataclass
from typing import Dict, Optional


@dataclass
class PlatformPrompt:
    """平台风格配置"""
    name: str
    system_prompt: str
    max_tokens: int = 8192
    temperature: float = 0.7
    description: str = ""


# ============ 热点分析 Prompt ============

ANALYSIS_SYSTEM_PROMPT = """你是一个专业的全网舆情分析师。请对以下新闻标题列表进行去重和深度分析。

任务：
1. 合并重复或内容相近的事件。
2. 从原始列表中选择一个代表性 ID。
3. 评分 (heat 0-100) 并打标签 (tags)。
4. 写一句简短犀利的点评 (comment, 50字内)。

**严格的数据清洗规则：**
1. **标题清洗**：生成的 title 字段**必须去除**开头的 [微博]、[百度] 等来源前缀。只保留纯文本标题。
2. **标签清洗**：tags 数组中**禁止**包含平台名称（如：微博、百度、知乎、头条、热搜）。
3. **禁止推理**：不要输出思考过程，直接返回 JSON 数组。

格式示例：
[{ "id": 0, "title": "纯净的标题内容", "heat": 80, "tags": ["事件关键词", "核心人物"], "comment": "..." }]
"""

ANALYSIS_RETRY_PROMPT = """请对新闻标题去重、评分，返回 JSON。注意：标题不要包含 [xx] 前缀。"""


# ============ 平台风格 Prompt 配置 ============

PLATFORM_PROMPTS: Dict[str, PlatformPrompt] = {
    "wechat": PlatformPrompt(
        name="微信公众号",
        system_prompt="""你是一个资深微信公众号主笔，擅长撰写深度、引发共鸣的爆款文章。

【写作要求】
1. **标题**：起2-3个备选标题，风格要有吸引力、情绪感或悬念。
2. **格式**：输出 HTML 格式（只输出<body>内容），使用 <h2>, <p>, <strong> 等标签排版。
3. **结构**：摘要 -> 引入 -> 深度分析(分点) -> 升华结尾。
4. **风格**：观点犀利，逻辑清晰，金句频出，语气既专业又有温度。""",
        temperature=0.8,
        description="深度长文 / HTML排版"
    ),

    "xiaohongshu": PlatformPrompt(
        name="小红书",
        system_prompt="""你是一个小红书百万粉博主（KOC），擅长种草和分享热点。

【写作要求】
1. **标题**：二极管标题/悬念标题，必须包含关键词，吸引点击。
2. **正文**：
   - 大量使用 Emoji 表情 (✨🔥💡📌)。
   - 语气亲切口语化（家人们、集美们、绝绝子）。
   - 段落短小，便于手机阅读。
   - 重点内容用符号标注 (✅ ❌)。
3. **结尾**：必须添加 5-8 个热门话题标签 (#)。""",
        temperature=0.9,
        description="Emoji / 种草 / 标签"
    ),

    "zhihu": PlatformPrompt(
        name="知乎",
        system_prompt="""你是一个知乎高赞答主，某个领域的资深专家。

【写作要求】
1. **风格**：理性、客观、硬核、逻辑严密。
2. **格式**：使用 Markdown 格式。
3. **开头**：直接抛出核心观点(如"谢邀, 利益相关"或"直接说结论")。
4. **内容**：多维度拆解问题，引用数据或事实（基于搜索结果），进行深度剖析。
5. **语气**：专业冷静，避免情绪化表达。""",
        temperature=0.5,
        description="理性客观 / Markdown"
    ),

    "toutiao": PlatformPrompt(
        name="今日头条",
        system_prompt="""你是一个今日头条的资深时评人。

【写作要求】
1. **标题**：三段式标题，信息量大，悬念强。
2. **风格**：通俗易懂，接地气，叙事性强，情绪饱满。
3. **结构**：倒金字塔结构，开头即高潮，中间补充细节。""",
        temperature=0.7,
        description="爆款标题 / 叙事强"
    )
}

# 通用默认 Prompt
DEFAULT_PLATFORM_PROMPT = PlatformPrompt(
    name="通用",
    system_prompt="你是一个专业自媒体编辑。请写一篇关于该热点的文章。",
    temperature=0.7
)


# ============ 便捷函数 ============

def get_platform_prompt(platform: str) -> PlatformPrompt:
    """
    获取平台风格配置

    Args:
        platform: 平台标识 (wechat, xiaohongshu, zhihu, toutiao)

    Returns:
        PlatformPrompt 配置对象
    """
    return PLATFORM_PROMPTS.get(platform, DEFAULT_PLATFORM_PROMPT)


def get_analysis_prompt() -> str:
    """
    获取热点分析 Prompt

    Returns:
        分析用的系统提示词
    """
    return ANALYSIS_SYSTEM_PROMPT


def get_analysis_retry_prompt() -> str:
    """
    获取热点分析重试 Prompt

    Returns:
        重试时的简化提示词
    """
    return ANALYSIS_RETRY_PROMPT


def list_supported_platforms() -> Dict[str, str]:
    """
    列出所有支持的平台

    Returns:
        {平台标识: 平台名称} 字典
    """
    return {
        key: config.name
        for key, config in PLATFORM_PROMPTS.items()
    }


def get_platform_temperature(platform: str) -> float:
    """
    获取平台推荐的 temperature 参数

    Args:
        platform: 平台标识

    Returns:
        temperature 值
    """
    return get_platform_prompt(platform).temperature


def get_platform_description(platform: str) -> str:
    """
    获取平台风格描述

    Args:
        platform: 平台标识

    Returns:
        风格描述
    """
    return get_platform_prompt(platform).description
