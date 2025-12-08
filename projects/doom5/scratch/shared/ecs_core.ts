// Lightweight TypeScript ECS core scaffold
// Entities are numeric IDs. Components are simple interfaces stored in Maps.

export type Entity = number;

export interface Position {
  x: number;
  y: number;
}

export interface Velocity {
  dx: number;
  dy: number;
}

export interface Sprite {
  key: string;
  layer?: number;
}

export interface RenderItem {
  entity: Entity;
  x: number;
  y: number;
  spriteKey: string;
}

// World is a minimal ECS world holding components in maps keyed by entity.
export class World {
  private nextEntityId: number = 1;

  private positions: Map<Entity, Position> = new Map();
  private velocities: Map<Entity, Velocity> = new Map();
  private sprites: Map<Entity, Sprite> = new Map();

  // Create a new entity and return its ID
  public createEntity(): Entity {
    const id = this.nextEntityId++;
    return id;
  }

  // Position component
  public addPosition(entity: Entity, pos: Position): void {
    this.positions.set(entity, pos);
  }
  public getPosition(entity: Entity): Position | undefined {
    return this.positions.get(entity);
  }
  public removePosition(entity: Entity): void {
    this.positions.delete(entity);
  }
  public getPositions(): Map<Entity, Position> {
    return this.positions;
  }

  // Velocity component
  public addVelocity(entity: Entity, vel: Velocity): void {
    this.velocities.set(entity, vel);
  }
  public getVelocity(entity: Entity): Velocity | undefined {
    return this.velocities.get(entity);
  }
  public removeVelocity(entity: Entity): void {
    this.velocities.delete(entity);
  }
  public getVelocities(): Map<Entity, Velocity> {
    return this.velocities;
  }

  // Sprite component
  public addSprite(entity: Entity, sprite: Sprite): void {
    this.sprites.set(entity, sprite);
  }
  public getSprite(entity: Entity): Sprite | undefined {
    return this.sprites.get(entity);
  }
  public removeSprite(entity: Entity): void {
    this.sprites.delete(entity);
  }
  public getSprites(): Map<Entity, Sprite> {
    return this.sprites;
  }

  // Utilities for systems
  public getEntitiesWithPosition(): Entity[] {
    return Array.from(this.positions.keys());
  }

  // Entities that have both Position and Sprite
  public getEntitiesWithPositionAndSprite(): Entity[] {
    const ents: Entity[] = [];
    for (const [e, pos] of this.positions.entries()) {
      if (this.sprites.has(e)) {
        ents.push(e);
      }
    }
    return ents;
  }

  // Convenience: step simulation for a fixed dt using Velocity -> Position
  public step(dt: number): void {
    if (dt === 0) return;
    for (const [e, vel] of this.velocities.entries()) {
      const pos = this.positions.get(e);
      if (!pos) continue;
      pos.x += vel.dx * dt;
      pos.y += vel.dy * dt;
    }
  }
}

// Render system computes render-ready data from World
export class RenderSystem {
  // Produce a simple render list: entity, position, and sprite key
  public static render(world: World): ReadonlyArray<RenderItem> {
    const res: RenderItem[] = [];
    const entities = world.getEntitiesWithPositionAndSprite();
    for (const e of entities) {
      const pos = world.getPosition(e);
      const spr = world.getSprite(e);
      if (pos && spr) {
        res.push({ entity: e, x: pos.x, y: pos.y, spriteKey: spr.key });
      }
    }
    return res;
  }
}

// Simple demonstration helper (not part of the core library API, but useful in docs/tests)
export function demoCreateSampleWorld(): World {
  const world = new World();
  // Entity 1: hero with velocity
  const hero = world.createEntity();
  world.addPosition(hero, { x: 0, y: 0 });
  world.addVelocity(hero, { dx: 1, dy: 0 });
  world.addSprite(hero, { key: 'hero' });

  // Entity 2: enemy static
  const enemy = world.createEntity();
  world.addPosition(enemy, { x: 5, y: 2 });
  world.addSprite(enemy, { key: 'enemy' });

  // Entity 3: obstacle with downward motion
  const orb = world.createEntity();
  world.addPosition(orb, { x: -1, y: 4 });
  world.addVelocity(orb, { dx: 0, dy: -1 });
  world.addSprite(orb, { key: 'orb' });

  return world;
}

// Tick the world by dt and return render-ready data structure
export function demoTickAndRender(world: World, dt: number): ReadonlyArray<RenderItem> {
  world.step(dt);
  return RenderSystem.render(world);
}

export default World;
