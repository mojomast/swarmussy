export type Entity = number;

export interface IComponent {
  // marker interface
}

export class World {
  private nextEntityId: number = 1;
  private components: Map<string, Map<Entity, IComponent>> = new Map();

  createEntity(): Entity {
    const id = this.nextEntityId++;
    return id;
  }

  addComponent<T extends IComponent>(entity: Entity, type: string, component: T): void {
    if (!this.components.has(type)) {
      this.components.set(type, new Map<Entity, IComponent>());
    }
    this.components.get(type)!.set(entity, component);
  }

  getComponent<T extends IComponent>(entity: Entity, type: string): T | undefined {
    const map = this.components.get(type);
    return map ? (map.get(entity) as T | undefined) : undefined;
  }

  query(types: string[]): Entity[] {
    if (types.length === 0) return [];
    const [first, ...rest] = types;
    const firstMap = this.components.get(first);
    if (!firstMap) return [];
    const candidates = Array.from(firstMap.keys());
    return candidates.filter((id) => rest.every((t) => (this.components.get(t)?.has(id) ?? false)));
  }
}

export class Position implements IComponent {
  constructor(public x: number, public y: number) {}
}

export class Velocity implements IComponent {
  constructor(public vx: number, public vy: number) {}
}

export interface System {
  update(world: World, dt: number): void;
}

export class MovementSystem implements System {
  update(world: World, dt: number): void {
    const entities = world.query(['Position', 'Velocity']);
    for (const id of entities) {
      const pos = world.getComponent<Position>(id, 'Position');
      const vel = world.getComponent<Velocity>(id, 'Velocity');
      if (pos && vel) {
        pos.x += vel.vx * dt;
        pos.y += vel.vy * dt;
      }
    }
  }
}

export class RenderSystem implements System {
  update(world: World, dt: number): void {
    // Lightweight textual render for a Node/CLI environment
    const entities = world.query(['Position']);
    if (entities.length === 0) {
      console.log('[Render] No entities with Position.');
      return;
    }
    console.log('[Render] Entities state:');
    for (const id of entities) {
      const pos = world.getComponent<Position>(id, 'Position')!;
      console.log(`  Entity ${id}: position (${pos.x.toFixed(2)}, ${pos.y.toFixed(2)})`);
    }
  }
}

export class SystemPipeline {
  private systems: System[] = [];
  add(system: System) {
    this.systems.push(system);
  }
  update(world: World, dt: number) {
    for (const sys of this.systems) sys.update(world, dt);
  }
}
