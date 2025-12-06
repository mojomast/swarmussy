#!/usr/bin/env node
/* Basic unit tests for the Auth service scaffolding
 * - spins up an isolated instance using createAuthApp
 * - tests /api/auth/register and /api/auth/login endpoints
 */

const assert = require('assert');
const path = require('path');
const http = require('http');

async function runTests() {
  // Import the auth module builder
  const { createAuthApp } = require('../../src/modules/auth/server.js');

  const dbPath = path.join(__dirname, 'test-auth.db');
  // Cleanup any previous leftover
  try {
    require('fs').unlinkSync(dbPath);
  } catch (e) {
    // ignore
  }

  const appBuilder = createAuthApp({ port: 0, dbPath: dbPath, jwtSecret: 'testsecret' });

  await appBuilder.initDB();
  const server = await appBuilder.startServer();
  const port = server.address().port;

  function post(endpoint, payload) {
    return new Promise((resolve, reject) => {
      const req = http.request({ hostname: '127.0.0.1', port, path: endpoint, method: 'POST', headers: { 'Content-Type': 'application/json' } }, (res) => {
        let data = '';
        res.on('data', (d) => (data += d));
        res.on('end', () => resolve({ statusCode: res.statusCode, body: data }));
      });
      req.on('error', reject);
      req.write(JSON.stringify(payload));
      req.end();
    });
  }

  // Register a user
  const reg = await post('/api/auth/register', {
    username: 'alice',
    email: 'alice@example.com',
    password: 'password123',
  });
  assert.strictEqual(reg.statusCode, 201, `Unexpected register status: ${reg.statusCode}`);
  const regBody = JSON.parse(reg.body);
  assert.ok(regBody.token, 'Register response should include token');

  // Login by username
  const login = await post('/api/auth/login', {
    username: 'alice',
    password: 'password123',
  });
  assert.strictEqual(login.statusCode, 200, `Unexpected login status: ${login.statusCode}`);
  const loginBody = JSON.parse(login.body);
  assert.ok(loginBody.token, 'Login response should include token');

  // Cleanup: shutdown server and DB file
  server.close(() => {
    try {
      require('fs').unlinkSync(dbPath);
    } catch (e) {
      // ignore
    }
  });
  console.log('Auth tests passed');
}

runTests().catch((err) => {
  console.error('Auth tests failed:', err);
  process.exit(1);
});
