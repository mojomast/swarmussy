import http from 'http'
import express from 'express'

export type LevelData = {
  id?: string
  name: string
  width: number
  height: number
  grid?: number[][]
}

export type InventoryItem = {
  id: string
  name: string
  icon?: string
}

export type GameStore = {
  levels: Record<string, LevelData>
  inventory?: InventoryItem[]
  player?: { id: string; x: number; y: number }
}

let bootTime = Date.now()

// Simple in-memory store builder for tests/routers
export function createStore(): GameStore {
  return {
    levels: {},
    inventory: [{ id: 'potion', name: 'Health Potion' }],
    player: { id: 'player', x: 0, y: 0 },
  }
}

export function health(): { status: string; uptime: number } {
  return { status: 'ok', uptime: Math.floor((Date.now() - bootTime) / 1000) }
}

export function levelLoad(store: GameStore, payload: { levelId: string }): { ok: boolean; level?: LevelData } {
  if (!payload?.levelId || payload.levelId.trim() === '') {
    return { ok: false, level: undefined as any }
  }
  let lvl = store.levels[payload.levelId]
  if (!lvl) {
    lvl = { id: payload.levelId, name: 'Untitled', width: 8, height: 8, grid: [] }
    store.levels[payload.levelId] = lvl
  }
  return { ok: true, level: lvl }
}

export function levelSave(store: GameStore, payload: { levelId: string; data?: any }): { ok: boolean; updatedAt?: number } {
  if (!payload?.levelId || payload.levelId.trim() === '') {
    return { ok: false, updatedAt: undefined }
  }
  const lvl = store.levels[payload.levelId]
  if (!lvl) {
    store.levels[payload.levelId] = { id: payload.levelId, name: 'Untitled', width: 8, height: 8, grid: [] }
  }
  return { ok: true, updatedAt: Date.now() }
}

export function playerMove(store: GameStore, payload: { playerId: string; dx?: number; dy?: number }): { ok: boolean; player?: { id: string; x: number; y: number } } {
  if (!payload?.playerId || payload.playerId.trim() === '') {
    return { ok: false }
  }
  const dx = payload.dx ?? 0
  const dy = payload.dy ?? 0
  if (!store.player) store.player = { id: payload.playerId, x: 0, y: 0 }
  store.player.x += dx
  store.player.y += dy
  return { ok: true, player: { id: payload.playerId, x: store.player.x, y: store.player.y } }
}

export function playerShoot(store: GameStore, payload: { playerId: string; direction: { x: number; y: number } }): { ok: boolean; event?: { playerId: string; direction: { x: number; y: number } } } {
  if (!payload?.playerId || payload.playerId.trim() === '') {
    return { ok: false }
  }
  return { ok: true, event: { playerId: payload.playerId, direction: payload.direction } }
}

// Start a minimal HTTP server exposing the above endpoints
export async function startServer(port: number = 5173): Promise<http.Server> {
  const app = express()
  app.use(express.json())

  // In-memory store instance
  const store = createStore()

  app.get('/api/health', (_req, res) => {
    res.json(health())
  })

  // Level load/save routes
  app.post('/api/level/load', (req, res) => {
    const body = req.body as { levelId: string }
    const result = levelLoad(store, body)
    if (!result.ok) {
      res.status(400).json({ error: 'invalid_payload' })
      return
    }
    res.json(result)
  })

  app.post('/api/level/save', (req, res) => {
    const body = req.body as { levelId: string; data?: any }
    const result = levelSave(store, body)
    if (!result.ok) {
      res.status(400).json({ error: 'invalid_payload' })
      return
    }
    res.json(result)
  })

  // Player actions
  app.post('/api/player/move', (req, res) => {
    const body = req.body as { playerId: string; dx?: number; dy?: number }
    const result = playerMove(store, body)
    if (!result.ok) {
      res.status(400).json({ error: 'invalid_payload' })
      return
    }
    res.json(result)
  })

  app.post('/api/player/shoot', (req, res) => {
    const body = req.body as { playerId: string; direction: { x: number; y: number } }
    const result = playerShoot(store, body)
    if (!result.ok) {
      res.status(400).json({ error: 'invalid_payload' })
      return
    }
    res.json(result)
  })

  const server = app.listen(port)
  return server
}

export function stopServer(server: http.Server): Promise<void> {
  return new Promise((resolve) => {
    server.close(() => resolve())
  })
}

export { } // end module
