// Phase 1 validation end-to-end tests using a tiny HTTP server
const http = require('http');
const assert = require('assert');

function startServer() {
  const server = http.createServer((req, res) => {
    const url = req.url;
    if (req.method === 'GET' && url === '/v1/engine/render') {
      const payload = { width: 1280, height: 720, data: [0, 1, 2, 3, 4, 5] };
      res.writeHead(200, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify(payload));
    } else if (req.method === 'GET' && url === '/v1/editor/level') {
      const payload = {
        level_id: 'level_01',
        name: 'Intro Level',
        version: 'v1.0',
        content: { entities: [], assets: [] }
      };
      res.writeHead(200, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify(payload));
    } else if (req.method === 'GET' && url === '/v1/events/stream') {
      res.writeHead(200, {
        'Content-Type': 'text/event-stream'
      });
      res.write("data: {\"event_type\":\"frame_rendered\"}\n\n");
      res.end();
    } else if (req.method === 'POST' && url === '/v1/editor/level') {
      let body = '';
      req.on('data', chunk => { body += chunk; });
      req.on('end', () => {
        try {
          const payload = JSON.parse(body || '{}');
          const required = new Set(['level_id','name','version','content']);
          const ok = [...required].every(k => Object.prototype.hasOwnProperty.call(payload, k));
          if (ok) {
            res.writeHead(200, { 'Content-Type': 'application/json' });
            res.end(JSON.stringify({ success: true, level_id: payload.level_id }));
          } else {
            res.writeHead(400, { 'Content-Type': 'application/json' });
            res.end(JSON.stringify({ error: 'Missing required fields' }));
          }
        } catch (e) {
          res.writeHead(400, { 'Content-Type': 'application/json' });
          res.end(JSON.stringify({ error: 'Invalid JSON' }));
        }
      });
    } else {
      res.writeHead(404, { 'Content-Type': 'text/plain' });
      res.end('Not Found');
    }
  });

  return new Promise((resolve, reject) => {
    server.listen(0, '127.0.0.1', () => {
      const port = server.address().port;
      resolve({ server, port });
    });
    server.on('error', (e) => reject(e));
  });
}

function httpGet(host, port, path) {
  const options = {
    hostname: host,
    port: port,
    path: path,
    method: 'GET'
  };
  return new Promise((resolve, reject) => {
    const req = http.request(options, (res) => {
      let data = '';
      res.setEncoding('utf8');
      res.on('data', chunk => data += chunk);
      res.on('end', () => {
        resolve({ status: res.statusCode, body: data, headers: res.headers });
      });
    });
    req.on('error', reject);
    req.end();
  });
}

function httpPost(host, port, path, payload) {
  const data = JSON.stringify(payload);
  const options = {
    hostname: host,
    port: port,
    path: path,
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Content-Length': Buffer.byteLength(data)
    }
  };
  return new Promise((resolve, reject) => {
    const req = http.request(options, (res) => {
      let body = '';
      res.setEncoding('utf8');
      res.on('data', chunk => body += chunk);
      res.on('end', () => resolve({ status: res.statusCode, body }));
    });
    req.on('error', reject);
    req.write(data);
    req.end();
  });
}

(async () => {
  const { server, port } = await startServer();
  const host = '127.0.0.1';
  try {
    // 1) GET engine/render
    let res = await httpGet(host, port, '/v1/engine/render');
    if (res.status !== 200) throw new Error('engine/render status ' + res.status);
    const p1 = JSON.parse(res.body);
    if (p1.width !== 1280 || p1.height !== 720 || !Array.isArray(p1.data)) throw new Error('invalid render payload');

    // 2) GET editor/level
    res = await httpGet(host, port, '/v1/editor/level');
    if (res.status !== 200) throw new Error('editor/level status ' + res.status);
    const level = JSON.parse(res.body);
    if (level.level_id !== 'level_01' || level.name !== 'Intro Level') throw new Error('invalid level payload');

    // 3) POST editor/level with valid payload
    const payload = {
      level_id: 'level_01',
      name: 'Intro Level',
      version: 'v1.0',
      content: { entities: [], assets: [] }
    };
    res = await httpPost(host, port, '/v1/editor/level', payload);
    if (res.status !== 200) throw new Error('post editor/level status ' + res.status);
    const postRes = JSON.parse(res.body);
    if (!postRes.success) throw new Error('post editor/level not success');

    // 4) POST with missing fields
    const badPayload = { level_id: 'level_01' };
    res = await httpPost(host, port, '/v1/editor/level', badPayload);
    if (res.status !== 400) throw new Error('expected 400 for bad payload, got ' + res.status);

    // 5) GET events/stream
    res = await httpGet(host, port, '/v1/events/stream');
    if (res.status !== 200) throw new Error('events/stream status ' + res.status);
    if (!res.headers['content-type'] || !res.headers['content-type'].includes('text/event-stream')) throw new Error('invalid SSE content-type');
    if (!res.body.includes('data:')) throw new Error('invalid SSE body');

    console.log('phase1_validation: PASSED');
  } catch (e) {
    console.error('phase1_validation: FAILED', e.message);
    process.exit(1);
  } finally {
    server.close();
  }
})();
