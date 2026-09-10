"""WebSocket 实时通信"""

import asyncio
import json
from fastapi import WebSocket, WebSocketDisconnect
from sqlalchemy import select
from app.database import async_session_factory
from app.models.workflow import AgentStatus, SystemLog, WorkflowRun


class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        for conn in self.active_connections:
            try:
                await conn.send_json(message)
            except Exception:
                pass

    async def send_personal(self, message: dict, websocket: WebSocket):
        try:
            await websocket.send_json(message)
        except Exception:
            pass


manager = ConnectionManager()


async def realtime_push(websocket: WebSocket):
    """实时推送：工作流进度、Agent状态、日志（数据来自数据库）"""
    last_run_id = None
    last_pct = -1
    last_agents_snapshot = ""
    last_log_id = 0

    while True:
        try:
            async with async_session_factory() as db:
                # 最新工作流运行进度
                run = (await db.execute(
                    select(WorkflowRun).order_by(WorkflowRun.created_at.desc()).limit(1)
                )).scalar()
                if run:
                    pct = run.percentage or 0
                    if run.id != last_run_id or pct != last_pct:
                        await manager.send_personal({
                            "type": "workflow:progress",
                            "data": {"currentStage": run.current_stage or "", "percentage": pct},
                        }, websocket)
                        last_run_id = run.id
                        last_pct = pct

                # Agent 状态
                agents_result = await db.execute(select(AgentStatus).order_by(AgentStatus.id))
                agents = [
                    {"name": a.name, "icon": a.icon, "status": a.status, "detail": a.detail,
                     "statusText": a.status_text, "color": a.color}
                    for a in agents_result.scalars().all()
                ]
                snapshot = json.dumps(agents, ensure_ascii=False, sort_keys=True)
                if snapshot != last_agents_snapshot:
                    for a in agents:
                        await manager.send_personal({"type": "agent:status", "data": a}, websocket)
                    last_agents_snapshot = snapshot

                # 新增日志
                logs_result = await db.execute(
                    select(SystemLog).where(SystemLog.id > last_log_id)
                    .order_by(SystemLog.id.asc()).limit(20)
                )
                logs = logs_result.scalars().all()
                for l in logs:
                    await manager.send_personal({
                        "type": "log:new",
                        "data": {"time": l.time, "level": l.level, "message": l.message},
                    }, websocket)
                    last_log_id = l.id
        except Exception:
            pass

        await asyncio.sleep(3)


async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    push_task = asyncio.create_task(realtime_push(websocket))
    try:
        while True:
            data = await websocket.receive_text()
            msg = json.loads(data)
            if msg.get("type") == "ping":
                await manager.send_personal({"type": "pong"}, websocket)
    except WebSocketDisconnect:
        push_task.cancel()
    except json.JSONDecodeError:
        pass
    finally:
        manager.disconnect(websocket)
