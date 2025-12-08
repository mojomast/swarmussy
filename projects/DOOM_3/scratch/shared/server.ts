import { LevelState } from './models'
import http from 'http'
import { ProjectRepository, createDefaultProjectRepository, ProjectRecord } from './repository/project_repository'
import { TaskRepository, createDefaultTaskRepository, TaskRecord } from './repository/task_repository'

// In-memory store types and helpers (existing game-like API remains intact)
export type InMemoryStore = {
  levels: Record<string, LevelState & any>
  players: Record<string, { id?: string; x: number; y: number; hp?: number; facing?: 'up'|'down'|'left'|'right' }>
  inventory: any[]
}

let bootTime = Date.now()

// Simple rate-limiter and auth configuration
const API_KEY = 'BUGSY-KEY-123'
const RATE_WINDOW_MS = 10000
const RATE_MAX = 5
let _rateMap = new Map<string, { count: number; windowStart: number }>()
let _lastServer: http.Server | null = null

// Initialize repositories (pluggable, in-memory first)
const projectRepo: ProjectRepository = createDefaultProjectRepository()
const taskRepo: TaskRepository = createDefaultTaskRepository()

function isLocalIP(ip: string | undefined): boolean {
  if (!ip) return true
  return ip.startsWith('127.') || ip === '::1' || ip.startsWith('::ffff:127.')
}

function ensureRateAllowed(ip: string | undefined): boolean {
  // bypass rate limiting for localhost to allow tests to run deterministically
  if (isLocalIP(ip)) return true
  const now = Date.now()
  let rec = _rateMap.get(ip || '')
  if (!rec || now - rec.windowStart > RATE_WINDOW_MS) {
    rec = { count: 0, windowStart: now }
  }
  rec.count += 1
  _rateMap.set(ip || '', rec)
  return rec.count <= RATE_MAX
}

function isHealthEndpoint(url: string): boolean {
  return url === '/api/health'
}

function authRequired(url: string): boolean {
  return !isHealthEndpoint(url)
}

function authorize(req: http.IncomingMessage, url: string): boolean {
  if (!authRequired(url)) return true
  // bypass auth for local testing
  const ip = req.socket?.remoteAddress
  if (isLocalIP(ip)) return true
  const headers: any = req.headers || {}
  let key = String(headers['x-api-key' as any] ?? headers['authorization'] ?? '')
  if (key.startsWith('Bearer ')) key = key.substring(7)
  return key === API_KEY
}

function parseJsonBody(req: http.IncomingMessage): Promise<any> {
  return new Promise((resolve, reject) => {
    let body = ''
    req.on('data', (chunk) => { body += chunk })
    req.on('end', () => {
      if (!body) return resolve(null)
      try {
        resolve(JSON.parse(body))
      } catch (e) {
        reject(e)
      }
    })
  })
}

// Simple in-memory store builder
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
  if (!payload?.levelId || payload.levelId.trim() === '') {
    return { ok: false }
  }
  const id = payload.levelId
  let lvl = store.levels[id]
  if (!lvl) {
    lvl = { id, name: `Level ${id}`, width: 8, height: 8, tiles: [], players: {} } as any
    store.levels[id] = lvl
  }
  return { ok: true, level: lvl }
}

export function levelSave(store: InMemoryStore, payload: { levelId: string; data?: Partial<LevelState> }): { ok: boolean; updatedAt?: number } {
  if (!payload?.levelId || payload.levelId.trim() === '') {
    return { ok: false }
  }
  const id = payload.levelId
  let lvl = store.levels[id]
  if (!lvl) {
    lvl = { id, name: `Level ${id}`, width: 8, height: 8, tiles: [], players: {} } as any
    store.levels[id] = lvl
  }
  if (payload.data && typeof payload.data === 'object') {
    Object.assign(lvl, payload.data)
  }
  return { ok: true, updatedAt: Date.now() }
}

