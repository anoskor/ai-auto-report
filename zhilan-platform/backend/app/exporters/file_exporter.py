"""文件导出模块 — Markdown 真实导出（按研报字段渲染）"""

import os

from sqlalchemy import select

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_CENTER
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont

from app.config import settings
from app.database import async_session_factory
from app.models.report import ResearchReport

_CJK_FONT = "STSong-Light"


def _register_cjk_font():
    """注册内置 CID 中文字体（无需外部字体文件）"""
    try:
        pdfmetrics.registerFont(UnicodeCIDFont(_CJK_FONT))
    except Exception:
        pass


def _escape(text) -> str:
    """转义 HTML 特殊字符，避免 Paragraph 解析报错"""
    return (text or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


async def _get_report(report_id: int):
    async with async_session_factory() as db:
        result = await db.execute(select(ResearchReport).where(ResearchReport.id == report_id))
        return result.scalar()


async def export_to_markdown(report_id: int) -> str:
    """按研报字段真实渲染 Markdown 并写入 EXPORT_DIR，返回文件路径"""
    report = await _get_report(report_id)
    if not report:
        return ""

    lines = [
        f"# {report.title or f'Report #{report_id}'}",
        "",
        f"> {report.summary or ''}",
        "",
        "## 背景",
        report.background or "",
        "",
        "## 现状",
        report.status_content or "",
        "",
        "## 趋势",
        f"**短期**：{report.trend_short or ''}",
        "",
        f"**中长期**：{report.trend_long or ''}",
        "",
        "## 风险",
        f"### {report.risk1 or '风险1'}",
        report.risk1_desc or "",
        "",
        f"### {report.risk2 or '风险2'}",
        report.risk2_desc or "",
        "",
        "## 关键数据",
    ]
    for kd in report.key_data or []:
        lines.append(f"- {kd.get('label', '')}: {kd.get('value', '')}（{kd.get('change', '')}）")
    lines.append("")
    lines.append("## 来源")
    for s in report.sources or []:
        if isinstance(s, dict):
            title = s.get("title") or s.get("source") or ""
            url = s.get("url") or ""
            lines.append(f"- {title}" + (f"（{url}）" if url else ""))
        else:
            lines.append(f"- {s}")
    content = "\n".join(lines)

    os.makedirs(settings.EXPORT_DIR, exist_ok=True)
    path = os.path.join(settings.EXPORT_DIR, f"report_{report_id}.md")
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    return path


async def export_to_pdf(report_id: int) -> str:
    """生成真实 PDF 文件并写入 EXPORT_DIR，返回文件路径"""
    report = await _get_report(report_id)
    if not report:
        return ""

    _register_cjk_font()

    title_style = ParagraphStyle("title", fontName=_CJK_FONT, fontSize=20, leading=28,
                                 alignment=TA_CENTER, spaceAfter=10)
    heading_style = ParagraphStyle("heading", fontName=_CJK_FONT, fontSize=14, leading=20,
                                   spaceBefore=12, spaceAfter=6)
    body_style = ParagraphStyle("body", fontName=_CJK_FONT, fontSize=10.5, leading=17)

    story = [Paragraph(_escape(report.title or f"Report #{report_id}"), title_style)]
    if report.summary:
        story.append(Paragraph(f"<i>{_escape(report.summary)}</i>", body_style))
        story.append(Spacer(1, 8))

    story.append(Paragraph("一、背景", heading_style))
    story.append(Paragraph(_escape(report.background or ""), body_style))

    story.append(Paragraph("二、现状", heading_style))
    story.append(Paragraph(_escape(report.status_content or ""), body_style))

    story.append(Paragraph("三、趋势", heading_style))
    story.append(Paragraph(f"<b>短期（1-3个月）：</b>{_escape(report.trend_short or '')}", body_style))
    story.append(Paragraph(f"<b>中长期（6-12个月）：</b>{_escape(report.trend_long or '')}", body_style))

    story.append(Paragraph("四、风险", heading_style))
    story.append(Paragraph(f"<b>{_escape(report.risk1 or '风险1')}</b>", body_style))
    story.append(Paragraph(_escape(report.risk1_desc or ""), body_style))
    story.append(Paragraph(f"<b>{_escape(report.risk2 or '风险2')}</b>", body_style))
    story.append(Paragraph(_escape(report.risk2_desc or ""), body_style))

    if report.key_data:
        story.append(Paragraph("五、关键数据", heading_style))
        for kd in report.key_data:
            if isinstance(kd, dict):
                label = _escape(str(kd.get('label', '')))
                value = _escape(str(kd.get('value', '')))
                change = _escape(str(kd.get('change', '')))
                story.append(Paragraph(f"• {label}：{value}（{change}）", body_style))
            else:
                story.append(Paragraph(f"• {_escape(str(kd))}", body_style))

    if report.sources:
        story.append(Paragraph("六、来源", heading_style))
        for s in report.sources:
            if isinstance(s, dict):
                title = s.get("title") or s.get("source") or ""
                url = s.get("url") or ""
                text = f"• {_escape(str(title))}"
                if url:
                    text += f"（{_escape(str(url))}）"
                story.append(Paragraph(text, body_style))
            else:
                story.append(Paragraph(f"• {_escape(str(s))}", body_style))

    os.makedirs(settings.EXPORT_DIR, exist_ok=True)
    path = os.path.join(settings.EXPORT_DIR, f"report_{report_id}.pdf")
    doc = SimpleDocTemplate(path, pagesize=A4,
                            leftMargin=2 * cm, rightMargin=2 * cm,
                            topMargin=2 * cm, bottomMargin=2 * cm)
    doc.build(story)
    return path
