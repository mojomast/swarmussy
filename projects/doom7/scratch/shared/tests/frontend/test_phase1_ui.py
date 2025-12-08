import unittest

# Simple unit tests for Phase1 UI mapping utility
from phase1_tasks import map_phase1_tasks_to_ui, UI_STATE_ENABLED, UI_STATE_DISABLED, UI_STATE_HIDDEN

class TestPhase1UI(unittest.TestCase):
    def test_map_empty(self):
        self.assertEqual(map_phase1_tasks_to_ui([]), [])

    def test_map_basic(self):
        tasks = [
            {'id': 't1', 'name': 'Task 1', 'status': 'pending'},
            {'id': 't2', 'name': 'Task 2', 'status': 'in_progress'},
            {'id': 't3', 'name': 'Task 3', 'status': 'done'},
        ]
        out = map_phase1_tasks_to_ui(tasks)
        self.assertEqual(len(out), 3)
        self.assertEqual(out[0]['ui_state'], UI_STATE_ENABLED)
        self.assertEqual(out[1]['ui_state'], UI_STATE_ENABLED)
        self.assertEqual(out[2]['ui_state'], UI_STATE_HIDDEN)

if __name__ == '__main__':
    unittest.main()
