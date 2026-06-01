import logging
from fastapi import APIRouter, HTTPException, Request
from services.pipeline import run_full_pipeline
from services.database import save_report

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("/api/webhook")
async def webhook(request: Request):
    try:
        body = await request.json()

        source   = body.get("source", "n8n")
        content  = body.get("content", "")
        filename = body.get("filename", "unknown")
        metadata = body.get("metadata", {})

        # Extract company from metadata or filename
        company  = metadata.get("company", "")
        if not company or company == "Unknown":
            # Try from filename
            import re
            name = re.sub(r'\.(txt|pdf|csv|xlsx)$', '', filename, flags=re.IGNORECASE)
            name = re.sub(r'[_\-]', ' ', name)
            name = re.sub(r'\s*(ESG|Report|Data|Disclosure|2024|2025|2026).*', '', name, flags=re.IGNORECASE).strip()
            company = name if len(name) > 2 else "Unknown"

        industry   = metadata.get("industry", "General")
        year       = metadata.get("year", "2024")
        frameworks = metadata.get("frameworks", ["GRI", "SASB", "TCFD"])

        if not content or len(content.strip()) < 20:
            raise HTTPException(status_code=400, detail="No content provided")

        logger.info(f"Webhook received: source={source} file={filename} company={company}")

        result = await run_full_pipeline(
            content=content,
            company=company,
            industry=industry,
            year=year,
            frameworks=frameworks
        )

        await save_report(result, source=source, filename=filename)
        return {"status": "ok", "report_id": result.get("reportId")}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Webhook error: {e}")
        raise HTTPException(status_code=502, detail=str(e))