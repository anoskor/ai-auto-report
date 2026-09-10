"""负样本（库中不存在主题）评估 — 检验检索系统是否克制、不误报。

对每条「库中不存在」的 query，跑 BM25 / RRF / RRF+Rerank 三种配置，
取 top-1，计算 query 与 top-1 chunk 的 embedding 余弦相似度。
相似度越低，说明系统越克制（没有强行返回"看似相关"的文章）。
"""

import asyncio
import json
import os
import sys

os.chdir(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.generators.llm_client import embed, rerank, cosine_sim  # noqa: E402
from app.rag.indexer import INDEX_NAME  # noqa: E402
from app.search.es_client import get_es_client, init_es  # noqa: E402

TOP_K = 10
RRF_K = 60

# 库中不存在（或极不可能存在）的主题
ABSENT_QUERIES = [
    "比特币最近的价格走势如何？",
    "量子计算机的最新突破是什么？",
    "NBA 总决赛今年谁夺冠了？",
    "诺贝尔文学奖今年颁给了哪位作家？",
    "特斯拉最新车型的续航里程是多少？",
    "下一届世界杯足球赛的赛程怎么安排？",
    "如何在家自制酸奶？",
    "Python 3.13 有哪些新特性？",
    "苹果公司新发布的手机有什么亮点？",
    "最近有哪些好看的韩国电视剧推荐？",
]


async def bm25_search(es, query: str, size: int) -> list[dict]:
    resp = await es.search(
        index=INDEX_NAME,
        size=size,
        query={"multi_match": {"query": query, "fields": ["title^3", "text^2", "content"]}},
        _source=["chunk_id", "article_id", "title", "text", "embedding"],
    )
    return [{"chunk_id": h["_id"], **h["_source"]} for h in resp["hits"]["hits"]]


async def knn_search(es, vec, size: int) -> list[dict]:
    resp = await es.search(
        index=INDEX_NAME,
        size=size,
        knn={"field": "embedding", "query_vector": vec, "k": size, "num_candidates": 50},
        _source=["chunk_id", "article_id", "title", "text", "embedding"],
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


async def main():
    await init_es()
    es = get_es_client()
    if not es:
        print("ES 未连接")
        return

    configs = ("bm25", "rrf", "rerank")
    sim_sum = {c: 0.0 for c in configs}
    n = 0
    rows = []

    for q in ABSENT_QUERIES:
        n += 1
        bm = await bm25_search(es, q, TOP_K)
        vecs = await embed([q])
        knn = await knn_search(es, vecs[0], TOP_K) if vecs and vecs[0] else []
        rrf = rrf_fusion(bm, knn, TOP_K)
        rr = await rerank_docs(q, rrf, TOP_K)

        row = {"q": q}
        line = f"[absent] {q}"
        for name, hits in (("bm25", bm), ("rrf", rrf), ("rerank", rr)):
            top = hits[0] if hits else {}
            top_vec = top.get("embedding")
            sim = cosine_sim(vecs[0], top_vec) if (vecs and vecs[0] and top_vec) else 0.0
            sim_sum[name] += sim
            row[name + "_sim"] = round(sim, 4)
            row[name + "_title"] = (top.get("title") or "")[:40]
            line += f"\n    {name}: sim={sim:.3f} top=「{(top.get('title') or '')[:30]}」"
        rows.append(row)
        print(line)

    print("\n================ 负样本评估（相似度越低越克制）================")
    print(f"n = {n}")
    for c in configs:
        print(f"{c:8s}: avg top-1 cosine = {sim_sum[c]/n:.4f}")

    with open("eval_absent_result.json", "w", encoding="utf-8") as f:
        json.dump(rows, f, ensure_ascii=False, indent=2)
    print("SAVED eval_absent_result.json")


if __name__ == "__main__":
    asyncio.run(main())
