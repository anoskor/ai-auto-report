"""Search API — RAG 混合检索（BM25 + kNN + RRF）。"""

from fastapi import APIRouter, Query
from app.rag.retriever import hybrid_search

router = APIRouter(prefix="/search", tags=["Search"])


@router.get("")
async def search(
    q: str = Query(..., min_length=1, description="检索关键词或问题"),
    top_k: int = Query(10, ge=1, le=50, description="返回条数"),
    rerank: bool = Query(True, description="是否启用 Rerank 精排"),
):
    """混合检索：关键词(BM25) + 语义(kNN) 双路召回，RRF 融合排序。"""
    result = await hybrid_search(q, top_k=top_k, use_rerank=rerank)
    return {"query": q, **result}
