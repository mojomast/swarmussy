import http from 'http';
import express from 'express';
import levelsRouter, { resetLevelsStore } from '../src/engine/api/levels.js';

let server;
let port;

function createApp() {
  const app = express();
  app.use(express.json());
  app.use('/levels', levelsRouter);
  return app;
}

beforeAll((done) => {
  const app = createApp();
  server = app.listen(0, () => {
    port = server.address().port;
    done();
  });
});

afterAll((done) => {
  server.close(done);
});

function request(path, method, body) {
  return new Promise((resolve, reject) => {
    const options = {
      hostname: '127.0.0.1',
      port,
      path,
      method,
      headers: {
        'Content-Type': 'application/json',
      },
    };
    const req = http.request(options, (res) => {
      let data = '';
      res.on('data', (chunk) => (data += chunk));
      res.on('end', () => {
        let payload = null;
        try {
          payload = data ? JSON.parse(data) : null;
        } catch (e) {
          payload = data;
        }
        resolve({ statusCode: res.statusCode, body: payload });
      });
    });
    req.on('error', reject);
    if (body) {
      req.write(JSON.stringify(body));
    }
    req.end();
  });
}

describe('Levels API', () => {
  beforeEach(() => {
    // Reset store before each test to ensure isolation
    resetLevelsStore();
  });

  test('GET /levels returns empty array initially', async () => {
    const res = await request('/levels', 'GET', null);
    expect(res.statusCode).toBe(200);
    expect(Array.isArray(res.body)).toBe(true);
    expect(res.body.length).toBe(0);
  });

  test('POST /levels creates a level', async () => {
    const payload = {
      name: 'First Level',
      difficulty: 'easy',
      map: ['tile_a', 'tile_b'],
      monsters: ['goblin'],
      assets: ['asset_1'],
    };
    const postRes = await request('/levels', 'POST', payload);
    expect(postRes.statusCode).toBe(201);
    expect(postRes.body).toBeDefined();
    expect(postRes.body.id).toBeDefined();
    expect(postRes.body.name).toBe(payload.name);
  });

  test('GET /levels/:id reads a level', async () => {
    // create first
    const payload = {
      name: 'Second Level',
      difficulty: 'normal',
      map: ['t1'],
      monsters: [],
      assets: [],
    };
    const created = await request('/levels', 'POST', payload);
    expect(created.statusCode).toBe(201);
    const id = created.body.id;
    const getRes = await request(`/levels/${id}`, 'GET', null);
    expect(getRes.statusCode).toBe(200);
    expect(getRes.body.id).toBe(id);
    expect(getRes.body.name).toBe(payload.name);
  });

  test('PUT /levels/:id updates a level', async () => {
    const payload = {
      name: 'Third Level',
      difficulty: 'hard',
      map: [],
      monsters: [],
      assets: [],
    };
    const created = await request('/levels', 'POST', payload);
    const id = created.body.id;
    const update = {
      name: 'Third Level Updated',
      difficulty: 'normal',
      map: ['mx'],
      monsters: ['dragon'],
      assets: ['asset_x'],
    };
    const putRes = await request(`/levels/${id}`, 'PUT', update);
    expect(putRes.statusCode).toBe(200);
    expect(putRes.body.name).toBe(update.name);
    expect(putRes.body.difficulty).toBe(update.difficulty);
  });

  test('POST /levels with invalid payload returns 400', async () => {
    const bad = { difficulty: 'normal' };
    const res = await request('/levels', 'POST', bad);
    expect(res.statusCode).toBe(400);
  });
});
