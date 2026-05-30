"""
optimize.py - Day 7: 优化前后对比
==================================
不修改原始代码，通过包装器实现优化，对比优化前后效果。

优化策略：
  1. chunk_size: 300 -> 200（更小的块 = 更精准的检索）
  2. Top-K: 3 -> 5（更多候选 = 更好的召回）
  3. System Prompt 优化（更好的回答格式 + 超出范围处理）
  4. Prompt 模板优化（更明确的回答要求）
"""

import os, sys, json, time
from pathlib import Path
from dataclasses import dataclass, field


# ============================================================
# 第一部分：优化后的 Prompt 模板
# ============================================================

# 优化后的 System Prompt（关键改动：增加格式要求 + 超出范围处理）
OPTIMIZED_SYSTEM_PROMPT = """你是一个智能助手，基于提供的知识库内容回答用户问题。

规则：
1. 只根据提供的上下文信息回答问题
2. 如果上下文中没有相关信息，简短告知"根据现有知识库信息，无法回答该问题"，不要添加无关内容
3. 回答要准确、简洁、有条理
4. 引用具体信息时注明来源
5. 涉及数字计算时，直接给出计算过程和结果"""

# 优化后的 RAG Prompt 模板（增加格式引导）
OPTIMIZED_RAG_TEMPLATE = """{system_prompt}

---
以下是从知识库中检索到的相关信息：

{context}
---

{chat_history}用户问题：{question}

请基于以上知识库内容，用简洁的语言回答："""


# ============================================================
# 第二部分：优化后的 Pipeline 包装器
# ============================================================

class OptimizedRAGPipeline:
    """
    优化后的 RAG Pipeline 包装器。
    不修改原始代码，通过组合和参数调整实现优化。
    """

    def __init__(self, original_pipeline, overrides: dict = None):
        """
        Args:
            original_pipeline: 原始的 RAGPipeline 实例
            overrides: 参数覆盖 dict
        """
        self._pipeline = original_pipeline
        self._overrides = overrides or {}

        # 优化 1: 替换 Prompt 模板
        from rag_pipeline import PromptTemplate
        self._pipeline.prompt_template = PromptTemplate(
            template=OPTIMIZED_RAG_TEMPLATE,
            system_prompt=OPTIMIZED_SYSTEM_PROMPT,
        )

    def query(self, question, top_k=None, **kwargs):
        """代理原始 query 方法，覆盖参数。"""
        k = top_k or self._overrides.get("top_k", 5)
        return self._pipeline.query(
            question, top_k=k,
            use_hybrid=kwargs.get("use_hybrid", True),
            use_rerank=kwargs.get("use_rerank", True),
            save_history=kwargs.get("save_history", False),
        )

    @property
    def info(self):
        return self._pipeline.info()


# ============================================================
# 第三部分：对比评估
# ============================================================

def calc_keyword_match(answer, expected_keywords):
    if not expected_keywords:
        return 1.0
    hits = sum(1 for kw in expected_keywords if kw in answer)
    return hits / len(expected_keywords)

def calc_retrieval_precision(retrieved_sources, expected_docs):
    if not retrieved_sources:
        return 0.0 if expected_docs else 1.0
    if not expected_docs:
        return 0.0
    hits = sum(1 for src in retrieved_sources
               if any(exp.lower() in src.lower() for exp in expected_docs))
    return hits / len(retrieved_sources)

def calc_retrieval_recall(retrieved_sources, expected_docs):
    if not expected_docs:
        return 1.0
    if not retrieved_sources:
        return 0.0
    hits = sum(1 for exp in expected_docs
               if any(exp.lower() in src.lower() for src in retrieved_sources))
    return hits / len(expected_docs)


def llm_judge(llm, question, answer, expected_keywords):
    """用 LLM 评判回答质量（0-1）。"""
    prompt = f"""评判以下 RAG 系统的回答质量，输出 0-1 的分数。

问题：{question}
回答：{answer}
期望关键词：{expected_keywords}

评分标准（综合考虑准确性、完整性、简洁性）：
1.0 - 完全正确，信息完整，表达简洁
0.8 - 基本正确，有少量遗漏
0.6 - 部分正确，有明显遗漏或冗余
0.4 - 回答偏离或信息不准确
0.2 - 严重错误或答非所问
0.0 - 完全无法回答

只输出一个数字。"""
    try:
        resp = llm.chat([{"role": "user", "content": prompt}], temperature=0)
        return max(0.0, min(1.0, float(resp.content.strip())))
    except Exception:
        return 0.5


def evaluate_pipeline(pipeline, test_cases, llm=None, label=""):
    """对一个 Pipeline 运行评估，返回结果列表。"""
    results = []
    for tc in test_cases:
        start = time.time()
        result = pipeline.query(tc["question"], save_history=False)
        latency = (time.time() - start) * 1000

        sources = [Path(s.metadata.get("source", "")).name
                   for s in result.sources if s.metadata.get("source")]

        precision = calc_retrieval_precision(sources, tc.get("expected_doc_keywords", []))
        recall = calc_retrieval_recall(sources, tc.get("expected_doc_keywords", []))
        kw_match = calc_keyword_match(result.answer, tc.get("expected_answer_keywords", []))

        # 用 LLM 评判回答质量
        if llm:
            quality = llm_judge(llm, tc["question"], result.answer,
                               tc.get("expected_answer_keywords", []))
        else:
            quality = kw_match

        # 综合得分：检索质量 40% + 回答质量 60%
        overall = (precision * 0.2 + recall * 0.2 + quality * 0.6)

        results.append({
            "id": tc["id"],
            "question": tc["question"],
            "category": tc.get("category", ""),
            "precision": precision,
            "recall": recall,
            "keyword_match": kw_match,
            "quality": quality,
            "overall": overall,
            "latency_ms": latency,
            "answer": result.answer[:150],
        })
    return results


