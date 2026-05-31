# Day 8 — Web App 前后端整合 学习笔记

> 日期：2026-05-31
> 目录：web_app/
> 技术栈：Next.js + TypeScript（前端）+ FastAPI + ChromaDB + Redis（后端）

---

## 一、今天做了什么

把 Day1-Day7 的 RAG 核心模块整合成一个完整的 Web 应用：

- **前端**：Next.js + TypeScript，用户端对话界面 + 后台管理面板
- **后端**：FastAPI + Uvicorn，RESTful API 服务
- **向量存储**：ChromaDB（文件持久化，无需 Docker）
- **缓存**：Redis（Docker 容器部署）
- **LLM**：DeepSeek API 兼容接口（也可切换 OpenAI / Ollama / Mock）

---

## 二、项目结构

```
web_app/
├── backend/                  # Python FastAPI 后端
│   ├── app/
│   │   ├── config.py         # 环境变量配置
│   │   ├── database.py       # 数据库（SQLite + SQLAlchemy）
│   │   ├── main.py           # FastAPI 入口 + 生命周期
│   │   ├── models/           # 数据模型
│   │   ├── routes/           # API 路由
│   │   │   ├── chat.py       # 对话 + 历史记录 API
│   │   │   └── admin.py      # 管理后台 API
│   │   └── services/         # 业务逻辑
│   │       ├── rag_service.py    # 核心 RAG 服务
│   │       ├── llm_service.py    # LLM 抽象层
│   │       ├── vector_store.py   # ChromaDB 封装
│   │       └── cache_service.py  # Redis 缓存
│   └── data/                 # 运行时数据（logs, chroma_db）
├── frontend/                 # Next.js 前端
│   ├── src/
│   │   ├── app/
│   │   │   ├── page.tsx          # 用户端对话页
│   │   │   ├── layout.tsx        # 全局布局
│   │   │   └── admin/            # 管理后台
│   │   │       ├── page.tsx      # 概览页
│   │   │       └── documents/
│   │   │           └── page.tsx  # 文档管理页
│   │   └── lib/
│   │       └── api.ts       # API 调用封装
│   ├── next.config.ts       # Next.js 配置（代理重写）
│   └── package.json
├── scripts/                 # 部署运维脚本
├── docker-compose.yml       # Docker 编排（Redis）
└── README.md
```

## 五、后端核心流程

### 5.1 启动生命周期（main.py）

```
1. 初始化 RAGService
2. 初始化 ChromaDB
3. 调用 RAGService.initialize()
   ├── 建 SQLite 表（查询日志）
   ├── 检查 ChromaDB 是否为空
   └── 若为空 → 自动从 data/ 目录 ingest 文档
4. 打印就绪信息：[READY] ChromaDB: N chunks, LLM: xxx
5. 开始接收请求
```

### 5.2 对话流程（rag_service.py）

```
POST /api/chat { question, top_k }
    │
    ├─ 1. Embedding 编码问题
    ├─ 2. ChromaDB 向量检索（top_k 条）
    ├─ 3. 问候语检测（直接返回，不调 LLM）
    ├─ 4. Redis 缓存检查（命中直接返回）
    ├─ 5. 组装 Context → Prompt
    ├─ 6. LLM 生成回答
    ├─ 7. Redis 缓存结果
    └─ 8. 返回 { answer, sources, latency_ms, model }
```

### 5.3 LLM 自动选择（llm_service.py）

```
get_llm("auto"):
  1. 有 OPENAI_API_KEY → 用 OpenAI
  2. 有 DEEPSEEK_API_KEY → 用 DeepSeek（兼容 OpenAI 协议）
  3. 有 OLLAMA_BASE_URL → 用 Ollama
  4. 都没有 → 用 MockLLM（返回 context 片段）
```

---

## 七、启动方式

### 完整启动（前后端 + Redis）

```powershell
# 1. 启动 Redis（Docker）
docker start redis

# 2. 启动后端
conda activate rag
$env:DEEPSEEK_API_KEY="sk-xxx"
$env:DEEPSEEK_MODEL="deepseek-v4-flash"
uvicorn web_app.backend.app.main:app --host 127.0.0.1 --port 18762 --log-level info

# 3. 启动前端（新终端）
cd web_app\frontend
npx next dev --port 19123

# 4. 浏览器访问
#    用户端：http://localhost:19123/
#    管理端：http://localhost:19123/admin
```
