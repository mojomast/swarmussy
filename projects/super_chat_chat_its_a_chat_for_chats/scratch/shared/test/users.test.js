"use strict";

const request = require('supertest');
const express = require('express');
const { initDb, createUsersRouter } = require('../src/users');
const path = require('path');
const os = require('os');

describe('Users API Skeleton', () => {
  let app;
  let db;
  let dbPath;

  beforeAll(() => {
    // Create a temporary sqlite file for tests
    dbPath = path.join(os.tmpdir(), `test_users_${Date.now()}.db`);
    db = initDb(dbPath);

    app = express();
    app.use(express.json());
    const router = createUsersRouter(db);
    app.use('/', router);
  });

  afterAll(() => {
    if (db) {
      try {
        db.close();
      } catch (_) {}
    }
    try {
      const fs = require('fs');
      if (fs.existsSync(dbPath)) {
        fs.unlinkSync(dbPath);
      }
    } catch (_) {}
  });

  test('GET /users returns empty array initially', async () => {
    const res = await request(app).get('/users');
    expect(res.status).toBe(200);
    expect(Array.isArray(res.body)).toBe(true);
    expect(res.body.length).toBe(0);
  });

  test('POST /users creates a user', async () => {
    const payload = { name: 'Test User', email: 'test1@example.com' };
    const res = await request(app).post('/users').send(payload);
    expect(res.status).toBe(201);
    expect(res.body).toHaveProperty('id');
    expect(res.body.name).toBe(payload.name);
    expect(res.body.email).toBe(payload.email);
    expect(typeof res.body.created_at).toBe('string');
  });

  test('GET /users/:id returns user', async () => {
    // Create a second user
    const payload = { name: 'Another User', email: 'another@example.com' };
    const postRes = await request(app).post('/users').send(payload);
    const id = postRes.body.id;
    const getRes = await request(app).get(`/users/${id}`);
    expect(getRes.status).toBe(200);
    expect(getRes.body).toHaveProperty('id', id);
    expect(getRes.body.name).toBe(payload.name);
    expect(getRes.body.email).toBe(payload.email);
  });

  test('POST /users with invalid payload returns 400', async () => {
    const res = await request(app).post('/users').send({ name: '', email: 'bad' });
    expect(res.status).toBe(400);
    expect(res.body).toHaveProperty('errors');
  });

  test('POST /users with duplicate email returns 409', async () => {
    const payload = { name: 'Unique', email: 'dup@example.com' };
    const first = await request(app).post('/users').send(payload);
    expect(first.status).toBe(201);
    const second = await request(app).post('/users').send(payload);
    expect(second.status).toBe(409);
  });
});
