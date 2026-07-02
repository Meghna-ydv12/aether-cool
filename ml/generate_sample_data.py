"""
AETHER-COOL — Sample City Data Generator
Generates realistic synthetic urban heat data for a 50x50 grid city.
Simulates correlations between LST, NDVI, albedo, building density, SVF, etc.
"""

import numpy as np
import json
import os

# ----- Configuration -----
GRID_SIZE = 50
CENTER_LAT = 28.6139  # Delhi
CENTER_LON = 77.2090
PIXEL_SIZE_DEG = 0.0003  # ~30m at this latitude
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), '..', 'data', 'sample')

# Random seed for reproducibility
np.random.seed(42)


def generate_urban_zones(n: int) -> np.ndarray:
    """Generate LULC zones: 0=commercial, 1=residential, 2=industrial, 3=park, 4=water"""
    zones = np.ones((n, n), dtype=int)  # default residential

    # Commercial core (center)
    zones[18:32, 18:32] = 0

    # Industrial areas (corners)
    zones[0:10, 0:10] = 2
    zones[40:50, 40:50] = 2
    zones[0:8, 42:50] = 2

    # Parks (scattered)
    zones[12:17, 5:12] = 3
    zones[35:42, 20:28] = 3
    zones[5:10, 35:40] = 3
    zones[25:30, 40:46] = 3

    # Water body
    zones[20:25, 8:14] = 4
    zones[42:48, 30:38] = 4

    return zones


def generate_building_density(zones: np.ndarray) -> np.ndarray:
    """Building density correlated with LULC zone"""
    n = zones.shape[0]
    density = np.zeros((n, n))
    noise = np.random.normal(0, 0.05, (n, n))

    density[zones == 0] = 0.85 + noise[zones == 0]  # commercial
    density[zones == 1] = 0.55 + noise[zones == 1]  # residential
    density[zones == 2] = 0.70 + noise[zones == 2]  # industrial
    density[zones == 3] = 0.05 + np.abs(noise[zones == 3])  # park
    density[zones == 4] = 0.0   # water

    return np.clip(density, 0, 1)


def generate_ndvi(zones: np.ndarray) -> np.ndarray:
    """NDVI (vegetation) inversely correlated with building density"""
    n = zones.shape[0]
    ndvi = np.zeros((n, n))
    noise = np.random.normal(0, 0.05, (n, n))

    ndvi[zones == 0] = 0.10 + noise[zones == 0]  # commercial = low vegetation
    ndvi[zones == 1] = 0.30 + noise[zones == 1]  # residential = moderate
    ndvi[zones == 2] = 0.08 + noise[zones == 2]  # industrial = very low
    ndvi[zones == 3] = 0.72 + noise[zones == 3]  # park = high
    ndvi[zones == 4] = 0.05 + np.abs(noise[zones == 4])  # water = low

    return np.clip(ndvi, 0.0, 0.95)


def generate_albedo(zones: np.ndarray) -> np.ndarray:
    """Surface albedo by zone type"""
    n = zones.shape[0]
    albedo = np.zeros((n, n))
    noise = np.random.normal(0, 0.02, (n, n))

    albedo[zones == 0] = 0.15 + noise[zones == 0]  # dark roofs
    albedo[zones == 1] = 0.22 + noise[zones == 1]  # mixed
    albedo[zones == 2] = 0.12 + noise[zones == 2]  # industrial dark
    albedo[zones == 3] = 0.20 + noise[zones == 3]  # vegetation
    albedo[zones == 4] = 0.06 + np.abs(noise[zones == 4])  # water (low)

    return np.clip(albedo, 0.05, 0.5)


def generate_svf(zones: np.ndarray) -> np.ndarray:
    """Sky View Factor — higher in open areas, lower in dense urban canyons"""
    n = zones.shape[0]
    svf = np.zeros((n, n))
    noise = np.random.normal(0, 0.05, (n, n))

    svf[zones == 0] = 0.35 + noise[zones == 0]  # urban canyons
    svf[zones == 1] = 0.55 + noise[zones == 1]  # moderate
    svf[zones == 2] = 0.50 + noise[zones == 2]  # industrial
    svf[zones == 3] = 0.85 + noise[zones == 3]  # open parks
    svf[zones == 4] = 0.90 + noise[zones == 4]  # water (open)

    return np.clip(svf, 0.1, 1.0)


