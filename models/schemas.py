"""
All Pydantic request/response models for ClarityESG API.
Keep all data contracts here — one source of truth.
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any


# ── Inbound ──────────────────────────────────────────

class AnalyseRequest(BaseModel):
    content: str = Field(..., description="Raw extracted document text")
    company: Optional[str] = Field("Unknown", description="Company or client name")
    industry: Optional[str] = Field("General", description="Industry / sector")
    year: Optional[str] = Field("2024", description="Reporting year")
    notes: Optional[str] = Field("", description="Extra analyst instructions")
    frameworks: Optional[List[str]] = Field(
        ["GRI", "SASB", "TCFD"],
        description="Target ESG frameworks to map against"
    )


class WebhookRequest(BaseModel):
    """Payload shape that n8n sends to /api/webhook."""
    source: str = Field(..., description="gmail | slack | jira | manual")
    content: str = Field(..., description="Extracted document text")
    filename: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = Field(
        default_factory=dict,
        description="company, industry, year, frameworks passed by n8n"
    )


# ── Outbound ─────────────────────────────────────────

class KeyMetric(BaseModel):
    name: str
    value: str
    unit: Optional[str] = None
    category: str   # E | S | G


class CategoryDetail(BaseModel):
    score: int
    items: List[str]


class Categories(BaseModel):
    environmental: CategoryDetail
    social: CategoryDetail
    governance: CategoryDetail


class Finding(BaseModel):
    type: str       # gap | risk | recommendation | strength
    severity: str   # high | medium | low | positive
    title: str
    description: str
    framework: Optional[str] = None
    action: Optional[str] = None


class FrameworkData(BaseModel):
    coverage: int
    met: List[str]
    missing: List[str]


class AnalyseResponse(BaseModel):
    company: str
    industry: str
    year: str
    categories: Categories
    overallScore: int
    dataQuality: str
    keyMetrics: List[KeyMetric]
    frameworkCoverage: Dict[str, FrameworkData]
    findings: List[Finding]
    totalGaps: int
    totalRisks: int
    greenwashingRisk: str
    summary: str
    frameworks: List[str]
    model: str


class HealthResponse(BaseModel):
    status: str
    ai_configured: bool
    model: str


class ModelInfo(BaseModel):
    id: str
    label: str
    note: str


class ModelsResponse(BaseModel):
    current: str
    available: List[ModelInfo]
