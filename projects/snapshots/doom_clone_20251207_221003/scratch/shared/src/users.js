// scratch/shared/src/users.js
// User API module using Express + SQLite3
// Endpoints:
//  - GET /users
//  - POST /users
//  - GET /users/:id
//
// Features:
//  - Lightweight input validation
//  - Basic error handling with meaningful HTTP status codes
//  - SQLite-backed persistence (supports in-memory DB for tests)
//  - Exports a small API surface to be composed by the main app

const express = require('express');
const sqlite3 = require('sqlite3');
const { open } = require('sqlite'); // for convenience (promises on sqlite)
const crypto = require('crypto');

// Lightweight email regex (same spirit as Rust implementation)
const EMAIL_REGEX = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
const NAME_MIN_LEN = 1;

// In-memory wrapper helpers (promisified)
async function openDatabase(dbPath) {
  // sqlite's open() returns a Database with Promise API
  // we use sqlite3's Database behind the scenes via sqlite
  return open({ filename: dbPath, driver: sqlite3.Database });
}

// Public validation helper for tests and runtime usage
function validateNewUser(input) {
  const errors = [];
  const name = input?.name?.toString?.() ?? '';
  const email = input?.email ?? '';

  if (name.trim().length < NAME_MIN_LEN) {
    errors.push('name_required');
  }
  if (!EMAIL_REGEX.test(email)) {
    errors.push('email_invalid');
  }
  return errors;
}

// Initialize the DB with the users table if not exists
async function initDb(dbPath) {
  const db = await openDatabase(dbPath);
  await db.exec(`
    CREATE TABLE IF NOT EXISTS users (
      id TEXT PRIMARY KEY,
      name TEXT NOT NULL,
      email TEXT NOT NULL UNIQUE,
      created_at TEXT NOT NULL
    );
  `);
  return db;
}

// Helper to run queries with sqlite/promise interface
async function runQuery(db, sql, params = []) {
  return new Promise((resolve, reject) => {
    db.run(sql, params, function (err) {
      if (err) return reject(err);
      resolve(this);
    });
  });
}

async function getRow(db, sql, params = []) {
  return new Promise((resolve, reject) => {
    db.get(sql, params, (err, row) => {
      if (err) return reject(err);
      resolve(row);
    });
  });
}

async function getAll(db, sql, params = []) {
  return new Promise((resolve, reject) => {
    db.all(sql, params, (err, rows) => {
      if (err) return reject(err);
      resolve(rows);
    });
  });
}

// Create app with routes bound to a given SQLite DB instance
function createApp(db) {
  const app = express();
  app.use(express.json());

  // GET /users
  app.get('/users', async (req, res) => {
    try {
      const rows = await getAll(db, 'SELECT id, name, email, created_at FROM users ORDER BY created_at DESC');
      const users = rows.map((r) => ({ id: r.id, name: r.name, email: r.email, created_at: r.created_at }));
      res.status(200).json(users);
    } catch (err) {
      console.error('Error fetching users:', err);
      res.status(500).json({ error: 'internal_server_error' });
    }
  });

  // POST /users
  app.post('/users', async (req, res) => {
    try {
      const payload = req.body || {};
      const errors = validateNewUser(payload);
      if (errors.length > 0) {
        return res.status(400).json({ error: 'validation_failed', details: errors });
      }
      const id = crypto.randomUUID ? crypto.randomUUID() : require('crypto').randomBytes(16).toString('hex');
      const createdAt = new Date().toISOString();
      await runQuery(db, 'INSERT INTO users (id, name, email, created_at) VALUES (?, ?, ?, ?)', [id, payload.name, payload.email, createdAt]);
      const user = { id, name: payload.name, email: payload.email, created_at: createdAt };
      res.status(201).json(user);
    } catch (err) {
      // Unique constraint for email
      if (err && err.code === 'SQLITE_CONSTRAINT') {
        return res.status(409).json({ error: 'conflict', details: ['email_taken'] });
      }
      console.error('Error creating user:', err);
      res.status(500).json({ error: 'internal_server_error' });
    }
  });

  // GET /users/:id
  app.get('/users/:id', async (req, res) => {
    try {
      const id = req.params.id;
      const row = await getRow(db, 'SELECT id, name, email, created_at FROM users WHERE id = ?', [id]);
      if (!row) {
        return res.status(404).json({ error: 'not_found' });
      }
      res.status(200).json({ id: row.id, name: row.name, email: row.email, created_at: row.created_at });
    } catch (err) {
      console.error('Error fetching user by id:', err);
      res.status(500).json({ error: 'internal_server_error' });
    }
  });

  return app;
}

module.exports = {
  initDb,
  createApp,
  validateNewUser,
};
