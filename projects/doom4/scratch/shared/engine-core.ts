// Core ECS, Engine, Input, and minimal rendering for MVP

export type CompName = 'Position' | 'Velocity' | 'Renderable' | 'Camera' | 'AI' | 'Bullet';

export interface Position {
  x: number;
  y: number;
  z?: number;
}

export interface Velocity {
  x: number;
  y: number;
  z?: number;
}

export interface Renderable {
  sprite?: string;
  color?: string;
  ascii?: string;
}

export interface Camera {
  fov?: number;
  dist?: number;
}

export interface AI {
  type: string;
  targetId?: string;
  state?: string;
  cooldown?: number;
}

export interface Bullet {
  speed: number;
  life?: number;
}

export type Entity = number;

// Simple in-memory ECS
export class World {
  private _nextId: number = 1;
  private _entities: Set<Entity> = new Set();
  private _store: Map<Entity, Map<CompName, any>> = new Map();

  createEntity(): Entity {
    const id = this._nextId++;
    this._entities.add(id);
    this._store.set(id, new Map());
    return id;
  }

  addComponent<T>(entity: Entity, comp: CompName, data: T): void {
    const ent = this._store.get(entity);
    if (!ent) throw new Error('Unknown entity');
    ent.set(comp, data);
  }

  getComponent<T>(entity: Entity, comp: CompName): T | undefined {
    const ent = this._store.get(entity);
    if (!ent) return undefined;
    return ent.get(comp) as T;
  }

  hasComponent(entity: Entity, comp: CompName): boolean {
    const ent = this._store.get(entity);
    return !!ent?.has(comp);
  }

  removeEntity(entity: Entity): void {
    this._store.delete(entity);
    this._entities.delete(entity);
  }

  getEntitiesWith(...comps: CompName[]): Entity[] {
    const result: Entity[] = [];
    for (const e of this._entities) {
      const ent = this._store.get(e);
      if (!ent) continue;
      const ok = comps.every(c => ent.has(c));
      if (ok) result.push(e);
    }
    return result;
  }

  serialize(): string {
    const data: any = {
      nextId: this._nextId,
      entities: Array.from(this._entities),
      components: Array.from(this._store.entries()).map(([eid, map]) => {
        const obj: any = { id: eid, comps: {} };
        for (const [k, v] of map.entries()) {
          obj.comps[k] = v;
        }
        return obj;
      }),
    };
    return JSON.stringify(data);
  }

  deserialize(raw: string): void {
    const obj = JSON.parse(raw);
    this._store.clear();
    this._entities.clear();
    this._nextId = obj.nextId ?? 1;
    for (const ent of obj.entities) {
      const id = Number(ent);
      this._entities.add(id);
      this._store.set(id, new Map());
    }
    for (const ent of obj.components) {
      const id = ent.id as Entity;
      const comps = ent.comps as { [k in CompName]?: any };
      const map = this._store.get(id);
      if (map) {
        for (const k of Object.keys(comps) as CompName[]) {
          map.set(k, comps[k]);
        }
      }
    }
  }
}

export class InputManager {
  private _pressed: Set<string> = new Set();
  constructor() {
    window.addEventListener('keydown', (e) => this._pressed.add(e.key.toLowerCase()));
    window.addEventListener('keyup', (e) => this._pressed.delete(e.key.toLowerCase()));
  }
  isPressed(key: string): boolean {
    return this._pressed.has(key.toLowerCase());
  }
  getState(): string[] {
    return Array.from(this._pressed);
  }
}

export class Engine {
  private _world: World = new World();
  private _canvas?: HTMLCanvasElement;
  private _ctx?: CanvasRenderingContext2D | null;
  private _map: number[][] = [];
  private _running: boolean = false;
  private _player?: Entity;
  private _aiEntities: Entity[] = [];
  private _input: InputManager = new InputManager();
  private _width: number = 320;
  private _height: number = 180;

  constructor(map: number[][]) {
    this._map = map;
  }

