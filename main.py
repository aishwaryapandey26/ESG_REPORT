
"""
main.py — ClarityESG FastAPI entry point.
Only job: configure the app, register routers, add middleware.
All logic lives in routes/ and services/.
"""

from dotenv import load_dotenv
load_dotenv()
import os
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routes.health   import router as health_router
from routes.analyse  import router as analyse_router
from routes.webhook  import router as webhook_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)

app = FastAPI(
    title="ClarityESG API",
    description="ESG Intelligence Pipeline — Groq-powered, n8n-connected",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# ── CORS ──────────────────────────────────────────────
# Set ALLOWED_ORIGINS in Railway env vars → your Netlify URL
# e.g. "https://clarityesg.netlify.app,http://localhost:5500"
_origins_raw = os.getenv("ALLOWED_ORIGINS", "http://localhost:5500,http://127.0.0.1:5500")
ALLOWED_ORIGINS = [o.strip() for o in _origins_raw.split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ───────────────────────────────────────────
app.include_router(health_router)
app.include_router(analyse_router)
app.include_router(webhook_router)
