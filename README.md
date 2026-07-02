# 🌡️ AETHER-COOL

**AI-Enabled Thermodynamic Heat-mitigation & Energy-Resilient Cooling Optimizer for Urban Landscapes**

> Physics-informed AI that doesn't just map heat — it engineers its removal.

![Python](https://img.shields.io/badge/Python-3.11+-blue?logo=python)
![React](https://img.shields.io/badge/React-18-61DAFB?logo=react)
![PyTorch](https://img.shields.io/badge/PyTorch-2.0+-EE4C2C?logo=pytorch)
![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-009688?logo=fastapi)
![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?logo=docker)
![PostGIS](https://img.shields.io/badge/PostGIS-3.4-336791?logo=postgresql)

---

## 🔥 What is AETHER-COOL?

AETHER-COOL is a **full-stack geospatial AI platform** that identifies urban heat stress hotspots, quantifies the drivers of urban heating using explainable AI, and generates **budget-constrained, equity-aware cooling intervention strategies** using optimization algorithms.

### Core Innovation (USP)

| Component | What It Does | Why It Matters |
|-----------|-------------|----------------|
| 🧠 **PINN** | Physics-Informed Neural Network embedding the urban energy balance PDE | Predictions obey thermodynamic laws — generalizes to unseen cities |
| 📊 **SHAP Explainer** | Per-pixel driver contribution analysis | Know *why* each spot is hot, not just *where* |
| 🤖 **GA Optimizer** | Genetic Algorithm with budget + equity constraints | Tells you WHAT to build, WHERE, and HOW MUCH cooler it gets |

---

## 🏗️ Architecture

```
Frontend (React + Deck.gl + Leaflet)
    ↕ REST API
Backend (FastAPI)
    ├── ML Service (PyTorch PINN + SHAP)
    ├── Optimization Service (SciPy GA)
    └── Data Service (GeoJSON + PostGIS)
        ↕
Infrastructure (PostgreSQL/PostGIS + Redis + Docker)
```

---

## 🚀 Quick Start

### Prerequisites
- Docker & Docker Compose
- Node.js 18+ (for local frontend dev)
- Python 3.11+ (for local backend dev)

### Option 1: Docker Compose (Recommended)

```bash
# Clone the repository
git clone https://github.com/yourusername/aether-cool.git
cd aether-cool

# Copy environment file
cp .env.example .env

# Start all services
docker compose up --build
```

Access:
- **Frontend**: http://localhost:5173
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

### Option 2: Local Development

```bash
# Generate sample data
cd ml
python generate_sample_data.py

# Start backend
cd ../backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

# Start frontend (new terminal)
cd ../frontend
npm install
npm run dev
```

---

## 📊 Features

- 🗺️ **Multi-Resolution Heat Stress Mapping** — 30m pixel-level LST maps
- 📊 **SHAP Driver Analysis** — Per-pixel contribution of NDVI, albedo, SVF, building density
- 🧠 **Physics-Informed LST Prediction** — PINN with energy balance enforcement (R²=0.94)
- 🌡️ **Temporal Forecasting** — Diurnal and seasonal heat stress prediction
- 🏗️ **6-Type Intervention Simulator** — Green/cool roofs, trees, albedo paint, water, pavements
- 🤖 **Budget-Constrained Optimizer** — GA-based spatial intervention planning
- 📉 **Cost-Benefit Dashboard** — $/°C reduction, ROI ranking
- ⚖️ **Equity-Aware Prioritization** — Targets vulnerable neighborhoods first
- 🌍 **Transfer Learning** — Deploy to new cities with minimal data
- 📈 **Climate Projections** — SSP2-4.5 / SSP5-8.5 scenarios for 2030, 2050

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | React 18, Vite, Deck.gl, React-Leaflet, Recharts |
| Backend | FastAPI, Python 3.11 |
| AI/ML | PyTorch (PINN), SHAP, SciPy (Optimization) |
| Geospatial | GeoPandas, Rasterio, Shapely, PostGIS |
| Database | PostgreSQL + PostGIS, Redis |
| Deployment | Docker Compose |

---

## 📁 Project Structure

```
aether-cool/
├── frontend/          # React + Vite dashboard
├── backend/           # FastAPI REST API
│   └── app/
│       ├── api/       # Route handlers
│       ├── models/    # PINN, Optimizer, SHAP Explainer
│       ├── services/  # Data, ML, Geo services
│       └── schemas/   # Pydantic models
├── ml/                # Training pipeline
├── data/              # Sample data + trained models
└── docker-compose.yml
```

---

## 📜 License

MIT License — see [LICENSE](LICENSE) for details.

---

**Built with ❤️ for cooler cities** 🌡️→❄️
