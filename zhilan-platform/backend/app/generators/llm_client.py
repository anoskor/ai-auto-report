"""AI 客户端封装 — DeepSeek 对话 + 阿里云 DashScope Embedding"""

import math
from typing import Optional

import httpx

from app.config import settings


async def chat(messages: list[dict], json_mode: bool = False, temperature: float = 0.7) -> Optional[str]:
    """调用 DeepSeek 对话模型，返回消息文本内容。

    json_mode=True 时要求模型返回 JSON（response_format=json_object）。
    无 API key 时返回 None（调用方应做降级处理）。
    """
    if not settings.DEEPSEEK_API_KEY:
        return None

    payload = {
        "model": settings.DEEPSEEK_MODEL,
        "messages": messages,
        "temperature": temperature,
        "stream": False,
    }
    if json_mode:
        payload["response_format"] = {"type": "json_object"}

    headers = {
        "Authorization": f"Bearer {settings.DEEPSEEK_API_KEY}",
        "Content-Type": "application/json",
    }
    async with httpx.AsyncClient(timeout=120) as client:
        resp = await client.post(
            f"{settings.DEEPSEEK_API_BASE}/chat/completions",
            json=payload,
            headers=headers,
        )
        resp.raise_for_status()
        data = resp.json()
        return data["choices"][0]["message"]["content"]


async def embed(texts: list[str]) -> list[list[float]]:
    """调用 DashScope text-embedding-v3 生成向量，按 10 条一批拆分。

    返回与 texts 顺序一致的向量列表；无 API key 或空输入时返回空列表。
    """
    if not texts:
        return []
    if not settings.DASHSCOPE_API_KEY:
        return []

    headers = {
        "Authorization": f"Bearer {settings.DASHSCOPE_API_KEY}",
        "Content-Type": "application/json",
    }
    vectors: list[list[float]] = []
    async with httpx.AsyncClient(timeout=120) as client:
        for i in range(0, len(texts), 10):
            batch = texts[i:i + 10]
            payload = {
                "model": settings.DASHSCOPE_EMBEDDING_MODEL,
                "input": batch,
                "dimensions": settings.DASHSCOPE_EMBEDDING_DIMENSIONS,
            }
            resp = await client.post(
                f"{settings.DASHSCOPE_BASE}/embeddings",
                json=payload,
                headers=headers,
            )
            resp.raise_for_status()
            data = resp.json()
            for item in sorted(data["data"], key=lambda x: x["index"]):
                vectors.append(item["embedding"])
    return vectors


async def rerank(query: str, documents: list[str], top_n: int = 5) -> list[dict]:
    """Rerank candidate documents via DashScope qwen3-rerank.

    Returns list of {"index": original_index, "relevance_score": score}
    sorted by relevance desc. Returns empty list on missing API key / empty
    input / call failure (caller falls back to original order).
    """
    if not documents or not settings.DASHSCOPE_API_KEY:
        return []

    headers = {
        "Authorization": f"Bearer {settings.DASHSCOPE_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": settings.DASHSCOPE_RERANK_MODEL,
        "query": query,
        "documents": documents,
        "top_n": top_n,
    }
    async with httpx.AsyncClient(timeout=120) as client:
        resp = await client.post(
            settings.DASHSCOPE_RERANK_BASE,
            json=payload,
            headers=headers,
        )
        resp.raise_for_status()
        data = resp.json()
    # qwen3-rerank response: results at top level (no output wrapper)
    results = data.get("results", [])
    return [
        {"index": r["index"], "relevance_score": r["relevance_score"]}
        for r in results
    ]


def cosine_sim(a: list[float], b: list[float]) -> float:
    """计算两个向量的余弦相似度（0~1）"""
    if not a or not b or len(a) != len(b):
        return 0.0
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    if na == 0 or nb == 0:
        return 0.0
    return dot / (na * nb)
