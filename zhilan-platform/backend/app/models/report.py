"""研报模型"""

from datetime import datetime
from typing import Optional
from sqlalchemy import String, Text, DateTime, Integer, Boolean, JSON, func
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base


class ResearchReport(Base):
    __tablename__ = "research_reports"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(500))
    summary: Mapped[str] = mapped_column(Text, default="")
    article_count: Mapped[int] = mapped_column(Integer, default=0)
    pass_rate: Mapped[str] = mapped_column(String(20), default="")
    sections: Mapped[list] = mapped_column(JSON, default=list)
    background: Mapped[str] = mapped_column(Text, default="")
    status_content: Mapped[str] = mapped_column(Text, default="")
    trend_short: Mapped[str] = mapped_column(Text, default="")
    trend_long: Mapped[str] = mapped_column(Text, default="")
    risk1: Mapped[str] = mapped_column(Text, default="")
    risk1_desc: Mapped[str] = mapped_column(Text, default="")
    risk2: Mapped[str] = mapped_column(Text, default="")
    risk2_desc: Mapped[str] = mapped_column(Text, default="")
    sources: Mapped[list] = mapped_column(JSON, default=list)
    key_data: Mapped[list] = mapped_column(JSON, default=list)
    review_passed: Mapped[bool] = mapped_column(Boolean, default=True)
    review_feedback: Mapped[list] = mapped_column(JSON, default=list)
    cluster_id: Mapped[Optional[int]] = mapped_column(default=None)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
