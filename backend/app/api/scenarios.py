"""
AETHER-COOL — Scenarios / Simulate API

POST /api/simulate   → apply interventions, return per-zone ΔT
GET  /api/scenarios   → list saved scenarios
GET  /api/trends      → diurnal & seasonal LST trends for a zone
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, HTTPException, Query

from app.schemas import (
    Intervention,
    ScenarioSummary,
    ScenariosListResponse,
    SimulateRequest,
    SimulateResponse,
    TrendPoint,
    TrendsResponse,
    ZoneDelta,
)
from app.services.data_service import DataService
from app.services.ml_service import MLService

router = APIRouter(prefix="/api", tags=["scenarios"])

# In-memory scenario store (replaced by DB / Redis later)
_saved_scenarios: list[dict[str, Any]] = []


def _seed_scenarios() -> None:
    """Pre-populate a few sample scenarios so GET /api/scenarios is never empty."""
    if _saved_scenarios:
        return
    _saved_scenarios.extend([
        {
            "id": "scn-001",
            "name": "Green Delhi 2030",
            "city": "Delhi",
            "created_at": datetime(2024, 11, 10, 9, 30, tzinfo=timezone.utc),
            "total_zones": 120,
            "mean_delta_t": -2.8,
            "budget_used": 4500.0,
            "interventions_count": 3,
        },
        {
            "id": "scn-002",
            "name": "Cool Roofs Pilot",
            "city": "Delhi",
            "created_at": datetime(2024, 12, 1, 14, 0, tzinfo=timezone.utc),
            "total_zones": 45,
            "mean_delta_t": -1.4,
            "budget_used": 1800.0,
            "interventions_count": 1,
        },
        {
            "id": "scn-003",
            "name": "Equity-Optimised Mix",
            "city": "Delhi",
            "created_at": datetime(2025, 1, 15, 11, 15, tzinfo=timezone.utc),
            "total_zones": 200,
            "mean_delta_t": -3.5,
            "budget_used": 7200.0,
            "interventions_count": 5,
        },
    ])


# ── POST /api/simulate ──────────────────────────────────────────


@router.post(
    "/simulate",
    response_model=SimulateResponse,
    summary="Simulate intervention impact",
    description=(
        "Apply one or more interventions to selected zones and compute "
        "the predicted temperature change using physics-based formulas."
    ),
)
async def simulate(req: SimulateRequest) -> SimulateResponse:
    grid = DataService.get_grid(req.city)
    all_zone_ids = set(grid["zones"].keys())

    zone_deltas: list[ZoneDelta] = []

    for intervention in req.interventions:
        target_ids = (
            set(intervention.zone_ids) & all_zone_ids
            if intervention.zone_ids
            else all_zone_ids
        )
        if not target_ids:
            continue

        for zid in sorted(target_ids):
            zone = grid["zones"][zid]
            dt = MLService.compute_delta_t(
                intervention.type.value,
                intervention.intensity,
                zone,
            )
            # Check if we already have a delta for this zone (stacking)
            existing = next((d for d in zone_deltas if d.zone_id == zid), None)
            if existing:
                existing.delta_t = round(existing.delta_t + dt, 3)
                existing.predicted_lst = round(
                    existing.original_lst + existing.delta_t, 2
                )
                existing.interventions_applied.append(intervention.type.value)
            else:
                zone_deltas.append(
                    ZoneDelta(
                        zone_id=zid,
                        original_lst=zone["lst"],
                        predicted_lst=round(zone["lst"] + dt, 2),
                        delta_t=round(dt, 3),
                        interventions_applied=[intervention.type.value],
                    )
                )

    if not zone_deltas:
        raise HTTPException(400, "No valid zones matched the intervention targets.")

    deltas = [d.delta_t for d in zone_deltas]
    mean_dt = round(sum(deltas) / len(deltas), 3)
    max_dt = round(min(deltas), 3)  # most negative = maximum cooling

    # Auto-save as a scenario
    scenario_id = f"scn-{uuid.uuid4().hex[:6]}"
    _saved_scenarios.append({
        "id": scenario_id,
        "name": f"Simulation {scenario_id}",
        "city": req.city,
        "created_at": datetime.now(timezone.utc),
        "total_zones": len(zone_deltas),
        "mean_delta_t": mean_dt,
        "budget_used": 0.0,
        "interventions_count": len(req.interventions),
    })

    return SimulateResponse(
        city=req.city,
        total_zones_affected=len(zone_deltas),
        mean_delta_t=mean_dt,
        max_delta_t=max_dt,
        zone_deltas=zone_deltas,
    )


# ── GET /api/scenarios ───────────────────────────────────────────


@router.get(
    "/scenarios",
    response_model=ScenariosListResponse,
    summary="List saved scenarios",
)
async def list_scenarios() -> ScenariosListResponse:
    _seed_scenarios()
    return ScenariosListResponse(
        scenarios=[ScenarioSummary(**s) for s in _saved_scenarios]
    )


# ── GET /api/trends ──────────────────────────────────────────────


@router.get(
    "/trends",
    response_model=TrendsResponse,
    summary="Diurnal & seasonal LST trends for a zone",
)
async def get_trends(
    zone_id: str = Query(..., description="Zone ID"),
    city: str = Query("Delhi"),
) -> TrendsResponse:
    zone = DataService.get_zone_data(city, zone_id)
    if zone is None:
        raise HTTPException(404, f"Zone '{zone_id}' not found")

    base_lst = zone["lst"]
    ndvi = zone["ndvi"]

    # ── Diurnal curve (24 hours, 3-hour steps) ──────────────────
    import math

    diurnal: list[TrendPoint] = []
    for h in range(0, 24, 3):
        # Peak around 14:00, trough around 05:00
        phase = 2 * math.pi * (h - 14) / 24
        amplitude = 6.0 * (1 - 0.3 * ndvi)  # vegetation dampens amplitude
        lst = base_lst + amplitude * math.cos(phase) - 3.0
        diurnal.append(TrendPoint(
            timestamp=f"{h:02d}:00",
            lst=round(lst, 2),
            ndvi=round(ndvi + 0.02 * math.sin(phase), 4),
        ))

    # ── Seasonal curve (12 months) ──────────────────────────────
    months = [
        "Jan", "Feb", "Mar", "Apr", "May", "Jun",
        "Jul", "Aug", "Sep", "Oct", "Nov", "Dec",
    ]
    # Delhi-like seasonal pattern: peak in May–Jun, cooler Dec–Jan
    seasonal_offsets = [-8, -5, -1, 3, 6, 7, 4, 3, 2, -1, -5, -8]

    seasonal: list[TrendPoint] = []
    for m, offset in zip(months, seasonal_offsets):
        lst = base_lst + offset + 0.5 * (1 - ndvi)
        seasonal.append(TrendPoint(
            timestamp=m,
            lst=round(lst, 2),
            ndvi=round(ndvi + 0.08 * math.cos(2 * math.pi * (months.index(m) - 8) / 12), 4),
        ))

    return TrendsResponse(zone_id=zone_id, diurnal=diurnal, seasonal=seasonal)
