async function get(path, params = {}) {
  const qs = new URLSearchParams(params).toString()
  const res = await fetch(`/api/${path}${qs ? `?${qs}` : ''}`)
  if (!res.ok) {
    let detail = ''
    try { detail = (await res.json()).detail } catch { }
    throw new Error(detail || `Request failed (${res.status})`)
  }
  return res.json()
}

export const getMeta = () => get('meta')
export const getLatestForecast = (date, cutoff) => get('forecast/latest', { date, cutoff })
export const getAccuracy = (start, end, horizon_hours) =>
  get('accuracy', { start, end, horizon_hours })
export const getAccuracyByHorizon = (start, end) =>
  get('accuracy/by-horizon', { start, end })
