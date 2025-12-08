// Simple REST API server in plain JavaScript for API contract tests
// Exposes endpoints used by the UI tests and by CI to verify health, version, and persistence contracts.

const express = require('express');
const bodyParser = require('body-parser');
const fs = require('fs');
const path = require('path');

// In-memory data store with optional disk persistence
const DATA_DIR = path.resolve(__dirname, 'data');
const WORLD_FILE = path.resolve(DATA_DIR, 'world.json');
let portCache = null;
let _server = null;
let appInstance = null;

function ensureDir(dir) {
  if (!fs.existsSync(dir)) {
    fs.mkdirSync(dir, { recursive: true });
  }
}

function nowISO() {
  return new Date().toISOString();
}

function uuid() {
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function (c) {
    const r = (Math.random() * 16) | 0;
    const v = c === 'x' ? r : (r & 0x3) | 0x8;
    return v.toString(16);
  });
}
}

// Shapes (documented in tests); keep JS dynamic
let store = {
  editor: {
    editorId: 'editor-default',
    mode: 'edit',
    lastModified: nowISO()
  },
  plan: {
    planId: 'plan-1',
    name: 'Initial Plan',
    status: 'draft',
    updatedAt: nowISO()
  },
  assets: [],
  levels: [],
  entities: [],
  createdAt: nowISO(),
  updatedAt: nowISO()
};

function loadFromDisk() {
  try {
    if (fs.existsSync(WORLD_FILE)) {
      const raw = fs.readFileSync(WORLD_FILE, 'utf-8');
      const parsed = JSON.parse(raw);
      if (parsed) store = parsed;
    }
  } catch (e) {
    // console.error('Failed to load world from disk', e);
  }
}

function saveToDisk() {
  try {
    ensureDir(DATA_DIR);
    fs.writeFileSync(WORLD_FILE, JSON.stringify(store, null, 2), 'utf-8');
  } catch (e) {
    // console.error('Failed to save world to disk', e);
  }
}

function asApiResponse(data) {
  return { ok: true, data };
}

