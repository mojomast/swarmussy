import { saveLevel, loadLevel } from '../src/editor.js';

test('persistence save/load round trip', () => {
  const level = {
    id: 'lvl-01',
    name: 'Test Level',
    dimensions: { width: 8, height: 8, depth: 1 },
    tiles: [], monsters: [], weapons: [], assets: [], spawn_points: [{ x:0, y:0, z:0 }], version: '1.0.0'
  };
  // In-memory save
  expect(() => saveLevel(level)).not.toThrow();
  const loaded = loadLevel('lvl-01');
  // Since our storage is in-memory within module, ensure data round-trips
  expect(loaded).not.toBeNull();
  expect(loaded.id).toBe('lvl-01');
});
