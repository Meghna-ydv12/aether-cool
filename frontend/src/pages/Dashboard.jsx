import { useState } from 'react'
import HeatMap from '../components/Map/HeatMap'
import DriverAnalysis from '../components/Charts/DriverAnalysis'
import TemperatureTrend from '../components/Charts/TemperatureTrend'
import CostBenefit from '../components/Charts/CostBenefit'
import GlassCard from '../components/common/GlassCard'
import './Dashboard.css'

const STATS = [
  { label: 'Avg LST', value: '44.2°C', icon: '🌡️', trend: '+2.1°C vs 2020', color: '#ef4444' },
  { label: 'Hotspot Zones', value: '127', icon: '🔥', trend: '18% of city area', color: '#f97316' },
  { label: 'Max ΔT Possible', value: '-4.8°C', icon: '❄️', trend: 'With full intervention', color: '#06b6d4' },
  { label: 'Coverage', value: '89%', icon: '📍', trend: 'Population at risk', color: '#8b5cf6' },
]

export default function Dashboard({ selectedCity = 'Delhi NCR' }) {
  const [selectedZone, setSelectedZone] = useState(null)

  return (
    <div className="dashboard">
      {/* Summary Stats */}
      <div className="dashboard-stats">
        {STATS.map((stat, i) => (
          <div key={i} className="stat-card" style={{ '--stat-color': stat.color, animationDelay: `${i * 0.08}s` }}>
            <div className="stat-icon">{stat.icon}</div>
            <div className="stat-content">
              <p className="stat-value">{stat.value}</p>
              <p className="stat-label">{stat.label}</p>
              <p className="stat-trend">{stat.trend}</p>
            </div>
          </div>
        ))}
      </div>

      {/* Map Section */}
      <div className="dashboard-map-section">
        <HeatMap onZoneSelect={setSelectedZone} selectedCity={selectedCity} />
      </div>

      {/* Charts Grid */}
      <div className="dashboard-charts">
        <div className="chart-item">
          <DriverAnalysis />
        </div>
        <div className="chart-item">
          <TemperatureTrend />
        </div>
        <div className="chart-item">
          <CostBenefit />
        </div>
      </div>

      {/* Selected Zone Detail */}
      {selectedZone && (
        <div className="dashboard-zone-detail animate-slide-up">
          <GlassCard title={`Zone ${selectedZone.zone_id}`} icon="📍" accentColor="var(--accent-cyan)">
            <div className="zone-detail-grid">
              <div className="zone-metric">
                <span className="zone-metric-label">LST</span>
                <span className="zone-metric-value" style={{ color: selectedZone.lst > 45 ? '#ef4444' : '#10b981' }}>
                  {selectedZone.lst?.toFixed(1)}°C
                </span>
              </div>
              <div className="zone-metric">
                <span className="zone-metric-label">NDVI</span>
                <span className="zone-metric-value">{selectedZone.ndvi?.toFixed(2)}</span>
              </div>
              <div className="zone-metric">
                <span className="zone-metric-label">Albedo</span>
                <span className="zone-metric-value">{selectedZone.albedo?.toFixed(2)}</span>
              </div>
              <div className="zone-metric">
                <span className="zone-metric-label">Building Density</span>
                <span className="zone-metric-value">{(selectedZone.building_density * 100)?.toFixed(0)}%</span>
              </div>
            </div>
          </GlassCard>
        </div>
      )}
    </div>
  )
}
