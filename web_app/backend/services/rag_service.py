"""RAG service with direct pgvector search."""
import os, sys, time, json, traceback
os.environ.setdefault("HF_HUB_OFFLINE", "1")
os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")
from pathlib import Path
from django.conf import settings

from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_core.documents import Document
from .llm_service import llm_client

_emb_model = None
def get_embeddings():
    global _emb_model
    if _emb_model is None:
        model_name = getattr(settings, "EMBEDDING_MODEL", "BAAI/bge-small-zh-v1.5")
        print(f"[INFO] Loading embedding model: {model_name} ...")
        _emb_model = HuggingFaceEmbeddings(
            model_name=model_name,
            model_kwargs={"device": "cpu"},
            encode_kwargs={"normalize_embeddings": True},
        )
        print("[INFO] Embedding model loaded")
    return _emb_model

def _get_pg_conn():
    import psycopg2
    return psycopg2.connect(
        host=settings.PGVECTOR_HOST, port=settings.PGVECTOR_PORT,
        user=settings.PGVECTOR_USER, password=settings.PGVECTOR_PASSWORD,
        dbname=settings.PGVECTOR_DATABASE, connect_timeout=10,
    )

def ensure_tables():
    conn = _get_pg_conn()
    try:
        cur = conn.cursor()
        cur.execute("CREATE EXTENSION IF NOT EXISTS vector")
        cur.execute("""
            CREATE TABLE IF NOT EXISTS embeddings (
                id SERIAL PRIMARY KEY,
                content TEXT NOT NULL,
                metadata JSONB DEFAULT '{}'::jsonb,
                embedding vector(512)
            )
        """)
        conn.commit()
        cur.close()
    finally:
        conn.close()

def count_chunks() -> int:
    try:
        conn = _get_pg_conn()
        cur = conn.cursor()
        cur.execute("SELECT count(*) FROM embeddings")
        count = cur.fetchone()[0]
        cur.close()
        conn.close()
        return count
    except Exception as e:
        print(f"[WARN] count_chunks: {e}")
        return 0

def add_texts(texts: list[str]):
    emb = get_embeddings()
    vectors = emb.embed_documents(texts)
    conn = _get_pg_conn()
    try:
        cur = conn.cursor()
        for i, text in enumerate(texts):
            vec_str = "[" + ",".join(str(v) for v in vectors[i]) + "]"
            cur.execute("INSERT INTO embeddings (content, embedding) VALUES (%s, %s::vector)", (text, vec_str))
        conn.commit()
        cur.close()
    finally:
        conn.close()

def search_similar(query_text: str, top_k: int = 5) -> list[Document]:
    t = time.time()
    emb = get_embeddings()
    print(f"[DEBUG] embed_query start... ({round(time.time()-t,1)}s)")
    vector = emb.embed_query(query_text)
    print(f"[DEBUG] embed_query done ({round(time.time()-t,1)}s)")
    vector_str = "[" + ",".join(f"{v:.15f}" for v in vector) + "]"

    conn = _get_pg_conn()
    try:
        cur = conn.cursor()
        cur.execute(
            "SELECT content, metadata, 1 - (embedding <=> %s::vector) AS score "
            "FROM embeddings WHERE embedding IS NOT NULL "
            "ORDER BY score DESC LIMIT %s",
            (vector_str, top_k)
        )
        print(f"[DEBUG] pgvector query done ({round(time.time()-t,1)}s)")
        docs = []
        for row in cur.fetchall():
            doc = Document(page_content=row[0], metadata={**(row[1] or {}), "score": row[2] or 0})
            
            docs.append(doc)
        print(f"[DEBUG] found {len(docs)} docs ({round(time.time()-t,1)}s)")
        return docs
    finally:
        cur.close()
        conn.close()

_llm_client = None
def get_llm():
    global _llm_client
    if _llm_client is None:
        _llm_client = llm_client
    return _llm_client

def format_docs(docs):
    return "\n\n".join(d.page_content[:500] for d in docs)

