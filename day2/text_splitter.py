"""
text_splitter.py - RAG 文本分段模块
====================================
Day 2 产出：3 种文本分段器 + 对比测试

核心权衡：
    chunk 太大 → 检索不精确，找到的块包含太多无关信息
    chunk 太小 → 上下文丢失，LLM 缺乏足够信息生成答案

依赖：
    无额外依赖，纯 Python 实现
"""

from __future__ import annotations

import os
import re
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


# ============================================================
# 第一部分：Chunk 数据结构
# ============================================================

@dataclass
class Chunk:
    """
    分段后的文本块。

    Attributes:
        content:      文本内容
        metadata:     元数据（来源、序号、字符位置等）
        chunk_index:  在原文中的序号
    """
    content: str
    metadata: dict = field(default_factory=dict)
    chunk_index: int = 0

    def __repr__(self) -> str:
        preview = self.content[:50].replace("\n", " ")
        return f"Chunk(#{self.chunk_index}, {len(self.content)} chars, '{preview}...')"


# ============================================================
# 第二部分：基类
# ============================================================

class BaseSplitter(ABC):
    """
    文本分段器基类。

    所有分段器都实现 split_text() 方法：
        输入：长文本字符串
        输出：List[Chunk]
    """

    def __init__(self, chunk_size: int = 500, chunk_overlap: int = 100):
        """
        Args:
            chunk_size:     每个 chunk 的最大字符数
            chunk_overlap:  相邻 chunk 的重叠字符数（防止语义断裂）
        """
        if chunk_overlap >= chunk_size:
            raise ValueError(f"chunk_overlap ({chunk_overlap}) 必须小于 chunk_size ({chunk_size})")
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    @abstractmethod
    def split_text(self, text: str, metadata: dict | None = None) -> list[Chunk]:
        """将长文本切分为多个 Chunk。"""
        pass

    def split_documents(self, documents: list) -> list[Chunk]:
        """
        批量分段 Document 对象（兼容 Day 1 的 DocumentLoader 输出）。

        Args:
            documents: Document 列表（需要有 content 和 metadata 属性）
        """
        all_chunks = []
        for doc in documents:
            doc_meta = getattr(doc, "metadata", {}) or {}
            source = getattr(doc, "source", "unknown")
            doc_meta["source"] = source
            chunks = self.split_text(doc.content, metadata=doc_meta)
            all_chunks.extend(chunks)
        return all_chunks


# ============================================================
# 第三部分：3 种分段器实现
# ============================================================

class CharacterSplitter(BaseSplitter):
    """
    最基础的分段器：按固定字符数切分。

    策略：
        1. 每 chunk_size 个字符切一刀
        2. 相邻 chunk 重叠 chunk_overlap 个字符

    优点：简单、可预测
    缺点：可能在句子中间切断，语义不完整
    适用：快速原型、对质量要求不高的场景
    """

    def split_text(self, text: str, metadata: dict | None = None) -> list[Chunk]:
        metadata = metadata or {}
        chunks = []

        if not text or not text.strip():
            return chunks

        start = 0
        idx = 0
        while start < len(text):
            end = start + self.chunk_size
            chunk_text = text[start:end]

            if chunk_text.strip():  # 跳过空白 chunk
                chunks.append(Chunk(
                    content=chunk_text.strip(),
                    chunk_index=idx,
                    metadata={**metadata, "start_char": start, "end_char": end},
                ))
                idx += 1

            # 下一个 chunk 从 overlap 位置开始
            start += self.chunk_size - self.chunk_overlap

        return chunks