  init(canvasId: string): void {
    const c = document.getElementById(canvasId) as HTMLCanvasElement | null;
    if (!c) throw new Error('Canvas not found');
    this._canvas = c;
    const ctx = c.getContext('2d');
    if (!ctx) throw new Error('Canvas context not available');
    this._ctx = ctx;

    const w = c.clientWidth || 320;
    const h = c.clientHeight || 180;
    c.width = w;
    c.height = h;
    this._width = w;
    this._height = h;

    // Player
    const player = this._world.createEntity();
    this._world.addComponent<Position>(player, 'Position', { x: 1.5, y: 1.5, z: 0 });
    this._world.addComponent<Velocity>(player, 'Velocity', { x: 0, y: 0, z: 0 });
    this._world.addComponent<Renderable>(player, 'Renderable', { color: '#0f0', ascii: '@' });
    this._world.addComponent<Camera>(player, 'Camera', { fov: Math.PI / 3, dist: 1.0 });
    this._player = player;

    // AI
    const ai = this._world.createEntity();
    this._world.addComponent<Position>(ai, 'Position', { x: 4, y: 4, z: 0 });
    this._world.addComponent<Velocity>(ai, 'Velocity', { x: 0, y: 0, z: 0 });
    this._world.addComponent<Renderable>(ai, 'Renderable', { color: '#f00', ascii: 'E' });
    this._world.addComponent<AI>(ai, 'AI', { type: 'chaser', targetId: `${player}`, state: 'idle', cooldown: 0 });
    this._aiEntities.push(ai);
  }

  private _timePrev: number = performance.now();
  start(): void {
    if (!this._canvas || !this._ctx) throw new Error('Engine not initialized');
    this._running = true;
    requestAnimationFrame(this._loop.bind(this));
  }

  stop(): void {
    this._running = false;
  }

  private _loop(t: number): void {
    if (!this._running) return;
    const dt = Math.min(0.05, (t - this._timePrev) / 1000);
    this._timePrev = t;

    this.update(dt);
    this.render();
    requestAnimationFrame(this._loop.bind(this));
  }

  private update(dt: number) {
    // movement via WASD/Arrows
    if (this._player) {
      const pos = this._world.getComponent<Position>(this._player, 'Position');
      const vel = this._world.getComponent<Velocity>(this._player, 'Velocity');
      if (pos && vel) {
        const speed = 1.8;
        const up = this._input.isPressed('w') || this._input.isPressed('arrowup');
        const down = this._input.isPressed('s') || this._input.isPressed('arrowdown');
        const left = this._input.isPressed('a') || this._input.isPressed('arrowleft');
        const right = this._input.isPressed('d') || this._input.isPressed('arrowright');
        vel.x = 0; vel.y = 0;
        if (up) pos.y -= speed * dt;
        if (down) pos.y += speed * dt;
        if (left) pos.x -= speed * dt;
        if (right) pos.x += speed * dt;
      }
    }

    // AI chase
    for (const ai of this._aiEntities) {
      const aPos = this._world.getComponent<Position>(ai, 'Position');
      const aAI = this._world.getComponent<AI>(ai, 'AI');
      if (aPos && aAI) {
        if (!this._player) continue;
        const pPos = this._world.getComponent<Position>(this._player, 'Position');
        if (pPos) {
          const dx = pPos.x - aPos.x;
          const dy = pPos.y - aPos.y;
          const dist = Math.hypot(dx, dy);
          const speed = 0.8;
          if (dist > 0.1) {
            aPos.x += (dx / dist) * speed * dt;
            aPos.y += (dy / dist) * speed * dt;
          }
        }
      }
    }
  }

  private render(): void {
    if (!this._ctx || !this._canvas) return;
    const ctx = this._ctx;
    const w = this._width; const h = this._height;
    ctx.clearRect(0, 0, w, h);

    // Simple top-down mini-map rendering
    const scale = 20; // pixels per map unit
    // draw a simple boundary and map grid if provided
    // render a few walls from a placeholder map if available in future

    // render entities
    const renderEntity = (entity: Entity, color: string, symbol: string) => {
      const pos = this._world.getComponent<Position>(entity, 'Position');
      if (pos) {
        ctx.fillStyle = color;
        ctx.fillRect(pos.x * scale - 3, pos.y * scale - 3, 6, 6);
        ctx.fillStyle = '#fff';
        ctx.font = '10px monospace';
        ctx.fillText(symbol, pos.x * scale - 3, pos.y * scale - 6);
      }
    };

    // draw player and AI
    if (this._player) renderEntity(this._player, '#0f0', '@');
    for (const ai of this._aiEntities) renderEntity(ai, '#f00', 'E');
  }

  // Persistence helpers
  saveWorld(): string {
    return this._world.serialize();
  }
  loadWorld(json: string): void {
    this._world.deserialize(json);
  }

  // accessors for tests
  getWorld(): World { return this._world; }
  getInput(): InputManager { return this._input; }
}

export { World };
export { Engine };
export { InputManager };

