"""
AETHER-COOL — Heatmap API
GET /api/heatmap  → GeoJSON FeatureCollection (2 500 grid points)
"""

from __future__ import annotations

from fastapi import APIRouter, Query

from app.schemas import GeoJSONFeatureCollection
from app.services.data_service import DataService
from app.services.geo_service import GeoService

router = APIRouter(prefix="/api", tags=["heatmap"])


@router.get(
    "/heatmap",
    response_model=GeoJSONFeatureCollection,
    summary="City heatmap as GeoJSON FeatureCollection",
    description=(
        "Returns a 50×50 grid of points centred on the requested city. "
        "Each feature carries LST, NDVI, albedo, LULC, SVF, "
        "building_density, population, and elevation."
    ),
)
async def get_heatmap(
    city: str = Query("Delhi", description="City name"),
    date: str = Query("2024-05-15", description="Date (YYYY-MM-DD)"),
) -> GeoJSONFeatureCollection:
    grid = DataService.get_grid(city)
    zones = grid["flat"]

    fc = GeoService.create_feature_collection(
        zones,
        metadata={
            "city": grid["city"],
            "date": date,
            "grid_size": grid["grid_size"],
            "total_zones": grid["total_zones"],
            "center": {
                "lat": grid["center_lat"],
                "lon": grid["center_lon"],
            },
            "bbox": GeoService.bounding_box(zones),
        },
    )
    return fc
