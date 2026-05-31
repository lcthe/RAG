"""LangChain-powered RAG service with pgvector."""
import os, time, traceback
from pathlib import Path
from urllib.parse import quote
from django.conf import settings

from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_postgres import PGVector
from .llm_service import llm_client

# ---- pgvector connection ----
def _pg_connection_string():
    pw = quote(settings.PGVECTOR_PASSWORD)
    return (
        f"postgresql+psycopg2://{settings.PGVECTOR_USER}:{pw}"
        f"@{settings.PGVECTOR_HOST}:{settings.PGVECTOR_PORT}/{settings.PGVECTOR_DATABASE}"
    )

COLLECTION_NAME = "rag_docs"

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
    return _emb_model

_vec_store = None
def get_vector_store():
    global _vec_store
    if _vec_store is None:
        _vec_store = PGVector(
            collection_name=COLLECTION_NAME,
            connection=_pg_connection_string(),
            embeddings=get_embeddings(),
            use_jsonb=True,
        )
    return _vec_store

_llm_client = None
def get_llm():
    global _llm_client
    if _llm_client is None:
        _llm_client = llm_client
    return _llm_client

def format_docs(docs):
    return "\n\n".join(d.page_content[:500] for d in docs)

def _count_chunks():
    import psycopg2
    conn = psycopg2.connect(
        host=settings.PGVECTOR_HOST, port=settings.PGVECTOR_PORT,
        user=settings.PGVECTOR_USER, password=settings.PGVECTOR_PASSWORD,
        dbname=settings.PGVECTOR_DATABASE, connect_timeout=5
    )
    cur = conn.cursor()
    cur.execute("SELECT count(*) FROM langchain_pg_embedding")
    count = cur.fetchone()[0]
    cur.close()
    conn.close()
    return count

class RAGService:
    def __init__(self):
        self._initialized = False

    def initialize(self):
        if self._initialized:
            return
        vs = get_vector_store()
        try:
            count = _count_chunks()
        except Exception:
            count = 0
        if count == 0:
            print("[INGEST] Loading documents into pgvector...")
            data_dir = Path(getattr(settings, "DATA_DIR", str(Path(__file__).resolve().parent.parent.parent.parent / "data")))
            if data_dir.exists():
                import sys
                root = Path(__file__).resolve().parent.parent.parent.parent
                for d in ["day1", "day2", "day3", "day4", "day5", "day6"]:
                    sys.path.insert(0, str(root / d))
                from document_loader import DocumentLoader
                from text_splitter import get_splitter
                loader = DocumentLoader()
                splitter = get_splitter("recursive", chunk_size=getattr(settings, "CHUNK_SIZE", 300), chunk_overlap=getattr(settings, "CHUNK_OVERLAP", 50))
                for fp in data_dir.rglob("*"):
                    if fp.is_file() and fp.suffix.lower() in (".txt", ".md", ".pdf", ".csv"):
                        try:
                            doc = loader.load(str(fp))
                            chunks = splitter.split_documents([doc])
                            texts = [c.content for c in chunks]
                            if texts:
                                vs.add_texts(texts)
                                print(f"  [OK] {fp.name} -> {len(chunks)} chunks")
                        except Exception as e:
                            print(f"  [WARN] {fp.name}: {e}")
                try:
                    count = _count_chunks()
                except Exception:
                    count = 0
        print(f"[READY] pgvector: {count} chunks, LLM: {get_llm().model_name}")
        self._initialized = True

    def query(self, question: str, top_k: int | None = None) -> dict:
        if not self._initialized:
            self.initialize()
        k = top_k or getattr(settings, "TOP_K", 5)
        vs = get_vector_store()
        llm = get_llm()
        from . import cache_service
        cached = cache_service.get_cached(question, k)
        if cached:
            return cached

        retriever = vs.as_retriever(search_kwargs={"k": k})
        start = time.time()
        try:
            docs = retriever.invoke(question)
            context = format_docs(docs)
            messages = [
                {"role": "system", "content": f"你是一个智能助手，基于知识库内容回答问题。\n只根据提供的上下文回答，没有相关信息就坦诚告知。\n回答简洁准确，使用中文。\n\n上下文内容：\n{context}"},
                {"role": "user", "content": question},
            ]
            answer = llm.chat(messages)
            latency = (time.time() - start) * 1000
        except Exception as e:
            print(f"[ERROR] query failed: {e}")
            traceback.print_exc()
            latency = (time.time() - start) * 1000
            answer = "抱歉，处理您的请求时出现错误。请稍后再试。"
            docs = []

        sources = [{"text": d.page_content[:200], "score": getattr(d, "score", 0) or 0} for d in docs[:k]]
        response = {"answer": answer, "sources": sources, "latency_ms": round(latency, 1), "model": getattr(llm, "model_name", "?"), "retrieval_count": len(sources)}
        cache_service.set_cached(question, k, response)
        return response

    def get_info(self) -> dict:
        count = 0
        try:
            count = _count_chunks()
        except Exception as e:
            print(f"[WARN] get_info count failed: {e}")
        from . import cache_service
        return {"chunks": count, "llm": getattr(get_llm(), "model_name", "?"), "emb": getattr(settings, "EMBEDDING_MODEL", "?"), "vector_store": "pgvector", "cache": "redis" if cache_service.ping() else "none"}

    def ingest_file(self, filepath: str) -> int:
        import sys
        root = Path(__file__).resolve().parent.parent.parent.parent
        for d in ["day1", "day2", "day3", "day4", "day5", "day6"]:
            sys.path.insert(0, str(root / d))
        from document_loader import DocumentLoader
        from text_splitter import get_splitter
        loader = DocumentLoader()
        splitter = get_splitter("recursive", chunk_size=getattr(settings, "CHUNK_SIZE", 300), chunk_overlap=getattr(settings, "CHUNK_OVERLAP", 50))
        doc = loader.load(filepath)
        chunks = splitter.split_documents([doc])
        texts = [c.content for c in chunks]
        if texts:
            get_vector_store().add_texts(texts)
        return len(chunks)

    def clear_data(self):
        try:
            vs = get_vector_store()
            vs.delete_collection()
        except Exception:
            pass
        from . import cache_service
        cache_service.invalidate_cache()
        self._initialized = False

    def reload(self):
        self.clear_data()
        self.initialize()

rag_service = RAGService()
