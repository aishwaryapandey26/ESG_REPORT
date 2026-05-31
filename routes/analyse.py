"""
routes/analyse.py
POST /api/analyse — triggered manually from the frontend.
Frontend sends document text + context; backend runs full pipeline.
"""
import logging
from fastapi import APIRouter
from models.schemas import AnalyseRequest
from services.pipeline import run_full_pipeline

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/api/analyse")
async def analyse(req: AnalyseRequest):
    """
    Accepts document text from frontend, runs 3-step Groq pipeline,
    returns structured ESG analysis. Groq key never leaves the server.
    """
    logger.info(f"Analyse request: company={req.company} industry={req.industry} frameworks={req.frameworks}")

    result = await run_full_pipeline(
        content=req.content,
        company=req.company,
        industry=req.industry,
        year=req.year,
        notes=req.notes,
        frameworks=req.frameworks,
    )

    return result
