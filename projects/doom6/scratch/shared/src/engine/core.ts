export type Entity = number;
export interface Component {}
export interface System { update(world: World, dt: number): void; }

// 2D vector helper used by some systems
export class Vec2 {
  constructor(public x: number, public y: number) {}
}

export class World {
  private nextEntity = 1;
  private stores: Map<string, Map<Entity, Component>> = new Map();
  private systems: any[] = [];

  // basic ECS methods
  createEntity(): Entity {
    return this.nextEntity++;
  }

  addComponent(entity: Entity, component: Component) {
    const key = (component as any).constructor.name;
    if (!this.stores.has(key)) this.stores.set(key, new Map());
    this.stores.get(key)!.set(entity, component);
  }

  getComponent<T>(entity: Entity, type: new (...args: any[]) => T): T | undefined {
    return (this.stores.get(type.name)?.get(entity) as T | undefined);
  }

  // simple system registration used by MVP runtime
  addSystem(s: System) {
    this.systems.push(s);
  }

  tick(dt: number) {
    for (const s of this.systems) {
      // Systems expect signature: (world, dt)
      s.update(this, dt);
    }
  }

  // helper: remove an entity and all components
  removeEntity(entity: Entity) {
    for (const map of this.stores.values()) {
      map.delete(entity);
    }
  }

  // helper: get entities that have all requested component types
  getEntitiesWithComponents(types: Array<new (...args: any[]) => any>): Entity[] {
    if (types.length === 0) return [];
    const sets = types.map((t) => {
      const map = this.stores.get(t.name);
      return map ? new Set<Entity>(Array.from(map.keys())) : new Set<Entity>();
    });
    // intersect all sets
    let result = Array.from(sets[0]);
    for (let i = 1; i < sets.length; i++) {
      result = result.filter((id) => sets[i].has(id));
    }
    return result;
  }

  // simple raycast against Position components for MVP shooting system
  raycast(origin: Vec2, dir: Vec2, maxDistance: number, targetMarkers: Array<new (...args: any[]) => any>): { entity: Entity, point: Vec2 } | null {
    // normalize direction
    const mag = Math.hypot(dir.x, dir.y) || 1;
    const dx = dir.x / mag;
    const dy = dir.y / mag;

    const posMap = this.stores.get('Position');
    if (!posMap) return null;

    let best: { entity: Entity, t: number, hitPoint: Vec2 } | null = null;

    for (const [entity, pos] of posMap.entries()) {
      // check if entity has any of the target markers
      const hasTarget = targetMarkers.length === 0 ? true : targetMarkers.some((marker) => {
        const m = this.stores.get(marker.name);
        return !!m?.has(entity);
      });
      if (!hasTarget) continue;

      const px = (pos as any).x;
      const py = (pos as any).y;
      const vx = px - origin.x;
      const vy = py - origin.y;
      const t = vx * dx + vy * dy; // projection length onto dir
      if (t < 0 || t > maxDistance) continue;
      const closestX = origin.x + dx * t;
      const closestY = origin.y + dy * t;
      const ddx = px - closestX;
      const ddy = py - closestY;
      const dist2 = ddx * ddx + ddy * ddy;
      const hitRadius = 25; // 5 units threshold squared
      if (dist2 <= hitRadius) {
        if (!best || t < best.t) {
          best = { entity, t, hitPoint: new Vec2(px, py) };
        }
      }
    }

    return best ? { entity: best.entity, point: best.hitPoint } : null;
  }

  // reveal how many entities exist (for debugging / tests)
  getEntityCount(): number {
    const all = Array.from(this.stores.values()).flatMap((m) => Array.from(m.keys()));
    return all.length;
  }
}

// Simple marker components would live in other modules, for MVP tests we keep them in separate files

export default World;
