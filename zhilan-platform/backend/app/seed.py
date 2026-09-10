"""系统配置初始化脚本 — 幂等初始化基础配置（非 mock）"""

import asyncio

from sqlalchemy import select, func

from app.database import async_session_factory, init_db
from app.models.topic import Topic, DataSource, CronConfig, PushChannel
from app.models.workflow import AgentStatus, SystemMetric


async def run_seed():
    """初始化系统基础配置：主题、数据源、定时任务、推送渠道。

    均为幂等操作，已存在数据时跳过，不插入任何演示/模拟数据。
    """
    await init_db()

    async with async_session_factory() as db:
        # 主题
        topic_count = (await db.execute(select(func.count(Topic.id)))).scalar() or 0
        if topic_count == 0:
            db.add_all([
                Topic(name="宏观经济政策", color="blue", active=True),
                Topic(name="人工智能与科技", color="green", active=True),
                Topic(name="新能源与碳中和", color="amber", active=True),
                Topic(name="半导体产业", color="orange", active=False),
            ])

        # 数据源（仅真实可用的爬虫源默认启用）
        source_count = (await db.execute(select(func.count(DataSource.id)))).scalar() or 0
        if source_count == 0:
            db.add_all([
                DataSource(name="RSS 订阅", description="主流媒体 RSS 源（免费无需 key）", enabled=True),
                DataSource(name="自定义爬虫", description="网页定向抓取", enabled=True),
                DataSource(name="天聚数行", description="TianAPI 国内新闻数据接口", enabled=False),
                DataSource(name="财报PDF解析", description="上市公司财报分析", enabled=False),
            ])

        # 定时任务配置
        cron_count = (await db.execute(select(func.count(CronConfig.id)))).scalar() or 0
        if cron_count == 0:
            db.add(CronConfig(name="collection", cron_expression="0 */2 * * *", description="采集频率"))
            db.add(CronConfig(name="reportGeneration", cron_expression="0 7 * * *", description="研报生成频率"))

        # 推送渠道
        push_count = (await db.execute(select(func.count(PushChannel.id)))).scalar() or 0
        if push_count == 0:
            db.add(PushChannel(name="REST API", description="供下游系统调用", enabled=True))
            db.add(PushChannel(name="文件下载", description="Markdown / PDF 格式", enabled=True))

        # Agent 状态（与 pipeline.py 的 agent_map 对齐，流水线运行时动态更新）
        agent_count = (await db.execute(select(func.count(AgentStatus.id)))).scalar() or 0
        if agent_count == 0:
            db.add_all([
                AgentStatus(name="CollectorAgent", icon="bot", status="idle", detail="等待采集任务", status_text="就绪", color="gray"),
                AgentStatus(name="DedupAgent", icon="bot", status="idle", detail="等待去重任务", status_text="就绪", color="gray"),
                AgentStatus(name="ClusterAgent", icon="bot", status="idle", detail="等待聚类任务", status_text="就绪", color="gray"),
                AgentStatus(name="ResearchAgent", icon="bot", status="idle", detail="等待研报生成任务", status_text="就绪", color="gray"),
            ])

        # 系统指标（流水线运行后动态更新）
        metric_count = (await db.execute(select(func.count(SystemMetric.id)))).scalar() or 0
        if metric_count == 0:
            db.add_all([
                SystemMetric(label="今日采集", value="0", sub_value="篇", percentage=0, color="blue"),
                SystemMetric(label="去重保留率", value="0", sub_value="%", percentage=0, color="green"),
                SystemMetric(label="聚类簇数", value="0", sub_value="簇", percentage=0, color="amber"),
                SystemMetric(label="研报通过率", value="0", sub_value="%", percentage=0, color="orange"),
            ])

        await db.commit()
        print("[Seed] 系统基础配置初始化完成")


if __name__ == "__main__":
    asyncio.run(run_seed())
