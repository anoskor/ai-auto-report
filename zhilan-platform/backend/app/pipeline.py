"""流水线编排 — 采集→去重→聚类→摘要→研报→简报→推送

串联真实数据流水线，并实时更新 workflow_runs 的七步状态与 Agent/日志。
"""

import asyncio
from datetime import datetime

from sqlalchemy import select

from app.database import async_session_factory
from app.models.report import ResearchReport
from app.models.workflow import WorkflowRun, AgentStatus, SystemLog, SystemMetric

# 全局锁，防止并发执行多条流水线
_pipeline_lock = asyncio.Lock()

_STEPS = ["采集", "预处理", "去重", "聚类", "摘要", "审核", "推送"]


def _step(label: str, status: str, detail: str = "") -> dict:
    """构造流水线步骤（与前端 PipelineStepOut 对齐）"""
    if status == "done":
        icon, bg, border, text = "check-circle", "bg-green-50", "border-green-200", "text-green-600"
    elif status == "running":
        icon, bg, border, text = "loader", "bg-amber-50", "border-amber-200", "text-amber-600"
    else:
        icon, bg, border, text = "clock", "bg-slate-50", "border-slate-200", "text-slate-400"
    return {
        "label": label, "status": status, "icon": icon, "detail": detail,
        "bgColor": bg, "borderColor": border, "textColor": text,
    }


async def _set_step(run_id: int, label: str, status: str, pct: int, detail: str):
    """更新工作流某一步的状态与总进度"""
    async with async_session_factory() as db:
        run = (await db.execute(select(WorkflowRun).where(WorkflowRun.id == run_id))).scalar()
        if not run:
            return
        # 深拷贝每个步骤 dict，确保 JSON 字段的变更能被 SQLAlchemy 检测到
        steps = []
        for s in (run.pipeline_steps or []):
            if s.get("label") == label:
                steps.append(_step(label, status, detail))
            else:
                steps.append(dict(s))
        run.pipeline_steps = steps
        run.current_stage = label
        run.percentage = pct
        await db.commit()


async def run_pipeline() -> dict:
    """执行一次完整数据流水线（后台运行，非阻塞）。"""
    if _pipeline_lock.locked():
        print("[Pipeline] 已有流水线在运行，跳过本次")
        return {"skipped": True}

    async with _pipeline_lock:
        async with async_session_factory() as db:
            run = WorkflowRun(
                status="running",
                current_stage="采集",
                percentage=0,
                pipeline_steps=[_step(s, "pending") for s in _STEPS],
                started_at=datetime.now(),
            )
            db.add(run)
            await db.commit()
            run_id = run.id

        # 1. 采集
        await _set_step(run_id, "采集", "running", 10, "正在抓取 RSS 源...")
        from app.collectors.news_collector import run_collection
        collected = await run_collection()
        await _set_step(run_id, "采集", "done", 20, f"✅ {collected}篇")

        # 2. 预处理（去重前清洗，随采集同步完成）
        await _set_step(run_id, "预处理", "done", 30, f"✅ {collected}篇")

        # 3. 去重
        await _set_step(run_id, "去重", "running", 40, "向量去重中...")
        from app.processors.dedup import deduplicate_articles
        dedup_result = await deduplicate_articles()
        await _set_step(run_id, "去重", "done", 50, f"✅ {dedup_result['unique']}篇")

        # 4. 聚类
        await _set_step(run_id, "聚类", "running", 60, "向量聚类中...")
        from app.processors.clusterer import cluster_articles
        cluster_result = await cluster_articles()
        await _set_step(run_id, "聚类", "done", 70, f"✅ {cluster_result['clusters']}簇")

        # 4.5 向量索引（RAG 阶段2，静默降级：ES 未连接时跳过）
        try:
            from app.rag.indexer import index_pending_articles
            rag_result = await index_pending_articles()
            print(f"[RAG] 向量索引: {rag_result['indexed']}篇文章/{rag_result['chunks']}chunks")
        except Exception as e:
            print(f"[RAG] 向量索引失败(降级跳过): {e}")

        # 5. 摘要 + 研报生成（LLM）
        await _set_step(run_id, "摘要", "running", 80, "LLM 生成摘要与研报...")
        from app.generators.report_generator import run_generation
        gen_result = await run_generation()
        await _set_step(run_id, "摘要", "done", 90, f"✅ {gen_result['generated']}篇研报")

        # 6. 审核
        await _set_step(run_id, "审核", "done", 95, f"✅ {gen_result['passed']}篇通过")

        # 7. 推送
        pushed = 0
        if gen_result.get("generated", 0) > 0:
            await _set_step(run_id, "推送", "running", 97, "推送研报...")
            from app.dispatchers.pusher import dispatch_report
            async with async_session_factory() as db:
                reports = (await db.execute(
                    select(ResearchReport).order_by(ResearchReport.id.desc()).limit(gen_result["generated"])
                )).scalars().all()
                for r in reports:
                    await dispatch_report(r.id)
                    pushed += 1
        await _set_step(run_id, "推送", "done", 100, f"✅ {pushed}篇")

        # 收尾：更新工作流状态 + Agent + 日志
        async with async_session_factory() as db:
            run = (await db.execute(select(WorkflowRun).where(WorkflowRun.id == run_id))).scalar()
            if run:
                run.status = "completed"
                run.percentage = 100
                run.completed_at = datetime.now()

            agent_map = {
                "CollectorAgent": f"已处理: {collected}篇",
                "DedupAgent": f"已处理: {dedup_result['unique']}篇",
                "ClusterAgent": f"已处理: {cluster_result['clusters']}簇",
                "ResearchAgent": f"已生成: {gen_result['generated']}篇研报",
            }
            agents = (await db.execute(select(AgentStatus))).scalars().all()
            for a in agents:
                if a.name in agent_map:
                    a.detail = agent_map[a.name]
                    a.status = "done"
                    a.status_text = "✅ 就绪"
                    a.color = "green"

            # 更新系统指标（基于本次流水线真实结果）
            total = max(collected, 1)
            dedup_rate = int(dedup_result['unique'] / total * 100)
            cluster_pct = min(100, cluster_result['clusters'] * 10)
            generated = gen_result.get("generated", 0)
            passed = gen_result.get("passed", 0)
            pass_rate = int(passed / max(generated, 1) * 100)
            metric_map = {
                "今日采集": (str(collected), "篇", min(100, collected * 5), "blue"),
                "去重保留率": (f"{dedup_rate}", "%", dedup_rate, "green"),
                "聚类簇数": (str(cluster_result['clusters']), "簇", cluster_pct, "amber"),
                "研报通过率": (f"{pass_rate}", "%", pass_rate, "orange"),
            }
            metrics = (await db.execute(select(SystemMetric))).scalars().all()
            for m in metrics:
                if m.label in metric_map:
                    v, sub, pct, color = metric_map[m.label]
                    m.value = v
                    m.sub_value = sub
                    m.percentage = pct
                    m.color = color

            db.add(SystemLog(
                time=datetime.now().strftime("%H:%M:%S"),
                level="SUCCESS",
                message=(
                    f"流水线完成：采集{collected}篇，去重后{dedup_result['unique']}篇，"
                    f"{cluster_result['clusters']}簇，生成{gen_result['generated']}篇研报"
                ),
                agent_name="Pipeline",
            ))
            await db.commit()

        return {
            "collected": collected,
            "dedup": dedup_result,
            "clusters": cluster_result,
            "generation": gen_result,
            "pushed": pushed,
        }
