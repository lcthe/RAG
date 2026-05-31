# RAG Web App 学习笔记

> 技术栈：Django 5.2 + DRF（后端）+ Vue 3 + Vite（前端）+ pgvector（向量数据库）+ Redis（缓存）
> LLM：DeepSeek API（兼容 OpenAI 协议）
> 嵌入模型：BAAI/bge-small-zh-v1.5（本地离线）

---

## 一、项目架构

```
用户浏览器 (Vue 3 + Vite :19123)
        │
        ├── /api/* ──→ Django REST API (:18762)
        │                    ├── /api/chat/         对话问答
        │                    ├── /api/chat/info/    系统信息
        │                    ├── /api/chat/conversations/  对话历史
        │                    ├── /api/admin/documents/    文档管理
        │                    └── /api/health/       健康检查
        │
        ├── /admin ──→ Vue Admin 管理页面
        │
        └── Django Admin (:18762/admin/) 数据库管理
```

## 二、技术栈

| 分类 | 技术 | 说明 |
|------|------|------|
| **后端** | Django 5.2 + Django REST Framework | RESTful API |
| **前端** | Vue 3 + Vite + Vue Router | SPA 单页应用 |
| **向量数据库** | pgvector (PostgreSQL 17) | 远程服务器 192.168.31.124:15432 |
| **缓存** | Redis 7 (Docker) | localhost:6379 |
| **LLM** | DeepSeek API (requests 库) | 绕过 httpx SSL 问题 |
| **嵌入模型** | BAAI/bge-small-zh-v1.5 | HuggingFace 本地离线 |

## 三、项目结构

```
web_app/
├── backend/                    # Django 项目
│   ├── config/                 # 项目配置
│   │   ├── settings.py         # 数据库、RAG、LLM 配置
│   │   ├── urls.py             # 根路由
│   │   ├── asgi.py / wsgi.py   # 部署入口
│   ├── apps/                   # Django App
│   │   ├── chat/               # 对话模块
│   │   │   ├── models.py       # Conversation, Message, QueryLog
│   │   │   ├── views.py        # 对话 API
│   │   │   ├── serializers.py  # 序列化
│   │   │   └── urls.py         # 路由
│   │   └── knowledge/          # 知识库模块
│   │       ├── models.py       # Document
│   │       ├── views.py        # 文档管理 API
│   │       └── urls.py
│   ├── services/               # 核心服务
│   │   ├── rag_service.py      # RAG 主逻辑（pgvector）
│   │   ├── llm_service.py      # LLM 抽象层（requests 版）
│   │   └── cache_service.py    # Redis 缓存
│   ├── data/                   # 运行时数据
│   └── manage.py
├── frontend_vue/               # Vue 3 前端
│   ├── src/
│   │   ├── api/index.ts        # API 客户端
│   │   ├── views/
│   │   │   ├── Chat.vue        # 问答页面（MaxKB 风格）
│   │   │   └── Admin.vue       # 后台管理页
│   │   ├── router/index.ts     # 路由
│   │   └── App.vue             # 根组件
│   └── vite.config.ts          # Vite 配置（代理 :18762）
├── scripts/
│   └── start.ps1
├── docker-compose.yml          # Redis + pgvector
└── README.md
```

## 四、启动方式

### 前置条件

```powershell
# 1. 启动 Redis（Docker）
docker start redis

# 2. 确认 pgvector 可用
conda run -n rag python -c "import psycopg2; conn=psycopg2.connect(host='192.168.31.124',port=15432,user='postgres',password='...',dbname='rag'); print('pgvector OK'); conn.close()"
```

### 启动后端

```powershell
cd D:\code\RAG\web_app\backend
$env:DEEPSEEK_API_KEY="sk-5f2d1af8c0f94a15be4ff72a53b49fd3"
$env:DEEPSEEK_MODEL="deepseek-v4-flash"
conda activate rag
python manage.py runserver 127.0.0.1:18762
```

### 启动前端

```powershell
cd D:\code\RAG\web_app\frontend_vue
npm run dev
```

### 访问

| 页面 | 地址 |
|------|------|
| 💬 问答页 | http://localhost:19123/ |
| ⚙️ 管理后台 | http://localhost:19123/admin |
| 🔌 Django Admin | http://localhost:18762/admin/ (admin / admin123) |

## 五、API 接口

| 端点 | 方法 | 说明 |
|------|------|------|
| `/api/chat/` | POST | 发送问题 { question, top_k? } |
| `/api/chat/info/` | GET | 系统运行信息 |
| `/api/chat/conversations/` | GET | 对话历史列表 |
| `/api/chat/conversations/:id/` | GET | 对话详情 |
| `/api/chat/save_conversation/` | POST | 保存对话 |
| `/api/chat/delete_conversation/:id/` | DELETE | 删除对话 |
| `/api/admin/documents/` | GET | 文档列表 |
| `/api/admin/documents/upload/` | POST | 上传文档 |
| `/api/admin/documents/reload/` | POST | 重新加载向量库 |
| `/api/health/` | GET | 健康检查 |

## 六、RAG 核心流程

```
POST /api/chat/ { question, top_k }
    │
    ├─ 1. 嵌入模型编码问题
    ├─ 2. pgvector 向量检索（top_k 条）
    ├─ 3. Redis 缓存检查（命中直接返回）
    ├─ 4. 组装 Context → 调用 LLM
    ├─ 5. Redis 缓存结果
    └─ 6. 返回 { answer, sources, latency_ms, model }
```

## 七、数据库

- **PostgreSQL 17**（远程）：Django 主数据库 + pgvector 向量存储
- **Redis 7**（Docker）：查询结果缓存
- **SQLite**：已废弃，全部迁移到 PostgreSQL
