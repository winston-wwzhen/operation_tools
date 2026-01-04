"""
分类管理 API 路由

提供分类的 CRUD 操作、关键词管理、平台配置等功能：
- 获取分类列表
- 创建/更新/删除分类
- 管理分类关键词
- 配置分类平台
- 初始化默认分类
- 按分类刷新热点
"""
from fastapi import APIRouter, HTTPException, Depends, status, Query
from pydantic import BaseModel
from typing import Optional, List

from core.auth import get_current_user
from db import (
    get_categories,
    get_category_by_id,
    get_categories_with_keywords,
    create_category,
    update_category,
    delete_category,
    update_category_keywords,
    update_category_platforms,
    init_default_categories,
    get_topics_by_category
)
from core.config import add_log

router = APIRouter(tags=["categories"], prefix="/categories")


# ============ 请求/响应模型 ============

class CategoryBase(BaseModel):
    """分类基础模型"""
    name: str
    slug: str
    description: Optional[str] = None
    icon: Optional[str] = None
    color: Optional[str] = None
    is_active: Optional[bool] = True
    sort_order: Optional[int] = 0


class CategoryCreate(CategoryBase):
    """创建分类请求"""
    keywords: Optional[List[str]] = []
    platforms: Optional[List[str]] = []


class CategoryUpdate(BaseModel):
    """更新分类请求"""
    name: Optional[str] = None
    slug: Optional[str] = None
    description: Optional[str] = None
    icon: Optional[str] = None
    color: Optional[str] = None
    is_active: Optional[bool] = None
    sort_order: Optional[int] = None


class KeywordsUpdate(BaseModel):
    """关键词更新请求"""
    keywords: List[str]


class PlatformsUpdate(BaseModel):
    """平台配置更新请求"""
    platforms: List[str]


class RefreshRequest(BaseModel):
    """刷新热点请求"""
    category_ids: Optional[List[int]] = None


# ============ 辅助函数 ============

async def check_is_admin(user: dict) -> bool:
    """检查用户是否为管理员"""
    return user.get('is_admin', False) == 1


# ============ API 端点 ============

@router.get("", summary="获取所有分类")
async def get_categories_endpoint(
    include_inactive: bool = Query(False, description="是否包含未激活的分类")
):
    """
    获取所有分类列表

    返回分类的基本信息，不包含关键词和平台配置
    """
    try:
        categories_list = await get_categories(include_inactive=include_inactive)
        return {"categories": categories_list}

    except Exception as e:
        add_log("ERROR", f"获取分类列表失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/with-keywords", summary="获取所有分类及关键词")
async def get_categories_with_keywords_endpoint():
    """
    获取所有分类及其关键词（用于抓取任务）
    """
    try:
        categories_list = await get_categories_with_keywords()
        return {"categories": categories_list}

    except Exception as e:
        add_log("ERROR", f"获取分类和关键词失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/{category_id}", summary="获取分类详情")
async def get_category_endpoint(category_id: int):
    """
    获取分类详情，包含关键词列表和平台配置
    """
    try:
        category = await get_category_by_id(category_id)

        if not category:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="分类不存在"
            )

        return category

    except HTTPException:
        raise
    except Exception as e:
        add_log("ERROR", f"获取分类详情失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("", summary="创建分类", status_code=status.HTTP_201_CREATED)
async def create_category_endpoint(
    data: CategoryCreate,
    current_user: dict = Depends(get_current_user)
):
    """
    创建新分类（仅管理员）
    """
    # 检查管理员权限
    if not await check_is_admin(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="仅管理员可以创建分类"
        )

    try:
        category_data = data.model_dump()
        category_id = await create_category(category_data)

        return {
            "id": category_id,
            "message": "分类创建成功"
        }

    except Exception as e:
        add_log("ERROR", f"创建分类失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.put("/{category_id}", summary="更新分类")
async def update_category_endpoint(
    category_id: int,
    data: CategoryUpdate,
    current_user: dict = Depends(get_current_user)
):
    """
    更新分类信息（仅管理员）
    """
    # 检查管理员权限
    if not await check_is_admin(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="仅管理员可以更新分类"
        )

    try:
        # 检查分类是否存在
        existing = await get_category_by_id(category_id)
        if not existing:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="分类不存在"
            )

        # 只包含提供的字段
        update_data = {k: v for k, v in data.model_dump().items() if v is not None}

        success = await update_category(category_id, update_data)

        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="更新分类失败"
            )

        return {"message": "分类更新成功"}

    except HTTPException:
        raise
    except Exception as e:
        add_log("ERROR", f"更新分类失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.delete("/{category_id}", summary="删除分类")
async def delete_category_endpoint(
    category_id: int,
    current_user: dict = Depends(get_current_user)
):
    """
    删除分类（仅管理员）

    注意：删除分类会级联删除其关键词和平台配置
    """
    # 检查管理员权限
    if not await check_is_admin(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="仅管理员可以删除分类"
        )

    try:
        # 检查分类是否存在
        existing = await get_category_by_id(category_id)
        if not existing:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="分类不存在"
            )

        success = await delete_category(category_id)

        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="删除分类失败"
            )

        return {"message": "分类删除成功"}

    except HTTPException:
        raise
    except Exception as e:
        add_log("ERROR", f"删除分类失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/init-defaults", summary="初始化默认分类")
