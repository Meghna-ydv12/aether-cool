"""
AETHER-COOL — Cooling Intervention Optimizer
Uses Genetic Algorithm (via scipy.optimize + custom GA) to find the optimal
mix and spatial placement of cooling interventions under budget constraints.
"""

import numpy as np
from scipy.optimize import differential_evolution
from dataclasses import dataclass
from typing import List, Dict, Optional
import json


@dataclass
class InterventionType:
    """Definition of a cooling intervention"""
    name: str
    type_id: str
    cost_per_sqm: float          # $/m²
    max_delta_t: float           # Maximum temperature reduction (°C)
    effectiveness_curve: str      # 'linear', 'logarithmic', 'sigmoid'
    ndvi_dependency: float        # How much NDVI affects effectiveness (0-1)
    albedo_change: float          # Change in albedo when applied
    maintenance_annual: float     # Annual maintenance cost ($/m²/year)


# Default intervention catalog
INTERVENTIONS = [
    InterventionType('Urban Tree Planting', 'tree_planting', 22.0, 5.0,
                     'logarithmic', 0.8, 0.05, 2.0),
    InterventionType('Cool Roofs', 'cool_roofs', 10.0, 2.5,
                     'linear', 0.1, 0.35, 1.0),
    InterventionType('Green Roofs', 'green_roofs', 60.0, 3.0,
                     'logarithmic', 0.6, 0.1, 5.0),
    InterventionType('Albedo Paint', 'albedo_paint', 7.0, 1.5,
                     'linear', 0.0, 0.25, 0.5),
    InterventionType('Water Bodies', 'water_bodies', 120.0, 3.0,
                     'sigmoid', 0.2, -0.1, 8.0),
    InterventionType('Permeable Pavements', 'permeable_pavement', 35.0, 1.5,
                     'linear', 0.1, 0.05, 3.0),
]


def compute_delta_t(intervention: InterventionType, intensity: float,
                    current_ndvi: float, current_albedo: float,
                    building_density: float) -> float:
    """
    Compute temperature reduction for a given intervention at a given intensity.

    Physics-based approach:
    - Tree planting: ΔT from evapotranspiration = f(canopy_fraction, 1 - current_ndvi)
    - Cool roofs: ΔT from albedo change = f(Δalbedo, solar_radiation)
    - Green roofs: ΔT from ET + insulation = f(intensity, building_area)
    - Water bodies: ΔT from evaporative cooling = f(water_fraction, wind)
    """
    intensity = np.clip(intensity, 0, 1)

    if intensity < 0.01:
        return 0.0

    # Base effectiveness
    max_dt = intervention.max_delta_t

    # Apply effectiveness curve
    if intervention.effectiveness_curve == 'linear':
        effect = intensity
    elif intervention.effectiveness_curve == 'logarithmic':
        effect = np.log1p(intensity * 2.718) / np.log1p(2.718)  # normalized log
    elif intervention.effectiveness_curve == 'sigmoid':
        effect = 1 / (1 + np.exp(-10 * (intensity - 0.5)))
    else:
        effect = intensity

    # NDVI dependency — less effective where vegetation already exists
    ndvi_factor = 1.0 - intervention.ndvi_dependency * current_ndvi

    # Building density factor — some interventions need buildings
    if intervention.type_id in ['cool_roofs', 'green_roofs']:
        bd_factor = building_density  # Need buildings for roof interventions
    elif intervention.type_id == 'tree_planting':
        bd_factor = 1.0 - 0.5 * building_density  # Trees harder in dense areas
    else:
        bd_factor = 1.0

    delta_t = -max_dt * effect * ndvi_factor * bd_factor

    return delta_t


def compute_cost(intervention: InterventionType, intensity: float,
                 zone_area_sqm: float = 900.0) -> float:
    """Compute cost of intervention at given intensity for a zone"""
    return intervention.cost_per_sqm * intensity * zone_area_sqm


