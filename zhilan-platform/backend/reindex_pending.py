"""重跑增量索引：将 unique 且未索引的文章写入 ES"""
import asyncio
import os
import sys

os.chdir(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.database import init_db  # noqa: E402
from app.search.es_client import init_es  # noqa: E402
from app.rag.indexer import index_pending_articles  # noqa: E402


async def main():
    await init_db()
    await init_es()
    result = await index_pending_articles()
    print("INDEXED RESULT:", result)


if __name__ == "__main__":
    asyncio.run(main())
