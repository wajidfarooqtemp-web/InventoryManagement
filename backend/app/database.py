"""
One shared database connection POOL for the whole app, instead of opening a
new connection per request. FastAPI opens it once when the server starts
and closes it once when the server stops (wired up in main.py).
"""
import asyncpg
from app.config import settings

_pool: asyncpg.Pool | None = None


async def connect_db():
    global _pool
    _pool = await asyncpg.create_pool(dsn=settings.database_url, min_size=1, max_size=10)


async def disconnect_db():
    if _pool:
        await _pool.close()


def get_pool() -> asyncpg.Pool:
    if _pool is None:
        raise RuntimeError("Database pool not initialized - did startup run?")
    return _pool