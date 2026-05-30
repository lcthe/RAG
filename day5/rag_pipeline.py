"""
rag_pipeline.py - RAG Pipeline Day5
"""
from __future__ import annotations
import os, sys, time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

@dataclass
class LLMResponse:
    content: str
    model: str
    tokens_used: int = 0
    latency_ms: float = 0.0

class BaseLLM(ABC):
    @property
    @abstractmethod
    def model_name(self) -> str: pass
    @abstractmethod
    def chat(self, messages, temperature=0.7) -> LLMResponse: pass

class MockLLM(BaseLLM):
    @property
    def model_name(self): return "mock-llm"
    def chat(self, messages, temperature=0.7):
        start = time.time()
        question = context = ""
        for m in messages:
            if m["role"] == "user": question = m["content"]
            if m["role"] == "system": context = m["content"]
        answer = self._gen(question, context)
        return LLMResponse(content=answer, model=self.model_name,
                           tokens_used=len(answer), latency_ms=(time.time()-start)*1000)
    def _gen(self, q, ctx):
        if not ctx or "[未检索到相关内容]" in ctx:
            return "根据已知信息，暂无法回答该问题。"
        lines = [l.strip() for l in ctx.split("\n") if l.strip() and not l.startswith("[来源")]
        if not lines: return "根据检索结果，暂时无法生成有效回答。"
        ans = "根据知识库中的信息\n\n"
        for i, l in enumerate(lines[:5]): ans += f"{i+1}. {l}\n"
        return ans + "\n以上信息来自知识库检索结果。"

class DeepSeekLLM(BaseLLM):
    def __init__(self, model="deepseek-chat", base_url=None, api_key=None):
        self._model = model
        self._base_url = base_url or "https://api.deepseek.com"
        self._api_key = api_key or os.environ.get("DEEPSEEK_API_KEY", "")
        self._client = None
    @property
    def model_name(self): return self._model
    def _get_client(self):
        if self._client: return self._client
        from openai import OpenAI
        self._client = OpenAI(base_url=self._base_url, api_key=self._api_key)
        return self._client
    def chat(self, messages, temperature=0.7):
        import time
        start = time.time()
        client = self._get_client()
        r = client.chat.completions.create(model=self._model, messages=messages, temperature=temperature)
        return LLMResponse(content=r.choices[0].message.content or "", model=self._model,
                           tokens_used=r.usage.total_tokens if r.usage else 0,
                           latency_ms=(time.time()-start)*1000)

def get_llm(provider="auto", **kw):
    if provider == "auto":
        if os.environ.get("DEEPSEEK_API_KEY") or kw.get("api_key"): return DeepSeekLLM(**kw)
        print("[INFO] 未检测到 DEEPSEEK_API_KEY，使用 MockLLM")
        return MockLLM()
    elif provider == "deepseek": return DeepSeekLLM(**kw)
    elif provider == "mock": return MockLLM()
    raise ValueError(f"不支持的 provider: {provider}")

DEFAULT_SYS = """你是一个智能助手，基于知识库回答问题。规则：只根据上下文回答，没有信息就坦诚告知。"""
DEFAULT_TPL = """{system_prompt}
---检索结果---
{context}
---
{chat_history}用户问题：{question}
请基于以上知识库内容回答："""

class PromptTemplate:
    def __init__(self, template=None, system_prompt=None):
        self.template = template or DEFAULT_TPL
        self.system_prompt = system_prompt or DEFAULT_SYS
    def render_context(self, results):
        if not results: return "[未检索到相关内容]"
        parts = []
        for i, r in enumerate(results, 1):
            src = Path(r.metadata.get("source","未知")).name
            parts.append(f"[来源{i}] ({src}, score={r.score:.3f})\n{r.text[:200]}")
        return "\n\n".join(parts)
    def render_history(self, history):
        if not history: return ""
        lines = ["[对话历史]"]
        for m in history[-6:]:
            role = "用户" if m["role"]=="user" else "助手"
            lines.append(f"{role}: {m['content'][:100]}")
        return "\n".join(lines) + "\n\n"
    def render(self, question, context="", chat_history=None):
        ht = self.render_history(chat_history or [])
        up = self.template.format(system_prompt="", context=context, chat_history=ht, question=question)
        return [{"role":"system","content":self.system_prompt},{"role":"user","content":up}]

@dataclass
class ChatMessage:
    role: str; content: str; timestamp: float = 0.0; sources: list = field(default_factory=list)
    def to_dict(self): return {"role":self.role,"content":self.content}

