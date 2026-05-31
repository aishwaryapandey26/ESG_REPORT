"""
routes/reports.py — GET /api/reports
Returns all stored reports (manual + gmail + jira) for the frontend feed.
"""
from fastapi import APIRouter
from services.database import get_all_reports, get_report_by_id

router = APIRouter()


@router.get("/api/reports")
async def list_reports(limit: int = 50):
    """Return all reports newest first."""
    reports = await get_all_reports(limit=limit)
    return {"reports": reports, "total": len(reports)}


@router.get("/api/reports/{report_id}")
async def get_report(report_id: int):
    """Return a single report by ID."""
    report = await get_report_by_id(report_id)
    if not report:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Report not found")
    return report