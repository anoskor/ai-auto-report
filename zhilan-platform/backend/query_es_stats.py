"""查询 ES 现状：chunk 总数、每文章 chunk 数分布、采样文章标题"""
import asyncio
import json
import os
import sys

os.chdir(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.search.es_client import init_es, get_es_client  # noqa: E402

INDEX = "news_chunks"


async def main():
    await init_es()
    es = get_es_client()
    if not es:
        print("ES 未连接")
        return

    cnt = await es.count(index=INDEX)
    print("TOTAL CHUNKS:", cnt["count"])

    # 按 article_id 聚合 chunk 数
    agg = await es.search(index=INDEX, size=0, aggs={
        "per_article": {"terms": {"field": "article_id", "size": 1000}},
    })
    buckets = agg["aggregations"]["per_article"]["buckets"]
    print("TOTAL ARTICLES:", len(buckets))
    dist = {}
    for b in buckets:
        n = b["doc_count"]
        dist[n] = dist.get(n, 0) + 1
    print("CHUNK_DIST (chunks_per_article -> article_count):", dict(sorted(dist.items())))

    # 采样文章标题（多 chunk 的文章优先，作为人工 query 候选）
    agg2 = await es.search(index=INDEX, size=0, aggs={
        "per_article": {"terms": {"field": "article_id", "size": 1000},
                        "aggs": {"t": {"top_hits": {"size": 1, "_source": ["title", "article_id", "source"]}}}},
    })
    rows = []
    for b in agg2["aggregations"]["per_article"]["buckets"]:
        hit = b["t"]["hits"]["hits"][0]["_source"]
        rows.append({
            "article_id": hit["article_id"],
            "chunks": b["doc_count"],
            "source": hit.get("source", ""),
            "title": hit.get("title", ""),
        })
    # 按 chunk 数降序，取前 60 篇
    rows.sort(key=lambda x: -x["chunks"])
    out = rows[:60]
    for r in out:
        print(f"[{r['chunks']}chunk][{r['source']}] a{r['article_id']}: {r['title']}")

    # 保存完整列表到文件
    with open("es_articles_snapshot.json", "w", encoding="utf-8") as f:
        json.dump(rows, f, ensure_ascii=False, indent=2)
    print("SAVED es_articles_snapshot.json, total articles:", len(rows))


if __name__ == "__main__":
    asyncio.run(main())