def compute_distance_to_water(zones: np.ndarray) -> np.ndarray:
    """Euclidean distance to nearest water pixel (normalized 0-1)"""
    n = zones.shape[0]
    water_mask = (zones == 4)
    water_coords = np.argwhere(water_mask)

    if len(water_coords) == 0:
        return np.ones((n, n))

    dist = np.zeros((n, n))
    for i in range(n):
        for j in range(n):
            distances = np.sqrt((water_coords[:, 0] - i) ** 2 + (water_coords[:, 1] - j) ** 2)
            dist[i, j] = distances.min()

    # Normalize to 0-1
    dist = dist / dist.max()
    return dist


def compute_lst(ndvi: np.ndarray, albedo: np.ndarray, building_density: np.ndarray,
                svf: np.ndarray, dist_water: np.ndarray, zones: np.ndarray) -> np.ndarray:
    """
    Physics-inspired LST computation using simplified urban energy balance.
    LST = baseline + solar_gain - vegetation_cooling - albedo_effect
           + urban_heat_storage - water_cooling + anthropogenic_heat
    """
    n = ndvi.shape[0]
    noise = np.random.normal(0, 0.8, (n, n))

    # Baseline air temperature (summer Delhi ~38°C)
    T_air = 38.0

    # Solar radiation absorbed (reduced by albedo)
    solar_gain = 12.0 * (1 - albedo)

    # Vegetation cooling via evapotranspiration
    vegetation_cooling = 15.0 * ndvi

    # Urban heat storage (thermal mass of buildings)
    heat_storage = 8.0 * building_density

    # Sky view factor effect (more open sky = more longwave radiation loss at night,
    # but more solar gain during day — net positive for daytime LST)
    svf_effect = 3.0 * (1 - svf)

    # Water body cooling
    water_cooling = 4.0 * (1 - dist_water)

    # Anthropogenic heat (higher in commercial/industrial)
    anthropogenic = np.zeros((n, n))
    anthropogenic[zones == 0] = 3.0  # commercial
    anthropogenic[zones == 2] = 4.0  # industrial
    anthropogenic[zones == 1] = 1.5  # residential

    # Final LST
    lst = (T_air + solar_gain - vegetation_cooling + heat_storage
           + svf_effect - water_cooling + anthropogenic + noise)

    return np.clip(lst, 25.0, 55.0)


def generate_population(zones: np.ndarray) -> np.ndarray:
    """Population density per grid cell"""
    n = zones.shape[0]
    pop = np.zeros((n, n))
    noise = np.random.normal(0, 50, (n, n))

    pop[zones == 0] = 800 + noise[zones == 0]   # commercial (daytime)
    pop[zones == 1] = 500 + noise[zones == 1]   # residential
    pop[zones == 2] = 200 + noise[zones == 2]   # industrial
    pop[zones == 3] = 50 + np.abs(noise[zones == 3])  # parks
    pop[zones == 4] = 0  # water

    return np.clip(pop, 0, 2000).astype(int)


def generate_vulnerability_index(zones: np.ndarray) -> np.ndarray:
    """Vulnerability index (0-1) — higher in low-income residential areas"""
    n = zones.shape[0]
    vuln = np.random.uniform(0.2, 0.5, (n, n))

    # Higher vulnerability in certain residential pockets
    vuln[15:25, 0:10] = np.random.uniform(0.7, 0.95, vuln[15:25, 0:10].shape)
    vuln[35:45, 10:20] = np.random.uniform(0.6, 0.85, vuln[35:45, 10:20].shape)
    vuln[zones == 3] = 0.1  # parks
    vuln[zones == 4] = 0.0  # water

    return np.clip(vuln, 0, 1)


def generate_diurnal_trends() -> dict:
    """Generate 24-hour LST trends for different zone types"""
    hours = list(range(24))
    trends = {}

    for zone_type, name in [(0, 'commercial'), (1, 'residential'), (2, 'industrial'), (3, 'park')]:
        base = {0: 44, 1: 40, 2: 46, 3: 34}[zone_type]
        amplitude = {0: 8, 1: 7, 2: 9, 3: 5}[zone_type]

        temps = []
        for h in hours:
            # Peak at 14:00 (2 PM), minimum at 05:00
            phase = (h - 14) * np.pi / 12
            temp = base + amplitude * np.cos(phase) * 0.5
            temp += np.random.normal(0, 0.3)
            temps.append(round(temp, 1))

        trends[name] = temps

    return {'hours': hours, 'trends': trends}


def generate_seasonal_trends() -> dict:
    """Generate monthly LST trends"""
    months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
              'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

    # Delhi seasonal pattern
    baseline = [22, 25, 32, 38, 44, 48, 42, 40, 38, 34, 28, 23]
    with_intervention = [21, 24, 30, 35, 40, 43, 38, 37, 35, 32, 27, 22]

    noise_c = np.random.normal(0, 0.5, 12)
    noise_i = np.random.normal(0, 0.5, 12)

    return {
        'months': months,
        'current': [round(b + n, 1) for b, n in zip(baseline, noise_c)],
        'with_intervention': [round(b + n, 1) for b, n in zip(with_intervention, noise_i)]
    }


