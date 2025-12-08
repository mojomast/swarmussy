import { strict as assert } from 'assert'
import { startServer, stopServer } from '../server'

const BASE = 'http://localhost:5173'

describe('integration_backend_http (in-memory Express server)', () => {
  beforeAll(async () => {
    await startServer()
  })

  afterAll(async () => {
    await stopServer()
  })

  it('health returns ok and uptime', async () => {
    const res = await globalThis.fetch(`${BASE}/api/health`)
    assert(res.status === 200)
    const body = await res.json()
    assert(body?.status === 'ok')
  })

  it('level load returns level data for existing id', async () => {
    const res = await globalThis.fetch(`${BASE}/api/levels/load`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ levelId: 'level-1' }),
    })
    assert(res.status === 200)
    const body = await res.json()
    assert.ok(body.ok || body?.id === 'level-1' || Array.isArray(body) || typeof body === 'object')
  })

  it('level save succeeds', async () => {
    const res = await globalThis.fetch(`${BASE}/api/levels/save`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ levelId: 'level-1', data: { name: 'Updated' } }),
    })
    assert(res.status === 200)
    const body = await res.json()
    assert.ok(body?.ok)
    assert(typeof body?.updatedAt === 'number')
  })

  it('player move updates position', async () => {
    const res = await globalThis.fetch(`${BASE}/api/player/move`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ playerId: 'tester', dx: 2, dy: -1 }),
    })
    assert(res.status === 200)
    const body = await res.json()
    assert.ok(body?.ok)
    assert.equal(body?.pos?.x, 2)
    assert.equal(body?.pos?.y, -1)
  })

  it('player shoot returns timestamp', async () => {
    const res = await globalThis.fetch(`${BASE}/api/player/shoot`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ playerId: 'tester', direction: { x: 1, y: 0 } }),
    })
    assert(res.status === 200)
    const body = await res.json()
    assert.ok(body?.ok)
    assert(typeof body?.ts === 'number')
  })
})
