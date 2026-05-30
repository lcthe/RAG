"""
evaluate.py - Day 7: RAG 评估与优化
====================================
评估维度：
  1. 检索质量：Precision / Recall
  2. 回答相关性：关键词匹配 + LLM 打分
  3. 端到端准确率：对比标准答案
"""

import os, sys, json, time
from pathlib import Path
from dataclasses import dataclass, field


# ============================================================
# 第一部分：评估指标
# ============================================================

@dataclass
class EvalResult:
    """单条测试的评估结果。"""
    test_id: int
    question: str
    category: str
    # 检索质量
    retrieval_precision: float = 0.0    # 检索结果中相关文档的比例
    retrieval_recall: float = 0.0       # 相关文档被检索到的比例
    retrieved_docs: list = field(default_factory=list)
    # 回答质量
    answer_relevance: float = 0.0       # 回答与问题的相关性 (0-1)
    keyword_match: float = 0.0          # 关键词命中率 (0-1)
    answer_text: str = ""
    # 综合
    overall_score: float = 0.0
    latency_ms: float = 0.0


def calc_keyword_match(answer: str, expected_keywords: list[str]) -> float:
    """计算回答中命中期望关键词的比例。"""
    if not expected_keywords:
        return 1.0  # 没有期望关键词时默认满分
    hits = sum(1 for kw in expected_keywords if kw in answer)
    return hits / len(expected_keywords)


def calc_retrieval_precision(retrieved_sources: list[str], expected_docs: list[str]) -> float:
    """检索精度：检索结果中命中文档的比例。"""
    if not retrieved_sources:
        return 0.0 if expected_docs else 1.0
    if not expected_docs:
        return 0.0  # 不该检索却检索了

    hits = 0
    for src in retrieved_sources:
        for exp in expected_docs:
            if exp.lower() in src.lower():
                hits += 1
                break
    return hits / len(retrieved_sources)


def calc_retrieval_recall(retrieved_sources: list[str], expected_docs: list[str]) -> float:
    """检索召回率：期望文档被检索到的比例。"""
    if not expected_docs:
        return 1.0  # 没有期望文档时默认满分
    if not retrieved_sources:
        return 0.0

    hits = 0
    for exp in expected_docs:
        for src in retrieved_sources:
            if exp.lower() in src.lower():
                hits += 1
                break
    return hits / len(expected_docs)


def llm_judge(llm, question: str, answer: str) -> float:
    """用 LLM 评判回答相关性（0-1 分）。"""
    prompt = f"""请评判以下回答与问题的相关性，给出 0-1 的分数。

问题：{question}
回答：{answer}

评分标准：
1.0 - 完全回答了问题，信息准确
0.8 - 基本回答了问题，有少量遗漏
0.6 - 部分回答了问题
0.4 - 回答偏离主题
0.0 - 完全不相关或无法回答

只输出一个数字，不要其他内容。"""
    try:
        resp = llm.chat([{"role": "user", "content": prompt}], temperature=0)
        score = float(resp.content.strip())
        return max(0.0, min(1.0, score))
    except Exception:
        return 0.5  # LLM 打分失败时给中间分


# ============================================================
# 第二部分：评估器
# ============================================================

