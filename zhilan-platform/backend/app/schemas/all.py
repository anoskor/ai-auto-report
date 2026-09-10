"""Pydantic Schema — 与前端 types/index.ts 完全对齐"""

from typing import Optional
from pydantic import BaseModel, Field


# ===== 公共 =====
class KeyDataItem(BaseModel):
    label: str
    value: str
    change: str


class SourceItem(BaseModel):
    title: str
    url: str
    source: str = ""


class ReportRef(BaseModel):
    id: int
    title: str


class ArticleRef(BaseModel):
    title: str
    source: str
    date: str


class TimelineEvent(BaseModel):
    time: str
    title: str
    description: str


class MessageResponse(BaseModel):
    message: str
    success: bool = True


# ===== Dashboard =====
class StatItemOut(BaseModel):
    label: str
    value: str
    changeLabel: str
    changeType: str
    icon: str
    color: str


class TopNewsItemOut(BaseModel):
    id: int
    title: str
    time: str
    category: str


class TrendDataPointOut(BaseModel):
    date: str
    count: int


class WorkflowStepOut(BaseModel):
    label: str
    status: str
    detail: str


class WorkflowProgressOut(BaseModel):
    currentStage: str
    percentage: int


class ReportCardOut(BaseModel):
    id: int
    title: str
    sections: list[str]
    summary: str
    source: str
    time: str
    passRate: str


# ===== Briefs =====
class IndustryItemOut(BaseModel):
    name: str
    tags: list[str]


class SentimentDataOut(BaseModel):
    sentiment: int
    heat: int
    volatility: int


class SentimentTrendOut(BaseModel):
    labels: list[str]
    sentiment: list[int]
    heat: list[int]
    volatility: list[int]


class BriefItemOut(BaseModel):
    id: int
    title: str
    summary: str
    time: str
    category: str
    rating: int
    articleCount: int
    content: str
    relatedArticleCount: int
    relatedReportCount: int
    relatedReports: list[ReportRef]


# ===== Reports =====
class ReportItemOut(BaseModel):
    id: int
    title: str
    time: str
    sections: list[str]
    summary: str
    articleCount: int
    passRate: str
    background: str
    statusContent: str
    trendShort: str
    trendLong: str
    risk1: str
    risk1desc: str
    risk2: str
    risk2desc: str
    sources: list[SourceItem]
    keyData: list[KeyDataItem]


# ===== Clusters =====
class ClusterNodeOut(BaseModel):
    id: str
    name: str
    symbolSize: int
    category: int
    itemStyle: Optional[dict] = None


class ClusterLinkOut(BaseModel):
    source: str
    target: str


class ClusterGraphOut(BaseModel):
    nodes: list[ClusterNodeOut]
    links: list[ClusterLinkOut]


class ClusterItemOut(BaseModel):
    id: int
    title: str
    articleCount: int
    timeSpan: str
    rating: int
    keywords: list[str]
    timeline: list[TimelineEvent]
    articles: list[ArticleRef]


# ===== Monitor =====
class AgentStatusOut(BaseModel):
    name: str
    icon: str
    status: str
    detail: str
    statusText: str
    color: str


class LogEntryOut(BaseModel):
    time: str
    level: str
    message: str


class SystemMetricOut(BaseModel):
    label: str
    value: str
    subValue: Optional[str] = None
    percentage: int
    color: str


class PipelineStepOut(BaseModel):
    label: str
    status: str
    icon: str
    detail: str
    bgColor: str = ""
    borderColor: str = ""
    textColor: str = ""


# ===== Settings =====
class TopicOut(BaseModel):
    id: int
    name: str
    color: str
    active: bool


class TopicCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)


class DataSourceOut(BaseModel):
    id: int
    name: str
    description: str
    enabled: bool


class CronConfigOut(BaseModel):
    collection: str
    reportGeneration: str


class CronConfigUpdate(BaseModel):
    collection: Optional[str] = None
    reportGeneration: Optional[str] = None


class PushChannelOut(BaseModel):
    id: int
    name: str
    description: str
    enabled: bool
    webhookUrl: str = ""


class PushChannelUpdate(BaseModel):
    enabled: Optional[bool] = None
    webhookUrl: Optional[str] = None
