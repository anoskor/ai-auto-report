"""存量数据向量索引回填脚本（一次性）。

用法：在 backend 目录下运行
    D:\\develop\\python\\python.exe reindex_tmp.py

前提：Elasticsearch 已启动（localhost:9200）。
"""

import asyncio
import os
import sys

sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.search.es_client import init_es, close_es, get_es_client  # noqa: E402
from app.rag.indexer import index_pending_articles  # noqa: E402


async def main() -> None:
    await init_es()
    if not get_es_client():
        print("[reindex] ES 未连接，请先启动 Elasticsearch (localhost:9200)")
        return

    result = await index_pending_articles()
    print(f"[reindex] 完成: {result['indexed']} 篇文章, {result['chunks']} 个 chunk")
    await close_es()


if __name__ == "__main__":
    asyncio.run(main())
