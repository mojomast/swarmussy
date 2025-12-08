import json
from dataclasses import asdict
from typing import Any
from .core import GameState, Enemy, Player, Bullet, Position

def save_metadata(gs: GameState) -> str:
    data = {
        'width': gs.width,
        'height': gs.height,
        'player': {'x': gs.player.pos.x, 'y': gs.player.pos.y},
        'enemies': [{'x': e.pos.x, 'y': e.pos.y} for e in gs.enemies],
        'bullets': [{'x': b.pos.x, 'y': b.pos.y, 'vx': b.vx, 'vy': b.vy} for b in gs.bullets],
    }
    return json.dumps(data)

def load_metadata(s: str) -> GameState:
    data = json.loads(s)
    gs = GameState(width=data['width'], height=data['height'])
    gs.player.pos = Position(data['player']['x'], data['player']['y'])
    gs.enemies = [Enemy(Position(e['x'], e['y'])) for e in data['enemies']] if data['enemies'] else []
    gs.bullets = [Bullet(Position(b['x'], b['y']), b['vx'], b['vy']) for b in data['bullets']]
    return gs
