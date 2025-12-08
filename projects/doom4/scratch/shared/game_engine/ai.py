from typing import List
from .core import GameState, Enemy, Bullet, Position

"""Basic AI: enemies move toward player and shoot when adjacent"""

def enemy_can_shoot(enemy, player) -> bool:
    dx = abs(enemy.pos.x - player.pos.x)
    dy = abs(enemy.pos.y - player.pos.y)
    return (dx + dy) == 1


def step_ai(gs: GameState):
    for e in gs.enemies:
        dx = dy = 0
        if gs.player.pos.x > e.pos.x:
            dx = 1
        elif gs.player.pos.x < e.pos.x:
            dx = -1
        if gs.player.pos.y > e.pos.y:
            dy = 1
        elif gs.player.pos.y < e.pos.y:
            dy = -1
        # move towards player
        e.pos = Position(e.pos.x + dx, e.pos.y + dy)
        # clamp
        e.pos.x = max(0, min(gs.width-1, e.pos.x))
        e.pos.y = max(0, min(gs.height-1, e.pos.y))
        # shoot if adjacent
        if enemy_can_shoot(e, gs.player):
            b = Bullet(Position(e.pos.x, e.pos.y), 0, 0)
            gs.bullets.append(b)
