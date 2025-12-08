// ECS core skeleton in TypeScript (core engine)

export type Entity = number;

export type Position = { x: number; y: number };
export type Velocity = { vx: number; vy: number };
export type Sprite = { w: number; h: number; color: string };

export class World {
  private nextId: number = 1;
  // Component stores: maps from entity id to component data
  public positions: Map<Entity, Position> = new Map();
  public velocities: Map<Entity, Velocity> = new Map();
  public sprites: Map<Entity, Sprite> = new Map();

  createEntity(): Entity {
    const id = this.nextId++;
    return id;
  }

  // Helper: add components
  addPosition(e: Entity, p: Position) {
    this.positions.set(e, p);
  }
  addVelocity(e: Entity, v: Velocity) {
    this.velocities.set(e, v);
  }
  addSprite(e: Entity, s: Sprite) {
    this.sprites.set(e, s);
  }

  // Systems helpers: query components exist
  hasPosition(e: Entity): boolean { return this.positions.has(e); }
  hasVelocity(e: Entity): boolean { return this.velocities.has(e); }
  hasSprite(e: Entity): boolean { return this.sprites.has(e); }

  // Iterate helpers for systems
  forEachEntityWithComponents(
    needPosition: boolean,
    needVelocity: boolean,
    needSprite: boolean,
    callback: (e: Entity) => void
  ) {
    const ids = new Set<Entity>();
    this.positions.forEach((_p, id) => ids.add(id));
    this.velocities.forEach((_v, id) => ids.add(id));
    this.sprites.forEach((_s, id) => ids.add(id));
    ids.forEach((e) => {
      if (needPosition && !this.positions.has(e)) return;
      if (needVelocity && !this.velocities.has(e)) return;
      if (needSprite && !this.sprites.has(e)) return;
      callback(e);
    });
  }
}

export class CanvasRendererAdapter {
  // This adapter is a thin bridge to actual rendering code in renderer.ts
  private drawFn: (pos: Position, sprite: Sprite) => void;
  constructor(drawFn: (pos: Position, sprite: Sprite) => void) {
    this.drawFn = drawFn;
  }
  render(pos: Position, sprite: Sprite) {
    this.drawFn(pos, sprite);
  }
}

export class RenderSystem {
  private draw: (pos: Position, sprite: Sprite) => void;
  constructor(draw: (pos: Position, sprite: Sprite) => void) {
    this.draw = draw;
  }
  render(world: World) {
    world.forEachEntityWithComponents(true, false, true, (e) => {
      const pos = world.positions.get(e)!;
      const sprite = world.sprites.get(e)!;
      this.draw(pos, sprite);
    });
  }
}

export class PhysicsSystem {
  step(world: World, dt: number) {
    if (dt <= 0) return;
    world.forEachEntityWithComponents(true, true, false, (e) => {
      const pos = world.positions.get(e)!;
      const vel = world.velocities.get(e)!;
      pos.x += vel.vx * dt;
      pos.y += vel.vy * dt;
    });
  }
}

export class InputSystem {
  private input: import('./input').KeyboardInput;
  constructor(input: any) {
    this.input = input;
  }
  update(world: World, e: Entity, speed: number) {
    // dynamic import to avoid circular type dependency in runtime
    // but for TS type checks, we cast accordingly
    const st: any = (this.input as any).getState();
    const v = world.velocities.get(e);
    if (!v) return;
    v.vx = (st.right ? speed : 0) - (st.left ? speed : 0);
    v.vy = (st.down ? speed : 0) - (st.up ? speed : 0);
  }
}

export {}; // ensure this module is treated as a module
