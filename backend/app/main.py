"""
AETHER-COOL — FastAPI Application Entry-point

Run locally:
    uvicorn app.main:app --reload --port 8000
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from datetime import datetime, timezone

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.schemas import HealthResponse
from app.services.data_service import DataService

# ── Import routers ───────────────────────────────────────────────
from app.api.heat_map import router as heatmap_router
from app.api.drivers import router as drivers_router
from app.api.scenarios import router as scenarios_router
from app.api.optimize import router as optimize_router


# ── Lifespan (startup / shutdown) ────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Pre-warm caches on startup."""
    settings = get_settings()
    print(f"🌡️  {settings.APP_NAME} v{settings.APP_VERSION} starting up …")
    print(f"   City : {settings.DEFAULT_CITY}")
    print(f"   Grid : {settings.GRID_SIZE}×{settings.GRID_SIZE}")
    print(f"   Mock : {settings.USE_MOCK_MODEL}")

    # Pre-generate the default city grid so first request is instant
    grid = DataService.get_grid(settings.DEFAULT_CITY)
    print(f"   ✓ Grid ready — {grid['total_zones']} zones cached")

    yield  # ← app is running

    print("🛑  AETHER-COOL shutting down.")


# ── Create app ───────────────────────────────────────────────────

settings = get_settings()

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description=(
        "Geospatial AI platform for urban heat island analysis "
        "and mitigation strategy optimisation."
    ),
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# ── CORS ─────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Include routers ──────────────────────────────────────────────
app.include_router(heatmap_router)
app.include_router(drivers_router)
app.include_router(scenarios_router)
app.include_router(optimize_router)


# ── Health endpoint (registered directly) ────────────────────────

@app.get(
    "/api/health",
    response_model=HealthResponse,
    tags=["health"],
    summary="Health check",
)
async def health() -> HealthResponse:
    return HealthResponse(
        status="healthy",
        version=settings.APP_VERSION,
        model_loaded=settings.USE_MOCK_MODEL,
        city=settings.DEFAULT_CITY,
        grid_size=settings.GRID_SIZE,
        timestamp=datetime.now(timezone.utc),
    )
