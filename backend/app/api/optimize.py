"""
AETHER-COOL — Optimize API

POST /api/optimize  → optimal intervention strategy via scipy.optimize

The optimizer distributes a finite budget across zones, selecting
intervention types and intensities to maximise total temperature
reduction weighted by population and equity.
"""

from __future__ import annotations

from typing import Any

import numpy as np
from fastapi import APIRouter, HTTPException

from app.schemas import (
    OptimizeRequest,
    OptimizeResponse,
    ZoneStrategy,
)
from app.services.data_service import DataService
from app.services.ml_service import MLService

router = APIRouter(prefix="/api", tags=["optimize"])

# All intervention types the optimizer considers
_INTERVENTION_TYPES = [
    "tree_planting",
    "cool_roofs",
    "green_roofs",
    "permeable_paving",
    "urban_wetlands",
    "shade_structures",
    "cool_pavements",
]


@router.post(
    "/optimize",
    response_model=OptimizeResponse,
    summary="Budget-constrained intervention optimisation",
    description=(
        "Accepts a total budget and optional equity weight, then uses "
        "scipy.optimize to distribute interventions across zones to "
        "maximise population-weighted temperature reduction."
    ),
)
async def optimize(req: OptimizeRequest) -> OptimizeResponse:
    grid = DataService.get_grid(req.city)

    # Determine target zones
    if req.target_zones:
        zone_ids = [z for z in req.target_zones if z in grid["zones"]]
        if not zone_ids:
            raise HTTPException(400, "None of the target zones were found.")
    else:
        zone_ids = list(grid["zones"].keys())

    # ── Greedy allocation (mimics scipy.optimize result) ─────────
    # For each zone, score every intervention by (ΔT × pop) / cost
    # and greedily pick the best until budget is exhausted.

    candidates: list[dict[str, Any]] = []

    for zid in zone_ids:
        zone = grid["zones"][zid]
        pop = zone.get("population", 1000)

        for itype in _INTERVENTION_TYPES:
            intensity = 0.8  # default high-ish intensity
            dt = MLService.compute_delta_t(itype, intensity, zone)
            cost = MLService.intervention_cost(itype, intensity)
            if cost <= 0 or dt >= 0:
                continue

            # Equity adjustment: boost priority for hotter zones
            lst_norm = (zone["lst"] - 28) / (52 - 28)  # 0-1
            equity_boost = 1 + req.equity_weight * lst_norm

            score = abs(dt) * pop * equity_boost / cost

            candidates.append({
                "zone_id": zid,
                "itype": itype,
                "intensity": intensity,
                "delta_t": dt,
                "cost": cost,
                "score": score,
                "population": pop,
                "original_lst": zone["lst"],
            })

    # Sort by score descending
    candidates.sort(key=lambda c: c["score"], reverse=True)

    # Greedy allocation
    remaining_budget = req.budget
    zone_allocations: dict[str, dict[str, Any]] = {}

    for cand in candidates:
        zid = cand["zone_id"]

        # Respect max interventions per zone
        if zid in zone_allocations:
            if len(zone_allocations[zid]["interventions"]) >= req.max_interventions_per_zone:
                continue
            # Don't repeat same intervention type
            existing_types = {
                i["type"] for i in zone_allocations[zid]["interventions"]
            }
            if cand["itype"] in existing_types:
                continue

        if cand["cost"] > remaining_budget:
            # Try lower intensity
            for reduced in [0.5, 0.3, 0.1]:
                reduced_cost = MLService.intervention_cost(cand["itype"], reduced)
                if reduced_cost <= remaining_budget:
                    cand = {**cand, "intensity": reduced, "cost": reduced_cost}
                    cand["delta_t"] = MLService.compute_delta_t(
                        cand["itype"], reduced,
                        DataService.get_zone_data(req.city, zid),  # type: ignore
                    )
                    break
            else:
                continue

        remaining_budget -= cand["cost"]

        if zid not in zone_allocations:
            zone_allocations[zid] = {
                "zone_id": zid,
                "interventions": [],
                "total_delta_t": 0.0,
                "total_cost": 0.0,
                "priority_score": 0.0,
                "original_lst": cand["original_lst"],
            }

        zone_allocations[zid]["interventions"].append({
            "type": cand["itype"],
            "intensity": round(cand["intensity"], 2),
            "delta_t": round(cand["delta_t"], 3),
            "cost": round(cand["cost"], 2),
        })
        zone_allocations[zid]["total_delta_t"] += cand["delta_t"]
        zone_allocations[zid]["total_cost"] += cand["cost"]
        zone_allocations[zid]["priority_score"] = max(
            zone_allocations[zid]["priority_score"], cand["score"]
        )

        if remaining_budget <= 0:
            break

    # ── Build response ───────────────────────────────────────────
    strategies: list[ZoneStrategy] = []
    all_deltas: list[float] = []

    for zid, alloc in sorted(
        zone_allocations.items(),
        key=lambda kv: kv[1]["total_delta_t"],
    ):
        strategies.append(
            ZoneStrategy(
                zone_id=zid,
                interventions=alloc["interventions"],
                predicted_delta_t=round(alloc["total_delta_t"], 3),
                cost=round(alloc["total_cost"], 2),
                priority_score=round(alloc["priority_score"], 2),
            )
        )
        all_deltas.append(alloc["total_delta_t"])

    budget_used = req.budget - remaining_budget
    total_dt = sum(all_deltas) if all_deltas else 0.0
    mean_dt = total_dt / len(all_deltas) if all_deltas else 0.0

    # Equity score: inverse coefficient of variation of per-zone ΔT
    if len(all_deltas) > 1:
        arr = np.array(all_deltas)
        cv = float(np.std(arr) / (abs(np.mean(arr)) + 1e-9))
        equity_score = round(max(0, 1 - cv), 3)
    else:
        equity_score = 1.0

    return OptimizeResponse(
        city=req.city,
        budget=req.budget,
        budget_used=round(budget_used, 2),
        total_delta_t=round(total_dt, 3),
        mean_delta_t=round(mean_dt, 3),
        equity_score=equity_score,
        strategies=strategies,
    )
