from dataclasses import dataclass
from typing import List

@dataclass
class EditorEntity:
    x: int
    y: int

class Editor:
    def __init__(self):
        self.entities: List[EditorEntity] = []

    def add_entity(self, x: int, y: int) -> EditorEntity:
        e = EditorEntity(x, y)
        self.entities.append(e)
        return e

    def remove_entity(self, index: int) -> bool:
        if 0 <= index < len(self.entities):
            del self.entities[index]
            return True
        return False