class ConversationHistory:
    def __init__(self, max_turns=10):
        self.max_turns = max_turns; self.messages = []
    def add_user_message(self, content):
        self.messages.append(ChatMessage(role="user", content=content, timestamp=time.time()))
    def add_assistant_message(self, content, sources=None):
        self.messages.append(ChatMessage(role="assistant", content=content, timestamp=time.time(), sources=sources or []))
    def get_history(self):
        mx = self.max_turns * 2
        recent = self.messages[-mx:] if len(self.messages) > mx else self.messages
        return [m.to_dict() for m in recent]
    def clear(self): self.messages.clear()
    def __len__(self): return len(self.messages)
    def __repr__(self): return f"History(turns={len(self.messages)//2})"

@dataclass
class RAGResponse:
    answer: str; sources: list; question: str; llm_model: str
    retrieval_count: int; latency_ms: float = 0.0

class RAGPipeline:
    def __init__(self, embedding_provider=None, llm=None, chunk_size=300, chunk_overlap=50, top_k=3, system_prompt=None):
        base = os.path.join(os.path.dirname(__file__), "..")
        for d in ["day1","day2","day3","day4"]:
            sys.path.insert(0, os.path.join(base, d))
        from document_loader import DocumentLoader
        from text_splitter import get_splitter
        from embeddings import get_embedding_provider
        from retriever import RetrieverPipeline
        self.loader = DocumentLoader()
        self.splitter = get_splitter("recursive", chunk_size=chunk_size, chunk_overlap=chunk_overlap)
        self.embedding = embedding_provider or get_embedding_provider("local_bge")
        dim = getattr(self.embedding, "dimension", 512)
        self.retriever = RetrieverPipeline(self.embedding, dimension=dim)
        self.llm = llm or get_llm("auto")
        self.prompt = PromptTemplate(system_prompt=system_prompt)
        self.history = ConversationHistory()
        self.top_k = top_k; self._docs = 0; self._chunks = 0

    def ingest(self, path, recursive=True):
        p = Path(path)
        docs = [self.loader.load(p)] if p.is_file() else self.loader.load_directory(p, recursive=recursive)
        print(f"[INGEST] {len(docs)} docs")
        chunks = self.splitter.split_documents(docs)
        print(f"[INGEST] {len(chunks)} chunks")
        self.retriever.add_documents(chunks)
        self._docs += len(docs); self._chunks += len(chunks)

    def query(self, question, top_k=None, use_hybrid=True, use_rerank=True, save_history=True):
        start = time.time(); k = top_k or self.top_k
        results = self.retriever.search(question, top_k=k, rerank=use_rerank, use_hybrid=use_hybrid)
        ctx = self.prompt.render_context(results)
        msgs = self.prompt.render(question=question, context=ctx, chat_history=self.history.get_history())
        resp = self.llm.chat(msgs)
        if save_history:
            self.history.add_user_message(question)
            self.history.add_assistant_message(resp.content, sources=results)
        return RAGResponse(answer=resp.content, sources=results, question=question,
                           llm_model=resp.model, retrieval_count=len(results),
                           latency_ms=(time.time()-start)*1000)

    def clear_history(self): self.history.clear()
    def info(self):
        return {"docs":self._docs,"chunks":self._chunks,"emb":getattr(self.embedding,"model_name","?"),
                "llm":self.llm.model_name,"retriever":self.retriever.info(),"history":len(self.history)//2}

def demo():
    print("="*70); print("  Day 5 - RAG Pipeline Demo"); print("="*70)
    p = RAGPipeline(chunk_size=300, chunk_overlap=50)
    print(f"  LLM: {p.llm.model_name}, Embedding: {p.embedding.model_name}")
    data_dir = os.path.join(os.path.dirname(__file__), "..", "data")
    p.ingest(data_dir)
    print(f"\n{'='*70}\n  单轮问答\n{'='*70}")
    for q in ["音箱的价格是多少？","ZY-SP100 有哪些功能？","保修期多久？"]:
        r = p.query(q, top_k=2)
        print(f"\n  Q: {q}\n  A: {r.answer}\n  [refs={len(r.sources)}, {r.latency_ms:.0f}ms]")
    print(f"\n{'='*70}\n  多轮对话\n{'='*70}")
    p.clear_history()
    for q in ["ZY-SP100是什么？","它有什么特点？","价格呢？"]:
        r = p.query(q, top_k=2)
        print(f"\n  Q: {q}\n  A: {r.answer}\n  [turn {len(p.history)//2}]")
    print(f"\nPipeline: {p.info()}")

if __name__ == "__main__":
    demo()