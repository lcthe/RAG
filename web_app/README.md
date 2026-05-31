# RAG Web Console / RAG Web 控制台

> 企业级 RAG 问答系统 | Enterprise RAG Q&A System  
> 技术栈：Django 5.2 + Vue 3 + pgvector + Redis  
> 主题风格：MaxKB · 紫白 · 极简专业

---

## 🚀 快速启动 / Quick Start

### 1. 启动基础设施

```powershell
# Redis（Docker）
docker start redis

# pgvector（远程 PostgreSQL 17，确保可连接）
```

### 2. 启动后端（Django）

```powershell
cd D:\code\RAG\web_app\backend
$env:DEEPSEEK_API_KEY="sk-5f2d1af8c0f94a15be4ff72a53b49fd3"
$env:DEEPSEEK_MODEL="deepseek-v4-flash"
conda activate rag
python manage.py runserver 127.0.0.1:18762
```

### 3. 启动前端（Vue 3）

```powershell
cd D:\code\RAG\web_app\frontend_vue
npm run dev
```

### 4. 打开浏览器

| 页面 | 地址 |
|------|------|
| 💬 **问答页** | http://localhost:19123 |
| ⚙️ **管理后台** | http://localhost:19123/admin |
| 🔌 **Django Admin** | http://localhost:18762/admin/ |

> 管理员账号：`admin` / `admin123`

---

## 🔌 端口说明 / Ports

| 服务 | 端口 | 说明 |
|------|------|------|
| Frontend (Vite) | **19123** | Vue 3 前端（问答 + 管理后台） |
| Backend (Django) | **18762** | Django REST API |
| Redis | **6379** | 查询结果缓存 |
| PostgreSQL | **15432** | 远程 pgvector（192.168.31.124） |

---

## ⚙️ 环境变量 / Environment Variables

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `DEEPSEEK_API_KEY` | - | DeepSeek API 密钥 |
| `DEEPSEEK_MODEL` | `deepseek-v4-flash` | 模型名称 |
| `LLM_PROVIDER` | `auto` | LLM 供应商：auto / openai / deepseek / mock |
| `REDIS_URL` | `redis://localhost:6379/0` | Redis 连接 |
| `CHUNK_SIZE` | `300` | 文本分块大小 |
| `CHUNK_OVERLAP` | `50` | 分块重叠长度 |
| `TOP_K` | `5` | 每次检索返回的块数 |

---

## 🎨 主题设计 / Theme (MaxKB Style)

- **主色**：`#6366F1`（紫蓝）
- **背景**：`#FFFFFF` 纯白 / `#F9FAFB` 页面底色
- **文本**：`#1F2937` 主文本 / `#6B7280` 次要文本
- **字体**：Inter + PingFang SC + Noto Sans SC
- **圆角**：按钮 6px，卡片 8px
- **布局**：扁平化、卡片化、轻投影、留白充足

---

## 📁 项目结构 / Project Structure

```
web_app/
├── docker-compose.yml          # Redis + pgvector
├── scripts/
│   └── start.ps1               # 启动脚本
├── backend/                    # Django 后端
│   ├── config/                 # 项目配置（settings.py, urls.py）
│   ├── apps/
│   │   ├── chat/               # 对话模块（Conversation, Message, QueryLog）
│   │   └── knowledge/          # 知识库模块（Document）
│   ├── services/
│   │   ├── rag_service.py      # RAG 主逻辑（pgvector）
│   │   ├── llm_service.py      # LLM 抽象层
│   │   └── cache_service.py    # Redis 缓存
│   └── manage.py
├── frontend_vue/               # Vue 3 前端
│   └── src/
│       ├── api/index.ts        # API 客户端
│       ├── views/
│       │   ├── Chat.vue        # 问答页面（MaxKB 风格）
│       │   └── Admin.vue       # 管理后台
│       ├── router/index.ts     # 路由
│       └── App.vue
└── data/
    └── chroma_db/              # 旧 ChromaDB 数据（已废弃）
```

---

## 🌐 API 接口 / API Endpoints

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

---

## 🏗️ 技术栈 / Tech Stack

| 分类 | 技术 |
|------|------|
| **后端** | Django 5.2 + Django REST Framework |
| **前端** | Vue 3 + Vite + TypeScript |
| **向量数据库** | pgvector (PostgreSQL 17) |
| **缓存** | Redis 7 |
| **LLM** | DeepSeek API（兼容 OpenAI 协议） |
| **嵌入模型** | BAAI/bge-small-zh-v1.5（本地离线） |

---

## 📄 License / 许可

MIT
