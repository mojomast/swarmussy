import React, { useEffect, useState } from 'react'
import { healthCheck } from '../api'

const HealthDashboard: React.FC = () => {
  const [health, setHealth] = useState<{ status: string; uptime?: number } | null>(null)

  useEffect(() => {
    let mounted = true
    const fetchHealth = async () => {
      const h = await healthCheck()
      if (mounted) setHealth(h as any)
    }
    fetchHealth()
    const interval = setInterval(fetchHealth, 10000)
    return () => {
      mounted = false
      clearInterval(interval)
    }
  }, [])

  return (
    <div className="status-bar" aria-label="Health status bar" role="status" style={{ display: 'flex', gap: 12, alignItems: 'center', padding: '6px 12px', borderTop: '1px solid #1b2a33', background: '#0f141a' }}>
      <span>Health: {health?.status ?? 'loading'}</span>
      {typeof health?.uptime === 'number' ? <span>Uptime: {health.uptime}s</span> : null}
    </div>
  )
}

export default HealthDashboard
