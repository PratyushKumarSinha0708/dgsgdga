import {
  LineChart, Line, XAxis, YAxis, Tooltip, Legend, CartesianGrid, ResponsiveContainer,
} from 'recharts'

// rows: [{ time, forecast, actual, publishTime }]
export default function ForecastChart({ rows, xLabel = 'UK time' }) {
  const hasActual = rows.some(r => r.actual != null)
  return (
    <ResponsiveContainer width="100%" height={340} className={"graph"}>
      <LineChart data={rows} margin={{ bottom: 16, left: 8 }}>
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis dataKey="time" minTickGap={40} label={{ value: xLabel, position: 'insideBottom', offset: -10 }} />
        <YAxis tickFormatter={v => v.toLocaleString('en-GB')} label={{ value: 'MW', angle: -90, position: 'insideLeft' }} />
        <Tooltip formatter={(v) => (v == null ? '–' : `${Math.round(v).toLocaleString('en-GB')} MW`)}
          labelFormatter={(l, p) => `${l} (UK)${p?.[0]?.payload?.publishTime ? ` | published ${p[0].payload.publishTime.slice(0, 16).replace('T', ' ')}` : ''}`} />
        <Legend verticalAlign="top" />
        <Line dataKey="forecast" name="Forecast" stroke="#2563eb" dot={false} isAnimationActive={false} />
        {hasActual && <Line dataKey="actual" name="Actual" stroke="#16a34a" dot={false} isAnimationActive={false} />}
      </LineChart>
    </ResponsiveContainer>
  )
}
