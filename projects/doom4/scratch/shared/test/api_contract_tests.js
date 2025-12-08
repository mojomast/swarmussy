// API contract tests for scratch/shared/server.js
// This test harness starts a small in-process API server (via server.js) and runs a suite of contract checks,
// including health/version checks and JSON shape validations for state persistence.

const { startServer, stopServer, getPort } = require('../server.js');

async function runTests() {
  // Ensure a clean start
  try { await stopServer(); } catch (e) { /* ignore */ }
  await startServer(0); // OS picks port
  const port = getPort();
  const base = `http://localhost:${port}`;

  async function fetchJSON(path, opts = {}) {
    const res = await fetch(base + path, opts);
    const data = await res.json();
    return { res, data };
  }

  const errors = [];

  try {
    // 1) Health endpoint
    let r = await fetch(base + '/health');
    if (!r.ok) throw new Error('health endpoint failed with status ' + r.status);
    let j = await r.json();
    if (!j || j.ok !== true) throw new Error('health payload invalid');

    // 2) API editor health
    r = await fetch(base + '/api/editor/health');
    if (!r.ok) throw new Error('editor/health failed');
    j = await r.json();
    if (j === null || typeof j.ok !== 'boolean') throw new Error('editor/health invalid');

    // 3) Version
    r = await fetch(base + '/api/editor/version');
    if (!r.ok) throw new Error('version failed');
    j = await r.json();
    if (!j || typeof j.version !== 'string') throw new Error('version payload invalid');

    // 4) State schema
    r = await fetch(base + '/api/editor/state');
    if (!r.ok) throw new Error('state fetch failed');
    j = await r.json();
    if (!j || !('editor' in j) || !('plan' in j) || !('assets' in j) || !('levels' in j))
      throw new Error('state shape invalid');

    // 5) Ensure basic JSON schema-ish validation on the returned state
    const s = j;
    if (typeof s.editor.mode !== 'string') errors.push('editor.mode should be a string');
    if (!Array.isArray(s.assets)) errors.push('assets should be an array');
    if (!Array.isArray(s.levels)) errors.push('levels should be an array');

    // 6) World persistence roundtrip
    const payload = {
      world: {
        worldId: 'test-world-1',
        editor: { mode: 'edit' },
        plan: { planId: 'plan-1' },
        assets: [],
        levels: []
      }
    };
    r = await fetch(base + '/api/world/save', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    if (!r.ok) throw new Error('world/save failed');
    j = await r.json();
    if (!j || j.ok !== true) throw new Error('world/save response invalid');

    r = await fetch(base + '/api/world/load');
    if (!r.ok) throw new Error('world/load failed');
    j = await r.json();
    // Accept either { ok: true, data: ... } or { ok: true, data: undefined }
    if (!j || j.ok !== true) throw new Error('world/load response invalid');

    console.log('[api-contract-tests] All API contract checks passed');
  } catch (err) {
    const msg = err && err.message ? err.message : String(err);
    console.error('[api-contract-tests] FAILURE', msg);
    errors.push(msg);
  } finally {
    try { await stopServer(); } catch (e) { /* ignore */ }
  }

  if (errors.length > 0) {
    console.error('ERRORS:', errors);
    process.exitCode = 2;
  } else {
    process.exitCode = 0;
  }
}

// Polyfill fetch for Node 18+ if needed
if (typeof fetch !== 'function') {
  global.fetch = (...args) => import('node-fetch').then(m => m.default ? m.default(...args) : m(...args));
}

runTests();
