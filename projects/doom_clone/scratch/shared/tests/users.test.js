/*
  Unit tests for the User API
  - GET /users
  - POST /users
  - GET /users/:id
  - Tests include pagination and auth
*/

const assert = require('assert');
const path = require('path');
const fs = require('fs');

// Point the DB path to a test database BEFORE requiring the router
const DB_PATH = path.resolve(__dirname, 'test_db.sqlite');
process.env.DB_PATH = DB_PATH;

const createRouter = require('../src/users.js');

(async () => {
  // Cleanup any previous test db
  if (fs.existsSync(DB_PATH)) fs.unlinkSync(DB_PATH);

  const express = require('express');
  const app = express();
  app.use(express.json());

  const router = await createRouter();
  app.use('/api', router);

  const http = require('http');
  const server = http.createServer(app);
  await new Promise(resolve => server.listen(0, resolve));
  const port = server.address().port;

  function request(options, data) {
    return new Promise((resolve, reject) => {
      const opts = {
        hostname: '127.0.0.1',
        port: port,
        path: options.path,
        method: options.method || 'GET',
        headers: options.headers || { 'Content-Type': 'application/json', 'Authorization': 'Bearer token123' },
      };
      const req = require('http').request(opts, res => {
        let body = '';
        res.setEncoding('utf8');
        res.on('data', chunk => (body += chunk));
        res.on('end', () => {
          try {
            const parsed = body ? JSON.parse(body) : {};
            resolve({ status: res.statusCode, body: parsed });
          } catch (e) {
            resolve({ status: res.statusCode, body: body });
          }
        });
      });
      req.on('error', reject);
      if (data) {
        req.write(JSON.stringify(data));
      }
      req.end();
    });
  }

  function requestNoAuth(options, data) {
    return new Promise((resolve, reject) => {
      const opts = {
        hostname: '127.0.0.1',
        port: port,
        path: options.path,
        method: options.method || 'GET',
        headers: { 'Content-Type': 'application/json' }, // no Authorization
      };
      const req = require('http').request(opts, res => {
        let body = '';
        res.setEncoding('utf8');
        res.on('data', chunk => (body += chunk));
        res.on('end', () => {
          try {
            const parsed = body ? JSON.parse(body) : {};
            resolve({ status: res.statusCode, body: parsed });
          } catch (e) {
            resolve({ status: res.statusCode, body: body });
          }
        });
      });
      req.on('error', reject);
      if (data) {
        req.write(JSON.stringify(data));
      }
      req.end();
    });
  }

  try {
    // 1) GET /api/users should be empty list but requires auth
    let res = await request({ path: '/api/users', method: 'GET' }, null);
    // Should be 200 with ok true and empty array initially
    assert.equal(res.status, 200);
    assert.strictEqual(res.body.ok, true);
    assert.ok(Array.isArray(res.body.users));

    // 401 unauthorized when no token
    res = await requestNoAuth({ path: '/api/users', method: 'GET' }, null);
    // Expect 401
    assert.equal(res.status, 401);

    // 2) POST /api/users with valid data
    res = await request({ path: '/api/users', method: 'POST' }, {
      username: 'alice',
      email: 'alice@example.com',
      password_hash: 'secret123',
    });
    assert.equal(res.status, 201);
    assert.equal(res.body.ok, true);
    assert.ok(res.body.user);
    assert.equal(res.body.user.username, 'alice');
    const aliceId = res.body.user.id;

    // 3) GET /api/users/:id
    res = await request({ path: `/api/users/${aliceId}`, method: 'GET' }, null);
    assert.equal(res.status, 200);
    assert.equal(res.body.ok, true);
    assert.equal(res.body.user.id, aliceId);
    // 404 for non-existent user
    res = await request({ path: '/api/users/999999', method: 'GET' }, null);
    assert.equal(res.status, 404);

    // 4) POST with invalid data
    res = await request({ path: '/api/users', method: 'POST' }, {
      username: 'bob',
      email: 'not-an-email',
      password_hash: 'pw',
    });
    assert.equal(res.status, 400);

    // 400 invalid pagination
    res = await request({ path: '/api/users?page=0', method: 'GET' }, null);
    assert.equal(res.status, 400);
    res = await request({ path: '/api/users?limit=0', method: 'GET' }, null);
    assert.equal(res.status, 400);

    // 404 on pagination page beyond data
    // For page=2 with default 20 limit, with only 1 user, should be 404
    res = await request({ path: '/api/users?page=2', method: 'GET' }, null);
    assert.equal(res.status, 404);

    // 409 on duplicate user
    res = await request({ path: '/api/users', method: 'POST' }, {
      username: 'alice',
      email: 'alice2@example.com',
      password_hash: 'another123',
    });
    assert.equal(res.status, 409);

  } finally {
    server.close();
    if (fs.existsSync(DB_PATH)) fs.unlinkSync(DB_PATH);
    console.log('User API tests completed.');
  }
})().catch(err => {
  console.error('User API tests failed:', err);
  process.exit(1);
});
