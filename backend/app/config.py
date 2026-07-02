"""
AETHER-COOL — Application Configuration
Loads settings from environment variables with sensible defaults.
"""

from __future__ import annotations

import os
from functools import lru_cache
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Central configuration sourced from environment / .env file."""

    # ── Application ──────────────────────────────────────────────
    APP_NAME: str = "AETHER-COOL"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = True

    # ── Server ───────────────────────────────────────────────────
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # ── CORS ─────────────────────────────────────────────────────
    CORS_ORIGINS: list[str] = ["*"]

    # ── Redis (optional — gracefully degrades to in-memory) ─────
    REDIS_URL: str = "redis://localhost:6379/0"

    # ── Data paths ───────────────────────────────────────────────
    SAMPLE_DATA_DIR: str = os.path.join(
        os.path.dirname(__file__), "..", "..", "data", "sample"
    )

    # ── ML / PINN model ─────────────────────────────────────────
    PINN_MODEL_PATH: str = ""
    USE_MOCK_MODEL: bool = True

    # ── City defaults ────────────────────────────────────────────
    DEFAULT_CITY: str = "Delhi"
    DEFAULT_LAT: float = 28.6139
    DEFAULT_LON: float = 77.2090
    GRID_SIZE: int = 50  # 50×50 grid → 2500 cells

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


@lru_cache()
def get_settings() -> Settings:
    """Return cached singleton settings instance."""
    return Settings()
