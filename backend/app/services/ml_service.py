"""
AETHER-COOL — MLService
Mock PINN inference wrapper.

Uses a deterministic linear formula that mimics the physics-informed
neural net output:

    LST = 45 − 15·NDVI − 8·albedo + 5·building_density − 3·SVF + noise

When a real PINN checkpoint is available, swap `predict_lst` to call
`torch.load(…)` → `model.forward(…)`.
"""

from __future__ import annotations

from typing import Any

import numpy as np


class MLService:
    """Lightweight inference wrapper (mock mode)."""

    _COEFFICIENTS = {
        "intercept": 45.0,
        "ndvi": -15.0,
        "albedo": -8.0,
        "building_density": 5.0,
        "svf": -3.0,
    }

    # ── prediction ───────────────────────────────────────────────

    @classmethod
    def predict_lst(
        cls,
        ndvi: float,
        albedo: float,
        building_density: float,
        svf: float,
        *,
        noise_std: float = 0.3,
        seed: int | None = None,
    ) -> float:
        """Return predicted LST (°C) for one grid cell."""
        rng = np.random.default_rng(seed)
        c = cls._COEFFICIENTS
        lst = (
            c["intercept"]
            + c["ndvi"] * ndvi
            + c["albedo"] * albedo
            + c["building_density"] * building_density
            + c["svf"] * svf
            + rng.normal(0, noise_std)
        )
        return float(np.clip(lst, 28.0, 52.0))

    @classmethod
    def predict_batch(
        cls,
        features: list[dict[str, float]],
        *,
        noise_std: float = 0.3,
    ) -> list[float]:
        """Vectorised prediction for many cells."""
        n = len(features)
        rng = np.random.default_rng(42)
        c = cls._COEFFICIENTS

        ndvi = np.array([f["ndvi"] for f in features])
        albedo = np.array([f["albedo"] for f in features])
        bd = np.array([f["building_density"] for f in features])
        svf = np.array([f["svf"] for f in features])

        lst = (
            c["intercept"]
            + c["ndvi"] * ndvi
            + c["albedo"] * albedo
            + c["building_density"] * bd
            + c["svf"] * svf
            + rng.normal(0, noise_std, n)
        )
        return np.clip(lst, 28.0, 52.0).tolist()

    # ── intervention delta model ─────────────────────────────────

    @classmethod
    def compute_delta_t(
        cls,
        intervention_type: str,
        intensity: float,
        zone: dict[str, Any],
    ) -> float:
        """
        Physics-inspired ΔT formula per intervention type.

        Returns a negative number (cooling) when the intervention helps.
        """
        ndvi = zone.get("ndvi", 0.3)
        albedo = zone.get("albedo", 0.2)
        bd = zone.get("building_density", 0.5)
        svf = zone.get("svf", 0.5)

        match intervention_type:
            case "tree_planting":
                # More impact where NDVI is currently low
                return -intensity * 5.0 * (1.0 - ndvi)
            case "cool_roofs":
                albedo_change = intensity * 0.35  # max +0.35 albedo
                return -intensity * albedo_change * 3.0
            case "green_roofs":
                return -intensity * 3.5 * (1.0 - ndvi) * bd
            case "permeable_paving":
                return -intensity * 2.0 * bd
            case "urban_wetlands":
                return -intensity * 4.0 * (1.0 - ndvi) * 0.7
            case "shade_structures":
                return -intensity * 2.5 * (1.0 - svf)
            case "cool_pavements":
                albedo_change = intensity * 0.25
                return -intensity * albedo_change * 2.5
            case _:
                return 0.0

    # ── cost model ───────────────────────────────────────────────

    @staticmethod
    def intervention_cost(intervention_type: str, intensity: float) -> float:
        """Return normalised cost units for one zone × one intervention."""
        base_costs = {
            "tree_planting": 8.0,
            "cool_roofs": 12.0,
            "green_roofs": 18.0,
            "permeable_paving": 10.0,
            "urban_wetlands": 25.0,
            "shade_structures": 6.0,
            "cool_pavements": 9.0,
        }
        return base_costs.get(intervention_type, 10.0) * intensity
