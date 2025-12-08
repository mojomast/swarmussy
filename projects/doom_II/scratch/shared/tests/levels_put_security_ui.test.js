import http from 'http';
import { startServer } from '../src/api/levelsServer.js';

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

const validPayload = {
  id: 'lvl-01',
  name: 'Updated Level',
  dimensions: { width: 10, height: 10, depth: 1 },
  tiles: ['tile1'],
  monsters: ['goblin'],
  weapons: ['sword'],
  assets: ['asset'],
  spawn_points: [{ x: 0, y: 0, z: 0 }],
  version: '1.1.0'
};

// Unauthorized PUT should be rejected
test('PUT /levels/:id unauthorized returns 401', async () => {
  const server = await startServer(3350);
  try {
    const resPut = await httpRequest(server.port, '/levels/lvl-01', 'PUT', {
      // Intentionally no Authorization header
      'Content-Type': 'application/json'
    }, JSON.stringify(validPayload));
    expect(resPut.status).toBe(401);
  } finally {
    await server.stop();
  }
});

// ID mismatch should return 400
test('PUT /levels/:id id_mismatch returns 400', async () => {
  const server = await startServer(3351);
  try {
    const payload = { ...validPayload, id: 'lvl-02' }; // payload id does not match path id
    const resPut = await httpRequest(server.port, '/levels/lvl-01', 'PUT', {
      'Authorization': 'Bearer testtoken',
      'Content-Type': 'application/json'
    }, JSON.stringify(payload));
    expect(resPut.status).toBe(400);
  } finally {
    await server.stop();
  }
});

// Integration check: after valid PUT, GET returns updated level (UI would fetch)
test('UI integration: GET /levels reflects updates after PUT', async () => {
  const server = await startServer(3352);
  try {
    // First update with valid payload
    const resPut = await httpRequest(server.port, '/levels/lvl-01', 'PUT', {
      'Authorization': 'Bearer testtoken',
      'Content-Type': 'application/json'
    }, JSON.stringify(validPayload));
    expect(resPut.status).toBe(200);
    // Then fetch list to simulate UI rendering of levels list
    const resGet = await httpRequest(server.port, '/levels', 'GET', {
      'Authorization': 'Bearer testtoken'
    });
    expect(resGet.status).toBe(200);
    const levels = JSON.parse(resGet.body);
    const found = levels.find((l) => l.id === 'lvl-01');
    expect(found).toBeTruthy();
    expect(found.name).toBe('Updated Level');
  } finally {
    await server.stop();
  }
});
