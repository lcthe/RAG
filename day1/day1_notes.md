# Day 1 — 文档加载与解析 学习笔记

> 日期：2025-05-28
> 产出：document_loader.py
> 参考项目：LangChain、LlamaIndex、Dify、Unstructured

---

## 一、今天做了什么

完成了 RAG 流水线的第一步：**Document Loading**（文档加载）。

- 实现了 DocumentLoader 类，支持 PDF / TXT / Markdown 三种格式
- 了解了主流开源项目的 Document 设计差异
- 掌握了文档加载阶段的核心术语和设计思路

---

## 二、核心概念

### 2.1 RAG 数据流水线

`
原始文件 (.pdf / .txt / .md)
    |
    |  Day 1: DocumentLoader.load()    ← 我们在这里
    v
Document 对象 (content=str + metadata)
    |
    |  Day 2: TextSplitter.split()
    v
List[Document]  -- 每个就是一个 chunk
    |
    |  Day 3: Embedding.encode()
    v
List[chunk + 向量]
    |
    |  Day 4: VectorStore.add()
    v
向量数据库 (FAISS / Chroma)
`

Day 1 的产物是**内存中的中间产物**，不需要单独落盘，下一步 Day 2 的 TextSplitter 接手。

### 2.2 Document 数据结构

所有开源项目的 Document 本质都是：**文本字符串 + 字典元数据**。

| 项目 | 文本字段 | 额外字段 |
|------|----------|----------|
| LangChain | page_content: str | metadata: dict |
| LlamaIndex | 	ext: str | start_char_idx, end_char_idx |
| Dify | page_content: str | ector, children, ttachments |
| Unstructured | 	ext: str | category（26种Element类型）|
| **我们** | content: str | metadata, pages |

### 2.3 Metadata（元数据）

metadata = 文档的"身份证 + 体检报告"。

**加载时写入（溯源用）：**
- source：文件路径/URL — **必留，用于溯源**
- page：PDF 页码 — **必留，用于定位**
- 	itle：文档标题
- doc_type：文件类型
- encoding：文件编码
- headings：标题层级结构（Markdown）
- ile_size_bytes：文件大小
- line_count：行数

**检索时追加（Day 4）：**
- score：相似度分数
- keywords：关键词

---

## 三、代码实现要点

### 3.1 格式分发策略

采用**映射表模式**（而非 if/elif），扩展性更好：

`python
_PARSERS = {
    ".txt": "_load_txt",
    ".md":  "_load_markdown",
    ".pdf": "_load_pdf",
}

# 新增格式只需加一行映射 + 一个方法
`

Dify 用 if/elif，LangChain 用独立类，思路一致但风格不同。

### 3.2 编码检测

Windows 环境下 TXT 文件编码不统一，采用**依次尝试**策略：

`
UTF-8 → GBK → Latin-1（兜底）
`

### 3.3 Markdown 清洗

Markdown → HTML → 去标签 → 纯文本。

为什么要清洗？因为 #、**、-、<html> 标签对 LLM 的 embedding 是噪音。

### 3.4 PDF 解析

**常见坑（面试常考）：**
1. 表格 → 文本顺序错乱（pypdf 按流提取，不感知布局）
2. 页眉页脚 → 每页重复出现，需要去重
3. 多栏布局 → 左右栏文本交叉
4. 扫描版 PDF → 纯图片，需要 OCR

**各项目 PDF 库选择：**
- Dify：pypdfium2（支持图片提取）
- LangChain：pypdf / PDFPlumber
- Unstructured：pdfminer + 布局检测模型

---

## 四、开源项目对比

### 4.1 设计哲学

| 项目 | 一句话总结 |
|------|-----------|
| **LangChain** | 简单够用，page_content + metadata 就够了 |
| **LlamaIndex** | 多了字符位置索引，方便回溯原文 |
| **Dify** | Document 自带 children 字段，支持父子分段 |
| **Unstructured** | 26种 Element 类型，最细粒度的元素识别 |

### 4.2 Dify 架构要点

- **Extractor 模式**：每种格式一个类，ExtractProcessor 只做路由
- **父子分段**：大段落做检索（语义完整），小段落喂 LLM（精确答案）
- **缓存机制**：用 file_cache_key 避免重复解析

---

## 五、专业术语速查

| 术语 | 含义 | 用在哪 |
|------|------|--------|
| **Corpus** | 语料库，所有文档的集合 | "我们的 corpus 有 10 万篇文档" |
| **Ingestion** | 数据摄入/导入流程 | "ingestion pipeline 出错了" |
| **Preprocessing** | 预处理（加载+清洗+分段统称）| "preprocessing 阶段完成" |
| **Schema** | 数据结构定义 | "Document 的 schema" |
| **Provenance** | 溯源，数据从哪来 | "要支持 provenance tracking" |

---

## 六、Day 2 预习

下一步是 **文本分段（Chunking）**，这是 RAG 里最影响效果的环节。

要做的事：
- 实现 3 种分段器：按字符、按递归分隔符、按 Markdown 标题层级
- 对比测试同一文档用不同分段策略的切分效果
- 理解 chunk_size / overlap 等关键参数

关键问题：chunk 太大会导致检索不精确，太小会导致上下文丢失。怎么平衡？


---

## 运行方式

```bash
conda activate rag
PYTHONIOENCODING=utf-8 python day1/document_loader.py
```
