"""
内容生成相关 API
"""
from fastapi import APIRouter, BackgroundTasks
from pydantic import BaseModel
from typing import Dict
from core import run_full_pipeline, generate_article_for_topic

router = APIRouter(tags=["content"])


class GenerateRequest(BaseModel):
    """文章生成请求模型"""
    topic: Dict
    platform: str


@router.post("/refresh-topics", summary="刷新热点话题")
async def refresh_topics(background_tasks: BackgroundTasks):
    """
    触发热点聚合完整流程
    依次执行：爬虫 -> AI 分析 -> 热点精选

    使用后台任务执行，避免阻塞 API 响应
    """
    background_tasks.add_task(run_full_pipeline)
    return {"success": True, "message": "正在后台执行完整流程：爬虫 → AI 分析 → 热点精选"}


@router.post("/generate-draft", summary="生成文章草稿")
async def generate_draft(req: GenerateRequest):
    """
    根据选定的热点话题生成平台适配的文章草稿

    Args:
        req.topic: 热点话题对象
        req.platform: 目标平台 (wechat/xiaohongshu/zhihu/toutiao)

    Returns:
        {
            "success": True,
            "content": "# 生成的 Markdown 内容..."
        }
    """
    content = await generate_article_for_topic(req.topic, req.platform)
    return {"success": True, "content": content}
