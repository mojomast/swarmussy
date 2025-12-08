import React from 'react'

export const Renderer: React.FC<{ data?: any }> = ({ data }) => {
  return (
    <div aria-label="renderer" role="region" style={{ minHeight: 100 }}>
      <pre>{JSON.stringify(data, null, 2)}</pre>
    </div>
  )
}
