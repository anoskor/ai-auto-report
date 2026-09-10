"""RAG 混合检索模块 — BM25(关键词) + kNN(语义) 双路召回 + RRF 融合。

检索流程：
1. BM25：对 title/text/content 做 multi_match 关键词召回（精确关键词匹配）
2. kNN：对 embedding 字段做向量语义召回（同义/近义表达）
3. RRF：Reciprocal Rank Fusion 融合两路排名，无需手动调权

依赖：news_chunks 索引（由 app.rag.indexer 建立），ES 未连接时静默降级返回空。
"""

from app.generators.llm_client import embed, rerank
from app.rag.indexer import INDEX_NAME
from app.search.es_client import get_es_client

# RRF 平滑常数（标准值 60）：score = Σ 1/(k + rank)
RRF_K = 60


async def hybrid_search(
    query: str, top_k: int = 10, num_candidates: int = 50, use_rerank: bool = True
) -> dict:
    """混合检索主入口。

    返回 {"total": int, "hits": [{"chunk_id", "score", ...source字段}]}。
    BM25 或 kNN 任一失败时降级为单路召回，均失败时返回空。
    """
    es = get_es_client()
    if not es:
        return {"total": 0, "hits": []}

    query = (query or "").strip()
    if not query:
        return {"total": 0, "hits": []}

    recall_k = top_k * 2 if use_rerank else top_k

    # 1. BM25 关键词召回
    bm25_hits: list = []
    try:
        bm25 = await es.search(
            index=INDEX_NAME,
            size=recall_k,
            query={
                "multi_match": {
                    "query": query,
                    "fields": ["title^3", "text^2", "content"],
                }
            },
        )
        bm25_hits = bm25["hits"]["hits"]
    except Exception:
        bm25_hits = []

    # 2. kNN 语义召回
    knn_hits: list = []
    try:
        vecs = await embed([query])
        if vecs and vecs[0]:
            knn = await es.search(
                index=INDEX_NAME,
                size=recall_k,
                knn={
                    "field": "embedding",
                    "query_vector": vecs[0],
                    "k": recall_k,
                    "num_candidates": num_candidates,
                },
            )
            knn_hits = knn["hits"]["hits"]
    except Exception:
        knn_hits = []

    # 3. RRF 融合
    hits = _rrf_fusion(bm25_hits, knn_hits, recall_k)

    if use_rerank and hits:
        hits = await _rerank(query, hits, top_k)

    return {"total": len(hits), "hits": hits}


def _rrf_fusion(bm25_hits: list, knn_hits: list, top_k: int) -> list[dict]:
    """RRF 融合：每个文档最终得分 = Σ 1/(k + rank)。

    同时出现在两路的结果会获得更高分（关键词与语义双命中）。
    """
    scores: dict[str, float] = {}
    docs: dict[str, dict] = {}
    for lst in (bm25_hits, knn_hits):
        for rank, hit in enumerate(lst):
            doc_id = hit["_id"]
            scores[doc_id] = scores.get(doc_id, 0.0) + 1.0 / (RRF_K + rank + 1)
            docs[doc_id] = hit["_source"]

    ranked = sorted(scores.items(), key=lambda kv: -kv[1])[:top_k]
    return [
        {"chunk_id": doc_id, "score": round(score, 6), **docs[doc_id]}
        for doc_id, score in ranked
    ]


async def _rerank(query: str, hits: list[dict], top_k: int) -> list[dict]:
    """Re-rank RRF-fused hits via qwen3-rerank."""
    documents = [h.get("text") or h.get("content") or "" for h in hits]
    try:
        ranked = await rerank(query, documents, top_n=top_k)
    except Exception:
        return hits[:top_k]
    if not ranked:
        return hits[:top_k]
    order = {r["index"]: r["relevance_score"] for r in ranked}
    for i, h in enumerate(hits):
        if i in order:
            h["rerank_score"] = round(order[i], 6)
            h["score"] = round(order[i], 6)
    hits.sort(key=lambda h: h.get("rerank_score", -1.0), reverse=True)
    return hits[:top_k]
