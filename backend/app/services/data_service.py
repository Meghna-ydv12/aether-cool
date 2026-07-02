"""
AETHER-COOL — DataService
Generates and caches the 50×50 sample city grid with realistic
inter-feature correlations (Delhi defaults).

The grid is seeded deterministically so every restart produces
identical data, which makes the frontend experience reproducible.
"""

from __future__ import annotations

import hashlib
from functools import lru_cache
from typing import Any

import numpy as np

from app.config import get_settings

_RNG_SEED = 42


class DataService:
    """Singleton-ish service that lazily builds & caches city grids."""

    _cache: dict[str, dict[str, Any]] = {}

    # ── public API ───────────────────────────────────────────────

    @classmethod
    def get_grid(cls, city: str = "Delhi") -> dict[str, Any]:
        """Return the cached grid dict for *city*, building it on first call."""
        key = city.lower().strip()
        if key not in cls._cache:
            cls._cache[key] = cls._build_grid(city)
        return cls._cache[key]

    @classmethod
    def get_zone_data(cls, city: str, zone_id: str) -> dict[str, Any] | None:
        """Return a single zone's data dict or None."""
        grid = cls.get_grid(city)
        return grid["zones"].get(zone_id)

    @classmethod
    def list_zone_ids(cls, city: str = "Delhi") -> list[str]:
        grid = cls.get_grid(city)
        return list(grid["zones"].keys())

    # ── grid builder ─────────────────────────────────────────────

    @classmethod
    def _build_grid(cls, city: str) -> dict[str, Any]:
        settings = get_settings()
        n = settings.GRID_SIZE  # 50
        rng = np.random.default_rng(_RNG_SEED)

        center_lat = settings.DEFAULT_LAT
        center_lon = settings.DEFAULT_LON

        # Spatial extent ≈ 15 km × 15 km around centre
        lat_span = 0.135  # ~15 km
        lon_span = 0.155

        lats = np.linspace(
            center_lat - lat_span / 2, center_lat + lat_span / 2, n
        )
        lons = np.linspace(
            center_lon - lon_span / 2, center_lon + lon_span / 2, n
        )

        # ----- base features with realistic spatial autocorrelation ----
        # Create smooth underlying fields using distance from centre
        row_idx, col_idx = np.meshgrid(np.arange(n), np.arange(n), indexing="ij")
        dist_from_center = np.sqrt(
            ((row_idx - n / 2) / (n / 2)) ** 2
            + ((col_idx - n / 2) / (n / 2)) ** 2
        )

        # Building density: high in centre, tapering outward + noise
        building_density = np.clip(
            0.75 - 0.55 * dist_from_center + rng.normal(0, 0.08, (n, n)),
            0.02, 0.95,
        )

        # NDVI: inverse of building density + independent vegetation patches
        veg_patches = cls._smooth_noise(rng, n, scale=0.15)
        ndvi = np.clip(
            0.65 - 0.55 * building_density + veg_patches + rng.normal(0, 0.04, (n, n)),
            0.02, 0.85,
        )

        # Albedo: lower in dense built-up areas (dark asphalt), higher in
        # open / white-roofed areas
        albedo = np.clip(
            0.20 + 0.15 * (1 - building_density) + rng.normal(0, 0.03, (n, n)),
            0.08, 0.55,
        )

        # Sky View Factor: less sky visible in dense cores
        svf = np.clip(
            0.85 - 0.50 * building_density + rng.normal(0, 0.05, (n, n)),
            0.10, 0.98,
        )

        # Population proxy (thousands)
        population = np.clip(
            building_density * 12000 + rng.normal(0, 800, (n, n)),
            50, 18000,
        )

        # Elevation (m) — slight gradient + noise
        elevation = 215 + 15 * (row_idx / n) + rng.normal(0, 2, (n, n))

        # LULC class
        lulc_grid = cls._assign_lulc(building_density, ndvi, rng)

        # ----- LST with physically motivated formula ----
        lst = (
            45.0
            - 15.0 * ndvi
            - 8.0 * albedo
            + 5.0 * building_density
            - 3.0 * svf
            + rng.normal(0, 0.6, (n, n))
        )
        lst = np.clip(lst, 28.0, 52.0)

        # ----- package into zone dicts ----
        zones: dict[str, dict[str, Any]] = {}
        flat_features: list[dict[str, Any]] = []

        for r in range(n):
            for c in range(n):
                zone_id = f"Z-{r:02d}-{c:02d}"
                zone = {
                    "zone_id": zone_id,
                    "row": r,
                    "col": c,
                    "lat": float(lats[r]),
                    "lon": float(lons[c]),
                    "lst": float(round(lst[r, c], 2)),
                    "ndvi": float(round(ndvi[r, c], 4)),
                    "albedo": float(round(albedo[r, c], 4)),
                    "svf": float(round(svf[r, c], 4)),
                    "building_density": float(round(building_density[r, c], 4)),
                    "lulc": lulc_grid[r][c],
                    "population": float(round(population[r, c], 0)),
                    "elevation": float(round(elevation[r, c], 1)),
                }
                zones[zone_id] = zone
                flat_features.append(zone)

        return {
            "city": city,
            "center_lat": center_lat,
            "center_lon": center_lon,
            "grid_size": n,
            "total_zones": n * n,
            "zones": zones,
            "flat": flat_features,
            "lats": lats.tolist(),
            "lons": lons.tolist(),
        }

    # ── helpers ──────────────────────────────────────────────────

    @staticmethod
    def _smooth_noise(rng: np.random.Generator, n: int, scale: float = 0.1) -> np.ndarray:
        """Generate spatially correlated noise via low-res upsample."""
        small = rng.normal(0, scale, (n // 5, n // 5))
        # Bilinear-ish upscale using np
        from scipy.ndimage import zoom
        return zoom(small, n / (n // 5), order=1)[:n, :n]

    @staticmethod
    def _assign_lulc(
        building_density: np.ndarray,
        ndvi: np.ndarray,
        rng: np.random.Generator,
    ) -> list[list[str]]:
        n = building_density.shape[0]
        grid: list[list[str]] = []
        for r in range(n):
            row: list[str] = []
            for c in range(n):
                bd = building_density[r, c]
                nv = ndvi[r, c]
                roll = rng.random()
                if bd > 0.6:
                    row.append("built_up")
                elif nv > 0.5:
                    row.append("vegetation")
                elif bd < 0.15 and nv < 0.15 and roll < 0.15:
                    row.append("water")
                elif bd < 0.2 and nv < 0.2:
                    row.append("barren")
                else:
                    row.append("mixed")
            grid.append(row)
        return grid
