import http from 'http';

// In-memory storage of levels for QA purposes
let levels = [
  {
    id: 'lvl-01',
    name: 'Sample Level',
    dimensions: { width: 8, height: 8, depth: 1 },
    tiles: [],
    monsters: [],
    weapons: [],
    assets: [],
    spawn_points: [{ x: 0, y: 0, z: 0 }],
    version: '1.0.0'
  }
];
let portSecurity = 3002; // default port
let nextIdSeq = 2;

// Simple, in-process level payload validation against the Level schema shape
function validateLevelPayload(payload) {
  const errors = [];
  if (typeof payload !== 'object' || payload === null || Array.isArray(payload)) {
    errors.push('Payload should be an object');
    return { valid: false, errors };
  }

  // required top-level keys
  const required = ['id','name','dimensions','tiles','monsters','weapons','assets','spawn_points','version'];
  for (const k of required) {
    if (!(k in payload)) {
      errors.push(`Missing required property: ${k}`);
    }
  }
  // unknown top-level properties not allowed
  const allowed = new Set(required);
  for (const key of Object.keys(payload)) {
    if (!allowed.has(key)) {
      errors.push(`Unknown property: ${key}`);
    }
  }
  // dimensions
  const d = payload.dimensions;
  if (typeof d !== 'object' || d === null || Array.isArray(d)) {
    errors.push('dimensions should be an object');
  } else {
    const reqD = ['width','height','depth'];
    for (const k of reqD) if (!(k in d)) errors.push(`Missing required property: dimensions.${k}`);
    if (typeof d.width !== 'number') errors.push('dimensions.width should be number');
    if (typeof d.height !== 'number') errors.push('dimensions.height should be number');
    if (typeof d.depth !== 'number') errors.push('dimensions.depth should be number');
  }
  // arrays of strings
  const arrs = ['tiles','monsters','weapons','assets'];
  for (const a of arrs) {
    const v = payload[a];
    if (!Array.isArray(v)) errors.push(`${a} should be an array`);
    else for (const item of v) if (typeof item !== 'string') errors.push(`Each ${a} item should be string`);
  }
  // spawn_points
  const sp = payload.spawn_points;
  if (!Array.isArray(sp)) {
    errors.push('spawn_points should be an array');
  } else {
    sp.forEach((p, idx) => {
      if (typeof p !== 'object' || p === null) {
        errors.push(`spawn_points[${idx}] should be object`);
      } else {
        const r = ['x','y','z'];
        for (const k of r) if (typeof p[k] !== 'number') errors.push(`spawn_points[${idx}].${k} should be number`);
      }
    });
  }
  // version pattern
  const v = payload.version;
  if (typeof v !== 'string') {
    errors.push('version should be string');
  } else {
    const pat = /^\d+\.\d+\.\d+$/;
    if (!pat.test(v)) errors.push('version does not match pattern x.y.z');
  }

  return { valid: errors.length === 0, errors };
}

function isRateLimited(ip, state) {
  const now = Date.now();
  const WINDOW_MS = 60000; // 1 minute
  const LIMIT = 5; // 5 requests per window
  if (!state[ip]) state[ip] = [];
  const recents = state[ip].filter(ts => now - ts < WINDOW_MS);
  recents.push(now);
  state[ip] = recents;
  return state[ip].length > LIMIT;
}

