"""
services/database.py
SQLite database for storing all processed ESG reports.
Works on Railway with a persistent volume, or in-memory for testing.
"""
import os
import json
from datetime import datetime
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import String, Integer, Text, DateTime, select
from sqlalchemy.ext.asyncio import async_sessionmaker

DB_PATH = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./reports.db")

engine = create_async_engine(DB_PATH, echo=False)
SessionLocal = async_sessionmaker(engine, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


class Report(Base):
    __tablename__ = "reports"

    id:            Mapped[int]      = mapped_column(Integer, primary_key=True, autoincrement=True)
    company:       Mapped[str]      = mapped_column(String(255), default="Unknown")
    industry:      Mapped[str]      = mapped_column(String(255), default="General")
    year:          Mapped[str]      = mapped_column(String(10),  default="2024")
    overall_score: Mapped[int]      = mapped_column(Integer,     default=0)
    data_quality:  Mapped[str]      = mapped_column(String(50),  default="")
    summary:       Mapped[str]      = mapped_column(Text,        default="")
    frameworks:    Mapped[str]      = mapped_column(Text,        default="[]")   # JSON array
    findings:      Mapped[str]      = mapped_column(Text,        default="[]")   # JSON array
    full_result:   Mapped[str]      = mapped_column(Text,        default="{}")   # full JSON
    source:        Mapped[str]      = mapped_column(String(50),  default="manual")  # manual|gmail|jira
    filename:      Mapped[str]      = mapped_column(String(255), default="")
    created_at:    Mapped[datetime] = mapped_column(DateTime,    default=datetime.utcnow)


async def init_db():
    """Create tables on startup."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def save_report(result: dict, source: str = "manual", filename: str = "") -> int:
    """Save a pipeline result to the database. Returns the new report ID."""
    async with SessionLocal() as session:
        report = Report(
            company       = result.get("company", "Unknown"),
            industry      = result.get("industry", "General"),
            year          = result.get("year", "2024"),
            overall_score = result.get("overallScore", 0),
            data_quality  = result.get("dataQuality", ""),
            summary       = result.get("summary", ""),
            frameworks    = json.dumps(result.get("frameworks", [])),
            findings      = json.dumps(result.get("findings", [])),
            full_result   = json.dumps(result),
            source        = source,
            filename      = filename,
        )
        session.add(report)
        await session.commit()
        await session.refresh(report)
        return report.id


async def get_all_reports(limit: int = 50) -> list[dict]:
    """Fetch all reports ordered by newest first."""
    async with SessionLocal() as session:
        result = await session.execute(
            select(Report).order_by(Report.created_at.desc()).limit(limit)
        )
        rows = result.scalars().all()
        return [_row_to_dict(r) for r in rows]


async def get_report_by_id(report_id: int) -> dict | None:
    """Fetch a single report by ID."""
    async with SessionLocal() as session:
        result = await session.execute(select(Report).where(Report.id == report_id))
        row = result.scalar_one_or_none()
        return _row_to_dict(row) if row else None


def _row_to_dict(r: Report) -> dict:
    full = json.loads(r.full_result or "{}")
    full["_id"]       = r.id
    full["_source"]   = r.source
    full["_filename"] = r.filename
    full["_created"]  = r.created_at.isoformat()
    return full