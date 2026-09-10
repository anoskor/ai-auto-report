"""摘要生成模块 — 调用 DeepSeek LLM 生成结构化摘要与情绪/热度/波动评分"""

import json

from app.generators.llm_client import chat


def _fallback_summary(articles: list[dict], topic_label: str = "") -> dict:
    """无 API key 或调用失败时，基于真实文章标题生成基础摘要（非硬编码 mock）"""
    titles = [a.get("title", "") for a in articles if a.get("title")]
    title = (topic_label or (titles[0][:30] if titles else "新闻摘要"))[:30]
    summary = "；".join(titles[:3])[:100]
    return {
        "title": title,
        "summary": summary,
        "key_points": titles[:3],
        "sentiment": 60, "heat": 70, "volatility": 40,
        "sentiment_trend": [], "heat_trend": [], "volatility_trend": [],
        "category": "综合",
    }


async def generate_summary(articles: list[dict], topic_label: str = "") -> dict:
    """调用 LLM 对一组文章生成结构化摘要。

    articles: [{"title": str, "content": str}, ...]
    返回 title/summary/key_points + sentiment/heat/volatility 及近 7 日趋势数组。
    """
    snippets = []
    for i, a in enumerate(articles[:15]):
        title = a.get("title", "")
        content = (a.get("content", "") or "")[:200]
        snippets.append(f"{i + 1}. {title} | {content}")
    article_text = "\n".join(snippets)

    prompt = (
        "你是专业的金融新闻分析助手。以下是关于同一主题的一组新闻文章（标题 | 内容节选）：\n\n"
        f"{article_text}\n\n"
        "请基于以上文章生成结构化 JSON，字段如下（必须是合法 JSON，不要输出任何其他文字）：\n"
        "{\n"
        '  "title": "简洁有力的摘要标题（不超过30字）",\n'
        '  "summary": "100字以内的综合摘要",\n'
        '  "key_points": ["要点1", "要点2", "要点3"],\n'
        '  "sentiment": 0到100的整数（市场情绪，越高越乐观）,\n'
        '  "heat": 0到100的整数（热度）,\n'
        '  "volatility": 0到100的整数（波动性）,\n'
        '  "sentiment_trend": [7个0-100整数，近7日情绪走势],\n'
        '  "heat_trend": [7个0-100整数，近7日热度走势],\n'
        '  "volatility_trend": [7个0-100整数，近7日波动走势],\n'
        '  "category": "所属行业/领域（如宏观经济、科技、新能源等）"\n'
        "}"
    )
    messages = [
        {"role": "system", "content": "你是一名专业的金融新闻分析助手，输出严格符合 JSON 格式。"},
        {"role": "user", "content": prompt},
    ]

    try:
        raw = await chat(messages, json_mode=True, temperature=0.5)
        if raw:
            data = json.loads(raw)
            return {
                "title": data.get("title", topic_label or "新闻摘要"),
                "summary": data.get("summary", ""),
                "key_points": data.get("key_points", []),
                "sentiment": int(data.get("sentiment", 60)),
                "heat": int(data.get("heat", 70)),
                "volatility": int(data.get("volatility", 40)),
                "sentiment_trend": data.get("sentiment_trend", []),
                "heat_trend": data.get("heat_trend", []),
                "volatility_trend": data.get("volatility_trend", []),
                "category": data.get("category", "综合"),
            }
    except Exception as e:
        print(f"[Summarizer] LLM 摘要失败: {e}")

    return _fallback_summary(articles, topic_label)