class RAGService:
    def __init__(self):
        self._initialized = False

    def initialize(self):
        if self._initialized:
            return
        print("[INFO] RAG Service initializing...")
        ensure_tables()
        count = count_chunks()
        if count == 0:
            print("[INGEST] No data found, loading documents...")
            data_dir = Path(getattr(settings, "DATA_DIR", str(Path(__file__).resolve().parent.parent.parent.parent / "data")))
            if data_dir.exists():
                root = Path(__file__).resolve().parent.parent.parent.parent
                for d in ["day1", "day2", "day3", "day4", "day5", "day6"]:
                    sys.path.insert(0, str(root / d))
                from document_loader import DocumentLoader
                from text_splitter import get_splitter
                loader = DocumentLoader()
                splitter = get_splitter("recursive", chunk_size=300, chunk_overlap=50)
                for fp in sorted(data_dir.rglob("*")):
                    if fp.is_file() and fp.suffix.lower() in (".txt", ".md", ".pdf"):
                        try:
                            doc = loader.load(str(fp))
                            chunks = splitter.split_documents([doc])
                            texts = [c.content for c in chunks]
                            if texts:
                                add_texts(texts)
                                print(f"  [OK] {fp.name} -> {len(chunks)} chunks")
                        except Exception as e:
                            print(f"  [WARN] {fp.name}: {e}")
                count = count_chunks()
        print(f"[READY] pgvector: {count} chunks, LLM: {get_llm().model_name}")
        self._initialized = True

    def query(self, question: str, top_k: int | None = None) -> dict:
        t = time.time()
        if not self._initialized:
            self.initialize()
        k = top_k or 5
        llm = get_llm()
        from . import cache_service
        cached = cache_service.get_cached(question, k)
        if cached:
            return cached

        print(f"[QUERY] question={question[:50]}")
        try:
            print(f"[DEBUG] searching similar... ({round(time.time()-t,1)}s)")
            docs = search_similar(question, k)
            context = format_docs(docs)
            print(f"[DEBUG] calling LLM... ({round(time.time()-t,1)}s)")
            messages = [
                {"role": "system", "content": f"你是一个智能助手...\n\n上下文：\n{context}"},
                {"role": "user", "content": question},
            ]
            answer = llm.chat(messages)
            latency = (time.time() - t) * 1000
            print(f"[DEBUG] LLM done ({round(time.time()-t,1)}s)")
        except Exception as e:
            print(f"[ERROR] query: {e}")
            traceback.print_exc()
            latency = (time.time() - t) * 1000
            answer = "抱歉，处理您的请求时出现错误。请稍后再试。"
            docs = []

        sources = [{"text": d.page_content[:200], "score": d.metadata.get("score", 0) or 0} for d in docs[:k]]
        response = {"answer": answer, "sources": sources, "latency_ms": round(latency, 1), "model": llm.model_name, "retrieval_count": len(sources)}
        cache_service.set_cached(question, k, response)
        return response

    def get_info(self) -> dict:
        count = count_chunks()
        from . import cache_service
        return {"chunks": count, "llm": get_llm().model_name, "emb": "BAAI/bge-small-zh-v1.5", "vector_store": "pgvector", "cache": "redis" if cache_service.ping() else "none"}

    def ingest_file(self, filepath: str) -> int:
        root = Path(__file__).resolve().parent.parent.parent.parent
        for d in ["day1", "day2", "day3", "day4", "day5", "day6"]:
            sys.path.insert(0, str(root / d))
        from document_loader import DocumentLoader
        from text_splitter import get_splitter
        doc = DocumentLoader().load(filepath)
        chunks = get_splitter("recursive", chunk_size=300, chunk_overlap=50).split_documents([doc])
        texts = [c.content for c in chunks]
        if texts:
            add_texts(texts)
        return len(chunks)

    def clear_data(self):
        try:
            conn = _get_pg_conn()
            cur = conn.cursor()
            cur.execute("DELETE FROM embeddings")
            conn.commit()
            cur.close()
            conn.close()
        except Exception:
            pass
        from . import cache_service
        cache_service.invalidate_cache()
        self._initialized = False

    def reload(self):
        self.clear_data()
        self.initialize()

rag_service = RAGService()
