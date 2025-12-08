import { strict as assert } from 'assert'
import { startServer, stopServer } from '../server'

const BASE = 'http://localhost:5173'

describe('backend_sanity_and_security (basic API sanity tests)', () => {
  let server: any

  beforeAll(async () => {
    server = await startServer(5173)
  })

  afterAll(async () => {
    await stopServer()
  })

  it('health endpoint returns ok', async () => {
    const res = await globalThis.fetch(`${BASE}/api/health`)
    assert(res.ok)
    const body = await res.json()
    assert.ok(body && body.status === 'ok')
  })

  it('level create requires id (validation fail)', async () => {
    const res = await globalThis.fetch(`${BASE}/api/levels`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name: 'Bad Level' }),
    })
    assert(res.status === 400)
  })

  it('level create with id succeeds', async () => {
    const res = await globalThis.fetch(`${BASE}/api/levels`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ levelId: 'sanity-level', name: 'Sanity Level' }),
    })
    assert(res.status === 200)
    const body = await res.json()
    assert.ok(body?.ok)
  })

  it('level load works for existing id', async () => {
    const res = await globalThis.fetch(`${BASE}/api/levels/load`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ levelId: 'sanity-level' }),
    })
    assert(res.status === 200)
    const body = await res.json()
    assert.ok(body?.level?.id === 'sanity-level' || body?.level?.id === 'sanity-level')
  })

  it('level save updates existing level', async () => {
    const res = await globalThis.fetch(`${BASE}/api/levels/save`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ levelId: 'sanity-level', data: { name: 'Sanity Level Updated' } }),
    })
    assert(res.status === 200)
    const body = await res.json()
    assert.ok(body?.ok)
  })

  it('player move updates position', async () => {
    const res = await globalThis.fetch(`${BASE}/api/player/move`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ playerId: 'sanity-player', dx: 3, dy: 1 }),
    })
    assert(res.status === 200)
    const body = await res.json()
    assert.ok(body?.ok || body?.pos?.x !== undefined)
  })

  it('player shoot returns timestamp', async () => {
    const res = await globalThis.fetch(`${BASE}/api/player/shoot`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ playerId: 'sanity-player', direction: { x: 1, y: 0 } }),
    })
    assert(res.status === 200)
    const body = await res.json()
    assert.ok(typeof body?.ts === 'number')
  })
})
