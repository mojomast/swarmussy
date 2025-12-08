import json
from typing import Dict, Any, List, Optional

class ECSValidationError(ValueError):
    pass

class ECSCore:
    def __init__(self):
        # entities -> {component_type: data}
        self._entities: Dict[int, Dict[str, Any]] = {}
        self._next_id: int = 1

    # Entity management
    def add_entity(self) -> int:
        entity_id = self._next_id
        self._entities[entity_id] = {}
        self._next_id += 1
        return entity_id

    def remove_entity(self, entity_id: int) -> None:
        if entity_id not in self._entities:
            raise ECSValidationError(f"Entity {entity_id} does not exist")
        del self._entities[entity_id]

    def has_entity(self, entity_id: int) -> bool:
        return entity_id in self._entities

    # Components management
    def add_component(self, entity_id: int, component_type: str, data: Any) -> None:
        if entity_id not in self._entities:
            raise ECSValidationError(f"Entity {entity_id} does not exist")
        if not isinstance(component_type, str) or not component_type:
            raise ECSValidationError("component_type must be a non-empty string")
        if data is None:
            raise ECSValidationError("component data cannot be None")
        self._entities[entity_id][component_type] = data

    def update_component(self, entity_id: int, component_type: str, data: Any) -> None:
        if entity_id not in self._entities:
            raise ECSValidationError(f"Entity {entity_id} does not exist")
        if component_type not in self._entities[entity_id]:
            raise ECSValidationError(f"Component {component_type} not found on entity {entity_id}")
        self._entities[entity_id][component_type] = data

    def remove_component(self, entity_id: int, component_type: str) -> None:
        if entity_id not in self._entities:
            raise ECSValidationError(f"Entity {entity_id} does not exist")
        if component_type in self._entities[entity_id]:
            del self._entities[entity_id][component_type]
        else:
            raise ECSValidationError(f"Component {component_type} not found on entity {entity_id}")

    def get_components(self, entity_id: int) -> Dict[str, Any]:
        if entity_id not in self._entities:
            raise ECSValidationError(f"Entity {entity_id} does not exist")
        return dict(self._entities[entity_id])

    def get_entities(self) -> List[int]:
        return sorted(list(self._entities.keys()))

    # Convenience setters/getters for common components
    def set_position(self, entity_id: int, x: float, y: float, z: float) -> None:
        self.add_component(entity_id, 'Position', {'x': float(x), 'y': float(y), 'z': float(z)})

    def set_sprite(self, entity_id: int, sprite: str) -> None:
        if not isinstance(sprite, str) or not sprite:
            raise ECSValidationError("sprite must be a non-empty string")
        self.add_component(entity_id, 'Renderable', {'sprite': sprite})

    def get_renderables(self) -> List[Dict[str, Any]]:
        # return list of entities with Renderable and Position for rendering
        result = []
        for eid, comps in self._entities.items():
            if 'Renderable' in comps and 'Position' in comps:
                result.append({
                    'entity_id': eid,
                    'sprite': comps['Renderable'].get('sprite'),
                    'position': comps['Position']
                })
        return result

    # Render simulation (returns what would be drawn)
    def render_scene(self) -> List[Dict[str, Any]]:
        # In a real engine this would issue draw calls. Here we simulate by returning the renderables.
        scene = self.get_renderables()
        return scene

    # Persistence
    def save_state(self, file_path: str) -> None:
        data = {
            'entities': self._entities,
            'next_id': self._next_id
        }
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)

    def load_state(self, file_path: str) -> None:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except json.JSONDecodeError:
            raise ECSValidationError('Corrupted save file')
        if 'entities' not in data or 'next_id' not in data:
            raise ECSValidationError('Corrupted save file')
        # Basic validation
        if not isinstance(data['entities'], dict) or not isinstance(data['next_id'], int):
            raise ECSValidationError('Corrupted save file')
        self._entities = {int(k): dict(v) for k, v in data['entities'].items()}
        self._next_id = int(data['next_id'])

    # Utilities
    def clear(self) -> None:
        self._entities.clear()
        self._next_id = 1

    def count(self) -> int:
        return len(self._entities)

    # Validation helper for safety checks
    def validate_no_negative_positions(self) -> None:
        for comps in self._entities.values():
            if 'Position' in comps:
                p = comps['Position']
                if any(float(p[k]) < 0.0 for k in ('x','y','z')):
                    raise ECSValidationError('Negative position values are not allowed')

    def __repr__(self) -> str:
        return f"ECSCore(entities={self.count()}, next_id={self._next_id})"
