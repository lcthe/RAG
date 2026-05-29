import re, sys, os, faiss, pickle, json, time, numpy as np
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional
from rank_bm25 import BM25Okapi

@dataclass
class SearchResult:
    text: str
    score: float
    metadata: dict = field(default_factory=dict)
    rank: int = 0
    retrieval_type: str = "vector"
    def __repr__(self) -> str:
        preview = self.text[:40].replace(chr(10), " ")
        return f"SearchResult(#%d, score=%.4f, type=%s, text='%s...')" % (self.rank, self.score, self.retrieval_type, preview)

# ===========================================
# FAISS VectorStore
# ===========================================
class VectorStore:
    def __init__(self, dimension: int = 512, index_type: str = "flat"):
        self.dimension = dimension
        self.index_type = index_type
        self._index = self._build(dimension, index_type)
        self._texts = []
        self._metadatas = []
        self._trained = (index_type == "flat")

    def _build(self, d, t):
        if t == "flat":
            return faiss.IndexFlatIP(d)
        elif t == "ivf":
            q = faiss.IndexFlatIP(d)
            idx = faiss.IndexIVFFlat(q, d, 100, faiss.METRIC_INNER_PRODUCT)
            idx.nprobe = 10
            return idx
        elif t == "hnsw":
            idx = faiss.IndexHNSWFlat(d, 32)
            idx.hnsw.efConstruction = 200
            idx.hnsw.efSearch = 64
            return idx
        else:
            raise ValueError(f"Unknown index: {t}")

    def add(self, vectors, texts, metadatas=None):
        if len(vectors) != len(texts):
            raise ValueError(f"vectors (%d) != texts (%d)" % (len(vectors), len(texts)))
        vec_np = np.array(vectors).astype(np.float32)
        faiss.normalize_L2(vec_np)
        if not self._trained and self.index_type != "flat":
            self._index.train(vec_np)
            self._trained = True
        self._index.add(vec_np)
        self._texts.extend(texts)
        if metadatas:
            self._metadatas.extend(metadatas)
        else:
            self._metadatas.extend([{}] * len(texts))

    def search(self, query_vector, top_k=5):
        if not self._texts:
            return []
        q = np.array([query_vector]).astype(np.float32)
        faiss.normalize_L2(q)
        k = min(top_k, len(self._texts))
        scores, indices = self._index.search(q, k)
        results = []
        for i, idx in enumerate(indices[0]):
            if idx == -1: continue
            results.append(SearchResult(
                text=self._texts[idx], score=float(scores[0][i]),
                metadata=self._metadatas[idx], rank=i+1, retrieval_type="vector"))
        return results

    def save(self, path):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        faiss.write_index(self._index, f"{path}.index")
        with open(f"{path}.data.pkl", "wb") as f:
            pickle.dump({"texts": self._texts, "metadatas": self._metadatas}, f)

    def load(self, path):
        self._index = faiss.read_index(f"{path}.index")
        self.dimension = self._index.d
        with open(f"{path}.data.pkl", "rb") as f:
            d = pickle.load(f)
            self._texts = d["texts"]
            self._metadatas = d["metadatas"]

    @property
    def count(self): return len(self._texts)

    def info(self):
        return {"count": self.count, "dimension": self.dimension, "index_type": self.index_type}

# ===========================================
# BM25 Retriever
# ===========================================
class BM25Retriever:
    def __init__(self):
        self._corpus = []
        self._metadatas = []
        self._bmodel = None

    def _tokenize(self, text):
        try:
            import jieba
            return jieba.lcut(text)
        except ImportError:
            return re.findall(r'[\\w]+', text)

    def add_texts(self, texts, metadatas=None):
        self._corpus.extend(texts)
        if metadatas: self._metadatas.extend(metadatas)
        else: self._metadatas.extend([{}] * len(texts))
        all_tok = [self._tokenize(t) for t in self._corpus]
        self._bmodel = BM25Okapi(all_tok)

    def search(self, query, top_k=5):
        if self._bmodel is None or not self._corpus:
            return []
        tok = self._tokenize(query)
        scores = self._bmodel.get_scores(tok)
        idxs = np.argsort(scores)[::-1][:top_k]
        results = []
        for r, idx in enumerate(idxs):
            if scores[idx] <= 0: continue
            results.append(SearchResult(
                text=self._corpus[idx], score=float(scores[idx]),
                metadata=self._metadatas[idx], rank=r+1, retrieval_type="bm25"))
        return results

    @property
    def count(self): return len(self._corpus)

# ===========================================
# Hybrid Retriever
# ===========================================
class HybridRetriever:
    def __init__(self, vector_store, bm25_retriever, vec_weight=0.7, bm25_weight=0.3):
        self.vector_store = vector_store
        self.bm25_retriever = bm25_retriever
        self.vec_w = vec_weight
        self.bm25_w = bm25_weight

    def search(self, query_vector, query_text, top_k=5):
        vec_r = self.vector_store.search(query_vector, top_k=top_k*2)
        bm25_r = self.bm25_retriever.search(query_text, top_k=top_k*2)
        vec_r = self._norm(vec_r)
        bm25_r = self._norm(bm25_r)
        merged = {}
        for r in vec_r:
            merged[r.text] = {"score": r.score * self.vec_w, "meta": r.metadata, "types": ["vector"]}
        for r in bm25_r:
            if r.text in merged:
                merged[r.text]["score"] += r.score * self.bm25_w
                merged[r.text]["types"].append("bm25")
            else:
                merged[r.text] = {"score": r.score * self.bm25_w, "meta": r.metadata, "types": ["bm25"]}
        sorted_items = sorted(merged.items(), key=lambda x: x[1]["score"], reverse=True)[:top_k]
        return [SearchResult(text=t, score=d["score"], metadata=d["meta"], rank=i+1, retrieval_type="+".join(d["types"]))
                for i, (t, d) in enumerate(sorted_items)]

    @staticmethod
    def _norm(results):
        if not results: return results
        scores = [r.score for r in results]
        mn, mx = min(scores), max(scores)
        if mx != mn:
            for r in results: r.score = (r.score - mn) / (mx - mn)
        return results

