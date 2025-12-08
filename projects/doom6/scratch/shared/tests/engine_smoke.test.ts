import { World } from '../src/engine';

describe('Engine smoke', () => {
  test('basic world tick with no entities', () => {
    const w = new World();
    w.tick(0.016);
    expect(true).toBe(true);
  });
});
