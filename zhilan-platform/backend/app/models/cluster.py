"""聚类模型"""

from datetime import datetime
from typing import Optional
from sqlalchemy import String, DateTime, Integer, Float, JSON, func
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base


class NewsCluster(Base):
    __tablename__ = "news_clusters"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    topic_label: Mapped[str] = mapped_column(String(200))
    article_count: Mapped[int] = mapped_column(Integer, default=0)
    time_span: Mapped[str] = mapped_column(String(50), default="")
    importance_score: Mapped[float] = mapped_column(Float, default=0.0)
    rating: Mapped[int] = mapped_column(Integer, default=3)
    keywords: Mapped[list] = mapped_column(JSON, default=list)
    representative_article_id: Mapped[Optional[int]] = mapped_column(default=None)
    timeline: Mapped[list] = mapped_column(JSON, default=list)
    articles: Mapped[list] = mapped_column(JSON, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
