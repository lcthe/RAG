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
| - | **Web Console / Web 控制台** | `web_app/` (Django + Vue 3 + pgvector) | ✅ |

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
│   ├── docker-compose.yml    # Redis + pgvector
│   ├── backend/              # Django 5.2 + DRF（REST API）
│   │   ├── config/           # 项目配置
│   │   ├── apps/             # chat（对话）, knowledge（知识库）
│   │   └── services/         # RAG, LLM, Cache 服务
│   └── frontend_vue/         # Vue 3 + Vite（MaxKB 紫白主题）
│       └── src/views/        # Chat.vue（问答）, Admin.vue（管理后台）
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

#### 1. 启动基础设施

```powershell
# Redis（Docker）
docker start redis

# pgvector（确保 PostgreSQL 17 可连接）
```

#### 2. 启动后端（Django）

```powershell
cd D:\code\RAG\web_app\backend
$env:DEEPSEEK_API_KEY="sk-your-key-here"
$env:DEEPSEEK_MODEL="deepseek-v4-flash"
conda run -n rag python manage.py runserver 127.0.0.1:18762
```

#### 3. 启动前端（Vue 3，新终端）

```powershell
cd D:\code\RAG\web_app\frontend_vue
npm run dev
```

#### 4. 访问

| 页面 | 地址 |
|------|------|
| 💬 问答页 | http://localhost:19123 |
| ⚙️ 管理后台 | http://localhost:19123/admin |
| 🔌 Django Admin | http://localhost:18762/admin/ (admin / admin123) |

---

## 🏗️ Tech Stack / 技术栈

| Category / 分类 | Technology / 技术 |
|----------------|-------------------|
| **Core RAG** | Python 3.11, LangChain, sentence-transformers |
| **LLM** | DeepSeek API, OpenAI API, MockLLM |
| **Vector DB** | pgvector (PostgreSQL 17) |
| **Backend** | Django 5.2 + Django REST Framework |
| **Frontend** | Vue 3 + Vite + TypeScript |
| **Cache** | Redis 7 |
| **Theme** | MaxKB Style: 紫白 #6366F1, 纯白背景, 极简专业 |
| **Documents** | pypdf, markdown, fpdf2, jieba |

---

## 🎯 Key Features / 核心功能

- **Multi-format document parsing**: TXT, Markdown, PDF, CSV / 多格式文档解析
- **Flexible chunking**: Recursive, fixed-size / 灵活分块策略
- **Hybrid retrieval**: Vector search + BM25 + Reranker / 混合检索
- **Multi-provider LLM**: DeepSeek, OpenAI, Ollama, Mock / 多 LLM 供应商
- **pgvector**: PostgreSQL vector extension / 生产级向量数据库
- **Redis caching**: Accelerate repeated queries / 缓存加速
- **MaxKB theme**: Enterprise-grade UI with Chinese localization / 企业级中文界面
- **Admin panel**: Dashboard, knowledge base, model config / 三栏管理后台
- **RAG citations**: Source tracing with score display / 引用溯源
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
