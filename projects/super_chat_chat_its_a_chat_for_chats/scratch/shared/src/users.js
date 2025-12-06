"use strict";

// User API skeleton using Express + SQLite
// Endpoints:
//  - GET /users
//  - POST /users
//  - GET /users/:id
// DB schema:
//   CREATE TABLE IF NOT EXISTS users (
//      id INTEGER PRIMARY KEY AUTOINCREMENT,
//      name TEXT NOT NULL,
//      email TEXT NOT NULL UNIQUE,
//      created_at DATETIME DEFAULT CURRENT_TIMESTAMP
//  );
// This module exports:
//  - initDb(dbPath) -> sqlite3.Database
//  - createUsersRouter(db) -> express.Router
//  - validateUser(payload) -> { valid, errors }
//  - seedDemoUsers(db) -> Promise
//
// Note: This is a production-ready skeleton that validates input and
// handles errors gracefully. The router is designed to be mounted by a
// main Express application.

const express = require('express');
const sqlite3 = require('sqlite3').verbose();
const path = require('path');
const fs = require('fs');

// Default DB path (relative to this file)
const DEFAULT_DB_PATH = path.resolve(__dirname, '../../db/users.db');

// Ensure DB directory exists for file-based DBs when using a relative path
function ensureDirExists(filePath) {
  const dir = path.dirname(filePath);
  if (!fs.existsSync(dir)) {
    fs.mkdirSync(dir, { recursive: true });
  }
}

// Initialize (or reopen) the SQLite DB and ensure the schema exists
function initDb(dbPath = DEFAULT_DB_PATH) {
  ensureDirExists(dbPath);
  const db = new sqlite3.Database(dbPath);

  // Create table if not exists
  db.serialize(() => {
    db.run(
      `CREATE TABLE IF NOT EXISTS users (
         id INTEGER PRIMARY KEY AUTOINCREMENT,
         name TEXT NOT NULL,
         email TEXT NOT NULL UNIQUE,
         created_at DATETIME DEFAULT CURRENT_TIMESTAMP
       )`,
      (err) => {
        if (err) {
          // In production, you might log this
          console.error('Error creating users table:', err);
        }
      }
    );
  });

  return db;
}

// Basic payload validation scaffolding
function validateUser(payload) {
  const errors = {};
  if (!payload || typeof payload !== 'object') {
    errors.payload = 'Request body must be a JSON object.';
  }
  const name = payload && payload.name;
  const email = payload && payload.email;

  if (!name || typeof name !== 'string' || name.trim().length === 0) {
    errors.name = 'Name is required.';
  }

  if (!email || typeof email !== 'string') {
    errors.email = 'Email is required.';
  } else {
    // Simple email regex for validation scaffolding
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(email)) {
      errors.email = 'Email must be valid.';
    }
  }

  const valid = Object.keys(errors).length === 0;
  return { valid, errors };
}

// Helper to fetch user by id
function getUserById(db, id) {
  return new Promise((resolve, reject) => {
    db.get('SELECT id, name, email, created_at FROM users WHERE id = ?', [id], (err, row) => {
      if (err) return reject(err);
      resolve(row || null);
    });
  });
}

// Helper to fetch all users
function getAllUsers(db) {
  return new Promise((resolve, reject) => {
    db.all('SELECT id, name, email, created_at FROM users ORDER BY id ASC', [], (err, rows) => {
      if (err) return reject(err);
      resolve(rows);
    });
  });
}

// Seed a couple of demo users (for quick testing)
function seedDemoUsers(db) {
  return new Promise((resolve, reject) => {
    const stmt = db.prepare('INSERT OR IGNORE INTO users (name, email) VALUES (?, ?)');
    db.serialize(() => {
      stmt.run(['Alice Example', 'alice@example.com']);
      stmt.run(['Bob Example', 'bob@example.com']);
      stmt.finalize((err) => {
        if (err) return reject(err);
        resolve();
      });
    });
  });
}

// Create the Express router that handles /users endpoints
function createUsersRouter(db) {
  const router = express.Router();

  // GET /users
  router.get('/users', async (req, res, next) => {
    try {
      const users = await getAllUsers(db);
      res.json(users);
    } catch (err) {
      next(err);
    }
  });

  // POST /users
  router.post('/users', async (req, res, next) => {
    try {
      const payload = req.body;
      const { valid, errors } = validateUser(payload);
      if (!valid) {
        return res.status(400).json({ errors });
      }

      // Insert user
      db.run(
        'INSERT INTO users (name, email) VALUES (?, ?)',
        [payload.name, payload.email],
        function (err) {
          if (err) {
            // Unique constraint on email
            if (err.code === 'SQLITE_CONSTRAINT' || /UNIQUE/.test(err.message)) {
              return res.status(409).json({ error: 'User with this email already exists.' });
            }
            return next(err);
          }
          const id = this.lastID;
          // Return created user representation
          res.status(201).json({ id, name: payload.name, email: payload.email, created_at: new Date().toISOString() });
        }
      );
    } catch (err) {
      next(err);
    }
  });

  // GET /users/:id
  router.get('/users/:id', async (req, res, next) => {
    try {
      const id = parseInt(req.params.id, 10);
      if (Number.isNaN(id)) {
        return res.status(400).json({ error: 'Invalid user id.' });
      }
      const user = await getUserById(db, id);
      if (!user) {
        return res.status(404).json({ error: 'User not found.' });
      }
      res.json(user);
    } catch (err) {
      next(err);
    }
  });

  // Simple error handler for this router
  router.use((err, req, res, next) => {
    console.error('Router error:', err);
    res.status(500).json({ error: 'Internal Server Error' });
  });

  return router;
}

// Exports
module.exports = {
  initDb,
  createUsersRouter,
  validateUser,
  seedDemoUsers,
};

// Documentation for API consumers (inline for discoverability)
// Users API Endpoints:
// - GET /users -> list all users
// - POST /users -> create a new user { name, email }
// - GET /users/:id -> fetch a user by id
