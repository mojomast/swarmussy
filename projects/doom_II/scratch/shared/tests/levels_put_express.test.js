import http from 'http';
import express from 'express';

function startExpressApp() {
  const app = express();
  app.use(express.json());

  // In-memory store for this test
  let levelsStore = [
    {
      id: 'lvl-01',
      name: 'Sample Level',
      dimensions: { width: 8, height: 8, depth: 1 },
      tiles: [],
      monsters: [],
      weapons: [],
      assets: [],
      spawn_points: [{ x: 0, y: 0, z: 0 }],
      version: '1.0.0'
    }
  ];

  // PUT /levels/:id implementation mirroring POST rules as a unit under test
  app.put('/levels/:id', (req, res) => {
    const id = req.params.id;
    // basic path traversal protection
    if (id.includes('..') || id.includes('/')) {
      return res.status(400).json({ error: 'invalid_id' });
    }
    const existingIndex = levelsStore.findIndex(l => l.id === id);
    if (existingIndex === -1) {
      return res.status(404).json({ error: 'Level not found' });
    }
    const payload = req.body || {};
    const errors = [];
    // id must match path if provided
    if (payload.id !== undefined && payload.id !== id) {
      errors.push('id_mismatch');
    }
    const { name, description, difficulty, enabled, dimensions, tiles, monsters, weapons, assets, spawn_points, version } = payload;
    if (name === undefined || typeof name !== 'string' || name.trim().length === 0) errors.push('Name is required');
    if (difficulty === undefined || !['Easy','Medium','Hard'].includes(difficulty)) errors.push('Valid difficulty is required');
    if (description !== undefined && typeof description === 'string' && description.length > 500) errors.push('Description too long');
    if (tiles !== undefined && !Array.isArray(tiles)) errors.push('tiles should be an array');
    if (monsters !== undefined && !Array.isArray(monsters)) errors.push('monsters should be an array');
    if (weapons !== undefined && !Array.isArray(weapons)) errors.push('weapons should be an array');
    if (assets !== undefined && !Array.isArray(assets)) errors.push('assets should be an array');
    if (spawn_points !== undefined && !Array.isArray(spawn_points)) errors.push('spawn_points should be an array');
    if (version !== undefined && typeof version !== 'string') errors.push('version should be string');
    if (errors.length > 0) return res.status(400).json({ errors });
    // update
    const existing = levelsStore[existingIndex];
    if (name !== undefined) existing.name = name.trim();
    if (description !== undefined) existing.description = description;
    if (difficulty !== undefined) existing.difficulty = difficulty;
    if (dimensions !== undefined) existing.dimensions = dimensions;
    if (tiles !== undefined) existing.tiles = tiles;
    if (monsters !== undefined) existing.monsters = monsters;
    if (weapons !== undefined) existing.weapons = weapons;
    if (assets !== undefined) existing.assets = assets;
    if (spawn_points !== undefined) existing.spawn_points = spawn_points;
    if (version !== undefined) existing.version = version;
    existing.updatedAt = new Date().toISOString();
    return res.json(existing);
  });

  // GET to fetch level by id
  app.get('/levels/:id', (req, res) => {
    const id = req.params.id;
    const lv = levelsStore.find(l => l.id === id);
    if (!lv) return res.status(404).json({ error: 'not_found' });
    res.json(lv);
  });

  const server = app.listen(0); // random port
  return new Promise((resolve)=>{
    server.on('listening', ()=> {
      const port = server.address().port;
      resolve({ stop: () => new Promise((r)=> server.close(()=> r())), port, app });
    });
  });
}

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

test('PUT existing level updates with valid payload (express style test)', async () => {
  const started = await startExpressApp();
  const port = started.port;
  try {
    const payload = {
      id: 'lvl-01',
      name: 'Updated Level',
      dimensions: { width: 5, height: 5, depth: 1 },
      tiles: [], monsters: [], weapons: [], assets: [], spawn_points: [{ x:0,y:0,z:0 }], version: '1.0.1'
    };
    const resPut = await httpRequest(port, '/levels/lvl-01', 'PUT', { 'Content-Type': 'application/json' }, JSON.stringify(payload));
    expect(resPut.status).toBe(200);
  } finally {
    await started.stop();
  }
});

// 400 on invalid payload
test('PUT invalid payload returns 400', async () => {
  const started = await startExpressApp();
  const port = started.port;
  try {
    const payload = { id: 'lvl-01' }; // missing required fields
    const resPut = await httpRequest(port, '/levels/lvl-01', 'PUT', { 'Content-Type': 'application/json' }, JSON.stringify(payload));
    expect(resPut.status).toBe(400);
  } finally {
    await started.stop();
  }
});

// 404 when updating non-existent
test('PUT non-existent returns 404', async () => {
  const started = await startExpressApp();
  const port = started.port;
  try {
    const payload = {
      id: 'not-exist',
      name: 'X',
      dimensions: { width: 1, height: 1, depth: 1 },
      tiles: [], monsters: [], weapons: [], assets: [], spawn_points: [{ x:0,y:0,z:0 }], version: '1.0.0'
    };
    const resPut = await httpRequest(port, '/levels/not-exist', 'PUT', { 'Content-Type': 'application/json' }, JSON.stringify(payload));
    expect(resPut.status).toBe(404);
  } finally {
    await started.stop();
  }
});

// traversal rejection
test('PUT path traversal rejected (400)', async () => {
  const started = await startExpressApp();
  const port = started.port;
  try {
    const payload = {
      id: 'lvl-01',
      name: 'X',
      dimensions: { width: 1, height: 1, depth: 1 },
      tiles: [], monsters: [], weapons: [], assets: [], spawn_points: [{ x:0,y:0,z:0 }], version: '1.0.0'
    };
    const resPut = await httpRequest(port, '/levels/../../etc/passwd', 'PUT', { 'Content-Type': 'application/json' }, JSON.stringify(payload));
    expect(resPut.status).toBe(400);
  } finally {
    await started.stop();
  }
});

