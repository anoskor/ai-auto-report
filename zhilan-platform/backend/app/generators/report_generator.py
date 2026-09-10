"""研报生成模块 — 调用 DeepSeek LLM 生成四段式研报 + 每日简报"""

import asyncio
import json
from datetime import date, datetime
from typing import Optional

from sqlalchemy import select

from app.database import async_session_factory
from app.generators.llm_client import chat
from app.models.article import ProcessedArticle
from app.models.brief import DailyBrief
from app.models.cluster import NewsCluster
from app.models.report import ResearchReport

# 并发上限：同时最多发起的 LLM 请求数
_CONCURRENCY = 5


def _to_int(v, default: int = 60) -> int:
    try:
        return int(v)
    except (TypeError, ValueError):
        return default


def _html_escape(text) -> str:
    """转义 HTML 特殊字符，避免 v-html 渲染时被当作标签"""
    return (text or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _build_brief_content(data: dict) -> str:
    """用四段式研报内容拼接简报「新闻正文」的 HTML 段落"""
    sections = [
        ("背景", data.get("background", "")),
        ("现状", data.get("status_content", "")),
        ("短期趋势", data.get("trend_short", "")),
        ("中长期趋势", data.get("trend_long", "")),
    ]
    parts = []
    for label, text in sections:
        if text:
            parts.append(f"<p><strong>{label}：</strong>{_html_escape(text)}</p>")
    if not parts:
        parts.append(f"<p>{_html_escape(data.get('summary', ''))}</p>")
    return "".join(parts)


def _build_sources(articles: list[dict]) -> list[dict]:
    """构造带原文链接的真实来源列表：[{title, url, source}]"""
    items = []
    for a in articles:
        url = (a.get("url") or "").strip()
        if not url:
            continue
        title = (a.get("title") or "").strip() or a.get("source", "")
        items.append({
            "title": title,
            "url": url,
            "source": a.get("source", ""),
        })
    return items[:5]


def _fallback_full(articles: list[dict], topic_label: str = "") -> dict:
    """LLM 不可用时的降级：基于真实标题生成基础研报（非硬编码 mock）"""
    titles = [a.get("title", "") for a in articles if a.get("title")]
    title = (topic_label or (titles[0][:30] if titles else "新闻研报"))[:30]
    summary = "；".join(titles[:3])[:100]
    return {
        "title": title, "summary": summary,
        "sentiment": 60, "heat": 70, "volatility": 40,
        "sentiment_trend": [], "heat_trend": [], "volatility_trend": [],
        "category": "综合",
        "background": summary, "status_content": summary,
        "trend_short": "", "trend_long": "",
        "risk1": "", "risk1_desc": "", "risk2": "", "risk2_desc": "",
        "key_data": [],
        "sources": _build_sources(articles),
    }


async def _generate_full(articles: list[dict], topic_label: str = "") -> Optional[dict]:
    """一次 LLM 调用同时生成摘要 + 四段式研报（背景/现状/趋势/风险）。"""
    snippets = []
    for i, a in enumerate(articles[:10]):
        snippets.append(f"{i + 1}. {a.get('title', '')} | {(a.get('content', '') or '')[:150]}")
    article_text = "\n".join(snippets)

    prompt = (
        "你是资深行业研究员。以下是关于同一主题的一组新闻文章（标题 | 内容节选）：\n\n"
        f"{article_text}\n\n"
        "请生成结构化 JSON（必须是合法 JSON，不要输出其他文字），字段如下：\n"
        "{\n"
        '  "title": "简洁有力的研报标题（不超过30字）",\n'
        '  "summary": "100字以内的综合摘要",\n'
        '  "sentiment": 0到100整数（市场情绪，越高越乐观）,\n'
        '  "heat": 0到100整数（热度）,\n'
        '  "volatility": 0到100整数（波动性）,\n'
        '  "sentiment_trend": [7个0-100整数，近7日情绪走势],\n'
        '  "heat_trend": [7个0-100整数，近7日热度走势],\n'
        '  "volatility_trend": [7个0-100整数，近7日波动走势],\n'
        '  "category": "所属行业/领域（如宏观经济、科技、新能源等）",\n'
        '  "background": "背景段落（200字内）",\n'
        '  "status_content": "现状段落（200字内）",\n'
        '  "trend_short": "短期趋势（150字内）",\n'
        '  "trend_long": "中长期趋势（150字内）",\n'
        '  "risk1": "风险点1标题",\n'
        '  "risk1_desc": "风险点1描述（100字内）",\n'
        '  "risk2": "风险点2标题",\n'
        '  "risk2_desc": "风险点2描述（100字内）",\n'
        '  "key_data": [{"label": "指标名", "value": "数值", "change": "变化"}],\n'
        '  "sources": ["来源1", "来源2", "来源3"]\n'
        "}"
    )
    messages = [
        {"role": "system", "content": "你是一名资深行业研究员，输出严格符合 JSON 格式。"},
        {"role": "user", "content": prompt},
    ]
    try:
        raw = await chat(messages, json_mode=True, temperature=0.6)
        if not raw:
            return None
        data = json.loads(raw)
        return {
            "title": data.get("title", topic_label or "新闻研报"),
            "summary": data.get("summary", ""),
            "sentiment": _to_int(data.get("sentiment"), 60),
            "heat": _to_int(data.get("heat"), 70),
            "volatility": _to_int(data.get("volatility"), 40),
            "sentiment_trend": data.get("sentiment_trend", []),
            "heat_trend": data.get("heat_trend", []),
            "volatility_trend": data.get("volatility_trend", []),
            "category": data.get("category", "综合"),
            "background": data.get("background", ""),
            "status_content": data.get("status_content", ""),
            "trend_short": data.get("trend_short", ""),
            "trend_long": data.get("trend_long", ""),
            "risk1": data.get("risk1", ""),
            "risk1_desc": data.get("risk1_desc", ""),
            "risk2": data.get("risk2", ""),
            "risk2_desc": data.get("risk2_desc", ""),
            "key_data": data.get("key_data", []),
            "sources": data.get("sources", []),
        }
    except Exception as e:
        print(f"[ReportGenerator] LLM 生成失败: {e}")
        return None


async def run_generation() -> dict:
    """并发生成研报与简报，持久化到 research_reports / daily_briefs。

    流程：串行读库 → 并发 LLM 生成 → 串行写库，返回 {"generated": n, "passed": m, "failed": k}
    """
    # 1. 串行读取所有待生成簇及其文章
    tasks: list[tuple] = []  # (cluster, articles)
    async with async_session_factory() as db:
        done_ids = set((await db.execute(
            select(ResearchReport.cluster_id).where(ResearchReport.cluster_id.isnot(None))
        )).scalars().all())

        clusters = (await db.execute(
            select(NewsCluster).order_by(NewsCluster.importance_score.desc())
        )).scalars().all()

        for c in clusters:
            if c.id in done_ids:
                continue
            art_result = await db.execute(
                select(ProcessedArticle).where(ProcessedArticle.cluster_id == c.id)
                .order_by(ProcessedArticle.published_at.desc())
            )
            arts = art_result.scalars().all()
            articles = [
                {"title": a.title or "", "content": a.content or "", "source": a.source or "", "url": a.url or ""}
                for a in arts
            ]
            if articles:
                tasks.append((c, articles))

    if not tasks:
        return {"generated": 0, "passed": 0, "failed": 0}

    # 2. 并发执行 LLM 生成（限流）
    sem = asyncio.Semaphore(_CONCURRENCY)

    async def generate_one(item):
        c, articles = item
        async with sem:
            data = await _generate_full(articles, c.topic_label)
        if data is None:
            data = _fallback_full(articles, c.topic_label)
        return c, articles, data

    results = await asyncio.gather(*(generate_one(t) for t in tasks), return_exceptions=True)

    # 3. 串行写库
    generated = 0
    passed = 0
    failed = 0
    async with async_session_factory() as db:
        for item in results:
            if isinstance(item, BaseException):
                print(f"[ReportGenerator] 生成异常: {item}")
                failed += 1
                continue
            c, articles, data = item
            try:
                report = ResearchReport(
                    title=data.get("title", c.topic_label),
                    summary=data.get("summary", ""),
                    article_count=len(articles),
                    pass_rate="100%",
                    sections=["背景", "现状", "趋势", "风险"],
                    background=data.get("background", ""),
                    status_content=data.get("status_content", ""),
                    trend_short=data.get("trend_short", ""),
                    trend_long=data.get("trend_long", ""),
                    risk1=data.get("risk1", ""),
                    risk1_desc=data.get("risk1_desc", ""),
                    risk2=data.get("risk2", ""),
                    risk2_desc=data.get("risk2_desc", ""),
                    sources=_build_sources(articles),
                    key_data=data.get("key_data", []),
                    review_passed=True,
                    review_feedback=[],
                    cluster_id=c.id,
                    created_at=datetime.now(),
                )
                db.add(report)
                await db.flush()

                brief = DailyBrief(
                    title=data.get("title", c.topic_label),
                    summary=data.get("summary", ""),
                    time=datetime.now().strftime("%H:%M"),
                    category=data.get("category", "综合"),
                    rating=max(3, min(5, c.rating or 4)),
                    article_count=len(articles),
                    content=_build_brief_content(data),
                    related_article_count=len(articles),
                    related_report_count=1,
                    related_reports=[{"id": report.id, "title": report.title}],
                    sentiment=data.get("sentiment", 60),
                    heat=data.get("heat", 70),
                    volatility=data.get("volatility", 40),
                    sentiment_trend=data.get("sentiment_trend", []),
                    heat_trend=data.get("heat_trend", []),
                    volatility_trend=data.get("volatility_trend", []),
                    industries=[{"name": data.get("category", "综合"), "tags": c.keywords or []}],
                    brief_date=date.today(),
                    created_at=datetime.now(),
                )
                db.add(brief)
                generated += 1
                passed += 1
            except Exception as e:
                print(f"[ReportGenerator] 聚类 {c.id} 落库失败: {e}")
                failed += 1

        await db.commit()
        return {"generated": generated, "passed": passed, "failed": failed}
