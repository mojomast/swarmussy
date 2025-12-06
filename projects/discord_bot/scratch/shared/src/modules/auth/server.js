#!/usr/bin/env node
/** Auth Service - Express + SQLite + bcrypt + JWT
 * Exposes:
 *  - POST /api/auth/register
 *  - POST /api/auth/login
 *  - Exports createAuthApp(options) for testability and multi-instance usage
 *
 * Usage (production):
 *  const { createAuthApp } = require('./server.js');
 *  const appBuilder = createAuthApp({ port: 3001, dbPath: './auth.db', jwtSecret: 'secret' });
 *  appBuilder.initDB().then(() => appBuilder.startServer());
 *
 * Tests can import createAuthApp and spin up isolated instances.
 */

const path = require('path');
const express = require('express');
const bcrypt = require('bcrypt');
const sqlite3 = require('sqlite3').verbose();
const jwt = require('jsonwebtoken');

// Default configuration (used when running as a standalone process)
const DEFAULT_PORT = 3001;
const DEFAULT_DB_PATH = path.join(__dirname, 'auth.db');
const DEFAULT_JWT_SECRET = 'secret';
const DEFAULT_SALT_ROUNDS = 10;

function createAuthApp(options = {}) {
  // Options may include: port, dbPath, jwtSecret, saltRounds
  const PORT = typeof options.port === 'number' ? options.port : DEFAULT_PORT;
  const DB_PATH = options.dbPath || DEFAULT_DB_PATH;
  const JWT_SECRET = options.jwtSecret || DEFAULT_JWT_SECRET;
  const SALT_ROUNDS = typeof options.saltRounds === 'number' ? options.saltRounds : DEFAULT_SALT_ROUNDS;

  const app = express();
  app.use(express.json());

  let db;

  function initDB() {
    return new Promise((resolve, reject) => {
      db = new sqlite3.Database(DB_PATH, (err) => {
        if (err) return reject(err);
        const createStmt = `
          CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
          )
        `;
        db.run(createStmt, (err) => {
          if (err) return reject(err);
          resolve(db);
        });
      });
    });
  }

  function hashPassword(pwd) {
    return bcrypt.hash(pwd, SALT_ROUNDS);
  }

  function verifyPassword(hash, pwd) {
    return bcrypt.compare(pwd, hash);
  }

  function createToken(user) {
    const payload = { id: user.id, username: user.username };
    return jwt.sign(payload, JWT_SECRET, { expiresIn: '1h' });
  }

  // Registration
  app.post('/api/auth/register', async (req, res) => {
    const { username, email, password } = req.body || {};
    if (!username || !email || !password) {
      return res.status(400).json({ error: 'Missing required fields' });
    }
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(email)) {
      return res.status(400).json({ error: 'Invalid email' });
    }
    if (password.length < 6) {
      return res.status(400).json({ error: 'Password too short' });
    }
    try {
      const hash = await hashPassword(password);
      const stmt = 'INSERT INTO users (username, email, password_hash) VALUES (?, ?, ?)';
      db.run(stmt, [username, email, hash], function (err) {
        if (err) {
          if (err.code === 'SQLITE_CONSTRAINT') {
            // UNIQUE constraint failed
            return res.status(409).json({ error: 'User exists' });
          }
          return res.status(500).json({ error: 'DB error' });
        }
        const user = { id: this.lastID, username, email };
        const token = createToken(user);
        res.status(201).json({ id: user.id, username: user.username, token });
      });
    } catch (e) {
      return res.status(500).json({ error: 'Server error' });
    }
  });

  // Login
  app.post('/api/auth/login', (req, res) => {
    const { username, email, password } = req.body || {};
    const byUsername = !!username;
    const lookup = byUsername ? 'username' : 'email';
    const value = byUsername ? username : email;
    if (!value || !password) {
      return res.status(400).json({ error: 'Missing credentials' });
    }
    const query = byUsername
      ? `SELECT id, username, email, password_hash FROM users WHERE username = ?`
      : `SELECT id, username, email, password_hash FROM users WHERE email = ?`;
    db.get(query, [value], async (err, row) => {
      if (err) return res.status(500).json({ error: 'DB error' });
      if (!row) return res.status(401).json({ error: 'Invalid credentials' });
      try {
        const match = await verifyPassword(row.password_hash, password);
        if (!match) return res.status(401).json({ error: 'Invalid credentials' });
        const token = jwt.sign({ id: row.id, username: row.username }, JWT_SECRET, { expiresIn: '1h' });
        res.json({ token, id: row.id, username: row.username });
      } catch (e) {
        return res.status(500).json({ error: 'Server error' });
      }
    });
  });

  // Start server
  function startServer() {
    return new Promise((resolve, reject) => {
      const server = app.listen(PORT, () => resolve(server));
      server.on('error', reject);
    });
  }

  return { app, initDB, startServer, port: PORT, dbPath: DB_PATH };
}

// Integrate as a module: export the builder function
module.exports = { createAuthApp };

// If run directly, start a default server instance (production-friendly behavior)
if (require.main === module) {
  const { app, initDB, startServer } = createAuthApp({ port: process.env.PORT ? parseInt(process.env.PORT, 10) : DEFAULT_PORT, dbPath: process.env.DB_PATH || DEFAULT_DB_PATH, jwtSecret: process.env.JWT_SECRET || DEFAULT_JWT_SECRET });
  initDB()
    .then(() => {
      return startServer();
    })
    .then((server) => {
      // eslint-disable-next-line no-console
      console.log(`Auth service listening on port ${server.address().port}`);
    })
    .catch((err) => {
      // eslint-disable-next-line no-console
      console.error('Auth service failed to start:', err);
      process.exit(1);
    });
}
