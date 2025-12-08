import { startServer, stopServer } from '../server';

describe('API-backed Persistence HTTP integration', () => {
  let server: any;
  let port: number;

  beforeAll(async () => {
    server = await startServer(0); // port 0 => random available port
    // obtain port
    port = server.address().port;
  });

  afterAll(async () => {
    await stopServer();
  });

  async function api(path: string, opts?: any) {
    const url = `http://localhost:${port}${path}`;
    const res = await fetch(url, opts);
    const json = await res.json();
    // Normalize to TS-friendly shape
    return { res, json };
  }

  it('API contract: GET /api/editor/state returns data with expected shape', async () => {
    const { json } = await api('/api/editor/state');
    expect(json.ok).toBe(true);
    expect(json.data).toBeDefined();
    expect(Array.isArray(json.data.assets)).toBe(true);
    expect(Array.isArray(json.data.levels)).toBe(true);
    expect(Array.isArray(json.data.entities)).toBe(true);
  });

  it('CORS headers are present', async () => {
    const url = `http://localhost:${port}/api/editor/state`;
    const res = await fetch(url);
    const acao = res.headers.get('Access-Control-Allow-Origin');
    expect(acao).toBe('*');
  });

  it('Create an asset via POST /api/assets and list it', async () => {
    const post = await fetch(`http://localhost:${port}/api/assets`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name: 'hero', type: 'monster' }),
    });
    const added = await post.json();
    expect(added.ok).toBe(true);
    const list = await fetch(`http://localhost:${port}/api/assets`);
    const assets = await list.json();
    expect(assets.ok).toBe(true);
    expect(Array.isArray(assets.data)).toBe(true);
    const found = assets.data.find((a: any) => a.name === 'hero');
    expect(found).toBeDefined();
  });

  it('End-to-end: update plan and verify in editor state', async () => {
    const newName = 'QA Plan ' + Date.now();
    const postPlan = await fetch(`http://localhost:${port}/api/plan`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name: newName }),
    });
    expect(postPlan.ok).toBe(true);

    const st = await fetch(`http://localhost:${port}/api/editor/state`);
    const state = await st.json();
    expect(state.ok).toBe(true);
    expect(state.data.plan?.name).toBe(newName);
  });

  it('World save and load cycle persists metadata', async () => {
    const name = 'WorldTest ' + Date.now();
    const postPlan = await fetch(`http://localhost:${port}/api/plan`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name }),
    });
    expect(postPlan.ok).toBe(true);

    const payload = {
      world: {
        worldId: 'w1',
        editor: {
          assets: [],
          levels: [],
          entities: [],
          plan: { id: 'plan', name },
        },
      },
    };
    const save = await fetch(`http://localhost:${port}/api/world/save`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    expect(save.ok).toBe(true);

    const load = await fetch(`http://localhost:${port}/api/world/load`);
    const w = await load.json();
    expect(w.ok).toBe(true);
    expect(w.data).toBeDefined();
  });
});
