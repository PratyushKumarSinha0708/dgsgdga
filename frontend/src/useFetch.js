import { useEffect, useState } from 'react'

// fn returns a promise; re-runs when any value in deps changes.
export function useFetch(fn, deps) {
  const [state, setState] = useState({ data: null, loading: true, error: null })
  const [tick, setTick] = useState(0)

  useEffect(() => {
    let cancelled = false
    setState(s => ({ ...s, loading: true, error: null }))
    fn()
      .then(data => !cancelled && setState({ data, loading: false, error: null }))
      .catch(e => !cancelled && setState({ data: null, loading: false, error: e.message }))
    return () => { cancelled = true }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [...deps, tick])

  return { ...state, retry: () => setTick(t => t + 1) }
}
