import { Router, jsonBodyParser } from '../router'
import type { InMemoryStore } from '../server'

// Build a modular backend router that wires API endpoints for the in-memory store.
export function buildBackendRouter(store: InMemoryStore): Router {
  const router = new Router()
  // Parse JSON bodies for relevant endpoints
  router.use(jsonBodyParser)

  // Health check
  router.get('/api/health', async (_req: any, res: any) => {
    const { health } = await import('../server')
    res.json(health())
  })

  // Level load
  router.post('/api/level/load', async (req: any, res: any) => {
    const { levelLoad } = await import('../server')
    const payload = req?.body || {}
    const result = levelLoad(store, { levelId: String(payload.levelId ?? '') })
    res.json(result)
  })

  // Level save
  router.post('/api/level/save', async (req: any, res: any) => {
    const { levelSave } = await import('../server')
    const payload = req?.body || {}
    const result = levelSave(store, {
      levelId: String(payload.levelId ?? ''),
      data: payload?.data as any,
    })
    res.json(result)
  })

  // Player move
  router.post('/api/player/move', async (req: any, res: any) => {
    const { playerMove } = await import('../server')
    const payload = req?.body || {}
    const result = playerMove(store, {
      playerId: String(payload.playerId ?? ''),
      dx: (payload?.dx as any) ?? 0,
      dy: (payload?.dy as any) ?? 0,
    })
    res.json(result)
  })

  // Player shoot
  router.post('/api/player/shoot', async (req: any, res: any) => {
    const { playerShoot } = await import('../server')
    const payload = req?.body || {}
    const result = playerShoot(store, {
      playerId: String(payload.playerId ?? ''),
      direction: payload?.direction as any,
    })
    res.json(result)
  })

  return router
}
