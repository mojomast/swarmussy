import { strict as assert } from 'assert'
import express from 'express'
import { createBackendRouter } from '../src/backend_router'
import { createStore } from '../server'

async function runIntegrationTests() {
  const store = createStore()
  const router = createBackendRouter(store)
  const app = express()
  app.use('/api', router)
  const server = app.listen(0)
  const port = (server.address() as any).port
  const base = `http://localhost:${port}`

  try {
    // Health check (adjusted to /api/health when mounted under /api)
    const h = await fetch(`${base}/api/health`).then(r => r.json())
    assert.ok(h && h.status === 'ok', 'health should be ok')

    // Create a new level
    const newLevel = { id: 'level-2', name: 'Level 2', width: 10, height: 8, grid: [] }
    const lvlRes = await fetch(`${base}/api/levels`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(newLevel)
    })
    const lvlJson = await lvlRes.json()
    assert.ok(lvlJson && lvlJson.id === 'level-2', 'level should be created')

    // Load levels list to include level-2
    const listRes = await fetch(`${base}/api/levels`)
    const list = await listRes.json()
    const found = list.find((l: any) => l.id === 'level-2')
    assert.ok(found, 'level-2 should be in levels list')

    // Move a player
    const moveRes = await fetch(`${base}/api/player/move`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ playerId: 'tester', dx: 2, dy: 3 })
    })
    const moveJson = await moveRes.json()
    assert.ok(moveJson && moveJson.ok, 'player move should succeed')

    // Shoot
    const shootRes = await fetch(`${base}/api/player/shoot`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ playerId: 'tester', direction: { x: 1, y: 0 } })
    })
    const shootJson = await shootRes.json()
    assert.ok(shootJson && shootJson.ok, 'player shoot should succeed')

    console.log('integration_router.test.ts: all tests passed')
  } finally {
    server.close()
  }
}

runIntegrationTests().catch((err) => {
  console.error('integration_router.test.ts: test failed', err)
  process.exit(1)
})
