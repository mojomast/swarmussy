#!/usr/bin/env node
/**
 * Node.js integration tests for the User API (GET /users, POST /users, GET /users/:id)
 * - Spins up an in-memory SQLite-backed app via the shared Node module: scratch/shared/src/users.js
 * - Uses a minimal HTTP client (Node's http module) to exercise endpoints
 * - Validates happy-path flows and basic SQL-injection-safe behavior
 * - Leaves the running server running until tests complete
 */

const http = require('http');
const assert = require('assert');
const { initDb, createApp } = require('../src/users.js');

function jsonReq(options, body) {
  return new Promise((resolve, reject) => {
    const req = http.request(options, (res) => {
      let data = '';
      res.on('data', (chunk) => (data += chunk));
      res.on('end', () => resolve({ statusCode: res.statusCode, body: data }));
    });
    req.on('error', (e) => reject(e));
    if (body) {
      req.write(JSON.stringify(body));
    }
    req.end();
  });
}

async function runTests() {
  // 1) Init in-memory DB and app
  const db = await initDb(':memory:');
  const app = createApp(db);
  const server = app.listen(0, async () => {
    const port = server.address().port;
    const base = `http://127.0.0.1:${port}`;

    // Helper to perform GET/POST with JSON
    async function get(path) {
      return jsonReq({ hostname: '127.0.0.1', port, path, method: 'GET' }, null);
    }
    async function post(path, payload) {
      return jsonReq({ hostname: '127.0.0.1', port, path, method: 'POST', headers: { 'Content-Type': 'application/json' } }, payload);
    }

    try {
      // 2) GET /users -> expect 200 and empty array
      let res = await get('/users');
      assert.strictEqual(res.statusCode, 200, 'GET /users should return 200');
      const list = JSON.parse(res.body);
      assert(Array.isArray(list), 'GET /users should return an array');

      // 3) POST /users with valid payload
      const payload1 = { name: 'Alice', email: 'alice@example.com' };
      res = await post('/users', payload1);
      assert.strictEqual(res.statusCode, 201, 'POST /users should return 201');
      const created = JSON.parse(res.body);
      assert.ok(created.id, 'Created user should have id');
      assert.strictEqual(created.name, payload1.name);
      assert.strictEqual(created.email, payload1.email);
      const createdId = created.id;

      // 4) GET /users/:id should return created user
      res = await jsonReq({ hostname: '127.0.0.1', port, path: `/users/${createdId}`, method: 'GET' }, null);
      assert.strictEqual(res.statusCode, 200, 'GET /users/:id should return 200');
      const fetched = JSON.parse(res.body);
      assert.strictEqual(fetched.id, createdId);

      // 5) SQL injection-style payload should be treated as data, not executed
      const injPayload = { name: "Eve'; DROP TABLE users;--", email: 'eve@example.com' };
      res = await post('/users', injPayload);
      assert.strictEqual(res.statusCode, 201, 'POST /users with injection-like string should still 201');
      const injCreated = JSON.parse(res.body);
      assert.ok(injCreated.id);

      // 6) Final list should include at least two users
      res = await get('/users');
      assert.strictEqual(res.statusCode, 200);
      const finalList = JSON.parse(res.body);
      assert.ok(finalList.length >= 2, 'Expected at least 2 users in list');

      // Edge Case Tests
      // 7) Missing name should fail with 400 and name_required in details
      res = await post('/users', { email: 'missingname@example.com' });
      assert.strictEqual(res.statusCode, 400, 'POST /users with missing name should return 400');
      const missingName = JSON.parse(res.body);
      assert.strictEqual(missingName.error, 'validation_failed');
      assert.ok(Array.isArray(missingName.details) && missingName.details.includes('name_required'));

      // 8) Missing email should fail with 400 and email_invalid in details
      res = await post('/users', { name: 'NoEmail' });
      assert.strictEqual(res.statusCode, 400, 'POST /users with missing email should return 400');
      const missingEmail = JSON.parse(res.body);
      assert.strictEqual(missingEmail.error, 'validation_failed');
      assert.ok(Array.isArray(missingEmail.details) && missingEmail.details.includes('email_invalid'));

      // 9) Invalid email should fail with 400
      res = await post('/users', { name: 'Invalid', email: 'not-an-email' });
      assert.strictEqual(res.statusCode, 400, 'POST /users with invalid email should return 400');
      const invalidEmail = JSON.parse(res.body);
      assert.strictEqual(invalidEmail.error, 'validation_failed');

      // 10) GET non-existent user -> 404
      res = await jsonReq({ hostname: '127.0.0.1', port, path: `/users/nonexistent-id-123`, method: 'GET' }, null);
      assert.strictEqual(res.statusCode, 404, 'GET /users/:id with non-existent id should return 404');

      // 11) Duplicate email -> 409
      res = await post('/users', { name: 'Alice Clone', email: 'alice@example.com' });
      assert.strictEqual(res.statusCode, 409, 'POST /users with duplicate email should return 409');
      const dup = JSON.parse(res.body);
      assert.strictEqual(dup.error, 'conflict');
      assert.ok(Array.isArray(dup.details) && dup.details.includes('email_taken'));

      // 12) Very long name should be accepted (no enforcement in Node path)
      const longName = 'A'.repeat(300);
      res = await post('/users', { name: longName, email: 'longname@example.com' });
      assert.strictEqual(res.statusCode, 201, 'POST /users with long name should return 201');
      const longUser = JSON.parse(res.body);
      assert.ok(longUser.id);

      // 13) Empty body -> 400
      res = await post('/users', {});
      assert.strictEqual(res.statusCode, 400, 'POST /users with empty body should return 400');

      console.log('user_api_integration_tests: PASS');
      server.close();
      process.exit(0);
    } catch (e) {
      console.error('user_api_integration_tests: FAIL', e && e.message ? e.message : e);
      server.close();
      process.exit(1);
    }
  });
}

runTests();
