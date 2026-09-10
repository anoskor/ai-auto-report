"""文章模型"""

from datetime import datetime
from typing import Optional
from sqlalchemy import String, Text, DateTime, Boolean, JSON, func
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base


class RawArticle(Base):
    __tablename__ = "raw_articles"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    source: Mapped[str] = mapped_column(String(50), default="newsapi")
    title: Mapped[str] = mapped_column(String(500))
    content: Mapped[str] = mapped_column(Text, default="")
    url: Mapped[str] = mapped_column(String(1000))
    url_hash: Mapped[str] = mapped_column(String(64), default="", unique=True)
    published_at: Mapped[Optional[datetime]] = mapped_column(DateTime, default=None)
    author: Mapped[str] = mapped_column(String(200), default="")
    language: Mapped[str] = mapped_column(String(10), default="zh")
    topic_tags: Mapped[list] = mapped_column(JSON, default=list)
    raw_html: Mapped[str] = mapped_column(Text, default="")
    is_processed: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class ProcessedArticle(Base):
    __tablename__ = "processed_articles"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    raw_article_id: Mapped[Optional[int]] = mapped_column(default=None)
    title: Mapped[str] = mapped_column(String(500))
    content: Mapped[str] = mapped_column(Text, default="")
    source: Mapped[str] = mapped_column(String(50), default="")
    url: Mapped[str] = mapped_column(String(1000), default="")
    published_at: Mapped[Optional[datetime]] = mapped_column(DateTime, default=None)
    language: Mapped[str] = mapped_column(String(10), default="zh")
    embedding: Mapped[Optional[list]] = mapped_column(JSON, default=None)
    dedup_status: Mapped[str] = mapped_column(String(20), default="pending")
    cluster_id: Mapped[Optional[int]] = mapped_column(default=None)
    indexed: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
