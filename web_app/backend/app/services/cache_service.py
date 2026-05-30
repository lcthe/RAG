"""Redis cache service for query caching."""
import json
import hashlib
from redis.asyncio import Redis
from web_app.backend.app.config import REDIS_URL, CACHE_TTL

redis_client: Redis | None = None


async def get_redis() -> Redis:
    global redis_client
    if redis_client is None:
        redis_client = Redis.from_url(REDIS_URL, decode_responses=True)
    return redis_client


async def close_redis():
    global redis_client
    if redis_client:
        await redis_client.close()
        redis_client = None


def _make_key(question: str, top_k: int) -> str:
    h = hashlib.md5(question.encode()).hexdigest()
    return f"rag:q:{h}:k{top_k}"


async def get_cached(question: str, top_k: int) -> dict | None:
    r = await get_redis()
    key = _make_key(question, top_k)
    data = await r.get(key)
    return json.loads(data) if data else None


async def set_cached(question: str, top_k: int, result: dict):
    r = await get_redis()
    key = _make_key(question, top_k)
    await r.setex(key, CACHE_TTL, json.dumps(result, ensure_ascii=False))


async def invalidate_cache():
    r = await get_redis()
    keys = await r.keys("rag:q:*")
    if keys:
        await r.delete(*keys)


async def ping() -> bool:
    try:
        r = await get_redis()
        return await r.ping()
    except Exception:
        return False
