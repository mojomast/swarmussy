import React, { useEffect, useMemo, useState } from 'react'
import { LevelData, levelLoadFromServer, levelSaveFromServer } from '../api'

// Minimal Level Editor: left pane shows a grid canvas, right pane shows inspector controls
const LevelEditor: React.FC = () => {
  const [levelId, setLevelId] = useState<string>('')
  const [name, setName] = useState<string>('New Level')
  const [width, setWidth] = useState<number>(8)
  const [height, setHeight] = useState<number>(8)
  const [grid, setGrid] = useState<number[][]>(Array.from({ length: height }, () => Array.from({ length: width }, () => 0)))
  const [loading, setLoading] = useState<boolean>(false)
  const [status, setStatus] = useState<string>('idle')

  // Ensure grid size matches width x height
  useEffect(() => {
    resizeGrid(width, height)
    // eslint-disable-next-line
  }, [width, height])

  const resizeGrid = (w: number, h: number) => {
    setGrid((g) => {
      const newGrid = Array.from({ length: h }, () => Array.from({ length: w }, () => 0))
      for (let y = 0; y < Math.min(g.length, h); y++) {
        for (let x = 0; x < Math.min(g[0]?.length ?? 0, w); x++) {
          newGrid[y][x] = g[y][x] ?? 0
        }
      }
      return newGrid
    })
  }

  const toggleCell = (x: number, y: number) => {
    setGrid((g) => {
      const copy = g.map((row) => row.slice())
      if (!copy[y]) copy[y] = []
      copy[y][x] = (copy[y][x] ?? 0) ? 0 : 1
      return copy
    })
  }

  const handleLoad = async () => {
    if (!levelId) return
    setLoading(true)
    setStatus('loading')
    try {
      const res = await levelLoadFromServer(levelId)
      if (res.ok && res.level) {
        const lvl = res.level
        setName(lvl.name)
        setWidth(lvl.width)
        setHeight(lvl.height)
        if (lvl.grid && lvl.grid.length) {
          setGrid(lvl.grid)
        }
        setStatus('loaded')
      } else {
        setStatus('load_failed')
      }
    } catch {
      setStatus('error')
    } finally {
      setLoading(false)
    }
  }

  const handleSave = async () => {
    const data: LevelData = {
      id: levelId || 'new',
      name,
      width,
      height,
      grid,
    }
    const res = await levelSaveFromServer(data.id, data)
    if (res.ok) {
      setStatus('saved')
    } else {
      setStatus('save_failed')
    }
  }

  const randomize = () => {
    setGrid((g) => g.map((row) => row.map(() => (Math.random() > 0.5 ? 1 : 0))))
  }

  const cellSize = useMemo(() => {
    // compute reasonable cell size for a fixed canvas width
    const maxW = Math.max(width, 8)
    const maxH = Math.max(height, 8)
    const base = 22
    const w = Math.max(12, Math.min(40, base))
    return w
  }, [width, height])

  const gridStyle: React.CSSProperties = {
    display: 'grid',
    gridTemplateColumns: `repeat(${width}, ${cellSize}px)`,
    gridAutoRows: `${cellSize}px`,
    gap: 2,
    background: '#1b1f2a',
    padding: 8,
    borderRadius: 8,
  }

  return (
    <div aria-label="Level Editor" className="grid grid-editor" style={{ minHeight: 540 }}>
      <section className="panel panel-left" aria-label="Level grid editor" style={{ display: 'flex', flexDirection: 'column' }}>
        <h3>Level Editor</h3>
        <div
          className="canvas-placeholder"
          role="region"
          aria-label="Canvas area"
          style={{ flex: 1, padding: 8, display: 'flex', alignItems: 'center', justifyContent: 'center', minHeight: 320 }}
        >
          <div style={gridStyle} aria-label="level-grid" role="grid">
            {grid.map((row, y) => row.map((val, x) => (
              <div key={`${x}-${y}`} role="gridcell" aria-label={`cell ${x},${y}`} onClick={() => toggleCell(x, y)} style={{ width: cellSize, height: cellSize, background: val ? '#4ade80' : '#111827', borderRadius: 3, border: '1px solid #333' }} />
            )))}
          </div>
        </div>
        <div className="toolbox" style={{ display: 'flex', gap: 8, marginTop: 8 }}>
          <button className="btn" onClick={randomize} aria-label="Randomize grid">Randomize</button>
          <button className="btn" onClick={handleSave} aria-label="Save level">Save</button>
          <button className="btn" onClick={handleLoad} aria-label="Load level">Load</button>
        </div>
        <div aria-live="polite" style={{ marginTop: 6, minHeight: 20, color: '#9ad' }}>{status}</div>
      </section>
      <section className="panel panel-right" aria-label="Inspector and HUD" style={{ display: 'flex', flexDirection: 'column' }}>
        <h3>Inspector</h3>
        <div className="hud" aria-label="level-insp" style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8 }}>
          <div className="hud-item" style={{ gridColumn: 'span 2' }}>
            <label style={{ display: 'block', fontSize: 12, color: '#9bd' }}>Level ID</label>
            <input value={levelId} onChange={(e) => setLevelId(e.target.value)} placeholder="level-id" style={{ width: '100%', padding: 6, borderRadius: 4, border: '1px solid #333', background: '#111' }} />
          </div>
          <div className="hud-item">
            <label style={{ display: 'block', fontSize: 12, color: '#9bd' }}>Name</label>
            <input value={name} onChange={(e) => setName(e.target.value)} placeholder="Level name" style={{ width: '100%', padding: 6, borderRadius: 4, border: '1px solid #333', background: '#111' }} />
          </div>
          <div className="hud-item" style={{ display: 'flex', flexDirection: 'column' }}>
            <label style={{ fontSize: 12, color: '#9bd' }}>Width</label>
            <input type="number" value={width} min={1} max={64} onChange={(e) => setWidth(parseInt(e.target.value || '0', 10))} style={{ width: '100%', padding: 6, borderRadius: 4, border: '1px solid #333', background: '#111' }} />
          </div>
          <div className="hud-item" style={{ display: 'flex', flexDirection: 'column' }}>
            <label style={{ fontSize: 12, color: '#9bd' }}>Height</label>
            <input type="number" value={height} min={1} max={64} onChange={(e) => setHeight(parseInt(e.target.value || '0', 10))} style={{ width: '100%', padding: 6, borderRadius: 4, border: '1px solid #333', background: '#111' }} />
          </div>
        </div>
        <div className="inventory" aria-label="Inventory inspector" style={{ marginTop: 8 }}>
          <h4>Grid Preview</h4>
          <div className="inventory-grid" style={{ display: 'grid', gridTemplateColumns: `repeat(${Math.min(6, width)}, 1fr)`, gap: 6 }}>
            {grid.flat().slice(0, Math.min(width * height, 18)).map((v, idx) => (
              <div key={idx} className="inventory-slot" style={{ height: 28, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>{v}</div>
            ))}
          </div>
        </div>
      </section>
    </div>
  )
}

export default LevelEditor
