"""文本去重模块 — URL hash 精确去重 + embedding 余弦相似度近似去重"""

from sqlalchemy import select
from app.database import async_session_factory
from app.models.article import RawArticle, ProcessedArticle
from app.generators.llm_client import embed, cosine_sim


async def deduplicate_articles(article_ids: list[int] = None, threshold: float = 0.85) -> dict:
    """对未处理的原始文章做去重，写入 processed_articles。

    1. 精确去重：爬虫阶段已通过 url_hash 保证同 URL 不重复入库；
    2. 近似去重：标题+正文 embedding 余弦相似度 > threshold 判为重复。

    返回 {"total": n, "unique": m, "duplicates": k}
    """
    async with async_session_factory() as db:
        stmt = select(RawArticle).order_by(RawArticle.published_at.desc(), RawArticle.id.desc())
        if article_ids:
            stmt = stmt.where(RawArticle.id.in_(article_ids))
        else:
            stmt = stmt.where(RawArticle.is_processed.is_(False))
        result = await db.execute(stmt)
        articles = result.scalars().all()
        if not articles:
            return {"total": 0, "unique": 0, "duplicates": 0}

        # 向量化：标题 + 正文前 500 字
        texts = [(a.title or "") + " " + (a.content or "")[:500] for a in articles]
        try:
            vectors = await embed(texts)
        except Exception as e:
            print(f"[Dedup] embedding 失败: {e}")
            vectors = []

        # 历史已保留文章的向量参与跨批次去重
        existing_result = await db.execute(select(ProcessedArticle).where(ProcessedArticle.dedup_status == "unique"))
        kept_vectors = [e.embedding for e in existing_result.scalars().all() if e.embedding]

        total = 0
        unique_count = 0
        duplicate_count = 0

        for i, art in enumerate(articles):
            vec = vectors[i] if i < len(vectors) else None
            is_dup = False
            if vec is not None:
                for kv in kept_vectors:
                    if cosine_sim(vec, kv) > threshold:
                        is_dup = True
                        break

            status = "duplicate" if is_dup else "unique"
            db.add(ProcessedArticle(
                raw_article_id=art.id,
                title=art.title,
                content=art.content,
                source=art.source,
                url=art.url,
                published_at=art.published_at,
                language=art.language or "zh",
                embedding=vec,
                dedup_status=status,
                cluster_id=None,
            ))
            art.is_processed = True

            if is_dup:
                duplicate_count += 1
            else:
                unique_count += 1
                if vec is not None:
                    kept_vectors.append(vec)
            total += 1

        await db.commit()
        return {"total": total, "unique": unique_count, "duplicates": duplicate_count}
