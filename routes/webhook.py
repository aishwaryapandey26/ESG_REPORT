"""
routes/webhook.py — POST /api/webhook (automated trigger from n8n)
Receives Gmail / Jira payloads, runs pipeline, saves to DB.
"""
import logging
import os
from fastapi import APIRouter, Header, HTTPException
from models.schemas import WebhookRequest
from services.pipeline import run_full_pipeline
from services.database import save_report

logger = logging.getLogger(__name__)
router = APIRouter()

WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET", "")


@router.post("/api/webhook")
async def webhook(
    req: WebhookRequest,
    x_webhook_secret: str = Header(default=""),
):
    if WEBHOOK_SECRET and x_webhook_secret != WEBHOOK_SECRET:
        raise HTTPException(status_code=401, detail="Invalid webhook secret.")

    logger.info(f"Webhook: source={req.source} file={req.filename}")

    result = await run_full_pipeline(
        content=req.content,
        company=req.metadata.get("company", "Unknown"),
        industry=req.metadata.get("industry", "General"),
        year=req.metadata.get("year", "2024"),
        notes=req.metadata.get("notes", ""),
        frameworks=req.metadata.get("frameworks", ["GRI", "SASB", "TCFD"]),
    )

    # Save to DB — this is what makes it appear in the UI
    report_id = await save_report(result, source=req.source, filename=req.filename or "")
    result["_id"]       = report_id
    result["_source"]   = req.source
    result["_filename"] = req.filename

    return result