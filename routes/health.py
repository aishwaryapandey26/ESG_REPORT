"""routes/health.py — /health endpoint"""
from fastapi import APIRouter
from models.schemas import HealthResponse, ModelsResponse, ModelInfo
from services import groq_client

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def health():
    return HealthResponse(
        status="ok",
        ai_configured=groq_client.is_configured(),
        model=groq_client.current_model(),
    )


@router.get("/api/models", response_model=ModelsResponse)
async def models():
    """Return available models — no secrets exposed."""
    return ModelsResponse(
        current=groq_client.current_model(),
        available=[
            ModelInfo(id="llama3-70b-8192",    label="LLaMA 3 70B",   note="Best quality · Recommended"),
            ModelInfo(id="llama3-8b-8192",     label="LLaMA 3 8B",    note="Fastest · Good for testing"),
            ModelInfo(id="mixtral-8x7b-32768", label="Mixtral 8x7B",  note="Longest context window"),
            ModelInfo(id="gemma2-9b-it",       label="Gemma 2 9B",    note="Balanced · Google"),
        ],
    )
