import type { Level } from './levels_api.js';

export const sampleLevels: Level[] = [
  {
    id: 'lvl_default',
    name: 'Starter Level',
    dimensions: { width: 10, height: 5, depth: 1 },
    tiles: [],
    monsters: [],
    weapons: [],
    assets: [],
    spawn_points: [ { x: 0, y: 0, z: 0 } ],
    version: '1.0.0',
    createdAt: new Date().toISOString(),
  }
];
