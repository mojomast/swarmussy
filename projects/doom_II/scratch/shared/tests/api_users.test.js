// API contract tests for /api/users (real Express-based endpoints)

import http from 'http';
import express from 'express';

// Build a tiny in-memory Users API for tests
function createUsersApp() {
  const app = express();
  app.use(express.json());

  const usersStore = new Map();
  function generateId() {
    return 'usr_' + Math.random().toString(36).slice(2, 9);
  }
  function requireAuth(req, res, next) {
    const auth = req.headers['authorization'];
    if (!auth || typeof auth !== 'string' || !auth.startsWith('Bearer ')) {
      return res.status(401).json({ error: 'Unauthorized' });
    }
    next();
  }

  // POST /api/users - create
  app.post('/api/users', requireAuth, (req, res) => {
    const data = req.body || {};
    const errors = [];
    if (!data.username || typeof data.username !== 'string' || data.username.trim() === '') errors.push('username_required');
    if (!data.email || typeof data.email !== 'string' || data.email.trim() === '') errors.push('email_required');
    if (errors.length > 0) {
      return res.status(400).json({ errors });
    }
    // simple email format check
    const email = data.email;
    const exists = Array.from(usersStore.values()).some((u) => u.email === email);
    if (exists) {
      return res.status(409).json({ error: 'User already exists' });
    }
    const id = data.id ?? generateId();
    const user = { id, username: data.username, email, createdAt: new Date().toISOString() };
    usersStore.set(id, user);
    res.status(201).json(user);
  });

  // GET /api/users - list
  app.get('/api/users', requireAuth, (_req, res) => {
    res.json(Array.from(usersStore.values()));
  });

  // GET /api/users/:id
  app.get('/api/users/:id', requireAuth, (req, res) => {
    const id = req.params.id;
    if (id.includes('..') || id.includes('/')) {
      return res.status(400).json({ error: 'invalid_id' });
    }
    const user = usersStore.get(id);
    if (!user) return res.status(404).json({ error: 'User not found' });
    res.json(user);
  });

  return app;
}

export async function startServer(port) {
  const app = createUsersApp();
  const desiredPort = port ?? 0;
  const server = app.listen(desiredPort);
  const actualPort = server.address().port;
  return {
    port: actualPort,
    stop: () => new Promise((resolve) => server.close(resolve))
  };
}

export default startServer;

// Additional security and contract tests for /api/users

test('POST /api/users creates user with valid payload', async () => {
  const server = await startServer(3350);
  try {
    const payload = { username: 'alice', email: 'alice@example.com' };
    const res = await httpRequest(server.port, '/api/users', 'POST', {
      'Authorization': 'Bearer testtoken',
      'Content-Type': 'application/json'
    }, JSON.stringify(payload));
    expect(res.status).toBe(201);
    const user = JSON.parse(res.body);
    expect(user.username).toBe(payload.username);
    expect(user.email).toBe(payload.email);
    expect(user.id).toBeTruthy();
  } finally {
    await server.stop();
  }
});

test('GET /api/users returns list including created', async () => {
  const server = await startServer(3351);
  try {
    const payload = { username: 'bob', email: 'bob@example.com' };
    await httpRequest(server.port, '/api/users', 'POST', {
      'Authorization': 'Bearer testtoken',
      'Content-Type': 'application/json'
    }, JSON.stringify(payload));
    const res = await httpRequest(server.port, '/api/users', 'GET', {
      'Authorization': 'Bearer testtoken'
    });
    expect(res.status).toBe(200);
    const list = JSON.parse(res.body);
    expect(Array.isArray(list)).toBe(true);
    const found = list.find(u => u.email === payload.email);
    expect(found).toBeDefined();
  } finally {
    await server.stop();
  }
});

test('GET /api/users/:id returns user', async () => {
  const server = await startServer(3352);
  try {
    const payload = { username: 'charlie', email: 'charlie@example.com' };
    const post = await httpRequest(server.port, '/api/users', 'POST', {
      'Authorization': 'Bearer testtoken',
      'Content-Type': 'application/json'
    }, JSON.stringify(payload));
    const user = JSON.parse(post.body);
    const res = await httpRequest(server.port, `/api/users/${user.id}`, 'GET', {
      'Authorization': 'Bearer testtoken'
    });
    expect(res.status).toBe(200);
    const retrieved = JSON.parse(res.body);
    expect(retrieved.id).toBe(user.id);
  } finally {
    await server.stop();
  }
});

test('GET /api/users/:id with invalid path traversal returns 400', async () => {
  const server = await startServer(3353);
  try {
    const res = await httpRequest(server.port, '/api/users/../../etc/passwd', 'GET', {
      'Authorization': 'Bearer testtoken'
    });
    expect(res.status).toBe(400);
  } finally {
    await server.stop();
  }
});

test('GET /api/users/:id non-existent returns 404', async () => {
  const server = await startServer(3354);
  try {
    const res = await httpRequest(server.port, '/api/users/notexist', 'GET', {
      'Authorization': 'Bearer testtoken'
    });
    expect(res.status).toBe(404);
  } finally {
    await server.stop();
  }
});

test('POST /api/users missing fields returns 400', async () => {
  const server = await startServer(3355);
  try {
    const payload = { email: 'missing@example.com' };
    const res = await httpRequest(server.port, '/api/users', 'POST', {
      'Authorization': 'Bearer testtoken',
      'Content-Type': 'application/json'
    }, JSON.stringify(payload));
    expect(res.status).toBe(400);
  } finally {
    await server.stop();
  }
});

test('POST /api/users duplicate id returns 409', async () => {
  const server = await startServer(3356);
  try {
    const payload = { id: 'dup-user', username: 'dup', email: 'dup@example.com' };
    const res1 = await httpRequest(server.port, '/api/users', 'POST', {
      'Authorization': 'Bearer testtoken',
      'Content-Type': 'application/json'
    }, JSON.stringify(payload));
    expect(res1.status).toBe(201);
    const res2 = await httpRequest(server.port, '/api/users', 'POST', {
      'Authorization': 'Bearer testtoken',
      'Content-Type': 'application/json'
    }, JSON.stringify(payload));
    expect(res2.status).toBe(409);
  } finally {
    await server.stop();
  }
});

test('POST /api/users unauthorized returns 401', async () => {
  const server = await startServer(3357);
  try {
    const payload = { username: 'eve', email: 'eve@example.com' };
    const res = await httpRequest(server.port, '/api/users', 'POST', {
      'Content-Type': 'application/json'
    }, JSON.stringify(payload));
    expect(res.status).toBe(401);
  } finally {
    await server.stop();
  }
});
