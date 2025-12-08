import http from 'http'

// Start/stop helpers from server
import { startServer, stopServer } from '../server'

const HOST = '127.0.0.1'

function request(port: number, method: string, path: string, body?: any, headers?: Record<string, string>): Promise<{ statusCode: number; body: any }> {
  return new Promise((resolve, reject) => {
    const options: http.RequestOptions = {
      hostname: HOST,
      port,
      path,
      method,
      headers: {
        'Content-Type': 'application/json',
        ...(headers || {})
      }
    }
    const req = http.request(options, (res) => {
      let data = ''
      res.on('data', (chunk) => { data += chunk })
      res.on('end', () => {
        try {
          const parsed = data ? JSON.parse(data) : null
          resolve({ statusCode: res.statusCode || 0, body: parsed })
        } catch (e) {
          // If not JSON, return raw
          resolve({ statusCode: res.statusCode || 0, body: data })
        }
      })
    })
    req.on('error', (err) => reject(err))
    if (body !== undefined) {
      req.write(JSON.stringify(body))
    }
    req.end()
  })
}

describe('Backend API sanity and security tests', () => {
  let port = 5173
  beforeAll(async () => {
    // Start server for tests
    await stopServer()
    await startServer(port)
  })
  afterAll(async () => {
    await stopServer()
  })

  test('GET /api/health is public and returns ok', async () => {
    const res = await request(port, 'GET', '/api/health')
    expect(res.statusCode).toBe(200)
    expect(res.body?.status).toBe('ok')
  })

  test('POST /api/level/load with invalid payload returns 400 (auth required)', async () => {
    const res = await request(port, 'POST', '/api/level/load', { levelId: '' }, { 'x-api-key': 'BUGSY-KEY-123' })
    expect(res.statusCode).toBe(400)
  })

  test('POST /api/level/load with valid payload and auth succeeds', async () => {
    const res = await request(port, 'POST', '/api/level/load', { levelId: 'level-1' }, { 'x-api-key': 'BUGSY-KEY-123' })
    expect(res.statusCode).toBe(200)
    expect(res.body?.ok).toBe(true)
  })

  test('POST /api/level/save with valid payload and auth succeeds', async () => {
    const res = await request(port, 'POST', '/api/level/save', { levelId: 'level-1', data: { name: 'First Level' } }, { 'x-api-key': 'BUGSY-KEY-123' })
    expect(res.statusCode).toBe(200)
    expect(res.body?.ok).toBe(true)
  })

  test('POST /api/player/move creates and moves a player', async () => {
    const res = await request(port, 'POST', '/api/player/move', { playerId: 'player-1', dx: 2, dy: 3 }, { 'x-api-key': 'BUGSY-KEY-123' })
    expect(res.statusCode).toBe(200)
    expect(res.body?.player?.id).toBe('player-1')
    expect(res.body?.player?.x).toBe(2)
    expect(res.body?.player?.y).toBe(3)
  })

  test('POST /api/player/shoot registers a shot event', async () => {
    const res = await request(port, 'POST', '/api/player/shoot', { playerId: 'player-1', direction: { x: 1, y: 0 } }, { 'x-api-key': 'BUGSY-KEY-123' })
    expect(res.statusCode).toBe(200)
    expect(res.body?.ok).toBe(true)
  })
})
