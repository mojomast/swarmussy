import http from 'http'
import { Router, jsonBodyParser } from '../router'
import { LevelState, PlayerState } from '../models'

// In-memory store interface specialized for batch integration
export type InMemoryStoreBatch = {
  levels: Record<string, LevelState>
  players: Record<string, PlayerState>
}

// Simple in-memory store factory
export function createStoreBatch(): InMemoryStoreBatch {
  return { levels: {}, players: {} }
}

// Health hook for tests
export function health(): { status: string } {
  return { status: 'ok' }
}

// Ensure a level exists in the store
export function ensureLevelExists(store: InMemoryStoreBatch, id: string, fallback?: Partial<LevelState>): LevelState {
  let lvl = store.levels[id]
  if (!lvl) {
    const w = 8
    const h = 8
    const tiles = Array.from({ length: h }, () => Array.from({ length: w }, () => ' '))
    lvl = {
      id,
      name: fallback?.name ?? `Level ${id}`,
      width: fallback?.width ?? w,
      height: fallback?.height ?? h,
      tiles,
      players: {},
    }
    store.levels[id] = lvl
  }
  return lvl
}

// Level load endpoint logic
export function levelLoad(store: InMemoryStoreBatch, payload: { levelId: string; name?: string; width?: number; height?: number }): { ok: boolean; level?: LevelState; error?: string } {
  const id = payload?.levelId
  if (!id || typeof id !== 'string') {
    return { ok: false, error: 'Invalid level id' }
  }
  const level = ensureLevelExists(store, id, { name: payload?.name, width: payload?.width, height: payload?.height })
  return { ok: true, level }
}

// Level save endpoint logic
export function levelSave(store: InMemoryStoreBatch, payload: { levelId: string; data?: Partial<LevelState> }): { ok: boolean; level?: LevelState } {
  const id = payload?.levelId
  if (!id || typeof id !== 'string') {
    return { ok: false } as any
  }
  let lvl = store.levels[id]
  if (!lvl) {
    lvl = ensureLevelExists(store, id)
  }
  if (payload?.data && typeof payload.data === 'object') {
    Object.assign(lvl, payload.data)
  }
  store.levels[id] = lvl
  return { ok: true, level: lvl }
}

// Player move endpoint logic
export function playerMove(store: InMemoryStoreBatch, payload: { playerId: string; dx?: number; dy?: number }): { ok: boolean; player?: { id: string; x: number; y: number } } {
  const pid = payload?.playerId
  if (!pid || typeof pid !== 'string') return { ok: false }
  // find level containing player or create default
  let level: LevelState | undefined
  for (const lvl of Object.values(store.levels)) {
    if (lvl.players && lvl.players[pid]) { level = lvl; break }
  }
  if (!level) {
    const first = Object.values(store.levels)[0]
    level = first ?? ensureLevelExists(store, 'level-1')
  }
  if (!level!.players[pid]) {
    level!.players[pid] = { id: pid, x: 0, y: 0, hp: 100, facing: 'down' as const }
  }
  const p = level!.players[pid] as any
  const dx = typeof payload.dx === 'number' ? payload.dx : 0
  const dy = typeof payload.dy === 'number' ? payload.dy : 0
  p.x += dx
  p.y += dy
  return { ok: true, player: { id: pid, x: p.x, y: p.y } }
}

// Player shoot endpoint logic
export function playerShoot(store: InMemoryStoreBatch, payload: { playerId: string; direction?: { x: number; y: number } }): { ok: boolean; event?: { playerId: string; direction: { x: number; y: number } } } {
  const pid = payload?.playerId
  if (!pid || typeof pid !== 'string') return { ok: false }
  // ensure level and player exist for event
  let level: LevelState | undefined
  for (const lvl of Object.values(store.levels)) {
    if (lvl.players && lvl.players[pid]) { level = lvl; break }
  }
  if (!level) {
    const first = Object.values(store.levels)[0]
    level = first ?? ensureLevelExists(store, 'level-1')
  }
  if (!level!.players[pid]) {
    level!.players[pid] = { id: pid, x: 0, y: 0, hp: 100, facing: 'down' as const }
  }
  return { ok: true, event: { playerId: pid, direction: payload.direction || { x: 0, y: 1 } } }
}

// HTTP server wiring for batch backend (modular, to be wired into scratch/shared/server.ts)
export function createApp(store: InMemoryStoreBatch): http.Server {
  const router = new Router()
  // Basic logger
  // You can wire a lightweight logger in tests if desired

  router.get('/api/health', (req: any, res: any) => {
    res.setHeader('Content-Type', 'application/json')
    res.end(JSON.stringify(health()))
  })

  router.post('/api/level/load', jsonBodyParser, (req: any, res: any) => {
    const body = req.body || {}
    const id = body?.levelId
    if (!id) {
      res.statusCode = 400
      res.setHeader('Content-Type', 'application/json')
      res.end(JSON.stringify({ error: 'Invalid level id' }))
      return
    }
    const result = levelLoad(store, { levelId: id, name: body?.name, width: body?.width, height: body?.height })
    res.setHeader('Content-Type', 'application/json')
    res.end(JSON.stringify(result))
  })

  router.post('/api/level/save', jsonBodyParser, (req: any, res: any) => {
    const body = req.body || {}
    const id = body?.levelId
    const data = body?.data
    const result = levelSave(store, { levelId: id, data })
    res.setHeader('Content-Type', 'application/json')
    res.end(JSON.stringify(result))
  })

  router.post('/api/player/move', jsonBodyParser, (req: any, res: any) => {
    const body = req.body || {}
    const result = playerMove(store, { playerId: body?.playerId, dx: body?.dx, dy: body?.dy })
    res.setHeader('Content-Type', 'application/json')
    res.end(JSON.stringify(result))
  })

  router.post('/api/player/shoot', jsonBodyParser, (req: any, res: any) => {
    const body = req.body || {}
    const result = playerShoot(store, { playerId: body?.playerId, direction: body?.direction })
    res.setHeader('Content-Type', 'application/json')
    res.end(JSON.stringify(result))
  })

  const server = http.createServer((req, res) => router.handle(req as any, res as any))
  return server
}

export { LevelState, PlayerState }

// Convenience export for tests to mount the batch API onto the existing server
export function mountIntoExistingServer(existingServer: http.Server, store: InMemoryStoreBatch) {
  // This is a touchpoint for startup scripts. Tests can use createApp(store).listen() instead.
  // No-op on purpose to keep modular wiring since integration with an existing Express-like server is external.
  return existingServer
}
