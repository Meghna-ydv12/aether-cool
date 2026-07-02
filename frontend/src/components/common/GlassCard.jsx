import './GlassCard.css'

export default function GlassCard({
  children,
  title,
  icon,
  accentColor,
  className = '',
  style = {},
  noPadding = false,
  animDelay = 0,
}) {
  return (
    <div
      className={`glass-card ${className}`}
      style={{
        '--accent-border': accentColor || 'var(--accent-teal)',
        animationDelay: `${animDelay}ms`,
        ...style,
      }}
    >
      {accentColor && <div className="glass-card__accent-bar" />}
      {(title || icon) && (
        <div className="glass-card__header">
          {icon && <span className="glass-card__icon">{icon}</span>}
          {title && <h3 className="glass-card__title">{title}</h3>}
        </div>
      )}
      <div className={`glass-card__body ${noPadding ? 'glass-card__body--no-pad' : ''}`}>
        {children}
      </div>
    </div>
  )
}
