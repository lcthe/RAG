"""
document_loader.py - RAG 文档加载与解析模块
============================================
Day 1 产出：支持 PDF、TXT、Markdown 三种格式的结构化文本加载器。

核心设计思路：
    1. 每种格式一个独立解析方法，职责清晰
    2. 统一输出 Document 数据类，方便下游 chunking / embedding 使用
    3. metadata 保留来源信息，支持后续溯源和调试

依赖：
    pip install pypdf markdown
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


# ============================================================
# 第一部分：数据结构定义
# ============================================================

@dataclass
class Document:
    """
    统一的文档数据结构，所有解析器的输出都转为这个格式。

    Attributes:
        content:     解析后的纯文本内容（已清洗，可直接用于 chunking）
        source:      原始文件路径，方便溯源
        doc_type:    文档类型标识（pdf / txt / md）
        metadata:    额外元数据（页码、标题、编码等），按需扩展
        pages:       仅 PDF 有值，按页拆分的内容列表，每页一个字符串
    """
    content: str
    source: str
    doc_type: str
    metadata: dict = field(default_factory=dict)
    pages: Optional[list[str]] = None

    def __repr__(self) -> str:
        preview = self.content[:80].replace("\n", " ")
        return (
            f"Document(type={self.doc_type}, source={self.source}, "
            f"length={len(self.content)}, preview='{preview}...')"
        )


# ============================================================
# 第二部分：DocumentLoader 主类
# ============================================================

class DocumentLoader:
    """
    统一文档加载器，根据文件后缀自动选择对应解析器。

    用法示例：
        loader = DocumentLoader()
        doc = loader.load("data/txt/product_zy_sp100.txt")
        print(doc.content[:200])

    支持格式：
        - .txt  -> 纯文本直接读取
        - .md   -> Markdown 转纯文本（去除格式标记）
        - .pdf  -> 使用 pypdf 提取文本，按页拆分
    """

    # 支持的文件后缀 -> 解析方法的映射表
    # 好处：新增格式只需加一行映射 + 一个方法，不用改 load() 的逻辑
    _PARSERS: dict[str, str] = {
        ".txt": "_load_txt",
        ".md":  "_load_markdown",
        ".pdf": "_load_pdf",
    }

    def load(self, file_path: str | Path) -> Document:
        """
        加载单个文件，自动识别格式并调用对应解析器。

        Args:
            file_path: 文件路径（字符串或 Path 对象）

        Returns:
            Document 对象，包含解析后的文本和元数据

        Raises:
            FileNotFoundError: 文件不存在
            ValueError: 不支持的文件格式
        """
        path = Path(file_path)

        # ---------- 校验文件是否存在 ----------
        if not path.exists():
            raise FileNotFoundError(f"文件不存在: {path}")

        # ---------- 识别文件后缀，选择解析器 ----------
        suffix = path.suffix.lower()  # 统一转小写，避免 .TXT 和 .txt 不一致

        if suffix not in self._PARSERS:
            supported = ", ".join(self._PARSERS.keys())
            raise ValueError(
                f"不支持的文件格式: {suffix}，目前仅支持: {supported}"
            )

        # 通过映射表拿到方法名，用 getattr 动态调用
        parser_method = getattr(self, self._PARSERS[suffix])
        document = parser_method(path)

        return document

    def load_batch(self, file_paths: list[str | Path]) -> list[Document]:
        """
        批量加载多个文件，跳过出错的文件并记录警告。

        Args:
            file_paths: 文件路径列表

        Returns:
            成功解析的 Document 列表（出错的文件会被跳过）
        """
        results = []
        for fp in file_paths:
            try:
                doc = self.load(fp)
                results.append(doc)
            except (FileNotFoundError, ValueError) as e:
                # 打印警告但不中断，保证批量加载的健壮性
                print(f"[WARNING] skip {fp}: {e}")
        return results

    def load_directory(
        self,
        dir_path: str | Path,
        recursive: bool = False,
    ) -> list[Document]:
        """
        加载目录下所有支持格式的文件。

        Args:
            dir_path:   目录路径
            recursive:  是否递归扫描子目录

        Returns:
            所有成功解析的 Document 列表
        """
        dir_path = Path(dir_path)
        if not dir_path.is_dir():
            raise NotADirectoryError(f"不是有效目录: {dir_path}")

        # glob 模式匹配所有支持的后缀
        patterns = [f"*{suffix}" for suffix in self._PARSERS]
        files = []
        for pattern in patterns:
            if recursive:
                files.extend(dir_path.rglob(pattern))  # 递归
            else:
                files.extend(dir_path.glob(pattern))   # 仅当前目录

        # 去重（理论上不会重复，但防御性编程）
        files = sorted(set(files))
        print(f"[INFO] found {len(files)} files in {dir_path}")

        return self.load_batch(files)

    # ============================================================
    # 第三部分：各格式解析器（私有方法）
    # ============================================================

    def _load_txt(self, path: Path) -> Document:
        """
        解析纯文本文件（.txt）。

        关键问题 - 编码：
            Windows 上很多 TXT 文件是 GBK/GB2312 编码，直接用 UTF-8 读会乱码。
            策略：先尝试 UTF-8，失败则回退到 GBK。
        """
        content, encoding = self._read_text_file(path)

        return Document(
            content=content,
            source=str(path),
            doc_type="txt",
            metadata={
                "encoding": encoding,
                "file_size_bytes": path.stat().st_size,
                "line_count": content.count("\n") + 1,
            },
        )

    def _load_markdown(self, path: Path) -> Document:
        """
        解析 Markdown 文件（.md）-> 转为纯文本。

        处理要点：
            1. 先读取原始 Markdown 文本
            2. 使用 markdown 库转为 HTML
            3. 再用正则去掉 HTML 标签，得到纯文本
            4. 保留标题层级信息到 metadata

        为什么不直接用原始文本？
            因为 Markdown 里的 #, **, ` 等标记对 LLM 是噪音，
            去掉后 embedding 质量更高。
        """
        raw_content, encoding = self._read_text_file(path)

        # ---------- 提取标题信息（在转 HTML 之前）----------
        # 用正则匹配所有 # 开头的标题行
        headings = re.findall(r"^(#{1,6})\s+(.+)$", raw_content, re.MULTILINE)
        heading_list = [{"level": len(h[0]), "text": h[1]} for h in headings]

        # ---------- Markdown -> HTML -> 纯文本 ----------
        import markdown as md_lib
        html = md_lib.markdown(raw_content)

        # 去除 HTML 标签，保留文本内容
        # 注意：这里用简单的正则，生产环境建议用 BeautifulSoup
        clean_text = re.sub(r"<[^>]+>", "", html)
        # 去除多余空行
        clean_text = re.sub(r"\n{3,}", "\n\n", clean_text).strip()

        return Document(
            content=clean_text,
            source=str(path),
            doc_type="md",
            metadata={
                "encoding": encoding,
                "file_size_bytes": path.stat().st_size,
                "headings": heading_list,       # 保留标题结构，后续可用于分段
                "heading_count": len(heading_list),
            },
        )

    def _load_pdf(self, path: Path) -> Document:
        """
        解析 PDF 文件（.pdf）。

        使用 pypdf 库逐页提取文本。

        PDF 解析的常见坑（面试常考）：
            1. 表格 -> 文本顺序可能错乱（pypdf 按流顺序提取，不感知布局）
            2. 页眉页脚 -> 每页重复出现，需要去重
            3. 多栏布局 -> 左栏和右栏的文本可能交叉
            4. 扫描版 PDF -> 纯图片，pypdf 提取不出文字（需要 OCR）
        """
        from pypdf import PdfReader

        reader = PdfReader(str(path))

        # ---------- 逐页提取文本 ----------
        pages = []
        for i, page in enumerate(reader.pages):
            page_text = page.extract_text() or ""  # 某些页面可能提取不出内容
            page_text = page_text.strip()
            if page_text:  # 跳过空白页
                pages.append(page_text)

        # ---------- 合并为全文 ----------
        full_content = "\n\n".join(pages)

        # ---------- 提取 PDF 元信息 ----------
        pdf_info = reader.metadata
        title = pdf_info.title if pdf_info and pdf_info.title else path.stem
        author = pdf_info.author if pdf_info and pdf_info.author else "unknown"

        return Document(
            content=full_content,
            source=str(path),
            doc_type="pdf",
            metadata={
                "title": title,
                "author": author,
                "page_count": len(reader.pages),      # 总页数
                "extracted_pages": len(pages),         # 成功提取的页数
                "file_size_bytes": path.stat().st_size,
            },
            pages=pages,  # 保留按页拆分的内容，方便后续按页检索
        )

    # ============================================================
    # 第四部分：工具方法
    # ============================================================

    @staticmethod
    def _read_text_file(path: Path) -> tuple[str, str]:
        """
        读取文本文件，自动处理编码问题。

        策略：
            1. 先尝试 UTF-8
            2. 失败则尝试 GBK（Windows 中文环境常见编码）
            3. 再失败则尝试 Latin-1（兜底，不会抛异常）

        Returns:
            (text, encoding_name) 元组
        """
        encodings = ["utf-8", "gbk", "latin-1"]
        for enc in encodings:
            try:
                text = path.read_text(encoding=enc)
                return text, enc
            except (UnicodeDecodeError, UnicodeError):
                continue

        # 理论上 latin-1 不会失败，但以防万一
        raise UnicodeDecodeError(
            encodings[-1], b"", 0, 1,
            f"无法以任何已知编码读取文件: {path}"
        )


# ============================================================
# 第五部分：命令行测试入口
# ============================================================

def main():
    """
    简单的命令行测试，验证三种格式的加载效果。
    运行方式：conda activate rag && python src/document_loader.py
    """
    loader = DocumentLoader()

    # 测试文件路径（相对于项目根目录）
    test_files = [
        "data/txt/product_zy_sp100.txt",
        "data/md/quick_start_guide.md",
        "data/pdf/product_launch_report_q1_2025.pdf",
    ]

    print("=" * 60)
    print("  DocumentLoader Test")
    print("=" * 60)

    for file_path in test_files:
        # 从 day1/ 目录运行时，需要向上找 data/
        full_path = os.path.join(os.path.dirname(__file__), "..", file_path)

        if not os.path.exists(full_path):
            print(f"\n[SKIP] file not found: {file_path}")
            continue

        print(f"\n{'─' * 60}")
        print(f"Load: {file_path}")

        doc = loader.load(full_path)

        # 打印文档概要
        print(f"  Type:     {doc.doc_type}")
        print(f"  Source:   {doc.source}")
        print(f"  Length:   {len(doc.content)} chars")
        print(f"  Metadata: {doc.metadata}")
        if doc.pages is not None:
            print(f"  Pages:    {len(doc.pages)}")
        print(f"\n  Preview (first 200 chars):")
        print(f"  {doc.content[:200]}")
        print(f"\n  repr: {doc}")

    # 测试批量加载整个 data 目录
    print(f"\n{'=' * 60}")
    print("Batch Load: data/")
    print(f"{'=' * 60}")

    data_dir = os.path.join(os.path.dirname(__file__), "..", "data")
    if os.path.exists(data_dir):
        docs = loader.load_directory(data_dir, recursive=True)
        print(f"\nTotal: {len(docs)} documents loaded")
        for d in docs:
            print(f"  [{d.doc_type:>3}] {d.source} ({len(d.content)} chars)")


if __name__ == "__main__":
    main()

