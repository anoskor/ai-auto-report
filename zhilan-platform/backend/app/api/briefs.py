"""Briefs API"""

from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models.brief import DailyBrief
from app.models.report import ResearchReport
from app.models.cluster import NewsCluster
from app.schemas.all import BriefItemOut, IndustryItemOut, SentimentDataOut, SentimentTrendOut, ReportRef

router = APIRouter(prefix="/briefs", tags=["Briefs"])

_WEEK_LABELS = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]


@router.get("")
async def get_briefs(date: Optional[str] = Query(None), db: AsyncSession = Depends(get_db)):
    stmt = select(DailyBrief).order_by(DailyBrief.rating.desc())
    if date:
        stmt = stmt.where(DailyBrief.brief_date == date)
    result = await db.execute(stmt)
    briefs = result.scalars().all()

    # 查询最近研报作为"深度研报"卡片
    report_result = await db.execute(select(ResearchReport).order_by(ResearchReport.created_at.desc()).limit(2))
    reports = report_result.scalars().all()
    report_cards = [
        {
            "id": r.id, "title": r.title, "sections": r.sections or ["背景", "现状", "趋势", "风险"],
            "summary": (r.summary or "")[:80], "source": f"{r.article_count}篇文章",
            "time": "今天", "passRate": r.pass_rate or "91.7%",
        } for r in reports
    ]

    # 行业主题：从真实聚类数据聚合（每个聚类一个行业主题，关键词作为标签）
    cluster_result = await db.execute(select(NewsCluster).order_by(NewsCluster.importance_score.desc()).limit(6))
    clusters = cluster_result.scalars().all()
    industries = [
        {"name": c.topic_label, "tags": (c.keywords or [])[:4]} for c in clusters
    ]

    # 情绪/热度/波动：取最新一条简报的真实字段
    latest_brief = (await db.execute(
        select(DailyBrief).order_by(DailyBrief.created_at.desc(), DailyBrief.id.desc()).limit(1)
    )).scalar()
    if latest_brief:
        sentiment = {"sentiment": latest_brief.sentiment, "heat": latest_brief.heat, "volatility": latest_brief.volatility}
        trend_data = {
            "labels": _WEEK_LABELS,
            "sentiment": latest_brief.sentiment_trend or [],
            "heat": latest_brief.heat_trend or [],
            "volatility": latest_brief.volatility_trend or [],
        }
    else:
        sentiment = {"sentiment": 0, "heat": 0, "volatility": 0}
        trend_data = {"labels": _WEEK_LABELS, "sentiment": [], "heat": [], "volatility": []}

    return {
        "briefs": [
            {
                "id": b.id, "title": b.title, "summary": b.summary, "time": b.time,
                "category": b.category, "rating": b.rating, "articleCount": b.article_count,
                "content": b.content, "relatedArticleCount": b.related_article_count,
                "relatedReportCount": b.related_report_count,
                "relatedReports": b.related_reports or [],
            } for b in briefs
        ],
        "reportCards": report_cards,
        "industries": industries,
        "sentiment": sentiment,
        "trendData": trend_data,
    }


@router.get("/{brief_id}")
async def get_brief_detail(brief_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(DailyBrief).where(DailyBrief.id == brief_id))
    b = result.scalar()
    if not b:
        return {"detail": "not found"}
    return {
        "id": b.id, "title": b.title, "summary": b.summary, "time": b.time,
        "category": b.category, "rating": b.rating, "articleCount": b.article_count,
        "content": b.content, "relatedArticleCount": b.related_article_count,
        "relatedReportCount": b.related_report_count,
        "relatedReports": b.related_reports or [],
    }
