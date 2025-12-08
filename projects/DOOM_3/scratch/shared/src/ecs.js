// Minimal ECS implementation for testing in this QA scaffold
export class ECS {
  constructor() {
    this.nextId = 1;
    this.entities = new Set();
    // Map<componentName, Map<entityId, data>>
    this.components = new Map();
    this.systems = [];
  }

  createEntity() {
    const id = this.nextId++;
    this.entities.add(id);
    return id;
  }

  addComponent(entity, name, data) {
    if (!this.entities.has(entity)) throw new Error('Unknown entity');
    let compMap = this.components.get(name);
    if (!compMap) {
      compMap = new Map();
      this.components.set(name, compMap);
    }
    compMap.set(entity, data);
  }

  getComponent(entity, name) {
    const compMap = this.components.get(name);
    return compMap?.get(entity);
  }

  hasComponent(entity, name) {
    const compMap = this.components.get(name);
    return !!compMap?.has(entity);
  }

  removeComponent(entity, name) {
    const compMap = this.components.get(name);
    if (compMap) compMap.delete(entity);
  }

  addSystem(fn, deps = []) {
    this.systems.push({ fn, deps });
  }

  // Helper to get entities that have all specified components and provide their components
  getEntitiesWith(...names) {
    if (names.length === 0) return [];
    // Start from the smallest component map to optimize
    let smallestName = names[0];
    let smallestSize = -1;
    for (const n of names) {
      const m = this.components.get(n);
      const size = m ? m.size : 0;
      if (smallestSize === -1 || size < smallestSize) {
        smallestSize = size;
        smallestName = n;
      }
    }
    const result = [];
    const firstMap = this.components.get(smallestName) || new Map();
    for (const [entity, comp0] of firstMap.entries()) {
      let ok = true;
      const comps = { [smallestName]: comp0 };
      for (const n of names) {
        if (n === smallestName) continue;
        const m = this.components.get(n);
        if (!m || !m.has(entity)) { ok = false; break; }
        comps[n] = m.get(entity);
      }
      if (ok) {
        result.push({ entity, components: comps });
      }
    }
    return result;
  }

  run(delta) {
    const world = {
      ecs: this,
      delta,
      getEntitiesWith: (...names) => this.getEntitiesWith(...names)
    };
    for (const s of this.systems) {
      s.fn(world, delta);
    }
  }
}

export default ECS;
