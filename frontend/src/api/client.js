import axios from 'axios';

// In production monolith, VITE_API_URL is set to empty string so it calls relative /api paths
const API_BASE_URL = import.meta.env.VITE_API_URL !== undefined ? import.meta.env.VITE_API_URL : 'http://localhost:8000';

const client = axios.create({
  baseURL: API_BASE_URL,
  timeout: 15000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor
client.interceptors.request.use(
  (config) => {
    console.log(`[API] ${config.method?.toUpperCase()} ${config.url}`);
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor
client.interceptors.response.use(
  (response) => response,
  (error) => {
    console.warn('[API] Request failed, using mock data:', error.message);
    return Promise.reject(error);
  }
);

// ── Mock Data ─────────────────────────────────────────────────────────────

export const MOCK_HEATMAP_DATA = (() => {
  const points = [];
  const centerLat = 28.6139;
  const centerLng = 77.2090;
  for (let i = 0; i < 50; i++) {
    for (let j = 0; j < 50; j++) {
      const lat = centerLat - 0.15 + (i / 50) * 0.30;
      const lng = centerLng - 0.15 + (j / 50) * 0.30;
      const distFromCenter = Math.sqrt(
        Math.pow(lat - centerLat, 2) + Math.pow(lng - centerLng, 2)
      );
      const base = 38 + Math.random() * 8;
      const urbanHeat = Math.max(0, 6 - distFromCenter * 40);
      const noise = (Math.sin(lat * 100) * Math.cos(lng * 100)) * 2;
      const lst = base + urbanHeat + noise;
      points.push({ lat, lng, lst: Math.round(lst * 10) / 10 });
    }
  }
  return points;
})();

export const MOCK_DRIVERS = [
  { name: 'NDVI (Vegetation)', value: 3.2, fullMark: 4 },
  { name: 'Albedo', value: 2.8, fullMark: 4 },
  { name: 'Sky View Factor', value: 2.1, fullMark: 4 },
  { name: 'Building Density', value: 1.9, fullMark: 4 },
  { name: 'Distance to Water', value: 1.4, fullMark: 4 },
  { name: 'Impervious Surface', value: 1.2, fullMark: 4 },
  { name: 'Wind Speed', value: 0.8, fullMark: 4 },
];

export const MOCK_TRENDS = [
  { month: 'Jan', current: 22, intervention: 21 },
  { month: 'Feb', current: 25, intervention: 23 },
  { month: 'Mar', current: 32, intervention: 29 },
  { month: 'Apr', current: 38, intervention: 34 },
  { month: 'May', current: 44, intervention: 39 },
  { month: 'Jun', current: 48, intervention: 42 },
  { month: 'Jul', current: 46, intervention: 40 },
  { month: 'Aug', current: 43, intervention: 38 },
  { month: 'Sep', current: 39, intervention: 35 },
  { month: 'Oct', current: 33, intervention: 30 },
  { month: 'Nov', current: 27, intervention: 25 },
  { month: 'Dec', current: 23, intervention: 22 },
];

export const MOCK_COST_BENEFIT = [
  { name: 'Albedo Paint', cost: 5, color: '#10b981' },
  { name: 'Tree Planting', cost: 6, color: '#14b8a6' },
  { name: 'Cool Roofs', cost: 8, color: '#06b6d4' },
  { name: 'Green Roofs', cost: 22, color: '#f59e0b' },
  { name: 'Permeable Pave', cost: 28, color: '#f97316' },
  { name: 'Water Bodies', cost: 35, color: '#ef4444' },
];

export const MOCK_SCENARIOS = [
  {
    id: 1,
    name: 'Maximum Cooling',
    deltaT: -4.8,
    cost: 2400000,
    population: 3200000,
    equity: 0.72,
    recommended: false,
  },
  {
    id: 2,
    name: 'Budget Balanced',
    deltaT: -3.6,
    cost: 850000,
    population: 2800000,
    equity: 0.85,
    recommended: true,
  },
  {
    id: 3,
    name: 'Equity First',
    deltaT: -2.9,
    cost: 1100000,
    population: 3500000,
    equity: 0.95,
    recommended: false,
  },
];

// ── API Functions with Mock Fallback ──────────────────────────────────────

export async function fetchHeatmapData() {
  try {
    const res = await client.get('/api/heatmap');
    return res.data;
  } catch {
    return MOCK_HEATMAP_DATA;
  }
}

export async function fetchDrivers() {
  try {
    const res = await client.get('/api/drivers/summary');
    return res.data;
  } catch {
    return MOCK_DRIVERS;
  }
}

export async function fetchTrends() {
  try {
    const res = await client.get('/api/trends');
    return res.data;
  } catch {
    return MOCK_TRENDS;
  }
}

export async function runSimulation(params) {
  try {
    const res = await client.post('/api/simulate', params);
    return res.data;
  } catch {
    return {
      deltaT: -3.2,
      costEstimate: 920000,
      coveragePercent: 78,
    };
  }
}

export async function runOptimization(params) {
  try {
    const res = await client.post('/api/optimize', params);
    return res.data;
  } catch {
    return MOCK_SCENARIOS;
  }
}

export default client;