def print_comparison(before, after, test_cases):
    """打印优化前后对比表。"""
    print("\n" + "=" * 90)
    print("  优化前后对比")
    print("=" * 90)

    # 表头
    print(f"\n  {'ID':>3} {'问题':<30} {'优化前':>6} {'优化后':>6} {'提升':>6}")
    print(f"  {'---':>3} {'-'*30:<30} {'------':>6} {'------':>6} {'------':>6}")

    # 逐条对比
    improvements = 0
    regressions = 0
    for b, a in zip(before, after):
        q = b["question"][:28]
        delta = a["overall"] - b["overall"]
        marker = "+" if delta > 0 else ("=" if delta == 0 else "")
        if delta > 0:
            improvements += 1
        elif delta < 0:
            regressions += 1
        print(f"  {b['id']:>3} {q:<30} {b['overall']:>5.2f}  {a['overall']:>5.2f}  {marker}{delta:>+5.2f}")

    # 汇总
    n = len(before)
    avg_before = sum(b["overall"] for b in before) / n
    avg_after = sum(a["overall"] for a in after) / n
    avg_delta = avg_after - avg_before

    p_before = sum(b["precision"] for b in before) / n
    p_after = sum(a["precision"] for a in after) / n

    r_before = sum(b["recall"] for b in before) / n
    r_after = sum(a["recall"] for a in after) / n

    kw_before = sum(b["keyword_match"] for b in before) / n
    kw_after = sum(a["keyword_match"] for a in after) / n

    lat_before = sum(b["latency_ms"] for b in before) / n
    lat_after = sum(a["latency_ms"] for a in after) / n

    print(f"\n  {'汇总':<30} {'':>6} {'':>6}")
    print(f"  {'-'*60}")
    print(f"  {'综合得分':<28} {avg_before:>6.2%}  {avg_after:>6.2%}  {avg_delta:>+5.2%}")
    print(f"  {'检索精度':<28} {p_before:>6.2%}  {p_after:>6.2%}  {p_after-p_before:>+5.2%}")
    print(f"  {'检索召回率':<27} {r_before:>6.2%}  {r_after:>6.2%}  {r_after-r_before:>+5.2%}")
    print(f"  {'关键词命中':<27} {kw_before:>6.2%}  {kw_after:>6.2%}  {kw_after-kw_before:>+5.2%}")
    print(f"  {'平均耗时':<28} {lat_before:>5.0f}ms  {lat_after:>5.0f}ms")
    print(f"\n  提升: {improvements}条, 下降: {regressions}条, 不变: {n-improvements-regressions}条")


# ============================================================
# 第四部分：Demo
# ============================================================

def demo():
    print("=" * 70)
    print("  Day 7 - 优化前后对比")
    print("=" * 70)

    # 1. 加载测试集
    print("\n--- 1. 加载测试集 ---")
    test_file = Path(__file__).parent / "test_cases.json"
    test_cases = json.loads(test_file.read_text(encoding="utf-8"))
    print(f"  共 {len(test_cases)} 条测试用例")

    # 2. 初始化原始 Pipeline
    print("\n--- 2. 初始化原始 Pipeline ---")
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "day5"))
    from rag_pipeline import RAGPipeline

    pipeline = RAGPipeline(chunk_size=300, chunk_overlap=50)
    data_dir = os.path.join(os.path.dirname(__file__), "..", "data")
    pipeline.ingest(data_dir)

    # 3. 初始化 LLM for judging
    print("\n--- 3. 初始化 LLM（用于评判回答质量）---")
    from rag_pipeline import get_llm
    judge_llm = get_llm("auto")

    # 4. 优化前评估
    print("\n--- 4. 优化前评估 ---")
    before_results = evaluate_pipeline(pipeline, test_cases, llm=judge_llm, label="before")

    # 5. 创建优化后的 Pipeline
    print("\n--- 4. 创建优化后 Pipeline ---")
    print("  优化策略:")
    print("    1. chunk_size: 300 -> 200（更精准的检索）")
    print("    2. Top-K: 3 -> 5（更多候选）")
    print("    3. System Prompt 优化（更好的格式 + 超出范围处理）")

    # 创建优化后的 pipeline（用新的分段参数重建索引）
    from rag_pipeline import RAGPipeline as PipelineV2
    optimized_pipeline = PipelineV2(chunk_size=200, chunk_overlap=50)
    optimized_pipeline.ingest(data_dir)

    # 包装优化
    optimized = OptimizedRAGPipeline(
        optimized_pipeline,
        overrides={"top_k": 5}
    )

    # 6. 优化后评估
    print("\n--- 6. 优化后评估 ---")
    after_results = evaluate_pipeline(optimized, test_cases, llm=judge_llm, label="after")

    # 7. 对比
    print_comparison(before_results, after_results, test_cases)

    # 7. 保存对比结果
    comparison = {
        "before": before_results,
        "after": after_results,
        "optimizations": [
            "chunk_size: 300 -> 200",
            "top_k: 3 -> 5",
            "System Prompt: 增加格式要求和超出范围处理",
        ]
    }
    output_file = Path(__file__).parent / "comparison.json"
    output_file.write_text(json.dumps(comparison, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n  对比结果已保存到 {output_file}")


if __name__ == "__main__":
    demo()