class RecursiveSplitter(BaseSplitter):
    """
    递归分段器：按分隔符优先级递归切分（LangChain/Dify 的核心算法）。

    策略：
        1. 按优先级尝试分隔符：\\n\\n > \\n > 。 > ！？ > . > 空格 > 空
        2. 如果切出来还是超长，递归用下一个分隔符继续切
        3. 最终合并成不超过 chunk_size 的块，保留 overlap

    优点：尽量在自然断点处分割，语义更完整
    缺点：比简单切分慢一点
    适用：通用场景，推荐默认使用
    """

    # 中文友好的分隔符优先级
    DEFAULT_SEPARATORS = [
        "\n\n",      # 段落分隔（最优）
        "\n",        # 换行
        "。",        # 中文句号
        "！",        # 中文感叹号
        "？",        # 中文问号
        ".",         # 英文句号
        "!",         # 英文感叹号
        "?",         # 英文问号
        "；",        # 中文分号
        ";",         # 英文分号
        "，",        # 中文逗号
        ",",         # 英文逗号
        " ",         # 空格
        "",          # 空字符串（最后手段，按字符切）
    ]

    def __init__(
        self,
        chunk_size: int = 500,
        chunk_overlap: int = 100,
        separators: list[str] | None = None,
    ):
        super().__init__(chunk_size, chunk_overlap)
        self.separators = separators or self.DEFAULT_SEPARATORS

    def split_text(self, text: str, metadata: dict | None = None) -> list[Chunk]:
        metadata = metadata or {}
        if not text or not text.strip():
            return []

        # 1. 先用递归算法切成小段
        raw_chunks = self._recursive_split(text, self.separators)

        # 2. 合并过小的块，同时添加 overlap
        merged = self._merge_chunks(raw_chunks)

        # 3. 包装成 Chunk 对象
        chunks = []
        current_pos = 0
        for idx, chunk_text in enumerate(merged):
            start = text.find(chunk_text[:20], current_pos)  # 粗略定位
            if start == -1:
                start = current_pos
            end = start + len(chunk_text)
            chunks.append(Chunk(
                content=chunk_text,
                chunk_index=idx,
                metadata={**metadata, "start_char": start, "end_char": end},
            ))
            current_pos = end - self.chunk_overlap  # 下一个从 overlap 位置开始

        return chunks

    def _recursive_split(self, text: str, separators: list[str]) -> list[str]:
        """递归切分核心算法。"""
        if len(text) <= self.chunk_size:
            return [text] if text.strip() else []

        # 找到最后一个出现的分隔符
        separator = ""
        for sep in separators:
            if sep in text:
                separator = sep
                break

        # 按找到的分隔符切分
        splits = text.split(separator) if separator else [text[i:i+1] for i in range(len(text))]

        # 递归处理每个子段
        result = []
        remaining_separators = separators[1:] if separators else [""]

        for split in splits:
            if len(split) <= self.chunk_size:
                if split.strip():
                    result.append(split)
            else:
                # 递归用下一个分隔符继续切
                result.extend(self._recursive_split(split, remaining_separators))

        return result

    def _merge_chunks(self, chunks: list[str]) -> list[str]:
        """合并过小的块，添加 overlap。"""
        if not chunks:
            return []

        merged = []
        current = chunks[0]

        for i in range(1, len(chunks)):
            next_chunk = chunks[i]
            combined = current + next_chunk

            if len(combined) <= self.chunk_size:
                current = combined
            else:
                merged.append(current.strip())
                # 从当前块末尾取 overlap
                overlap_text = current[-self.chunk_overlap:] if self.chunk_overlap > 0 else ""
                current = overlap_text + next_chunk

        if current.strip():
            merged.append(current.strip())

        return merged


class MarkdownSplitter(BaseSplitter):
    """
    Markdown 分段器：按标题层级切分。

    策略：
        1. 识别 Markdown 标题（#, ##, ### ...）
        2. 按标题将文档切成"标题+内容"的段落
        3. 如果某段落超长，递归按换行继续切

    优点：保留文档结构，每个 chunk 都有明确的上下文
    缺点：只适用于 Markdown 格式
    适用：技术文档、README、API 文档等结构化文本
    """

    # 匹配 Markdown 标题行
    HEADING_PATTERN = re.compile(r"^(#{1,6})\s+(.+)$", re.MULTILINE)

    def split_text(self, text: str, metadata: dict | None = None) -> list[Chunk]:
        metadata = metadata or {}
        if not text or not text.strip():
            return []

        # 1. 按标题切分
        sections = self._split_by_headings(text)

        # 2. 对超长段落进一步切分
        chunks = []
        idx = 0
        for section in sections:
            section_text = section["content"]
            heading = section.get("heading", "")

            if len(section_text) <= self.chunk_size:
                if section_text.strip():
                    chunks.append(Chunk(
                        content=section_text.strip(),
                        chunk_index=idx,
                        metadata={
                            **metadata,
                            "heading": heading,
                            "heading_level": section.get("level", 0),
                        },
                    ))
                    idx += 1
            else:
                # 超长段落，用递归方式继续切
                sub_chunks = self._split_long_section(section_text, heading, metadata)
                for sc in sub_chunks:
                    sc.chunk_index = idx
                    chunks.append(sc)
                    idx += 1

        return chunks

    def _split_by_headings(self, text: str) -> list[dict]:
        """按标题切分文档，返回 [{heading, level, content}, ...]"""
        headings = list(self.HEADING_PATTERN.finditer(text))

        if not headings:
            return [{"heading": "", "level": 0, "content": text}]

        sections = []

        # 标题前的内容（如果有）
        if headings[0].start() > 0:
            preamble = text[:headings[0].start()].strip()
            if preamble:
                sections.append({"heading": "", "level": 0, "content": preamble})

        # 每个标题到下一个标题之间的内容
        for i, match in enumerate(headings):
            level = len(match.group(1))  # # = 1, ## = 2, ...
            heading_text = match.group(2)

            # 内容范围：当前标题行结束 到 下一个标题行开始
            content_start = match.end()
            content_end = headings[i + 1].start() if i + 1 < len(headings) else len(text)
            content = text[content_start:content_end].strip()

            # 把标题本身也加到内容前面，让 chunk 有上下文
            full_content = f"{'#' * level} {heading_text}\n\n{content}" if content else f"{'#' * level} {heading_text}"
            sections.append({
                "heading": heading_text,
                "level": level,
                "content": full_content,
            })

        return sections

    def _split_long_section(self, text: str, heading: str, metadata: dict) -> list[Chunk]:
        """对超长段落按换行切分。"""
        chunks = []
        paragraphs = text.split("\n\n")

        current = ""
        for para in paragraphs:
            if len(current) + len(para) <= self.chunk_size:
                current += ("\n\n" if current else "") + para
            else:
                if current.strip():
                    chunks.append(Chunk(
                        content=current.strip(),
                        metadata={**metadata, "heading": heading},
                    ))
                # overlap：保留上一段的末尾
                overlap_text = current[-self.chunk_overlap:] if self.chunk_overlap > 0 else ""
                current = overlap_text + "\n\n" + para

        if current.strip():
            chunks.append(Chunk(
                content=current.strip(),
                metadata={**metadata, "heading": heading},
            ))

        return chunks


