const fetch = require('node-fetch');
const BASE = 'http://127.0.0.1:5001';

async function run() {
  // Bootstrap a profile
  await fetch(`${BASE}/profiles/bootstrap`, { method: 'POST' }).then(r => r.json());
  // Create a profile
  const res1 = await fetch(`${BASE}/profiles`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ id: 'u1', data: { name: 'Alice' } }) });
  console.log('create', res1.status);
  // Load profile
  const res2 = await fetch(`${BASE}/profiles/${'u1'}`);
  console.log('load', res2.status);
  // Delete profile
  const del = await fetch(`${BASE}/profiles/${'u1'}`, { method: 'DELETE' });
  console.log('del', del.status);
}

run();
