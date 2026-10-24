import { useState } from 'react'
import { getMeta } from './api'
import { useFetch } from './useFetch'
import Status from './components/Status'
import LatestForecastPage from './pages/LatestForecastPage'
import AccuracyPage from './pages/AccuracyPage'
import './App.css'

export default function App() {
  const [tab, setTab] = useState('latest')
  const { data: meta, loading, error, retry } = useFetch(getMeta, [])

  return (
    <div className="app">
      <h1 >Wind Forecast Desk</h1>
      <p className="note">GB national wind (Elexon WINDFOR vs FUELHH) for day-ahead buying decisions, January 2026.</p>
      <nav>
        <button className={tab === 'latest' ? 'active' : ''} onClick={() => setTab('latest')}>Latest forecast at decision time</button>
        <button className={tab === 'accuracy' ? 'active' : ''} onClick={() => setTab('accuracy')}>Forecast accuracy</button>
      </nav>
      <Status loading={loading} error={error} retry={retry}>
        {meta && (tab === 'latest' ? <LatestForecastPage meta={meta} /> : <AccuracyPage meta={meta} />)}
      </Status>
    </div>
  )
}
