# RAG Full-Stack Learning Project / RAG 全栈学习项目

> 7-day hands-on RAG system from scratch + Web Console (MaxKB Theme)  
> 7 天从零搭建 RAG 系统 + Web 控制台（MaxKB 主题风格）

---

## 📋 Learning Progress / 学习进度

| Day | Topic / 主题 | Output / 产出 | Status / 状态 |
|-----|-------------|---------------|--------------|
| 1 | Document Loading / 文档加载 | `document_loader.py` | ✅ |
| 2 | Text Chunking / 文本分块 | `text_splitter.py` | ✅ |
| 3 | Embedding & Vectorization / 向量化 | `embeddings.py` | ✅ |
| 4 | Vector Storage & Retrieval / 向量存储与检索 | `retriever.py` | ✅ |
| 5 | RAG Pipeline / 串联检索生成 | `rag_pipeline.py` | ✅ |
| 6 | Agent + RAG Integration / 智能代理集成 | `agent.py` | ✅ |
| 7 | Evaluation & Optimization / 评估与优化 | `evaluate.py`, `optimize.py` | ✅ |
| - | **Web Console / Web 控制台** | `web_app/` (ChromaDB + Redis + Next.js) | ✅ |

---

## 📁 Project Structure / 项目结构

```text
RAG/
├── data/                     # Example data / 示例数据（智云科技产品线）
│   ├── csv/                  # Product catalog, orders, feedback
│   ├── md/                   # API docs, quick start, changelog
│   ├── pdf/                  # Reports, user research
│   └── txt/                  # Product manuals, terms of service
├── day1/                     # Document Loading / 文档加载与解析
├── day2/                     # Text Chunking / 文本分块
├── day3/                     # Embedding / 向量化
├── day4/                     # Vector Store & Retrieval / 向量存储与检索
├── day5/                     # RAG Pipeline / 串联检索生成
├── day6/                     # Agent + RAG / 智能代理
├── day7/                     # Evaluation / 评估与优化
├── reference/                # Open-source references / 开源项目参考
├── web_app/                  # Web Console / Web 控制台 ⭐
│   ├── docker-compose.yml    # Redis
│   ├── backend/              # FastAPI + ChromaDB
│   └── frontend/             # Next.js + TS (MaxKB 紫白主题)
├── requirements.txt
└── README.md
```

---

## 🚀 How to Run / 运行方式

### Core Modules / Day 1-7（核心模块学习）

```bash
conda create -n rag python=3.11 -y
conda activate rag
pip install -r requirements.txt

set PYTHONIOENCODING=utf-8
python day1/document_loader.py
python day2/text_splitter.py
python day3/embeddings.py
python day4/retriever.py
set DEEPSEEK_API_KEY=your_key
python day5/rag_pipeline.py
python day6/agent.py
python day7/evaluate.py
```

### Web Console / Web 控制台

```bash
# 1. Start Redis（可选，已有容器可跳过）
cd web_app && docker-compose up -d

# 2. Install dependencies
cd ..
pip install -r web_app/backend/requirements.txt
cd web_app/frontend && npm install

# 3. Configure LLM API key（choose one, required for real answers）
set DEEPSEEK_API_KEY=sk-your-key-here
set DEEPSEEK_MODEL=deepseek-v4-flash
rem set OPENAI_API_KEY=sk-your-key-here

# 4. Start backend（use conda env）
cd D:\code\RAG
conda activate rag
set TRANSFORMERS_OFFLINE=1
set HF_HUB_OFFLINE=1
python -u -m uvicorn web_app.backend.app.main:app --host 127.0.0.1 --port 18762 --log-level info

# 5. Start frontend（new terminal）
cd D:\code\RAG\web_app\frontend && npm run dev

# 6. Open
#   Chat / 问答:  http://localhost:19123
#   Admin / 后台: http://localhost:19123/admin
```

---

## 🏗️ Tech Stack / 技术栈

| Category / 分类 | Technology / 技术 |
|----------------|-------------------|
| **Core RAG** | Python 3.11, sentence-transformers, ChromaDB |
| **LLM** | DeepSeek API, OpenAI API, Ollama, MockLLM |
| **Vector DB** | ChromaDB（纯 Python，无需 Docker） |
| **Backend** | FastAPI, SQLAlchemy, aiosqlite |
| **Frontend** | Next.js 16, TypeScript, Tailwind CSS 4 |
| **Cache** | Redis 7 |
| **Theme** | MaxKB Style: 紫白 #6366F1, 纯白背景, 极简专业 |
| **Documents** | pypdf, markdown, fpdf2, jieba |

---

## 🎯 Key Features / 核心功能

- **Multi-format document parsing**: TXT, Markdown, PDF, CSV / 多格式文档解析
- **Flexible chunking**: Recursive, fixed-size / 灵活分块策略
- **Hybrid retrieval**: Vector search + BM25 + Reranker / 混合检索
- **Multi-provider LLM**: DeepSeek, OpenAI, Ollama, Mock / 多 LLM 供应商
- **ChromaDB**: Pure Python vector DB, no Docker required / 纯 Python 向量库
- **Redis caching**: Accelerate repeated queries / 缓存加速
- **MaxKB theme**: Enterprise-grade UI with Chinese localization / 企业级中文界面
- **Admin panel**: Dashboard, knowledge base, logs, config / 三栏管理后台
- **RAG citations**: Source tracing with expandable preview / 引用溯源
- **Evaluation framework**: Precision, Recall, keyword match / 评估框架

---

## 🔗 Reference Projects / 参考项目

| Project / 项目 | Link / 链接 | Reference / 参考内容 |
|---------------|------------|---------------------|
| LangChain | [GitHub](https://github.com/langchain-ai/langchain) | Document, TextSplitter |
| LlamaIndex | [GitHub](https://github.com/run-llama/llama_index) | Document, TextNode |
| Dify | [GitHub](https://github.com/langgenius/dify) | Full RAG platform |
| Unstructured | [GitHub](https://github.com/Unstructured-IO/unstructured) | 26 Element types |
| MaxKB | [GitHub](https://github.com/1Panel-dev/MaxKB) | UI theme reference |
