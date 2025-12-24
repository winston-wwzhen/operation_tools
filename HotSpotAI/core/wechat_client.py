"""
微信公众号 API 客户端

提供微信公众号 API 调用功能：
- AccessToken 管理（带缓存）
- 草稿创建
- 草稿发布
- 错误处理

官方文档：https://developers.weixin.qq.com/doc/offiaccount/Getting_Started/Overview.html
"""
import asyncio
import time
import httpx
from typing import Any, Dict, List, Optional
from .logger import add_log


class WeChatAPIError(Exception):
    """微信 API 错误"""
    def __init__(self, errcode: int, errmsg: str):
        self.errcode = errcode
        self.errmsg = errmsg
        super().__init__(f"[{errcode}] {errmsg}")


class WeChatClient:
    """微信公众号 API 客户端"""

    # API 端点
    API_BASE_URL = "https://api.weixin.qq.com"
    TOKEN_ENDPOINT = "/cgi-bin/token"
    DRAFT_ADD_ENDPOINT = "/cgi-bin/draft/add"
    FREEPUBLISH_SUBMIT_ENDPOINT = "/cgi-bin/freepublish/submit"

    # 常见错误码
    ERROR_CODES = {
        40001: "AppSecret 错误",
        40002: "不合法的凭证类型",
        40013: "不合法的 AppID",
        40014: "不合法的 access_token",
        42001: "access_token 超时",
        42002: "refresh_token 超时",
        45009: "接口调用超过限制",
        46003: "标题长度超过限制",
        46004: "文章内容长度超过限制",
        61070: "草稿箱已满",
    }

    def __init__(self, app_id: str, secret: str, token_cache_time: int = 6600):
        """
        初始化微信客户端

        Args:
            app_id: 微信公众号 AppID
            secret: 微信公众号 Secret
            token_cache_time: access_token 缓存时间（秒），默认 6600（提前 5 分钟刷新）
        """
        self.app_id = app_id
        self.secret = secret
        self.token_cache_time = token_cache_time

        # Token 缓存
        self._access_token: Optional[str] = None
        self._token_expires_at: float = 0  # Unix 时间戳

        # HTTP 客户端
        self._client: Optional[httpx.AsyncClient] = None

    async def _get_client(self) -> httpx.AsyncClient:
        """获取 HTTP 客户端（懒加载）"""
        if self._client is None:
            self._client = httpx.AsyncClient(
                base_url=self.API_BASE_URL,
                timeout=30.0,
                follow_redirects=True
            )
        return self._client

    async def close(self):
        """关闭客户端连接"""
        if self._client:
            await self._client.aclose()
            self._client = None

    async def get_access_token(self, force_refresh: bool = False) -> str:
        """
        获取 access_token（带缓存）

        Args:
            force_refresh: 是否强制刷新

        Returns:
            access_token

        Raises:
            WeChatAPIError: API 调用失败
        """
        current_time = time.time()

        # 检查缓存是否有效
        if not force_refresh and self._access_token and current_time < self._token_expires_at:
            return self._access_token

        # 刷新 token
        return await self._refresh_token()

    async def _refresh_token(self) -> str:
        """
        刷新 access_token

        Returns:
            新的 access_token

        Raises:
            WeChatAPIError: API 调用失败
        """
        client = await self._get_client()

        params = {
            "grant_type": "client_credential",
            "appid": self.app_id,
            "secret": self.secret,
        }

        try:
            add_log("DEBUG", f"正在刷新 access_token (app_id: {self.app_id})")
            response = await client.get(self.TOKEN_ENDPOINT, params=params)
            response.raise_for_status()

            data = response.json()

            if "errcode" in data and data["errcode"] != 0:
                raise WeChatAPIError(data["errcode"], data.get("errmsg", "Unknown error"))

            self._access_token = data["access_token"]
            # 设置过期时间（提前 5 分钟刷新）
            self._token_expires_at = time.time() + self.token_cache_time

            add_log("INFO", f"access_token 刷新成功，将在 {self.token_cache_time} 秒后过期")
            return self._access_token

        except httpx.HTTPStatusError as e:
            add_log("ERROR", f"刷新 access_token 失败: {e}")
            raise WeChatAPIError(-1, f"HTTP 请求失败: {e}")
        except Exception as e:
            add_log("ERROR", f"刷新 access_token 异常: {e}")
            raise WeChatAPIError(-1, str(e))

    async def create_draft(
        self,
        articles: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        创建草稿

        Args:
            articles: 文章列表
                [{
                    "title": "标题",
                    "author": "作者（可选）",
                    "digest": "摘要（可选）",
                    "content": "HTML 内容",
                    "thumb_media_id": "封面图 media_id（可选）",
                    "need_open_comment": 1,  # 是否打开评论（0=不打开，1=打开）
                    "only_fans_can_comment": 0,  # 是否只有粉丝可以评论（0=所有人，1=粉丝）
                }]

        Returns:
            {
                "media_id": "草稿 media_id",
                "create_time": 1234567890
            }

        Raises:
            WeChatAPIError: API 调用失败
        """
        access_token = await self.get_access_token()
        client = await self._get_client()

        # 构建请求数据
        data = {
            "articles": articles
        }

        params = {"access_token": access_token}

        try:
            add_log("DEBUG", f"正在创建草稿，文章数: {len(articles)}")
            response = await client.post(
                self.DRAFT_ADD_ENDPOINT,
                params=params,
                json=data
            )
            response.raise_for_status()

            result = response.json()

            if "errcode" in result and result["errcode"] != 0:
                errmsg = self.ERROR_CODES.get(result["errcode"], result.get("errmsg", "Unknown error"))
                raise WeChatAPIError(result["errcode"], errmsg)

            add_log("INFO", f"草稿创建成功: media_id={result.get('media_id')}")
            return {
                "media_id": result.get("media_id"),
                "create_time": result.get("create_time"),
            }

        except httpx.HTTPStatusError as e:
            add_log("ERROR", f"创建草稿失败: {e}")
            raise WeChatAPIError(-1, f"HTTP 请求失败: {e}")
        except WeChatAPIError:
            raise
        except Exception as e:
            add_log("ERROR", f"创建草稿异常: {e}")
            raise WeChatAPIError(-1, str(e))

    async def publish_draft(self, media_id: str) -> Dict[str, Any]:
        """
        发布草稿

        Args:
            media_id: 草稿 media_id

        Returns:
            {
                "publish_id": "发布任务 ID",
                "msg_id": "消息 ID",
                "msg_data_id": "消息数据 ID"
            }

        Raises:
            WeChatAPIError: API 调用失败
        """
        access_token = await self.get_access_token()
        client = await self._get_client()

        data = {
            "media_id": media_id
        }

        params = {"access_token": access_token}

        try:
            add_log("DEBUG", f"正在发布草稿: media_id={media_id}")
            response = await client.post(
                self.FREEPUBLISH_SUBMIT_ENDPOINT,
                params=params,
                json=data
            )
            response.raise_for_status()

            result = response.json()

            if "errcode" in result and result["errcode"] != 0:
                errmsg = self.ERROR_CODES.get(result["errcode"], result.get("errmsg", "Unknown error"))
                raise WeChatAPIError(result["errcode"], errmsg)

            add_log("INFO", f"草稿发布成功: publish_id={result.get('publish_id')}")
            return {
                "publish_id": result.get("publish_id"),
                "msg_id": result.get("msg_id"),
                "msg_data_id": result.get("msg_data_id"),
            }

        except httpx.HTTPStatusError as e:
            add_log("ERROR", f"发布草稿失败: {e}")
            raise WeChatAPIError(-1, f"HTTP 请求失败: {e}")
        except WeChatAPIError:
            raise
        except Exception as e:
            add_log("ERROR", f"发布草稿异常: {e}")
            raise WeChatAPIError(-1, str(e))

    def get_error_message(self, errcode: int) -> str:
        """获取错误码对应的错误信息"""
        return self.ERROR_CODES.get(errcode, f"未知错误 ({errcode})")


# 测试代码
if __name__ == "__main__":
    async def test():
        # 测试代码需要配置环境变量
        import os
        app_id = os.getenv("WECHAT_APP_ID", "")
        secret = os.getenv("WECHAT_SECRET", "")

        if not app_id or not secret:
            print("请设置 WECHAT_APP_ID 和 WECHAT_SECRET 环境变量")
            return

        client = WeChatClient(app_id, secret)

        try:
            # 测试获取 access_token
            token = await client.get_access_token()
            print(f"access_token: {token[:20]}...")

            # 测试创建草稿
            draft_data = [{
                "title": "测试文章",
                "author": "HotSpotAI",
                "digest": "这是一篇测试文章",
                "content": "<p>这是测试内容</p>",
                "need_open_comment": 1,
                "only_fans_can_comment": 0,
            }]
            result = await client.create_draft(draft_data)
            print(f"草稿创建成功: {result}")

        finally:
            await client.close()

    asyncio.run(test())
