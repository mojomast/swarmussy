const express = require('express');
const bodyParser = require('body-parser');

function createServer() {
  const app = express();
  app.use(bodyParser.json());

  // In-memory store for demonstration; replace with DB in production
  const users = new Map();
  let nextId = 1;

  // Health check endpoint
  app.get('/healthz', (req, res) => {
    res.status(200).json({ status: 'ok', timestamp: new Date().toISOString() });
  });

  // GET /users - list summaries
  app.get('/users', (req, res) => {
    const summaries = Array.from(users.values()).map(u => ({ id: u.id, name: u.name, avatar: u.avatar }));
    res.json(summaries);
  });

  // POST /users - create
  app.post('/users', (req, res) => {
    const { name, avatar, level, health, score, inventory } = req.body || {};
    if (!name) {
      return res.status(400).json({ error: 'name is required' });
    }
    const id = String(nextId++);
    const user = { id, name, avatar, level, health, score, inventory, lastSaved: new Date().toISOString() };
    users.set(id, user);
    res.status(201).json(user);
  });

  // GET /users/:id - read
  app.get('/users/:id', (req, res) => {
    const user = users.get(req.params.id);
    if (!user) return res.status(404).json({ error: 'not found' });
    res.json(user);
  });

  // PUT /users/:id - update
  app.put('/users/:id', (req, res) => {
    const user = users.get(req.params.id);
    if (!user) return res.status(404).json({ error: 'not found' });
    const updates = req.body || {};
    Object.assign(user, updates, { lastSaved: new Date().toISOString() });
    users.set(user.id, user);
    res.json(user);
  });

  // DELETE /users/:id
  app.delete('/users/:id', (req, res) => {
    if (!users.has(req.params.id)) return res.status(404).json({ error: 'not found' });
    users.delete(req.params.id);
    res.status(204).end();
  });

  // Health check for server readiness
  app.get('/health', (req, res) => {
    res.status(200).json({ status: 'healthy' });
  });

  // Simple ping route for integration tests
  app.get('/ping', (req, res) => {
    res.json({ ok: true, ts: Date.now() });
  });

  return app;
}

module.exports = createServer;
