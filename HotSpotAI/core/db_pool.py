"""
数据库连接池管理模块
使用 aiosqlite 提供高效的数据库访问，启用 WAL 模式提升并发性能
"""
import asyncio
import aiosqlite
from contextlib import asynccontextmanager
from typing import AsyncIterator, Optional
from pathlib import Path

from .config import get_settings


class DatabasePool:
    """
    SQLite 连接池管理器

    注意：aiosqlite 不支持真正的连接池，但我们可以使用单例模式管理
    并通过 WAL 模式提升读写并发性能
    """

    _instance: Optional['DatabasePool'] = None
    _lock = asyncio.Lock()
    _connection: Optional[aiosqlite.Connection] = None
    _initialized: bool = False

    def __init__(self):
        raise RuntimeError("Use get_pool() instead")

    @classmethod
    async def get_pool(cls) -> 'DatabasePool':
        """获取连接池实例（单例模式）"""
        if cls._instance is None:
            async with cls._lock:
                if cls._instance is None:
                    cls._instance = cls.__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    async def initialize(self):
        """初始化数据库连接并配置性能优化选项"""
        if self._initialized:
            return

        settings = get_settings()
        db_url = settings.database_url
        db_path = db_url.replace("sqlite:///", "").replace("sqlite://", "")

        # 确保数据库目录存在
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)

        # 创建连接
        self._connection = await aiosqlite.connect(db_path)

        # 性能优化配置
        # WAL 模式允许读操作与写操作并发执行
        await self._connection.execute("PRAGMA journal_mode=WAL")
        # NORMAL 模式在安全性和性能之间平衡
        await self._connection.execute("PRAGMA synchronous=NORMAL")
        # 64MB 缓存
        await self._connection.execute("PRAGMA cache_size=-64000")
        # 临时表存储在内存中
        await self._connection.execute("PRAGMA temp_store=MEMORY")
        # 禁用等待（WAL 模式下不需要）
        await self._connection.execute("PRAGMA busy_timeout=5000")

        await self._connection.commit()
        self._initialized = True

    @asynccontextmanager
    async def acquire(self) -> AsyncIterator[aiosqlite.Connection]:
        """
        获取数据库连接的上下文管理器

        用法:
            async with pool.acquire() as db:
                await db.execute(...)
        """
        if not self._initialized:
            await self.initialize()

        # 设置 row_factory 以便按列名访问
        self._connection.row_factory = aiosqlite.Row

        try:
            yield self._connection
        except Exception:
            # 发生错误时回滚
            await self._connection.rollback()
            raise

    async def close(self):
        """关闭数据库连接"""
        if self._connection:
            await self._connection.close()
            self._connection = None
            self._initialized = False

    async def execute(self, sql: str, parameters=()):
        """
        便捷的执行方法

        Args:
            sql: SQL 语句
            parameters: 参数

        Returns:
            游标对象
        """
        async with self.acquire() as db:
            return await db.execute(sql, parameters)

    async def executemany(self, sql: str, parameters_list):
        """
        便捷的批量执行方法

        Args:
            sql: SQL 语句
            parameters_list: 参数列表

        Returns:
            游标对象
        """
        async with self.acquire() as db:
            return await db.executemany(sql, parameters_list)

    async def commits(self):
        """便捷的提交方法"""
        async with self.acquire() as db:
            await db.commit()


# 全局连接池实例
_pool: Optional[DatabasePool] = None


async def get_db_pool() -> DatabasePool:
    """
    获取全局数据库连接池

    Returns:
        DatabasePool 实例
    """
    global _pool
    if _pool is None:
        _pool = await DatabasePool.get_pool()
        await _pool.initialize()
    return _pool


@asynccontextmanager
async def get_db() -> AsyncIterator[aiosqlite.Connection]:
    """
    获取数据库连接的便捷函数

    用法:
        async with get_db() as db:
            result = await db.execute(...)

    Returns:
        aiosqlite.Connection
    """
    pool = await get_db_pool()
    async with pool.acquire() as db:
        yield db


async def close_db():
    """关闭数据库连接（应用关闭时调用）"""
    global _pool
    if _pool:
        await _pool.close()
        _pool = None
