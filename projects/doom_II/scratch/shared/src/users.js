import express, { Request, Response } from 'express';
import crypto from 'crypto';
import { validateJson } from './validate.js';

// SQLite usage with graceful fallback to in-memory if sqlite3 is unavailable at runtime.
let useSQLite = false;
let db: any = null;
let initialized = false;
let memoryStore = [];
let memNextId = 1;
let sqliteInitAttempted = false;

async function initDbIfPossible() {
  if (initialized) return;
  if (sqliteInitAttempted) {
    return;
  }
  sqliteInitAttempted = true;
  try {
    const sqlite3Module = await import('sqlite3');
    const sqlite3 = sqlite3Module.default || sqlite3Module;
    if (!sqlite3) throw new Error('sqlite3 module not found');
    if (typeof sqlite3.verbose === 'function') {
      // @ts-ignore
      sqlite3 = sqlite3.verbose();
    }
    // @ts-ignore
    db = new sqlite3.Database('./scratch/shared/users.db', (err) => {
      if (err) {
        console.error('Failed to open sqlite database, falling back to memory. Error:', err);
      }
    });
    const createTbl = `
      CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        salt TEXT NOT NULL,
        created_at TEXT NOT NULL
      )`;
    await new Promise((resolve, reject) => {
      db.run(createTbl, (err: any) => (err ? reject(err) : resolve(null)));
    });
    useSQLite = true;
    initialized = true;
  } catch (e) {
    // fall back to memory path
    console.warn('SQLite unavailable, using in-memory user store.');
    useSQLite = false;
    memoryStore = [];
    memNextId = 1;
    initialized = true;
  }
}

function generateId() {
  // not used with sqlite; for memory mode, produce incremental-like ids
  if (useSQLite) return undefined;
  return 'usr_' + memNextId++;
}

const userSchema = {
  type: 'object',
  required: ['username','email','password'],
  properties: {
    id: { type: 'string' },
    username: { type: 'string' },
    email: { type: 'string' },
    password: { type: 'string' }
  },
  additionalProperties: false
};

function hashPassword(password, salt) {
  const h = crypto.createHash('sha256');
  h.update(password + salt);
  return h.digest('hex');
}

async function ensureInit() {
  if (initialized) return;
  await initDbIfPossible();
}

export function createUsersRouter() {
  const router = express.Router();
  // Require Authorization header for all user endpoints (best-effort in tests)
  router.use((req: Request, res: Response, next: Function) => {
    const auth = req.headers['authorization'];
    if (!auth || typeof auth !== 'string' || !auth.startsWith('Bearer ')) {
      return res.status(401).json({ error: 'Unauthorized' });
    }
    next();
  });

  // POST /users
  router.post('/users', async (req: Request, res: Response) => {
    try {
      await ensureInit();
      const data = req.body as any;
      const validation = validateJson(userSchema, data);
      if (!validation.valid) {
        return res.status(400).json({ errors: validation.errors });
      }
      const username = data.username;
      const email = data.email;
      const password = data.password;

      if (useSQLite) {
        // check duplicates
        const existing = await new Promise((resolve) => {
          db.get('SELECT id FROM users WHERE username = ? OR email = ?', [username, email], (err: any, row: any) => {
            resolve(row);
          });
        });
        if (existing) {
          return res.status(409).json({ error: 'user_exists' });
        }
        const salt = crypto.randomBytes(16).toString('hex');
        const created_at = new Date().toISOString();
        const hash = hashPassword(password, salt);
        const info = await new Promise((resolve, reject) => {
          db.run('INSERT INTO users (username, email, password_hash, salt, created_at) VALUES (?, ?, ?, ?, ?)', [username, email, hash, salt, created_at], function (err: any) {
            if (err) return reject(err);
            resolve({ id: this.lastID, username, email, created_at });
          });
        });
        return res.status(201).json({ id: info.id, username: info.username, email: info.email, created_at: info.created_at });
      } else {
        // memory mode
        await ensureInit();
        // check duplicates
        const exists = memoryStore.find((u) => u.username === username || u.email === email);
        if (exists) {
          return res.status(409).json({ error: 'user_exists' });
        }
        const id = generateId();
        const created_at = new Date().toISOString();
        const salt = crypto.randomBytes(16).toString('hex');
        const passwordHash = hashPassword(password, salt);
        const user = { id, username, email, passwordHash, salt, created_at };
        memoryStore.push(user);
        return res.status(201).json({ id, username, email, created_at });
      }
    } catch (err) {
      return res.status(500).json({ error: 'internal_server_error' });
    }
  });

  // GET /users
  router.get('/users', async (_req: Request, res: Response) => {
    try {
      await ensureInit();
      if (useSQLite) {
        const rows = await new Promise((resolve, reject) => {
          db.all('SELECT id, username, email, created_at FROM users', [], (err: any, rows: any[]) => {
            if (err) return reject(err);
            resolve(rows);
          });
        });
        return res.json(rows.map((r) => ({ id: r.id, username: r.username, email: r.email, created_at: r.created_at })));
      } else {
        return res.json(memoryStore.map((u) => ({ id: u.id, username: u.username, email: u.email, created_at: u.created_at })));
      }
    } catch {
      return res.status(500).json({ error: 'internal_server_error' });
    }
  });

  // GET /users/:id
  router.get('/users/:id', async (req: Request, res: Response) => {
    try {
      await ensureInit();
      const idParam = req.params.id;
      const idNum = parseInt(idParam, 10);
      if (Number.isNaN(idNum) && typeof idParam !== 'string') {
        // fallback to string match
      }
      if (useSQLite) {
        const user = await new Promise((resolve) => {
          db.get('SELECT id, username, email, created_at FROM users WHERE id = ?', [idParam], (err: any, row: any) => {
            resolve(row);
          });
        });
        if (!user) return res.status(404).json({ error: 'user_not_found' });
        return res.json(user);
      } else {
        const u = memoryStore.find((x) => x.id === idParam || x.id === String(idNum));
        if (!u) return res.status(404).json({ error: 'user_not_found' });
        return res.json({ id: u.id, username: u.username, email: u.email, created_at: u.created_at });
      }
    } catch {
      return res.status(500).json({ error: 'internal_server_error' });
    }
  });

  return router;
}

export function resetUsersStore() {
  memoryStore = [];
  memNextId = 1;
  // Do not reset sqlite DB to avoid destructive tests in environments that rely on it
}

export default createUsersRouter();
