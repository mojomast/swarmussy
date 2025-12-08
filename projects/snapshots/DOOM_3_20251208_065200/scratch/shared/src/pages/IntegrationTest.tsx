import React, { useEffect, useState } from 'react'
import { healthCheck, levelLoadFromServer } from '../api'

export const IntegrationTest: React.FC = () => {
  const [health, setHealth] = useState<string>('unknown')
  const [level, setLevel] = useState<string | null>(null)

  useEffect(() => {
    ;(async () => {
      const h = await healthCheck()
      setHealth(h?.status ?? 'unknown')
    })()
  }, [])

  const runLevelLoad = async () => {
    const res = await levelLoadFromServer('test-level')
    if (res.ok) setLevel(JSON.stringify(res.level))
    else setLevel('load_failed')
  }

  return (
    <section aria-label="integration-tests" style={{ padding: 16 }}>
      <h2>Integration Tests</h2>
      <div>
        <button onClick={runLevelLoad} className="btn">Load Test Level</button>
      </div>
      <pre style={{ background: '#111', color: '#fff', padding: 12, borderRadius: 6, marginTop: 8 }}>{level ?? ''}</pre>
    </section>
  )
}
