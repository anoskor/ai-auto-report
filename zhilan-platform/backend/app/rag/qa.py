"""RAG QA 生成模块 — 混合检索 + LLM 生成带引用答案。"""

from app.generators.llm_client import chat
from app.rag.retriever import hybrid_search


async def generate_answer(query: str, top_k: int = 5, use_rerank: bool = True) -> dict:
    """检索相关新闻片段并生成带引用的答案。

    返回 {"answer": str, "sources": [来源片段]}。
    检索无结果时 answer 为提示语；LLM 未配置或失败时 answer 为 None（sources 仍返回）。
    """
    result = await hybrid_search(query, top_k=top_k, use_rerank=use_rerank)
    hits = result.get("hits", [])
    if not hits:
        return {"answer": "未找到相关信息，请尝试更换关键词或问题表述。", "sources": []}

    # 拼接带编号的上下文（[1]~[n]），供模型引用
    parts = []
    for i, h in enumerate(hits, 1):
        title = (h.get("title") or "").strip()
        text = (h.get("text") or h.get("content") or "").strip()
        parts.append(f"[{i}] {title}\n{text}")
    context = "\n\n".join(parts)

    system = (
        "你是智览平台的新闻信息助手。请严格依据下方提供的新闻片段回答用户问题，"
        "不得编造片段之外的信息。引用某一片段时，请在句末用 [编号] 标注来源；"
        "若片段不足以回答问题，请明确说明信息不足。回答使用简体中文，简洁准确。"
    )
    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": f"新闻片段：\n{context}\n\n用户问题：{query}"},
    ]

    answer = await chat(messages, temperature=0.3)

    sources = [
        {
            "chunk_id": h.get("chunk_id"),
            "title": h.get("title") or "",
            "url": h.get("url") or "",
            "source": h.get("source") or "",
            "published_at": h.get("published_at"),
            "text": (h.get("text") or h.get("content") or "")[:300],
            "score": h.get("score"),
        }
        for h in hits
    ]

    return {"answer": answer, "sources": sources}
