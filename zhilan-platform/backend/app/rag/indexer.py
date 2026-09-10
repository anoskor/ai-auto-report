"""RAG 向量索引模块 — 将文章切 chunk + embedding 写入 ES dense_vector 索引。

依赖：
- ES 服务端 ≥ 8.x（dense_vector 支持 index:true 以启用 kNN 检索）
- 复用 app.search.es_client 的全局异步客户端（ES 未连接时静默降级，返回 0）
"""

from typing import Any

from app.config import settings
from app.generators.llm_client import embed
from app.rag.chunker import chunk_article
from app.search.es_client import get_es_client

INDEX_NAME = "news_chunks"
CHUNK_SIZE = 500
OVERLAP = 100


def _mapping() -> dict[str, Any]:
    """news_chunks 索引 mapping：embedding 为 dense_vector，启用余弦 kNN。"""
    return {
        "properties": {
            "chunk_id": {"type": "keyword"},
            "article_id": {"type": "long"},
            "title": {"type": "text"},
            "content": {"type": "text"},
            "text": {"type": "text"},
            "embedding": {
                "type": "dense_vector",
                "dims": settings.DASHSCOPE_EMBEDDING_DIMENSIONS,
                "index": True,
                "similarity": "cosine",
            },
            "source": {"type": "keyword"},
            "url": {"type": "keyword"},
            "published_at": {"type": "date"},
            "chunk_index": {"type": "integer"},
        }
    }


async def ensure_index() -> bool:
    """创建 news_chunks 索引（不存在时）。返回 ES 是否可用。"""
    es = get_es_client()
    if not es:
        return False
    exists = await es.indices.exists(index=INDEX_NAME)
    if not exists:
        await es.indices.create(index=INDEX_NAME, mappings=_mapping())
    return True


async def index_article(article) -> int:
    """索引单篇文章：切 chunk → 向量化 → bulk 写入。返回成功写入的 chunk 数。

    article 需具备 title/content/url/source/published_at 属性（ProcessedArticle 满足）。
    """
    es = get_es_client()
    if not es:
        return 0

    chunks = chunk_article(article.title, article.content, CHUNK_SIZE, OVERLAP)
    if not chunks:
        return 0

    vectors = await embed(chunks)
    if not vectors:
        return 0

    published = article.published_at.isoformat() if article.published_at else None
    actions: list[dict[str, Any]] = []
    for i, (chunk_text, vec) in enumerate(zip(chunks, vectors)):
        if not vec:
            continue
        chunk_id = f"{article.id}_{i}"
        actions.append({
            "_index": INDEX_NAME,
            "_id": chunk_id,
            "_source": {
                "chunk_id": chunk_id,
                "article_id": article.id,
                "title": article.title or "",
                "content": article.content or "",
                "text": chunk_text,
                "embedding": vec,
                "source": article.source or "",
                "url": article.url or "",
                "published_at": published,
                "chunk_index": i,
            },
        })

    if not actions:
        return 0

    from elasticsearch.helpers import async_bulk
    await async_bulk(es, actions)
    return len(actions)


async def delete_article(article_id: int) -> bool:
    """删除某篇文章的所有 chunk（文章删除或更新时调用）。"""
    es = get_es_client()
    if not es:
        return False
    await es.delete_by_query(
        index=INDEX_NAME,
        query={"term": {"article_id": article_id}},
    )
    return True


async def index_pending_articles() -> dict:
    """增量索引所有 unique 且未索引的文章（回填脚本与流水线共用）。

    返回 {"indexed": 文章数, "chunks": chunk 总数}。ES 未连接时静默降级返回 0。
    """
    if not await ensure_index():
        return {"indexed": 0, "chunks": 0}

    from sqlalchemy import select
    from app.database import async_session_factory
    from app.models.article import ProcessedArticle

    async with async_session_factory() as db:
        articles = (await db.execute(
            select(ProcessedArticle).where(
                ProcessedArticle.dedup_status == "unique",
                ProcessedArticle.indexed.is_(False),
            )
        )).scalars().all()

    total_chunks = 0
    indexed_ids: list[int] = []
    for a in articles:
        n = await index_article(a)
        if n > 0:
            total_chunks += n
            indexed_ids.append(a.id)

    if indexed_ids:
        async with async_session_factory() as db:
            arts = (await db.execute(
                select(ProcessedArticle).where(ProcessedArticle.id.in_(indexed_ids))
            )).scalars().all()
            for art in arts:
                art.indexed = True
            await db.commit()

    return {"indexed": len(indexed_ids), "chunks": total_chunks}
