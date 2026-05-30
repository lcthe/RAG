"""Admin routes."""
import os
from fastapi import APIRouter, UploadFile, File, HTTPException
from sqlalchemy import text
from pathlib import Path
from web_app.backend.app.database import async_session
from web_app.backend.app.services import cache_service
from web_app.backend.app.services.rag_service import rag_service
from web_app.backend.app.config import DATA_DIR

router = APIRouter(prefix="/api/admin", tags=["Admin"])


@router.get("/stats")
async def dashboard_stats():
    async with async_session() as session:
        log_count = (await session.execute(text("SELECT COUNT(*) FROM query_logs"))).scalar() or 0
        row = (await session.execute(text("SELECT created_at FROM query_logs ORDER BY created_at DESC LIMIT 1"))).scalar()
        last_query = str(row) if row else None

    info = await rag_service.get_info()
    files = list(DATA_DIR.rglob("*")) if DATA_DIR.exists() else []
    docs = [f for f in files if f.is_file() and f.suffix.lower() in (".txt", ".md", ".pdf", ".csv")]
    return {
        "documents": len(docs),
        "chunks": info.get("chunks", 0),
        "queries": log_count,
        "last_query": last_query,
        "cache_available": await cache_service.ping(),
    }


@router.get("/documents")
async def list_documents():
    if not DATA_DIR.exists():
        return []
    files = []
    for f in DATA_DIR.rglob("*"):
        if f.is_file() and f.suffix.lower() in (".txt", ".md", ".pdf", ".csv"):
            files.append({
                "name": f.name,
                "path": str(f.relative_to(DATA_DIR.parent)),
                "size": f.stat().st_size,
                "format": f.suffix[1:] if f.suffix else "unknown",
            })
    return files


@router.post("/documents/upload")
async def upload_document(file: UploadFile = File(...)):
    if not file.filename:
        raise HTTPException(400, "No file provided")
    suffix = Path(file.filename).suffix.lower()
    if suffix not in (".txt", ".md", ".pdf", ".csv"):
        raise HTTPException(400, f"Unsupported file format: {suffix}")
    
    os.makedirs(str(DATA_DIR), exist_ok=True)
    save_path = DATA_DIR / file.filename
    content = await file.read()
    with open(str(save_path), "wb") as f:
        f.write(content)
    
    # Ingest into ChromaDB
    info = await rag_service.ingest_file(str(save_path))
    return {"status": "ok", "filename": file.filename, "chunks": info}


@router.post("/documents/reload")
async def reload_documents():
    await rag_service.reload()
    return {"status": "ok", "chunks": await rag_service._store.count()}


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