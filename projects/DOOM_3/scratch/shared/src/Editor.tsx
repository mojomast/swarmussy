import React from 'react'

export const Editor: React.FC = () => {
  return (
    <div aria-label="Level editor page" style={{ padding: 16 }}>
      <h2>Level Editor</h2>
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
        <div style={{ border: '1px solid #334', borderRadius: 8, padding: 8 }}>
          <div style={{ height: 240, background: '#111827' }} />
        </div>
        <div style={{ border: '1px solid #334', borderRadius: 8, padding: 8 }}>
          <div style={{ height: 60, background: '#1f2937' }} />
          <div style={{ height: 60, background: '#374151', marginTop: 8 }} />
          <div style={{ height: 60, background: '#1f2937', marginTop: 8 }} />
        </div>
      </div>
    </div>
  )
}
