// Phase 2 API helpers for frontend phase 2 UI

export async function getLevel() {
  const res = await fetch('/v2/editor/level');
  if (!res.ok) throw new Error('Failed to load level');
  const data = await res.json();
  // Normalize to a Level object if endpoint returns { level: {...} }
  return data?.level ?? data;
}

export async function saveLevel(payload) {
  const res = await fetch('/v2/editor/level', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload)
  });
  if (!res.ok) throw new Error('Failed to save level');
  return res.json();
}

export async function getRenderStats() {
  const res = await fetch('/v2/engine/render_stats');
  if (!res.ok) throw new Error('Failed to load render stats');
  return res.json();
}

export async function subscribeEvents() {
  // Simple SSE hook for events stream if available
  const es = new EventSource('/v2/events/stream');
  return es;
}
