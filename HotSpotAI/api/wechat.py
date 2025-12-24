"""
微信公众号 API 路由

提供微信公众号账号管理和文章发布功能：
- 绑定/解绑公众号账号
- 保存文章为草稿
- 自动发布文章
- 查询发布记录
"""
import aiosqlite
from fastapi import APIRouter, HTTPException, Depends, status, Query
from pydantic import BaseModel
from typing import Optional, List

from core.auth import get_current_user
from core.wechat import WeChatPublisher
from core.config import add_log

router = APIRouter(tags=["wechat"], prefix="/wechat")

# 数据库文件路径
DB_FILE = "data.db"


# ============ 请求/响应模型 ============

class BindAccountRequest(BaseModel):
    """绑定公众号请求"""
    app_id: str
    secret: str
    account_name: Optional[str] = None


class BindAccountResponse(BaseModel):
    """绑定公众号响应"""
    success: bool
    account_id: Optional[int] = None
    message: Optional[str] = None


class SaveDraftRequest(BaseModel):
    """保存草稿请求"""
    wechat_account_id: int


class PublishRequest(BaseModel):
    """发布文章请求"""
    wechat_account_id: int


class PublishResponse(BaseModel):
    """发布响应"""
    success: bool
    media_id: Optional[str] = None
    publish_id: Optional[str] = None
    published_at: Optional[str] = None
    log_id: Optional[int] = None
    message: Optional[str] = None


# ============ 辅助函数 ============

async def get_db():
    """获取数据库连接"""
    return await aiosqlite.connect(DB_FILE)


async def get_wechat_accounts_list(user_id: int) -> List[dict]:
    """获取用户的公众号账号列表"""
    async with aiosqlite.connect(DB_FILE) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute('''
            SELECT id, app_id, account_name, nickname, avatar_url, is_active, created_at
            FROM wechat_accounts
            WHERE user_id = ?
            ORDER BY created_at DESC
        ''', (user_id,)) as cursor:
            rows = await cursor.fetchall()

        return [
            {
                "id": r["id"],
                "app_id": r["app_id"],
                "account_name": r["account_name"],
                "nickname": r["nickname"],
                "avatar_url": r["avatar_url"],
                "is_active": bool(r["is_active"]),
                "created_at": r["created_at"]
            }
            for r in rows
        ]


# ============ API 端点 ============

@router.post("/accounts", response_model=BindAccountResponse, summary="绑定公众号")
async def bind_wechat_account(
    req: BindAccountRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    绑定微信公众号账号

    AppID 和 Secret 可在微信公众平台 > 开发 > 基本配置中获取
    """
    try:
        async with aiosqlite.connect(DB_FILE) as db:
            # 检查是否已绑定相同的 app_id
            db.row_factory = aiosqlite.Row
            async with db.execute(
                "SELECT id FROM wechat_accounts WHERE user_id = ? AND app_id = ?",
                (current_user["id"], req.app_id)
            ) as cursor:
                existing = await cursor.fetchone()

            if existing:
                return BindAccountResponse(
                    success=False,
                    message="该公众号已绑定"
                )

            # 插入新账号
            await db.execute('''
                INSERT INTO wechat_accounts (user_id, app_id, secret, account_name)
                VALUES (?, ?, ?, ?)
            ''', (current_user["id"], req.app_id, req.secret, req.account_name))
            await db.commit()

            # 获取新插入的 ID
            async with db.execute("SELECT last_insert_rowid() as id") as cursor:
                row = await cursor.fetchone()
                account_id = row["id"]

            add_log("INFO", f"用户 {current_user['id']} 绑定公众号: {req.app_id}")

            return BindAccountResponse(
                success=True,
                account_id=account_id,
                message="公众号绑定成功"
            )

    except Exception as e:
        add_log("ERROR", f"绑定公众号失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/accounts", summary="获取已绑定的公众号列表")
async def get_wechat_accounts(
    current_user: dict = Depends(get_current_user)
):
    """
    获取当前用户绑定的所有公众号账号

    返回的列表中 Secret 会被隐藏
    """
    try:
        accounts = await get_wechat_accounts_list(current_user["id"])
        return {"accounts": accounts}

    except Exception as e:
        add_log("ERROR", f"获取公众号列表失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.delete("/accounts/{account_id}", summary="解绑公众号")
async def unbind_wechat_account(
    account_id: int,
    current_user: dict = Depends(get_current_user)
):
    """
    解绑公众号账号

    注意：解绑后无法使用该账号发布文章
    """
    try:
        async with aiosqlite.connect(DB_FILE) as db:
            # 检查账号是否属于当前用户
            db.row_factory = aiosqlite.Row
            async with db.execute(
                "SELECT id FROM wechat_accounts WHERE id = ? AND user_id = ?",
                (account_id, current_user["id"])
            ) as cursor:
                account = await cursor.fetchone()

            if not account:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="账号不存在"
                )

            # 删除账号
            await db.execute(
                "DELETE FROM wechat_accounts WHERE id = ?",
                (account_id,)
            )
            await db.commit()

            add_log("INFO", f"用户 {current_user['id']} 解绑公众号: {account_id}")

            return {"message": "公众号已解绑"}

    except HTTPException:
        raise
    except Exception as e:
        add_log("ERROR", f"解绑公众号失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/articles/{article_id}/draft", response_model=PublishResponse, summary="保存为草稿")
async def save_as_draft(
    article_id: int,
    req: SaveDraftRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    将文章保存为微信公众号草稿

    草稿保存在公众平台的草稿箱中，需要人工审核后手动发布
    """
    # 使用传入的 wechat_account_id（优先于请求体中的）
    wechat_account_id = req.wechat_account_id

    try:
        async with aiosqlite.connect(DB_FILE) as db:
            publisher = WeChatPublisher(db)

            # 验证文章和账号所有权
            db.row_factory = aiosqlite.Row
            async with db.execute(
                "SELECT id FROM wechat_accounts WHERE id = ? AND user_id = ?",
                (wechat_account_id, current_user["id"])
            ) as cursor:
                if not await cursor.fetchone():
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="无权使用该公众号"
                    )

            # 保存草稿
            result = await publisher.save_draft(article_id, current_user["id"], wechat_account_id)

            return PublishResponse(
                success=True,
                media_id=result.get("media_id"),
                log_id=result.get("log_id"),
                message="草稿保存成功"
            )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        add_log("ERROR", f"保存草稿失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/articles/{article_id}/publish", response_model=PublishResponse, summary="自动发布")
