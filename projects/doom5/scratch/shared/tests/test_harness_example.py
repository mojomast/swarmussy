# Lightweight test harness example for ECS and editors
import json
from ecs_core import ECSCore, ECSValidationError

def run_example_scenario():
    core = ECSCore()
    e1 = core.add_entity()
    core.set_position(e1, 0.0, 0.0, 0.0)
    core.set_sprite(e1, 'hero.png')
    e2 = core.add_entity()
    core.set_position(e2, 10.0, 0.0, 0.0)
    core.set_sprite(e2, 'villain.png')
    print(json.dumps(core.render_scene(), indent=2))

if __name__ == '__main__':
    run_example_scenario()
