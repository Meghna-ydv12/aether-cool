import { useState } from 'react'
import GlassCard from '../common/GlassCard'
import './InterventionPanel.css'

const INTERVENTIONS = [
  { id: 'tree_planting', name: 'Urban Tree Planting', icon: '🌳', color: '#10b981',
    maxDelta: -5.0, mechanism: 'Evapotranspiration + Shade' },
  { id: 'cool_roofs', name: 'Cool Roofs', icon: '🏠', color: '#06b6d4',
    maxDelta: -2.5, mechanism: 'Solar reflectance increase' },
  { id: 'green_roofs', name: 'Green Roofs', icon: '🌿', color: '#22c55e',
    maxDelta: -3.0, mechanism: 'Evapotranspiration + Insulation' },
  { id: 'albedo_paint', name: 'Albedo Paint', icon: '🎨', color: '#f59e0b',
    maxDelta: -1.5, mechanism: 'Surface reflectance boost' },
  { id: 'water_bodies', name: 'Water Features', icon: '💧', color: '#3b82f6',
    maxDelta: -3.0, mechanism: 'Evaporative cooling' },
  { id: 'permeable_pavement', name: 'Permeable Pavements', icon: '🧱', color: '#8b5cf6',
    maxDelta: -1.5, mechanism: 'Reduced heat storage' },
]

export default function InterventionPanel({ onSimulate }) {
  const [interventions, setInterventions] = useState(
    INTERVENTIONS.map(i => ({ ...i, enabled: false, intensity: 50 }))
  )

  const toggleIntervention = (id) => {
    setInterventions(prev => prev.map(i =>
      i.id === id ? { ...i, enabled: !i.enabled } : i
    ))
  }

  const setIntensity = (id, value) => {
    setInterventions(prev => prev.map(i =>
      i.id === id ? { ...i, intensity: value } : i
    ))
  }

  const activeCount = interventions.filter(i => i.enabled).length
  const estimatedDelta = interventions
    .filter(i => i.enabled)
    .reduce((sum, i) => sum + (i.maxDelta * i.intensity / 100), 0)

  return (
    <GlassCard title="Intervention Simulator" icon="🏗️" accentColor="var(--accent-teal)">
      <div className="ip-container">
        {interventions.map((item) => (
          <div key={item.id} className={`ip-card ${item.enabled ? 'ip-card-active' : ''}`}
               style={{ '--card-accent': item.color }}>
            <div className="ip-card-header">
              <div className="ip-card-info">
                <span className="ip-card-icon">{item.icon}</span>
                <div>
                  <p className="ip-card-name">{item.name}</p>
                  <p className="ip-card-mechanism">{item.mechanism}</p>
                </div>
              </div>
              <label className="ip-toggle">
                <input type="checkbox" checked={item.enabled}
                       onChange={() => toggleIntervention(item.id)} />
                <span className="ip-toggle-slider"></span>
              </label>
            </div>
            {item.enabled && (
              <div className="ip-card-controls">
                <div className="ip-slider-row">
                  <span className="ip-slider-label">Intensity</span>
                  <span className="ip-slider-value">{item.intensity}%</span>
                </div>
                <input type="range" min="10" max="100" value={item.intensity}
                       onChange={(e) => setIntensity(item.id, parseInt(e.target.value))}
                       className="ip-slider" style={{ '--slider-color': item.color }} />
                <p className="ip-delta">
                  Estimated: <strong>{(item.maxDelta * item.intensity / 100).toFixed(1)}°C</strong>
                </p>
              </div>
            )}
          </div>
        ))}

        <div className="ip-summary">
          <div className="ip-summary-stat">
            <span className="ip-summary-label">Active</span>
            <span className="ip-summary-value">{activeCount}/6</span>
          </div>
          <div className="ip-summary-stat">
            <span className="ip-summary-label">Est. ΔT</span>
            <span className="ip-summary-value ip-delta-value">{estimatedDelta.toFixed(1)}°C</span>
          </div>
          <button className="ip-simulate-btn"
                  onClick={() => onSimulate && onSimulate(interventions.filter(i => i.enabled))}
                  disabled={activeCount === 0}>
            ⚡ Simulate
          </button>
        </div>
      </div>
    </GlassCard>
  )
}
