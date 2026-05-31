# Day 6 — Agent + RAG 集成 学习笔记

> 日期：2026-05-30
> 产出：agent.py
> 依赖：Day5 RAGPipeline + DeepSeek LLM

---

## 一、今天做了什么

实现了 Agent 决策层，让 RAG 系统从"被动回答"变成"主动思考"：

- BaseTool：工具抽象基类，统一接口
- ChatTool：闲聊工具，直接回答不检索
- RetrievalTool：知识库检索，封装 Day5 RAG Pipeline
- CalculatorTool：数学计算工具
- Agent：ReAct 模式（Reasoning + Acting），自主决定用什么工具

---

## 二、为什么需要 Agent

### 2.1 Day5 的问题

Day5 的 RAG Pipeline 是"无脑检索"——不管用户问什么，都去知识库搜：

```
用户: "你好" → 搜索"你好" → 搜不到 → 答非所问
用户: "899*10等于多少" → 搜索"899*10" → 搜不到 → 答非所问
用户: "ZY-SP100价格多少？买10台多少钱？" → 只回答价格，没算总价
```

### 2.2 Agent 解决什么

| 能力 | Day5 | Day6 Agent |
|------|------|-----------|
| 意图识别 | 无，全部检索 | 判断闲聊/检索/计算 |
| 工具选择 | 只有检索 | 多工具自主选择 |
| 多步推理 | 无 | 分步执行，逐步推理 |
| 条件路由 | 固定流程 | 根据问题动态路由 |

---

## 三、Tool 抽象层设计

### 3.1 统一接口

所有工具都继承 BaseTool，实现三个属性 + 一个方法：

```
BaseTool:
  name        -> 工具名（Agent 通过这个名字调用）
  description -> 工具描述（告诉 Agent 能做什么）
  execute()   -> 执行工具，返回 ToolResult
```

### 3.2 三个内置工具

| 工具 | 用途 | 什么时候用 |
|------|------|----------|
| ChatTool | 闲聊、问候、常识 | 不涉及知识库时 |
| RetrievalTool | 知识库检索 | 涉及产品、价格、规格时 |
| CalculatorTool | 数学计算 | 涉及数字运算时 |

### 3.3 工具注册

Agent 初始化时自动注册所有工具，并把工具描述注入 Prompt：

```
可用工具：
- chat: 闲聊、问候、常识问答
- retrieval: 从知识库检索产品信息
- calculator: 数学计算
```

---

## 四、ReAct 模式

### 4.1 什么是 ReAct

ReAct = Reasoning + Acting，是 Agent 的核心运行模式：

```
用户提问
    |
    v
[Think] Agent 思考：这个问题需要什么？
    |
    v
[Act] Agent 行动：调用某个工具
    |
    v
[Observe] Agent 观察：工具返回了什么结果？
    |
    v
[循环] 还需要更多信息？继续 Think -> Act -> Observe
    |
    v
[Final Answer] Agent 输出最终答案
```

### 4.2 Prompt 格式

LLM 按以下格式输出：

```
需要工具时：
Thought: 用户问的是产品价格，需要检索知识库
Action: retrieval
Action Input: ZY-SP100的价格是多少？

不需要工具时：
Thought: 这是闲聊，直接回答
Final Answer: 你好！我是智能助手...
```

### 4.3 循环控制

- 最多循环 max_steps 轮（默认 5），防止死循环
- LLM 输出 Final Answer 时立即停止
- 循环结束还没输出 Final Answer，强制总结

---

## 五、其他 Agent 运行模式

除了 ReAct，主流的 Agent 模式还有：

### 5.1 Plan-and-Execute（先规划再执行）

先让 LLM 制定完整计划，再逐步执行：

```
Plan:
  1. 检索 ZY-SP100 价格
  2. 计算 10 台总价
  3. 组合答案

Execute:
  Step 1: retrieval("ZY-SP100价格") -> 899元
  Step 2: calculator("899*10") -> 8990
  Step 3: 组合答案
```

优点：全局规划，步骤清晰；可以并行执行独立步骤
缺点：计划可能不准，执行中需要调整

### 5.2 LLM Compiler（并行执行）

类似编译器的依赖分析，识别哪些步骤可以并行：

