export class EngineCore {
  private world?: any
  private running: boolean = false
  private tickCount: number = 0
  private gravity: number = 1

  constructor(world?: any) {
    this.world = world
  }

  start() {
    this.running = true
  }

  tick() {
    this.tickCount++
    // apply gravity to any players if present
    if (this.world?.levels) {
      for (const lvl of Object.values(this.world.levels)) {
        if (lvl.players) {
          for (const p of Object.values(lvl.players)) {
            if (typeof p.y === 'number') p.y += 1
          }
        }
      }
    }
  }

  getWorld() {
    return this.world
  }
}
