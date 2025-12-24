"""
用户文章 API 路由
提供文章的创建、查询、更新、删除等功能
"""
from fastapi import APIRouter, HTTPException, Depends, status, Query
from pydantic import BaseModel
from typing import Optional

from core.auth import get_current_user
from core.articles import (
    create_article, get_user_articles, get_article_by_share_token,
    get_article_by_id, update_article_public_status, delete_article
)
from core.llm import generate_article_for_topic
from core.config import add_log

router = APIRouter(tags=["articles"], prefix="/articles")


class GenerateAndSaveRequest(BaseModel):
    """生成并保存文章请求"""
    topic: dict
    platform: str
    title: Optional[str] = None
    is_public: bool = False


class GenerateAndSaveResponse(BaseModel):
    """生成并保存响应"""
    success: bool
    article_id: Optional[int] = None
    share_token: Optional[str] = None
    content: Optional[str] = None
    message: Optional[str] = None


@router.post("/generate-and-save", response_model=GenerateAndSaveResponse, summary="生成并保存文章")
async def generate_and_save_article(
    req: GenerateAndSaveRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    生成文章并保存到用户文章库

    需要认证
    """
    try:
        # 生成内容
        content = await generate_article_for_topic(req.topic, req.platform)

        # 创建文章
        article_id = await create_article(
            user_id=current_user["id"],
            topic_id=req.topic.get("id"),
            topic_title=req.topic.get("title", ""),
            topic_link=req.topic.get("link"),
            topic_source=req.topic.get("source"),
            title=req.title or f"{req.topic.get('title', '')} - {req.platform}",
            content=content,
            platform=req.platform
        )

        if article_id:
            # 如果需要公开，更新状态
            if req.is_public:
                await update_article_public_status(article_id, current_user["id"], True)

            # 获取文章信息
            article = await get_article_by_id(article_id, current_user["id"])
            add_log('success', f'文章已保存: {article_id}')
            return GenerateAndSaveResponse(
                success=True,
                article_id=article_id,
                share_token=article["share_token"],
                content=content
            )
        else:
            return GenerateAndSaveResponse(
                success=False,
                content=content,
                message="文章已生成但保存失败"
            )
    except Exception as e:
        add_log('error', f'生成并保存失败: {e}')
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/my-articles", summary="获取我的文章")
async def get_my_articles(
    offset: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    current_user: dict = Depends(get_current_user)
):
    """
    获取当前用户的文章列表

    需要认证
    """
    return await get_user_articles(current_user["id"], offset, limit)


@router.get("/{article_id}", summary="获取文章详情")
async def get_article(
    article_id: int,
    current_user: dict = Depends(get_current_user)
):
    """
    获取指定文章的详情

    需要认证且是文章所有者
    """
    article = await get_article_by_id(article_id, current_user["id"])
    if not article:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="文章不存在"
        )
    return article


@router.patch("/{article_id}/visibility", summary="设置文章公开状态")
async def set_article_visibility(
    article_id: int,
    is_public: bool,
    current_user: dict = Depends(get_current_user)
):
    """
    设置文章是否可公开分享

    需要认证且是文章所有者
    """
    success = await update_article_public_status(article_id, current_user["id"], is_public)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="文章不存在"
        )
    return {"message": "可见性已更新", "is_public": is_public}


@router.delete("/{article_id}", summary="删除文章")
async def delete_article_endpoint(
    article_id: int,
    current_user: dict = Depends(get_current_user)
):
    """
    删除指定文章

    需要认证且是文章所有者
    """
    success = await delete_article(article_id, current_user["id"])
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="文章不存在"
        )
    return {"message": "文章已删除"}


@router.get("/share/{share_token}", summary="通过分享链接访问文章")
async def get_shared_article(share_token: str):
    """
    通过分享 token 访问文章（无需认证）

    文章必须设置为公开状态
    """
    article = await get_article_by_share_token(share_token)
    if not article:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="文章不存在或未公开"
        )
    return article
