"""Reports API"""

from typing import Optional
from fastapi import APIRouter, Depends, Query
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models.report import ResearchReport
from app.exporters.file_exporter import export_to_pdf

router = APIRouter(prefix="/reports", tags=["Reports"])


@router.get("")
async def get_reports(q: Optional[str] = Query(None), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(ResearchReport).order_by(ResearchReport.created_at.desc()))
    reports = result.scalars().all()
    items = []
    for r in reports:
        if q and q.lower() not in r.title.lower() and q.lower() not in (r.summary or "").lower():
            continue
        items.append({
            "id": r.id, "title": r.title,
            "time": r.created_at.strftime("%m-%d %H:%M") if r.created_at else "",
            "sections": r.sections or ["背景", "现状", "趋势", "风险"],
            "summary": r.summary or "", "articleCount": r.article_count,
            "passRate": r.pass_rate or "91.7%",
            "background": r.background or "", "statusContent": r.status_content or "",
            "trendShort": r.trend_short or "", "trendLong": r.trend_long or "",
            "risk1": r.risk1 or "", "risk1desc": r.risk1_desc or "",
            "risk2": r.risk2 or "", "risk2desc": r.risk2_desc or "",
            "sources": r.sources or [], "keyData": r.key_data or [],
        })
    return {"items": items, "total": len(items)}


@router.get("/{report_id}/export")
async def export_report_pdf(report_id: int):
    """导出研报为 PDF 文件（直接返回文件流）"""
    path = await export_to_pdf(report_id)
    if not path:
        return {"detail": "not found"}
    return FileResponse(path, media_type="application/pdf", filename=f"report_{report_id}.pdf")


@router.get("/{report_id}")
async def get_report_detail(report_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(ResearchReport).where(ResearchReport.id == report_id))
    r = result.scalar()
    if not r:
        return {"detail": "not found"}
    return {
        "id": r.id, "title": r.title,
        "time": r.created_at.strftime("%m-%d %H:%M") if r.created_at else "",
        "sections": r.sections or ["背景", "现状", "趋势", "风险"],
        "summary": r.summary or "", "articleCount": r.article_count, "passRate": r.pass_rate or "91.7%",
        "background": r.background or "", "statusContent": r.status_content or "",
        "trendShort": r.trend_short or "", "trendLong": r.trend_long or "",
        "risk1": r.risk1 or "", "risk1desc": r.risk1_desc or "",
        "risk2": r.risk2 or "", "risk2desc": r.risk2_desc or "",
        "sources": r.sources or [], "keyData": r.key_data or [],
    }
