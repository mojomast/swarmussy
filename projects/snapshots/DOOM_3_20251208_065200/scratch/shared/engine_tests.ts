import { EngineImpl, EngineStore, World, Entity, System } from './engine_impl'

class DummyStore implements EngineStore {
  private w: World = { entities: [], systems: [], tick: 0 }
  async loadWorld(): Promise<World> { return this.w }
  async saveWorld(world: World): Promise<void> { this.w = world }
  async resetWorld(): Promise<World> { this.w = { entities: [], systems: [], tick: 0 }; return this.w }
}

class MoveSystem implements System {
  update(world: World, deltaMs: number): void {
    // simple system: move all entities by delta in a component called 'pos'
    for (const e of world.entities) {
      const pos = e.components['pos'] ?? 0
      e.components['pos'] = pos + deltaMs
    }
  }
}

export async function runEngineTests() {
  const world: World = { entities: [{ id: 'a', components: { pos: 0 } }], systems: [new MoveSystem()], tick: 0 }
  const store = new DummyStore()
  const engine = new EngineImpl({ store, initialWorld: world })
  await engine.start()
  await engine.tick()
  await engine.tick()
  const s1 = world.entities[0].components['pos']
  await engine.reset()
  const w2 = engine.getWorldState()
  // Basic sanity checks
  if (!w2 || w2.tick !== 0) {
    throw new Error('Reset did not reset world tick')
  }
  if (s1 == null) {
    throw new Error('MoveSystem did not mutate entity')
  }
  console.log('Engine tests scaffold executed')
  return true
}
