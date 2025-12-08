import request from 'supertest';
import { createApp } from '../index';

describe('API Prototype - Express in-memory store', () => {
  it('GET /health returns ok', async () => {
    const app = createApp();
    const res = await request(app).get('/health');
    expect(res.status).toBe(200);
    expect(res.body?.ok).toBe(true);
  });

  it('POST /api/editor/assets creates asset and GET lists', async () => {
    const app = createApp();
    const agent = request(app);
    const payload = { name: 'test-entity', type: 'monster' };
    const post = await agent.post('/api/editor/assets').send(payload);
    expect(post.status).toBe(200);
    expect(post.body?.ok).toBe(true);
    const list = await agent.get('/api/editor/assets');
    expect(list.status).toBe(200);
    expect(Array.isArray(list.body?.data)).toBe(true);
  });

  it('POST /api/world/save and GET /api/world/load', async () => {
    const app = createApp();
    const agent = request(app);
    const w = {
      worldId: 'w1',
      editor: { editorId: 'e1', mode: 'edit', lastModified: new Date().toISOString() },
      plan: { planId: 'p1', name: 'P1', updatedAt: new Date().toISOString(), status: 'draft' },
      assets: [],
      levels: [],
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString()
    };
    const save = await agent.post('/api/world/save').send({ world: w });
    expect(save.status).toBe(200);
    const load = await agent.get('/api/world/load');
    expect(load.status).toBe(200);
    expect(load.body?.data?.worldId).toBe('w1');
  });
});