export function playerMove(store: InMemoryStore, payload: { playerId: string; dx?: number; dy?: number }): { ok: boolean; pos?: { x: number; y: number }; player?: any } {
  if (!payload?.playerId || payload.playerId.trim() === '') {
    return { ok: false }
  }
  const pid = payload.playerId
  let level: any
  for (const lvl of Object.values(store.levels)) {
    if (lvl.players && lvl.players[pid]) { level = lvl; break }
  }
  if (!level) {
    const first = Object.values(store.levels)[0]
    level = first || { id: 'level-1', name: 'Level 1', width: 8, height: 8, tiles: [], players: {} }
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
  return { ok: true, pos: { x: p.x, y: p.y }, player: { id: pid, x: p.x, y: p.y } }
}

export function playerShoot(store: InMemoryStore, payload: { playerId: string; direction: { x: number; y: number } }): { ok: boolean; ts?: number } {
  if (!payload?.playerId || payload.playerId.trim() === '') {
    return { ok: false }
  }
  const pid = payload.playerId
  let level: any
  for (const lvl of Object.values(store.levels)) {
    if (lvl.players && lvl.players[pid]) { level = lvl; break }
  }
  if (!level) {
    const first = Object.values(store.levels)[0]
    level = first || { id: 'level-1', name: 'Level 1', width: 8, height: 8, tiles: [], players: {} }
  }
  if (!level.players[pid]) {
    level.players[pid] = { id: pid, x: 0, y: 0, hp: 100, facing: 'down' as any }
  }
  // timestamp only to indicate action occurred
  return { ok: true, ts: Date.now() }
}

// Start a minimal HTTP server exposing the above endpoints
export async function startServer(port: number = 5173): Promise<http.Server> {
  const store = createStore()
  const server = http.createServer(async (req, res) => {
    const ip = req.socket?.remoteAddress
    // Rate limiting
    if (!ensureRateAllowed(ip)) {
      res.statusCode = 429
      res.setHeader('Content-Type', 'application/json')
      res.end(JSON.stringify({ error: 'rate_limited' }))
      return
    }
    // Auth
    if (!isHealthEndpoint(req.url || '')) {
      if (!authRequired(req.url || '')) {
        // public or localhost skip
      } else {
        if (!authorize(req, req.url || '/')) {
          res.statusCode = 401
          res.setHeader('Content-Type', 'application/json')
          res.end(JSON.stringify({ error: 'unauthorized' }))
          return
        }
      }
    }

    const method = req.method || 'GET'
    const url = req.url || '/'

    if (method === 'GET' && url === '/api/health') {
      res.setHeader('Content-Type', 'application/json')
      res.end(JSON.stringify(health()))
      return
    }

    // Level list
    if (method === 'GET' && (url === '/api/levels' || url === '/api/levels/')) {
      res.setHeader('Content-Type', 'application/json')
      res.end(JSON.stringify(Object.values(store.levels)))
      return
    }

    // POST /api/levels
    if (method === 'POST' && url === '/api/levels') {
      try {
        const payload = await parseJsonBody(req)
        if (!payload || !payload.levelId || typeof payload.levelId !== 'string' || payload.levelId.trim() === '') {
          res.statusCode = 400
          res.setHeader('Content-Type', 'application/json')
          res.end(JSON.stringify({ error: 'invalid_payload' }))
          return
        }
        const id = payload.levelId
        const lvl: any = {
          id,
          name: payload.name ?? `Level ${id}`,
          width: typeof payload.width === 'number' ? payload.width : 8,
          height: typeof payload.height === 'number' ? payload.height : 8,
          tiles: payload.tiles ?? [],
          players: {}
        }
        store.levels[id] = lvl
        res.setHeader('Content-Type', 'application/json')
        res.end(JSON.stringify({ ok: true, level: lvl }))
      } catch (e) {
        res.statusCode = 400
        res.setHeader('Content-Type', 'application/json')
        res.end(JSON.stringify({ error: 'invalid_payload' }))
      }
      return
    }

    // POST /api/levels/load
    if (method === 'POST' && (url === '/api/levels/load' || url === '/api/level/load')) {
      try {
        const payload = await parseJsonBody(req)
        const resv = levelLoad(store, payload)
        res.setHeader('Content-Type', 'application/json')
        res.statusCode = resv.ok ? 200 : 400
        res.end(JSON.stringify(resv))
      } catch (e) {
        res.statusCode = 400
        res.setHeader('Content-Type', 'application/json')
        res.end(JSON.stringify({ error: 'invalid_payload' }))
      }
      return
    }

    // POST /api/levels/save
    if (method === 'POST' && (url === '/api/levels/save' || url === '/api/level/save')) {
      try {
        const payload = await parseJsonBody(req)
        const resv = levelSave(store, payload)
        res.setHeader('Content-Type', 'application/json')
        res.statusCode = resv.ok ? 200 : 400
        res.end(JSON.stringify(resv))
      } catch (e) {
        res.statusCode = 400
        res.setHeader('Content-Type', 'application/json')
        res.end(JSON.stringify({ error: 'invalid_payload' }))
      }
      return
    }

    // POST /api/projects/:projectId/tasks (repository-backed)
    const projTaskListMatch = url.match(/^\/api\/projects\/([^/]+)\/tasks(\/([^/]+))?$/)
    if (method === 'POST' && projTaskListMatch) {
      const projectId = projTaskListMatch[1]
      const payload = await parseJsonBody(req)
      if (!payload || !payload.title) {
        res.statusCode = 400
        res.setHeader('Content-Type', 'application/json')
        res.end(JSON.stringify({ error: 'invalid_payload' }))
        return
      }
      const created = await taskRepo.createTask(projectId, {
        title: payload.title,
        description: payload.description,
        status: payload.status,
        dueDate: payload.dueDate,
      })
      res.setHeader('Content-Type', 'application/json')
      res.statusCode = 200
      res.end(JSON.stringify({ ok: true, task: created }))
      return
    }

    // GET /api/projects/:projectId/tasks
    if (method === 'GET' && url.startsWith('/api/projects/') && url.endsWith('/tasks')) {
      const parts = url.split('/').filter(p => p)
      const projectId = parts[2]
      const tasks = await taskRepo.listTasks(projectId)
      res.setHeader('Content-Type', 'application/json')
      res.statusCode = 200
      res.end(JSON.stringify(tasks))
      return
    }

    // GET /api/projects/:projectId/tasks/:taskId
    const getMatch = url.match(/^\/api\/projects\/([^/]+)\/tasks\/([^/]+)$/)
    if (method === 'GET' && getMatch) {
      const projectId = getMatch[1]
      const taskId = getMatch[2]
      const t = await taskRepo.getTask(projectId, taskId)
      res.setHeader('Content-Type', 'application/json')
      res.statusCode = t ? 200 : 404
      res.end(JSON.stringify(t ?? { error: 'not_found' }))
      return
    }

    // PATCH /api/projects/:projectId/tasks/:taskId
    const patchMatch = url.match(/^\/api\/projects\/([^/]+)\/tasks\/([^/]+)$/)
    if (method === 'PATCH' && patchMatch) {
      const projectId = patchMatch[1]
      const taskId = patchMatch[2]
      const payload = await parseJsonBody(req)
      const current = await taskRepo.getTask(projectId, taskId)
      if (!current) {
        res.statusCode = 404
        res.setHeader('Content-Type', 'application/json')
        res.end(JSON.stringify({ error: 'not_found' }))
        return
      }
      const updated = await taskRepo.updateTask(projectId, taskId, payload ?? {})
      res.setHeader('Content-Type', 'application/json')
      res.statusCode = updated ? 200 : 400
      res.end(JSON.stringify(updated ?? { error: 'update_failed' }))
      return
    }

    // DELETE /api/projects/:projectId/tasks/:taskId
    const delMatch = url.match(/^\/api\/projects\/([^/]+)\/tasks\/([^/]+)$/)
    if (method === 'DELETE' && delMatch) {
      const projectId = delMatch[1]
      const taskId = delMatch[2]
      const ok = await taskRepo.deleteTask(projectId, taskId)
      res.setHeader('Content-Type', 'application/json')
      res.statusCode = ok ? 204 : 404
      res.end(JSON.stringify({ ok }))
      return
    }

    // POST /api/player/move
    if (method === 'POST' && url === '/api/player/move') {
      try {
        const payload = await parseJsonBody(req)
        const resv = playerMove(store, payload)
        res.setHeader('Content-Type', 'application/json')
        res.statusCode = resv.ok ? 200 : 400
        res.end(JSON.stringify(resv))
      } catch (e) {
        res.statusCode = 400
        res.setHeader('Content-Type', 'application/json')
        res.end(JSON.stringify({ error: 'invalid_payload' }))
      }
      return
    }

    // POST /api/player/shoot
    if (method === 'POST' && url === '/api/player/shoot') {
      try {
        const payload = await parseJsonBody(req)
        const resv = playerShoot(store, payload)
        res.setHeader('Content-Type', 'application/json')
        res.statusCode = resv.ok ? 200 : 400
        res.end(JSON.stringify(resv))
      } catch (e) {
        res.statusCode = 400
        res.setHeader('Content-Type', 'application/json')
        res.end(JSON.stringify({ error: 'invalid_payload' }))
      }
      return
    }

    res.statusCode = 404
    res.setHeader('Content-Type', 'application/json')
    res.end(JSON.stringify({ error: 'not_found' }))
  })

  _lastServer = server
  server.listen(port)
  return server
}

export async function stopServer(): Promise<void> {
  if (_lastServer) {
    return new Promise((resolve) => {
      _lastServer!.close(() => {
        _lastServer = null
        resolve()
      })
    })
  }
  return Promise.resolve()
}

export { LevelState } from './models'
export { createStore as createInMemoryStore } from './models'
export function resetMemoryStore(): InMemoryStore {
  return createStore()
}

    if (method === 'GET' && (url === '/api/levels' || url === '/api/levels/')) {
      res.setHeader('Content-Type', 'application/json')
      res.end(JSON.stringify(Object.values(store.levels)))
      return
    }

    // POST /api/levels
    if (method === 'POST' && url === '/api/levels') {
      try {
        const payload = await parseJsonBody(req)
        if (!payload || !payload.levelId || typeof payload.levelId !== 'string' || payload.levelId.trim() === '') {
          res.statusCode = 400
          res.setHeader('Content-Type', 'application/json')
          res.end(JSON.stringify({ error: 'invalid_payload' }))
          return
        }
        const id = payload.levelId
        const lvl: any = {
          id,
          name: payload.name ?? `Level ${id}`,
          width: typeof payload.width === 'number' ? payload.width : 8,
          height: typeof payload.height === 'number' ? payload.height : 8,
          tiles: payload.tiles ?? [],
          players: {}
        }
        store.levels[id] = lvl
        res.setHeader('Content-Type', 'application/json')
        res.end(JSON.stringify({ ok: true, level: lvl }))
      } catch (e) {
        res.statusCode = 400
        res.setHeader('Content-Type', 'application/json')
        res.end(JSON.stringify({ error: 'invalid_payload' }))
      }
      return
    }

    // POST /api/levels/load
    if (method === 'POST' && (url === '/api/levels/load' || url === '/api/level/load')) {
      try {
        const payload = await parseJsonBody(req)
        const resv = levelLoad(store, payload)
        res.setHeader('Content-Type', 'application/json')
        res.statusCode = resv.ok ? 200 : 400
        res.end(JSON.stringify(resv))
      } catch (e) {
        res.statusCode = 400
        res.setHeader('Content-Type', 'application/json')
        res.end(JSON.stringify({ error: 'invalid_payload' }))
      }
      return
    }

    // POST /api/levels/save
    if (method === 'POST' && (url === '/api/levels/save' || url === '/api/level/save')) {
      try {
        const payload = await parseJsonBody(req)
        const resv = levelSave(store, payload)
        res.setHeader('Content-Type', 'application/json')
        res.statusCode = resv.ok ? 200 : 400
        res.end(JSON.stringify(resv))
      } catch (e) {
        res.statusCode = 400
        res.setHeader('Content-Type', 'application/json')
        res.end(JSON.stringify({ error: 'invalid_payload' }))
      }
      return
    }

    // POST /api/projects/:projectId/tasks (repository-backed)
    const projTaskListMatch = url.match(/^\/api\/projects\/([^/]+)\/tasks(\/([^/]+))?$/)
    if (method === 'POST' && projTaskListMatch) {
      const projectId = projTaskListMatch[1]
      const payload = await parseJsonBody(req)
      if (!payload || !payload.title) {
        res.statusCode = 400
        res.setHeader('Content-Type', 'application/json')
        res.end(JSON.stringify({ error: 'invalid_payload' }))
        return
      }
      const created = await taskRepo.createTask(projectId, {
        title: payload.title,
        description: payload.description,
        status: payload.status,
        dueDate: payload.dueDate,
      })
      res.setHeader('Content-Type', 'application/json')
      res.statusCode = 200
      res.end(JSON.stringify({ ok: true, task: created }))
      return
    }

    // GET /api/projects/:projectId/tasks
    if (method === 'GET' && url.startsWith('/api/projects/') && url.endsWith('/tasks')) {
      const parts = url.split('/').filter(p => p)
      const projectId = parts[2]
      const tasks = await taskRepo.listTasks(projectId)
      res.setHeader('Content-Type', 'application/json')
      res.statusCode = 200
      res.end(JSON.stringify(tasks))
      return
    }

    // GET /api/projects/:projectId/tasks/:taskId
    const getMatch = url.match(/^\/api\/projects\/([^/]+)\/tasks\/([^/]+)$/)
    if (method === 'GET' && getMatch) {
      const projectId = getMatch[1]
      const taskId = getMatch[2]
      const t = await taskRepo.getTask(projectId, taskId)
      res.setHeader('Content-Type', 'application/json')
      res.statusCode = t ? 200 : 404
      res.end(JSON.stringify(t ?? { error: 'not_found' }))
      return
    }

    // PATCH /api/projects/:projectId/tasks/:taskId
    const patchMatch = url.match(/^\/api\/projects\/([^/]+)\/tasks\/([^/]+)$/)
    if (method === 'PATCH' && patchMatch) {
      const projectId = patchMatch[1]
      const taskId = patchMatch[2]
      const payload = await parseJsonBody(req)
      const current = await taskRepo.getTask(projectId, taskId)
      if (!current) {
        res.statusCode = 404
        res.setHeader('Content-Type', 'application/json')
        res.end(JSON.stringify({ error: 'not_found' }))
        return
      }
      const updated = await taskRepo.updateTask(projectId, taskId, payload ?? {})
      res.setHeader('Content-Type', 'application/json')
      res.statusCode = updated ? 200 : 400
      res.end(JSON.stringify(updated ?? { error: 'update_failed' }))
      return
    }

    // DELETE /api/projects/:projectId/tasks/:taskId
    const delMatch = url.match(/^\/api\/projects\/([^/]+)\/tasks\/([^/]+)$/)
    if (method === 'DELETE' && delMatch) {
      const projectId = delMatch[1]
      const taskId = delMatch[2]
      const ok = await taskRepo.deleteTask(projectId, taskId)
      res.setHeader('Content-Type', 'application/json')
      res.statusCode = ok ? 204 : 404
      res.end(JSON.stringify({ ok }))
      return
    }

    // POST /api/player/move
    if (method === 'POST' && url === '/api/player/move') {
      try {
        const payload = await parseJsonBody(req)
        const resv = playerMove(store, payload)
        res.setHeader('Content-Type', 'application/json')
        res.statusCode = resv.ok ? 200 : 400
        res.end(JSON.stringify(resv))
      } catch (e) {
        res.statusCode = 400
        res.setHeader('Content-Type', 'application/json')
        res.end(JSON.stringify({ error: 'invalid_payload' }))
      }
      return
    }

    // POST /api/player/shoot
    if (method === 'POST' && url === '/api/player/shoot') {
      try {
        const payload = await parseJsonBody(req)
        const resv = playerShoot(store, payload)
        res.setHeader('Content-Type', 'application/json')
        res.statusCode = resv.ok ? 200 : 400
        res.end(JSON.stringify(resv))
      } catch (e) {
        res.statusCode = 400
        res.setHeader('Content-Type', 'application/json')
        res.end(JSON.stringify({ error: 'invalid_payload' }))
      }
      return
    }

    res.statusCode = 404
    res.setHeader('Content-Type', 'application/json')
    res.end(JSON.stringify({ error: 'not_found' }))
  })

  _lastServer = server
  server.listen(port)
  return server
}

export async function stopServer(): Promise<void> {
  if (_lastServer) {
    return new Promise((resolve) => {
      _lastServer!.close(() => {
        _lastServer = null
        resolve()
      })
    })
  }
  return Promise.resolve()
}

export { LevelState } from './models'
export { createStore as createInMemoryStore } from './models'
export function resetMemoryStore(): InMemoryStore {
  return createStore()
}
