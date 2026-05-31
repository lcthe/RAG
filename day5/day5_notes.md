# Day 5 — RAG Pipeline 串连 学习笔记

> 日期：2026-05-30
> 产出：rag_pipeline.py
> 依赖：前 4 天所有模块 + LLM（DeepSeek API 或 MockLLM）

---

## 一、今天做了什么

把 Day1-Day4 的所有模块串成完整的 RAG 问答系统：

- PromptTemplate：Prompt 模板管理，自动组装 context + history + question
- ConversationHistory：多轮对话历史管理
- RAGPipeline：端到端流水线（加载 -> 分段 -> 向量化 -> 检索 -> 生成）
- LLM 抽象层：MockLLM（本地测试） + DeepSeekLLM（真实 API）

---
理解了今天的产出，下面先回答一个核心问题：RAG 到底是什么？为什么要把检索和生成拼在一起？


## 二、RAG 到底是什么

RAG = Retrieval-Augmented Generation（检索增强生成）

传统 LLM 的问题：
- 知识截止：训练数据有时间限制，不知道最新信息
- 幻觉：没有依据时会"编造"答案
- 私有知识：无法访问企业内部文档

RAG 的解决思路：
- 不改模型，改输入
- 先从知识库检索相关信息
- 把检索结果和问题一起喂给 LLM
- LLM 基于检索到的事实生成答案

流程图：

```
用户提问: "ZY-SP100 价格多少？"
         |
         v
    检索阶段（Day1-4）
    知识库 -> 相关文档片段
         |
         v
    生成阶段（Day5）
    [上下文 + 问题] -> LLM -> 答案
         |
         v
    "ZY-SP100 售价 2999 元..."
```

---
搞清楚 RAG 的原理后，接下来看看实际的 Pipeline 怎么设计。前 4 天的模块怎么串成一个端到端的系统？


## 三、Pipeline 架构设计

### 3.1 整体流程

```
ingest（索引阶段）:
  文件 -> DocumentLoader(Day1) -> TextSplitter(Day2)
  -> Embedding(Day3) -> VectorStore + BM25(Day4)

query（查询阶段）:
  问题 -> RetrieverPipeline(Day4) -> 检索结果
  -> PromptTemplate(Day5) -> [context + history + question]
  -> LLM(Day5) -> 答案
```

### 3.2 核心类设计

| 类 | 职责 | 依赖 |
|---|------|------|
| PromptTemplate | 组装 Prompt（context + history + question） | SearchResult |
| ConversationHistory | 管理多轮对话历史 | ChatMessage |
| RAGPipeline | 端到端流水线 | Day1-4 所有模块 |
| BaseLLM | LLM 抽象基类 | - |
| MockLLM | 本地测试用模拟 LLM | - |
| OpenAILLM | DeepSeek API 真实 LLM | openai（DeepSeek 兼容） |

---
Pipeline 架构定下来了，但还缺一个关键环节：怎么把检索到的内容和用户问题组装成 LLM 能看懂的 Prompt？


## 四、Prompt 模板设计

### 4.1 为什么需要模板

直接拼接有问题：
- LLM 不知道"哪些是知识库内容，哪些是用户问题"
- 没有规则约束，LLM 可能无视上下文乱答
- 多轮对话需要带上历史记录

模板解决：
- 明确的角色定义（system prompt）
- 结构化的 context 区域
- 对话历史占位符
- 用户问题位置

### 4.2 默认模板结构

```
[System Prompt] 规则定义
---
[Context] 检索结果（来源 + 内容）
---
[Chat History] 最近 N 轮对话
用户问题：[Question]
请基于以上知识库内容回答：
```

### 4.3 Context 组装

每条检索结果格式：
```
[来源1] (product_zy_sp100.txt, 相似度=0.823)
ZY-SP100 智能音箱，售价 2999 元，支持蓝牙 5.0...

[来源2] (api_documentation.md, 相似度=0.751)
音频规格：支持 AAC、LDAC、aptX HD...
```

关键点：
- 来源文件名方便溯源
- 相似度分数让用户判断可信度
- 内容截取前 200 字（避免 context 过长）

---
Prompt 模板解决了单轮问答的组装问题。但实际场景中用户往往会连着问好几个问题，怎么让 LLM 记得乊前的对话内容？


## 五、多轮对话管理

### 5.1 为什么需要对话历史

单轮问题：
- "ZY-SP100 是什么？" -> 介绍产品
- "它有什么特点？" -> LLM 不知道"它"指什么