def build_geojson(lats, lons, features_dict) -> dict:
    """Build GeoJSON FeatureCollection from grid data"""
    features = []
    n = lats.shape[0]

    lulc_names = {0: 'commercial', 1: 'residential', 2: 'industrial', 3: 'park', 4: 'water'}

    for i in range(n):
        for j in range(n):
            properties = {
                'zone_id': f'Z-{i * n + j:04d}',
                'row': int(i),
                'col': int(j),
            }
            for key, arr in features_dict.items():
                val = arr[i, j]
                if isinstance(val, (np.integer,)):
                    properties[key] = int(val)
                elif isinstance(val, (np.floating,)):
                    properties[key] = round(float(val), 4)
                else:
                    properties[key] = val

            if 'lulc' in properties:
                properties['lulc_name'] = lulc_names.get(properties['lulc'], 'unknown')

            feature = {
                'type': 'Feature',
                'geometry': {
                    'type': 'Point',
                    'coordinates': [round(float(lons[i, j]), 6), round(float(lats[i, j]), 6)]
                },
                'properties': properties
            }
            features.append(feature)

    return {
        'type': 'FeatureCollection',
        'features': features
    }


def main():
    print("=" * 60)
    print("AETHER-COOL — Sample Data Generator")
    print("=" * 60)

    # Create output directory
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # Generate grid coordinates
    print("\n[1/9] Generating grid coordinates (50x50, centered on Delhi)...")
    lat_range = np.linspace(
        CENTER_LAT - GRID_SIZE / 2 * PIXEL_SIZE_DEG,
        CENTER_LAT + GRID_SIZE / 2 * PIXEL_SIZE_DEG,
        GRID_SIZE
    )
    lon_range = np.linspace(
        CENTER_LON - GRID_SIZE / 2 * PIXEL_SIZE_DEG,
        CENTER_LON + GRID_SIZE / 2 * PIXEL_SIZE_DEG,
        GRID_SIZE
    )
    lons, lats = np.meshgrid(lon_range, lat_range)

    # Generate features
    print("[2/9] Generating LULC zones...")
    zones = generate_urban_zones(GRID_SIZE)

    print("[3/9] Generating building density...")
    building_density = generate_building_density(zones)

    print("[4/9] Generating NDVI (vegetation)...")
    ndvi = generate_ndvi(zones)

    print("[5/9] Generating surface albedo...")
    albedo = generate_albedo(zones)

    print("[6/9] Generating sky view factor...")
    svf = generate_svf(zones)

    print("[7/9] Computing distance to water bodies...")
    dist_water = compute_distance_to_water(zones)

    print("[8/9] Computing Land Surface Temperature (physics-based)...")
    lst = compute_lst(ndvi, albedo, building_density, svf, dist_water, zones)

    print("[9/9] Generating population & vulnerability data...")
    population = generate_population(zones)
    vulnerability = generate_vulnerability_index(zones)

    # Build features dict
    features_dict = {
        'lst': lst,
        'ndvi': ndvi,
        'albedo': albedo,
        'building_density': building_density,
        'svf': svf,
        'dist_water': dist_water,
        'lulc': zones,
        'population': population,
        'vulnerability': vulnerability
    }

    # Save GeoJSON
    print("\nSaving GeoJSON...")
    geojson = build_geojson(lats, lons, features_dict)
    geojson_path = os.path.join(OUTPUT_DIR, 'city_grid.geojson')
    with open(geojson_path, 'w') as f:
        json.dump(geojson, f, indent=2)
    print(f"  → {geojson_path} ({len(geojson['features'])} features)")

    # Save temporal trends
    print("Saving temporal trends...")
    diurnal = generate_diurnal_trends()
    seasonal = generate_seasonal_trends()
    trends = {'diurnal': diurnal, 'seasonal': seasonal}
    trends_path = os.path.join(OUTPUT_DIR, 'temporal_trends.json')
    with open(trends_path, 'w') as f:
        json.dump(trends, f, indent=2)
    print(f"  → {trends_path}")

    # Save numpy arrays for ML training
    print("Saving numpy arrays for ML pipeline...")
    np_dir = os.path.join(OUTPUT_DIR, 'numpy')
    os.makedirs(np_dir, exist_ok=True)

    for name, arr in features_dict.items():
        np.save(os.path.join(np_dir, f'{name}.npy'), arr)

    np.save(os.path.join(np_dir, 'lats.npy'), lats)
    np.save(os.path.join(np_dir, 'lons.npy'), lons)
    print(f"  → {np_dir}/ (11 .npy files)")

    # Save driver importance (SHAP-like)
    print("Saving driver importance rankings...")
    drivers = [
        {'driver': 'NDVI', 'importance': 3.21, 'direction': 'negative',
         'description': 'More vegetation → Lower LST'},
        {'driver': 'Surface Albedo', 'importance': 2.83, 'direction': 'negative',
         'description': 'Higher reflectance → Lower LST'},
        {'driver': 'Sky View Factor', 'importance': 2.14, 'direction': 'positive',
         'description': 'Open sky → More solar exposure'},
        {'driver': 'Building Density', 'importance': 1.92, 'direction': 'positive',
         'description': 'More buildings → Higher thermal mass'},
        {'driver': 'Distance to Water', 'importance': 1.43, 'direction': 'positive',
         'description': 'Farther from water → Less evaporative cooling'},
        {'driver': 'Impervious Surface', 'importance': 1.18, 'direction': 'positive',
         'description': 'More concrete → Higher heat absorption'},
        {'driver': 'Wind Speed', 'importance': 0.82, 'direction': 'negative',
         'description': 'More wind → Better convective cooling'}
    ]
    drivers_path = os.path.join(OUTPUT_DIR, 'driver_importance.json')
    with open(drivers_path, 'w') as f:
        json.dump(drivers, f, indent=2)
    print(f"  → {drivers_path}")

    # Save intervention templates
    print("Saving intervention templates...")
    interventions = [
        {'type': 'tree_planting', 'name': 'Urban Tree Planting',
         'avg_delta_t': -3.5, 'cost_per_sqm': 22, 'cost_per_degree': 6.3,
         'mechanism': 'Evapotranspiration + Shade'},
        {'type': 'cool_roofs', 'name': 'Cool Roofs (High Albedo)',
         'avg_delta_t': -1.8, 'cost_per_sqm': 10, 'cost_per_degree': 5.6,
         'mechanism': 'Solar reflectance increase'},
        {'type': 'green_roofs', 'name': 'Green Roofs',
         'avg_delta_t': -2.2, 'cost_per_sqm': 60, 'cost_per_degree': 27.3,
         'mechanism': 'Evapotranspiration + Insulation'},
        {'type': 'albedo_paint', 'name': 'Albedo Paint on Roads',
         'avg_delta_t': -1.0, 'cost_per_sqm': 7, 'cost_per_degree': 7.0,
         'mechanism': 'Surface reflectance increase'},
        {'type': 'water_bodies', 'name': 'Water Features / Ponds',
         'avg_delta_t': -2.0, 'cost_per_sqm': 120, 'cost_per_degree': 60.0,
         'mechanism': 'Evaporative cooling'},
        {'type': 'permeable_pavement', 'name': 'Permeable Pavements',
         'avg_delta_t': -1.0, 'cost_per_sqm': 35, 'cost_per_degree': 35.0,
         'mechanism': 'Reduced heat storage + drainage'}
    ]
    interventions_path = os.path.join(OUTPUT_DIR, 'interventions.json')
    with open(interventions_path, 'w') as f:
        json.dump(interventions, f, indent=2)
    print(f"  → {interventions_path}")

    # Summary statistics
    print("\n" + "=" * 60)
    print("DATA GENERATION COMPLETE")
    print("=" * 60)
    print(f"\nCity Grid: {GRID_SIZE}×{GRID_SIZE} = {GRID_SIZE**2} pixels")
    print(f"Center: {CENTER_LAT}°N, {CENTER_LON}°E (Delhi)")
    print(f"LST Range: {lst.min():.1f}°C — {lst.max():.1f}°C")
    print(f"Mean LST: {lst.mean():.1f}°C")
    print(f"NDVI Range: {ndvi.min():.2f} — {ndvi.max():.2f}")
    print(f"Hotspot zones (LST > 45°C): {(lst > 45).sum()}")
    print(f"\nZone distribution:")
    lulc_names = {0: 'Commercial', 1: 'Residential', 2: 'Industrial', 3: 'Park', 4: 'Water'}
    for z, name in lulc_names.items():
        count = (zones == z).sum()
        mean_t = lst[zones == z].mean()
        print(f"  {name:15s}: {count:5d} pixels, mean LST = {mean_t:.1f}°C")

    print(f"\nAll files saved to: {os.path.abspath(OUTPUT_DIR)}")


if __name__ == '__main__':
    main()
