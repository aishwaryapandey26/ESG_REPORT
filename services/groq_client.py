"""
services/groq_client.py
The ONLY file that touches the Groq API key.
Key is read from environment — never passed in from outside.
"""
import os
import json
import httpx
from fastapi import HTTPException
import logging

logger = logging.getLogger(__name__)

GROQ_API_KEY  = os.getenv("GROQ_API_KEY")
GROQ_API_URL  = "https://api.groq.com/openai/v1/chat/completions"
GROQ_MODEL    = os.getenv("GROQ_MODEL", "llama3-70b-8192")
GROQ_TIMEOUT  = float(os.getenv("GROQ_TIMEOUT_SECONDS", "60"))


def is_configured() -> bool:
    return bool(GROQ_API_KEY)


def current_model() -> str:
    return GROQ_MODEL


async def call(prompt: str, system: str, max_tokens: int = 2000) -> str:
    """
    Send a prompt to Groq and return the raw text response.
    Raises HTTPException on any failure so FastAPI handles it cleanly.
    """
    if not GROQ_API_KEY:
        raise HTTPException(
            status_code=503,
            detail="AI service is not configured. Contact the administrator."
        )

    payload = {
        "model": GROQ_MODEL,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user",   "content": prompt},
        ],
        "temperature": 0.3,
        "max_tokens": max_tokens,
    }

    try:
        async with httpx.AsyncClient(timeout=GROQ_TIMEOUT) as client:
            resp = await client.post(
                GROQ_API_URL,
                headers={
                    "Authorization": f"Bearer {GROQ_API_KEY}",
                    "Content-Type": "application/json",
                },
                json=payload,
            )
    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="AI service timed out. Try a shorter document.")
    except httpx.RequestError as e:
        raise HTTPException(status_code=502, detail=f"AI service unreachable: {e}")

    if resp.status_code != 200:
        err = {}
        try:
            err = resp.json().get("error", {})
        except Exception:
            pass
        msg = err.get("message", resp.text[:200])
        logger.error(f"Groq error {resp.status_code}: {msg}")
        raise HTTPException(status_code=502, detail=f"AI error: {msg}")

    content = resp.json()["choices"][0]["message"]["content"]
    logger.debug(f"Groq response ({len(content)} chars)")
    return content


def parse_json_response(raw: str) -> dict:
    """Strip markdown fences and parse JSON from Groq response."""
    cleaned = raw.strip()
    for fence in ("```json", "```"):
        if cleaned.startswith(fence):
            cleaned = cleaned[len(fence):]
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]
    cleaned = cleaned.strip()
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError as e:
        logger.error(f"JSON parse failed: {e}\nRaw: {raw[:300]}")
        raise HTTPException(status_code=500, detail="AI returned malformed JSON. Please retry.")
