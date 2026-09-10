"""Clusters API"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models.cluster import NewsCluster
from app.schemas.all import ClusterGraphOut, ClusterNodeOut, ClusterLinkOut

router = APIRouter(prefix="/clusters", tags=["Clusters"])


@router.get("")
async def get_clusters(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(NewsCluster).order_by(NewsCluster.importance_score.desc()))
    clusters = result.scalars().all()
    return {
        "items": [
            {
                "id": c.id, "title": c.topic_label, "articleCount": c.article_count,
                "timeSpan": c.time_span or "3天", "rating": c.rating,
                "importanceScore": c.importance_score or 0,
                "keywords": c.keywords or [], "timeline": c.timeline or [],
                "articles": c.articles or [],
            } for c in clusters
        ],
        "total": len(clusters),
    }


@router.get("/graph", response_model=ClusterGraphOut)
async def get_cluster_graph(topic: str = None, db: AsyncSession = Depends(get_db)):
    """从真实聚类数据构建关系图：聚类主题为中心节点，关键词为子节点。
    默认返回重要性最高的 top 60 个簇（避免节点过多导致渲染卡死）；
    传入 topic 时返回该主题的单个子图。"""
    stmt = select(NewsCluster).order_by(NewsCluster.importance_score.desc())
    if topic:
        stmt = stmt.where(NewsCluster.topic_label == topic)
    else:
        stmt = stmt.limit(60)
    result = await db.execute(stmt)
    clusters = result.scalars().all()

    category_colors = [
        "oklch(0.52 0.18 230)",
        "oklch(0.52 0.17 160)",
        "oklch(0.65 0.18 80)",
        "oklch(0.55 0.20 30)",
        "oklch(0.60 0.16 300)",
    ]

    nodes: list[ClusterNodeOut] = []
    links: list[ClusterLinkOut] = []
    seen_ids: set[str] = set()

    for ci, c in enumerate(clusters):
        center_id = c.topic_label
        color = category_colors[ci % len(category_colors)]
        if center_id not in seen_ids:
            nodes.append(ClusterNodeOut(
                id=center_id, name=center_id, symbolSize=40, category=ci % 3,
                itemStyle={"color": color},
            ))
            seen_ids.add(center_id)
        for kw in (c.keywords or [])[:6]:
            if not kw:
                continue
            if kw not in seen_ids:
                nodes.append(ClusterNodeOut(id=kw, name=kw, symbolSize=24, category=ci % 3))
                seen_ids.add(kw)
            links.append(ClusterLinkOut(source=center_id, target=kw))

    return ClusterGraphOut(nodes=nodes, links=links)


@router.get("/{cluster_id}")
async def get_cluster_detail(cluster_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(NewsCluster).where(NewsCluster.id == cluster_id))
    c = result.scalar()
    if not c:
        return {"detail": "not found"}
    return {
        "id": c.id, "title": c.topic_label, "articleCount": c.article_count,
        "timeSpan": c.time_span or "3天", "rating": c.rating,
        "importanceScore": c.importance_score or 0,
        "keywords": c.keywords or [], "timeline": c.timeline or [],
        "articles": c.articles or [],
    }