function createApp() {
  const app = express();
  // Basic CORS for development
  app.use((req, res, next) => {
    res.header('Access-Control-Allow-Origin', '*');
    res.header('Access-Control-Allow-Methods', 'GET,POST,PUT,DELETE,OPTIONS');
    res.header('Access-Control-Allow-Headers', 'Content-Type, Authorization');
    if (req.method === 'OPTIONS') { res.sendStatus(200); return; }
    next();
  });
  app.use(bodyParser.json({ limit: '1mb' }));

  // Health
  app.get('/health', (_req, res) => res.status(200).json({ ok: true }));
  // Editor state: snapshot
  app.get('/api/editor/state', (_req, res) => {
    res.json({ editor: store.editor, plan: store.plan, assets: store.assets, levels: store.levels, entities: store.entities, world: store.world });
  });
  app.post('/api/editor/state', (req, res) => {
    const payload = req.body || {};
    if (payload.mode) store.editor.mode = payload.mode;
    if (payload.activePlanId !== undefined) store.plan.planId = payload.activePlanId;
    store.editor.lastModified = nowISO();
    store.updatedAt = nowISO();
    res.json(asApiResponse(store.editor));
  });

  // Plan
  app.post('/api/editor/plan', (req, res) => {
    const payload = req.body || {};
    if (payload.name !== undefined) store.plan.name = payload.name;
    if (payload.description !== undefined) store.plan.description = payload.description;
    if (payload.status !== undefined) store.plan.status = payload.status;
    store.plan.updatedAt = nowISO();
    store.updatedAt = nowISO();
    res.json(asApiResponse(store.plan));
  });
  app.get('/api/editor/plan', (_req, res) => res.json(asApiResponse(store.plan)));

  // Assets
  app.get('/api/editor/assets', (_req, res) => res.json(asApiResponse(store.assets)));
  app.post('/api/editor/assets', (req, res) => {
    const payload = req.body || {};
    if (payload.assetId) {
      const idx = store.assets.findIndex(a => a.assetId === payload.assetId);
      if (idx >= 0) {
        const a = store.assets[idx];
        if (payload.type !== undefined) a.type = payload.type;
        if (payload.name !== undefined) a.name = payload.name;
        if (payload.metadata !== undefined) a.metadata = payload.metadata;
        a.updatedAt = nowISO();
        store.updatedAt = nowISO();
        return res.json(asApiResponse(a));
      }
    }
    const newAsset = {
      assetId: payload.assetId || uuid(),
      type: payload.type || 'asset',
      name: payload.name || 'unnamed-asset',
      metadata: payload.metadata,
      updatedAt: nowISO()
    };
    store.assets.push(newAsset);
    store.updatedAt = nowISO();
    res.json(asApiResponse(newAsset));
  });

  // Levels
  app.get('/api/editor/levels', (_req, res) => res.json(asApiResponse(store.levels)));
  app.post('/api/editor/levels', (req, res) => {
    const payload = req.body || {};
    if (payload.levelId) {
      const idx = store.levels.findIndex(l => l.levelId === payload.levelId);
      if (idx >= 0) {
        const l = store.levels[idx];
        if (payload.name !== undefined) l.name = payload.name;
        if (payload.width !== undefined) l.width = payload.width;
        if (payload.height !== undefined) l.height = payload.height;
        l.updatedAt = nowISO();
        store.updatedAt = nowISO();
        return res.json(asApiResponse(l));
      }
    }
    const newLevel = {
      levelId: payload.levelId || uuid(),
      name: payload.name || 'untitled-level',
      width: payload.width ?? 64,
      height: payload.height ?? 64,
      updatedAt: nowISO()
    };
    store.levels.push(newLevel);
    store.updatedAt = nowISO();
    res.json(asApiResponse(newLevel));
  });

  // Entities
  app.get('/api/editor/entities', (_req, res) => res.json(asApiResponse(store.entities)));
  app.post('/api/editor/entities', (req, res) => {
    const payload = req.body || {};
    if (payload.id) {
      const idx = store.entities.findIndex(e => e.id === payload.id);
      if (idx >= 0) {
        const e = store.entities[idx];
        if (payload.type !== undefined) e.type = payload.type;
        if (payload.name !== undefined) e.name = payload.name;
        if (payload.levelId !== undefined) e.levelId = payload.levelId;
        if (payload.components !== undefined) e.components = payload.components;
        e.updatedAt = nowISO();
        store.updatedAt = nowISO();
        return res.json(asApiResponse(e));
      }
    }
    const newEntity = {
      id: payload.id || uuid(),
      type: payload.type || 'entity',
      name: payload.name,
      levelId: payload.levelId,
      components: payload.components,
      updatedAt: nowISO()
    };
    store.entities.push(newEntity);
    store.updatedAt = nowISO();
    res.json(asApiResponse(newEntity));
  });

  // World save/load
  app.post('/api/world/save', (req, res) => {
    const w = req.body?.world || req.body;
    if (w) {
      store.world = w;
      store.updatedAt = nowISO();
      saveToDisk();
      res.json(asApiResponse({ saved: true }));
    } else {
      res.status(400).json({ ok: false, error: 'No world payload' });
    }
  });
  app.get('/api/world/load', (_req, res) => {
    if (store.world) return res.json(asApiResponse(store.world));
    return res.status(404).json({ ok: false, error: 'No world saved' });
  });

  // Health/version
  app.get('/api/editor/health', (_req, res) => res.json({ ok: true, version: '0.1.0', timestamp: nowISO() }));
  app.get('/api/editor/version', (_req, res) => res.json({ version: '0.1.0', commit: 'dev' }));

  // Diagnostics
  app.get('/debug/store', (_req, res) => res.json(store));

  return app;
}

function ensureApp() {
  if (!appInstance) appInstance = createApp();
  return appInstance;
}

function startServer(port) {
  return new Promise((resolve) => {
    loadFromDisk();
    const app = ensureApp();
    const server = app.listen(port, function() {
      portCache = server.address().port;
      _server = server;
      resolve(server);
    });
  });
}

function stopServer() {
  return new Promise((resolve) => {
    if (!_server) return resolve();
    _server.close(() => { _server = null; resolve(); });
  });
}

module.exports = { startServer, stopServer, createApp, getPort: () => portCache };