多轮对话：
- "ZY-SP100 是什么？" -> 介绍产品
- "它有什么特点？" -> LLM 知道"它"= ZY-SP100，回答特点

### 5.2 历史管理策略

- 保留最近 N 轮（默认 3 轮，共 6 条消息）
- 防止 context 超长导致 LLM 性能下降
- 超出限制的旧消息自动丢弃

### 5.3 历史在 Prompt 中的位置

```
[对话历史]
用户: ZY-SP100 是什么？
助手: ZY-SP100 是智云科技推出的智能音箱...

用户问题：它有什么特点？
```

---
对话历史管理好了，下一个问题：用什么 LLM 来生成答案？开发时没有 API Key 怎么测试？


## 六、LLM 抽象层

### 6.1 为什么需要抽象

不同场景用不同 LLM：
- 开发调试 -> MockLLM（免费、快速、无需网络）
- 本地测试 -> MockLLM
- 生产环境 -> DeepSeek / 其他 API

统一接口：都实现 chat(messages) -> LLMResponse

### 6.2 MockLLM 策略

不是真正的生成，而是从 context 中提取信息拼接回答：
- 从检索结果中取关键段落
- 组织成结构化回答
- 标注"来自知识库检索结果"

用途：验证整个 Pipeline 流程是否正确，不需要 API Key

### 6.3 自动选择

get_llm("auto") 逻辑：
1. 检查环境变量 DEEPSEEK_API_KEY
2. 有 -> 用 DeepSeekLLM
3. 没有 -> 用 MockLLM + 提示

---
所有组件都准备好了，现在把它们串成完整的端到端流程。从用户提问到拿到答案，中间经过哪些步骤？


## 七、完整检索流程（端到端）

```
用户提问: "音箱的价格是多少？"
         |
         v
第1步  Embedding（Day3）
       问题 -> 向量
         |
         v
第2步  混合检索（Day4）
       向量检索 + BM25 -> 粗筛 Top-K*2
         |
         v
第3步  重排序（Day4 Reranker）
       精排 -> Top-K
         |
         v
第4步  Context 组装（Day5 PromptTemplate）
       检索结果 -> 结构化文本
         |
         v
第5步  Prompt 构造
       system + context + history + question
         |
         v
第6步  LLM 生成（Day5）
       Prompt -> LLM -> 答案
         |
         v
第7步  保存历史
       记录 Q&A 到 ConversationHistory
         |
         v
    返回 RAGResponse（答案 + 来源 + 耗时）
```

---
流程设计完成了，实际跑一下看效果怎么样。知识库加载了多少文档？检索速度多快？多轮对话能不能记住上下文？


## 八、测试结果

### 8.1 知识库加载

| 指标 | 数值 |
|------|------|
| 文档数 | 9 |
| 分段数 | 65 |
| 向量维度 | 512 |
| 索引类型 | Flat（暴力搜索） |
| Embedding 模型 | BAAI/bge-small-zh-v1.5 |

### 8.2 单轮问答

| 问题 | 检索条数 | 耗时 |
|------|---------|------|
| 音箱的价格是多少？ | 2 | ~8ms |
| ZY-SP100 有哪些功能？ | 2 | ~6ms |
| 保修期多久？ | 2 | ~7ms |

（使用 DeepSeek API，检索 + 生成总耗时约 1-2 秒）

### 8.3 多轮对话

| 轮次 | 问题 | 历史条数 |
|------|------|---------|
| 1 | ZY-SP100 是什么？ | 0 |
| 2 | 它有什么特点？ | 2 |
| 3 | 价格呢？ | 4 |

---
测试结果看完了，Day 5 的 RAG Pipeline 已经跑通。但目前还是被动回答模式，下一步要让系统更智能——让 Agent 自己决定什么时候查知识库，什么时候直接回答。


## 九、Day 6 预习

Day 5 把 RAG 流水线串起来了，但还是"被动回答"模式。下一步是让系统更智能：

- Agent + RAG 集成
- 意图识别：判断问题是需要检索还是闲聊
- 工具调用：Agent 自主决定用什么工具
- 多步推理：复杂问题分步检索和回答
- 自动路由：根据问题类型选择不同的检索策略

关键问题：Agent 怎么知道什么时候该查知识库，什么时候直接回答？


---

## 运行方式

```bash
conda activate rag
set DEEPSEEK_API_KEY=your-deepseek-api-key
python day5/rag_pipeline.py
```
