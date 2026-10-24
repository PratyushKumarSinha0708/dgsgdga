export default function Status({ loading, error, empty, retry, children }) {
  if (loading) return <p className="status">Loading…</p>
  if (error) return (
    <p className="status error">{error} <button onClick={retry}>Retry</button></p>
  )
  if (empty) return <p className="status">No data for this selection.</p>
  return children
}
