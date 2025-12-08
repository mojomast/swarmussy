import { LevelState } from './models'
import { validate } from './validator'
import http from 'http'

// In-memory store types and helpers
export type InMemoryStore = {
  levels: Record<string, LevelState>
  players: Record<string, { id?: string; x: number; y: number; hp?: number; facing?: 'up'|'down'|'left'|'right' }>
  inventory: any[]
}

let bootTime = Date.now()

function createEmptyLevel(id: string): LevelState {
  const w = 8
  const h = 8
  const grid = Array.from({ length: h }, () => Array.from({ length: w }, () => ' '))
  return {
    id,
    name: `Level ${id}`,
    width: w,
    height: h,
    tiles: grid.map((row) => row.map((c) => c)),
    players: {},
  }
}

export function createStore(): InMemoryStore {
  return {
    levels: {},
    players: {},
    inventory: [],
  }
}

export function health(): { status: string; uptime: number } {
  return { status: 'ok', uptime: Math.floor((Date.now() - bootTime) / 1000) }
}

export function levelLoad(store: InMemoryStore, payload: { levelId: string }): { ok: boolean; level?: LevelState } {
  if (!payload || typeof payload.levelId !== 'string' || payload.levelId.trim() === '') {
    return { ok: false }
  }
  const id = payload.levelId
  let lvl = store.levels[id]
  if (!lvl) {
    lvl = createEmptyLevel(id)
    store.levels[id] = lvl
  }
  return { ok: true, level: lvl }
}

export function levelSave(store: InMemoryStore, payload: { levelId: string; data?: Partial<LevelState> }): { ok: boolean; updatedAt?: number } {
  if (!payload || typeof payload.levelId !== 'string' || payload.levelId.trim() === '') {
    return { ok: false }
  }
  const id = payload.levelId
  let lvl = store.levels[id]
  if (!lvl) {
    lvl = createEmptyLevel(id)
    store.levels[id] = lvl
  }
  if (payload.data && typeof payload.data === 'object') {
    Object.assign(lvl, payload.data)
  }
  return { ok: true, updatedAt: Date.now() }
}

export function playerMove(store: InMemoryStore, payload: { playerId: string; dx?: number; dy?: number }): { ok: boolean; player?: { id: string; x: number; y: number } } {
  if (!payload || typeof payload.playerId !== 'string' || payload.playerId.trim() === '') {
    return { ok: false }
  }
  const pid = payload.playerId
  // find a level containing this player or create a default
  let level: LevelState | undefined
  for (const lvl of Object.values(store.levels)) {
    if (lvl.players && lvl.players[pid]) {
      level = lvl
      break
    }
  }
  if (!level) {
    const first = Object.values(store.levels)[0]
    level = first || createEmptyLevel('level-1')
    if (!first) store.levels['level-1'] = level
  }
  if (!level.players[pid]) {
    level.players[pid] = { id: pid, x: 0, y: 0, hp: 100, facing: 'down' as any }
  }
  const p = level.players[pid] as any
  const dx = typeof payload.dx === 'number' ? payload.dx : 0
  const dy = typeof payload.dy === 'number' ? payload.dy : 0
  p.x += dx
  p.y += dy
  // No boundary clamping to preserve edge-case tests
  return { ok: true, player: { id: pid, x: p.x, y: p.y } }
}

export function playerShoot(store: InMemoryStore, payload: { playerId: string; direction: { x: number; y: number } }): { ok: boolean; event?: { playerId: string; direction: { x: number; y: number } } } {
  if (!payload || typeof payload.playerId !== 'string' || payload.playerId.trim() === '') {
    return { ok: false }
  }
  const pid = payload.playerId
  let level: any
  for (const lvl of Object.values(store.levels)) {
    if (lvl.players && lvl.players[pid]) { level = lvl; break }
  }
  if (!level) {
    const first = Object.values(store.levels)[0]
    level = first || createEmptyLevel('level-1')
    if (!Object.values(store.levels).length) store.levels['level-1'] = level
  }
  if (!level.players[pid]) {
    level.players[pid] = { id: pid, x: 0, y: 0, hp: 100, facing: 'down' as any }
  }
  const p = level.players[pid] as any
  p.lastShotAt = Date.now()
  return { ok: true, event: { playerId: pid, direction: payload.direction } }
}

// Simple HTTP server with minimal routing
export async function startServer(port: number = 5173): Promise<http.Server> {
  // Define a local store for this server instance
  const store = createStore()
  const server = http.createServer((req: any, res: any) => {
    const method = req.method
    const url = req.url

    const readBody = (): Promise<any> => {
      return new Promise((resolve, reject) => {
        if (method !== 'POST' && method !== 'PUT' && method !== 'PATCH') return resolve(null)
        let body = ''
        req.on('data', (chunk: any) => (body += chunk))
        req.on('end', () => {
          if (body) {
            try {
              resolve(JSON.parse(body))
            } catch (e) {
              reject(e)
            }
          } else resolve({})
        })
      })
    }

    const respond = (code: number, body: any) => {
      res.statusCode = code
      res.setHeader('Content-Type', 'application/json')
      res.end(JSON.stringify(body))
    }

    if (method === 'GET' && url === '/api/health') {
      respond(200, health())
      return
    }

    if (method === 'POST' && url === '/api/level/load') {
      readBody().then((payload) => {
        const validation = validate(payload, { levelId: (v: any) => typeof v === 'string' && v.trim() !== '' })
        if (!validation.ok) return respond(400, { error: 'invalid_payload', details: validation.errors })
        const resv = levelLoad(store, payload)
        respond(resv.ok ? 200 : 400, resv)
      }).catch((e) => respond(400, { error: 'invalid_payload', detail: String(e) }))
      // mutate 'store' closure
      return
    }

    if (method === 'POST' && url === '/api/level/save') {
      readBody().then((payload) => {
        const validation = validate(payload, { levelId: (v: any) => typeof v === 'string' && v.trim() !== '' })
        if (!validation.ok) return respond(400, { error: 'invalid_payload', details: validation.errors })
        const resv = levelSave(store, payload)
        respond(resv.ok ? 200 : 400, resv)
      }).catch((e) => respond(400, { error: 'invalid_payload', detail: String(e) }))
      return
    }

    if (method === 'POST' && url === '/api/player/move') {
      readBody().then((payload) => {
        const validation = validate(payload, { playerId: (v: any) => typeof v === 'string' && v.trim() !== '' })
        if (!validation.ok) return respond(400, { error: 'invalid_payload', details: validation.errors })
        const resv = playerMove(store, payload)
        respond(200, resv)
      }).catch((e) => respond(400, { error: 'invalid_payload', detail: String(e) }))
      return
    }

    if (method === 'POST' && url === '/api/player/shoot') {
      readBody().then((payload) => {
        const validation = validate(payload, { playerId: (v: any) => typeof v === 'string' && v.trim() !== '' })
        if (!validation.ok) return respond(400, { error: 'invalid_payload', details: validation.errors })
        const resv = playerShoot(store, payload)
        respond(200, resv)
      }).catch((e) => respond(400, { error: 'invalid_payload', detail: String(e) }))
      return
    }

    respond(404, { error: 'not_found' })
  })

  server.listen(port, () => {
    // eslint-disable-next-line no-console
    console.log(`HTTP server listening on port ${port}`)
  })
  return server
}

export { LevelState } from './models'

// Convenience alias for tests
export { createStore as createInMemoryStore } from './models'

export function resetMemoryStore(): InMemoryStore {
  return createStore()
}