# ============================================================
# 第四部分：工厂函数（方便使用）
# ============================================================

def get_splitter(
    strategy: str = "recursive",
    chunk_size: int = 500,
    chunk_overlap: int = 100,
    **kwargs,
) -> BaseSplitter:
    """
    根据策略名称获取分段器实例。

    Args:
        strategy:     "character" | "recursive" | "markdown"
        chunk_size:   chunk 最大字符数
        chunk_overlap: 重叠字符数
    """
    splitters = {
        "character": CharacterSplitter,
        "recursive": RecursiveSplitter,
        "markdown": MarkdownSplitter,
    }

    if strategy not in splitters:
        raise ValueError(f"不支持的策略: {strategy}，可选: {list(splitters.keys())}")

    return splitters[strategy](chunk_size=chunk_size, chunk_overlap=chunk_overlap, **kwargs)


# ============================================================
# 第五部分：对比测试
# ============================================================

def demo():
    """
    用同一份文档对比三种分段策略的效果。
    """
    # 加载 Day 1 的 DocumentLoader
    import sys
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "day1"))
    from document_loader import DocumentLoader

    loader = DocumentLoader()
    doc = loader.load(os.path.join(os.path.dirname(__file__), "..", "data", "md", "quick_start_guide.md"))

    print("=" * 70)
    print("  Day 2 - Text Splitter 对比测试")
    print("=" * 70)
    print(f"\n  原文长度: {len(doc.content)} 字符")
    print(f"  原文预览: {doc.content[:100]}...")
    print()

    # 三种策略对比
    strategies = ["character", "recursive", "markdown"]
    metadata = {"source": doc.source, "doc_type": doc.doc_type}

    for strategy in strategies:
        splitter = get_splitter(strategy, chunk_size=300, chunk_overlap=50)
        chunks = splitter.split_text(doc.content, metadata=metadata)

        print(f"{'─' * 70}")
        print(f"  策略: {strategy.upper()}")
        print(f"  chunk_size=300, chunk_overlap=50")
        print(f"  切分结果: {len(chunks)} 个 chunks")
        print()

        for i, chunk in enumerate(chunks[:3]):  # 只显示前3个
            preview = chunk.content[:80].replace("\n", " ")
            print(f"    Chunk #{i} ({len(chunk.content)} chars): {preview}...")

        if len(chunks) > 3:
            print(f"    ... 还有 {len(chunks) - 3} 个 chunks")

        # 统计信息
        sizes = [len(c.content) for c in chunks]
        print(f"\n    统计: 最小={min(sizes)}, 最大={max(sizes)}, 平均={sum(sizes)//len(sizes)}")
        print()

    # 用不同 chunk_size 测试 RecursiveSplitter
    print(f"{'═' * 70}")
    print(f"  RecursiveSplitter - 不同 chunk_size 对比")
    print(f"{'═' * 70}")

    for size in [200, 500, 1000]:
        splitter = get_splitter("recursive", chunk_size=size, chunk_overlap=50)
        chunks = splitter.split_text(doc.content, metadata=metadata)
        sizes = [len(c.content) for c in chunks]
        print(f"\n  chunk_size={size}: {len(chunks)} chunks, 平均 {sum(sizes)//len(sizes)} chars")


if __name__ == "__main__":
    demo()
