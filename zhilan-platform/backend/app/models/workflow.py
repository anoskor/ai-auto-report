"""工作流与监控模型"""

from datetime import datetime
from typing import Optional
from sqlalchemy import String, Text, DateTime, Integer, JSON, Boolean, func
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base


class WorkflowRun(Base):
    __tablename__ = "workflow_runs"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    status: Mapped[str] = mapped_column(String(20), default="pending")
    current_stage: Mapped[str] = mapped_column(String(100), default="")
    percentage: Mapped[int] = mapped_column(Integer, default=0)
    pipeline_steps: Mapped[list] = mapped_column(JSON, default=list)
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime, default=None)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, default=None)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class AgentStatus(Base):
    __tablename__ = "agent_statuses"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), unique=True)
    icon: Mapped[str] = mapped_column(String(50), default="bot")
    status: Mapped[str] = mapped_column(String(20), default="idle")
    detail: Mapped[str] = mapped_column(String(200), default="")
    status_text: Mapped[str] = mapped_column(String(50), default="就绪")
    color: Mapped[str] = mapped_column(String(20), default="gray")
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())


class SystemLog(Base):
    __tablename__ = "system_logs"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    time: Mapped[str] = mapped_column(String(20))
    level: Mapped[str] = mapped_column(String(10), default="INFO")
    message: Mapped[str] = mapped_column(Text, default="")
    agent_name: Mapped[str] = mapped_column(String(100), default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class SystemMetric(Base):
    __tablename__ = "system_metrics"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    label: Mapped[str] = mapped_column(String(100))
    value: Mapped[str] = mapped_column(String(50), default="")
    sub_value: Mapped[str] = mapped_column(String(50), default="")
    percentage: Mapped[int] = mapped_column(Integer, default=0)
    color: Mapped[str] = mapped_column(String(20), default="blue")
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())
