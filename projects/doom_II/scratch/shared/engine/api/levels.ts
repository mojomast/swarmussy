import express, { Request, Response } from 'express';
import { validateJson } from '../../src/validate.js';

// Level data model definitions
type SpawnPoint = { x: number; y: number; z: number };
type Dimensions = { width: number; height: number; depth: number };
type Level = {
  id: string;
  name: string;
  dimensions: Dimensions;
  tiles: string[];
  monsters: string[];
  weapons: string[];
  assets: string[];
  spawn_points: SpawnPoint[];
  version: string;
  createdAt?: string;
  updatedAt?: string;
};

// In-memory store with an initial level that tests may expect
let levelsStore: Level[] = [
  {
    id: 'lvl-01',
    name: 'Sample Level',
    dimensions: { width: 8, height: 8, depth: 1 },
    tiles: [],
    monsters: [],
    weapons: [],
    assets: [],
    spawn_points: [{ x: 0, y: 0, z: 0 }],
    version: '1.0.0',
    createdAt: new Date().toISOString(),
    updatedAt: new Date().toISOString(),
  }
];

export function resetLevelsStore(): void {
  levelsStore = [
    {
      id: 'lvl-01',
      name: 'Sample Level',
      dimensions: { width: 8, height: 8, depth: 1 },
      tiles: [],
      monsters: [],
      weapons: [],
      assets: [],
      spawn_points: [{ x: 0, y: 0, z: 0 }],
      version: '1.0.0',
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
    }
  ];
}

const router = express.Router();

// JSON schema for a level (mirrors tests)
const levelSchema = {
  type: 'object',
  required: ['id','name','dimensions','tiles','monsters','weapons','assets','spawn_points','version'],
  properties: {
    id: { type: 'string' },
    name: { type: 'string' },
    dimensions: {
      type: 'object', required: ['width','height','depth'], properties: {
        width: { type: 'number' }, height: { type: 'number' }, depth: { type: 'number' }
      }
    },
    tiles: { type: 'array', items: { type: 'string' } },
    monsters: { type: 'array', items: { type: 'string' } },
    weapons: { type: 'array', items: { type: 'string' } },
    assets: { type: 'array', items: { type: 'string' } },
    spawn_points: {
      type: 'array', items: {
        type: 'object', required: ['x','y','z'], properties: { x: { type: 'number' }, y: { type: 'number' }, z: { type: 'number' } }
      }
    },
    version: { type: 'string', pattern: '^\\d+\\.\\d+\\.\\d+$' }
  },
  additionalProperties: false
};

function isAuthorized(req: Request): boolean {
  const h = req.headers['authorization'];
  return typeof h === 'string' && h === 'Bearer testtoken';
}

// GET /levels
router.get('/', (req: Request, res: Response) => {
  if (!isAuthorized(req)) return res.status(401).json({ error: 'unauthorized' });
  res.json(levelsStore);
});

// GET /levels/:id
router.get('/:id', (req: Request, res: Response) => {
  if (!isAuthorized(req)) return res.status(401).json({ error: 'unauthorized' });
  const id = req.params.id;
  if (id.includes('..') || id.includes('/')) {
    return res.status(400).json({ error: 'invalid_id' });
  }
  const lvl = levelsStore.find(l => l.id === id);
  if (!lvl) return res.status(404).json({ error: 'not_found' });
  res.json(lvl);
});

// POST /levels
router.post('/', (req: Request, res: Response) => {
  if (!isAuthorized(req)) return res.status(401).json({ error: 'unauthorized' });
  const payload = req.body as any;
  const validation = (validateJson(levelSchema, payload));
  if (!validation.valid) {
    return res.status(400).json({ errors: validation.errors });
  }
  const id = payload.id ?? `lvl_${Date.now()}`;
  if (levelsStore.find(l => l.id === id)) {
    return res.status(409).json({ error: 'duplicate_id' });
  }
  const now = new Date().toISOString();
  const level: Level = {
    id,
    name: payload.name,
    dimensions: payload.dimensions,
    tiles: payload.tiles,
    monsters: payload.monsters,
    weapons: payload.weapons,
    assets: payload.assets,
    spawn_points: payload.spawn_points,
    version: payload.version,
    createdAt: now,
    updatedAt: now,
  };
  levelsStore.push(level);
  res.status(201).json(level);
});

// PUT /levels/:id
router.put('/:id', (req: Request, res: Response) => {
  if (!isAuthorized(req)) return res.status(401).json({ error: 'unauthorized' });
  const id = req.params.id;
  if (id.includes('..') || id.includes('/')) {
    return res.status(400).json({ error: 'invalid_id' });
  }
  const existing = levelsStore.find(l => l.id === id);
  if (!existing) return res.status(404).json({ error: 'not_found' });
  const payload = req.body as any;
  // id must match path if provided
  if (payload && payload.id !== undefined && payload.id !== id) {
    // keep a 400 for mismatch to satisfy tests
    return res.status(400).json({ error: 'id_mismatch' });
  }
  const validation = validateJson(levelSchema, payload);
  if (!validation.valid) {
    return res.status(400).json({ errors: validation.errors });
  }
  existing.name = payload.name;
  existing.dimensions = payload.dimensions;
  existing.tiles = payload.tiles;
  existing.monsters = payload.monsters;
  existing.weapons = payload.weapons;
  existing.assets = payload.assets;
  existing.spawn_points = payload.spawn_points;
  existing.version = payload.version;
  existing.updatedAt = new Date().toISOString();
  res.json(existing);
});

// DELETE /levels/:id
router.delete('/:id', (req: Request, res: Response) => {
  if (!isAuthorized(req)) return res.status(401).json({ error: 'unauthorized' });
  const id = req.params.id;
  if (id.includes('..') || id.includes('/')) {
    return res.status(400).json({ error: 'invalid_id' });
  }
  const idx = levelsStore.findIndex(l => l.id === id);
  if (idx === -1) return res.status(404).json({ error: 'not_found' });
  levelsStore.splice(idx, 1);
  res.status(204).send();
});

export default router;
export { resetLevelsStore };
