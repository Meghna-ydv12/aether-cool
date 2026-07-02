"""
AETHER-COOL — Drivers API
GET /api/drivers?zone_id={id}  → per-zone SHAP breakdown
GET /api/drivers/summary       → city-wide driver ranking
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from app.schemas import (
    DriverContribution,
    DriversResponse,
    DriversSummaryResponse,
)
from app.services.data_service import DataService

router = APIRouter(prefix="/api", tags=["drivers"])

# ── City-wide driver template ────────────────────────────────────
# Derived from SHAP analysis of the mock PINN model:
#   LST = 45 − 15·NDVI − 8·albedo + 5·BD − 3·SVF + noise
# Importance ≈ |coefficient| × std(feature)

_CITY_DRIVERS: list[dict] = [
    {
        "driver": "NDVI",
        "importance": 3.21,
        "direction": "negative",
        "description": "Vegetation cools via evapotranspiration; strongest single driver.",
    },
    {
        "driver": "Building Density",
        "importance": 2.14,
        "direction": "positive",
        "description": "Dense built-up areas trap heat and reduce ventilation.",
    },
    {
        "driver": "Albedo",
        "importance": 1.87,
        "direction": "negative",
        "description": "Higher surface reflectivity reduces absorbed solar radiation.",
    },
    {
        "driver": "Sky View Factor",
        "importance": 1.35,
        "direction": "negative",
        "description": "Open sky exposure aids longwave radiative cooling at night.",
    },
    {
        "driver": "Impervious Surface Fraction",
        "importance": 1.12,
        "direction": "positive",
        "description": "Sealed surfaces reduce evaporative cooling and increase runoff.",
    },
    {
        "driver": "Anthropogenic Heat",
        "importance": 0.89,
        "direction": "positive",
        "description": "Waste heat from vehicles, AC, and industry.",
    },
    {
        "driver": "Elevation",
        "importance": 0.42,
        "direction": "negative",
        "description": "Higher terrain tends to be slightly cooler (lapse rate effect).",
    },
]


@router.get(
    "/drivers/summary",
    response_model=DriversSummaryResponse,
    summary="City-wide SHAP driver ranking",
)
async def get_drivers_summary(
    city: str = Query("Delhi"),
) -> DriversSummaryResponse:
    grid = DataService.get_grid(city)
    return DriversSummaryResponse(
        city=grid["city"],
        total_zones=grid["total_zones"],
        drivers=[DriverContribution(**d) for d in _CITY_DRIVERS],
    )


@router.get(
    "/drivers",
    response_model=DriversResponse,
    summary="Per-zone SHAP driver breakdown",
)
async def get_drivers(
    zone_id: str = Query(..., description="Zone ID, e.g. Z-25-25"),
    city: str = Query("Delhi"),
) -> DriversResponse:
    zone = DataService.get_zone_data(city, zone_id)
    if zone is None:
        raise HTTPException(404, f"Zone '{zone_id}' not found in {city}")

    # Scale importances by the zone's own feature values so the
    # per-zone breakdown differs from the city-wide summary.
    ndvi = zone["ndvi"]
    albedo = zone["albedo"]
    bd = zone["building_density"]
    svf = zone["svf"]

    zone_drivers = [
        DriverContribution(
            driver="NDVI",
            importance=round(abs(-15.0 * ndvi), 2),
            direction="negative",
            description=f"Zone NDVI = {ndvi:.3f}",
        ),
        DriverContribution(
            driver="Building Density",
            importance=round(abs(5.0 * bd), 2),
            direction="positive",
            description=f"Zone building density = {bd:.3f}",
        ),
        DriverContribution(
            driver="Albedo",
            importance=round(abs(-8.0 * albedo), 2),
            direction="negative",
            description=f"Zone albedo = {albedo:.3f}",
        ),
        DriverContribution(
            driver="Sky View Factor",
            importance=round(abs(-3.0 * svf), 2),
            direction="negative",
            description=f"Zone SVF = {svf:.3f}",
        ),
        DriverContribution(
            driver="Impervious Surface Fraction",
            importance=round(1.12 * bd, 2),
            direction="positive",
            description="Correlated with building density.",
        ),
        DriverContribution(
            driver="Anthropogenic Heat",
            importance=round(0.89 * bd, 2),
            direction="positive",
            description="Estimated from population / built-up fraction.",
        ),
        DriverContribution(
            driver="Elevation",
            importance=0.42,
            direction="negative",
            description=f"Zone elevation ≈ {zone.get('elevation', 215):.0f} m",
        ),
    ]
    # Sort by importance descending
    zone_drivers.sort(key=lambda d: d.importance, reverse=True)

    return DriversResponse(
        zone_id=zone_id,
        drivers=zone_drivers,
        mean_lst=zone["lst"],
    )
