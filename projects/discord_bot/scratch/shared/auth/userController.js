const bcrypt = require('bcrypt');
const jwt = require('jsonwebtoken');
const { initDb, run, get, all } = require('../db');

const JWT_SECRET = process.env.JWT_SECRET || 'change-me';
const TOKEN_EXPIRY = '7d';

async function register(req, res) {
  const { username, password } = req.body;
  if (!username || !password) return res.status(400).json({ error: 'username and password required' });
  const db = await initDb();
  const salt = await bcrypt.genSalt(10);
  const hash = await bcrypt.hash(password, salt);
  const id = require('uuid').v4();
  try {
    await run(db, 'INSERT INTO users (id, username, password_hash, created_at) VALUES (?, ?, ?, datetime("now"))', [id, username, hash]);
    await run(db, 'INSERT INTO wallets (user_id, balance) VALUES (?, ?)', [id, 0]);
    res.json({ id, username });
  } catch (e) {
    res.status(500).json({ error: 'register failed', detail: e.message });
  }
}

async function login(req, res) {
  const { username, password } = req.body;
  if (!username || !password) return res.status(400).json({ error: 'username and password required' });
  const db = await initDb();
  const user = await get(db, 'SELECT * FROM users WHERE username = ?', [username]);
  if (!user) return res.status(401).json({ error: 'invalid credentials' });
  const ok = await bcrypt.compare(password, user.password_hash);
  if (!ok) return res.status(401).json({ error: 'invalid credentials' });
  const token = jwt.sign({ id: user.id, username: user.username }, JWT_SECRET, { expiresIn: TOKEN_EXPIRY });
  res.json({ token, user: { id: user.id, username: user.username } });
}

async function refresh(req, res) {
  // Very lightweight refresh: accept an existing valid token and issue a new one
  try {
    const authHeader = (req.headers['authorization'] || '').toString();
    const token = authHeader.startsWith('Bearer ') ? authHeader.slice(7) : (req.body?.token || null);
    if (!token) return res.status(401).json({ error: 'unauthorized' });
    const payload = jwt.verify(token, JWT_SECRET);
    // Issue new token with same payload
    const newToken = jwt.sign({ id: payload.id, username: payload.username }, JWT_SECRET, { expiresIn: TOKEN_EXPIRY });
    res.json({ token: newToken });
  } catch (e) {
    return res.status(401).json({ error: 'invalid_token', detail: e?.message });
  }
}

module.exports = { register, login, refresh };
