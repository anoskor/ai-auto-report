"""Elasticsearch 客户端 — 全文检索与日志存储"""

from typing import Any, Optional
from app.config import settings

_es_client: Optional[Any] = None


async def init_es():
    """初始化 ES 异步客户端"""
    global _es_client
    if not settings.ES_HOST:
        return
    try:
        from elasticsearch import AsyncElasticsearch
        _es_client = AsyncElasticsearch(
            hosts=[settings.ES_HOST],
            basic_auth=(settings.ES_USER, settings.ES_PASSWORD) if settings.ES_USER else None,
            verify_certs=False,
        )
        await _es_client.ping()
    except Exception:
        _es_client = None


async def close_es():
    """关闭 ES 连接"""
    if _es_client:
        await _es_client.close()


def get_es_client() -> Optional[Any]:
    return _es_client


async def search_news(query: str, size: int = 10, from_: int = 0) -> dict:
    """全文搜索新闻"""
    if not _es_client:
        return {"hits": [], "total": 0}
    result = await _es_client.search(
        index="news",
        from_=from_,
        size=size,
        query={
            "multi_match": {
                "query": query,
                "fields": ["title^3", "content", "summary"],
            }
        },
        highlight={
            "fields": {"title": {}, "content": {"fragment_size": 150}}
        },
    )
    return {
        "hits": [hit["_source"] for hit in result["hits"]["hits"]],
        "total": result["hits"]["total"]["value"],
    }
