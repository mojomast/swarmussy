import { strict as assert } from 'assert';

// Import in-memory server helpers and client API wrappers
import { fetchMockHandler, resetMemoryStore } from '../server';
import { healthCheck, levelLoadFromServer, levelSaveFromServer, movePlayerToServer, shootPlayerToServer } from '../src/api';

async function runIntegrationTests() {
  // Wire global fetch to in-memory mock
  // @ts-ignore
  global.fetch = fetchMockHandler as any

  // Reset server state for deterministic tests
  resetMemoryStore()

  // Health check via client wrapper
  const health = await healthCheck()
  assert.ok(health && typeof (health as any).status !== 'undefined', 'healthCheck should return status')

  // Level load
  const lvlLoad = await levelLoadFromServer('level-1')
  assert.ok(lvlLoad.ok, 'levelLoadFromServer should succeed for level-1')
  if (lvlLoad.level) {
    assert.equal(lvlLoad.level.id, 'level-1', 'level id should match')
  }

  // Level save
  const lvlData = { id: 'level-1', name: 'Level 1 Updated', width: 20, height: 15, grid: [] }
  const lvlSave = await levelSaveFromServer('level-1', lvlData)
  assert.ok(lvlSave.ok, 'levelSaveFromServer should succeed')

  // Move player
  const move = await movePlayerToServer('integration-player', 2, -3)
  assert.ok(move.ok, 'movePlayerToServer should succeed')
  if (move.player) {
    assert.equal(move.player.id, 'integration-player')
    assert.equal(move.player.x, 2)
    assert.equal(move.player.y, -3)
  }

  // Shoot
  const shoot = await shootPlayerToServer('integration-player', { x: 1, y: 0 })
  assert.ok(shoot.ok, 'shootPlayerToServer should succeed')
  if (shoot.event) {
    assert.equal(shoot.event.playerId, 'integration-player')
  }

  console.log('integration_api.test.ts: all tests passed')
}

runIntegrationTests().catch((err) => {
  console.error('integration_api.test.ts: test failed', err)
  process.exit(1)
})
