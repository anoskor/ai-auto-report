"""每日简报模型"""

from datetime import datetime, date
from sqlalchemy import String, Text, DateTime, Date, Integer, JSON, func
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base


class DailyBrief(Base):
    __tablename__ = "daily_briefs"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(500))
    summary: Mapped[str] = mapped_column(Text, default="")
    time: Mapped[str] = mapped_column(String(50), default="")
    category: Mapped[str] = mapped_column(String(100), default="")
    rating: Mapped[int] = mapped_column(Integer, default=4)
    article_count: Mapped[int] = mapped_column(Integer, default=0)
    content: Mapped[str] = mapped_column(Text, default="")
    related_article_count: Mapped[int] = mapped_column(Integer, default=0)
    related_report_count: Mapped[int] = mapped_column(Integer, default=0)
    related_reports: Mapped[list] = mapped_column(JSON, default=list)
    sentiment: Mapped[int] = mapped_column(Integer, default=72)
    heat: Mapped[int] = mapped_column(Integer, default=85)
    volatility: Mapped[int] = mapped_column(Integer, default=45)
    sentiment_trend: Mapped[list] = mapped_column(JSON, default=list)
    heat_trend: Mapped[list] = mapped_column(JSON, default=list)
    volatility_trend: Mapped[list] = mapped_column(JSON, default=list)
    industries: Mapped[list] = mapped_column(JSON, default=list)
    brief_date: Mapped[date] = mapped_column(Date, default=date.today)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
