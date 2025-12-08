export type PlayerState = {
  x: number
  y: number
  lastShotAt?: number
}

export function movePlayer(p: PlayerState, dx: number, dy: number): PlayerState {
  p.x += dx
  p.y += dy
  return p
}

export function shoot(p: PlayerState, directionX: number, directionY: number): PlayerState {
  p.lastShotAt = Date.now()
  return p
}
