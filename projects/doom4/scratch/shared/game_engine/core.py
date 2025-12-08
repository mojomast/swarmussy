from dataclasses import dataclass
from typing import List, Optional

@dataclass
class Position:
    x: int
    y: int

@dataclass
class Bullet:
    pos: Position
    vx: int
    vy: int

@dataclass
class Player:
    pos: Position

@dataclass
class Enemy:
    pos: Position

class GameState:
    def __init__(self, width: int = 10, height: int = 10):
        self.width = width
        self.height = height
        self.player = Player(Position(width//2, height//2))
        self.enemies: List[Enemy] = []
        self.bullets: List[Bullet] = []

    def move_player(self, dx: int, dy: int):
        nx = max(0, min(self.width-1, self.player.pos.x + dx))
        ny = max(0, min(self.height-1, self.player.pos.y + dy))
        self.player.pos = Position(nx, ny)

    def update(self):
        # move bullets
        new_bullets = []
        for b in self.bullets:
            nb = Bullet(Position(b.pos.x + b.vx, b.pos.y + b.vy), b.vx, b.vy)
            # keep within bounds
            if 0 <= nb.pos.x < self.width and 0 <= nb.pos.y < self.height:
                new_bullets.append(nb)
        self.bullets = new_bullets

    def render_grid(self) -> List[str]:
        grid = [['.' for _ in range(self.width)] for _ in range(self.height)]
        grid[self.player.pos.y][self.player.pos.x] = 'P'
        for e in self.enemies:
            grid[e.pos.y][e.pos.x] = 'E'
        for b in self.bullets:
            grid[b.pos.y][b.pos.x] = '*'
        return [''.join(row) for row in grid]
