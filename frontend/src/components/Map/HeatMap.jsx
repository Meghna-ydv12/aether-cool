import { useMemo } from 'react'
import { MapContainer, TileLayer, CircleMarker, Tooltip } from 'react-leaflet'
import { MOCK_HEATMAP_DATA } from '../../api/client'
import './HeatMap.css'

/* ── Colour helpers ──────────────────────────────────────────────────── */
function lstToColor(lst) {
  // Green (cool) → Yellow → Orange → Red (hot)
  const min = 32, max = 50;
  const t = Math.max(0, Math.min(1, (lst - min) / (max - min)));

  let r, g, b;
  if (t < 0.25) {
    // Green → Yellow-green
    r = Math.round(34 + t * 4 * (180 - 34));
    g = Math.round(197 - t * 4 * (197 - 180));
    b = Math.round(94 - t * 4 * 94);
  } else if (t < 0.5) {
    // Yellow-green → Yellow
    const s = (t - 0.25) * 4;
    r = Math.round(180 + s * (250 - 180));
    g = Math.round(180 + s * (204 - 180));
    b = Math.round(0);
  } else if (t < 0.75) {
    // Yellow → Orange
    const s = (t - 0.5) * 4;
    r = Math.round(250 + s * (255 - 250));
    g = Math.round(204 - s * (204 - 120));
    b = 0;
  } else {
    // Orange → Red
    const s = (t - 0.75) * 4;
    r = 255;
    g = Math.round(120 - s * 120);
    b = Math.round(s * 40);
  }
  return `rgb(${r},${g},${b})`;
}

function lstToOpacity(lst) {
  const min = 32, max = 50;
  const t = Math.max(0, Math.min(1, (lst - min) / (max - min)));
  return 0.35 + t * 0.55;
}

/* ── Legend Data ──────────────────────────────────────────────────────── */
const LEGEND_STOPS = [
  { temp: '32°C', color: lstToColor(32), label: 'Cool' },
  { temp: '37°C', color: lstToColor(37) },
  { temp: '41°C', color: lstToColor(41) },
  { temp: '45°C', color: lstToColor(45) },
  { temp: '50°C', color: lstToColor(50), label: 'Hot' },
];

export default function HeatMap({ data, height = '100%' }) {
  const points = data || MOCK_HEATMAP_DATA;
  const center = [28.6139, 77.2090];

  // Downsample for performance — show every 2nd point
  const visiblePoints = useMemo(() => {
    if (points.length <= 900) return points;
    return points.filter((_, i) => i % 2 === 0);
  }, [points]);

  return (
    <div className="heatmap-container" style={{ height }}>
      <MapContainer
        center={center}
        zoom={11}
        className="heatmap-leaflet"
        zoomControl={true}
        attributionControl={true}
      >
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OSM</a> &copy; <a href="https://carto.com/">CARTO</a>'
          url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
        />

        {visiblePoints.map((pt, idx) => (
          <CircleMarker
            key={idx}
            center={[pt.lat, pt.lng]}
            radius={6}
            pathOptions={{
              fillColor: lstToColor(pt.lst),
              fillOpacity: lstToOpacity(pt.lst),
              stroke: false,
            }}
          >
            <Tooltip direction="top" offset={[0, -5]} className="heatmap-tooltip">
              <div>
                <strong>{pt.lst}°C</strong>
                <br />
                <span style={{ fontSize: '0.7rem', opacity: 0.7 }}>
                  {pt.lat.toFixed(4)}, {pt.lng.toFixed(4)}
                </span>
              </div>
            </Tooltip>
          </CircleMarker>
        ))}
      </MapContainer>

      {/* Floating Legend */}
      <div className="heatmap-legend">
        <div className="heatmap-legend__title">Land Surface Temperature</div>
        <div className="heatmap-legend__bar">
          {LEGEND_STOPS.map((stop, i) => (
            <div key={i} className="heatmap-legend__stop">
              <div
                className="heatmap-legend__color"
                style={{ background: stop.color }}
              />
              <span className="heatmap-legend__temp">{stop.temp}</span>
            </div>
          ))}
        </div>
        <div className="heatmap-legend__labels">
          <span>Cool</span>
          <span>Hot</span>
        </div>
      </div>

      {/* Floating Stats */}
      <div className="heatmap-stats">
        <div className="heatmap-stats__item">
          <span className="heatmap-stats__value">{visiblePoints.length.toLocaleString()}</span>
          <span className="heatmap-stats__label">Grid Points</span>
        </div>
        <div className="heatmap-stats__divider" />
        <div className="heatmap-stats__item">
          <span className="heatmap-stats__value">30m</span>
          <span className="heatmap-stats__label">Resolution</span>
        </div>
      </div>
    </div>
  )
}
