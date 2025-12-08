import type { World } from './ecs';
import type { IComponent } from './ecs';

export type Lambda = ( dt: number, world: World ) => void;

export class System {
  private name: string;
  private tick: Lambda;
  constructor(name: string, tick: Lambda) {
    this.name = name;
    this.tick = tick;
  }

  run(dt: number, world: World) {
    this.tick(dt, world);
  }
}
