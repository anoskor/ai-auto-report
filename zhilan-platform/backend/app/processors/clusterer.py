"""文本聚类模块 — embedding 向量 + DBSCAN 聚类 + jieba 关键词提取"""

import math
from collections import defaultdict
from datetime import datetime

import numpy as np
from sqlalchemy import select

from app.database import async_session_factory
from app.models.article import ProcessedArticle
from app.models.cluster import NewsCluster


def _is_valid_vector(v) -> bool:
    """判断是否为有效向量（非空、非 NaN）"""
    if not v or not isinstance(v, (list, tuple)):
        return False
    try:
        return all(not (isinstance(x, float) and math.isnan(x)) for x in v)
    except TypeError:
        return False


def _extract_keywords(text: str, topk: int = 6) -> list[str]:
    """用 jieba 提取关键词"""
    try:
        import jieba.analyse
        return jieba.analyse.extract_tags(text, topK=topk) or []
    except Exception:
        return []


def _cluster(vectors: list[list[float]]) -> list[int]:
    """DBSCAN 余弦距离聚类，返回每个样本的簇标签（噪声点各自成簇）"""
    from sklearn.cluster import DBSCAN
    n = len(vectors)
    if n <= 1:
        return [0] * n

    arr = np.array(vectors, dtype=np.float64)
    eps = 0.35 if n <= 50 else 0.30
    min_samples = 1 if n <= 5 else 2
    model = DBSCAN(metric="cosine", eps=eps, min_samples=min_samples)
    labels = model.fit_predict(arr)

    # 噪声点（-1）各自独立成簇
    next_label = int(max(labels)) + 1 if len(labels) else 0
    result = []
    for lab in labels:
        if lab == -1:
            result.append(next_label)
            next_label += 1
        else:
            result.append(int(lab))
    return result


async def cluster_articles(article_ids: list[int] = None) -> dict:
    """对去重后的文章做向量聚类，写入 news_clusters。"""
    async with async_session_factory() as db:
        stmt = select(ProcessedArticle).where(
            ProcessedArticle.dedup_status == "unique",
            ProcessedArticle.cluster_id.is_(None),
            ProcessedArticle.embedding.isnot(None),
        ).order_by(ProcessedArticle.id)
        if article_ids:
            stmt = stmt.where(ProcessedArticle.id.in_(article_ids))
        result = await db.execute(stmt)
        valid = [a for a in result.scalars().all() if _is_valid_vector(a.embedding)]
        if not valid:
            return {"clusters": 0, "noise_count": 0, "clusters_detail": []}

        labels = _cluster([a.embedding for a in valid])

        groups: dict[int, list] = defaultdict(list)
        for art, lab in zip(valid, labels):
            groups[lab].append(art)

        clusters_detail = []
        created = 0
        for lab, arts in groups.items():
            arts = sorted(arts, key=lambda x: (x.published_at or datetime.min), reverse=True)
            rep = arts[0]

            combined_text = " ".join(
                (a.title or "") + " " + (a.content or "")[:200] for a in arts
            )
            keywords = _extract_keywords(combined_text, topk=6)
            if not keywords:
                keywords = (rep.title or "").split()[:4]

            # 时间跨度
            times = [a.published_at for a in arts if a.published_at]
            if times:
                span_days = max(1, (max(times) - min(times)).days + 1)
                time_span = f"{span_days}天"
            else:
                time_span = "1天"

            # 时间线（真实文章按时间排序）
            timeline = [
                {
                    "time": a.published_at.strftime("%m-%d %H:%M") if a.published_at else "",
                    "title": (a.title or "")[:60],
                    "description": (a.content or "")[:80],
                }
                for a in arts[:8]
            ]

            cluster = NewsCluster(
                topic_label=(rep.title or "未命名主题")[:200],
                article_count=len(arts),
                time_span=time_span,
                importance_score=round(min(0.99, 0.5 + 0.05 * len(arts)), 2),
                rating=5 if len(arts) >= 5 else (4 if len(arts) >= 3 else 3),
                keywords=keywords,
                representative_article_id=rep.id,
                timeline=timeline,
                articles=[
                    {
                        "title": a.title or "",
                        "source": a.source or "",
                        "date": a.published_at.strftime("%Y-%m-%d") if a.published_at else "",
                    }
                    for a in arts[:10]
                ],
                created_at=datetime.now(),
            )
            db.add(cluster)
            await db.flush()
            for a in arts:
                a.cluster_id = cluster.id
            created += 1
            clusters_detail.append({
                "cluster_id": cluster.id,
                "topic_label": cluster.topic_label,
                "article_count": len(arts),
                "keywords": keywords,
            })

        await db.commit()
        return {"clusters": created, "noise_count": 0, "clusters_detail": clusters_detail}
