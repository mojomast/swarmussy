import { strict as assert } from 'assert'
import { startServer, stopServer } from '../server'

const BASE = 'http://localhost:5173'

describe('integration_http_edge_cases', () => {
  beforeAll(async () => {
    await startServer()
  })

  afterAll(async () => {
    await stopServer()
  })

  it('POST /api/levels without id returns 400', async () => {
    const res = await globalThis.fetch(`${BASE}/api/levels`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name: 'Bad Level' }),
    })
    // Our handler returns 400 for missing id
    // Since this test runs after server has started, ensure 400
    // If the server does not set 400, this test will fail.
    assert(res.status === 400)
  })
})
