"""
AETHER-COOL — GeoService
Spatial helper utilities: GeoJSON construction, distance helpers,
bounding-box queries.
"""

from __future__ import annotations

import math
from typing import Any

from app.schemas import (
    GeoJSONFeature,
    GeoJSONFeatureCollection,
    GeoJSONGeometry,
    PixelProperties,
)


class GeoService:
    """Stateless spatial helper methods."""

    # ── GeoJSON builders ─────────────────────────────────────────

    @staticmethod
    def zone_to_feature(zone: dict[str, Any]) -> GeoJSONFeature:
        """Convert a zone data dict to a GeoJSON Feature."""
        return GeoJSONFeature(
            geometry=GeoJSONGeometry(
                type="Point",
                coordinates=[zone["lon"], zone["lat"]],
            ),
            properties=PixelProperties(
                zone_id=zone["zone_id"],
                row=zone["row"],
                col=zone["col"],
                lst=zone["lst"],
                ndvi=zone["ndvi"],
                albedo=zone["albedo"],
                lulc=zone["lulc"],
                svf=zone["svf"],
                building_density=zone["building_density"],
                population=zone.get("population", 0),
                elevation=zone.get("elevation", 0),
            ),
        )

    @classmethod
    def create_feature_collection(
        cls,
        zones: list[dict[str, Any]],
        metadata: dict[str, Any] | None = None,
    ) -> GeoJSONFeatureCollection:
        """Build a full FeatureCollection from a list of zone dicts."""
        features = [cls.zone_to_feature(z) for z in zones]
        return GeoJSONFeatureCollection(
            features=features,
            metadata=metadata or {},
        )

    # ── distance / bbox helpers ──────────────────────────────────

    @staticmethod
    def haversine_km(
        lat1: float, lon1: float,
        lat2: float, lon2: float,
    ) -> float:
        """Great-circle distance in kilometres."""
        R = 6371.0
        φ1, φ2 = math.radians(lat1), math.radians(lat2)
        Δφ = math.radians(lat2 - lat1)
        Δλ = math.radians(lon2 - lon1)
        a = (
            math.sin(Δφ / 2) ** 2
            + math.cos(φ1) * math.cos(φ2) * math.sin(Δλ / 2) ** 2
        )
        return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    @classmethod
    def zones_within_radius_km(
        cls,
        zones: list[dict[str, Any]],
        center_lat: float,
        center_lon: float,
        radius_km: float,
    ) -> list[dict[str, Any]]:
        """Filter zones within *radius_km* of a point."""
        return [
            z for z in zones
            if cls.haversine_km(center_lat, center_lon, z["lat"], z["lon"]) <= radius_km
        ]

    @staticmethod
    def bounding_box(
        zones: list[dict[str, Any]],
    ) -> dict[str, float]:
        """Return {min_lat, max_lat, min_lon, max_lon}."""
        lats = [z["lat"] for z in zones]
        lons = [z["lon"] for z in zones]
        return {
            "min_lat": min(lats),
            "max_lat": max(lats),
            "min_lon": min(lons),
            "max_lon": max(lons),
        }