# ===========================================
# Simple Reranker (keyword-based, no model download)
# ===========================================
class Reranker:
    def __init__(self, use_model=False, model_name="BAAI/bge-reranker-v2-m3"):
        self.use_model = use_model
        self.model_name = model_name
        self._model = None

    def rerank(self, query, candidates, top_k=5):
        if not candidates:
            return []
        if self.use_model:
            self._load_model()
        query_tokens = set(re.findall(r'[\\w\\u4e00-\\u9fff]+', query))
        for c in candidates:
            doc_tokens = set(re.findall(r'[\\w\\u4e00-\\u9fff]+', c.text))
            overlap = len(query_tokens & doc_tokens)
            final_score = c.score * (0.7 + 0.3 * min(overlap / max(len(query_tokens), 1), 1.0))
            c.score = final_score
        candidates.sort(key=lambda x: x.score, reverse=True)
        for i, c in enumerate(candidates[:top_k]):
            c.rank = i + 1
        return candidates[:top_k]

    def _load_model(self):
        if self._model: return
        from transformers import AutoModelForSequenceClassification, AutoTokenizer
        self._tokenizer = AutoTokenizer.from_pretrained(self.model_name)
        self._model = AutoModelForSequenceClassification.from_pretrained(self.model_name)

# ===========================================
# RetrieverPipeline
# ===========================================
class RetrieverPipeline:
    def __init__(self, embedding_provider, dimension=512, index_type="flat", vec_w=0.7, bm25_w=0.3):
        self.embedding_provider = embedding_provider
        self.vector_store = VectorStore(dimension, index_type)
        self.bm25 = BM25Retriever()
        self.hybrid = HybridRetriever(self.vector_store, self.bm25, vec_w, bm25_w)
        self.reranker = Reranker(use_model=False)

    def add_documents(self, chunks):
        texts = [c.content for c in chunks]
        metas = [{**c.metadata, "chunk_index": c.chunk_index} if hasattr(c, "chunk_index") else c.metadata for c in chunks]
        vectors = self.embedding_provider.encode(texts)
        self.vector_store.add(vectors, texts, metas)
        self.bm25.add_texts(texts, metas)
        return len(texts)

    def search(self, query, top_k=5, rerank=True, use_hybrid=True):
        qv = self.embedding_provider.encode(query)
        if use_hybrid:
            results = self.hybrid.search(qv, query, top_k=top_k*2)
        else:
            results = self.vector_store.search(qv, top_k=top_k*2)
        if rerank:
            results = self.reranker.rerank(query, results, top_k=top_k)
        return results[:top_k]

    def info(self):
        return {"vector_store": self.vector_store.info(), "bm25": self.bm25.count}

# ===========================================
# Demo
# ===========================================
def demo():
    from day1.document_loader import DocumentLoader
    from day2.text_splitter import get_splitter
    from day3.embeddings import get_embedding_provider

    print("="*70)
    print("  Day 4 - Vector Store & Retrieval Demo")
    print("="*70)

    # 1. Load & chunk
    loader = DocumentLoader()
    doc = loader.load('../data/txt/product_zy_sp100.txt')
    splitter = get_splitter("recursive", chunk_size=200, chunk_overlap=50)
    chunks = splitter.split_text(doc.content, {"source": doc.source})
    print(f"\\n1. Loaded: {len(doc.content)} chars -> {len(chunks)} chunks")

    # 2. Build pipeline
    emb = get_embedding_provider("local_bge")
    pipeline = RetrieverPipeline(emb, dimension=512)
    pipeline.add_documents(chunks)
    print(f"2. Pipeline ready: {pipeline.info()}")

    # 3. Search tests
    queries = ["音箱的价格是多少？", "保修期多久", "音频规格和尺寸", "今天天气"]
    print(f"\\n3. Search results:")
    for q in queries:
        results = pipeline.search(q, top_k=2, rerank=True, use_hybrid=True)
        print(f"\\n  Q: {q}")
        for r in results:
            print(f"    #%d score=%.3f [%s]: %s..." % (r.rank, r.score, r.retrieval_type, r.text[:50]))

    # 4. Comparison: vector vs hybrid
    print(f"\\n{'='*70}")
    print("  Vector vs Hybrid Comparison")
    print(f"{'='*70}")
    q = "音箱"
    qv = emb.encode(q)
    print(f"\\n  Q: {q}")
    print(f"\\n  [Vector only]:")
    for r in pipeline.vector_store.search(qv, 3):
        print(f"    #%d score=%.3f: %s..." % (r.rank, r.score, r.text[:50]))
    print(f"\\n  [Hybrid]:")
    for r in pipeline.hybrid.search(qv, q, 3):
        print(f"    #%d score=%.3f [%s]: %s..." % (r.rank, r.score, r.retrieval_type, r.text[:50]))

if __name__ == "__main__":
    demo()
