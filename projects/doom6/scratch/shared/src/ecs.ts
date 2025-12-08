// Robust MVP ECS for MVP runtime QA tests (flexible component keys case-insensitive)

export class Entity {
  static nextId: number = 1;
  public id: number;
  public components: Map<string, any> = new Map();
  constructor() {
    this.id = Entity.nextId++;
  }
  addComponent(type: string, component: any) {
    this.components.set(type, component);
  }
  getComponent<T>(type: string): T | undefined {
    return this.components.get(type) as T | undefined;
  }
}

export interface IComponent {}

export class Position implements IComponent {
  constructor(public x: number, public y: number) {}
}

export class Velocity implements IComponent {
  constructor(public vx: number, public vy: number) {}
}

export class Shooting implements IComponent {
  rate: number;
  cooldown: number;
  bulletSpeed: number;
  constructor(params: { rate: number; cooldown?: number; bulletSpeed: number }) {
    this.rate = params.rate;
    this.cooldown = params.cooldown ?? 0;
    this.bulletSpeed = params.bulletSpeed;
  }
}

export interface System {
  update(world: World, dt: number): void;
}

export class MovementSystem implements System {
  update(world: World, dt: number): void {
    if (dt <= 0) return;
    const ids = world.query(['Position', 'Velocity']);
    for (const id of ids) {
      const pos = world.getComponent<Position>(id, 'Position') || world.getComponent<Position>(id, 'position');
      const vel = world.getComponent<Velocity>(id, 'Velocity') || world.getComponent<Velocity>(id, 'velocity');
      if (pos && vel) {
        pos.x += vel.vx * dt;
        pos.y += vel.vy * dt;
      }
    }
  }
}

export class ShootingSystem implements System {
  update(world: World, dt: number): void {
    if (dt < 0) dt = 0;
    const shooters = world.query(['Shooting', 'shooting']);
    for (const id of shooters) {
      const shoot = world.getComponent<Shooting>(id, 'Shooting') || world.getComponent<Shooting>(id, 'shooting');
      const pos = world.getComponent<Position>(id, 'Position') || world.getComponent<Position>(id, 'position');
      if (!shoot || !pos) continue;
      if (shoot.cooldown <= 0) {
        const bullet = new Entity();
        bullet.addComponent('Position', new Position(pos.x, pos.y));
        bullet.addComponent('Velocity', new Velocity(shoot.bulletSpeed, 0));
        world.addEntity(bullet);
        shoot.cooldown = 1 / shoot.rate;
      } else {
        shoot.cooldown -= dt;
      }
    }
  }
}

export class World {
  private entities: Entity[] = [];
  // stores: component type -> (entity.id -> component)
  private stores: Map<string, Map<number, any>> = new Map();
  private systems: System[] = [];

  createEntity(): Entity {
    const e = new Entity();
    this.entities.push(e);
    return e;
  }

  addEntity(e: Entity) {
    this.entities.push(e);
    // copy existing components from the entity into stores
    for (const [type, comp] of e.components) {
      this.addComponent(e.id, type, comp);
    }
  }

  addComponent(entityOrId: number | Entity, type: string, component: any) {
    const id = typeof entityOrId === 'object' ? (entityOrId as Entity).id : (entityOrId as number);
    const keys = [type, type.toLowerCase()];
    for (const k of keys) {
      if (!this.stores.has(k)) this.stores.set(k, new Map<number, any>());
      this.stores.get(k)!.set(id, component);
    }
  }

  getComponent<T>(entityOrId: number | Entity, type: string): T | undefined {
    const id = typeof entityOrId === 'object' ? (entityOrId as Entity).id : (entityOrId as number);
    const v1 = this.stores.get(type)?.get(id);
    if (v1 !== undefined) return v1 as T;
    const v2 = this.stores.get(type.toLowerCase())?.get(id);
    return v2 as T | undefined;
  }

  query(types: string[]): number[] {
    if (types.length === 0) return [];
    // Build candidate set from first type (union of both case keys)
    const first = types[0];
    const firstSet = new Set<number>();
    const s1 = this.stores.get(first);
    if (s1) for (const id of s1.keys()) firstSet.add(id);
    const s2 = this.stores.get(first.toLowerCase());
    if (s2) for (const id of s2.keys()) firstSet.add(id);

    let result: number[] = Array.from(firstSet);

    for (let i = 1; i < types.length; i++) {
      const t = types[i];
      const cur = new Set<number>();
      const a = this.stores.get(t);
      if (a) for (const id of a.keys()) cur.add(id);
      const b = this.stores.get(t.toLowerCase());
      if (b) for (const id of b.keys()) cur.add(id);
      result = result.filter((id) => cur.has(id));
    }
    return result;
  }

  getEntities(): Entity[] {
    return this.entities;
  }

  registerSystem(s: System) {
    this.systems.push(s);
  }

  boot(): void {
    // no-op bootstrap
  }

  tick(dt: number) {
    for (const s of this.systems) s.update(this, dt);
  }

  removeEntity(entityId: number) {
    // remove from all stores
    for (const m of this.stores.values()) {
      m.delete(entityId);
    }
    this.entities = this.entities.filter((e) => e.id !== entityId);
  }

  getEntityCount(): number {
    return this.entities.length;
  }

  getEntitiesWithComponents(types: Array<string>): number[] {
    return this.query(types);
  }

  raycast(origin: { x: number, y: number }, dir: { x: number, y: number }, maxDistance: number, targetMarkers: Array<string>): { entity: number, point: { x: number, y: number } } | null {
    const mag = Math.hypot(dir.x, dir.y) || 1;
    const dx = dir.x / mag;
    const dy = dir.y / mag;
    const posMap = this.stores.get('Position');
    if (!posMap) return null;
    let best: { entity: number, t: number, hitPoint: { x: number, y: number } } | null = null;
    for (const [entity, pos] of posMap.entries()) {
      // check target markers
      let hasTarget = targetMarkers.length === 0;
      if (!hasTarget) {
        hasTarget = targetMarkers.some((m) => {
          const map = this.stores.get(m);
          return !!map?.has(entity);
        });
      }
      if (!hasTarget) continue;
      const px = (pos as any).x;
      const py = (pos as any).y;
      const vx = px - origin.x;
      const vy = py - origin.y;
      const t = vx * dx + vy * dy;
      if (t < 0 || t > maxDistance) continue;
      const closestX = origin.x + dx * t;
      const closestY = origin.y + dy * t;
      const ddx = px - closestX;
      const ddy = py - closestY;
      const dist2 = ddx * ddx + ddy * ddy;
      const hitRadius = 25;
      if (dist2 <= hitRadius) {
        if (!best || t < best.t) {
          best = { entity, t, hitPoint: { x: px, y: py } };
        }
      }
    }
    return best ? { entity: best.entity, point: best.hitPoint } : null;
  }
}

export default World;
