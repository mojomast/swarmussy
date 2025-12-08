import React from 'react'

export const Viewer: React.FC = () => {
  return (
    <div aria-label="Canvas viewer page" style={{ padding: 16 }}>
      <h2>Canvas Viewer</h2>
      <div style={{ width: '100%', height: 420, background: '#0b1220', borderRadius: 8 }} />
    </div>
  )
}
