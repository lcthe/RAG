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
