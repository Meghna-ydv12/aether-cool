import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, Area, Legend,
} from 'recharts'
import { MOCK_TRENDS } from '../../api/client'
import './TemperatureTrend.css'

function CustomTooltip({ active, payload, label }) {
  if (!active || !payload?.length) return null;
  return (
    <div className="trend-tooltip">
      <div className="trend-tooltip__month">{label}</div>
      {payload.map((entry, i) => (
        <div key={i} className="trend-tooltip__row">
          <span
            className="trend-tooltip__dot"
            style={{ background: entry.color }}
          />
          <span className="trend-tooltip__label">{entry.name}:</span>
          <strong className="trend-tooltip__val">{entry.value}°C</strong>
        </div>
      ))}
      {payload.length === 2 && (
        <div className="trend-tooltip__delta">
          ΔT: {(payload[0].value - payload[1].value).toFixed(1)}°C
        </div>
      )}
    </div>
  );
}

export default function TemperatureTrend({ data, compact = false }) {
  const trends = data || MOCK_TRENDS;

  return (
    <div className="temperature-trend">
      {!compact && (
        <div className="temperature-trend__header">
          <h3 className="temperature-trend__title">Temperature Trends</h3>
          <span className="temperature-trend__subtitle">Monthly LST — Current vs Projected</span>
        </div>
      )}
      <div className="temperature-trend__chart" style={{ height: compact ? 200 : 280 }}>
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={trends} margin={{ top: 10, right: 20, left: -10, bottom: 5 }}>
            <defs>
              <linearGradient id="currentGrad" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor="#f97316" stopOpacity={0.15} />
                <stop offset="100%" stopColor="#f97316" stopOpacity={0} />
              </linearGradient>
              <linearGradient id="interventionGrad" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor="#0d9488" stopOpacity={0.15} />
                <stop offset="100%" stopColor="#0d9488" stopOpacity={0} />
              </linearGradient>
            </defs>
            <CartesianGrid
              strokeDasharray="3 3"
              vertical={false}
              stroke="rgba(148,163,184,0.08)"
            />
            <XAxis
              dataKey="month"
              tick={{ fill: '#94a3b8', fontSize: 11 }}
              axisLine={{ stroke: 'rgba(148,163,184,0.1)' }}
              tickLine={false}
            />
            <YAxis
              tick={{ fill: '#94a3b8', fontSize: 11 }}
              axisLine={false}
              tickLine={false}
              domain={[15, 55]}
              unit="°"
            />
            <Tooltip content={<CustomTooltip />} />
            <Legend
              verticalAlign="top"
              height={30}
              iconType="circle"
              iconSize={8}
              wrapperStyle={{ fontSize: '0.75rem', color: '#94a3b8' }}
            />
            <Area
              type="monotone"
              dataKey="current"
              fill="url(#currentGrad)"
              stroke="none"
            />
            <Line
              type="monotone"
              dataKey="current"
              name="Current"
              stroke="#f97316"
              strokeWidth={2.5}
              dot={{ fill: '#f97316', r: 3, strokeWidth: 0 }}
              activeDot={{ r: 5, stroke: '#f97316', strokeWidth: 2, fill: '#0f172a' }}
            />
            <Area
              type="monotone"
              dataKey="intervention"
              fill="url(#interventionGrad)"
              stroke="none"
            />
            <Line
              type="monotone"
              dataKey="intervention"
              name="With Interventions"
              stroke="#0d9488"
              strokeWidth={2.5}
              strokeDasharray="6 3"
              dot={{ fill: '#0d9488', r: 3, strokeWidth: 0 }}
              activeDot={{ r: 5, stroke: '#0d9488', strokeWidth: 2, fill: '#0f172a' }}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
