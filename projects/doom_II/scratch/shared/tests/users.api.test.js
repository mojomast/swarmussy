import express from 'express';
import request from 'supertest';
import usersRouter, { resetUsersStore } from '../src/users.js';

describe('Users API (Express + SQLite with memory fallback)', () => {
  let app;

  beforeEach(() => {
    resetUsersStore();
    app = express();
    app.use(express.json());
    // Mount under /api so tests can call /api/users
    app.use('/api', usersRouter);
  });

  test('POST /api/users creates a user', async () => {
    const user = { username: 'alice', email: 'alice@example.com', password: 'password123' };
    const res = await request(app)
      .post('/api/users')
      .set('Authorization', 'Bearer testtoken')
      .send(user);
    expect(res.status).toBe(201);
    expect(res.body).toHaveProperty('id');
    expect(res.body.username).toBe('alice');
    expect(res.body.email).toBe('alice@example.com');
  });

  test('GET /api/users returns list including created user', async () => {
    // Create a user first
    await request(app)
      .post('/api/users')
      .set('Authorization', 'Bearer testtoken')
      .send({ username: 'bob', email: 'bob@example.com', password: 'secret456' });

    const res = await request(app)
      .get('/api/users')
      .set('Authorization', 'Bearer testtoken');
    expect(res.status).toBe(200);
    expect(Array.isArray(res.body)).toBe(true);
    expect(res.body.length).toBeGreaterThanOrEqual(1);
  });

  test('GET /api/users/:id returns the user', async () => {
    const create = await request(app)
      .post('/api/users')
      .set('Authorization', 'Bearer testtoken')
      .send({ username: 'charlie', email: 'charlie@example.com', password: 'pass7890' });
    const id = create.body.id;
    const res = await request(app)
      .get(`/api/users/${id}`)
      .set('Authorization', 'Bearer testtoken');
    expect(res.status).toBe(200);
    expect(res.body).toHaveProperty('id', id);
    expect(res.body.username).toBe('charlie');
    expect(res.body.email).toBe('charlie@example.com');
  });
});
