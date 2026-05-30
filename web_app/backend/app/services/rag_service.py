"""Main RAG service with ChromaDB + Redis."""
import os, sys, time, json
from pathlib import Path
from datetime import datetime

_RAG_ROOT = Path(__file__).resolve().parent.parent.parent.parent.parent  # RAG/
for d in ["day1", "day2", "day3", "day4", "day5", "day6"]:
    sys.path.insert(0, str(_RAG_ROOT / d))

from web_app.backend.app.config import (
    DATA_DIR, DEFAULT_CHUNK_SIZE, DEFAULT_CHUNK_OVERLAP,
    DEFAULT_TOP_K, EMBEDDING_PROVIDER,
)
from web_app.backend.app.services.vector_store import VectorStore
from web_app.backend.app.services.llm_service import get_llm
from web_app.backend.app.services import cache_service
from web_app.backend.app.models import QueryLog
from web_app.backend.app.database import engine, Base


class RAGService:
    def __init__(self):
        self._store = VectorStore()
        self._llm = get_llm()
        self._initialized = False
        self._emb_provider = None

    @property
    def embedding(self):
        if self._emb_provider is None:
            from embeddings import get_embedding_provider
            self._emb_provider = get_embedding_provider(EMBEDDING_PROVIDER)
        return self._emb_provider

    async def initialize(self):
        if self._initialized:
            return
        # Init query log table
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        # Ingest if empty
        count = await self._store.count()
        if count == 0:
            print("[INGEST] Loading documents into ChromaDB...")
            await self._ingest_data()
        print(f"[READY] ChromaDB: {await self._store.count()} chunks, LLM: {self._llm.model_name}")
        self._initialized = True

    async def _ingest_data(self):
        from document_loader import DocumentLoader
        from text_splitter import get_splitter

        loader = DocumentLoader()
        splitter = get_splitter("recursive", chunk_size=DEFAULT_CHUNK_SIZE, chunk_overlap=DEFAULT_CHUNK_OVERLAP)

        files = [f for f in DATA_DIR.rglob("*") if f.is_file() and f.suffix.lower() in (".txt", ".md", ".pdf", ".csv")]
        for fp in files:
            try:
                doc = loader.load(str(fp))
                chunks = splitter.split_documents([doc])
                texts = [c.content for c in chunks]
                if not texts:
                    continue
                embeddings = self.embedding.encode(texts)
                if isinstance(embeddings, list) and embeddings and isinstance(embeddings[0], float):
                    embeddings = [embeddings]
                await self._store.add_chunks(texts, embeddings)
                print(f"  [OK] {fp.name} -> {len(chunks)} chunks")
            except Exception as e:
                print(f"  [WARN] {fp.name}: {e}")

    async def query(self, question: str, top_k: int | None = None) -> dict:
        k = top_k or DEFAULT_TOP_K

        cached = await cache_service.get_cached(question, k)
        if cached:
            return cached

        qv = self.embedding.encode(question)
        if isinstance(qv, list) and qv and isinstance(qv[0], list):
            qv = qv[0]

        results = await self._store.search(qv, top_k=k)
        # Detect greetings / small talk
        greetings = ["你好", "hello", "hi", "嗨", "早上好", "下午好", "晚上好", "在吗", "在不在", "你是谁", "你叫什么"]
        is_greeting = any(g in question.lower() for g in greetings)

        if is_greeting:
            result = {
                "answer": "你好！我是基于知识库的智能问答助手，有什么可以帮助你的吗？😊",
                "sources": [],
                "latency_ms": 0,
                "model": self._llm.model_name,
                "retrieval_count": 0,
            }
            return result

        context_parts = [f"[Source score={r['score']:.3f}]\n{r['text'][:500]}" for r in results]

        if not context_parts:
            messages = [
                {"role": "system", "content": "你是一个智能问答助手。用户的问题在知识库中没有找到相关内容，请友善地告知用户暂时无法回答，并引导用户提供更多信息或换个问题。"},
                {"role": "user", "content": question},
            ]
            start = time.time()
            resp = await self._llm.chat(messages)
            latency = (time.time() - start) * 1000
            result = {
                "answer": resp.content,
                "sources": [],
                "latency_ms": round(latency, 1),
                "model": resp.model,
                "retrieval_count": 0,
            }
            await cache_service.set_cached(question, k, result)
            return result

        context = "\n\n".join(context_parts)

        messages = [
            {"role": "system", "content": "你是一个智能助手，基于知识库回答问题。只根据上下文回答，没有信息就坦诚告知。回答简洁准确。"},
            {"role": "user", "content": f"---知识库内容---\n{context}\n---\n问题：{question}\n请基于以上知识库内容回答："},
        ]

        start = time.time()
        resp = await self._llm.chat(messages)
        latency = (time.time() - start) * 1000

        result = {
            "answer": resp.content,
            "sources": [{"text": r["text"][:200], "score": round(r["score"], 4)} for r in results],
            "latency_ms": round(latency, 1),
            "model": resp.model,
            "retrieval_count": len(results),
        }

        await cache_service.set_cached(question, k, result)

        # Log query
        try:
            from sqlalchemy import insert
            async with engine.begin() as conn:
                await conn.execute(
                    insert(QueryLog).values(
                        question=question,
                        answer_preview=result["answer"][:200],
                        latency_ms=result["latency_ms"],
                        retrieval_count=result["retrieval_count"],
                        model_used=result["model"],
                    )
                )
        except Exception:
            pass

        return result

    async def get_info(self) -> dict:
        return {
            "chunks": await self._store.count(),
            "llm": self._llm.model_name,
            "emb": getattr(self.embedding, "model_name", "?"),
            "vector_store": "chroma",
            "cache": "redis" if await cache_service.ping() else "none",
        }

    async def ingest_file(self, filepath: str) -> int:
        """Ingest a single file into ChromaDB."""
        from document_loader import DocumentLoader
        from text_splitter import get_splitter

        loader = DocumentLoader()
        splitter = get_splitter("recursive", chunk_size=DEFAULT_CHUNK_SIZE, chunk_overlap=DEFAULT_CHUNK_OVERLAP)

        doc = loader.load(filepath)
        chunks = splitter.split_documents([doc])
        texts = [c.content for c in chunks]
        if not texts:
            return 0
        embeddings = self.embedding.encode(texts)
        if isinstance(embeddings, list) and embeddings and isinstance(embeddings[0], float):
            embeddings = [embeddings]
        await self._store.add_chunks(texts, embeddings)
        print(f"  [INGEST] {Path(filepath).name} -> {len(chunks)} chunks")
        return len(chunks)

    async def clear_data(self):
        await self._store.clear()
        await cache_service.invalidate_cache()
        self._initialized = False

    async def reload(self):
        await self.clear_data()
        await self.initialize()


rag_service = RAGService()