async def publish_to_wechat(
    article_id: int,
    req: PublishRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    自动发布文章到微信公众号

    注意：此操作会直接发布文章，请确保内容已审核
    建议先使用草稿功能预览，确认无误后再发布
    """
    wechat_account_id = req.wechat_account_id

    try:
        async with aiosqlite.connect(DB_FILE) as db:
            publisher = WeChatPublisher(db)

            # 验证文章和账号所有权
            db.row_factory = aiosqlite.Row
            async with db.execute(
                "SELECT id FROM wechat_accounts WHERE id = ? AND user_id = ?",
                (wechat_account_id, current_user["id"])
            ) as cursor:
                if not await cursor.fetchone():
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="无权使用该公众号"
                    )

            # 发布文章
            result = await publisher.publish_article(article_id, current_user["id"], wechat_account_id)

            return PublishResponse(
                success=True,
                publish_id=result.get("publish_id"),
                published_at=result.get("published_at"),
                log_id=result.get("log_id"),
                message="文章发布成功"
            )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        add_log("ERROR", f"发布文章失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/publish-logs", summary="获取发布记录")
async def get_publish_logs(
    offset: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    current_user: dict = Depends(get_current_user)
):
    """
    获取当前用户的微信发布记录

    支持分页查询
    """
    try:
        async with aiosqlite.connect(DB_FILE) as db:
            publisher = WeChatPublisher(db)
            result = await publisher.get_publish_logs(current_user["id"], offset, limit)
            return result

    except Exception as e:
        add_log("ERROR", f"获取发布记录失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/articles/{article_id}/publish-status", summary="检查发布限制")
async def check_publish_status(
    article_id: int,
    wechat_account_id: int,
    current_user: dict = Depends(get_current_user)
):
    """
    检查是否可以发布文章

    返回发布频率限制检查结果
    """
    try:
        async with aiosqlite.connect(DB_FILE) as db:
            # 验证账号所有权
            db.row_factory = aiosqlite.Row
            async with db.execute(
                "SELECT id FROM wechat_accounts WHERE id = ? AND user_id = ?",
                (wechat_account_id, current_user["id"])
            ) as cursor:
                if not await cursor.fetchone():
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="无权使用该公众号"
                    )

            publisher = WeChatPublisher(db)
            result = await publisher.check_publish_limits(current_user["id"], wechat_account_id)

            return result

    except HTTPException:
        raise
    except Exception as e:
        add_log("ERROR", f"检查发布状态失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
