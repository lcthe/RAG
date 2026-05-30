"""ChromaDB-based vector store."""
import os
import chromadb
from chromadb.config import Settings
from web_app.backend.app.config import CHROMA_PERSIST_DIR

_COLLECTION_NAME = "rag_docs"


def _get_client() -> chromadb.PersistentClient:
    return chromadb.PersistentClient(
        path=CHROMA_PERSIST_DIR,
        settings=Settings(anonymized_telemetry=False),
    )


def _get_collection(client=None):
    if client is None:
        client = _get_client()
    # Use get_or_create to be idempotent
    return client.get_or_create_collection(
        name=_COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},
    )


class VectorStore:
    async def add_chunks(self, texts: list[str], embeddings: list[list[float]], document_id: int = 0, metadata: dict | None = None):
        if not texts:
            return 0
        client = _get_client()
        collection = _get_collection(client)
        ids = [f"chunk_{document_id}_{i}" for i in range(len(texts))]
        metadatas = [{"document_id": document_id, **(metadata or {})} for _ in texts]
        collection.add(
            ids=ids,
            embeddings=embeddings,
            documents=texts,
            metadatas=metadatas,
        )
        return len(texts)

    async def search(self, query_embedding: list[float], top_k: int = 5) -> list[dict]:
        client = _get_client()
        collection = _get_collection(client)
        if collection.count() == 0:
            return []
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=min(top_k, collection.count()),
            include=["documents", "metadatas", "distances"],
        )
        out = []
        if results["ids"] and results["ids"][0]:
            for i, doc_id in enumerate(results["ids"][0]):
                distance = results["distances"][0][i] if results.get("distances") else 1.0
                score = 1.0 - distance  # cosine distance -> similarity
                out.append({
                    "id": doc_id,
                    "text": results["documents"][0][i],
                    "metadata": results["metadatas"][0][i] if results.get("metadatas") else {},
                    "score": max(0.0, score),
                })
        return out

    async def count(self) -> int:
        try:
            collection = _get_collection()
            return collection.count()
        except Exception:
            return 0

    async def clear(self):
        try:
            client = _get_client()
            client.delete_collection(_COLLECTION_NAME)
        except Exception:
            pass
