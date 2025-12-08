// Simple unit tests for the frontend API client (mocked fetch)

(async function(){
  // ensure a clean global window mock
  global.window = global.window || {};
  const last = {};

  // Mock fetch for GET test
  global.window.fetch = async (url, opts) => {
    last.call = { url, opts };
    return {
      ok: true,
      json: async () => ({ planId: 'plan-123', name: 'Test Plan' })
    };
  };

  // Load ApiClient from module
  // For TS compile environment, use require on compiled JS path
  const ApiClientModule = require('../script/api-client.js');
  const ApiClient = global.window.ApiClient;
  const api = new ApiClient('/api');
  const plan = await api.getPlan();
  if (plan && plan.planId === 'plan-123') {
    console.log('api-client GET plan: PASS');
  } else {
    console.error('api-client GET plan: FAIL', plan);
  }
  if (last.call && last.call.url === '/api/editor/plan' && last.call.opts && last.call.opts.method === 'GET') {
    console.log('api-client GET endpoint: PASS');
  } else {
    console.error('api-client GET endpoint: FAIL', last.call);
  }

  // Mock fetch for POST test
  global.window.fetch = async (url, opts) => {
    last.call = { url, opts };
    if (opts && opts.method === 'POST') {
      // verify body
      const body = JSON.parse(opts.body);
      if (body && body.name === 'New Plan') {
        return { ok: true, json: async () => ({ status: 'saved' }) };
      }
    }
    return { ok: false };
  };

  // use api to save
  const postRes = await api.savePlan({ name: 'New Plan' });
  if (postRes && postRes.status === 'saved') {
    console.log('api-client POST savePlan: PASS');
  } else {
    console.error('api-client POST savePlan: FAIL', postRes);
  }
  if (last.call && last.call.url === '/api/editor/plan' && last.call.opts && last.call.opts.method === 'POST') {
    console.log('api-client POST endpoint: PASS');
  } else {
    console.error('api-client POST endpoint: FAIL', last.call);
  }
})();
