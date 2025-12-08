// Minimal ECS-like Engine core with gravity-like tick
// Exports:
//   - EngineCore: core engine with world integration and tick loop hooks
//   - WorldState, WorldEntity, Vec2, EngineState types for external usage

export type Vec2 = { x: number; y: number };

export interface WorldEntity {
  id: string;
  pos: Vec2;
  vel: Vec2;
}

export interface WorldState {
  entities: Map<string, WorldEntity>;
}

export interface EngineState {
  running: boolean;
  tick: number;
  fps: number;
  lastTickMs?: number;
}

export interface SystemFn {
  (world: WorldState, dt: number): void;
}

export class EngineCore {
  private world?: WorldState;
  private running: boolean = false;
  private tickCount: number = 0;
  private fps: number = 0;
  private gravity: number;
  private timeScale: number;
  private lastTickMs?: number;
  private systems: SystemFn[] = [];

  constructor(config?: { gravity?: number; timeScale?: number }) {
    this.gravity = config?.gravity ?? 9.81;
    this.timeScale = config?.timeScale ?? 1;
  }

  // World integration
  public setWorld(world: WorldState): void {
    this.world = world;
  }

  public getWorld(): WorldState | undefined {
    return this.world;
  }

  // Lifecycle
  public async start(): Promise<EngineState> {
    this.running = true;
    return this.status();
  }

  public async tick(dt?: number): Promise<EngineState> {
    // If dt not provided, default to 16ms (60fps)
    const delta = typeof dt === 'number' ? dt : 0.016;
    this.doTick(delta * this.timeScale);
    return this.status();
  }

  public stop(): void {
    this.running = false;
  }

  public status(): EngineState {
    return {
      running: this.running,
      tick: this.tickCount,
      fps: this.fps,
      lastTickMs: this.lastTickMs,
    };
  }

  public addSystem(system: SystemFn): void {
    this.systems.push(system);
  }

  private doTick(dt: number): void {
    // time delta
    const now = typeof performance !== 'undefined' ? (performance.now() as number) : Date.now();
    // naive FPS estimation using dt
    this.fps = dt > 0 ? Math.round(1 / dt) : this.fps;

    // Ensure world exists for gravity integration
    if (this.world) {
      for (const ent of this.world.entities.values()) {
        if (!ent || !('pos' in ent) || !('vel' in ent)) continue;
        // Gravity accelerates velocity along y
        ent.vel.y += this.gravity * dt;
        // Integrate position
        ent.pos.x += ent.vel.x * dt;
        ent.pos.y += ent.vel.y * dt;
      }
    }

    // Run systems if any
    for (const sys of this.systems) {
      sys(this.world ?? { entities: new Map<string, WorldEntity>() }, dt);
    }

    this.tickCount++;
    this.lastTickMs = now;
  }
