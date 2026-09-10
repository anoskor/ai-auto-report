"""APScheduler 定时任务调度"""

import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from app.config import settings

logger = logging.getLogger(__name__)
scheduler = AsyncIOScheduler()


async def _collect_job():
    """数据采集定时任务（完整流水线）"""
    logger.info("[Scheduler] 触发数据采集流水线")
    try:
        from app.pipeline import run_pipeline
        await run_pipeline()
    except Exception as e:
        logger.error(f"[Scheduler] 采集流水线失败: {e}")


async def _report_job():
    """研报生成定时任务（完整流水线）"""
    logger.info("[Scheduler] 触发研报生成流水线")
    try:
        from app.pipeline import run_pipeline
        await run_pipeline()
    except Exception as e:
        logger.error(f"[Scheduler] 研报生成流水线失败: {e}")


def init_scheduler():
    """注册并启动定时任务"""
    collection_interval = settings.COLLECTION_INTERVAL_MINUTES
    # 超过60分钟则用小时级触发
    if collection_interval > 59:
        hours = collection_interval // 60
        if collection_interval % 60 == 0:
            cron_expr = f"0 */{hours} * * *"
        else:
            cron_expr = f"0 */{hours} * * *"
    else:
        cron_expr = f"*/{collection_interval} * * * *"

    trigger = CronTrigger.from_crontab(cron_expr)
    scheduler.add_job(
        _collect_job,
        trigger=trigger,
        id="collect_job",
        name="数据采集",
        replace_existing=True,
    )
    scheduler.add_job(
        _report_job,
        trigger=CronTrigger(hour=settings.REPORT_GENERATION_HOUR, minute=settings.REPORT_GENERATION_MINUTE),
        id="report_job",
        name="研报生成",
        replace_existing=True,
    )
    scheduler.start()
    logger.info("[Scheduler] 定时任务已启动")


def close_scheduler():
    scheduler.shutdown(wait=False)
