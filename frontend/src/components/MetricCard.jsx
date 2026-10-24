export default function MetricCard({ label, value, unit = 'MW', hint }) {
  return (
    <div className="card">
      <div className="card-label">{label}</div>
      <div className="card-value">
        {value == null || !Number.isFinite(value) ? '–' : Math.round(value).toLocaleString('en-GB')} <small>{unit}</small>
      </div>
      <div className="card-hint">{hint}</div>
    </div>
  )
}