class CoolingOptimizer:
    """
    Genetic Algorithm-based optimizer for finding optimal cooling interventions
    under budget constraints.
    """

    def __init__(self, zone_data: List[Dict], budget: float,
                 equity_weight: float = 0.5,
                 interventions: List[InterventionType] = None):
        """
        Args:
            zone_data: List of dicts with keys: zone_id, lst, ndvi, albedo,
                       building_density, population, vulnerability
            budget: Total budget constraint ($)
            equity_weight: Weight for equity (vulnerability) in objective (0-1)
            interventions: List of available interventions
        """
        self.zone_data = zone_data
        self.n_zones = len(zone_data)
        self.budget = budget
        self.equity_weight = equity_weight
        self.interventions = interventions or INTERVENTIONS
        self.n_interventions = len(self.interventions)

        # Decision variables: for each zone, one intervention type (int) + intensity (float)
        # We encode as: [zone_0_type, zone_0_intensity, zone_1_type, zone_1_intensity, ...]
        self.n_vars = self.n_zones * 2  # type + intensity per zone

    def _decode_solution(self, x: np.ndarray) -> List[Dict]:
        """Decode continuous optimization vector into intervention assignments"""
        assignments = []
        for i in range(self.n_zones):
            type_idx = int(x[2 * i] * self.n_interventions) % self.n_interventions
            intensity = np.clip(x[2 * i + 1], 0, 1)
            assignments.append({
                'zone_idx': i,
                'intervention_idx': type_idx,
                'intensity': intensity
            })
        return assignments

    def _objective(self, x: np.ndarray) -> float:
        """
        Objective function to MINIMIZE (negative of what we want to maximize).
        Maximize: total temperature reduction × population × equity weight
        Subject to: total cost ≤ budget
        """
        assignments = self._decode_solution(x)

        total_benefit = 0.0
        total_cost = 0.0

        for a in assignments:
            zone = self.zone_data[a['zone_idx']]
            intervention = self.interventions[a['intervention_idx']]
            intensity = a['intensity']

            # Compute temperature reduction
            delta_t = compute_delta_t(
                intervention, intensity,
                zone['ndvi'], zone['albedo'], zone['building_density']
            )

            # Compute cost
            cost = compute_cost(intervention, intensity)
            total_cost += cost

            # Benefit = |ΔT| × population × (1 + equity_weight × vulnerability)
            pop = zone.get('population', 100)
            vuln = zone.get('vulnerability', 0.5)
            equity_factor = 1.0 + self.equity_weight * vuln
            benefit = abs(delta_t) * pop * equity_factor

            total_benefit += benefit

        # Budget penalty (soft constraint)
        budget_penalty = 0.0
        if total_cost > self.budget:
            budget_penalty = 1000.0 * (total_cost - self.budget) / self.budget

        # Minimize negative benefit + penalty
        return -total_benefit + budget_penalty

    def optimize(self, max_iter: int = 100, population_size: int = 50,
                 seed: int = 42) -> Dict:
        """
        Run the optimization.
        Returns optimal intervention strategy.
        """
        # Define bounds: [0, 1] for both type selector and intensity
        bounds = [(0, 0.999)] * self.n_vars

        # For small zone counts, optimize all zones
        # For large zone counts, optimize top hotspot zones only
        target_zones = self.zone_data
        if self.n_zones > 100:
            # Focus on top 100 hottest zones
            sorted_zones = sorted(self.zone_data, key=lambda z: z['lst'], reverse=True)
            target_zones = sorted_zones[:100]
            self.zone_data = target_zones
            self.n_zones = len(target_zones)
            self.n_vars = self.n_zones * 2
            bounds = [(0, 0.999)] * self.n_vars

        # Run differential evolution (GA variant)
        result = differential_evolution(
            self._objective,
            bounds=bounds,
            maxiter=max_iter,
            popsize=population_size,
            seed=seed,
            tol=1e-6,
            mutation=(0.5, 1.5),
            recombination=0.8,
            workers=1
        )

        # Decode best solution
        best_assignments = self._decode_solution(result.x)

        # Build result
        strategy = []
        total_cost = 0.0
        total_delta_t = 0.0
        total_pop_covered = 0

        for a in best_assignments:
            zone = self.zone_data[a['zone_idx']]
            intervention = self.interventions[a['intervention_idx']]
            intensity = a['intensity']

            if intensity < 0.05:  # Skip near-zero interventions
                continue

            delta_t = compute_delta_t(
                intervention, intensity,
                zone['ndvi'], zone['albedo'], zone['building_density']
            )
            cost = compute_cost(intervention, intensity)

            total_cost += cost
            total_delta_t += delta_t
            total_pop_covered += zone.get('population', 0)

            strategy.append({
                'zone_id': zone['zone_id'],
                'zone_lst': round(zone['lst'], 1),
                'intervention': intervention.name,
                'intervention_type': intervention.type_id,
                'intensity': round(intensity, 2),
                'predicted_delta_t': round(delta_t, 2),
                'predicted_new_lst': round(zone['lst'] + delta_t, 1),
                'cost': round(cost, 0),
                'population': zone.get('population', 0),
                'vulnerability': round(zone.get('vulnerability', 0.5), 2),
                'priority': 'critical' if zone['lst'] > 45 else
                            'high' if zone['lst'] > 42 else
                            'medium' if zone['lst'] > 39 else 'low'
            })

        # Sort by priority / delta_t
        strategy.sort(key=lambda s: s['predicted_delta_t'])

        n_active = len(strategy)
        avg_delta_t = total_delta_t / n_active if n_active > 0 else 0

        return {
            'status': 'success',
            'optimization_result': {
                'total_cost': round(total_cost, 0),
                'budget': self.budget,
                'budget_utilization': round(total_cost / self.budget * 100, 1),
                'zones_optimized': n_active,
                'total_zones': self.n_zones,
                'avg_temperature_reduction': round(avg_delta_t, 2),
                'population_covered': total_pop_covered,
                'equity_weight': self.equity_weight
            },
            'strategy': strategy
        }


def generate_pareto_scenarios(zone_data: List[Dict], budget: float) -> List[Dict]:
    """
    Generate Pareto-optimal scenarios with different objective weights.
    """
    scenarios = [
        {'name': 'Maximum Cooling', 'equity_weight': 0.0, 'budget_fraction': 1.0},
        {'name': 'Budget Balanced', 'equity_weight': 0.3, 'budget_fraction': 0.7},
        {'name': 'Equity First', 'equity_weight': 0.9, 'budget_fraction': 0.7},
        {'name': 'Quick Wins', 'equity_weight': 0.2, 'budget_fraction': 0.4},
    ]

    results = []
    for scenario in scenarios:
        opt = CoolingOptimizer(
            zone_data=zone_data,
            budget=budget * scenario['budget_fraction'],
            equity_weight=scenario['equity_weight']
        )
        result = opt.optimize(max_iter=50, population_size=30)
        result['scenario_name'] = scenario['name']
        results.append(result)

    return results
