"""Settings API"""

import asyncio
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models.topic import Topic, DataSource, CronConfig, PushChannel
from app.schemas.all import TopicCreate, CronConfigUpdate, PushChannelUpdate, MessageResponse

router = APIRouter(tags=["Settings"])


# ===== Topics =====
@router.get("/topics")
async def get_topics(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Topic).order_by(Topic.id))
    topics = result.scalars().all()
    return [{"id": t.id, "name": t.name, "color": t.color, "active": t.active} for t in topics]


@router.post("/topics")
async def create_topic(data: TopicCreate, db: AsyncSession = Depends(get_db)):
    colors = ["blue", "green", "amber", "orange", "purple"]
    existing = (await db.execute(select(Topic))).scalars().all()
    topic = Topic(name=data.name, color=colors[len(existing) % len(colors)], active=True)
    db.add(topic)
    await db.commit()
    await db.refresh(topic)
    return {"id": topic.id, "name": topic.name, "color": topic.color, "active": topic.active}


@router.delete("/topics/{topic_id}", response_model=MessageResponse)
async def delete_topic(topic_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Topic).where(Topic.id == topic_id))
    topic = result.scalar()
    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found")
    await db.delete(topic)
    await db.commit()
    return MessageResponse(message="主题已删除")


@router.put("/topics/{topic_id}/toggle")
async def toggle_topic(topic_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Topic).where(Topic.id == topic_id))
    topic = result.scalar()
    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found")
    topic.active = not topic.active
    await db.commit()
    await db.refresh(topic)
    return {"id": topic.id, "name": topic.name, "color": topic.color, "active": topic.active}


# ===== Data Sources =====
@router.get("/sources")
async def get_sources(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(DataSource).order_by(DataSource.id))
    sources = result.scalars().all()
    return [{"id": s.id, "name": s.name, "description": s.description, "enabled": s.enabled} for s in sources]


@router.put("/sources/{source_id}")
async def toggle_source(source_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(DataSource).where(DataSource.id == source_id))
    source = result.scalar()
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")
    source.enabled = not source.enabled
    await db.commit()
    await db.refresh(source)
    return {"id": source.id, "name": source.name, "description": source.description, "enabled": source.enabled}


# ===== Cron Config =====
@router.get("/config/cron")
async def get_cron_config(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(CronConfig).order_by(CronConfig.id))
    configs = {c.name: c.cron_expression for c in result.scalars().all()}
    return {
        "collection": configs.get("collection", "0 */2 * * *"),
        "reportGeneration": configs.get("reportGeneration", "0 7 * * *"),
    }


@router.put("/config/cron")
async def update_cron_config(data: CronConfigUpdate, db: AsyncSession = Depends(get_db)):
    if data.collection is not None:
        result = await db.execute(select(CronConfig).where(CronConfig.name == "collection"))
        cfg = result.scalar()
        if cfg:
            cfg.cron_expression = data.collection
        else:
            db.add(CronConfig(name="collection", cron_expression=data.collection, description="采集频率"))
    if data.reportGeneration is not None:
        result = await db.execute(select(CronConfig).where(CronConfig.name == "reportGeneration"))
        cfg = result.scalar()
        if cfg:
            cfg.cron_expression = data.reportGeneration
        else:
            db.add(CronConfig(name="reportGeneration", cron_expression=data.reportGeneration, description="研报生成频率"))
    await db.commit()
    return await get_cron_config(db)


# ===== Push Channels =====
@router.get("/config/push")
async def get_push_channels(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(PushChannel).order_by(PushChannel.id))
    channels = result.scalars().all()
    return [{"id": c.id, "name": c.name, "description": c.description,
             "enabled": c.enabled, "webhookUrl": c.webhook_url or ""} for c in channels]


@router.put("/config/push/{channel_id}")
async def toggle_push_channel(channel_id: int, data: Optional[PushChannelUpdate] = None,
                               db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(PushChannel).where(PushChannel.id == channel_id))
    channel = result.scalar()
    if not channel:
        raise HTTPException(status_code=404, detail="Channel not found")
    if data:
        if data.enabled is not None:
            channel.enabled = data.enabled
        if data.webhookUrl is not None:
            channel.webhook_url = data.webhookUrl
    else:
        channel.enabled = not channel.enabled
    await db.commit()
    await db.refresh(channel)
    return {"id": channel.id, "name": channel.name, "description": channel.description,
            "enabled": channel.enabled, "webhookUrl": channel.webhook_url or ""}


# ===== Manual Collect =====
@router.post("/collect", response_model=MessageResponse)
async def trigger_collect():
    from app.pipeline import run_pipeline
    asyncio.create_task(run_pipeline())
    return MessageResponse(message="即时采集任务已触发")
