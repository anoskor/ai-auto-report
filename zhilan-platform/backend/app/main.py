"""FastAPI 应用入口"""

import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.database import init_db, close_db
from app.api import dashboard, briefs, reports, clusters, monitor, settings as settings_api, search, qa
from app.api.websocket import websocket_endpoint
from app.cache.redis_cache import init_cache, close_cache
from app.search.es_client import init_es, close_es
from app.scheduler.jobs import init_scheduler, close_scheduler
from app.pipeline import run_pipeline


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    await init_cache()
    await init_es()
    init_scheduler()
    # 启动后自动执行一次完整数据流水线（后台运行，不阻塞启动）
    asyncio.create_task(run_pipeline())
    yield
    close_scheduler()
    await close_es()
    await close_cache()
    await close_db()


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="智览 — AI自动化研报/新闻摘要生成平台",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# 注册 API 路由
app.include_router(dashboard.router, prefix=settings.API_PREFIX)
app.include_router(briefs.router, prefix=settings.API_PREFIX)
app.include_router(reports.router, prefix=settings.API_PREFIX)
app.include_router(clusters.router, prefix=settings.API_PREFIX)
app.include_router(monitor.router, prefix=settings.API_PREFIX)
app.include_router(settings_api.router, prefix=settings.API_PREFIX)
app.include_router(search.router, prefix=settings.API_PREFIX)
app.include_router(qa.router, prefix=settings.API_PREFIX)

# WebSocket 路由
app.websocket("/ws")(websocket_endpoint)


@app.get("/health")
async def health_check():
    return {"status": "ok", "app": settings.APP_NAME, "version": settings.APP_VERSION}
