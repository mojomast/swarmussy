const API_BASE = '/levels';

async function apiGet(url) {
  const res = await fetch(url);
  if (!res.ok) throw new Error(`Request failed: ${res.status}`);
  return res.json();
}

async function apiPost(url, data){
  const res = await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data)
  });
  if (!res.ok) throw new Error(`Request failed: ${res.status}`);
  return res.json();
}

async function apiPut(url, data){
  const res = await fetch(url, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data)
  });
  if (!res.ok) throw new Error(`Request failed: ${res.status}`);
  return res.json();
}

async function apiDelete(url){
  const res = await fetch(url, { method: 'DELETE' });
  if (!res.ok) throw new Error(`Request failed: ${res.status}`);
  return res.json();
}

async function fetchLevels(){ return apiGet(API_BASE); }

async function createLevel(payload){ return apiPost(API_BASE, payload); }
async function updateLevel(id, payload){ return apiPut(`${API_BASE}/${id}`, payload); }
async function deleteLevel(id){ return apiDelete(`${API_BASE}/${id}`); }

window.__levels_api__ = { fetchLevels, createLevel, updateLevel, deleteLevel };
