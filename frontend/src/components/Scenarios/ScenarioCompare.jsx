import GlassCard from '../common/GlassCard'
import './ScenarioCompare.css'

const SCENARIOS = [
  {
    name: 'Maximum Cooling',
    icon: '❄️',
    recommended: false,
    totalDelta: -4.8,
    cost: 142000,
    populationCovered: 185000,
    equityScore: 0.62,
    topIntervention: 'Tree Planting (65%)',
    color: '#06b6d4',
  },
  {
    name: 'Budget Balanced',
    icon: '⚖️',
    recommended: true,
    totalDelta: -3.6,
    cost: 95000,
    populationCovered: 162000,
    equityScore: 0.78,
    topIntervention: 'Cool Roofs + Trees (50%)',
    color: '#10b981',
  },
  {
    name: 'Equity First',
    icon: '🤝',
    recommended: false,
    totalDelta: -2.9,
    cost: 88000,
    populationCovered: 210000,
    equityScore: 0.95,
    topIntervention: 'Trees in Vulnerable Zones (70%)',
    color: '#8b5cf6',
  },
]

function formatCurrency(val) {
  return '$' + (val / 1000).toFixed(0) + 'K'
}

export default function ScenarioCompare() {
  return (
    <GlassCard title="Scenario Comparison" icon="📊" accentColor="var(--accent-cyan)">
      <div className="sc-container">
        {SCENARIOS.map((scenario, idx) => (
          <div key={idx} className={`sc-card ${scenario.recommended ? 'sc-card-recommended' : ''}`}
               style={{ '--sc-accent': scenario.color, animationDelay: `${idx * 0.1}s` }}>
            {scenario.recommended && <div className="sc-badge">✨ Recommended</div>}
            <div className="sc-header">
              <span className="sc-icon">{scenario.icon}</span>
              <h4 className="sc-name">{scenario.name}</h4>
            </div>
            <div className="sc-metrics">
              <div className="sc-metric">
                <span className="sc-metric-label">Avg ΔT</span>
                <span className="sc-metric-value sc-delta">{scenario.totalDelta}°C</span>
              </div>
              <div className="sc-metric">
                <span className="sc-metric-label">Cost</span>
                <span className="sc-metric-value">{formatCurrency(scenario.cost)}</span>
              </div>
              <div className="sc-metric">
                <span className="sc-metric-label">Population</span>
                <span className="sc-metric-value">{(scenario.populationCovered / 1000).toFixed(0)}K</span>
              </div>
              <div className="sc-metric">
                <span className="sc-metric-label">Equity</span>
                <div className="sc-equity-bar">
                  <div className="sc-equity-fill" style={{ width: `${scenario.equityScore * 100}%` }}></div>
                  <span className="sc-equity-text">{(scenario.equityScore * 100).toFixed(0)}%</span>
                </div>
              </div>
            </div>
            <p className="sc-top-intervention">
              🔧 {scenario.topIntervention}
            </p>
          </div>
        ))}
      </div>
    </GlassCard>
  )
}