async def init_default_categories_endpoint(
    current_user: dict = Depends(get_current_user)
):
    """
    初始化10个预定义分类（仅管理员）

    如果分类已存在则跳过
    """
    # 检查管理员权限
    if not await check_is_admin(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="仅管理员可以初始化默认分类"
        )

    try:
        created_count = await init_default_categories()

        return {
            "message": f"初始化完成，创建了 {created_count} 个分类",
            "created_count": created_count
        }

    except Exception as e:
        add_log("ERROR", f"初始化默认分类失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.put("/{category_id}/keywords", summary="更新分类关键词")
async def update_keywords_endpoint(
    category_id: int,
    data: KeywordsUpdate,
    current_user: dict = Depends(get_current_user)
):
    """
    更新分类的关键词列表（仅管理员）

    会完全替换原有的关键词列表
    """
    # 检查管理员权限
    if not await check_is_admin(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="仅管理员可以更新关键词"
        )

    try:
        # 检查分类是否存在
        existing = await get_category_by_id(category_id)
        if not existing:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="分类不存在"
            )

        success = await update_category_keywords(category_id, data.keywords)

        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="更新关键词失败"
            )

        return {"message": "关键词更新成功"}

    except HTTPException:
        raise
    except Exception as e:
        add_log("ERROR", f"更新关键词失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.put("/{category_id}/platforms", summary="更新分类平台配置")
async def update_platforms_endpoint(
    category_id: int,
    data: PlatformsUpdate,
    current_user: dict = Depends(get_current_user)
):
    """
    更新分类的平台配置（仅管理员）

    platforms 列表中的平台将被启用，其他平台将被禁用
    """
    # 检查管理员权限
    if not await check_is_admin(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="仅管理员可以更新平台配置"
        )

    try:
        # 检查分类是否存在
        existing = await get_category_by_id(category_id)
        if not existing:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="分类不存在"
            )

        success = await update_category_platforms(category_id, data.platforms)

        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="更新平台配置失败"
            )

        return {"message": "平台配置更新成功"}

    except HTTPException:
        raise
    except Exception as e:
        add_log("ERROR", f"更新平台配置失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/{category_id}/topics", summary="按分类获取热点话题")
async def get_category_topics_endpoint(
    category_id: int,
    start_date: Optional[str] = Query(None, description="起始日期 (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="结束日期 (YYYY-MM-DD)"),
    source: Optional[str] = Query(None, description="数据源筛选"),
    offset: int = Query(0, ge=0, description="偏移量"),
    limit: int = Query(50, ge=1, le=100, description="每页数量")
):
    """
    按分类获取热点话题

    支持按日期范围和数据源进一步筛选
    """
    try:
        # 检查分类是否存在
        category = await get_category_by_id(category_id)
        if not category:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="分类不存在"
            )

        result = await get_topics_by_category(
            category_id=category_id,
            start_date=start_date,
            end_date=end_date,
            source=source,
            offset=offset,
            limit=limit
        )

        return result

    except HTTPException:
        raise
    except Exception as e:
        add_log("ERROR", f"获取分类热点失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/refresh", summary="手动刷新分类热点")
async def refresh_category_topics(
    data: RefreshRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    手动触发分类热点抓取任务（仅管理员）

    可以选择性刷新指定分类，不指定则刷新所有启用的分类
    """
    # 检查管理员权限
    if not await check_is_admin(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="仅管理员可以刷新分类热点"
        )

    try:
        from core.tasks import run_scraper_task
        from threading import Thread
        import asyncio

        category_ids = data.category_ids

        # 在后台线程中运行异步任务
        def run_task():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                if category_ids and len(category_ids) > 0:
                    # 刷新指定的分类
                    for cat_id in category_ids:
                        loop.run_until_complete(run_scraper_task(category_id=cat_id))
                else:
                    # 刷新所有分类（不包含热榜新闻）
                    loop.run_until_complete(run_scraper_task(category_id=None))
            finally:
                loop.close()

        Thread(target=run_task, daemon=True).start()

        return {
            "message": "分类热点刷新任务已启动",
            "category_ids": category_ids
        }

    except Exception as e:
        add_log("ERROR", f"刷新分类热点失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
