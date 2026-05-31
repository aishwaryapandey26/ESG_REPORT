"""
services/pipeline.py
Orchestrates the 3-step ESG analysis pipeline.
Each step is a separate async function — easy to test individually.
"""
import os
import json
import logging
from typing import List
from services import groq_client

logger = logging.getLogger(__name__)

MAX_DOC_CHARS = int(os.getenv("MAX_DOC_CHARS", "8000"))


# ── Step 1: Classify ─────────────────────────────────

async def classify(content: str, company: str, industry: str, year: str, notes: str) -> dict:
    """Identify ESG categories, scores, and key metrics from raw text."""

    prompt = f"""You are an expert ESG data analyst. Analyse this ESG data for {company} ({industry} sector, {year}).

Document content:
{content[:MAX_DOC_CHARS]}

{f'Additional context from analyst: {notes}' if notes else ''}

Respond ONLY with valid JSON — no markdown fences, no explanation, no preamble:
{{
  "company": "{company}",
  "industry": "{industry}",
  "year": "{year}",
  "categories": {{
    "environmental": {{
      "score": <integer 0-100>,
      "items": ["list of specific environmental data points found"]
    }},
    "social": {{
      "score": <integer 0-100>,
      "items": ["list of specific social data points found"]
    }},
    "governance": {{
      "score": <integer 0-100>,
      "items": ["list of specific governance data points found"]
    }}
  }},
  "overallScore": <integer 0-100, weighted average>,
  "dataQuality": "High|Medium|Low",
  "keyMetrics": [
    {{"name": "metric name", "value": "numeric value", "unit": "unit string", "category": "E|S|G"}}
  ]
}}"""

    raw = await groq_client.call(
        prompt=prompt,
        system="You are an ESG data analyst. Respond only with valid JSON, nothing else.",
        max_tokens=1500,
    )
    result = groq_client.parse_json_response(raw)
    logger.info(f"Classify complete: score={result.get('overallScore')}")
    return result


# ── Step 2: Framework Mapping ─────────────────────────

async def map_frameworks(classified: dict, frameworks: List[str]) -> dict:
    """Map classified ESG data to specific reporting framework requirements."""

    frameworks_str = ", ".join(frameworks)
    framework_template = "\n    ".join([
        f'"{fw}": {{"coverage": <int 0-100>, "met": ["requirement met"], "missing": ["missing requirement"]}}'
        for fw in frameworks
    ])

    prompt = f"""You are an ESG framework specialist. Map this classified ESG data to frameworks: {frameworks_str}.

Classified data:
{json.dumps(classified, indent=2)}

For each framework, assess what percentage of key disclosure requirements are covered by the data provided.
Respond ONLY with valid JSON:
{{
  "frameworkCoverage": {{
    {framework_template}
  }}
}}"""

    raw = await groq_client.call(
        prompt=prompt,
        system="You are an ESG framework compliance specialist. Respond only with valid JSON.",
        max_tokens=1500,
    )
    result = groq_client.parse_json_response(raw)
    logger.info(f"Framework mapping complete: {list(result.get('frameworkCoverage', {}).keys())}")
    return result


# ── Step 3: Gap Detection ─────────────────────────────

async def detect_gaps(classified: dict, mapped: dict) -> dict:
    """Detect gaps, risks, greenwashing signals, and generate recommendations."""

    prompt = f"""You are a senior ESG audit specialist. Review this ESG data and framework mapping to identify gaps, risks, and opportunities.

Classification:
{json.dumps(classified, indent=2)}

Framework mapping:
{json.dumps(mapped, indent=2)}

Respond ONLY with valid JSON:
{{
  "findings": [
    {{
      "type": "gap|risk|recommendation|strength",
      "severity": "high|medium|low|positive",
      "title": "Concise finding title",
      "description": "Detailed explanation of the finding",
      "framework": "GRI 305-1|SASB|TCFD|null",
      "action": "Specific recommended action for the company"
    }}
  ],
  "totalGaps": <integer>,
  "totalRisks": <integer>,
  "greenwashingRisk": "High|Medium|Low|None",
  "summary": "2-3 sentence executive summary suitable for a board report"
}}"""

    raw = await groq_client.call(
        prompt=prompt,
        system="You are a senior ESG auditor. Respond only with valid JSON.",
        max_tokens=2000,
    )
    result = groq_client.parse_json_response(raw)
    logger.info(f"Gap detection complete: gaps={result.get('totalGaps')} risks={result.get('totalRisks')}")
    return result


# ── Full pipeline ─────────────────────────────────────

async def run_full_pipeline(
    content: str,
    company: str,
    industry: str,
    year: str,
    notes: str,
    frameworks: List[str],
) -> dict:
    """
    Run all 3 steps in sequence and merge results.
    Called by both /api/analyse (manual) and /api/webhook (automated via n8n).
    """
    classified = await classify(content, company, industry, year, notes)
    mapped     = await map_frameworks(classified, frameworks)
    gaps       = await detect_gaps(classified, mapped)

    return {
        **classified,
        **mapped,
        **gaps,
        "frameworks": frameworks,
        "model": groq_client.current_model(),
    }
