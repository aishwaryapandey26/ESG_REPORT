"""
routes/analyse.py — POST /api/analyse (manual trigger from frontend)
Saves result to database so it appears in the reports feed.
"""
import logging
from fastapi import APIRouter
from models.schemas import AnalyseRequest
from services.pipeline import run_full_pipeline
from services.database import save_report

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/api/analyse")
async def analyse(req: AnalyseRequest):
    logger.info(f"Analyse: company={req.company} frameworks={req.frameworks}")

    result = await run_full_pipeline(
        content=req.content,
        company=req.company,
        industry=req.industry,
        year=req.year,
        notes=req.notes,
        frameworks=req.frameworks,
    )

    # Save to DB so it shows in the reports feed
    report_id = await save_report(result, source="manual")
    result["_id"] = report_id
    result["_source"] = "manual"

    return result