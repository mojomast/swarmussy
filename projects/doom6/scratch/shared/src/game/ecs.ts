export interface IEntity {
  id: number;
}

export class ECS {
  private nextId = 1;
  private map = new Map<number, any>();

  createEntity(): number {
    const id = this.nextId++;
    this.map.set(id, {});
    return id;
  }

  addComponent(entity: number, component: any): void {
    const curr = this.map.get(entity) || {};
    this.map.set(entity, { ...curr, ...component });
  }

  getComponent(entity: number): any {
    return this.map.get(entity);
  }
}

export default ECS;
