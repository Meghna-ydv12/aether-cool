import { useState } from 'react'
import { NavLink } from 'react-router-dom'
import './Sidebar.css'

const NAV_ITEMS = [
  {
    path: '/',
    label: 'Dashboard',
    icon: (
      <svg width="20" height="20" viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth="1.5">
        <rect x="2" y="2" width="7" height="7" rx="1.5" />
        <rect x="11" y="2" width="7" height="4" rx="1.5" />
        <rect x="2" y="11" width="7" height="7" rx="1.5" />
        <rect x="11" y="8" width="7" height="10" rx="1.5" />
      </svg>
    ),
  },
  {
    path: '/analysis',
    label: 'Analysis',
    icon: (
      <svg width="20" height="20" viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth="1.5">
        <polyline points="2,16 6,10 10,13 14,6 18,2" />
        <circle cx="6" cy="10" r="1.5" fill="currentColor" />
        <circle cx="10" cy="13" r="1.5" fill="currentColor" />
        <circle cx="14" cy="6" r="1.5" fill="currentColor" />
      </svg>
    ),
  },
  {
    path: '/optimizer',
    label: 'Optimizer',
    icon: (
      <svg width="20" height="20" viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth="1.5">
        <circle cx="10" cy="10" r="8" />
        <path d="M10 6v4l3 2" />
        <path d="M14 3l2 2M6 3L4 5" />
      </svg>
    ),
  },
]

const CITIES = ['Delhi NCR', 'Mumbai', 'Bangalore', 'Chennai', 'Hyderabad', 'Kolkata']

const LAYERS = [
  { id: 'lst', label: 'Land Surface Temp', defaultOn: true },
  { id: 'ndvi', label: 'NDVI (Vegetation)', defaultOn: false },
  { id: 'lulc', label: 'Land Use / Land Cover', defaultOn: false },
  { id: 'interventions', label: 'Interventions', defaultOn: true },
]

export default function Sidebar({ collapsed, onToggle }) {
  const [selectedCity, setSelectedCity] = useState('Delhi NCR')
  const [layers, setLayers] = useState(
    LAYERS.reduce((acc, l) => ({ ...acc, [l.id]: l.defaultOn }), {})
  )

  const toggleLayer = (id) => {
    setLayers((prev) => ({ ...prev, [id]: !prev[id] }))
  }

  return (
    <aside className={`sidebar ${collapsed ? 'sidebar--collapsed' : ''}`}>
      {/* Toggle button */}
      <button className="sidebar__toggle" onClick={onToggle} title={collapsed ? 'Expand' : 'Collapse'}>
        <svg
          width="18"
          height="18"
          viewBox="0 0 18 18"
          fill="none"
          stroke="currentColor"
          strokeWidth="1.5"
          style={{ transform: collapsed ? 'rotate(180deg)' : 'none', transition: 'transform 0.3s' }}
        >
          <polyline points="12,4 6,9 12,14" />
        </svg>
      </button>

      {/* Navigation */}
      <nav className="sidebar__nav">
        <div className="sidebar__section-label">{!collapsed && 'Navigation'}</div>
        {NAV_ITEMS.map((item) => (
          <NavLink
            key={item.path}
            to={item.path}
            className={({ isActive }) =>
              `sidebar__nav-item ${isActive ? 'sidebar__nav-item--active' : ''}`
            }
            title={item.label}
          >
            <span className="sidebar__nav-icon">{item.icon}</span>
            {!collapsed && <span className="sidebar__nav-label">{item.label}</span>}
          </NavLink>
        ))}
      </nav>

      {/* Filters - only visible when expanded */}
      {!collapsed && (
        <div className="sidebar__filters">
          {/* City Selector */}
          <div className="sidebar__section">
            <div className="sidebar__section-label">Region</div>
            <select
              className="sidebar__select"
              value={selectedCity}
              onChange={(e) => setSelectedCity(e.target.value)}
            >
              {CITIES.map((city) => (
                <option key={city} value={city}>{city}</option>
              ))}
            </select>
          </div>

          {/* Date Range */}
          <div className="sidebar__section">
            <div className="sidebar__section-label">Date Range</div>
            <div className="sidebar__date-range">
              <input type="date" className="sidebar__date-input" defaultValue="2025-03-01" />
              <span className="sidebar__date-sep">to</span>
              <input type="date" className="sidebar__date-input" defaultValue="2025-06-15" />
            </div>
          </div>

          {/* Layer Toggles */}
          <div className="sidebar__section">
            <div className="sidebar__section-label">Map Layers</div>
            <div className="sidebar__layers">
              {LAYERS.map((layer) => (
                <label key={layer.id} className="sidebar__layer-toggle">
                  <div className="sidebar__toggle-switch">
                    <input
                      type="checkbox"
                      checked={layers[layer.id]}
                      onChange={() => toggleLayer(layer.id)}
                    />
                    <span className="sidebar__toggle-slider" />
                  </div>
                  <span className="sidebar__layer-label">{layer.label}</span>
                </label>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Bottom brand mark */}
      {!collapsed && (
        <div className="sidebar__footer">
          <span className="sidebar__version">v1.0.0-alpha</span>
        </div>
      )}
    </aside>
  )
}
