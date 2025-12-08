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

test('PUT /levels/:id updates existing level with valid payload', async () => {
  const server = await startServer(3340);
  try {
    const resPut = await httpRequest(server.port, '/levels/lvl-01', 'PUT', {
      'Authorization': 'Bearer testtoken',
      'Content-Type': 'application/json'
    }, JSON.stringify(validPayload));
    expect(resPut.status).toBe(200);
    const updated = JSON.parse(resPut.body);
    expect(updated.id).toBe('lvl-01');
    expect(updated.name).toBe('Updated Level');

    // verify via GET
    const resGet = await httpRequest(server.port, '/levels/lvl-01', 'GET', {
      'Authorization': 'Bearer testtoken'
    });
    expect(resGet.status).toBe(200);
    const lev = JSON.parse(resGet.body);
    expect(lev.name).toBe('Updated Level');
  } finally {
    await server.stop();
  }
});

test('PUT /levels/:id invalid payload returns 400 with errors', async () => {
  const server = await startServer(3341);
  try {
    const badPayload = { id: 'lvl-01' }; // missing required fields
    const resPut = await httpRequest(server.port, '/levels/lvl-01', 'PUT', {
      'Authorization': 'Bearer testtoken',
      'Content-Type': 'application/json'
    }, JSON.stringify(badPayload));
    expect(resPut.status).toBe(400);
  } finally {
    await server.stop();
  }
});

test('PUT /levels/:id non-existent returns 404', async () => {
  const server = await startServer(3342);
  try {
    const payload = { id: 'lvl-999', name: 'Nope', dimensions: { width: 1, height: 1, depth: 1 }, tiles: [], monsters: [], weapons: [], assets: [], spawn_points: [{ x:0,y:0,z:0 }], version: '1.0.0' };
    const resPut = await httpRequest(server.port, '/levels/lvl-99', 'PUT', {
      'Authorization': 'Bearer testtoken',
      'Content-Type': 'application/json'
    }, JSON.stringify(payload));
    expect(resPut.status).toBe(404);
  } finally {
    await server.stop();
  }
});

test('PUT /levels/:id path traversal rejected (400)', async () => {
  const server = await startServer(3343);
  try {
    const payload = { id: 'lvl-01', name: 'X', dimensions: { width: 1, height: 1, depth: 1 }, tiles: [], monsters: [], weapons: [], assets: [], spawn_points: [{ x:0,y:0,z:0 }], version: '1.0.0' };
    const resPut = await httpRequest(server.port, '/levels/../../etc/passwd', 'PUT', {
      'Authorization': 'Bearer testtoken',
      'Content-Type': 'application/json'
    }, JSON.stringify(payload));
    expect(resPut.status).toBe(400);
  } finally {
    await server.stop();
  }
});

test('GET /levels unauthorized is rejected', async () => {
  const server = await startServer(3344);
  try {
    const res = await httpRequest(server.port, '/levels', 'GET', {});
    expect(res.status).toBe(401);
  } finally {
    await server.stop();
  }
});
