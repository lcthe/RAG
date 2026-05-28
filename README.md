# RAG 全流程学习计划

7 天从零搭建 RAG 系统，每天一个核心模块。

## 项目结构

`
RAG/
├── data/                 # 示例数据（智云科技产品线）
│   ├── csv/              # 产品目录、订单、用户反馈
│   ├── md/               # API 文档、快速上手、更新日志
│   ├── pdf/              # 产品报告、用户调研
│   └── txt/              # 产品介绍、手册、服务协议
├── day1/                 # Day 1 — 文档加载与解析
│   ├── document_loader.py
│   ├── day1_notes.md
│   └── generate_pdfs.py
├── day2/                 # Day 2 — 文本分段
│   ├── text_splitter.py
│   └── day2_notes.md
├── reference/            # 开源项目参考源码
│   ├── dify/
│   ├── langchain/
│   └── llamaindex_schema.py
└── requirements.txt
`

## 学习进度

| Day | 主题 | 产出 | 状态 |
|-----|------|------|------|
| 1 | 文档加载与解析 | document_loader.py | ✅ 完成 |
| 2 | 文本分段（Chunking）| 	ext_splitter.py | ✅ 完成 |
| 3 | Embedding 与向量化 | — | ⏳ 进行中 |
| 4 | 向量存储与检索 | — | ⏳ 待开始 |
| 5 | RAG Pipeline 串联 | — | ⏳ 待开始 |
| 6 | Agent + RAG 集成 | — | ⏳ 待开始 |
| 7 | 评估与优化 | — | ⏳ 待开始 |

## 快速开始

`ash
# 创建虚拟环境
conda create -n rag python=3.11 -y
conda activate rag

# 安装依赖
pip install -r requirements.txt

# 运行 Day 1 — 文档加载测试
PYTHONIOENCODING=utf-8 python day1/document_loader.py

# 运行 Day 2 — 分段器对比测试
PYTHONIOENCODING=utf-8 python day2/text_splitter.py
`

## 参考项目

- [LangChain](https://github.com/langchain-ai/langchain) — Document 定义、TextSplitter
- [LlamaIndex](https://github.com/run-llama/llama_index) — Document、TextNode
- [Dify](https://github.com/langgenius/dify) — 完整 RAG 平台架构
- [Unstructured](https://github.com/Unstructured-IO/unstructured) — 26 种 Element 类型

## 技术栈

- Python 3.11 + conda 虚拟环境
- pypdf（PDF 解析）
- markdown（Markdown 解析）
- fpdf2（PDF 生成）
