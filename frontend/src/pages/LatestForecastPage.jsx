import { useState } from 'react'
import { getLatestForecast } from '../api'
import { useFetch } from '../useFetch'
import Status from '../components/Status'
import MetricCard from '../components/MetricCard'
import ForecastChart from '../components/ForecastChart'

const fmt = iso => (iso ? iso.slice(0, 16).replace('T', ' ') : '–')

export default function LatestForecastPage({ meta }) {
  const [date, setDate] = useState('2026-01-15')
  const [cutoff, setCutoff] = useState(meta.default_cutoff)

  const { data, loading, error, retry } = useFetch(
    () => getLatestForecast(date, cutoff), [date, cutoff]
  )

  const rows = data?.points ?? []
  const values = rows.map(r => r.forecast).filter(v => v != null)
  const avg = values.length ? values.reduce((a, b) => a + b, 0) / values.length : null

  return (
    <div>
      <div className="controls">
        <label>Delivery date
          <input type="date" value={date} min={meta.min_date} max={meta.max_date}
            onChange={e => e.target.value && setDate(e.target.value)} />
        </label>
        <label>Decision cutoff on D-1 (UK time)
          <input type="time" value={cutoff} onChange={e => e.target.value && setCutoff(e.target.value)} />
        </label>
      </div>

      <Status loading={loading} error={error} retry={retry} empty={!rows.length}>
        <p className="banner">
          Showing the latest wind forecast published at or before <b>{fmt(data?.cutoff_uk)}</b> (UK time)
          for delivery on <b>{date}</b>. Most recent forecast used was published at{' '}
          <b>{fmt(data?.latest_publish_time)}</b>.
        </p>

        <div className="cards">
          <MetricCard label="Average forecast" value={avg} hint="Typical wind output expected that day" />
          <MetricCard label="Min forecast" value={values.length ? Math.min(...values) : null} hint="Lowest expected wind, so the most power to buy" />
          <MetricCard label="Max forecast" value={values.length ? Math.max(...values) : null} hint="Highest expected wind" />
        </div>

        <ForecastChart rows={rows} />
        <p className="note">Green line (actual wind) appears because this delivery day is already in the past.</p>
      </Status>
    </div>
  )
}
