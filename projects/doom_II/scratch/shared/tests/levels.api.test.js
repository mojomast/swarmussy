import http from 'http';
import { startServer } from '../src/api/levelsServer.js';

// Simple HTTP helper for Node.js tests
function httpRequest(port, path, method = 'GET', headers = {}, body = null) {
  return new Promise((resolve, reject) => {
    const opts = {
      hostname: 'localhost',
      port,
      path,
      method,
      headers,
    };
    const req = http.request(opts, (res) => {
      let data = '';
      res.on('data', (chunk) => { data += chunk; });
      res.on('end', () => {
        resolve({ status: res.statusCode, body: data });
      });
    });
    req.on('error', reject);
    if (body) {
      req.write(body);
    }
    req.end();
  });
}

// Basic Level schema validation tests (self-contained)
const levelSchema = {
  type: 'object',
  required: ['id','name','dimensions','tiles','monsters','weapons','assets','spawn_points','version'],
  properties: {
    id: { type: 'string' },
    name: { type: 'string' },
    dimensions: {
      type: 'object', required: ['width','height','depth'], properties: {
        width: { type: 'number' }, height: { type: 'number' }, depth: { type: 'number' }
      }
    },
    tiles: { type: 'array', items: { type: 'string' } },
    monsters: { type: 'array', items: { type: 'string' } },
    weapons: { type: 'array', items: { type: 'string' } },
    assets: { type: 'array', items: { type: 'string' } },
    spawn_points: {
      type: 'array', items: {
        type: 'object', required: ['x','y','z'], properties: { x: { type: 'number' }, y: { type: 'number' }, z: { type: 'number' } }
      }
    },
    version: { type: 'string', pattern: '^\\d+\\.\\d+\\.\\d+$' }
  },
  additionalProperties: false
};

// Lightweight JSON schema validator import used by the API
import { validateJson } from '../src/validate.js';

test('validate level schema - valid', () => {
  const lvl = { id: 'lvl1', name: 'Test', dimensions: { width: 10, height: 10, depth: 2 }, tiles: [], monsters: [], weapons: [], assets: [], spawn_points: [{ x:0,y:0,z:0 }], version: '1.0.0' };
  const res = validateJson(levelSchema, lvl);
  expect(res.valid).toBe(true);
});

test('validate level schema - missing required', () => {
  const lvl = { id: 'lvl1' };
  const res = validateJson(levelSchema, lvl);
  expect(res.valid).toBe(false);
  expect(res.errors.length).toBeGreaterThan(0);
});

// API tests

test('GET /levels returns sample levels with authorized request', async () => {
  const server = await startServer(3333);
  try {
    const res = await httpRequest(server.port, '/levels', 'GET', { 'Authorization': 'Bearer testtoken' });
    expect(res.status).toBe(200);
    const data = JSON.parse(res.body);
    expect(Array.isArray(data)).toBe(true);
    expect(data.length).toBeGreaterThanOrEqual(1);
    expect(data[0].id).toBe('lvl-01');
  } finally {
    await server.stop();
  }
});

test('GET /levels/:id returns existing level', async () => {
  const server = await startServer(3334);
  try {
    const res = await httpRequest(server.port, '/levels/lvl-01', 'GET', { 'Authorization': 'Bearer testtoken' });
    expect(res.status).toBe(200);
    const lev = JSON.parse(res.body);
    expect(lev.id).toBe('lvl-01');
  } finally {
    await server.stop();
  }
});

test('GET /levels/:id rejects path traversal', async () => {
  const server = await startServer(3335);
  try {
    const res = await httpRequest(server.port, '/levels/../../etc/passwd', 'GET', { 'Authorization': 'Bearer testtoken' });
    expect(res.status).toBe(400);
  } finally {
    await server.stop();
  }
});

test('GET /levels unauthorized is rejected', async () => {
  const server = await startServer(3336);
  try {
    const res = await httpRequest(server.port, '/levels', 'GET', {});
    expect(res.status).toBe(401);
  } finally {
    await server.stop();
  }
});

test('POST /levels creates a new level and can be retrieved', async () => {
  const server = await startServer(3337);
  try {
    const payload = {
      id: 'lvl-02',
      name: 'New Level',
      dimensions: { width: 5, height: 5, depth: 1 },
      tiles: [], monsters: [], weapons: [], assets: [], spawn_points: [{ x:0, y:0, z:0 }], version: '1.0.0'
    };
    const resPost = await httpRequest(server.port, '/levels', 'POST', {
      'Authorization': 'Bearer testtoken',
      'Content-Type': 'application/json'
    }, JSON.stringify(payload));
    expect(resPost.status).toBe(201);
    const created = JSON.parse(resPost.body);
    expect(created.id).toBe('lvl-02');

    const resGet = await httpRequest(server.port, '/levels/lvl-02', 'GET', { 'Authorization': 'Bearer testtoken' });
    expect(resGet.status).toBe(200);
    const lev = JSON.parse(resGet.body);
    expect(lev.id).toBe('lvl-02');
  } finally {
    await server.stop();
  }
});

test('POST /levels duplicate id returns conflict', async () => {
  const server = await startServer(3338);
  try {
    const payload = {
      id: 'dup-lvl',
      name: 'Dup Level',
      dimensions: { width: 3, height: 3, depth: 1 },
      tiles: [], monsters: [], weapons: [], assets: [], spawn_points: [{ x:0, y:0, z:0 }], version: '1.0.0'
    };
    // first create
    const res1 = await httpRequest(server.port, '/levels', 'POST', {
      'Authorization': 'Bearer testtoken',
      'Content-Type': 'application/json'
    }, JSON.stringify(payload));
    expect(res1.status).toBe(201);
    // second create with same id
    const res2 = await httpRequest(server.port, '/levels', 'POST', {
      'Authorization': 'Bearer testtoken',
      'Content-Type': 'application/json'
    }, JSON.stringify(payload));
    expect(res2.status).toBe(409);
  } finally {
    await server.stop();
  }
});

test('GET /levels rate limiting after 5 requests', async () => {
  const server = await startServer(3339);
  try {
    // make 6 authorized requests in sequence
    for (let i = 0; i < 6; i++) {
      const res = await httpRequest(server.port, '/levels', 'GET', { 'Authorization': 'Bearer testtoken' });
      if (i < 5) {
        expect(res.status).toBe(200);
      } else {
        // 6th should be rate-limited
        expect(res.status).toBe(429);
      }
    }
  } finally {
    await server.stop();
  }
});
