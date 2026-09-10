"""RAG 检索评估脚本 v2 — LLM 改写 query，对比 BM25 / RRF / RRF+Rerank。

评估方法：
- 随机抽样 N 个 chunk 作为评估样本
- 用 LLM 为每个 chunk 生成一个"语义等价但用词不同"的用户问题
  （避免直接用 title/text 检索带来的精确匹配偏置）
- 用该问题检索，ground truth = 原 chunk 的 article_id（文章粒度）/ chunk_id（严格粒度）
- 对比 BM25 / RRF / RRF+Rerank 的 Recall@k 与 MRR
"""

import asyncio
import json
import os
import random
import sys

os.chdir(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.generators.llm_client import chat, embed, rerank  # noqa: E402
from app.rag.indexer import INDEX_NAME  # noqa: E402
from app.search.es_client import get_es_client, init_es  # noqa: E402

SAMPLE_N = 20
TOP_K = 10
RRF_K = 60


async def sample_chunks(es, n: int) -> list[dict]:
    resp = await es.search(
        index=INDEX_NAME,
        size=10000,
        query={"match_all": {}},
        _source=["chunk_id", "article_id", "title", "text"],
    )
    all_chunks = [h["_source"] for h in resp["hits"]["hits"]]
    all_chunks = [
        c for c in all_chunks
        if (c.get("title") or "").strip() and (c.get("text") or "").strip()
    ]
    return random.sample(all_chunks, min(n, len(all_chunks)))


def parse_json(raw: str):
    raw = (raw or "").strip()
    if raw.startswith("```"):
        raw = raw.strip("`")
        if raw.startswith("json"):
            raw = raw[4:]
        raw = raw.strip()
    return json.loads(raw)


async def gen_queries(chunks: list[dict]) -> dict:
    items = [
        {"id": c["chunk_id"], "title": c["title"], "text": (c["text"] or "")[:150]}
        for c in chunks
    ]
    system = (
        "你是检索评估集生成器。针对每条新闻片段，写一个用户可能提出的中文问题，"
        "该问题的答案包含在该片段中。必须换一种说法表达，不要直接照抄标题或正文原句。"
        '严格输出 JSON 数组，每个元素为 {"id": 片段id, "q": 问题}，不要输出其他内容。'
    )
    user = "新闻片段：\n" + json.dumps(items, ensure_ascii=False)
    raw = await chat(
        [{"role": "system", "content": system}, {"role": "user", "content": user}],
        json_mode=True,
        temperature=0.7,
    )
    arr = parse_json(raw) if raw else []
    return {item["id"]: item["q"] for item in arr}


async def bm25_search(es, query: str, size: int) -> list[dict]:
    resp = await es.search(
        index=INDEX_NAME,
        size=size,
        query={"multi_match": {"query": query, "fields": ["title^3", "text^2", "content"]}},
        _source=["chunk_id", "article_id", "title", "text"],
    )
    return [{"chunk_id": h["_id"], **h["_source"]} for h in resp["hits"]["hits"]]


async def knn_search(es, vec, size: int) -> list[dict]:
    resp = await es.search(
        index=INDEX_NAME,
        size=size,
        knn={"field": "embedding", "query_vector": vec, "k": size, "num_candidates": 50},
        _source=["chunk_id", "article_id", "title", "text"],
    )
    return [{"chunk_id": h["_id"], **h["_source"]} for h in resp["hits"]["hits"]]


def rrf_fusion(bm25: list[dict], knn: list[dict], top_k: int) -> list[dict]:
    scores: dict = {}
    docs: dict = {}
    for lst in (bm25, knn):
        for rank, h in enumerate(lst):
            cid = h["chunk_id"]
            scores[cid] = scores.get(cid, 0.0) + 1.0 / (RRF_K + rank + 1)
            docs[cid] = h
    ranked = sorted(scores.items(), key=lambda kv: -kv[1])[:top_k]
    return [docs[cid] for cid, _ in ranked]


async def rerank_docs(query: str, hits: list[dict], top_k: int) -> list[dict]:
    documents = [h.get("text") or h.get("content") or "" for h in hits]
    try:
        ranked = await rerank(query, documents, top_n=top_k)
    except Exception:
        return hits[:top_k]
    if not ranked:
        return hits[:top_k]
    order = {r["index"]: r["relevance_score"] for r in ranked}
    for i, h in enumerate(hits):
        if i in order:
            h["_rr"] = round(order[i], 6)
    hits.sort(key=lambda h: h.get("_rr", -1.0), reverse=True)
    return hits[:top_k]


def hit_article(gt_article, hits, k):
    return any(h.get("article_id") == gt_article for h in hits[:k])


def mrr(gt_chunk, hits):
    for i, h in enumerate(hits):
        if h.get("chunk_id") == gt_chunk:
            return 1.0 / (i + 1)
    return 0.0


async def main():
    await init_es()
    es = get_es_client()
    random.seed(42)

    samples = await sample_chunks(es, SAMPLE_N)
    qmap = await gen_queries(samples)
    print("samples:", len(samples), "queries:", len(qmap))

    stats = {
        "bm25": {"r5": 0, "r10": 0, "mrr": 0.0},
        "rrf": {"r5": 0, "r10": 0, "mrr": 0.0},
        "rerank": {"r5": 0, "r10": 0, "mrr": 0.0},
    }
    n = 0
    for s in samples:
        q = qmap.get(s["chunk_id"])
        if not q:
            continue
        n += 1
        gt_chunk = s["chunk_id"]
        gt_article = s["article_id"]

        bm = await bm25_search(es, q, TOP_K)
        vecs = await embed([q])
        knn = await knn_search(es, vecs[0], TOP_K) if vecs and vecs[0] else []
        rrf = rrf_fusion(bm, knn, TOP_K)
        rr = await rerank_docs(q, rrf, TOP_K)

        for name, hits in (("bm25", bm), ("rrf", rrf), ("rerank", rr)):
            stats[name]["r5"] += hit_article(gt_article, hits, 5)
            stats[name]["r10"] += hit_article(gt_article, hits, 10)
            stats[name]["mrr"] += mrr(gt_chunk, hits)

    print("eval n:", n)
    print("=== Recall@5 (article) ===")
    for k in ("bm25", "rrf", "rerank"):
        print(f"{k:8s}: {stats[k]['r5'] / n:.3f}")
    print("=== Recall@10 (article) ===")
    for k in ("bm25", "rrf", "rerank"):
        print(f"{k:8s}: {stats[k]['r10'] / n:.3f}")
    print("=== MRR (chunk) ===")
    for k in ("bm25", "rrf", "rerank"):
        print(f"{k:8s}: {stats[k]['mrr'] / n:.4f}")


if __name__ == "__main__":
    asyncio.run(main())
