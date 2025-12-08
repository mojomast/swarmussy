import express from 'express';

// Production-grade in-memory Level API (JS version for tests that import levels.js)
// Data model: Level { id, name, difficulty: 'easy'|'normal'|'hard', map: string[], monsters: string[], assets: string[] }

/**
 * Difficulty can be 'easy' | 'normal' | 'hard'
 */
const levelsStore = new Map();
export const __levelsStore = levelsStore; // for test inspection if needed

function generateId() {
  if (typeof crypto !== 'undefined' && crypto.randomUUID) {
    return crypto.randomUUID();
  }
  const rand = Math.random().toString(36).slice(2, 8);
  return 'lvl_' + Date.now().toString(36) + '_' + rand;
}

function isDifficulty(v) {
  return v === 'easy' || v === 'normal' || v === 'hard';
}

function asStringArray(v) {
  if (!Array.isArray(v)) return [];
  // filter non-strings
  return v.filter((x) => typeof x === 'string');
}

function validateLevelPayload(input) {
  const errors = [];
  if (!input || typeof input !== 'object') {
    errors.push('Invalid payload');
    return { valid: false, errors };
  }
  const { name, difficulty, map, monsters, assets } = input;

  if (typeof name !== 'string' || name.trim().length === 0) {
    errors.push('name is required and must be a non-empty string');
  }
  if (!isDifficulty(difficulty)) {
    errors.push('difficulty must be one of easy, normal, hard');
  }

  const mapArr = asStringArray(map);
  const monstersArr = asStringArray(monsters);
  const assetsArr = asStringArray(assets);

  if (Array.isArray(map) && mapArr.length !== map.length) {
    errors.push('map must be an array of strings');
  }
  if (Array.isArray(monsters) && monstersArr.length !== monsters.length) {
    errors.push('monsters must be an array of strings');
  }
  if (Array.isArray(assets) && assetsArr.length !== assets.length) {
    errors.push('assets must be an array of strings');
  }

  if (errors.length > 0) {
    return { valid: false, errors };
  }

  return {
    valid: true,
    errors: [],
    payload: {
      name: name.trim(),
      difficulty,
      map: mapArr,
      monsters: monstersArr,
      assets: assetsArr,
    },
  };
}

function toLevel(id, payload) {
  return {
    id,
    name: payload.name,
    difficulty: payload.difficulty,
    map: payload.map ?? [],
    monsters: payload.monsters ?? [],
    assets: payload.assets ?? [],
  };
}

export const levelsRouter = express.Router();

// GET /levels
levelsRouter.get('/', (req, res) => {
  const levels = Array.from(levelsStore.values());
  res.json(levels);
});

// GET /levels/:id
levelsRouter.get('/:id', (req, res) => {
  const id = req.params.id;
  const level = levelsStore.get(id);
  if (!level) {
    return res.status(404).json({ error: 'Level not found' });
  }
  res.json(level);
});

// POST /levels
levelsRouter.post('/', (req, res) => {
  const payloadResult = validateLevelPayload(req.body);
  if (!payloadResult.valid) {
    return res.status(400).json({ errors: payloadResult.errors });
  }
  let id = (req.body && typeof req.body.id === 'string' && req.body.id.trim()) ? req.body.id.trim() : '';
  if (!id) {
    id = generateId();
  } else if (levelsStore.has(id)) {
    return res.status(409).json({ error: 'Level with this id already exists' });
  }
  const level = toLevel(id, payloadResult.payload);
  levelsStore.set(id, level);
  res.status(201).json(level);
});

// PUT /levels/:id
levelsRouter.put('/:id', (req, res) => {
  const id = req.params.id;
  if (!levelsStore.has(id)) {
    return res.status(404).json({ error: 'Level not found' });
  }
  const payloadResult = validateLevelPayload(req.body);
  if (!payloadResult.valid) {
    return res.status(400).json({ errors: payloadResult.errors });
  }
  const updated = toLevel(id, payloadResult.payload);
  levelsStore.set(id, updated);
  res.json(updated);
});

export default levelsRouter;

export function resetLevelsStore() {
  levelsStore.clear();
}
