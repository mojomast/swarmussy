import sys
import os
import json
import time
import tempfile
import unittest
import pathlib

# Adjust path to import ECSCore from the shared module
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))  # add scratch/shared
from ecs_core import ECSCore, ECSValidationError

class TestECSCore(unittest.TestCase):
    def setUp(self):
        self.core = ECSCore()

    def test_add_entity_and_get_entities(self):
        e1 = self.core.add_entity()
        e2 = self.core.add_entity()
        self.assertEqual(self.core.get_entities(), [e1, e2])

    def test_add_and_get_component(self):
        e = self.core.add_entity()
        self.core.set_position(e, 1.0, 2.0, 3.0)
        self.core.set_sprite(e, 'hero.png')
        comps = self.core.get_components(e)
        self.assertIn('Position', comps)
        self.assertIn('Renderable', comps)
        self.assertEqual(comps['Position'], {'x': 1.0, 'y': 2.0, 'z': 3.0})
        self.assertEqual(comps['Renderable'], {'sprite': 'hero.png'})

    def test_update_component(self):
        e = self.core.add_entity()
        self.core.set_position(e, 0.0, 0.0, 0.0)
        self.core.update_component(e, 'Position', {'x': 5.0, 'y': 6.0, 'z': 7.0})
        comps = self.core.get_components(e)
        self.assertEqual(comps['Position'], {'x': 5.0, 'y': 6.0, 'z': 7.0})

    def test_remove_component(self):
        e = self.core.add_entity()
        self.core.set_sprite(e, 'sprite.png')
        self.core.remove_component(e, 'Renderable')
        comps = self.core.get_components(e)
        self.assertNotIn('Renderable', comps)

    def test_remove_entity(self):
        e = self.core.add_entity()
        self.assertTrue(self.core.has_entity(e))
        self.core.remove_entity(e)
        self.assertFalse(self.core.has_entity(e))
        with self.assertRaises(ECSValidationError):
            self.core.remove_entity(e)  # already removed

    def test_render_scene(self):
        e = self.core.add_entity()
        self.core.set_position(e, 1.0, 2.0, 3.0)
        self.core.set_sprite(e, 'sprite.png')
        scene = self.core.render_scene()
        self.assertIsInstance(scene, list)
        self.assertEqual(len(scene), 1)
        item = scene[0]
        self.assertIn('entity_id', item)
        self.assertIn('sprite', item)
        self.assertIn('position', item)
        self.assertEqual(item['sprite'], 'sprite.png')

    def test_save_load_roundtrip(self):
        e = self.core.add_entity()
        self.core.set_position(e, 0.0, 1.0, 2.0)
        self.core.set_sprite(e, 'hero.png')
        with tempfile.NamedTemporaryFile(delete=False) as tf:
            path = tf.name
        try:
            self.core.save_state(path)
            other = ECSCore()
            other.load_state(path)
            self.assertEqual(other.count(), 1)
            comps = other.get_components(e)
            self.assertIn('Position', comps)
        finally:
            try:
                os.remove(path)
            except Exception:
                pass

    def test_invalid_component_input(self):
        e = self.core.add_entity()
        with self.assertRaises(ECSValidationError):
            self.core.add_component(9999, 'Position', {'x': 0})
        with self.assertRaises(ECSValidationError):
            self.core.add_component(e, '', {'x': 0})
        with self.assertRaises(ECSValidationError):
            self.core.add_component(e, 'Position', None)

    def test_update_nonexistent_component(self):
        e = self.core.add_entity()
        with self.assertRaises(ECSValidationError):
            self.core.update_component(e, 'Position', {'x': 0})

    def test_negative_positions_validation(self):
        e = self.core.add_entity()
        self.core.set_position(e, -1.0, 0.0, 0.0)
        with self.assertRaises(ECSValidationError):
            self.core.validate_no_negative_positions()

    def test_load_corrupted_file_raises(self):
        e = self.core.add_entity()
        self.core.set_position(e, 1.0, 2.0, 3.0)
        self.core.set_sprite(e, 'sprite.png')
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as tf:
            tf.write('not json')
            path = tf.name
        try:
            with self.assertRaises(ECSValidationError):
                self.core.load_state(path)
        finally:
            try:
                os.remove(path)
            except Exception:
                pass

    def test_large_render_performance(self):
        # Create many entities to test rendering performance
        n = 2000  # keep reasonable for CI
        eids = []
        for i in range(n):
            eid = self.core.add_entity()
            self.core.set_position(eid, float(i), float(i), float(i))
            self.core.set_sprite(eid, f'sprite_{i}.png')
            eids.append(eid)
        t0 = time.perf_counter()
        scene = self.core.render_scene()
        t1 = time.perf_counter()
        self.assertEqual(len(scene), n)
        self.assertLess(t1 - t0, 2.0)  # should render quickly for moderate n

if __name__ == '__main__':
    unittest.main()
