"""Redis cache service."""
import os, json, hashlib
from django.conf import settings
try:
    import redis as redis_lib
    _redis = redis_lib.from_url(settings.REDIS_URL)
    _redis.ping()
    _available = True
except Exception:
    _redis = None
    _available = False

CACHE_TTL = int(os.getenv("CACHE_TTL", "3600"))

def _key(question: str, top_k: int = 5) -> str:
    raw = f"rag:q:{hashlib.md5(question.encode()).hexdigest()}:k={top_k}"
    return raw

def get_cached(question: str, top_k: int = 5):
    if not _available:
        return None
    try:
        data = _redis.get(_key(question, top_k))
        if data:
            return json.loads(data)
    except Exception:
        pass
    return None

def set_cached(question: str, top_k: int, result: dict):
    if not _available:
        return
    try:
        _redis.setex(_key(question, top_k), CACHE_TTL, json.dumps(result, ensure_ascii=False))
    except Exception:
        pass

def invalidate_cache():
    if not _available:
        return
    try:
        for k in _redis.scan_iter("rag:q:*"):
            _redis.delete(k)
    except Exception:
        pass

def ping():
    if not _available:
        return False
    try:
        return _redis.ping()
    except Exception:
        return False

