import DriverAnalysis from '../components/Charts/DriverAnalysis'
import TemperatureTrend from '../components/Charts/TemperatureTrend'
import GlassCard from '../components/common/GlassCard'
import './Analysis.css'

const ZONE_DATA = [
  { id: 'Z-0625', lulc: 'Commercial', lst: 51.2, ndvi: 0.08, albedo: 0.14, density: 0.89, priority: 'Critical' },
  { id: 'Z-0626', lulc: 'Commercial', lst: 50.8, ndvi: 0.10, albedo: 0.15, density: 0.85, priority: 'Critical' },
  { id: 'Z-0001', lulc: 'Industrial', lst: 49.5, ndvi: 0.06, albedo: 0.11, density: 0.72, priority: 'Critical' },
  { id: 'Z-0675', lulc: 'Commercial', lst: 48.3, ndvi: 0.12, albedo: 0.16, density: 0.82, priority: 'High' },
  { id: 'Z-0050', lulc: 'Industrial', lst: 47.9, ndvi: 0.09, albedo: 0.13, density: 0.68, priority: 'High' },
  { id: 'Z-0800', lulc: 'Residential', lst: 44.2, ndvi: 0.28, albedo: 0.21, density: 0.58, priority: 'Medium' },
  { id: 'Z-0560', lulc: 'Residential', lst: 42.1, ndvi: 0.32, albedo: 0.23, density: 0.52, priority: 'Medium' },
  { id: 'Z-1250', lulc: 'Park', lst: 34.8, ndvi: 0.74, albedo: 0.20, density: 0.04, priority: 'Low' },
  { id: 'Z-1050', lulc: 'Water', lst: 30.2, ndvi: 0.05, albedo: 0.06, density: 0.00, priority: 'Low' },
]

function getPriorityBadge(priority) {
  const colors = { Critical: '#ef4444', High: '#f97316', Medium: '#f59e0b', Low: '#10b981' }
  return (
    <span className="priority-badge" style={{ '--badge-color': colors[priority] }}>
      {priority}
    </span>
  )
}

export default function Analysis() {
  return (
    <div className="analysis">
      <div className="analysis-header">
        <h2>🔬 Heat Driver Analysis</h2>
        <p>Zone-level breakdown of urban heat contributors with SHAP explainability</p>
      </div>

      <div className="analysis-charts">
        <div className="analysis-chart-large">
          <DriverAnalysis />
        </div>
        <div className="analysis-chart-large">
          <TemperatureTrend />
        </div>
      </div>

      <GlassCard title="Zone-Level Breakdown" icon="📋" accentColor="var(--accent-cyan)">
        <div className="analysis-table-wrapper">
          <table className="analysis-table">
            <thead>
              <tr>
                <th>Zone ID</th>
                <th>LULC</th>
                <th>LST (°C)</th>
                <th>NDVI</th>
                <th>Albedo</th>
                <th>Density</th>
                <th>Priority</th>
              </tr>
            </thead>
            <tbody>
              {ZONE_DATA.map((zone, i) => (
                <tr key={i} className="analysis-row" style={{ animationDelay: `${i * 0.04}s` }}>
                  <td className="zone-id-cell">{zone.id}</td>
                  <td>{zone.lulc}</td>
                  <td className="lst-cell" style={{ color: zone.lst > 45 ? '#ef4444' : zone.lst > 40 ? '#f59e0b' : '#10b981' }}>
                    {zone.lst}
                  </td>
                  <td>{zone.ndvi}</td>
                  <td>{zone.albedo}</td>
                  <td>{(zone.density * 100).toFixed(0)}%</td>
                  <td>{getPriorityBadge(zone.priority)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </GlassCard>
    </div>
  )
}
