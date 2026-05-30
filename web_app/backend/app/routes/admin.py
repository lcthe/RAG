"""Admin routes."""
from fastapi import APIRouter
from sqlalchemy import text
from web_app.backend.app.database import async_session
from web_app.backend.app.services import cache_service
from web_app.backend.app.services.rag_service import rag_service

router = APIRouter(prefix="/api/admin", tags=["Admin"])


@router.get("/stats")
async def dashboard_stats():
    async with async_session() as session:
        log_count = (await session.execute(text("SELECT COUNT(*) FROM query_logs"))).scalar() or 0
        row = (await session.execute(text("SELECT created_at FROM query_logs ORDER BY created_at DESC LIMIT 1"))).scalar()
        last_query = str(row) if row else None

    info = await rag_service.get_info()
    return {
        "documents": 0,
        "chunks": info.get("chunks", 0),
        "queries": log_count,
        "last_query": last_query,
        "cache_available": await cache_service.ping(),
    }


@router.get("/logs")
async def query_logs(limit: int = 100):
    async with async_session() as session:
        rows = await session.execute(
            text("SELECT id, question, answer_preview, latency_ms, retrieval_count, model_used, created_at FROM query_logs ORDER BY created_at DESC LIMIT :lim"),
            {"lim": limit},
        )
        return [
            {
                "id": r[0], "question": r[1], "answer_preview": r[2],
                "latency_ms": r[3], "retrieval_count": r[4],
                "model_used": r[5], "created_at": str(r[6]) if r[6] else None,
            }
            for r in rows.fetchall()
        ]


@router.get("/cache/status")
async def cache_status():
    return {"available": await cache_service.ping()}


@router.post("/cache/clear")
async def clear_cache():
    await cache_service.invalidate_cache()
    return {"status": "ok"}
