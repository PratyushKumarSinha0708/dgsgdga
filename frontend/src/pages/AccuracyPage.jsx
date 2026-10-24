import { useState } from 'react'
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, CartesianGrid, ResponsiveContainer,
  LineChart, Line, Legend,
} from 'recharts'
import { getAccuracy, getAccuracyByHorizon } from '../api'
import { useFetch } from '../useFetch'
import Status from '../components/Status'
import MetricCard from '../components/MetricCard'
import ForecastChart from '../components/ForecastChart'

export default function AccuracyPage({ meta }) {
  const initial = { start: meta.min_date, end: meta.max_date, horizon: 24 }
  const [form, setForm] = useState(initial)
  const [applied, setApplied] = useState(initial) // fetch only when Apply is clicked
  const set = k => e => setForm({ ...form, [k]: e.target.value })

  const acc = useFetch(
    () => getAccuracy(applied.start, applied.end, applied.horizon), [applied]
  )
  const byH = useFetch(
    () => getAccuracyByHorizon(applied.start, applied.end), [applied.start, applied.end]
  )
  const m = acc.data?.metrics

  return (
    <div>
      <div className="controls">
        <label>Start (delivery day)
          <input type="date" value={form.start} min={meta.min_date} max={meta.max_date} onChange={set('start')} />
        </label>
        <label>End (delivery day)
          <input type="date" value={form.end} min={meta.min_date} max={meta.max_date} onChange={set('end')} />
        </label>
        <label>Forecast made at least {form.horizon}h ahead
          <input type="range" min="1" max="48" value={form.horizon} onChange={set('horizon')} />
        </label>
        <button onClick={() => setApplied(form)}>Apply</button>
      </div>

      <Status loading={acc.loading} error={acc.error} retry={acc.retry} empty={!m}>
        <p className="note">
          Error = actual − forecast. <b>Negative</b> means wind came in below forecast, so extra power had to be bought.
          Based on {m?.n?.toLocaleString('en-GB')} forecast points.
        </p>
        <div className="cards">
          <MetricCard label="MAE" value={m?.mae} hint="On average, the forecast is off by this much" />
          <MetricCard label="RMSE" value={m?.rmse} hint="Like MAE, but big misses count more" />
          <MetricCard label="Bias" value={m?.bias} hint="Positive = wind under-forecast on average; negative = over-forecast" />
          <MetricCard label="P5 error" value={m?.p5} hint="Wind came in this far below forecast (or worse) 1 time in 20: your downside buffer" />
          <MetricCard label="P95 error" value={m?.p95} hint="Wind came in this far above forecast (or more) 1 time in 20" />
          <MetricCard label="P99 absolute error" value={m?.abs_p99} hint="Worst-case buffer in either direction" />
        </div>

        <h3 style={{textAlign: 'center'}}>Forecast vs actual</h3>
        <ForecastChart rows={acc.data?.series ?? []} xLabel="UK time" />

        <h3 style={{textAlign: 'center'}}>Error distribution (actual − forecast, MW)</h3>
        <ResponsiveContainer width="100%" height={280} className={"graph"}>
          <BarChart data={acc.data?.histogram ?? []}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="bin" tickFormatter={v => v.toLocaleString('en-GB')} />
            <YAxis /><Tooltip />
            <Bar dataKey="count" name="Half-hours / hours" fill="#2563eb" />
          </BarChart>
        </ResponsiveContainer>
      </Status>

      <h3 style={{textAlign: 'center'}}>Error vs forecast horizon</h3>
      <Status loading={byH.loading} error={byH.error} retry={byH.retry} empty={!byH.data?.points?.length}>
        <ResponsiveContainer width="100%" height={280} className={"graph"}>
          <LineChart data={byH.data?.points ?? []} margin={{ bottom: 16 }}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="horizon" label={{ value: 'Hours ahead of delivery', position: 'insideBottom', offset: -10 }} />
            <YAxis label={{ value: 'MW', angle: -90, position: 'insideLeft' }} />
            <Tooltip /><Legend verticalAlign="top" />
            <Line dataKey="mae" name="MAE" stroke="#2563eb" dot={false} isAnimationActive={false} />
            <Line dataKey="abs_p90" name="P90 abs error" stroke="#dc2626" dot={false} isAnimationActive={false} />
          </LineChart>
        </ResponsiveContainer>
      </Status>
    </div>
  )
}
