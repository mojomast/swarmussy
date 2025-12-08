import { WorldSnapshot } from '../../engine/core'

export class MockWorldProvider {
  private baseWorld: WorldSnapshot
  constructor(baseWorld: WorldSnapshot) {
    // deep copy to avoid external mutation
    this.baseWorld = JSON.parse(JSON.stringify(baseWorld))
  }

  public getWorld(): WorldSnapshot {
    // return a fresh snapshot to simulate a dynamic world
    const clone = JSON.parse(JSON.stringify(this.baseWorld))
    // bump a tiny random seed in a deterministic way for tests could be added
    return clone
  }
}
