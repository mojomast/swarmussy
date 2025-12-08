import express, { Request, Response } from 'express';
import { validateJson } from './validate.js';

// Level data model definitions (in-memory store)
export interface SpawnPoint { x: number; y: number; z: number; }
export interface Dimensions { width: number; height: number; depth: number; }
export interface Level {
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
}

// In-memory store
const levelsStore = new Map<string, Level>();

// Simple id generator
function generateId(): string {
  return 'lvl_' + Math.random().toString(36).slice(2, 9);
}

// JSON Schema for a level (mirrors tests/validation.test.js)
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

export function createLevelsRouter(): express.Router {
  const router = express.Router();

  // POST /levels - create level
  router.post('/levels', (req, res) => {
    const data = req.body as any;
    const validation = validateJson(levelSchema, data);
    if (!validation.valid) {
      return res.status(400).json({ errors: validation.errors });
    }

    const id = data.id ?? generateId();
    if (levelsStore.has(id)) {
      return res.status(409).json({ error: 'Level already exists' });
    }

    const level: Level = {
      id,
      name: data.name,
      dimensions: data.dimensions,
      tiles: data.tiles,
      monsters: data.monsters,
      weapons: data.weapons,
      assets: data.assets,
      spawn_points: data.spawn_points,
      version: data.version,
      createdAt: new Date().toISOString(),
    };

    levelsStore.set(id, level);
    res.status(201).json(level);
  });

  // GET /levels - list levels
  router.get('/levels', (_req, res) => {
    res.json(Array.from(levelsStore.values()));
  });

  // GET /levels/:id - read level
  router.get('/levels/:id', (req, res) => {
    const id = req.params.id;
    const lvl = levelsStore.get(id);
    if (!lvl) {
      return res.status(404).json({ error: 'Level not found' });
    }
    res.json(lvl);
  });

  // PUT /levels/:id - update level
  router.put('/levels/:id', (req: Request, res: Response) => {
    const id = req.params.id;
    // Basic path traversal protection
    if (id.includes('..') || id.includes('/')) {
      return res.status(400).json({ error: 'invalid_id' });
    }

    const data = req.body as any;

    // Basic API rule: body must include id and match route id
    if (!data || typeof data.id !== 'string' || data.id !== id) {
      return res.status(400).json({ error: 'Payload id must match URL id' });
    }

    const validation = validateJson(levelSchema, data);
    if (!validation.valid) {
      return res.status(400).json({ errors: validation.errors });
    }

    const existing = levelsStore.get(id);
    if (!existing) {
      return res.status(404).json({ error: 'Level not found' });
    }

    const updated: Level = {
      ...existing,
      name: data.name,
      dimensions: data.dimensions,
      tiles: data.tiles,
      monsters: data.monsters,
      weapons: data.weapons,
      assets: data.assets,
      spawn_points: data.spawn_points,
      version: data.version
      // createdAt remains the same
    };

    levelsStore.set(id, updated);
    res.status(200).json(updated);
  });

  return router;
}

export function seedFromData(levels: any[]): void {
  if (!Array.isArray(levels)) return;
  for (const lvl of levels) {
    if (lvl && typeof lvl.id === 'string') {
      levelsStore.set(lvl.id, lvl as Level);
    }
  }
}

export function resetLevelsStore(): void {
  levelsStore.clear();
}

export default createLevelsRouter();

// Note: This file now serves the real, production-like API used by the server.ts in this repo.