export async function startServer(port = portSecurity) {
  const state = {};
  const server = http.createServer(async (req, res) => {
    const ip = (req.headers['x-forwarded-for'] || req.connection?.remoteAddress || '').toString();
    // Rate limiting
    if (isRateLimited(ip, state)) {
      res.writeHead(429, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({ error: 'rate_limited' }));
      return;
    }
    // Simple auth stub
    const auth = (req.headers['authorization'] || '');
    if (auth !== 'Bearer testtoken') {
      res.writeHead(401, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({ error: 'unauthorized' }));
      return;
    }
    // CORS friendly for tests (not required but convenient)
    if (req.method === 'OPTIONS') {
      res.writeHead(204);
      res.end();
      return;
    }

    const url = req.url || '/';
    const path = url.split('?')[0];

    // Routes
    if (req.method === 'GET' && path === '/levels') {
      res.writeHead(200, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify(levels));
      return;
    }

    if (req.method === 'GET' && path.startsWith('/levels/')) {
      const id = path.substring('/levels/'.length);
      // basic path traversal protection
      if (id.includes('..') || id.includes('/')) {
        res.writeHead(400, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ error: 'invalid_id' }));
        return;
      }
      const lv = levels.find(l => l.id === id);
      if (!lv) {
        res.writeHead(404, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ error: 'not_found' }));
        return;
      }
      res.writeHead(200, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify(lv));
      return;
    }

    if (req.method === 'POST' && path === '/levels') {
      let body = '';
      req.on('data', (chunk) => { body += chunk; });
      req.on('end', () => {
        let payload;
        try {
          payload = JSON.parse(body || '{}');
        } catch (e) {
          res.writeHead(400, { 'Content-Type': 'application/json' });
          res.end(JSON.stringify({ error: 'invalid_json' }));
          return;
        }
        const vres = validateLevelPayload(payload);
        if (!vres.valid) {
          res.writeHead(400, { 'Content-Type': 'application/json' });
          res.end(JSON.stringify({ errors: vres.errors }));
          return;
        }
        // ensure unique id
        if (levels.find(l => l.id === payload.id)) {
          res.writeHead(409, { 'Content-Type': 'application/json' });
          res.end(JSON.stringify({ error: 'duplicate_id' }));
          return;
        }
        levels.push(payload);
        res.writeHead(201, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify(payload));
      });
      return;
    }

    // PUT /levels/:id - update existing level
    if (req.method === 'PUT' && path.startsWith('/levels/')) {
      const id = path.substring('/levels/'.length);
      if (id.includes('..') || id.includes('/')) {
        res.writeHead(400, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ error: 'invalid_id' }));
        return;
      }
      const existingIndex = levels.findIndex(l => l.id === id);
      if (existingIndex === -1) {
        res.writeHead(404, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ error: 'not_found' }));
        return;
      }
      let body = '';
      req.on('data', (chunk) => { body += chunk; });
      req.on('end', () => {
        let payload;
        try {
          payload = JSON.parse(body || '{}');
        } catch (e) {
          res.writeHead(400, { 'Content-Type': 'application/json' });
          res.end(JSON.stringify({ error: 'invalid_json' }));
          return;
        }
        const vres = validateLevelPayload(payload);
        if (!vres.valid) {
          res.writeHead(400, { 'Content-Type': 'application/json' });
          res.end(JSON.stringify({ errors: vres.errors }));
          return;
        }
        // id must match path
        if (payload.id && payload.id !== id) {
          res.writeHead(400, { 'Content-Type': 'application/json' });
          res.end(JSON.stringify({ error: 'id_mismatch' }));
          return;
        }
        const existing = levels[existingIndex];
        const updated = { ...existing, ...payload, id };
        levels[existingIndex] = updated;
        res.writeHead(200, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify(updated));
      });
      return;
    }

    // Not found
    res.writeHead(404, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify({ error: 'not_found' }));
  });

  await new Promise((resolve) => server.listen(port, resolve));
  return {
    port,
    stop: () => new Promise((resolve) => server.close(() => resolve()))
  };
}

export default startServer;

        res.writeHead(404, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ error: 'not_found' }));
        return;
      }
      res.writeHead(200, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify(lv));
      return;
    }

    if (req.method === 'POST' && path === '/levels') {
      let body = '';
      req.on('data', (chunk) => { body += chunk; });
      req.on('end', () => {
        let payload;
        try {
          payload = JSON.parse(body || '{}');
        } catch (e) {
          res.writeHead(400, { 'Content-Type': 'application/json' });
          res.end(JSON.stringify({ error: 'invalid_json' }));
          return;
        }
        const vres = validateLevelPayload(payload);
        if (!vres.valid) {
          res.writeHead(400, { 'Content-Type': 'application/json' });
          res.end(JSON.stringify({ errors: vres.errors }));
          return;
        }
        // ensure unique id
        if (levels.find(l => l.id === payload.id)) {
          res.writeHead(409, { 'Content-Type': 'application/json' });
          res.end(JSON.stringify({ error: 'duplicate_id' }));
          return;
        }
        levels.push(payload);
        res.writeHead(201, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify(payload));
      });
      return;
    }

    // PUT /levels/:id - update existing level
    if (req.method === 'PUT' && path.startsWith('/levels/')) {
      const id = path.substring('/levels/'.length);
      if (id.includes('..') || id.includes('/')) {
        res.writeHead(400, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ error: 'invalid_id' }));
        return;
      }
      const existingIndex = levels.findIndex(l => l.id === id);
      if (existingIndex === -1) {
        res.writeHead(404, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ error: 'not_found' }));
        return;
      }
      let body = '';
      req.on('data', (chunk) => { body += chunk; });
      req.on('end', () => {
        let payload;
        try {
          payload = JSON.parse(body || '{}');
        } catch (e) {
          res.writeHead(400, { 'Content-Type': 'application/json' });
          res.end(JSON.stringify({ error: 'invalid_json' }));
          return;
        }
        const vres = validateLevelPayload(payload);
        if (!vres.valid) {
          res.writeHead(400, { 'Content-Type': 'application/json' });
          res.end(JSON.stringify({ errors: vres.errors }));
          return;
        }
        // id must match path
        if (payload.id && payload.id !== id) {
          res.writeHead(400, { 'Content-Type': 'application/json' });
          res.end(JSON.stringify({ error: 'id_mismatch' }));
          return;
        }
        const existing = levels[existingIndex];
        const updated = { ...existing, ...payload, id };
        levels[existingIndex] = updated;
        res.writeHead(200, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify(updated));
      });
      return;
    }

    // Not found
    res.writeHead(404, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify({ error: 'not_found' }));
  });

  await new Promise((resolve) => server.listen(port, resolve));
  return {
    port,
    stop: () => new Promise((resolve) => server.close(() => resolve()))
  };
}

export default startServer;
