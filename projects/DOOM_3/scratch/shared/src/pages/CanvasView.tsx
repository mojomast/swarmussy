import React from 'react'

export const CanvasView: React.FC<{ width?: number; height?: number }> = ({ width = 320, height = 180 }) => {
  // Simple placeholder canvas using div
  return (
    <div role="img" aria-label="canvas" style={{ width, height, background: '#111827', borderRadius: 6 }} />
  )
}
