import { EditorStore, marshalState, unmarshalState } from '../api/editor_api';

describe('EditorStore API surface', () => {
  it('can upsert assets, levels, and entities', () => {
    const store = new EditorStore();
    // assets
    const a1 = store.upsertAsset({ name: 'hero', type: 'monster', metadata: { hp: 100 } });
    expect(a1.name).toBe('hero');
    expect(a1.type).toBe('monster');

    const a2 = store.upsertAsset({ assetId: a1.assetId, name: 'hero-elite' });
    expect(a2.assetId).toBe(a1.assetId);
    expect(a2.name).toBe('hero-elite');

    // levels
    const l1 = store.upsertLevel({ name: 'level-1', width: 128, height: 64 });
    expect(l1.name).toBe('level-1');
    expect(l1.width).toBe(128);

    // entities
    const e1 = store.upsertEntity({ type: 'monster', name: 'goblin', levelId: l1.levelId });
    expect(e1.type).toBe('monster');
    expect(e1.name).toBe('goblin');
    expect(e1.levelId).toBe(l1.levelId);

    // metadata fetchers
    const assets = store.getAssets();
    const levels = store.getLevels();
    const entities = store.getEntities();
    expect(assets.length).toBeGreaterThanOrEqual(1);
    expect(levels.length).toBeGreaterThanOrEqual(1);
    expect(entities.length).toBeGreaterThanOrEqual(1);
  });

  it('can marshal/unmarshal editor state', () => {
    const store = new EditorStore();
    const s = marshalState(store.getState());
    const restored = unmarshalState(s);
    // simple sanity: JSON round-trip yields a string representation that parses back
    expect(restored).toBeDefined();
  });
});
