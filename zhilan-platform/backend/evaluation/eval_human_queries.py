"""RAG 检索评估 v3 — 人工 query 集（口语化改写 + 黄金文章标注）。

与 v2 的区别：
- 抛弃 LLM 自动改写（仍有关键词重叠偏置），改为人工构造口语化 query
- ground truth 标注到「文章」粒度（人工 query 的回答单元是文章，而非单个 chunk）
- 数据已扩充：841 chunk / 677 文章，含 11 篇 13-chunk 的 BBC 长文
- 分组统计：长文 / 短文 / 同主题混淆对，检验检索的区分度

指标：
- Recall@5/@10（文章粒度）：黄金文章是否出现在 top-k 结果中
- MRR（文章粒度）：黄金文章的任一 chunk 首次出现的倒数排名
"""

import asyncio
import os
import sys

os.chdir(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.generators.llm_client import embed, rerank  # noqa: E402
from app.rag.indexer import INDEX_NAME  # noqa: E402
from app.search.es_client import get_es_client, init_es  # noqa: E402

TOP_K = 10
RRF_K = 60

# ---- 人工 query 集：{query, gold(article_id), group} ----
# group: long=多chunk长文 / short=单chunk短文 / hard=同主题混淆对
QUERIES = [
    # ============ A. 多 chunk 长文（BBC 全文，13/11/10 chunk）============
    {"q": "美国这轮对伊朗的经济制裁，为什么偏偏给中国留了口子？", "gold": 788, "group": "long"},
    {"q": "哈里和梅根要是回英国定居，他们会怎么安排自己的工作和生活？", "gold": 789, "group": "long"},
    {"q": "华盛顿再次对伊朗动手，这轮制裁真能让德黑兰低头吗？", "gold": 790, "group": "long"},
    {"q": "美国乡村音乐天后去世了，她这一生留下了哪些经典作品？", "gold": 800, "group": "long"},
    {"q": "搬到英国布里斯托尔的香港人，靠什么活动找到了归属感？", "gold": 801, "group": "long"},
    {"q": "塔利班掌权后的阿富汗，普通人的生活受到了哪些管控？", "gold": 803, "group": "long"},
    {"q": "现在中国有些年轻人靠嗑处方药来逃避压力，这是怎么回事？", "gold": 805, "group": "long"},
    {"q": "全球海洋温度最近为何打破历史纪录？", "gold": 807, "group": "long"},
    {"q": "人为什么会莫名其妙地对没有实际危险的东西感到恐惧？", "gold": 808, "group": "long"},
    {"q": "有台湾艺人往日本国宝上泼东西，这事会怎样影响台日关系？", "gold": 811, "group": "long"},
    {"q": "有的女孩才六岁就来月经了，医生为什么也查不出原因？", "gold": 812, "group": "long"},
    {"q": "西藏靠近尼泊尔边境的山洪灾害，现在有多少人下落不明？", "gold": 787, "group": "long"},
    {"q": "老干妈的创始人陶华碧，她的成功经历给了我们哪些启发？", "gold": 806, "group": "long"},

    # ============ B. 单 chunk 短文（chinanews 摘要）============
    {"q": "今年暑期档的电影市场成绩怎么样？", "gold": 121, "group": "short"},
    {"q": "伊朗高层最近对地区冲突释放了什么强硬信号？", "gold": 92, "group": "short"},
    {"q": "美国最近是不是打算往中东增派航母了？", "gold": 93, "group": "short"},
    {"q": "香港今年上半年的外贸进出口数据表现如何？", "gold": 103, "group": "short"},
    {"q": "今年有多少东南亚水果是通过中老铁路运进中国的？", "gold": 117, "group": "short"},
    {"q": "两弹一星元勋里那位转行搞航天的王希季有什么贡献？", "gold": 118, "group": "short"},
    {"q": "欧洲消费者现在怎么看中国制造的电动汽车？", "gold": 122, "group": "short"},
    {"q": "日本最新财年的防卫预算申请有什么值得关注的动向？", "gold": 124, "group": "short"},
    {"q": "河南周口贾鲁河的那处决口最后堵上了吗？", "gold": 516, "group": "short"},
    {"q": "福州最近的高温天气，反而带火了什么消费？", "gold": 105, "group": "short"},

    # ============ C. 同主题混淆对（需精确区分）============
    {"q": "美国制裁伊朗的新措施里，为什么对中国企业网开一面？", "gold": 788, "group": "hard"},
    {"q": "美国对伊朗的新制裁能不能奏效，会不会真的让德黑兰改变政策？", "gold": 790, "group": "hard"},
    {"q": "日本现在是不是正在走向军国主义的道路上？", "gold": 123, "group": "hard"},
    {"q": "日本政府新一年申请的防卫预算金额达到了多少？", "gold": 124, "group": "hard"},
    {"q": "北京景山公园晚上开放后，游客能体验到什么新东西？", "gold": 369, "group": "hard"},
]


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


def article_rank(gt_article, hits):
    """返回黄金文章任一 chunk 在结果中首次出现的排名（1-based），未命中返回 0。"""
    for i, h in enumerate(hits):
        if h.get("article_id") == gt_article:
            return i + 1
    return 0


def recall_at(gt_article, hits, k):
    return any(h.get("article_id") == gt_article for h in hits[:k])


async def main():
    await init_es()
    es = get_es_client()
    if not es:
        print("ES 未连接")
        return

    configs = ("bm25", "rrf", "rerank")
    # 总体 + 分组统计
    stat = {g: {c: {"r5": 0, "r10": 0, "mrr": 0.0, "n": 0} for c in configs}
            for g in ("all", "long", "short", "hard")}

    details = []
    for item in QUERIES:
        q = item["q"]
        gt = item["gold"]
        g = item["group"]

        bm = await bm25_search(es, q, TOP_K)
        vecs = await embed([q])
        knn = await knn_search(es, vecs[0], TOP_K) if vecs and vecs[0] else []
        rrf = rrf_fusion(bm, knn, TOP_K)
        rr = await rerank_docs(q, rrf, TOP_K)

        row = {"q": q, "gold": gt, "group": g}
        for name, hits in (("bm25", bm), ("rrf", rrf), ("rerank", rr)):
            rank = article_rank(gt, hits)
            stat["all"][name]["n"] += 1
            stat[g][name]["n"] += 1
            stat["all"][name]["r5"] += recall_at(gt, hits, 5)
            stat[g][name]["r5"] += recall_at(gt, hits, 5)
            stat["all"][name]["r10"] += recall_at(gt, hits, 10)
            stat[g][name]["r10"] += recall_at(gt, hits, 10)
            if rank:
                stat["all"][name]["mrr"] += 1.0 / rank
                stat[g][name]["mrr"] += 1.0 / rank
            row[name + "_rank"] = rank
        details.append(row)
        print(f"[{g}] gold={gt} rank: bm25={row['bm25_rank']} rrf={row['rrf_rank']} rerank={row['rerank_rank']}  | {q}")

    print("\n================ 评估结果 ================")
    for g in ("all", "long", "short", "hard"):
        n = stat[g]["bm25"]["n"]
        if n == 0:
            continue
        print(f"\n--- {g} (n={n}) ---")
        print(f"{'config':8s} {'Recall@5':>9s} {'Recall@10':>10s} {'MRR':>8s}")
        for c in configs:
            print(f"{c:8s} {stat[g][c]['r5']/n:9.3f} {stat[g][c]['r10']/n:10.3f} {stat[g][c]['mrr']/n:8.4f}")

    import json
    with open("eval_human_result.json", "w", encoding="utf-8") as f:
        json.dump(details, f, ensure_ascii=False, indent=2)
    print("\nSAVED eval_human_result.json")


if __name__ == "__main__":
    asyncio.run(main())
