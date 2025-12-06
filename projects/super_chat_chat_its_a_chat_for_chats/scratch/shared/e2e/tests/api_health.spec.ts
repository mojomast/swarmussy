import { test, expect } from '@playwright/test';

test('API health: GET /api/users returns 200 and array', async ({ request }) => {
  const res = await request.get('/api/users');
  expect(res.status()).toBe(200);
  const json = await res.json();
  expect(Array.isArray(json)).toBe(true);
});
