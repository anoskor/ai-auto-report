"""采集新文章 → 去重 → 向量索引（数据扩充）。"""

import asyncio
import os
import sys

os.chdir(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.collectors.news_collector import run_collection  # noqa: E402
from app.database import init_db  # noqa: E402
from app.search.es_client import init_es  # noqa: E402


async def main():
    await init_db()
    await init_es()
    n = await run_collection()
    print("collected:", n)
    if n > 0:
        from app.processors.dedup import deduplicate_articles
        r = await deduplicate_articles()
        print("dedup:", r)
        from app.rag.indexer import index_pending_articles
        idx = await index_pending_articles()
        print("indexed:", idx)


if __name__ == "__main__":
    asyncio.run(main())
