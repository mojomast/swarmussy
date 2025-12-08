// Editor data persistence utilities (in-memory for testability in Node environments)

import { validateJson } from './validate.js';

// In-memory storage to support Node-based QA without browser APIs
const inMemoryStore = new Map();

export function saveLevel(level) {
  // Minimal schema reference placeholder; in real usage, load level.schema.json
  const schema = {};
  const res = validateJson(schema, level);
  if (!res.valid) {
    throw new Error('Validation failed: ' + res.errors.join('; '));
  }
  inMemoryStore.set('level:' + level.id, JSON.stringify(level));
  return true;
}

export function loadLevel(id) {
  const str = inMemoryStore.get('level:' + id);
  return str ? JSON.parse(str) : null;
}
