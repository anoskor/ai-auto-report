"""推送分发模块 — Webhook / 文件导出真实推送"""

import httpx
from sqlalchemy import select

from app.database import async_session_factory
from app.models.topic import PushChannel


async def dispatch_report(report_id: int, channels: list[str] = None) -> dict:
    """向启用的推送渠道分发研报。

    有 webhook_url 的渠道走 HTTP POST；无 webhook_url 的渠道走文件导出（Markdown + PDF）。
    """
    from app.exporters.file_exporter import export_to_markdown, export_to_pdf

    async with async_session_factory() as db:
        stmt = select(PushChannel).where(PushChannel.enabled.is_(True))
        result = await db.execute(stmt)
        chs = result.scalars().all()

        results = []
        for ch in chs:
            if channels and ch.name not in channels:
                continue
            try:
                if ch.webhook_url:
                    async with httpx.AsyncClient(timeout=10) as client:
                        await client.post(
                            ch.webhook_url,
                            json={"reportId": report_id, "channel": ch.name},
                        )
                    results.append({"channel": ch.name, "success": True})
                else:
                    md_path = await export_to_markdown(report_id)
                    pdf_path = await export_to_pdf(report_id)
                    results.append({
                        "channel": ch.name,
                        "success": bool(md_path) and bool(pdf_path),
                        "path": md_path,
                        "pdfPath": pdf_path,
                    })
            except Exception as e:
                print(f"[Pusher] 渠道 {ch.name} 推送失败: {e}")
                results.append({"channel": ch.name, "success": False})

        return {
            "success": True,
            "channels": channels or [c.name for c in chs],
            "results": results,
        }