```
Query: "ZY-SP100 和 ZY-CV200 分别多少钱？"

依赖分析：
  Step 1 (retrieval("ZY-SP100价格")) --+
                                        +--> Step 3 (组合答案)
  Step 2 (retrieval("ZY-CV200价格")) --+

执行：Step 1 和 Step 2 并行 -> Step 3
```

优点：大幅提速（并行调用 LLM/工具）
缺点：实现复杂，需要依赖分析

### 5.3 Reflexion（自我反思）

Agent 执行后反思结果，改进下一次行动：

```
Round 1:
  Act: retrieval("音箱价格")
  Observe: 返回了 ZY-SP100 的价格
  Reflect: 用户问的可能是所有音箱，不只是一款
  Retry: retrieval("所有音箱价格列表")

Round 2:
  Observe: 返回了多款音箱价格
  Answer: 完整回答
```

优点：自我纠错，回答质量更高
缺点：多轮调用，延迟高

### 5.4 Function Calling（结构化调用）

用 DeepSeek/OpenAI 的原生 Function Calling，不自己解析文本：

```python
# 定义工具的 JSON Schema
tools = [{
    "type": "function",
    "function": {
        "name": "retrieval",
        "description": "从知识库检索信息",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "检索关键词"}
            }
        }
    }
}]

# LLM 直接返回结构化的工具调用，不需要自己解析文本
response = llm.chat(messages, tools=tools)
```

优点：不需要自己解析文本，100% 准确；模型官方支持
缺点：依赖模型的 Function Calling 能力；工具定义有数量限制

### 5.5 Multi-Agent（多 Agent 协作）

多个专业 Agent 分工合作：

```
用户: "分析 ZY-SP100 的市场竞争力"

协调器 Agent:
  +-- 调研 Agent -> 检索产品信息
  +-- 分析 Agent -> 对比竞品数据
  +-- 计算 Agent -> 计算市场份额
  +-- 写作 Agent -> 生成分析报告
```

优点：专业分工，复杂任务处理能力强
缺点：架构复杂，Agent 间通信开销大

### 5.6 模式对比

| 模式 | 核心思路 | 适用场景 | 实现复杂度 |
|------|---------|---------|-----------|
| ReAct | 边想边做 | 通用问答 | 低 |
| Plan-and-Execute | 先想后做 | 复杂多步任务 | 中 |
| LLM Compiler | 并行执行 | 多个独立子任务 | 高 |
| Reflexion | 做完反思 | 需要高准确率 | 中 |
| Function Calling | 结构化调用 | 工具调用场景 | 低（模型自带） |
| Multi-Agent | 多 Agent 协作 | 超复杂任务 | 很高 |

实际项目通常混合使用，比如 Dify 同时支持 ReAct 和 Function Calling 两种模式。

---

## 六、完整执行流程

### 5.1 闲聊场景

```
用户: "你好"
  Step 1: Thought=闲聊 → Final Answer="你好！我是智能助手..."
  耗时: ~2s, 1步
```

### 5.2 单步检索

```
用户: "ZY-SP100 的价格是多少？"
  Step 1: Thought=需要检索 → Action=retrieval("ZY-SP100的价格是多少？")
  Observation: ZY-SP100 官方售价 899 元，首发优惠价 699 元
  Step 2: Thought=已有信息 → Final Answer="ZY-SP100 售价 899 元..."
  耗时: ~2.5s, 2步
```

### 5.3 多步推理

```
用户: "ZY-SP100 单价多少？10台多少钱？"
  Step 1: Thought=需要先查价格 → Action=retrieval("ZY-SP100 单价多少？")
  Observation: 官方售价 899 元，首发优惠价 699 元
  Step 2: Thought=需要计算 → Action=calculator("899 * 10")
  Observation: 899 * 10 = 8990
  Step 3: Thought=还要算优惠价 → Action=calculator("699 * 10")
  Observation: 699 * 10 = 6990
  Step 4: Thought=信息齐全 → Final Answer="官方价899元，10台8990元；优惠价699元，10台6990元"
  耗时: ~4.3s, 4步
```

### 5.4 知识库+计算

