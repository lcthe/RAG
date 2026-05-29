"""
embeddings.py - RAG Embedding 与向量化模块
==========================================
Day 3 产出：多模型兼容的 EmbeddingProvider

核心概念：
    Embedding = 把文本变成数字向量，让机器能"理解"语义
    语义相近的文本 → 向量距离近
    语义不同的文本 → 向量距离远

支持模型：
    1. 本地模型：BGE-small-zh（智源，中文优化）
    2. OpenAI：text-embedding-3-small
    3. 硅基流动：BAAI/bge-m3

依赖：
    pip install sentence-transformers numpy scikit-learn
"""

from __future__ import annotations

import os
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional

import numpy as np


# ============================================================
# 第一部分：数据结构
# ============================================================

@dataclass
class EmbeddingResult:
    """
    Embedding 结果。

    Attributes:
        text:       原始文本
        vector:     向量（float 列表）
        model:      使用的模型名称
        dimension:  向量维度
        latency_ms: 耗时（毫秒）
    """
    text: str
    vector: list[float]
    model: str
    dimension: int
    latency_ms: float = 0.0

    def __repr__(self) -> str:
        return (
            f"EmbeddingResult(model={self.model}, dim={self.dimension}, "
            f"latency={self.latency_ms:.1f}ms, text='{self.text[:30]}...')"
        )


# ============================================================
# 第二部分：基类
# ============================================================

class BaseEmbeddingProvider(ABC):
    """
    Embedding 提供者基类。

    所有模型都实现 encode() 方法：
        输入：文本（字符串或列表）
        输出：向量（list[float] 或 list[list[float]]）
    """

    @property
    @abstractmethod
    def model_name(self) -> str:
        """模型名称标识。"""
        pass

    @property
    @abstractmethod
    def dimension(self) -> int:
        """向量维度。"""
        pass

    @abstractmethod
    def _encode_single(self, text: str) -> list[float]:
        """编码单条文本。"""
        pass

    def encode(self, text: str | list[str]) -> list[float] | list[list[float]]:
        """
        编码文本为向量。

        Args:
            text: 单条文本或文本列表

        Returns:
            单条返回 list[float]，多条返回 list[list[float]]
        """
        if isinstance(text, str):
            return self._encode_single(text)
        return [self._encode_single(t) for t in text]

    def encode_with_metadata(self, text: str) -> EmbeddingResult:
        """编码并返回带元数据的结果。"""
        start = time.time()
        vector = self._encode_single(text)
        latency = (time.time() - start) * 1000
        return EmbeddingResult(
            text=text,
            vector=vector,
            model=self.model_name,
            dimension=len(vector),
            latency_ms=latency,
        )


# ============================================================
# 第三部分：3 种模型实现
# ============================================================

class LocalBGEProvider(BaseEmbeddingProvider):
    """
    本地 BGE 模型（智源 BAAI/bge-small-zh-v1.5）。

    优点：
        - 免费，无需 API Key
        - 中文效果好
        - 可离线运行

    缺点：
        - 需要下载模型（约 100MB）
        - 首次加载较慢
        - CPU 推理速度一般

    适用：学习、开发、小规模生产
    """

    def __init__(self, model_name: str = "BAAI/bge-small-zh-v1.5"):
        """
        Args:
            model_name: HuggingFace 模型名称
        """
        self._model_name = model_name
        self._model = None
        self._dimension = None

    def _load_model(self):
        """延迟加载模型（首次使用时才加载）。"""
        if self._model is not None:
            return

        from sentence_transformers import SentenceTransformer
        print(f"[INFO] Loading model: {self._model_name} ...")
        self._model = SentenceTransformer(self._model_name)
        # 获取维度：编码一个空文本
        test_vec = self._model.encode(["test"])
        self._dimension = len(test_vec[0])
        print(f"[INFO] Model loaded. Dimension: {self._dimension}")

    @property
    def model_name(self) -> str:
        return self._model_name

    @property
    def dimension(self) -> int:
        self._load_model()
        return self._dimension

    def _encode_single(self, text: str) -> list[float]:
        self._load_model()
        # BGE 模型建议在查询时加前缀
        vector = self._model.encode([text], normalize_embeddings=True)
        return vector[0].tolist()


