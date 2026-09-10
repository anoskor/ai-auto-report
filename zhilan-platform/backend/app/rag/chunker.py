"""RAG 文档切分模块 — 按字符滑动窗口切分，标题作为每个 chunk 的前缀。

设计说明：
- 中文文本按「字符」切分更直观，chunk_size 默认 500 字符（约等于 500 汉字），
  overlap 默认 100 字符，保证跨 chunk 的上下文连贯。
- 每个 chunk 都携带文章标题作为前缀，检索命中时自带语义上下文，
  也便于 embedding 时融合标题与正文信息。
"""

from typing import Optional


def _sliding_window(text: str, chunk_size: int, overlap: int) -> list[str]:
    """按字符滑动窗口切分长文本，返回切分片段列表。"""
    text = text.strip()
    if not text:
        return []
    if len(text) <= chunk_size:
        return [text]

    chunks: list[str] = []
    start = 0
    n = len(text)
    while start < n:
        end = min(start + chunk_size, n)
        chunks.append(text[start:end])
        if end >= n:
            break
        start = end - overlap
    return chunks


def chunk_article(
    title: str,
    content: str,
    chunk_size: int = 500,
    overlap: int = 100,
) -> list[str]:
    """将一篇文章切分为带标题前缀的 chunk 列表。

    返回 list[str]，每个元素形如 "标题\\n正文片段"。
    空内容时若标题非空则返回 [标题]，否则返回 []。
    """
    title = (title or "").strip()
    body = (content or "").strip()

    snippets = _sliding_window(body, chunk_size, overlap)
    if not snippets:
        return [title] if title else []

    prefix = f"{title}\n" if title else ""
    return [prefix + s for s in snippets]


def chunk_count(title: Optional[str], content: Optional[str], chunk_size: int = 500, overlap: int = 100) -> int:
    """预估切分后的 chunk 数量（供索引前判断是否需要切分）。"""
    body = (content or "").strip()
    if not body:
        return 1 if (title or "").strip() else 0
    if len(body) <= chunk_size:
        return 1
    # 首个 chunk 覆盖 chunk_size 字符，之后每个 chunk 新增 (chunk_size - overlap) 字符
    return 1 + (len(body) - overlap - 1) // (chunk_size - overlap)
