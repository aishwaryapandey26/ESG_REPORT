"""
routes/webhook.py — POST /api/webhook (automated trigger from n8n)
"""
import logging
import os
import re
import json
from fastapi import APIRouter, HTTPException, Request
from services.pipeline import run_full_pipeline
from services.database import save_report

logger = logging.getLogger(__name__)
router = APIRouter()

WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET", "")


@router.post("/api/webhook")
async def webhook(request: Request):
    x_secret = request.headers.get("x-webhook-secret", "")
    if WEBHOOK_SECRET and x_secret != WEBHOOK_SECRET:
        raise HTTPException(status_code=401, detail="Invalid webhook secret.")

    body = await request.json()

    source   = body.get("source", "n8n")
    content  = body.get("content", "")
    filename = body.get("filename", "unknown")
    metadata = body.get("metadata", {})

    if isinstance(metadata, str):
        try:
            metadata = json.loads(metadata)
        except:
            metadata = {}

    company    = metadata.get("company", "")
    if not company or company.strip() == "Unknown":
        name = re.sub(r'\.(txt|pdf|csv|xlsx)$', '', filename, flags=re.IGNORECASE)
        name = re.sub(r'[_\-]', ' ', name)
        name = re.sub(r'\s*(ESG|Report|Data|Disclosure|2024|2025|2026).*', '', name, flags=re.IGNORECASE).strip()
        company = name if len(name) > 2 else "Unknown"

    industry   = metadata.get("industry", "General")
    year       = metadata.get("year", "2024")
    frameworks = metadata.get("frameworks", ["GRI", "SASB", "TCFD"])
    notes      = metadata.get("notes", "")

    if not content or len(content.strip()) < 20:
        raise HTTPException(status_code=400, detail="No content provided")

    logger.info(f"Webhook received: source={source} file={filename} company={company}")

    result = await run_full_pipeline(
        content=content,
        company=company,
        industry=industry,
        year=year,
        notes=notes,
        frameworks=frameworks
    )

    report_id = await save_report(result, source=source, filename=filename)
    result["_id"]       = report_id
    result["_source"]   = source
    result["_filename"] = filename

    return result