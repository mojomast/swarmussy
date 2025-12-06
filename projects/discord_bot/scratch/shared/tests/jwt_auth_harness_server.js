"use strict";
const jwt = require('jsonwebtoken');
const express = require('express');
const app = express();
app.use(express.json());

const SECRET = process.env.JWT_SECRET || 'change-me';

app.post('/login', (req, res) => {
  const { username } = req.body;
  if (!username) return res.status(400).json({ error: 'username_required' });
  const token = jwt.sign({ username }, SECRET, { expiresIn: '60s' });
  res.json({ token });
});

app.get('/protected', (req, res) => {
  const auth = req.headers['authorization'];
  if (!auth || !auth.startsWith('Bearer ')) return res.status(401).json({ error: 'unauthorized' });
  const token = auth.slice(7);
  try {
    const payload = jwt.verify(token, SECRET);
    res.json({ ok: true, user: payload.username });
  } catch (e) {
    res.status(401).json({ error: 'invalid_token' });
  }
});

const server = app.listen(0, () => {
  const port = server.address().port;
  console.log(`JWT harness running on port ${port}`);
});

module.exports = server;
