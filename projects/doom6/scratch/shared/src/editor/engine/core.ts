// Editor-side lightweight ECS World scaffold
export class World {
  private nextId: number = 1;
  private components: Map<number, any> = new Map<number, any>();

  constructor() {}

  createEntity(): number {
    const id = this.nextId++;
    this.components.set(id, {});
    return id;
  }

  addComponent(entity: number, component: any): void {
    const current = this.components.get(entity) || {};
    const merged = { ...current, ...component };
    this.components.set(entity, merged);
  }

  getComponents(entity: number): any {
    return this.components.get(entity);
  }
}

export default World;
