"""RAG 索引重建脚本 — 更细切分重建索引，扩充 chunk 数量。

用法：
  python rebuild_index.py stats    # 查看文章长度分布 + 预估 chunk 数
  python rebuild_index.py rebuild  # 删旧索引 + 更细切分重建
"""

import asyncio
import os
import sys

os.chdir(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import select  # noqa: E402

from app.database import async_session_factory  # noqa: E402
from app.generators.llm_client import embed  # noqa: E402
from app.models.article import ProcessedArticle  # noqa: E402
from app.rag.chunker import chunk_article  # noqa: E402
from app.rag.indexer import INDEX_NAME, ensure_index  # noqa: E402
from app.search.es_client import get_es_client, init_es  # noqa: E402

NEW_CHUNK_SIZE = 200
NEW_OVERLAP = 50


async def _unique_articles() -> list[ProcessedArticle]:
    async with async_session_factory() as db:
        return (await db.execute(
            select(ProcessedArticle).where(ProcessedArticle.dedup_status == "unique")
        )).scalars().all()


async def stats():
    arts = await _unique_articles()
    lens = [len(a.content or "") for a in arts]
    n = len(arts)

    def est_chunks(length, size, overlap):
        if length <= size:
            return 1
        return 1 + (length - overlap - 1) // (size - overlap)

    for size, overlap in ((500, 100), (200, 50), (150, 40)):
        total = sum(est_chunks(L, size, overlap) for L in lens)
        print(f"CHUNK_SIZE={size} OVERLAP={overlap} -> est chunks: {total}")

    print("total unique:", n)
    print("avg len:", sum(lens) // max(n, 1))
    print("len<=100:", sum(1 for L in lens if L <= 100))
    print("100<len<=200:", sum(1 for L in lens if 100 < L <= 200))
    print("200<len<=400:", sum(1 for L in lens if 200 < L <= 400))
    print("400<len<=800:", sum(1 for L in lens if 400 < L <= 800))
    print("len>800:", sum(1 for L in lens if L > 800))


async def rebuild():
    es = get_es_client()
    if await es.indices.exists(index=INDEX_NAME):
        await es.indices.delete(index=INDEX_NAME)
        print("deleted old index")
    await ensure_index()

    from elasticsearch.helpers import async_bulk

    arts = await _unique_articles()
    total_chunks = 0
    for a in arts:
        chunks = chunk_article(a.title, a.content, NEW_CHUNK_SIZE, NEW_OVERLAP)
        vectors = await embed(chunks)
        actions = []
        for i, (c, v) in enumerate(zip(chunks, vectors)):
            if not v:
                continue
            cid = f"{a.id}_{i}"
            actions.append({
                "_index": INDEX_NAME,
                "_id": cid,
                "_source": {
                    "chunk_id": cid,
                    "article_id": a.id,
                    "title": a.title or "",
                    "content": a.content or "",
                    "text": c,
                    "embedding": v,
                    "source": a.source or "",
                    "url": a.url or "",
                    "published_at": a.published_at.isoformat() if a.published_at else None,
                    "chunk_index": i,
                },
            })
        if actions:
            await async_bulk(es, actions)
            total_chunks += len(actions)
    print("rebuilt chunks:", total_chunks)


async def main():
    await init_es()
    mode = sys.argv[1] if len(sys.argv) > 1 else "stats"
    if mode == "stats":
        await stats()
    elif mode == "rebuild":
        await rebuild()
    else:
        print("unknown mode, use: stats | rebuild")


if __name__ == "__main__":
    asyncio.run(main())