```
用户: "ZY-SP100 首发优惠价是多少？买5台打9折，总价多少？"
  Step 1: Action=retrieval("ZY-SP100 首发优惠价")
  Observation: 首发优惠价 699 元
  Step 2: Action=calculator("699 * 5 * 0.9")
  Observation: 699 * 5 * 0.9 = 3145.5
  Step 3: Final Answer="优惠价699元，买5台打9折总价3145.5元"
  耗时: ~3.7s, 3步
```

---

## 七、测试结果

| 场景 | 问题 | 步骤 | 工具调用 | 耗时 |
|------|------|------|---------|------|
| 闲聊 | 你好，你是谁？ | 1 | 无（直接回答） | ~2.3s |
| 检索 | ZY-SP100 价格多少？ | 2 | retrieval | ~2.5s |
| 计算 | 899 * 10 等于多少？ | 2 | calculator | ~1.5s |
| 多步推理 | 单价多少？10台多少钱？ | 4 | retrieval + calculator×2 | ~4.3s |
| 知识库+计算 | 优惠价？5台9折总价？ | 3 | retrieval + calculator | ~3.7s |

---

## 八、生产级项目怎么设计

### 7.1 核心区别：插件化 vs 硬编码

我们写的（硬编码）：

```python
class RAGPipeline:
    def __init__(self):
        self.splitter = RecursiveSplitter()     # 写死了
        self.embedding = BGEProvider()           # 写死了
        self.retriever = RetrieverPipeline()     # 写死了
```

Dify 的做法（配置驱动）：

```yaml
index:
  embedding_model: text-embedding-3-small    # 可换
  retrieval_mode: hybrid                     # 可换
  reranking_model: bge-reranker-v2-m3       # 可换
  keyword_table: jieba                       # 可换
```

### 7.2 Dify 的知识库检索架构

从参考代码（dataset_retrieval.py，1500+ 行）看，Dify 的检索层：

```
Dify 的检索层
+-- RetrievalService          # 统一检索入口
|   +-- VectorRetrieval       # 向量检索（可换模型）
|   +-- FullTextRetrieval     # 全文检索（可换引擎）
|   +-- HybridRetrieval       # 混合检索
+-- DataPostProcessor         # 后处理
|   +-- Reranking             # 重排序（可换模型）
|   +-- ScoreFusion           # 分数融合
+-- MetadataFilter            # 元数据过滤
|   +-- ConditionFilter       # 条件过滤（标签、时间、来源）
+-- MultiDatasetRouter        # 多知识库路由
|   +-- FunctionCallRouter    # 函数调用路由
|   +-- ReactRouter           # ReAct 路由
+-- CallbackHandler           # 回调/可观测性
    +-- TraceManager          # 链路追踪
```

### 7.3 RAGFlow 的侧重点

RAGFlow 更关注数据质量，它的 Loader 抽象层：

```
RAGFlow 的解析层
+-- Loader 抽象               # 统一加载接口
|   +-- PDF Parser            # 深度 PDF 解析（表格、图片、公式）
|   +-- Word Parser           # Word 解析
|   +-- Excel Parser          # Excel 解析
+-- 质量保证
    +-- 版面分析              # 识别标题、段落、表格
    +-- OCR                   # 扫描版 PDF 处理
    +-- 表格提取              # 结构化数据
```

### 7.4 MaxKB 的低代码 RAG

MaxKB（Max Knowledge Base）走的是低代码路线，核心理念是"拖拽式搭建 RAG"：

```
MaxKB 的架构
+-- 前端可视化编排
|   +-- 知识库管理            # 上传文档，自动分段+向量化
|   +-- 工作流编排            # 拖拽节点搭建 Pipeline
|   +-- 应用发布              # 一键发布为 API/Web 应用
+-- 后端引擎
|   +-- 问题分类器            # 意图识别，路由到不同流程
|   +-- 知识检索              # 向量+关键词混合检索
|   +-- LLM 节点              # 可换模型（DeepSeek/GPT/本地）
|   +-- 工具调用              # 内置工具 + 自定义工具
|   +-- 条件分支              # if/else 逻辑控制
+-- 数据层
    +-- PostgreSQL            # 元数据存储
    +-- 向量库                # 向量索引
```

和 Dify/RAGFlow 的区别：

