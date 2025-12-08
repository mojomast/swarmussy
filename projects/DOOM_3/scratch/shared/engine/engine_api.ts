import type { World } from '../world'

export interface EngineAPI {
  getWorldState(): any
  step(dt: number): void
  reset(): void
}

export class EngineAPIImpl implements EngineAPI {
  private world: World

  constructor(world: World) {
    this.world = world
  }

  public getWorldState() {
    return this.world.getState()
  }

  public step(dt: number) {
    // just delegate; world.step uses dt for internal logic
    return this.world.step(dt)
  }

  public reset() {
    this.world.reset()
  }
}