class RAGEvaluator:
    """RAG 系统评估器。"""

    def __init__(self, rag_pipeline, llm=None):
        self._pipeline = rag_pipeline
        self._llm = llm

    def evaluate_single(self, test_case: dict) -> EvalResult:
        """评估单条测试用例。"""
        question = test_case["question"]
        expected_kw = test_case.get("expected_answer_keywords", [])
        expected_docs = test_case.get("expected_doc_keywords", [])

        # 1. 运行 RAG Pipeline
        start = time.time()
        result = self._pipeline.query(question, save_history=False)
        latency = (time.time() - start) * 1000

        # 2. 提取检索到的文档来源
        retrieved_sources = []
        for s in result.sources:
            src = s.metadata.get("source", "")
            if src:
                retrieved_sources.append(Path(src).name)

        # 3. 计算检索质量
        precision = calc_retrieval_precision(retrieved_sources, expected_docs)
        recall = calc_retrieval_recall(retrieved_sources, expected_docs)

        # 4. 计算回答相关性（关键词匹配）
        keyword_match = calc_keyword_match(result.answer, expected_kw)

        # 5. LLM 打分（如果有 LLM）
        answer_relevance = keyword_match  # 默认用关键词匹配
        if self._llm:
            answer_relevance = llm_judge(self._llm, question, result.answer)

        # 6. 综合得分
        overall = (
            precision * 0.2 +
            recall * 0.2 +
            keyword_match * 0.3 +
            answer_relevance * 0.3
        )

        return EvalResult(
            test_id=test_case["id"],
            question=question,
            category=test_case.get("category", ""),
            retrieval_precision=precision,
            retrieval_recall=recall,
            retrieved_docs=retrieved_sources,
            answer_relevance=answer_relevance,
            keyword_match=keyword_match,
            answer_text=result.answer[:200],
            overall_score=overall,
            latency_ms=latency,
        )

    def evaluate_batch(self, test_cases: list[dict]) -> list[EvalResult]:
        """批量评估。"""
        results = []
        for i, tc in enumerate(test_cases, 1):
            print(f"  [{i}/{len(test_cases)}] {tc['question'][:30]}...", end=" ", flush=True)
            r = self.evaluate_single(tc)
            results.append(r)
            print(f"score={r.overall_score:.2f} ({r.latency_ms:.0f}ms)")
        return results

    def generate_report(self, results: list[EvalResult]) -> str:
        """生成评估报告。"""
        n = len(results)
        if n == 0:
            return "无评估结果"

        # 汇总指标
        avg_precision = sum(r.retrieval_precision for r in results) / n
        avg_recall = sum(r.retrieval_recall for r in results) / n
        avg_keyword = sum(r.keyword_match for r in results) / n
        avg_relevance = sum(r.answer_relevance for r in results) / n
        avg_overall = sum(r.overall_score for r in results) / n
        avg_latency = sum(r.latency_ms for r in results) / n

        # 按类别统计
        categories = {}
        for r in results:
            cat = r.category
            if cat not in categories:
                categories[cat] = {"count": 0, "scores": []}
            categories[cat]["count"] += 1
            categories[cat]["scores"].append(r.overall_score)

        # 找出薄弱环节
        weak_cases = [r for r in results if r.overall_score < 0.5]

        report = []
        report.append("=" * 60)
        report.append("  RAG 评估报告")
        report.append("=" * 60)
        report.append(f"\n  测试用例数: {n}")
        report.append(f"  平均耗时: {avg_latency:.0f}ms")
        report.append("")
        report.append("  --- 核心指标 ---")
        report.append(f"  检索精度 (Precision):  {avg_precision:.2%}")
        report.append(f"  检索召回率 (Recall):   {avg_recall:.2%}")
        report.append(f"  关键词命中率:          {avg_keyword:.2%}")
        report.append(f"  回答相关性:            {avg_relevance:.2%}")
        report.append(f"  综合得分:              {avg_overall:.2%}")
        report.append("")

        report.append("  --- 按类别统计 ---")
        for cat, data in sorted(categories.items()):
            avg = sum(data["scores"]) / len(data["scores"])
            report.append(f"  {cat}: {data['count']}条, 平均分={avg:.2f}")

        report.append("")

        if weak_cases:
            report.append("  --- 薄弱环节 (score < 0.5) ---")
            for r in weak_cases:
                report.append(f"  [{r.test_id}] {r.question[:40]}... score={r.overall_score:.2f}")
                report.append(f"      回答: {r.answer_text[:80]}...")
        else:
            report.append("  --- 所有测试用例得分均 >= 0.5 ---")

        report.append("")
        report.append("  --- 优化建议 ---")
        if avg_precision < 0.6:
            report.append("  - 检索精度低: 尝试调整 Top-K 或增加 Reranker")
        if avg_recall < 0.6:
            report.append("  - 检索召回率低: 尝试降低相似度阈值或增加 chunk 数量")
        if avg_keyword < 0.6:
            report.append("  - 关键词命中率低: 检查分段是否合理，尝试调整 chunk_size")
        if avg_latency > 5000:
            report.append("  - 延迟较高: 考虑缓存或优化检索流程")
        if avg_overall >= 0.8:
            report.append("  - 整体表现良好！可以考虑增加更多边界测试用例")

        return "\n".join(report)


# ============================================================
# 第三部分：Demo
# ============================================================

def demo():
    print("=" * 60)
    print("  Day 7 - RAG 评估与优化")
    print("=" * 60)

    # 1. 加载测试集
    print("\n--- 1. 加载测试集 ---")
    test_file = Path(__file__).parent / "test_cases.json"
    test_cases = json.loads(test_file.read_text(encoding="utf-8"))
    print(f"  共 {len(test_cases)} 条测试用例")

    # 2. 初始化 RAG Pipeline
    print("\n--- 2. 初始化 RAG Pipeline ---")
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "day5"))
    from rag_pipeline import RAGPipeline

    pipeline = RAGPipeline(chunk_size=300, chunk_overlap=50)
    data_dir = os.path.join(os.path.dirname(__file__), "..", "data")
    pipeline.ingest(data_dir)

    # 3. 初始化评估器
    print("\n--- 3. 开始评估 ---")
    evaluator = RAGEvaluator(pipeline)

    # 4. 批量评估
    results = evaluator.evaluate_batch(test_cases)

    # 5. 生成报告
    print("\n--- 4. 评估报告 ---")
    report = evaluator.generate_report(results)
    print(report)

    # 6. 保存结果
    output_file = Path(__file__).parent / "eval_results.json"
    eval_data = [
        {
            "id": r.test_id, "question": r.question, "category": r.category,
            "precision": r.retrieval_precision, "recall": r.retrieval_recall,
            "keyword_match": r.keyword_match, "relevance": r.answer_relevance,
            "overall": r.overall_score, "latency_ms": r.latency_ms,
            "answer": r.answer_text[:100],
        }
        for r in results
    ]
    output_file.write_text(json.dumps(eval_data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n  结果已保存到 {output_file}")


if __name__ == "__main__":
    demo()
