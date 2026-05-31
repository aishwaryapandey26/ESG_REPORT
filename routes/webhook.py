"""
routes/webhook.py
POST /api/webhook — called automatically by n8n.
n8n watches Gmail / Slack / Jira, extracts text, posts here.
No human needed — fully automated intake.
"""
import logging
from fastapi import APIRouter, Header, HTTPException
import os
from models.schemas import WebhookRequest
from services.pipeline import run_full_pipeline

logger = logging.getLogger(__name__)
router = APIRouter()

# Optional shared secret — set WEBHOOK_SECRET in Railway env vars
# n8n adds it as X-Webhook-Secret header
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET", "")


@router.post("/api/webhook")
async def webhook(
    req: WebhookRequest,
    x_webhook_secret: str = Header(default=""),
):
    """
    Receives ESG document text from n8n (Gmail/Slack/Jira triggers).
    Runs full pipeline automatically and returns results.
    n8n can then push those results to Notion/Slack/email.
    """
    # Validate shared secret if configured
    if WEBHOOK_SECRET and x_webhook_secret != WEBHOOK_SECRET:
        raise HTTPException(status_code=401, detail="Invalid webhook secret.")

    logger.info(
        f"n8n webhook received: source={req.source} "
        f"file={req.filename} company={req.metadata.get('company','unknown')}"
    )

    result = await run_full_pipeline(
        content=req.content,
        company=req.metadata.get("company", "Unknown"),
        industry=req.metadata.get("industry", "General"),
        year=req.metadata.get("year", "2024"),
        notes=req.metadata.get("notes", ""),
        frameworks=req.metadata.get("frameworks", ["GRI", "SASB", "TCFD"]),
    )

    # Include source metadata in response so n8n can log/route it
    result["_source"] = req.source
    result["_filename"] = req.filename

    return result