class OpenAIEmbeddingProvider(BaseEmbeddingProvider):
    """
    OpenAI Embedding API。

    优点：
        - 效果最好（多语言）
        - 无需本地计算

    缺点：
        - 需要 API Key
        - 按量计费
        - 需要网络

    适用：生产环境、高质量要求
    """

    def __init__(self, api_key: str | None = None, model: str = "text-embedding-3-small"):
        """
        Args:
            api_key: OpenAI API Key（默认从环境变量 OPENAI_API_KEY 读取）
            model:   模型名称
        """
        self._api_key = api_key or os.environ.get("OPENAI_API_KEY", "")
        self._model = model
        self._dimension = 1536  # text-embedding-3-small 的维度

    @property
    def model_name(self) -> str:
        return f"openai/{self._model}"

    @property
    def dimension(self) -> int:
        return self._dimension

    def _encode_single(self, text: str) -> list[float]:
        import httpx

        response = httpx.post(
            "https://api.openai.com/v1/embeddings",
            headers={
                "Authorization": f"Bearer {self._api_key}",
                "Content-Type": "application/json",
            },
            json={
                "input": text,
                "model": self._model,
            },
            timeout=30.0,
        )
        response.raise_for_status()
        data = response.json()
        return data["data"][0]["embedding"]


class SiliconFlowProvider(BaseEmbeddingProvider):
    """
    硅基流动 Embedding API（国内服务商）。

    优点：
        - 国内访问快
        - 支持中文 BGE-M3 模型
        - 价格便宜

    缺点：
        - 需要 API Key
        - 需要网络

    适用：国内生产环境
    """

    def __init__(self, api_key: str | None = None, model: str = "BAAI/bge-m3"):
        """
        Args:
            api_key: 硅基流动 API Key（默认从环境变量 SILICONFLOW_API_KEY 读取）
            model:   模型名称
        """
        self._api_key = api_key or os.environ.get("SILICONFLOW_API_KEY", "")
        self._model = model
        # BGE-M3 的维度是 1024
        self._dimension = 1024

    @property
    def model_name(self) -> str:
        return f"siliconflow/{self._model}"

    @property
    def dimension(self) -> int:
        return self._dimension

    def _encode_single(self, text: str) -> list[float]:
        import httpx

        response = httpx.post(
            "https://api.siliconflow.cn/v1/embeddings",
            headers={
                "Authorization": f"Bearer {self._api_key}",
                "Content-Type": "application/json",
            },
            json={
                "input": text,
                "model": self._model,
            },
            timeout=30.0,
        )
        response.raise_for_status()
        data = response.json()
        return data["data"][0]["embedding"]


# ============================================================
# 第四部分：相似度计算工具
# ============================================================

class SimilarityCalculator:
    """
    向量相似度计算工具。

    支持三种度量方式：
        1. 余弦相似度（Cosine）— 文本/语义最常用
        2. 欧氏距离（L2）— 图像/数值场景
        3. 点积（Dot Product）— ML 模型内积
    """

    @staticmethod
    def cosine_similarity(a: list[float], b: list[float]) -> float:
        """
        余弦相似度：衡量两个向量的方向相似性。

        范围：[-1, 1]
        - 1 = 完全相同方向（语义相同）
        - 0 = 无关
        - -1 = 完全相反方向（语义相反）

        为什么最常用？
            因为归一化后只看方向，不看大小。
            "我喜欢猫" 和 "猫我很喜欢" 方向相同，余弦相似度高。
        """
        a_np = np.array(a)
        b_np = np.array(b)
        return float(np.dot(a_np, b_np) / (np.linalg.norm(a_np) * np.linalg.norm(b_np)))

    @staticmethod
    def euclidean_distance(a: list[float], b: list[float]) -> float:
        """
        欧氏距离：两个向量在空间中的直线距离。

        范围：[0, +∞)
        - 0 = 完全相同
        - 越大 = 越不同

        注意：需要先归一化，否则受向量长度影响
        """
        a_np = np.array(a)
        b_np = np.array(b)
        return float(np.linalg.norm(a_np - b_np))

    @staticmethod
    def dot_product(a: list[float], b: list[float]) -> float:
        """
        点积：两个向量的内积。

        范围：(-∞, +∞)
        - 越大 = 越相似

        注意：受向量长度影响，未归一化时不能直接比较
        """
        return float(np.dot(np.array(a), np.array(b)))

    @staticmethod
    def normalize(vector: list[float]) -> list[float]:
        """
        L2 归一化：把向量缩放到单位长度（模为 1）。

        为什么要归一化？
            归一化后：
            - 点积 = 余弦相似度
            - 所有向量都在超球面上
            - 只看方向，不看大小
        """
        v = np.array(vector)
        norm = np.linalg.norm(v)
        if norm == 0:
            return vector
        return (v / norm).tolist()

    @staticmethod
    def similarity_matrix(
        vectors: list[list[float]],
        texts: list[str] | None = None,
    ) -> np.ndarray:
        """
        计算多条文本的相似度矩阵。

        Returns:
            shape=(n, n) 的相似度矩阵
        """
        n = len(vectors)
        matrix = np.zeros((n, n))
        for i in range(n):
            for j in range(n):
                matrix[i][j] = SimilarityCalculator.cosine_similarity(vectors[i], vectors[j])
        return matrix


