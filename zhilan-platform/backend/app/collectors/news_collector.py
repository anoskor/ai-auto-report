"""数据采集模块 — 网络爬虫（RSS 订阅 + 网页抓取）

不依赖任何付费/需 key 的新闻接口，直接从网络采集：
1. RSS 订阅源（feedparser 解析）
2. 通用网页抓取（httpx + BeautifulSoup）
"""

import hashlib
from datetime import datetime, timezone
from urllib.parse import urlparse

import httpx
import feedparser
from bs4 import BeautifulSoup
from sqlalchemy import select

from app.config import settings
from app.database import async_session_factory
from app.models.article import RawArticle


def _clean_text(text: str) -> str:
    """去除多余空白，截断超长内容"""
    if not text:
        return ""
    text = " ".join(text.split())
    return text[:5000]


def _url_hash(url: str) -> str:
    return hashlib.sha256(url.encode()).hexdigest()[:16]


async def _fetch_rss() -> list[dict]:
    """从 RSS 源采集新闻（免费、无需 key）"""
    sources = [s.strip() for s in settings.RSS_SOURCES.split(",") if s.strip()]
    if not sources:
        return []

    articles: list[dict] = []
    headers = {"User-Agent": settings.CRAWL_USER_AGENT}
    async with httpx.AsyncClient(timeout=settings.CRAWL_TIMEOUT, headers=headers, follow_redirects=True) as client:
        for src in sources:
            try:
                resp = await client.get(src)
                resp.raise_for_status()
                feed = feedparser.parse(resp.content)
                for entry in feed.entries[:30]:
                    title = entry.get("title", "").strip()
                    link = entry.get("link", "").strip()
                    content = entry.get("summary", "") or entry.get("description", "")
                    if not title or not link:
                        continue
                    published = None
                    if entry.get("published_parsed"):
                        published = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)
                    articles.append({
                        "source": "rss",
                        "title": title,
                        "content": _clean_text(content),
                        "url": link,
                        "published_at": published or datetime.now(timezone.utc),
                    })
            except Exception as e:
                # 单个源失败不影响其他源
                print(f"[Crawler] RSS 源抓取失败 {src}: {e}")
    return articles


async def _fetch_webpages() -> list[dict]:
    """从网页列表抓取新闻标题与链接（通用抓取）"""
    targets = [s.strip() for s in settings.CRAWL_TARGETS.split(",") if s.strip()]
    if not targets:
        return []

    articles: list[dict] = []
    headers = {"User-Agent": settings.CRAWL_USER_AGENT}
    async with httpx.AsyncClient(timeout=settings.CRAWL_TIMEOUT, headers=headers, follow_redirects=True) as client:
        for target in targets:
            try:
                resp = await client.get(target)
                resp.raise_for_status()
                soup = BeautifulSoup(resp.text, "lxml")
                # 提取新闻链接：优先 <article>，退化为 <a>
                base_host = urlparse(target).netloc
                candidates = soup.select("article a, .news-list a, .list a, h3 a, h2 a, a[title]")
                if not candidates:
                    candidates = soup.select("a[href]")
                seen = 0
                for a in candidates:
                    title = (a.get("title") or a.get_text(strip=True)).strip()
                    href = a.get("href", "").strip()
                    if not title or not href or len(title) < 6:
                        continue
                    if href.startswith("/"):
                        href = f"https://{base_host}{href}"
                    if not href.startswith("http"):
                        continue
                    articles.append({
                        "source": "web",
                        "title": title,
                        "content": title,
                        "url": href,
                        "published_at": datetime.now(timezone.utc),
                    })
                    seen += 1
                    if seen >= 20:
                        break
            except Exception as e:
                print(f"[Crawler] 网页抓取失败 {target}: {e}")
    return articles


async def run_collection():
    """执行一次完整数据采集"""
    all_articles: list[dict] = []
    all_articles.extend(await _fetch_rss())
    all_articles.extend(await _fetch_webpages())

    inserted = 0
    if not all_articles:
        return inserted

    async with async_session_factory() as db:
        for art in all_articles:
            url_hash = _url_hash(art["url"])
            existing = await db.execute(select(RawArticle).where(RawArticle.url_hash == url_hash))
            if existing.scalar():
                continue
            raw = RawArticle(
                source=art["source"],
                title=art["title"],
                content=art["content"],
                url=art["url"],
                url_hash=url_hash,
                published_at=art["published_at"],
            )
            db.add(raw)
            inserted += 1
        await db.commit()
    return inserted
