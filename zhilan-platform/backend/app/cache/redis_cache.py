"""Redis 缓存层 — 缓存热数据、页面结果、API返回值"""

import json
import asyncio
from typing import Any, Callable, Optional
from app.config import settings

_redis_client: Optional[Any] = None
_memory_cache: dict[str, tuple[Any, float]] = {}
_lock = asyncio.Lock()


async def init_cache():
    global _redis_client
    try:
        import redis.asyncio as aioredis
        _redis_client = aioredis.Redis(
            host=settings.REDIS_HOST, port=settings.REDIS_PORT,
            db=0, password=settings.REDIS_PASSWORD,
            decode_responses=True,
        )
        await _redis_client.ping()
    except Exception:
        _redis_client = None


async def close_cache():
    if _redis_client:
        await _redis_client.close()


async def _get_redis(key: str) -> Optional[Any]:
    if _redis_client:
        try:
            val = await _redis_client.get(key)
            return json.loads(val) if val else None
        except Exception:
            return None
    return None


async def _set_redis(key: str, value: Any, ttl: int = 300):
    if _redis_client:
        try:
            await _redis_client.setex(key, ttl, json.dumps(value, ensure_ascii=False))
        except Exception:
            pass


def _get_memory(key: str) -> Optional[Any]:
    import time
    if key in _memory_cache:
        val, exp = _memory_cache[key]
        if time.time() < exp:
            return val
        del _memory_cache[key]
    return None


def _set_memory(key: str, value: Any, ttl: int = 300):
    import time
    _memory_cache[key] = (value, time.time() + ttl)


async def cache_get(key: str) -> Optional[Any]:
    val = await _get_redis(key)
    if val is not None:
        return val
    return _get_memory(key)


async def cache_set(key: str, value: Any, ttl: int = 300):
    await _set_redis(key, value, ttl)
    _set_memory(key, value, ttl)


async def cache_get_or_set(key: str, factory: Callable, ttl: int = 300) -> Any:
    val = await cache_get(key)
    if val is not None:
        return val
    if asyncio.iscoroutinefunction(factory):
        val = await factory()
    else:
        val = factory()
    await cache_set(key, val, ttl)
    return val


async def cache_delete(key: str):
    if _redis_client:
        try:
            await _redis_client.delete(key)
        except Exception:
            pass
    _memory_cache.pop(key, None)


async def cache_flush():
    global _memory_cache
    if _redis_client:
        try:
            await _redis_client.flushdb()
        except Exception:
            pass
    _memory_cache = {}


# ===== 接口级缓存 =====
async def cache_dashboard_stats() -> Optional[Any]:
    return await cache_get("dashboard:stats")


async def cache_dashboard_stats_set(value: Any, ttl: int = 1800):
    await cache_set("dashboard:stats", value, ttl)


async def cache_brief(date: str) -> Optional[Any]:
    return await cache_get(f"brief:{date}")


async def cache_brief_set(date: str, value: Any, ttl: int = 1800):
    await cache_set(f"brief:{date}", value, ttl)
