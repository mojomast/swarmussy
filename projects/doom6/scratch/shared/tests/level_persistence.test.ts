// Basic tests for level persistence round-trip
import LevelEditor from '../src/editor/levels/level_editor';

describe('Level persistence', () => {
  test('saveLevel and loadLevel round-trip', () => {
    const editor = new LevelEditor();
    const level = {
      filename: 'test_level.json',
      width: 5,
      height: 4,
      tiles: Array.from({ length: 5 }, () => Array.from({ length: 4 }, () => 0)),
      entities: [ { id: 'p1', type: 'player', x: 0, y: 0 }, { id: 'e1', type: 'enemy', x: 1, y: 1 } ],
      name: 'Test Level'
    } as any;
    const json = editor.saveLevel(level);
    const loaded = LevelEditor.loadLevel('test_level.json');
    expect(loaded).toBeDefined();
    expect(loaded!.width).toBe(5);
    expect(loaded!.height).toBe(4);
  });
});
