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


# === Chat History in Redis ===

async def save_conversation(conv_id: str, messages: list, title: str = ""):
    """Save full conversation to Redis."""
    r = await get_redis()
    key = f"rag:conv:{conv_id}"
    data = {"id": conv_id, "title": title, "messages": messages}
    await r.setex(key, 86400 * 7, json.dumps(data, ensure_ascii=False))  # 7 days TTL

async def get_conversation(conv_id: str) -> dict | None:
    """Load conversation from Redis."""
    r = await get_redis()
    data = await r.get(f"rag:conv:{conv_id}")
    return json.loads(data) if data else None

async def list_conversations() -> list[dict]:
    """List all conversation summaries (id + title)."""
    r = await get_redis()
    keys = await r.keys("rag:conv:*")
    result = []
    for k in keys:
        data = await r.get(k)
        if data:
            c = json.loads(data)
            result.append({"id": c["id"], "title": c["title"]})
    result.sort(key=lambda x: x["id"], reverse=True)
    return result

async def delete_conversation(conv_id: str):
    """Delete a conversation."""
    r = await get_redis()
    await r.delete(f"rag:conv:{conv_id}")
