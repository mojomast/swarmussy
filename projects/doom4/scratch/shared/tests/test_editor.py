import unittest
from shared.editor import Editor

class TestEditor(unittest.TestCase):
    def test_add_remove(self):
        ed = Editor()
        e = ed.add_entity(1,2)
        self.assertEqual((e.x, e.y), (1,2))
        self.assertEqual(len(ed.entities), 1)
        ed.remove_entity(0)
        self.assertEqual(len(ed.entities), 0)
