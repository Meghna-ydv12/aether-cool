import { useState } from 'react'
import HeatMap from '../components/Map/HeatMap'
import InterventionPanel from '../components/Scenarios/InterventionPanel'
import ScenarioCompare from '../components/Scenarios/ScenarioCompare'
import GlassCard from '../components/common/GlassCard'
import './Optimizer.css'

export default function Optimizer() {
  const [isOptimizing, setIsOptimizing] = useState(false)
  const [optimizationDone, setOptimizationDone] = useState(false)
  const [budget, setBudget] = useState(100000)

  const handleOptimize = () => {
    setIsOptimizing(true)
    setOptimizationDone(false)
    // Simulate optimization
    setTimeout(() => {
      setIsOptimizing(false)
      setOptimizationDone(true)
    }, 3000)
  }

  const handleSimulate = (activeInterventions) => {
    console.log('Simulating:', activeInterventions)
  }

  return (
    <div className="optimizer">
      <div className="optimizer-header">
        <h2>🤖 Cooling Optimizer</h2>
        <p>Budget-constrained, equity-aware intervention planning powered by Genetic Algorithm</p>
      </div>

      {/* Budget Controls */}
      <GlassCard title="Budget Configuration" icon="💰" accentColor="var(--accent-emerald)">
        <div className="opt-budget-controls">
          <div className="opt-budget-input-group">
            <label className="opt-label">Total Budget ($)</label>
            <input
              type="number"
              value={budget}
              onChange={(e) => setBudget(parseInt(e.target.value) || 0)}
              className="opt-budget-input"
            />
          </div>
          <div className="opt-budget-presets">
            {[50000, 100000, 200000, 500000].map(preset => (
              <button
                key={preset}
                className={`opt-preset-btn ${budget === preset ? 'opt-preset-active' : ''}`}
                onClick={() => setBudget(preset)}
              >
                ${(preset / 1000)}K
              </button>
            ))}
          </div>
          <button
            className={`opt-run-btn ${isOptimizing ? 'opt-running' : ''}`}
            onClick={handleOptimize}
            disabled={isOptimizing}
          >
            {isOptimizing ? (
              <>
                <span className="opt-spinner"></span>
                Optimizing...
              </>
            ) : (
              '⚡ Run Optimization'
            )}
          </button>
        </div>
      </GlassCard>

      {/* Main Grid */}
      <div className="optimizer-grid">
        <div className="optimizer-left">
          <InterventionPanel onSimulate={handleSimulate} />
        </div>
        <div className="optimizer-center">
          <GlassCard title="Intervention Map Preview" icon="🗺️" accentColor="var(--accent-cyan)">
            <div className="optimizer-map-container">
              <HeatMap />
            </div>
          </GlassCard>
        </div>
        <div className="optimizer-right">
          <ScenarioCompare />
        </div>
      </div>

      {/* Optimization Results */}
      {optimizationDone && (
        <div className="opt-results animate-slide-up">
          <GlassCard title="Optimization Results" icon="✅" accentColor="var(--accent-emerald)">
            <div className="opt-results-grid">
              <div className="opt-result-stat">
                <span className="opt-result-label">Budget Used</span>
                <span className="opt-result-value">$92,400</span>
                <span className="opt-result-sub">92.4% of ${(budget/1000)}K</span>
              </div>
              <div className="opt-result-stat">
                <span className="opt-result-label">Avg ΔT</span>
                <span className="opt-result-value opt-delta">-3.6°C</span>
                <span className="opt-result-sub">Across 84 zones</span>
              </div>
              <div className="opt-result-stat">
                <span className="opt-result-label">Population Covered</span>
                <span className="opt-result-value">162K</span>
                <span className="opt-result-sub">78% of at-risk pop.</span>
              </div>
              <div className="opt-result-stat">
                <span className="opt-result-label">Equity Score</span>
                <span className="opt-result-value">0.78</span>
                <span className="opt-result-sub">Vulnerability-weighted</span>
              </div>
            </div>
          </GlassCard>
        </div>
      )}
    </div>
  )
}
