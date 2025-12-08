import { strict as assert } from 'assert';
import { startServer, stopServer } from '../server';

async function runTests() {
  await startServer()
  const base = 'http://localhost:5173'

  // Health
  const health = await fetch(`${base}/api/health`).then(r => r.json())
  assert.ok(health && health.status === 'ok', 'health should be ok')

  // Create a level
  const levelPayload = { id: 'integration-level', name: 'Integration Level', width: 10, height: 10, grid: [] }
  const create = await fetch(`${base}/api/levels`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(levelPayload)
  }).then(r => r.json())
  assert.ok(create && create.success, 'level create should succeed')

  // List levels
  const levels = await fetch(`${base}/api/levels`).then(r => r.json())
  assert.ok(Array.isArray(levels), 'levels should be an array')
  const found = levels.find((l: any) => l.id === 'integration-level')
  assert.ok(found, 'integration-level should exist in list')

  // Load level
  const loaded = await fetch(`${base}/api/levels/load`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ levelId: 'integration-level' })
  }).then(r => r.json())
  assert.ok(loaded && loaded.ok, 'level load should be ok')
  if (loaded?.level) {
    assert.equal(loaded.level.id, 'integration-level')
  }

  // Save level
  const saved = await fetch(`${base}/api/levels/save`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ levelId: 'integration-level', data: { name: 'Integration Level Updated' } })
  }).then(r => r.json())
  assert.ok(saved && saved.ok, 'level save should be ok')

  // Move player
  const mv = await fetch(`${base}/api/player/move`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ playerId: 'integration-player', dx: 2, dy: -3 })
  }).then(r => r.json())
  assert.ok(mv && mv.ok, 'player move should be ok')

  // Shoot
  const sh = await fetch(`${base}/api/player/shoot`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ playerId: 'integration-player', targetX: 1, targetY: 0 })
  }).then(r => r.json())
  assert.ok(sh && sh.ts, 'player shoot should return timestamp')

  await stopServer()
}

runTests().catch((err) => {
  console.error('integration_backend_endpoints.test.ts failed', err)
  process.exit(1)
})
