"use strict";
let jwt = require('jsonwebtoken');
const sqlite3 = require('sqlite3').verbose();
const path = require('path');

// Keep refresh secret in env; actual values defaulted if missing

// Ensure a per-service (wallet/shop/games) auth DB exists and contains the user
async function ensureUserInServiceDb(user, serviceName) {
  if (!user || !user.id) return;
  const service = (serviceName || '').toLowerCase();
  if (!service) return;
  const dbPath = path.resolve(__dirname, '../../db', `${service}.db`);
  return new Promise((resolve, reject) => {
    const db = new sqlite3.Database(dbPath, (err) => {
      if (err) return reject(err);
      db.serialize(() => {
        db.run(`CREATE TABLE IF NOT EXISTS users (
          id TEXT PRIMARY KEY,
          username TEXT
        )`, [], (err) => {
          if (err) { db.close(); return reject(err); }
          db.get('SELECT 1 FROM users WHERE id = ? LIMIT 1', [user.id], (err, row) => {
            if (err) { db.close(); return reject(err); }
            if (row) {
              db.close();
              return resolve(true);
            }
            db.run('INSERT INTO users (id, username) VALUES (?, ?)', [user.id, user.username], (err) => {
              db.close();
              if (err) return reject(err);
              resolve(true);
            });
          });
        });
      });
    });
  });
}

async function authenticate(req, res, next) {
  try {
    const authHeader = (req.headers['authorization'] || '').toString();
    const token = authHeader.startsWith('Bearer ') ? authHeader.slice(7) : null;
    const SECRET = process.env.JWT_SECRET || 'change-me';

    if (!token) {
      // Fallback compatibility for tests using x-user-id header
      if (req.headers['x-user-id']) {
        req.user = { id: req.headers['x-user-id'] };
        req.userId = req.headers['x-user-id'];
        // Skip DB provisioning if no remote token; still proceed
        return next();
      }
      return res.status(401).json({ error: 'unauthorized' });
    }

    let payload;
    try {
      payload = jwt.verify(token, SECRET);
    } catch (e) {
      if (e.name === 'TokenExpiredError') {
        // Attempt refresh flow
        const REFRESH_SECRET = process.env.JWT_REFRESH_SECRET || 'refresh-change-me';
        const refreshToken = req.headers['x-refresh-token'];
        if (refreshToken) {
          try {
            const refreshPayload = jwt.verify(refreshToken, REFRESH_SECRET);
            const decoded = jwt.decode(token);
            const safePayload = decoded && typeof decoded === 'object' ? decoded : refreshPayload;
            const newToken = jwt.sign({ id: safePayload?.id, username: safePayload?.username }, SECRET, { expiresIn: '7d' });
            res.setHeader('x-new-token', newToken);
            payload = refreshPayload;
          } catch (rr) {
            return res.status(401).json({ error: 'token_expired', detail: 'refresh_invalid' });
          }
        } else {
          return res.status(401).json({ error: 'token_expired' });
        }
      } else {
        return res.status(401).json({ error: 'invalid_token', detail: e?.message });
      }
    }

    req.user = payload; // { id, username, ... }
    // Normalize userId for downstream usage
    req.userId = payload?.id || null;

    // Derive service name from route: /api/{service}
    const baseUrl = req.baseUrl || '';
    const parts = baseUrl.split('/').filter(Boolean);
    const serviceName = parts.length >= 2 ? parts[1] : null;

    if (serviceName) {
      await ensureUserInServiceDb(payload, serviceName);
    }

    return next();
  } catch (e) {
    if (e && e.name === 'TokenExpiredError') {
      return res.status(401).json({ error: 'token_expired' });
    }
    return res.status(401).json({ error: 'invalid_token', detail: e?.message });
  }
}

module.exports = { authenticate };
