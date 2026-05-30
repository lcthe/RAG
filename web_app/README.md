# RAG Web Console / RAG Web 控制台

> 企业级 RAG 问答系统 | Enterprise RAG Q&A System  
> 技术栈：Next.js + FastAPI + ChromaDB + Redis  
> 主题风格：MaxKB · 紫白 · 极简专业

---

## 🚀 快速启动 / Quick Start

### 1. 启动基础设施（Redis）

```bash
cd D:\code\RAG\web_app
docker-compose up -d
```

（现有 Redis 容器可直接用，无需额外启动）

### 2. 安装依赖

```bash
conda activate rag
pip install -r web_app/backend/requirements.txt
cd web_app/frontend && npm install
```

### 3. 启动后端

```bash
cd D:\code\RAG
# 设置 LLM API Key（可选，不设置则使用 MockLLM）
set DEEPSEEK_API_KEY=sk-xxx
# 离线模式加载嵌入模型
set TRANSFORMERS_OFFLINE=1
set HF_HUB_OFFLINE=1
python -m uvicorn web_app.backend.app.main:app --host 127.0.0.1 --port 18762
```

### 4. 启动前端（新终端）

```bash
cd D:\code\RAG\web_app\frontend
npm run dev
```

### 5. 打开浏览器

| 页面 | 地址 |
|------|------|
| 💬 **问答页** | http://localhost:19123 |
| ⚙️ **管理后台** | http://localhost:19123/admin |
| 🔌 **API 文档** | http://localhost:18762/docs |

---

## 🔌 端口说明 / Ports

| 服务 | 端口 | 说明 |
|------|------|------|
| Frontend | **19123** | Next.js 前端（问答 + 管理后台） |
| Backend | **18762** | FastAPI 后端 API |
| Redis | **6379** | 查询结果缓存 |

---

## ⚙️ 环境变量 / Environment Variables

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `DEEPSEEK_API_KEY` | - | DeepSeek API 密钥 |
| `OPENAI_API_KEY` | - | OpenAI API 密钥 |
| `LLM_PROVIDER` | `auto` | LLM 供应商：auto / openai / deepseek / ollama / mock |
| `PORT` | `18762` | 后端端口 |
| `REDIS_URL` | `redis://localhost:6379/0` | Redis 连接 |
| `CHUNK_SIZE` | `300` | 文本分块大小 |
| `CHUNK_OVERLAP` | `50` | 分块重叠长度 |
| `TOP_K` | `5` | 每次检索返回的块数 |
| `TRANSFORMERS_OFFLINE` | `1` | 离线模式（避免联网检查模型） |
| `HF_HUB_OFFLINE` | `1` | HuggingFace 离线模式 |

> 未设置 API Key 时自动使用 MockLLM（模拟回答），可正常验证全部界面功能。

---

## 🎨 主题设计 / Theme (MaxKB Style)

- **主色**：`#6366F1`（紫蓝）
- **背景**：`#FFFFFF` 纯白 + `#F5F5F7` 页面底色
- **文本**：`#1F2937` 主文本 / `#6B7280` 次要文本
- **字体**：Inter + PingFang SC（中文）
- **圆角**：按钮 6px，卡片 8px
- **布局**：扁平化、卡片化、轻投影、留白充足
- **RAG 专属**：引用溯源清晰、来源分段可预览、回答与引文分离展示

---

## 📁 项目结构 / Project Structure

```
web_app/
├── docker-compose.yml          # Redis
├── scripts/
│   └── start.ps1               # 一键启动脚本
├── backend/                    # FastAPI 后端
│   ├── requirements.txt
│   └── app/
│       ├── main.py             # 入口 + CORS
│       ├── config.py           # 环境变量配置
│       ├── database.py         # SQLite（查询日志）
│       ├── models/             # QueryLog 模型
│       ├── routes/
│       │   ├── chat.py         # POST /api/chat
│       │   └── admin.py        # 后台管理 API
│       └── services/
│           ├── rag_service.py       # RAG 主逻辑
│           ├── vector_store.py      # ChromaDB 向量检索
│           ├── cache_service.py     # Redis 缓存
│           └── llm_service.py       # 多供应商 LLM 兼容层
├── frontend/                   # Next.js 前端
│   └── src/
│       ├── lib/api.ts          # API 客户端
│       └── app/
│           ├── page.tsx             # 问答页面（MaxKB 风格）
│           ├── globals.css          # 紫白主题样式
│           └── admin/               # 管理后台（三栏布局）
│               ├── page.tsx         # 概览仪表盘
│               ├── documents/       # 知识库管理
│               ├── logs/            # 查询日志
│               └── config/          # 系统设置
└── data/
    └── chroma_db/              # ChromaDB 持久化数据
```

---

## 🌐 API 接口 / API Endpoints

| 端点 | 方法 | 说明 |
|------|------|------|
| `/api/chat` | POST | 发送问题（RAG 检索 + LLM 回答） |
| `/api/chat/info` | GET | 系统运行信息 |
| `/api/admin/stats` | GET | 仪表盘统计 |
| `/api/admin/logs` | GET | 查询日志 |
| `/api/admin/cache/clear` | POST | 清除 Redis 缓存 |
| `/api/health` | GET | 健康检查 |

---

## 🏗️ 技术栈 / Tech Stack

| 分类 | 技术 |
|------|------|
| **向量数据库** | ChromaDB（纯 Python，无需 Docker） |
| **缓存** | Redis 7 |
| **后端** | FastAPI + SQLAlchemy + aiosqlite |
| **LLM** | OpenAI / DeepSeek / Ollama / Mock 统一 API 层 |
| **前端** | Next.js 16 + TypeScript + Tailwind CSS 4 |
| **嵌入模型** | BAAI/bge-small-zh-v1.5（本地离线） |
| **文档解析** | pypdf, markdown, jieba（中文分词） |

---

## 📄 License / 许可

MIT