| 维度 | Dify | RAGFlow | MaxKB |
|------|------|---------|-------|
| 定位 | 通用 AI 应用平台 | 深度文档理解 | 轻量级知识库问答 |
| 核心优势 | 插件丰富，生态好 | PDF 解析质量高 | 上手快，低代码 |
| 目标用户 | 开发者 | 数据团队 | 业务人员 |
| 工作流 | 支持 | 不支持 | 支持（简化版）|
| 部署 | Docker | Docker | Docker |
| 开源协议 | Apache 2.0 | Apache 2.0 | GPL v3 |

MaxKB 的特点：
- 零代码：通过 Web 界面完成所有配置
- 开箱即用：Docker 一键部署，5 分钟搭建知识库
- 多模型：支持 OpenAI、DeepSeek、本地 Ollama 等
- 工作流：可视化编排，支持条件分支和循环

适合作为入门级 RAG 平台体验，不需要写代码就能跑通完整流程。

### 7.4 生产项目的共同设计模式

**模式 1：插件化架构**

```python
# 生产项目：通过注册机制动态加载
class RetrieverFactory:
    _registry = {}

    @classmethod
    def register(cls, name, retriever_class):
        cls._registry[name] = retriever_class

    @classmethod
    def create(cls, name, **config):
        return cls._registry[name](**config)

# 注册不同的检索器
RetrieverFactory.register("vector", VectorRetriever)
RetrieverFactory.register("keyword", KeywordRetriever)
RetrieverFactory.register("hybrid", HybridRetriever)

# 使用时通过配置选择
retriever = RetrieverFactory.create(config.retrieval_mode)
```

**模式 2：配置驱动**

```yaml
# config.yaml
dataset:
  retrieval:
    mode: hybrid
    vector_weight: 0.7
    keyword_weight: 0.3
  embedding:
    provider: openai
    model: text-embedding-3-small
  rerank:
    enabled: true
    model: bge-reranker-v2-m3
  splitting:
    strategy: recursive
    chunk_size: 500
```

**模式 3：可观测性（我们完全没做）**

```python
# 生产项目：每个步骤都记录 trace
class RAGPipeline:
    def query(self, question):
        with trace.span("retrieve") as span:
            results = self.retriever.search(question)
            span.log("results_count", len(results))

        with trace.span("rerank") as span:
            reranked = self.reranker.rerank(results)
            span.log("top_score", reranked[0].score)

        with trace.span("generate") as span:
            answer = self.llm.chat(prompt)
            span.log("tokens", answer.tokens_used)
```

**模式 4：语义缓存**

```python
# 生产项目：相似问题复用结果
class CachedRetriever:
    def search(self, query):
        cache_key = self.embedding.encode(query)
        cached = self.cache.get_similar(cache_key, threshold=0.95)
        if cached:
            return cached  # 命中缓存，跳过检索
        results = self.retriever.search(query)
        self.cache.set(cache_key, results)
        return results
```

### 7.5 对比总结

| 层面 | 我们的学习项目 | 生产项目（Dify/RAGFlow/MaxKB） |
|------|--------------|------------------------------|
| 架构 | 硬编码，写死流程 | 插件化，配置驱动 |
| 灵活性 | 换模型要改代码 | 换配置就行 |
| 可观测性 | print 调试 | 链路追踪 + 日志 |
| 可靠性 | 出错就崩 | 重试 + 降级 + 缓存 |
| 规模 | 单机跑 | 分布式 + 多租户 |

核心算法（向量检索、BM25、Rerank）都一样，区别在于怎么把它们搭成一个可靠、可扩展、可维护的系统。

---

## 九、Day 7 预习

Day 6 让 Agent 能自主选择工具了，但还有改进空间：

- 评估与优化：Agent 的回答质量怎么样？怎么量化？
- 评估指标：准确性、相关性、完整性
- 优化方向：Prompt 调优、检索参数调优、工具选择优化
- 端到端测试：批量测试各种问题类型

关键问题：怎么衡量 RAG 系统的好坏？有哪些评估指标？


---

## 运行方式

```bash
conda activate rag
set DEEPSEEK_API_KEY=your-deepseek-api-key
python day6/agent.py
```
