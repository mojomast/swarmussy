import express, { Request, Response } from 'express';

// Production-grade in-memory Level API
// Data model: Level { id, name, difficulty: 'easy'|'normal'|'hard', map: string[], monsters: string[], assets: string[] }

type Difficulty = 'easy' | 'normal' | 'hard';

export interface Level {
  id: string;
  name: string;
  difficulty: Difficulty;
  map: string[];
  monsters: string[];
  assets: string[];
}

// Local in-memory store (shared within this process)
const _levelsStore: Map<string, Level> = new Map();
export const __levelsStore = _levelsStore; // export for tests to reset/inspect

// Simple ID generator using crypto if available
function generateId(): string {
  if (typeof crypto !== 'undefined' && 'randomUUID' in (crypto as any)) {
    return (crypto as any).randomUUID();
  }
  // Fallback: timestamp + random
  const rand = Math.random().toString(36).slice(2, 8);
  return `lvl_${Date.now().toString(36)}_${rand}`;
}

function isDifficulty(v: any): v is Difficulty {
  return v === 'easy' || v === 'normal' || v === 'hard';
}

function asStringArray(v: any): string[] {
  if (!Array.isArray(v)) return [];
  return v.filter((x) => typeof x === 'string');
}

type LevelInput = Omit<Level, 'id'>;

function validateLevelPayload(input: any): { valid: boolean; errors: string[]; payload?: LevelInput } {
  const errors: string[] = [];
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
  // Coerce arrays, validate element types
  const mapArr = asStringArray(map);
  const monstersArr = asStringArray(monsters);
  const assetsArr = asStringArray(assets);

  // Note: arrays are optional; ensure if provided they are strings
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
      difficulty: difficulty,
      map: mapArr,
      monsters: monstersArr,
      assets: assetsArr,
    },
  };
}

function toLevel(id: string, payload: LevelInput): Level {
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
levelsRouter.get('/', (req: Request, res: Response) => {
  const levels = Array.from(_levelsStore.values());
  res.json(levels);
});

// GET /levels/:id
levelsRouter.get('/:id', (req: Request, res: Response) => {
  const id = req.params.id;
  const level = _levelsStore.get(id);
  if (!level) {
    return res.status(404).json({ error: 'Level not found' });
  }
  res.json(level);
});

// POST /levels
levelsRouter.post('/', (req: Request, res: Response) => {
  const payloadResult = validateLevelPayload(req.body);
  if (!payloadResult.valid) {
    return res.status(400).json({ errors: payloadResult.errors });
  }
  // Optional explicit id in body; otherwise generate
  let id = (req.body && typeof req.body.id === 'string' && req.body.id.trim()) ? req.body.id.trim() : '';
  if (!id) {
    id = generateId();
  } else if (_levelsStore.has(id)) {
    return res.status(409).json({ error: 'Level with this id already exists' });
  }
  const level = toLevel(id, payloadResult.payload!);
  _levelsStore.set(id, level);
  res.status(201).json(level);
});

// PUT /levels/:id
levelsRouter.put('/:id', (req: Request, res: Response) => {
  const id = req.params.id;
  if (!_levelsStore.has(id)) {
    return res.status(404).json({ error: 'Level not found' });
  }
  const payloadResult = validateLevelPayload(req.body);
  if (!payloadResult.valid) {
    return res.status(400).json({ errors: payloadResult.errors });
  }
  const updated = toLevel(id, payloadResult.payload!);
  _levelsStore.set(id, updated);
  res.json(updated);
});

// DELETE /levels/:id
levelsRouter.delete('/:id', (req: Request, res: Response) => {
  const id = req.params.id;
  if (!_levelsStore.has(id)) {
    return res.status(404).json({ error: 'Level not found' });
  }
  _levelsStore.delete(id);
  res.status(204).send();
});

// Export a default so importers can mount easily
export default levelsRouter;

// Helper to reset store in tests
export function resetLevelsStore() {
  _levelsStore.clear();
}