# ============================================================
# 第五部分：工厂函数
# ============================================================

def get_embedding_provider(
    provider: str = "local_bge",
    **kwargs,
) -> BaseEmbeddingProvider:
    """
    根据名称获取 Embedding 提供者。

    Args:
        provider: "local_bge" | "openai" | "siliconflow"
    """
    providers = {
        "local_bge": LocalBGEProvider,
        "openai": OpenAIEmbeddingProvider,
        "siliconflow": SiliconFlowProvider,
    }

    if provider not in providers:
        raise ValueError(f"不支持的 provider: {provider}，可选: {list(providers.keys())}")

    return providers[provider](**kwargs)


# ============================================================
# 第六部分：测试与可视化
# ============================================================

def demo():
    """
    演示 Embedding + 相似度计算。
    """
    print("=" * 70)
    print("  Day 3 - Embedding 与向量化 测试")
    print("=" * 70)

    # 使用本地 BGE 模型
    emb = get_embedding_provider("local_bge")

    # 测试文本（围绕"智云科技"主题）
    sentences = [
        "智云音箱 Pro 搭载灵犀 AI 大模型",
        "智云安防摄像头支持 4K 超高清画质",
        "今天天气真好，适合出去散步",
        "灵犀大模型的意图识别准确率提升了 35%",
        "智云智能门锁支持指纹和密码解锁",
    ]

    # 1. 编码所有句子
    print("\n--- 1. 编码结果 ---")
    results = []
    for s in sentences:
        r = emb.encode_with_metadata(s)
        results.append(r)
        print(f"  {r}")

    # 2. 计算相似度矩阵
    print("\n--- 2. 相似度矩阵 ---")
    vectors = [r.vector for r in results]
    sim_matrix = SimilarityCalculator.similarity_matrix(vectors)

    # 打印矩阵（简化版）
    labels = ["音箱", "摄像头", "天气", "灵犀模型", "门锁"]
    header = f"{'':>8}" + "".join(f"{l:>8}" for l in labels)
    print(f"  {header}")
    for i, label in enumerate(labels):
        row = "".join(f"{sim_matrix[i][j]:>8.3f}" for j in range(len(labels)))
        print(f"  {label:>8}{row}")

    # 3. 找最相似的句子对
    print("\n--- 3. 最相似的句子对 ---")
    max_sim = -1
    max_i, max_j = 0, 0
    for i in range(len(sentences)):
        for j in range(i + 1, len(sentences)):
            sim = sim_matrix[i][j]
            if sim > max_sim:
                max_sim = sim
                max_i, max_j = i, j

    print(f"  最相似: [{labels[max_i]}] vs [{labels[max_j]}]")
    print(f"  相似度: {max_sim:.4f}")
    print(f"  句子1: {sentences[max_i]}")
    print(f"  句子2: {sentences[max_j]}")

    # 4. 归一化演示
    print("\n--- 4. 归一化演示 ---")
    raw_vec = results[0].vector
    norm_vec = SimilarityCalculator.normalize(raw_vec)
    print(f"  原始向量模长: {np.linalg.norm(raw_vec):.4f}")
    print(f"  归一化后模长: {np.linalg.norm(norm_vec):.4f}")
    print(f"  归一化后余弦 = 点积: {abs(SimilarityCalculator.cosine_similarity(norm_vec, norm_vec) - SimilarityCalculator.dot_product(norm_vec, norm_vec)) < 1e-6}")

    # 5. 用 Day 1 的文档测试
    print("\n--- 5. 实际文档 Embedding ---")
    import sys
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "day1"))
    from document_loader import DocumentLoader

    loader = DocumentLoader()
    doc = loader.load(os.path.join(os.path.dirname(__file__), "..", "data", "txt", "product_zy_sp100.txt"))

    # 取前几段做 embedding
    paragraphs = [p.strip() for p in doc.content.split("\n\n") if p.strip()][:5]
    doc_vectors = []
    for p in paragraphs:
        r = emb.encode_with_metadata(p)
        doc_vectors.append(r)
        print(f"  [{len(p):>4} chars] {p[:50]}...")

    # 文档内的相似度
    vecs = [d.vector for d in doc_vectors]
    doc_sim = SimilarityCalculator.similarity_matrix(vecs)
    print(f"\n  文档内段落相似度矩阵:")
    for i in range(min(5, len(paragraphs))):
        row = "".join(f"{doc_sim[i][j]:>6.3f}" for j in range(min(5, len(paragraphs))))
        print(f"    P{i}{row}")


if __name__ == "__main__":
    demo()
