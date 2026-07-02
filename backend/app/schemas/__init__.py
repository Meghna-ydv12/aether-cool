"""
AETHER-COOL — Pydantic v2 Schemas
Request / response models for every API endpoint.
"""

from __future__ import annotations

from datetime import date, datetime
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field


# ── Enums ────────────────────────────────────────────────────────


class LULCClass(str, Enum):
    """Land-Use / Land-Cover categories."""
    BUILT_UP = "built_up"
    VEGETATION = "vegetation"
    WATER = "water"
    BARREN = "barren"
    MIXED = "mixed"


class InterventionType(str, Enum):
    """Supported urban heat mitigation interventions."""
    TREE_PLANTING = "tree_planting"
    COOL_ROOFS = "cool_roofs"
    GREEN_ROOFS = "green_roofs"
    PERMEABLE_PAVING = "permeable_paving"
    URBAN_WETLANDS = "urban_wetlands"
    SHADE_STRUCTURES = "shade_structures"
    COOL_PAVEMENTS = "cool_pavements"


# ── GeoJSON ──────────────────────────────────────────────────────


class GeoJSONGeometry(BaseModel):
    type: str = "Point"
    coordinates: list[float]  # [lon, lat]


class PixelProperties(BaseModel):
    """Per-grid-cell properties returned in the heatmap."""
    zone_id: str
    row: int
    col: int
    lst: float = Field(..., description="Land Surface Temperature (°C)")
    ndvi: float = Field(..., description="Normalized Difference Vegetation Index")
    albedo: float = Field(..., description="Surface albedo (0-1)")
    lulc: LULCClass
    svf: float = Field(..., description="Sky View Factor (0-1)")
    building_density: float = Field(..., description="Building density (0-1)")
    population: float = Field(0, description="Estimated population in cell")
    elevation: float = Field(0, description="Elevation (m)")


class GeoJSONFeature(BaseModel):
    type: str = "Feature"
    geometry: GeoJSONGeometry
    properties: PixelProperties


class GeoJSONFeatureCollection(BaseModel):
    type: str = "FeatureCollection"
    features: list[GeoJSONFeature]
    metadata: dict[str, Any] = {}


# ── Drivers / SHAP ───────────────────────────────────────────────


class DriverContribution(BaseModel):
    """Single driver importance entry (SHAP-style)."""
    driver: str
    importance: float = Field(..., description="Absolute SHAP value")
    direction: str = Field(
        ..., description="'positive' increases LST, 'negative' decreases"
    )
    description: str = ""


class DriversResponse(BaseModel):
    zone_id: Optional[str] = None
    drivers: list[DriverContribution]
    mean_lst: float = 0.0


class DriversSummaryResponse(BaseModel):
    city: str
    total_zones: int
    drivers: list[DriverContribution]


# ── Simulation ───────────────────────────────────────────────────


class Intervention(BaseModel):
    """Single intervention specification."""
    type: InterventionType
    intensity: float = Field(
        ..., ge=0, le=1.0,
        description="Fraction of maximum possible intervention (0-1)"
    )
    zone_ids: list[str] = Field(
        default_factory=list,
        description="Target zone IDs; empty → all zones"
    )


class SimulateRequest(BaseModel):
    interventions: list[Intervention]
    city: str = "Delhi"


class ZoneDelta(BaseModel):
    zone_id: str
    original_lst: float
    predicted_lst: float
    delta_t: float = Field(..., description="Temperature change (°C, negative = cooler)")
    interventions_applied: list[str]


class SimulateResponse(BaseModel):
    city: str
    total_zones_affected: int
    mean_delta_t: float
    max_delta_t: float
    zone_deltas: list[ZoneDelta]


# ── Optimizer ────────────────────────────────────────────────────


class OptimizeRequest(BaseModel):
    budget: float = Field(
        ..., gt=0, description="Total budget in arbitrary cost units"
    )
    equity_weight: float = Field(
        0.5, ge=0, le=1,
        description="Weight for equity (0 = efficiency only, 1 = equity only)"
    )
    target_zones: list[str] = Field(
        default_factory=list,
        description="Subset of zones to optimise; empty → all"
    )
    city: str = "Delhi"
    max_interventions_per_zone: int = Field(3, ge=1, le=7)


class ZoneStrategy(BaseModel):
    zone_id: str
    interventions: list[dict[str, Any]]
    predicted_delta_t: float
    cost: float
    priority_score: float


class OptimizeResponse(BaseModel):
    city: str
    budget: float
    budget_used: float
    total_delta_t: float
    mean_delta_t: float
    equity_score: float
    strategies: list[ZoneStrategy]


# ── Scenarios ────────────────────────────────────────────────────


class ScenarioSummary(BaseModel):
    id: str
    name: str
    city: str
    created_at: datetime
    total_zones: int
    mean_delta_t: float
    budget_used: float
    interventions_count: int


class ScenariosListResponse(BaseModel):
    scenarios: list[ScenarioSummary]


# ── Trends ───────────────────────────────────────────────────────


class TrendPoint(BaseModel):
    timestamp: str  # ISO-8601 or label like "06:00"
    lst: float
    ndvi: Optional[float] = None


class TrendsResponse(BaseModel):
    zone_id: str
    diurnal: list[TrendPoint]
    seasonal: list[TrendPoint]


# ── Health ───────────────────────────────────────────────────────


class HealthResponse(BaseModel):
    status: str = "healthy"
    version: str
    model_loaded: bool
    city: str
    grid_size: int
    timestamp: datetime
