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

---

## 八、Web App vs Day1-7 核心改进对比

| 维度 | Day1-7（原型） | Web App（生产级） | 改进说明 |
|------|---------------|-------------------|---------|
| **架构** | 独立 Python 脚本 | Django Web 服务 + REST API | 从脚本到可部署服务 |
| **向量库** | ChromaDB（本地文件） | pgvector（PostgreSQL） | 支持并发读写、事务、备份 |
| **数据库** | 无 | PostgreSQL + Django ORM | 对话历史、文档、日志持久化 |
| **LLM 调用** | 直接调用 DeepSeek SDK | requests 统一封装层 | 多供应商切换、错误重试 |
| **API 设计** | 无 | RESTful JSON API（10+ 端点） | 前后端分离 |
| **前端** | 无 | Vue 3 + Vite（MaxKB 主题） | 用户问答 + 后台管理 |
| **缓存** | 无 | Redis 7 | 相同问题秒级响应 |
| **对话管理** | 无 | 对话历史（保存/加载/删除） | 可追溯历史问答 |
| **文档管理** | 手动 ingest | 拖拽上传 + API 上传 | 在线管理知识库 |
| **系统监控** | print 日志 | 健康检查 + 系统信息 API | 可观测性 |
| **部署** | 手动运行脚本 | Docker Compose + 启动脚本 | 一键启动 |
| **错误处理** | try-except 简单处理 | HTTP 状态码 + 统一错误响应 | 更健壮 |

### 8.1 向量存储升级：ChromaDB → pgvector

| 特性 | ChromaDB | pgvector |
|------|----------|----------|
| **存储方式** | 本地 SQLite 文件 | PostgreSQL 数据库 |
| **并发支持** | 单进程 | 多进程/多线程 |
| **查询能力** | 仅向量检索 | 向量 + SQL 混合查询 |
| **备份恢复** | 文件拷贝 | pg_dump/pg_restore |
| **生态集成** | LangChain 原生 | LangChain + SQLAlchemy + Django |
| **部署运维** | 无 | 主从复制、连接池、监控 |

### 8.2 LLM 抽象层改进

Day1-7 直接调用 SDK，Web App 做了统一抽象：

```
Day1-7:  DeepSeekSDK.chat(prompt)
           │
           └── 切换模型要改代码

Web App:  llm_client.chat(messages)
            ├── 有 DEEPSEEK_API_KEY → DeepSeek
            ├── 有 OPENAI_API_KEY → OpenAI
            └── 都没有 → MockLLM（返回固定内容）
```

### 8.3 前端从无到有

Day1-7 只有命令行输出，Web App 提供了：

- **用户端**：MaxKB 风格对话界面，左侧历史列表，右侧聊天区
- **管理端**：三栏布局，概览/知识库/模型/系统管理
- **RAG 特有**：来源引用标注、检索状态可视化、Markdown 渲染

### 8.4 工程化改进

- **配置管理**：环境变量 + Django settings，不用改代码
- **依赖管理**：requirements.txt + package.json
- **版本控制**：Git 提交规范、CI 就绪
- **文档**：中英文双语 README + 学习笔记
- **日志**：Django 日志系统，不是 print
