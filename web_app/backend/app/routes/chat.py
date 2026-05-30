"""Chat and RAG query routes."""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from web_app.backend.app.services.rag_service import rag_service

router = APIRouter(prefix="/api/chat", tags=["Chat"])


class QueryRequest(BaseModel):
    question: str
    top_k: int | None = None


@router.post("")
async def chat(req: QueryRequest):
    if not req.question.strip():
        raise HTTPException(400, "Question cannot be empty")
    return await rag_service.query(req.question, top_k=req.top_k)


@router.get("/info")
async def info():
    return await rag_service.get_info()


@router.get("/history")
async def list_history():
    """Get all conversation summaries."""
    from web_app.backend.app.services.cache_service import list_conversations
    return await list_conversations()

@router.get("/history/{conv_id}")
async def get_history(conv_id: str):
    """Get a specific conversation."""
    from web_app.backend.app.services.cache_service import get_conversation
    return await get_conversation(conv_id) or {}

@router.post("/history/save")
async def save_history(data: dict):
    """Save a conversation."""
    from web_app.backend.app.services.cache_service import save_conversation
    await save_conversation(data["id"], data["messages"], data.get("title", ""))
    return {"status": "ok"}

@router.delete("/history/{conv_id}")
async def delete_history(conv_id: str):
    """Delete a conversation."""
    from web_app.backend.app.services.cache_service import delete_conversation
    await delete_conversation(conv_id)
    return {"status": "ok"}
