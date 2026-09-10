"""Monitor API"""

from datetime import datetime
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.database import get_db
from app.models.workflow import AgentStatus, SystemLog, SystemMetric, WorkflowRun
from app.models.article import RawArticle
from app.models.topic import CronConfig

router = APIRouter(prefix="/monitor", tags=["Monitor"])


def _rel_time(dt) -> str:
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
    return f"{int(seconds // 86400)}天前"


@router.get("/status")
async def get_monitor_status(db: AsyncSession = Depends(get_db)):
    # 最新工作流运行记录（含七步流水线状态）
    run = (await db.execute(select(WorkflowRun).order_by(WorkflowRun.created_at.desc()).limit(1))).scalar()
    pipeline_steps = run.pipeline_steps if run and run.pipeline_steps else []
    is_running = (run.status == "running") if run else False
    percentage = run.percentage if run else 0

    # Agent 状态
    agents_result = await db.execute(select(AgentStatus).order_by(AgentStatus.id))
    agents = [
        {"name": a.name, "icon": a.icon, "status": a.status, "detail": a.detail,
         "statusText": a.status_text, "color": a.color}
        for a in agents_result.scalars().all()
    ]
    if not is_running:
        is_running = any(a["status"] == "running" for a in agents)

    # 系统指标
    metrics_result = await db.execute(select(SystemMetric).order_by(SystemMetric.id))
    metrics = [
        {"label": m.label, "value": m.value, "subValue": m.sub_value or None,
         "percentage": m.percentage, "color": m.color}
        for m in metrics_result.scalars().all()
    ]

    # 最新日志
    logs_result = await db.execute(select(SystemLog).order_by(SystemLog.created_at.desc()).limit(6))
    logs = [{"time": l.time, "level": l.level, "message": l.message} for l in logs_result.scalars().all()]

    # 上次采集时间：最新入库文章
    latest_article = (await db.execute(select(RawArticle).order_by(RawArticle.created_at.desc()).limit(1))).scalar()
    last_collect = _rel_time(latest_article.created_at) if latest_article else "暂无"

    # 下次采集：从 cron 配置推导
    cron = (await db.execute(select(CronConfig).where(CronConfig.name == "collection"))).scalar()
    next_collect = "按计划执行"
    if cron and cron.cron_expression:
        parts = cron.cron_expression.split()
        if len(parts) >= 2 and parts[1].startswith("*/"):
            next_collect = f"约{parts[1][2:]}小时后"

    return {
        "isRunning": is_running,
        "lastCollect": last_collect,
        "nextCollect": next_collect,
        "percentage": percentage,
        "pipelineSteps": pipeline_steps,
        "agents": agents,
        "logs": logs,
        "metrics": metrics,
    }


@router.get("/agents")
async def get_agents(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(AgentStatus).order_by(AgentStatus.id))
    agents = result.scalars().all()
    return [{"name": a.name, "icon": a.icon, "status": a.status, "detail": a.detail,
             "statusText": a.status_text, "color": a.color} for a in agents]


@router.get("/logs")
async def get_logs(page: int = Query(1, ge=1), size: int = Query(20, ge=1, le=100),
                   db: AsyncSession = Depends(get_db)):
    total = (await db.execute(select(func.count(SystemLog.id)))).scalar() or 0
    result = await db.execute(
        select(SystemLog).order_by(SystemLog.created_at.desc()).offset((page - 1) * size).limit(size)
    )
    logs = result.scalars().all()
    return {
        "items": [{"time": l.time, "level": l.level, "message": l.message} for l in logs],
        "total": total, "page": page, "size": size,
    }


@router.get("/metrics")
async def get_metrics(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(SystemMetric).order_by(SystemMetric.id))
    metrics = result.scalars().all()
    return [{"label": m.label, "value": m.value, "subValue": m.sub_value or None,
             "percentage": m.percentage, "color": m.color} for m in metrics]
