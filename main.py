"""
main.py — ClarityESG FastAPI entry point.
"""
import os
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from services.database   import init_db
from routes.health       import router as health_router
from routes.analyse      import router as analyse_router
from routes.webhook      import router as webhook_router
from routes.reports      import router as reports_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()   # create DB tables on startup
    yield


app = FastAPI(
    title="ClarityESG API",
    version="2.0.0",
    lifespan=lifespan,
)

_origins_raw = os.getenv("ALLOWED_ORIGINS", "http://localhost:5500,http://127.0.0.1:5500")
ALLOWED_ORIGINS = [o.strip() for o in _origins_raw.split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router)
app.include_router(analyse_router)
app.include_router(webhook_router)
app.include_router(reports_router)