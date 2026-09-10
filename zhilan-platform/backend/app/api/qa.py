"""QA API — RAG 检索问答。"""

from fastapi import APIRouter, Query
from app.rag.qa import generate_answer

router = APIRouter(prefix="/qa", tags=["QA"])


@router.get("")
async def qa(
    q: str = Query(..., min_length=1, description="问题"),
    top_k: int = Query(5, ge=1, le=10, description="检索片段数"),
    rerank: bool = Query(True, description="是否启用 Rerank 精排"),
):
    """混合检索 + LLM 生成带引用答案。"""
    result = await generate_answer(q, top_k=top_k, use_rerank=rerank)
    return {"query": q, **result}
