import './Header.css'

export default function Header({ selectedCity = 'Delhi NCR' }) {
  return (
    <header className="header">
      <div className="header__left">
        <div className="header__logo">
          <div className="header__logo-icon">
            <svg width="28" height="28" viewBox="0 0 28 28" fill="none">
              <circle cx="14" cy="14" r="12" stroke="url(#logo-grad)" strokeWidth="2" />
              <circle cx="14" cy="14" r="7" fill="url(#logo-grad)" opacity="0.3" />
              <circle cx="14" cy="14" r="4" fill="url(#logo-grad)" />
              <defs>
                <linearGradient id="logo-grad" x1="0" y1="0" x2="28" y2="28">
                  <stop stopColor="#0d9488" />
                  <stop offset="1" stopColor="#06b6d4" />
                </linearGradient>
              </defs>
            </svg>
          </div>
          <div className="header__title-group">
            <h1 className="header__title">
              <span className="gradient-text">AETHER</span>
              <span className="header__title-separator">-</span>
              <span className="header__title-cool">COOL</span>
            </h1>
            <span className="header__subtitle">Urban Heat Intelligence Platform</span>
          </div>
        </div>
      </div>

      <div className="header__right">
        <div className="header__status">
          <span className="header__status-dot header__status-dot--live" />
          <span className="header__status-text">Live Data</span>
        </div>
        <div className="header__divider" />
        <div className="header__info">
          <span className="header__info-label">{selectedCity}</span>
          <span className="header__info-value">Monitoring Active</span>
        </div>
        <div className="header__divider" />
        <div className="header__info">
          <span className="header__info-label">Last Updated</span>
          <span className="header__info-value">
            {new Date().toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })}
          </span>
        </div>
      </div>
    </header>
  )
}
