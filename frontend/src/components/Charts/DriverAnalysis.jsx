import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell,
} from 'recharts'
import { MOCK_DRIVERS } from '../../api/client'
import './DriverAnalysis.css'

const COLORS = [
  '#0d9488', '#14b8a6', '#06b6d4', '#22d3ee',
  '#0891b2', '#0e7490', '#155e75',
];

function CustomTooltip({ active, payload }) {
  if (!active || !payload?.length) return null;
  const d = payload[0].payload;
  return (
    <div className="driver-tooltip">
      <div className="driver-tooltip__name">{d.name}</div>
      <div className="driver-tooltip__value">
        SHAP Impact: <strong>{d.value.toFixed(1)}°C</strong>
      </div>
    </div>
  );
}

export default function DriverAnalysis({ data, compact = false }) {
  const drivers = data || MOCK_DRIVERS;

  return (
    <div className="driver-analysis">
      {!compact && (
        <div className="driver-analysis__header">
          <h3 className="driver-analysis__title">Heat Driver Contributions</h3>
          <span className="driver-analysis__subtitle">SHAP Feature Importance (°C impact)</span>
        </div>
      )}
      <div className="driver-analysis__chart" style={{ height: compact ? 200 : 280 }}>
        <ResponsiveContainer width="100%" height="100%">
          <BarChart
            data={drivers}
            layout="vertical"
            margin={{ top: 5, right: 30, left: compact ? 80 : 120, bottom: 5 }}
            barCategoryGap="20%"
          >
            <CartesianGrid
              strokeDasharray="3 3"
              horizontal={false}
              stroke="rgba(148,163,184,0.08)"
            />
            <XAxis
              type="number"
              tick={{ fill: '#94a3b8', fontSize: 11 }}
              axisLine={{ stroke: 'rgba(148,163,184,0.1)' }}
              tickLine={false}
              domain={[0, 'auto']}
              unit="°C"
            />
            <YAxis
              type="category"
              dataKey="name"
              tick={{ fill: '#94a3b8', fontSize: compact ? 10 : 12 }}
              axisLine={false}
              tickLine={false}
              width={compact ? 75 : 115}
            />
            <Tooltip content={<CustomTooltip />} cursor={{ fill: 'rgba(13,148,136,0.06)' }} />
            <Bar dataKey="value" radius={[0, 6, 6, 0]} maxBarSize={24}>
              {drivers.map((_, i) => (
                <Cell key={i} fill={COLORS[i % COLORS.length]} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
