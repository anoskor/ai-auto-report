"""Dashboard API — 全部从数据库读取真实数据"""

from datetime import datetime, date, timedelta
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.database import get_db
from app.models.report import ResearchReport
from app.models.article import RawArticle, ProcessedArticle
from app.models.workflow import WorkflowRun
from app.schemas.all import StatItemOut, TopNewsItemOut, TrendDataPointOut, ReportCardOut

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])

_CATEGORY_KEYWORDS = [
    ("财经", ["央行", "金融", "经济", "股市", "证券", "财经", "银行", "房地产", "证监局", "基金", "降准"]),
    ("科技", ["AI", "人工智能", "科技", "芯片", "半导体", "互联网", "5G", "大模型"]),
    ("汽车", ["汽车", "新能源", "光伏", "车企", "电动车"]),
    ("国际", ["国际", "外交", "航母", "中东", "俄", "美", "欧盟", "伊朗"]),
    ("体育", ["体育", "篮球", "足球", "赛事", "男篮", "女足"]),
]


def _guess_category(title: str) -> str:
    for category, keywords in _CATEGORY_KEYWORDS:
        if any(k in title for k in keywords):
            return category
    return "综合"


def _rel_time(dt) -> str:
    """将时间转换为相对时间描述"""
    if not dt:
        return ""
    if dt.tzinfo is not None:
        dt = dt.replace(tzinfo=None)
    diff = datetime.now() - dt
    seconds = diff.total_seconds()
    if seconds < 60:
        return "刚刚"
    if seconds < 3600:
        return f"{int(seconds // 60)}分钟前"
    if seconds < 86400:
        return f"{int(seconds // 3600)}小时前"
    if seconds < 86400 * 2:
        return "昨天"
    return f"{int(seconds // 86400)}天前"


@router.get("/stats", response_model=list[StatItemOut])
async def get_stats(db: AsyncSession = Depends(get_db)):
    today_start = datetime.combine(date.today(), datetime.min.time())
    # 今日采集：今天入库的文章数
    today_collect = (await db.execute(
        select(func.count(RawArticle.id)).where(RawArticle.created_at >= today_start)
    )).scalar() or 0
    # 今日去重：已处理文章数
    dedup_count = (await db.execute(
        select(func.count(ProcessedArticle.id)).where(ProcessedArticle.created_at >= today_start)
    )).scalar() or 0
    # 生成研报：研报总数
    report_count = (await db.execute(select(func.count(ResearchReport.id)))).scalar() or 0
    # 推送次数：已完成的工作流运行次数
    push_count = (await db.execute(
        select(func.count(WorkflowRun.id)).where(WorkflowRun.status == "completed")
    )).scalar() or 0

    # 通过率：研报 review_passed 占比
    passed = (await db.execute(
        select(func.count(ResearchReport.id)).where(ResearchReport.review_passed == True)  # noqa: E712
    )).scalar() or 0
    pass_rate = f"{round(passed / report_count * 100, 1)}%" if report_count else "0%"

    return [
        {"label": "今日采集", "value": str(today_collect), "changeLabel": "实时采集", "changeType": "up", "icon": "rss", "color": "blue"},
        {"label": "今日去重", "value": str(dedup_count), "changeLabel": "已清洗入库", "changeType": "down", "icon": "filter", "color": "orange"},
        {"label": "生成研报", "value": str(report_count), "changeLabel": f"通过率 {pass_rate}", "changeType": "up", "icon": "file-check", "color": "green"},
        {"label": "推送次数", "value": str(push_count), "changeLabel": "已完成推送", "changeType": "neutral", "icon": "send", "color": "amber"},
    ]


@router.get("/top-news", response_model=list[TopNewsItemOut])
async def get_top_news(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(RawArticle).order_by(RawArticle.published_at.desc(), RawArticle.id.desc()).limit(8)
    )
    articles = result.scalars().all()
    return [
        TopNewsItemOut(
            id=a.id,
            title=a.title,
            time=_rel_time(a.published_at or a.created_at),
            category=_guess_category(a.title),
        ) for a in articles
    ]


@router.get("/trend", response_model=list[TrendDataPointOut])
async def get_trend(db: AsyncSession = Depends(get_db)):
    """近 7 天采集趋势（按发布时间聚合）"""
    days = [date.today() - timedelta(days=i) for i in range(6, -1, -1)]
    start = datetime.combine(days[0], datetime.min.time())
    rows = (await db.execute(
        select(func.date(RawArticle.published_at), func.count(RawArticle.id))
        .where(RawArticle.published_at >= start)
        .group_by(func.date(RawArticle.published_at))
    )).all()
    count_map = {row[0]: row[1] for row in rows}
    return [
        TrendDataPointOut(date=d.strftime("%m/%d"), count=int(count_map.get(d, 0)))
        for d in days
    ]


@router.get("/latest-reports", response_model=list[ReportCardOut])
async def get_latest_reports(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(ResearchReport).order_by(ResearchReport.created_at.desc()).limit(3))
    reports = result.scalars().all()
    return [
        ReportCardOut(
            id=r.id, title=r.title, sections=r.sections or ["背景", "现状", "趋势", "风险"],
            summary=(r.summary or "")[:80], source=f"{r.article_count}篇文章",
            time=_rel_time(r.created_at) or "今天", passRate=r.pass_rate or "—",
        ) for r in reports
    ]


@router.get("/workflow-status")
async def get_workflow_status(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(WorkflowRun).order_by(WorkflowRun.created_at.desc()).limit(1))
    run = result.scalar()
    if run:
        steps = run.pipeline_steps or []
        step_group1 = [
            {"label": s.get("label"), "status": s.get("status"), "detail": s.get("detail", "")}
            for s in steps if s.get("status") == "done"
        ]
        step_group2 = [
            {"label": s.get("label"), "status": s.get("status"), "detail": s.get("detail", "")}
            for s in steps if s.get("status") != "done"
        ]
        return {
            "currentStage": run.current_stage or "待启动",
            "percentage": run.percentage or 0,
            "stepGroup1": step_group1,
            "stepGroup2": step_group2,
        }
    return {"currentStage": "待启动", "percentage": 0, "stepGroup1": [], "stepGroup2": []}
