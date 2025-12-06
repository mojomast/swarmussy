"use strict";

const { createApp } = require('../app');
const supertest = require('supertest');

let app;
let request;

beforeAll(() => {
  app = createApp();
  request = supertest(app);
});

describe('Bonus Mode endpoints', () => {
  test('GET /api/bonus/top should be accessible and return an array', async () => {
    const res = await request.get('/api/bonus/top?limit=5');
    expect(res.status).toBe(200);
    expect(Array.isArray(res.body)).toBe(true);
  });

  test('POST /api/bonus/award without admin header should be forbidden', async () => {
    const res = await request.post('/api/bonus/award')
      .send({ userId: 'u1', username: 'Tester', amount: 10, reason: 'test' });
    expect(res.status).toBe(403);
  });

  test('POST /api/bonus/award with admin header should succeed', async () => {
    const res = await request.post('/api/bonus/award')
      .set('x-admin', 'true')
      .send({ userId: 'u1', username: 'Tester', amount: 25, reason: 'test' });
    expect(res.status).toBe(200);
    expect(res.body).toHaveProperty('entry');
    expect(res.body.entry).toHaveProperty('userId');
    expect(res.body.entry.userId).toBe('u1');
  });

  test('GET /api/bonus/top should include awarded entry', async () => {
    const res = await request.get('/api/bonus/top?limit=5');
    expect(res.status).toBe(200);
    expect(Array.isArray(res.body)).toBe(true);
    const found = res.body.find(e => e.userId === 'u1');
    expect(found).toBeDefined();
  });
});
