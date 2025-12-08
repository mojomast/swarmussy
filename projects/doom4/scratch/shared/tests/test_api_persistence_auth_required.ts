import { startServer, stopServer } from '../server';

describe('API Persistence - Auth placeholder (required)', () => {
  let server: any;
  let port: number;

  beforeAll(async () => {
    // Enable required auth mode for this test suite
    process.env.AUTH_MODE = 'required';
    server = await startServer(0);
    port = server.address().port;
  });

  afterAll(async () => {
    await stopServer();
    delete process.env.AUTH_MODE;
  });

  async function api(path: string, opts?: any) {
    const url = `http://localhost:${port}${path}`;
    const res = await fetch(url, opts);
    const json = res.headers.get('content-type')?.includes('application/json') ? await res.json() : null;
    return { res, json };
  }

  it('denies access when Authorization header is missing', async () => {
    const { res } = await api('/api/editor/state');
    expect(res.status).toBe(401);
  });

  it('allows access when Authorization header is provided', async () => {
    const { res, json } = await api('/api/editor/state', {
      headers: { 'Authorization': 'Bearer test-token' }
    });
    expect(res.status).toBe(200);
    // basic sanity on payload shape
    expect(json).toBeDefined();
  });
});
