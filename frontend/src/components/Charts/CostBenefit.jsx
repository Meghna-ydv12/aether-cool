import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from 'recharts'
import GlassCard from '../common/GlassCard'
import './CostBenefit.css'

const SAMPLE_DATA = [
  { intervention: 'Albedo Paint', costPerDegree: 5, color: '#10b981' },
  { intervention: 'Tree Planting', costPerDegree: 6, color: '#14b8a6' },
  { intervention: 'Cool Roofs', costPerDegree: 8, color: '#06b6d4' },
  { intervention: 'Green Roofs', costPerDegree: 22, color: '#f59e0b' },
  { intervention: 'Permeable Pave', costPerDegree: 28, color: '#f97316' },
  { intervention: 'Water Bodies', costPerDegree: 35, color: '#ef4444' },
]

const CustomTooltip = ({ active, payload }) => {
  if (active && payload && payload.length) {
    const data = payload[0].payload
    return (
      <div className="cb-tooltip">
        <p className="cb-tooltip-label">{data.intervention}</p>
        <p className="cb-tooltip-value">${data.costPerDegree} <span>per °C reduction</span></p>
      </div>
    )
  }
  return null
}

export default function CostBenefit() {
  return (
    <GlassCard title="Cost-Effectiveness ($/°C)" icon="💰" accentColor="var(--accent-emerald)">
      <div className="cb-chart-container">
        <ResponsiveContainer width="100%" height={260}>
          <BarChart data={SAMPLE_DATA} layout="vertical" margin={{ top: 5, right: 20, left: 10, bottom: 5 }}>
            <CartesianGrid strokeDasharray="3 3" horizontal={false} />
            <XAxis type="number" tick={{ fill: '#94a3b8', fontSize: 11 }} unit="$" />
            <YAxis dataKey="intervention" type="category" width={100} tick={{ fill: '#94a3b8', fontSize: 11 }} />
            <Tooltip content={<CustomTooltip />} cursor={{ fill: 'rgba(148, 163, 184, 0.05)' }} />
            <Bar dataKey="costPerDegree" radius={[0, 6, 6, 0]} barSize={20}>
              {SAMPLE_DATA.map((entry, index) => (
                <Cell key={index} fill={entry.color} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
        <p className="cb-insight">
          <span className="cb-best">🏆 Albedo Paint</span> is the most cost-effective at <strong>$5/°C</strong>
        </p>
      </div>
    </GlassCard>
  )
}
